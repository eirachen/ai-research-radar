#!/usr/bin/env python3
"""
enrich-papers.py — 用 arxiv_scanner HTML 解析增强 confirmed 论文作者信息。

流程：
  1. 读取 arxiv-daily.json，找出所有 confirmed 论文
  2. 对每篇论文调用 arxiv_scanner.HtmlParser 解析 HTML 页面
     → 提取每位作者的 affiliation + email
  3. 将高校端作者信息自动写入 talent-notes.json
  4. 可选：调用 Scholar/GitHub 搜索补充身份信息

用法：
  python scripts/enrich-papers.py                    # 处理所有 confirmed 论文
  python scripts/enrich-papers.py --ids 2604.12345   # 只处理指定论文
  python scripts/enrich-papers.py --new-only         # 只处理还没增强过的论文
  python scripts/enrich-papers.py --with-identity    # 同时搜索 Scholar/GitHub
  python scripts/enrich-papers.py --with-scholar     # 只搜索 Scholar（带缓存，安全）
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import time

# 确保能导入 arxiv_scanner
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arxiv_scanner.config import Config, RateLimitConfig
from arxiv_scanner.fetchers.html_parser import HtmlParser
from arxiv_scanner.fetchers.http_client import HttpClient
from arxiv_scanner.identity.scholar import ScholarSearcher
from arxiv_scanner.identity.github import GitHubSearcher
from arxiv_scanner.models import Author, AuthorIdentity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
for noisy in ("urllib3", "requests", "httpx", "scholarly"):
    logging.getLogger(noisy).setLevel(logging.WARNING)
logger = logging.getLogger("enrich-papers")

# ── 路径 ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
ARXIV_JSON = os.path.join(PROJECT_DIR, "reports", "arxiv-daily.json")
TALENT_JSON = os.path.join(PROJECT_DIR, "reports", "talent-notes.json")

# ── 港校关键词 ────────────────────────────────────────────────────────────────
HK_UNIVERSITIES = {
    "University of Hong Kong": "HKU",
    "Chinese University of Hong Kong": "CUHK",
    "Hong Kong University of Science and Technology": "HKUST",
    "City University of Hong Kong": "CityU",
    "Hong Kong Polytechnic University": "PolyU",
    "Hong Kong Baptist University": "HKBU",
}
# 内地分校不算港校
NOT_HK_KEYWORDS = ["Shenzhen", "Guangzhou", "(Guangzhou)", "(Shenzhen)", "CUHK-SZ", "HKUST-GZ"]

# ── Email 域名 → 大学映射 ─────────────────────────────────────────────────────
EMAIL_DOMAIN_TO_UNI = {
    # 港校
    "hku.hk": ("The University of Hong Kong", True),
    "cs.hku.hk": ("The University of Hong Kong", True),
    "connect.hku.hk": ("The University of Hong Kong", True),
    "cuhk.edu.hk": ("The Chinese University of Hong Kong", True),
    "link.cuhk.edu.hk": ("The Chinese University of Hong Kong", True),
    "se.cuhk.edu.hk": ("The Chinese University of Hong Kong", True),
    "ust.hk": ("Hong Kong University of Science and Technology", True),
    "connect.ust.hk": ("Hong Kong University of Science and Technology", True),
    "cse.ust.hk": ("Hong Kong University of Science and Technology", True),
    "cityu.edu.hk": ("City University of Hong Kong", True),
    "my.cityu.edu.hk": ("City University of Hong Kong", True),
    "polyu.edu.hk": ("Hong Kong Polytechnic University", True),
    "connect.polyu.hk": ("Hong Kong Polytechnic University", True),
    "hkbu.edu.hk": ("Hong Kong Baptist University", True),
    # 港校内地分校（不算港校）
    "connect.hkust-gz.edu.cn": ("HKUST (Guangzhou)", False),
    "hkust-gz.edu.cn": ("HKUST (Guangzhou)", False),
    "cuhk.edu.cn": ("CUHK-Shenzhen", False),
    # 内地高校
    "pku.edu.cn": ("Peking University", False),
    "stu.pku.edu.cn": ("Peking University", False),
    "tsinghua.edu.cn": ("Tsinghua University", False),
    "mails.tsinghua.edu.cn": ("Tsinghua University", False),
    "sjtu.edu.cn": ("Shanghai Jiao Tong University", False),
    "zju.edu.cn": ("Zhejiang University", False),
    "fudan.edu.cn": ("Fudan University", False),
    "ustc.edu.cn": ("USTC", False),
    "mail.ustc.edu.cn": ("USTC", False),
    "hit.edu.cn": ("Harbin Institute of Technology", False),
    "stu.hit.edu.cn": ("Harbin Institute of Technology", False),
    "hust.edu.cn": ("Huazhong University of Science and Technology", False),
    "mail.hust.edu.cn": ("Huazhong University of Science and Technology", False),
    "nju.edu.cn": ("Nanjing University", False),
    "buaa.edu.cn": ("Beihang University", False),
    "suda.edu.cn": ("Soochow University", False),
    "nwpu.edu.cn": ("Northwestern Polytechnical University", False),
    # 海外高校
    "stanford.edu": ("Stanford University", False),
    "mit.edu": ("MIT", False),
    "berkeley.edu": ("UC Berkeley", False),
    "cmu.edu": ("Carnegie Mellon University", False),
    "princeton.edu": ("Princeton University", False),
    "ethz.ch": ("ETH Zurich", False),
    "epfl.ch": ("EPFL", False),
    "cam.ac.uk": ("University of Cambridge", False),
    "ox.ac.uk": ("University of Oxford", False),
    "nyu.edu": ("New York University", False),
    "uva.nl": ("University of Amsterdam", False),
    "kaust.edu.sa": ("KAUST", False),
    "kyoto-u.ac.jp": ("Kyoto University", False),
}


def infer_university_from_email(email: str):
    """从 email 域名推断大学和港校状态，返回 (uni_name, is_hk) 或 None"""
    if not email or "@" not in email:
        return None
    domain = email.split("@")[1].lower().strip()
    # 精确匹配
    if domain in EMAIL_DOMAIN_TO_UNI:
        return EMAIL_DOMAIN_TO_UNI[domain]
    # 尝试去掉子域名匹配
    parts = domain.split(".")
    for i in range(len(parts) - 1):
        subdomain = ".".join(parts[i:])
        if subdomain in EMAIL_DOMAIN_TO_UNI:
            return EMAIL_DOMAIN_TO_UNI[subdomain]
    # 检查是否是 .edu / .edu.xx 域名（大概率是高校）
    if ".edu" in domain:
        return (domain, False)  # 返回域名本身作为大学名
    return None


def is_hk_university(affiliation: str) -> bool:
    """判断 affiliation 是否是港校（排除内地分校）"""
    if not affiliation:
        return False
    aff_upper = affiliation.upper()
    for kw in NOT_HK_KEYWORDS:
        if kw.upper() in aff_upper:
            return False
    for hk_name in HK_UNIVERSITIES:
        if hk_name.upper() in aff_upper:
            return True
    # 缩写匹配
    for abbr in HK_UNIVERSITIES.values():
        # 精确匹配缩写（前后有空格/逗号/开头结尾）
        if re.search(r'(?<![A-Za-z])' + re.escape(abbr) + r'(?![A-Za-z])', affiliation):
            return True
    return False


def is_university(affiliation: str) -> bool:
    """判断 affiliation 是否是高校（而非企业）"""
    if not affiliation:
        return False
    uni_keywords = [
        "University", "Institute", "College", "School", "Academy",
        "Laboratory", "Laboratoire", "Universit", "Politecnico",
        "ETH", "MIT", "EPFL", "INRIA", "CNRS", "Max Planck",
        "CAS", "Chinese Academy", "Tsinghua", "Peking", "Fudan",
    ]
    aff_lower = affiliation.lower()
    return any(kw.lower() in aff_lower for kw in uni_keywords)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_confirmed_papers(arxiv_data):
    """从 arxiv-daily.json 提取所有 confirmed 论文"""
    papers = []
    for company_id, company_data in arxiv_data.get("companies", {}).items():
        for p in company_data.get("papers", []):
            if p.get("collabConfidence") == "confirmed":
                p["_company"] = company_id
                papers.append(p)
    return papers


def extract_arxiv_id(paper):
    """从论文数据中提取 arXiv ID"""
    url = paper.get("arxivUrl", "") or paper.get("id", "")
    m = re.search(r"(\d{4}\.\d{4,5})", url)
    return m.group(1) if m else None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="用 arxiv_scanner 增强 confirmed 论文作者信息")
    parser.add_argument("--ids", nargs="+", help="只处理指定的 arXiv ID")
    parser.add_argument("--new-only", action="store_true", help="只处理还没增强过的论文")
    parser.add_argument("--with-identity", action="store_true", help="同时搜索 Scholar/GitHub")
    parser.add_argument("--with-scholar", action="store_true", help="只搜索 Scholar（带 7 天缓存，更安全）")
    parser.add_argument("--scholar-proxy", default="", help="Scholar 代理 URL（如 http://43.167.194.82:8800/scholar-proxy）")
    parser.add_argument("--scholar-max", type=int, default=20, help="Scholar 搜索最多处理人数（防封禁）")
    parser.add_argument("--max-authors", type=int, default=10, help="每篇论文最多处理作者数")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    args = parser.parse_args()

    # ── 加载数据 ──
    logger.info("加载 arxiv-daily.json...")
    arxiv_data = load_json(ARXIV_JSON)
    confirmed = get_confirmed_papers(arxiv_data)
    logger.info(f"共 {len(confirmed)} 篇 confirmed 论文")

    logger.info("加载 talent-notes.json...")
    talent_data = load_json(TALENT_JSON)
    notes = talent_data.get("notes", {})

    # ── 过滤 ──
    if args.ids:
        target_ids = set(args.ids)
        confirmed = [p for p in confirmed if extract_arxiv_id(p) in target_ids]
        logger.info(f"过滤后: {len(confirmed)} 篇")

    if args.new_only:
        confirmed = [p for p in confirmed if not p.get("_htmlEnriched")]
        logger.info(f"过滤 new-only 后: {len(confirmed)} 篇")

    if not confirmed:
        logger.info("没有需要处理的论文，退出")
        return

    # ── 初始化 arxiv_scanner ──
    config = Config(
        rate_limit=RateLimitConfig(
            html_fetch_delay=2.0,
            scholar_delay=12.0,
            github_delay=1.0,
        ),
        max_authors_per_paper=args.max_authors,
        enable_html_parse=True,
        enable_identity_search=args.with_identity,
    )
    http = HttpClient(config)
    html_parser = HtmlParser(config, http)

    # 可选：身份搜索器
    scholar_searcher = None
    identity_searchers = []
    use_scholar = args.with_scholar or args.with_identity
    scholar_proxy_url = args.scholar_proxy
    
    if use_scholar:
        if scholar_proxy_url:
            # 代理模式：通过 Lighthouse 服务器转发 Scholar 请求
            logger.info(f"📡 Scholar 代理模式: {scholar_proxy_url}")
            from _scholar_proxy_searcher import ProxyScholarSearcher
            try:
                scholar_searcher = ProxyScholarSearcher(scholar_proxy_url, config)
                identity_searchers.append(scholar_searcher)
                logger.info("✅ Scholar 代理搜索器已就绪（带 7 天本地缓存）")
            except Exception as e:
                logger.warning(f"Scholar 代理搜索器初始化失败: {e}")
        else:
            # 直连模式：直接用 scholarly 库
            try:
                scholar_searcher = ScholarSearcher(config)
                identity_searchers.append(scholar_searcher)
                logger.info("✅ Scholar 搜索器已就绪（带 7 天本地缓存）")
            except Exception as e:
                logger.warning(f"Scholar 搜索器初始化失败: {e}")
    if args.with_identity:
        try:
            identity_searchers.append(GitHubSearcher(config, http))
            logger.info("✅ GitHub 搜索器已就绪")
        except Exception as e:
            logger.warning(f"GitHub 搜索器初始化失败: {e}")
    
    scholar_count = 0  # Scholar 查询计数器（防封禁）
    scholar_max = args.scholar_max

    # ── 统计 ──
    stats = {
        "papers_processed": 0,
        "html_success": 0,
        "html_failed": 0,
        "affiliations_found": 0,
        "emails_found": 0,
        "talents_updated": 0,
        "talents_new": 0,
        "hk_talents": 0,
    }

    # ── 处理每篇论文 ──
    for i, paper in enumerate(confirmed, 1):
        arxiv_id = extract_arxiv_id(paper)
        if not arxiv_id:
            logger.warning(f"跳过: 无法提取 arXiv ID from {paper.get('title', '?')[:50]}")
            continue

        title_short = (paper.get("title") or "")[:60]
        company = paper.get("_company", "?")
        logger.info(f"\n[{i}/{len(confirmed)}] {arxiv_id} ({company}) - {title_short}")

        stats["papers_processed"] += 1

        # Step 1: HTML 解析
        parsed_authors = html_parser.fetch_and_parse(arxiv_id)
        if parsed_authors:
            stats["html_success"] += 1
            logger.info(f"  ✅ HTML 解析: {len(parsed_authors)} 位作者")
        else:
            stats["html_failed"] += 1
            logger.info(f"  ❌ HTML 解析失败（可能无 HTML 版本）")
            continue

        # Step 2: 提取高校端作者信息
        paper_authors = paper.get("authors", [])
        if isinstance(paper_authors, str):
            paper_authors = [a.strip() for a in paper_authors.split(",")]

        for pa in parsed_authors:
            affiliation = pa.affiliation
            email_inferred_hk = None

            # 如果 HTML 解析没有 affiliation，尝试从 email 域名推断
            if not affiliation and pa.email:
                inferred = infer_university_from_email(pa.email)
                if inferred:
                    affiliation = inferred[0]
                    email_inferred_hk = inferred[1]
                    logger.info(f"  📧 从 email 推断: {pa.name} → {affiliation} (via {pa.email})")

            if not affiliation:
                continue

            stats["affiliations_found"] += 1
            if pa.email:
                stats["emails_found"] += 1

            # 只处理高校端
            if not is_university(affiliation) and not email_inferred_hk:
                logger.debug(f"  跳过企业端: {pa.name} @ {affiliation}")
                continue

            is_hk = email_inferred_hk if email_inferred_hk is not None else is_hk_university(affiliation)
            if is_hk:
                stats["hk_talents"] += 1

            # 查找/创建人才记录
            talent_key = pa.name
            existing = notes.get(talent_key)

            if existing and existing.get("manuallyEdited"):
                logger.info(f"  ⏭ SKIP (manually edited): {pa.name}")
                continue

            if existing:
                # 只补充空字段，不覆盖
                updated = False
                if not existing.get("university") or existing["university"] == "待确认":
                    existing["university"] = affiliation
                    updated = True
                if pa.email and not existing.get("contactInfo", {}).get("email"):
                    if "contactInfo" not in existing:
                        existing["contactInfo"] = {}
                    existing["contactInfo"]["email"] = pa.email
                    updated = True
                if is_hk and not existing.get("isHK"):
                    existing["isHK"] = True
                    updated = True
                if updated:
                    stats["talents_updated"] += 1
                    logger.info(f"  📝 更新: {pa.name} → {affiliation}" +
                               (f" [{pa.email}]" if pa.email else "") +
                               (" 🇭🇰" if is_hk else ""))
            else:
                # 新增人才
                new_talent = {
                    "name": pa.name,
                    "university": affiliation,
                    "isHK": is_hk,
                    "status": "待确认",
                    "group": "待确认",
                }
                if pa.email:
                    new_talent["contactInfo"] = {"email": pa.email}
                notes[talent_key] = new_talent
                stats["talents_new"] += 1
                logger.info(f"  ➕ 新增: {pa.name} → {affiliation}" +
                           (f" [{pa.email}]" if pa.email else "") +
                           (" 🇭🇰" if is_hk else ""))

            # Step 3: 可选身份搜索（Scholar / GitHub）
            talent = notes[talent_key]
            should_search = identity_searchers and not talent.get("scholar")
            
            # Scholar 计数限制
            if should_search and scholar_searcher and scholar_count >= scholar_max:
                logger.info(f"  ⏸ Scholar 已达上限 ({scholar_max})，跳过")
                should_search = False
            
            if should_search:
                author_obj = Author(
                    name=pa.name,
                    affiliation=affiliation,
                    email=pa.email,
                    identity=AuthorIdentity(),
                )
                for searcher in identity_searchers:
                    try:
                        if searcher.platform == "google_scholar":
                            scholar_count += 1
                        searcher.search(author_obj)
                    except Exception as e:
                        logger.warning(f"  [{searcher.platform}] 搜索失败: {e}")
                        # Scholar 被封禁时停止所有后续 Scholar 搜索
                        if "blocked" in str(e).lower() or "MaxTriesExceeded" in str(e):
                            logger.error("  🚫 Scholar 已被封禁，停止所有 Scholar 查询")
                            scholar_count = scholar_max

                # 回写 Scholar 信息
                if author_obj.identity.google_scholar:
                    gs = author_obj.identity.google_scholar
                    
                    # affiliation 交叉验证：Scholar 返回的机构和论文 HTML 的要有关联
                    scholar_aff = (gs.affiliation or "").lower()
                    paper_aff = (affiliation or "").lower()
                    aff_match = True
                    if scholar_aff and paper_aff:
                        # 提取关键词比对（至少有一个主要词匹配）
                        scholar_tokens = set(re.findall(r'[a-z]{3,}', scholar_aff))
                        paper_tokens = set(re.findall(r'[a-z]{3,}', paper_aff))
                        overlap = scholar_tokens & paper_tokens
                        if not overlap and len(scholar_tokens) > 0 and len(paper_tokens) > 0:
                            aff_match = False
                            logger.warning(
                                f"  ⚠️ Scholar 机构不匹配: Scholar='{gs.affiliation}' "
                                f"vs HTML='{affiliation}' → 可能是同名不同人，跳过"
                            )
                    
                    if aff_match:
                        if not talent.get("scholar"):
                            talent["scholar"] = gs.url
                        if gs.citations and not talent.get("citations"):
                            talent["citations"] = gs.citations
                        if gs.h_index:
                            talent["hIndex"] = gs.h_index
                        if gs.affiliation and (not talent.get("university") or talent["university"] == "待确认"):
                            talent["university"] = gs.affiliation
                        if gs.interests:
                            talent["researchInterests"] = gs.interests[:5]
                        stats["scholar_found"] = stats.get("scholar_found", 0) + 1
                        logger.info(
                            f"  📚 Scholar: {gs.citations} citations, h={gs.h_index}, "
                            f"机构='{gs.affiliation}'"
                        )

                # 回写 GitHub 信息
                if author_obj.identity.github:
                    gh = author_obj.identity.github
                    if not talent.get("github"):
                        talent["github"] = gh.url
                    logger.info(f"  🐙 GitHub: @{gh.username}")

    # ── 保存 ──
    if not args.dry_run:
        talent_data["notes"] = notes
        save_json(talent_data, TALENT_JSON)
        logger.info(f"\n✅ 已保存到 {TALENT_JSON}")
    else:
        logger.info(f"\n🔍 Dry run 模式，未写入文件")

    # ── 统计输出 ──
    logger.info(f"""
{'='*50}
增强完成摘要
{'='*50}
论文处理: {stats['papers_processed']}
HTML 解析成功: {stats['html_success']}
HTML 解析失败: {stats['html_failed']}
识别到机构: {stats['affiliations_found']}
识别到邮箱: {stats['emails_found']}
人才更新: {stats['talents_updated']}
人才新增: {stats['talents_new']}
港校人才: {stats['hk_talents']}
Scholar 查到: {stats.get('scholar_found', 0)}
Scholar 查询数: {scholar_count}/{scholar_max}
{'='*50}
""")


if __name__ == "__main__":
    main()
