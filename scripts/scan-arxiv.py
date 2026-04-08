"""
arXiv 每日论文扫描器
自动搜索各AI公司的最新论文，按公司分类输出JSON供网站使用
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
import sys
import time
from datetime import datetime, timedelta

# 各公司搜索关键词
COMPANY_QUERIES = {
    "huawei": {
        "name": "华为诺亚",
        "icon": "🏢",
        "keywords": ['"Huawei Noah"', '"Huawei Technologies"', '"Noah\'s Ark Lab"']
    },
    "bytedance": {
        "name": "字节Seed",
        "icon": "🌱",
        "keywords": ['"ByteDance"', '"Seed Team"', '"Doubao"']
    },
    "alibaba": {
        "name": "阿里通义",
        "icon": "☁️",
        "keywords": ['"Alibaba"', '"Tongyi"', '"Qwen"', '"DAMO Academy"']
    },
    "deepseek": {
        "name": "DeepSeek",
        "icon": "🔍",
        "keywords": ['"DeepSeek"']
    },
    "moonshot": {
        "name": "月之暗面",
        "icon": "🌙",
        "keywords": ['"Moonshot AI"', '"Kimi"', '"MoonshotAI"']
    },
    "openai": {
        "name": "OpenAI",
        "icon": "🤖",
        "keywords": ['"OpenAI"']
    },
    "deepmind": {
        "name": "Google DeepMind",
        "icon": "🧠",
        "keywords": ['"DeepMind"', '"Google DeepMind"']
    },
    "anthropic": {
        "name": "Anthropic",
        "icon": "🔬",
        "keywords": ['"Anthropic"']
    },
    "meta": {
        "name": "Meta AI",
        "icon": "📘",
        "keywords": ['"Meta AI"', '"Meta FAIR"', '"Meta Platforms"']
    },
    "nvidia": {
        "name": "NVIDIA",
        "icon": "💚",
        "keywords": ['"NVIDIA Research"', '"NVIDIA Corporation"']
    }
}

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom"
}


def search_arxiv(query, max_results=30):
    """Search arXiv API and return parsed entries"""
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    })
    url = f"{ARXIV_API}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AI-Research-Radar/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        entries = []
        for entry in root.findall("atom:entry", NS):
            title = entry.find("atom:title", NS).text.strip().replace("\n", " ")
            summary = entry.find("atom:summary", NS).text.strip().replace("\n", " ")[:300]
            published = entry.find("atom:published", NS).text.strip()
            arxiv_id = entry.find("atom:id", NS).text.strip()
            authors = [a.find("atom:name", NS).text for a in entry.findall("atom:author", NS)]
            categories = [c.get("term") for c in entry.findall("atom:category", NS)]
            # Get comment (may contain venue info)
            comment_el = entry.find("arxiv:comment", NS)
            comment = comment_el.text.strip() if comment_el is not None and comment_el.text else ""
            # PDF link
            pdf_link = ""
            for link in entry.findall("atom:link", NS):
                if link.get("title") == "pdf":
                    pdf_link = link.get("href", "")
            entries.append({
                "title": title,
                "summary": summary,
                "published": published,
                "arxivId": arxiv_id.split("/abs/")[-1] if "/abs/" in arxiv_id else arxiv_id,
                "arxivUrl": arxiv_id,
                "pdfUrl": pdf_link,
                "authors": authors[:8],  # Limit to first 8 authors
                "authorCount": len(authors),
                "categories": categories[:3],
                "comment": comment[:200]
            })
        return entries
    except Exception as e:
        print(f"  Error searching arXiv: {e}", file=sys.stderr)
        return []


def filter_by_date(entries, since_date):
    """Filter entries published on or after since_date"""
    filtered = []
    for e in entries:
        try:
            pub = datetime.fromisoformat(e["published"].replace("Z", "+00:00"))
            if pub.date() >= since_date:
                filtered.append(e)
        except:
            filtered.append(e)  # Keep if date parse fails
    return filtered


def deduplicate(entries):
    """Remove duplicate entries by arxivId"""
    seen = set()
    unique = []
    for e in entries:
        if e["arxivId"] not in seen:
            seen.add(e["arxivId"])
            unique.append(e)
    return unique


def main():
    # Date range: from April 1, 2026 (or last 7 days, whichever is more recent)
    today = datetime.now().date()
    april_1 = datetime(2026, 4, 1).date()
    since = max(april_1, today - timedelta(days=7))

    print(f"Scanning arXiv papers since {since}...")

    all_papers = {}
    for company_id, company_info in COMPANY_QUERIES.items():
        print(f"\n[{company_info['icon']}] {company_info['name']}...")
        company_papers = []

        for keyword in company_info["keywords"]:
            query = keyword
            entries = search_arxiv(query, max_results=20)
            time.sleep(3)  # arXiv rate limit: 1 request per 3 seconds
            entries = filter_by_date(entries, since)
            company_papers.extend(entries)
            print(f"  {keyword}: {len(entries)} papers found")

        # Deduplicate within company
        company_papers = deduplicate(company_papers)
        # Sort by date
        company_papers.sort(key=lambda x: x["published"], reverse=True)

        if company_papers:
            all_papers[company_id] = {
                "company": company_info["name"],
                "icon": company_info["icon"],
                "papers": company_papers,
                "count": len(company_papers)
            }
            print(f"  → Total unique: {len(company_papers)}")

    # Build output
    output = {
        "generatedAt": datetime.now().isoformat() + "Z",
        "since": since.isoformat(),
        "totalPapers": sum(c["count"] for c in all_papers.values()),
        "companies": all_papers
    }

    # Write JSON
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "..", "reports", "arxiv-daily.json")
    output_path = os.path.normpath(output_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! {output['totalPapers']} papers saved to {output_path}")


if __name__ == "__main__":
    main()
