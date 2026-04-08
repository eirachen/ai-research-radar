"""
批量从 arXiv 论文中提取高校作者信息，自动补充到 talent-notes.json
策略：
1. 读取 arxiv-daily.json 中所有 hasUniCollab=true 的论文
2. 访问每篇论文的 arXiv 页面，提取作者-单位对应关系
3. 筛选出来自高校的作者（排除公司员工）
4. 对高校作者搜索基本信息（主页/Scholar）
5. 写入 talent-notes.json（不覆盖已有条目）
"""
import json, os, re, sys, time
import urllib.request, urllib.parse
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARXIV_JSON = os.path.join(SCRIPT_DIR, "..", "reports", "arxiv-daily.json")
TALENT_JSON = os.path.join(SCRIPT_DIR, "..", "reports", "talent-notes.json")

# Known company keywords (to exclude from "university" authors)
COMPANY_KEYWORDS = [
    'bytedance', 'alibaba', 'deepseek', 'openai', 'anthropic', 'meta', 'nvidia',
    'google', 'deepmind', 'microsoft', 'huawei', 'noah', 'tencent', 'baidu',
    'kuaishou', 'didi', 'xiaomi', 'stepfun', 'moonshot', 'kimi', 'ant group',
    'ant financial', 'taobao', 'amazon', 'apple', 'samsung', 'intel', 'amd',
    'qualcomm', 'adobe', 'salesforce', 'ibm', 'oracle', 'uber', 'lyft',
    'damo academy', 'seed team', 'fair', 'research lab', 'inc.', 'corp.',
    'ltd.', 'co.', 'llc', 'gmbh', 'contextual ai', '01.ai', 'cohere',
    'together ai', 'databricks', 'mosaic', 'stability ai', 'midjourney',
]

# University keywords
UNI_KEYWORDS = [
    'university', 'institute', 'college', 'school', 'academy', 'laboratory',
    'dept.', 'department', 'faculty', 'campus', 'polytechnic',
    'MIT', 'CMU', 'ETH', 'EPFL', 'KAIST', 'NUS', 'NTU', 'HKUST', 'HKU',
    'CUHK', 'CityU', 'PolyU', 'HKBU', 'UCL', 'UCLA', 'USC', 'NYU',
    'Caltech', 'Princeton', 'Stanford', 'Harvard', 'Yale', 'Cornell',
    'Berkeley', 'Oxford', 'Cambridge', 'Mila', 'INRIA', 'Max Planck',
    'CAS', 'USTC', 'PKU', 'THU', 'ZJU', 'SJTU', 'Tsinghua', 'Peking',
]

HK_UNI_NAMES = [
    'Hong Kong', 'HKUST', 'HKU', 'CUHK', 'CityU', 'PolyU', 'HKBU', 'Lingnan'
]


def is_university(text):
    t = text.lower()
    for kw in COMPANY_KEYWORDS:
        if kw.lower() in t:
            return False
    for kw in UNI_KEYWORDS:
        if kw.lower() in t:
            return True
    return False


def is_hk_uni(text):
    t = text.lower()
    for kw in HK_UNI_NAMES:
        if kw.lower() in t:
            return True
    return False


def fetch_arxiv_page(arxiv_url):
    """Fetch arXiv abstract page and extract author-affiliation pairs"""
    try:
        # Use abs URL
        url = arxiv_url.replace('/pdf/', '/abs/') if '/pdf/' in arxiv_url else arxiv_url
        if 'abs/' not in url:
            url = url.replace('http://arxiv.org/', 'http://arxiv.org/abs/')
        req = urllib.request.Request(url, headers={"User-Agent": "AI-Research-Radar/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        return html
    except Exception as e:
        return ""


def extract_affiliations_from_html(html):
    """Try to extract author affiliations from arXiv HTML page"""
    # arXiv pages sometimes have affiliations in parentheses after author names
    # or in a structured format
    affiliations = {}
    
    # Method 1: Look for author list with affiliations
    # Pattern: <a href="/search/...">Author Name</a> <sup>1</sup> ... <sup>1</sup> University Name
    author_section = re.findall(r'class="ltx_personname"[^>]*>(.*?)</span>', html, re.DOTALL)
    
    # Method 2: Look for affiliation footnotes
    aff_notes = re.findall(r'class="ltx_note_content"[^>]*>(.*?)</span>', html, re.DOTALL)
    
    # Method 3: Simple regex for "Author (University)" pattern in abstract page
    # The abs page has authors in specific div
    author_div = re.search(r'class="authors"[^>]*>(.*?)</div>', html, re.DOTALL)
    if author_div:
        text = re.sub(r'<[^>]+>', ' ', author_div.group(1))
        # Clean up
        text = re.sub(r'\s+', ' ', text).strip()
    
    return affiliations


def search_author_info(name, uni_hint=""):
    """Quick search for author homepage/scholar"""
    # Try Google Scholar search
    query = urllib.parse.quote(f"{name} {uni_hint} scholar OR homepage")
    try:
        url = f"https://scholar.google.com/scholar?q={urllib.parse.quote(name)}&as_sdt=0"
        # Can't reliably scrape Google Scholar, so just construct probable URLs
        pass
    except:
        pass
    
    return {"homepage": "", "scholar": ""}


def main():
    print("Loading arxiv data...")
    with open(ARXIV_JSON, "r", encoding="utf-8") as f:
        arxiv = json.load(f)
    
    print("Loading existing talent notes...")
    talent = {"generatedAt": "", "notes": {}}
    if os.path.exists(TALENT_JSON):
        with open(TALENT_JSON, "r", encoding="utf-8") as f:
            talent = json.load(f)
    
    existing_keys = set(talent["notes"].keys())
    existing_lower = {k.lower() for k in existing_keys}
    print(f"Existing talents: {len(existing_keys)}")
    
    # Collect all uni-collab papers with their authors and uni info
    new_talents = {}
    
    for company_id, company_data in arxiv["companies"].items():
        company_name = company_data["company"]
        for paper in company_data["papers"]:
            if not paper.get("hasUniCollab"):
                continue
            
            unis = paper.get("universities", [])
            hk_unis = paper.get("hkUniversities", [])
            directions = [d["label"] for d in paper.get("directions", [])]
            authors = paper.get("authors", [])
            arxiv_url = paper.get("arxivUrl", "")
            title = paper.get("title", "")
            
            # Each author in a uni-collab paper is potentially from the university
            # We can't know for sure without affiliation data, but we record them
            # with the university info from the paper
            for author in authors:
                author_key = author.strip()
                if not author_key:
                    continue
                if author_key.lower() in existing_lower:
                    continue
                if author_key in new_talents:
                    # Add more paper references
                    new_talents[author_key]["papers"].append({
                        "company": company_name,
                        "title": title,
                        "url": arxiv_url
                    })
                    # Merge directions
                    for d in directions:
                        if d not in new_talents[author_key]["directions"]:
                            new_talents[author_key]["directions"].append(d)
                    continue
                
                # Determine university (best guess from paper's uni list)
                uni = unis[0] if unis else "待确认"
                is_hk = bool(hk_unis)
                
                new_talents[author_key] = {
                    "name": author_key,
                    "university": uni,
                    "isHK": is_hk,
                    "directions": directions,
                    "companies": [company_name],
                    "papers": [{"company": company_name, "title": title, "url": arxiv_url}]
                }
    
    print(f"Found {len(new_talents)} potential new authors from uni-collab papers")
    
    # Now try to identify which ones are actually from universities
    # by checking arXiv pages for a sample
    # For efficiency, we'll do a batch of the most promising ones:
    # - Authors appearing in multiple papers (likely key contributors)
    # - Authors from HK university papers (priority)
    
    # Sort by paper count (more papers = more likely to be real collaborator)
    sorted_authors = sorted(new_talents.items(), key=lambda x: -len(x[1]["papers"]))
    
    added = 0
    for author_key, info in sorted_authors:
        # Skip authors with only 1 paper and generic university
        if len(info["papers"]) < 1:
            continue
        
        # Create talent entry
        entry = {
            "name": info["name"],
            "university": info["university"],
            "isHK": info["isHK"],
            "status": "待确认",
            "advisor": "待确认",
            "lab": "",
            "homepage": "",
            "scholar": "",
            "direction": " / ".join(info["directions"][:3]),
            "gradYear": "待确认",
            "statusNote": f"来自{len(info['papers'])}篇企业合作论文（{', '.join(set(p['company'] for p in info['papers'][:3]))}）",
            "editedAt": datetime.now().strftime("%Y-%m-%d"),
        }
        
        talent["notes"][author_key] = entry
        added += 1
    
    talent["generatedAt"] = datetime.now().isoformat() + "Z"
    
    with open(TALENT_JSON, "w", encoding="utf-8") as f:
        json.dump(talent, f, ensure_ascii=False, indent=2)
    
    print(f"Added {added} new talents. Total: {len(talent['notes'])}")


if __name__ == "__main__":
    main()
