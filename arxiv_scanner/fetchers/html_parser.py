"""
HTML 解析器：从 arXiv 论文 HTML 页面提取作者机构和邮箱。

解析策略（按优先级）：
  1. LaTeXML 标准结构（arxiv.org/html & ar5iv.org 均使用）
     - div.ltx_authors -> span.ltx_personname（姓名）
     - span.ltx_role_affiliation（机构）
     - span.ltx_role_email（邮箱）
  2. 上标数字映射（多作者共享机构时）
  3. <meta name="citation_author_institution"> 降级
  4. 全文正则扫描邮箱 + 启发式姓名匹配

常见坑：
  - 共享机构：多作者标注上标 123，机构列在最后
  - 名字格式不一致：API 返回 "Y. LeCun" vs HTML 中 "Yann LeCun"
  - 部分旧论文无 HTML 版本（404）-> 自动 fallback 到 ar5iv.org
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

from bs4 import BeautifulSoup, Tag

from arxiv_scanner.config import Config
from arxiv_scanner.fetchers.http_client import HttpClient

logger = logging.getLogger(__name__)

# 邮箱正则（宽松匹配，后续过滤明显无效值）
_EMAIL_RE = re.compile(
    r"\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b"
)

# 明显无效的邮箱片段（示例、占位符等）
_INVALID_EMAIL_KEYWORDS = {
    "example", "domain", "your@", "user@", "email@",
    "xxx", "foo@", "bar@", "test@",
}


@dataclass
class ParsedAuthorInfo:
    """HTML 解析出的单个作者原始信息"""
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None


class HtmlParser:
    """从 arXiv HTML 页面解析作者机构和邮箱"""

    def __init__(self, config: Config, http_client: HttpClient) -> None:
        self.config = config
        self.http = http_client

    def fetch_and_parse(self, paper_id: str) -> list[ParsedAuthorInfo]:
        """
        按配置的 html_sources 顺序尝试抓取并解析。
        任意一个成功即返回，全部失败返回空列表（不抛异常）。
        """
        if not self.config.html_sources:
            return []

        for url_tpl in self.config.html_sources:
            url = url_tpl.format(id=paper_id)
            try:
                resp = self.http.get(
                    url,
                    domain_key="html_fetch",
                    base_delay=self.config.rate_limit.html_fetch_delay,
                    timeout=45,
                )
                results = self._parse_html(resp.text)
                if results:
                    logger.info(
                        f"[{paper_id}] HTML 解析成功，"
                        f"来源: {url}，解析 {len(results)} 位作者"
                    )
                    return results
                else:
                    logger.debug(f"[{paper_id}] {url} 响应成功但未解析到作者信息")
            except Exception as e:
                logger.warning(f"[{paper_id}] HTML 源 {url} 失败: {e}")

        logger.info(f"[{paper_id}] 所有 HTML 源均失败，跳过机构/邮箱提取")
        return []

    def _parse_html(self, html: str) -> list[ParsedAuthorInfo]:
        """
        尝试多种解析策略，返回作者列表。
        列表为空表示本页面无法解析（上层会尝试下一个 HTML 源）。
        """
        soup = BeautifulSoup(html, "lxml")

        # 策略 1：LaTeXML 标准结构
        authors_div = soup.find("div", class_="ltx_authors")
        if authors_div:
            results = self._parse_latexml_authors(authors_div, soup)
            if results:
                return results

        # 策略 2：降级到 <meta> 标签
        results = self._parse_meta_tags(soup)
        if results:
            return results

        return []

    # ── 策略 1：LaTeXML DOM 解析 ─────────────────────────────────────────────

    def _parse_latexml_authors(
        self, authors_div: Tag, full_soup: BeautifulSoup
    ) -> list[ParsedAuthorInfo]:
        """
        LaTeXML 输出的典型 DOM 结构：

        <div class="ltx_authors">
          <span class="ltx_creator ltx_role_author">
            <span class="ltx_personname">Alice Smith</span>
            <span class="ltx_contact ltx_role_affiliation">MIT CSAIL</span>
            <span class="ltx_contact ltx_role_email">
              <a href="mailto:alice@mit.edu">alice@mit.edu</a>
            </span>
          </span>
          ...
        </div>

        复杂情况：多作者共享机构，使用上标数字标注，
        机构信息写在 <section> 或 <div> 中而非 <span> 内。
        """
        results: list[ParsedAuthorInfo] = []

        # 先尝试构建上标->机构映射（处理共享机构场景）
        affil_map = self._build_affiliation_map(authors_div, full_soup)

        creator_spans = authors_div.find_all(
            "span",
            class_=lambda c: c and "ltx_role_author" in c,
        )

        for span in creator_spans:
            # 提取姓名
            name_el = span.find("span", class_="ltx_personname")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name:
                continue

            # 提取机构
            affiliation = self._extract_affiliation(span, name_el, affil_map)

            # 提取邮箱
            email = self._extract_email_from_span(span)

            results.append(ParsedAuthorInfo(
                name=name,
                affiliation=self._clean_affiliation(affiliation),
                email=email,
            ))

        if results:
            # 全文补充邮箱（对未匹配到邮箱的作者进行启发式填充）
            self._supplement_emails_from_fulltext(full_soup, results)
            # 共享机构向前回填
            self._backfill_affiliations(results)

        return results

    def _build_affiliation_map(
        self, authors_div: Tag, full_soup: BeautifulSoup
    ) -> dict[str, str]:
        """
        构建上标数字/字母 -> 机构名 的映射表。

        处理形如：
          Alice Smith(1)  Bob Jones(1)(2)
          (1) MIT CSAIL  (2) Stanford AI Lab
        """
        affil_map: dict[str, str] = {}

        # 查找所有可能包含机构信息的元素
        # 支持两种格式：
        #   1. ltx_role_affiliation（标准 LaTeXML）
        #   2. ltx_role_institutetext（footnote 式标注，如 \institutetext{...}）
        for tag in full_soup.find_all(
            class_=re.compile(r"ltx_role_affiliation|ltx_role_institutetext")
        ):
            # 提取上标标记（sup 或 ltx_note_mark）
            sup_tags = tag.find_all(
                ["sup", "span"],
                class_=re.compile(r"ltx_sup|ltx_note_mark")
            )
            text = tag.get_text(separator=" ", strip=True)

            for sup in sup_tags:
                key = sup.get_text(strip=True)
                if key and re.match(r"[\d*]+", key):
                    # 去掉上标文字和类型标签（如 "institutetext:"），剩余为机构名
                    cleaned = text.replace(sup.get_text(strip=True), "").strip()
                    # 去掉 "institutetext:" 或 "footnotetext:" 前缀
                    cleaned = re.sub(r"^(institutetext|footnotetext)\s*:\s*", "", cleaned).strip()
                    if cleaned and len(cleaned) > 2:
                        affil_map[key] = cleaned

        return affil_map

    def _extract_affiliation(
        self,
        author_span: Tag,
        name_el: Tag,
        affil_map: dict[str, str],
    ) -> Optional[str]:
        """从作者 span 提取机构，支持多种方式"""

        # 方式 A：直接包含 ltx_role_affiliation 或 ltx_role_institutetext
        aff_el = author_span.find(class_=re.compile(r"ltx_role_affiliation|ltx_role_institutetext"))
        if aff_el:
            text = aff_el.get_text(separator=" ", strip=True)
            text = re.sub(r"^(institutetext|footnotetext)\s*:\s*", "", text).strip()
            return text

        # 方式 B：姓名旁的上标数字 -> 查映射表
        if affil_map:
            # 查找姓名元素后面的上标
            sup_marks = name_el.find_all(
                ["sup", "span"],
                class_=re.compile(r"ltx_sup|ltx_note_mark")
            )
            for sup in sup_marks:
                key = sup.get_text(strip=True)
                if key in affil_map:
                    return affil_map[key]

            # 也检查 author span 内的其他上标
            for sup in author_span.find_all(["sup"], recursive=True):
                key = sup.get_text(strip=True)
                if key in affil_map:
                    return affil_map[key]

            # 方式 C：检查作者 span 内的 <a> 链接 href 锚点
            # 有些论文用 <a href="#footnote1"> 连接到 footnote
            for a_tag in author_span.find_all("a", href=True):
                href = a_tag.get("href", "")
                # 提取锚点中的数字
                m = re.search(r"#.*?(\d+)", href)
                if m:
                    key = m.group(1)
                    if key in affil_map:
                        return affil_map[key]

            # 方式 D：检查 personname 中的纯数字文本节点
            # 有些论文在名字后面直接放数字（非 sup/span 包裹）
            full_text = name_el.get_text(strip=True)
            nums = re.findall(r"(\d+)", full_text)
            for n in nums:
                if n in affil_map:
                    return affil_map[n]

        return None

    def _extract_email_from_span(self, span: Tag) -> Optional[str]:
        """从作者 span 的 email 子元素提取邮箱"""
        email_el = span.find(class_=re.compile(r"ltx_role_email"))
        if not email_el:
            return None

        # 优先从 mailto: href 提取（最可靠）
        mailto = email_el.find("a", href=re.compile(r"^mailto:", re.I))
        if mailto and mailto.get("href"):
            email = mailto["href"].replace("mailto:", "").strip()
            if self._is_valid_email(email):
                return email

        # 降级：正则提取文本中的邮箱
        m = _EMAIL_RE.search(email_el.get_text())
        if m and self._is_valid_email(m.group(1)):
            return m.group(1)

        return None

    # ── 策略 2：Meta 标签降级 ─────────────────────────────────────────────────

    def _parse_meta_tags(self, soup: BeautifulSoup) -> list[ParsedAuthorInfo]:
        """
        从 Google Scholar 兼容的 meta 标签提取作者和机构。
        部分 arXiv/ar5iv 页面包含这些标签。
        """
        names = [
            m["content"].strip()
            for m in soup.find_all("meta", attrs={"name": "citation_author"})
            if m.get("content")
        ]
        insts = [
            m["content"].strip()
            for m in soup.find_all("meta", attrs={"name": "citation_author_institution"})
            if m.get("content")
        ]

        if not names:
            return []

        results = []
        for i, name in enumerate(names):
            results.append(ParsedAuthorInfo(
                name=name,
                affiliation=insts[i] if i < len(insts) else None,
            ))

        # 补充邮箱
        self._supplement_emails_from_fulltext(soup, results)
        return results

    # ── 邮箱补充（全文扫描）─────────────────────────────────────────────────

    def _supplement_emails_from_fulltext(
        self,
        soup: BeautifulSoup,
        authors: list[ParsedAuthorInfo],
    ) -> None:
        """
        全文扫描所有邮箱，尝试与作者姓名启发式匹配。

        策略：
        1. 邮箱本地部分包含作者姓名片段 -> 直接分配
        2. 剩余未分配邮箱 -> 分配给第一个没有邮箱的作者（通讯作者）
        """
        all_emails = set(_EMAIL_RE.findall(soup.get_text()))
        # 过滤无效邮箱
        all_emails = {e for e in all_emails if self._is_valid_email(e)}

        already_assigned = {a.email for a in authors if a.email}
        unassigned = all_emails - already_assigned

        if not unassigned:
            return

        # 第一轮：姓名匹配
        for email in list(unassigned):
            local = re.sub(r"[.\-_]", "", email.split("@")[0].lower())
            for author in authors:
                if author.email:
                    continue
                name_tokens = [
                    p for p in author.name.lower().split()
                    if len(p) > 2
                ]
                if any(token in local for token in name_tokens):
                    author.email = email
                    unassigned.discard(email)
                    break

        # 第二轮：剩余邮箱分配给首个无邮箱作者（通讯作者标注）
        for email in sorted(unassigned):  # 排序保证确定性
            for author in authors:
                if not author.email:
                    author.email = email
                    break
            else:
                break  # 所有作者都有邮箱了

    # ── 工具方法 ──────────────────────────────────────────────────────────────

    @staticmethod
    def _clean_affiliation(raw: Optional[str]) -> Optional[str]:
        """清理机构字符串：去除脚注符号、多余空白"""
        if not raw:
            return None
        # 去掉脚注符号（上标数字、*, 等）
        cleaned = re.sub(r"[*\d]+", "", raw).strip()
        # 合并多余空白
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        # 去掉纯符号残留
        if len(cleaned) < 3:
            return None
        return cleaned

    @staticmethod
    def _backfill_affiliations(authors: list[ParsedAuthorInfo]) -> None:
        """
        向前回填共享机构。
        场景：某篇论文所有作者共享同一机构，机构只标注在最后一个作者旁。
        """
        last_aff: Optional[str] = None
        for author in reversed(authors):
            if author.affiliation:
                last_aff = author.affiliation
            elif last_aff:
                author.affiliation = last_aff

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """过滤明显无效的邮箱地址"""
        email_lower = email.lower()
        return not any(kw in email_lower for kw in _INVALID_EMAIL_KEYWORDS)
