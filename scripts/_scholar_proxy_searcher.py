"""
Scholar 代理搜索器：通过 Lighthouse 服务器的 /scholar-proxy API 查询 Google Scholar。
解决公司网络无法直接访问 Google Scholar 的问题。

工作流：
  本地 → POST /scholar-proxy {url: "https://scholar.google.com/..."} → 服务器
  服务器 → GET scholar.google.com → HTML → 返回本地
  本地解析 HTML 提取 citation/h-index/affiliation

带 7 天本地缓存，避免重复查询。
"""
from __future__ import annotations

import json
import logging
import re
import time
import random
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional

from arxiv_scanner.config import Config
from arxiv_scanner.identity.base import IdentitySearcher
from arxiv_scanner.models import Author, ScholarProfile

logger = logging.getLogger(__name__)

_CACHE_DIR = Path.home() / ".arxiv_scanner_cache"
_CACHE_FILE = _CACHE_DIR / "scholar_proxy_cache.json"
_CACHE_TTL_DAYS = 7


class ProxyScholarSearcher(IdentitySearcher):
    """通过 Lighthouse 服务器代理查询 Google Scholar"""

    platform = "google_scholar"

    def __init__(self, proxy_url: str, config: Config) -> None:
        self.proxy_url = proxy_url.rstrip("/")
        self.config = config
        self._cache = self._load_cache()
        self._blocked = False

    def search(self, author: Author) -> None:
        if self._blocked:
            return

        cache_key = author.name.lower().strip()

        # 检查缓存
        cached = self._cache.get(cache_key)
        if cached and not self._is_expired(cached):
            self._apply_cached(author, cached)
            logger.info(f"  [Scholar-Proxy] 缓存命中: {author.name}")
            return

        # 额外延迟（尊重 Google 限速）
        delay = self.config.rate_limit.scholar_delay + random.uniform(0, 3)
        time.sleep(delay)

        try:
            self._do_search(author, cache_key)
        except Exception as e:
            err_str = str(e)
            if "blocked" in err_str.lower() or "rate limit" in err_str.lower():
                logger.error(f"  [Scholar-Proxy] 🚫 被限制: {e}")
                self._blocked = True
            else:
                logger.warning(f"  [Scholar-Proxy] {author.name} 搜索失败: {e}")

    def _do_search(self, author: Author, cache_key: str) -> None:
        # Step 1: 搜索作者
        search_url = (
            f"https://scholar.google.com/scholar?as_q=&as_epq=%22{urllib.parse.quote(author.name)}%22"
            f"&as_sauthors={urllib.parse.quote(author.name)}&hl=en"
        )

        html = self._proxy_fetch(search_url)
        if not html:
            return

        # 检查是否被拦截
        if "CAPTCHA" in html or "sorry" in html[:500].lower():
            self._blocked = True
            logger.error("  [Scholar-Proxy] 🚫 Google Scholar 返回 CAPTCHA")
            return

        # 尝试从搜索结果页提取 author profile 链接
        profile_match = re.search(
            r'href="(/citations\?user=[^"&]+)', html
        )

        if not profile_match:
            # 没找到 profile，缓存空结果
            self._cache[cache_key] = {"ts": time.time(), "found": False}
            self._save_cache()
            logger.info(f"  [Scholar-Proxy] {author.name}: 未找到 Scholar profile")
            return

        # Step 2: 获取 profile 详情
        profile_path = profile_match.group(1)
        profile_url = f"https://scholar.google.com{profile_path}&hl=en"

        time.sleep(3 + random.uniform(0, 2))  # 两次请求间隔
        profile_html = self._proxy_fetch(profile_url)
        if not profile_html:
            return

        # 解析 profile
        result = self._parse_profile(profile_html, profile_url, author.name)
        if result:
            author.identity.google_scholar = result
            # 用 Scholar 的机构信息补充
            if not author.affiliation and result.affiliation:
                author.affiliation = result.affiliation

            # 缓存
            self._cache[cache_key] = {
                "ts": time.time(),
                "found": True,
                "url": result.url,
                "citations": result.citations,
                "h_index": result.h_index,
                "affiliation": result.affiliation,
            }
            self._save_cache()

            logger.info(
                f"  [Scholar-Proxy] ✅ {author.name}: "
                f"citations={result.citations}, h={result.h_index}, "
                f"机构='{result.affiliation}'"
            )
        else:
            self._cache[cache_key] = {"ts": time.time(), "found": False}
            self._save_cache()

    def _proxy_fetch(self, scholar_url: str) -> Optional[str]:
        """通过 Lighthouse /scholar-proxy API 获取 Scholar 页面"""
        payload = json.dumps({"url": scholar_url}).encode("utf-8")
        req = urllib.request.Request(
            self.proxy_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                return data.get("html", "")
            else:
                logger.warning(f"  [Scholar-Proxy] 服务器返回错误: {data.get('error')}")
                return None
        except Exception as e:
            logger.warning(f"  [Scholar-Proxy] 代理请求失败: {e}")
            return None

    def _parse_profile(self, html: str, url: str, name: str) -> Optional[ScholarProfile]:
        """解析 Scholar profile 页面，提取 citations/h-index/affiliation"""
        # 验证姓名匹配
        name_match = re.search(r'id="gsc_prf_in"[^>]*>([^<]+)', html)
        if name_match:
            result_name = name_match.group(1).strip()
            if not self._name_matches(name, result_name):
                logger.debug(f"  [Scholar-Proxy] 姓名不匹配: '{name}' vs '{result_name}'")
                return None

        # 提取 Scholar ID
        scholar_id_match = re.search(r'user=([^&"]+)', url)
        scholar_id = scholar_id_match.group(1) if scholar_id_match else ""

        # 提取 citations（总引用数）
        citations = None
        # 格式：<td class="gsc_rsb_std">12345</td> (第一个是总引用)
        cite_matches = re.findall(r'class="gsc_rsb_std"[^>]*>(\d+)', html)
        if cite_matches:
            citations = int(cite_matches[0])

        # 提取 h-index
        h_index = None
        if len(cite_matches) >= 3:
            h_index = int(cite_matches[2])  # 第 3 个是 h-index

        # 提取 affiliation
        affiliation = None
        aff_match = re.search(r'class="gsc_prf_ila"[^>]*>([^<]+)', html)
        if aff_match:
            affiliation = aff_match.group(1).strip()

        return ScholarProfile(
            url=f"https://scholar.google.com/citations?user={scholar_id}" if scholar_id else url,
            citations=citations,
            h_index=h_index,
            affiliation=affiliation,
        )

    @staticmethod
    def _name_matches(query: str, result: str, threshold: float = 0.5) -> bool:
        q_tokens = set(query.lower().split())
        r_tokens = set(result.lower().split())
        if not q_tokens:
            return False
        overlap = len(q_tokens & r_tokens) / len(q_tokens)
        return overlap >= threshold

    def _load_cache(self) -> dict:
        if _CACHE_FILE.exists():
            try:
                return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_cache(self) -> None:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(
            json.dumps(self._cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _is_expired(entry: dict) -> bool:
        ts = entry.get("ts", 0)
        return (time.time() - ts) > _CACHE_TTL_DAYS * 86400

    def _apply_cached(self, author: Author, cached: dict) -> None:
        if not cached.get("found"):
            return
        author.identity.google_scholar = ScholarProfile(
            url=cached.get("url", ""),
            citations=cached.get("citations"),
            h_index=cached.get("h_index"),
            affiliation=cached.get("affiliation"),
        )
        if not author.affiliation and cached.get("affiliation"):
            author.affiliation = cached["affiliation"]
