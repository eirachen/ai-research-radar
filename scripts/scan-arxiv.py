"""
arXiv 每日论文扫描器 v2
自动搜索各AI公司最新论文，识别高校合作（港校特别标注）、分类AI研究方向
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
import sys
import time
import re
from datetime import datetime, timedelta

# ══════════════════════════════════════
# 高校关键词库
# ══════════════════════════════════════

# 香港高校（港校特别高亮）— 仅限香港本部，不含内地分校
HK_UNIVERSITIES = {
    "University of Hong Kong": "香港大学 (HKU)",
    "HKU": "香港大学 (HKU)",
    "Chinese University of Hong Kong": "香港中文大学 (CUHK)",
    "CUHK": "香港中文大学 (CUHK)",
    "Hong Kong University of Science and Technology": "香港科技大学 (HKUST)",
    "HKUST": "香港科技大学 (HKUST)",
    "Hong Kong Polytechnic University": "香港理工大学 (PolyU)",
    "PolyU": "香港理工大学 (PolyU)",
    "City University of Hong Kong": "香港城市大学 (CityU)",
    "CityU": "香港城市大学 (CityU)",
    "Hong Kong Baptist University": "香港浸会大学 (HKBU)",
    "HKBU": "香港浸会大学 (HKBU)",
    "Lingnan University": "岭南大学",
}

# 内地分校 — 这些不算港校！匹配到这些时要排除港校标记
NOT_HK_EXCLUSIONS = [
    "shenzhen",      # CUHK-Shenzhen
    "guangzhou",     # HKUST(GZ)
    "(gz)",          # HKUST(GZ) 简写
    "深圳",           # 中文
    "广州",           # 中文
]

# 知名高校关键词（用于从 author affiliations / comment / summary 中匹配）
UNIVERSITY_KEYWORDS = [
    # 中国大陆
    "Tsinghua University", "Peking University", "Zhejiang University",
    "Shanghai Jiao Tong", "Fudan University", "Nanjing University",
    "University of Science and Technology of China", "USTC",
    "Harbin Institute of Technology", "HIT",
    "Beihang University", "Beijing Institute of Technology",
    "Sun Yat-sen University", "Wuhan University",
    "Renmin University", "Southeast University",
    "Huazhong University", "Sichuan University",
    "Xiamen University", "Tianjin University",
    "Tongji University", "Dalian University",
    "Beijing University of Posts", "BUPT",
    "Guangdong University of Technology",
    "Shenzhen University", "Southern University of Science",
    "Institute of Computing Technology", "ICT CAS",
    "Chinese Academy of Sciences", "CAS",
    "Peng Cheng Laboratory",
    # 语音方向重要高校和实验室（P3 增强）
    "Northwestern Polytechnical University", "NWPU",  # 西北工大 ASLP
    "Soochow University",  # 苏州大学
    "X-LANCE",  # 上交语音实验室
    "National Engineering Research Center for Speech",  # 中科大语音国重
    "SpeechLab",  # 各校语音实验室通用名
    # 香港 (handled separately for special highlighting)
    # 北美
    "MIT", "Massachusetts Institute of Technology",
    "Stanford University", "Stanford",
    "Carnegie Mellon", "CMU",
    "UC Berkeley", "Berkeley",
    "Princeton University", "Princeton",
    "Harvard University", "Harvard",
    "Yale University", "Columbia University",
    "University of Washington", "UW",
    "Georgia Tech", "Georgia Institute of Technology",
    "University of Michigan", "University of Illinois",
    "Cornell University", "UCLA", "USC",
    "University of Texas", "University of Maryland",
    "New York University", "NYU",
    "University of Pennsylvania", "UPenn",
    "University of Toronto", "University of Montreal",
    "McGill University", "Mila",
    "University of Waterloo", "University of Alberta",
    # 欧洲
    "University of Oxford", "Oxford",
    "University of Cambridge", "Cambridge",
    "ETH Zurich", "ETH",
    "EPFL", "Max Planck",
    "University of Edinburgh", "Imperial College",
    "UCL", "University College London",
    # 亚洲（非中国）
    "University of Tokyo", "Kyoto University",
    "Seoul National University", "KAIST",
    "National University of Singapore", "NUS",
    "Nanyang Technological University", "NTU",
    # 澳洲
    "University of Sydney", "University of Melbourne",
    "Australian National University", "ANU",
    "Monash University",
]

# ══════════════════════════════════════
# AI 研究方向分类
# ══════════════════════════════════════

AI_DIRECTIONS = {
    "LLM": {
        "label": "LLM",
        "color": "#3b82f6",
        "keywords": [
            "language model", "LLM", "GPT", "transformer", "pre-training",
            "fine-tuning", "instruction tuning", "RLHF", "alignment",
            "chat model", "text generation", "token", "decoder",
            "scaling law", "in-context learning", "prompt",
            "chain-of-thought", "reasoning model",
        ]
    },
    "Multimodal": {
        "label": "多模态",
        "color": "#a855f7",
        "keywords": [
            "multimodal", "vision-language", "VLM", "image-text",
            "visual question answering", "VQA", "image captioning",
            "video understanding", "audio-visual", "cross-modal",
            "visual grounding", "OCR", "document understanding",
        ]
    },
    "Agent": {
        "label": "Agent",
        "color": "#f97316",
        "keywords": [
            "agent", "tool use", "function calling", "planning",
            "multi-agent", "autonomous", "web agent", "code agent",
            "agentic", "task automation", "API call", "workflow",
        ]
    },
    "Infra": {
        "label": "Infra",
        "color": "#22c55e",
        "keywords": [
            "inference", "training efficiency", "quantization", "pruning",
            "distillation", "compression", "serving", "parallelism",
            "MoE", "mixture of experts", "attention mechanism",
            "memory efficient", "KV cache", "speculative decoding",
            "distributed", "GPU", "hardware", "kernel", "CUDA",
            "flash attention", "throughput", "latency",
        ]
    },
    "Vision": {
        "label": "视觉",
        "color": "#ec4899",
        "keywords": [
            "image generation", "diffusion model", "text-to-image",
            "video generation", "image editing", "object detection",
            "segmentation", "3D", "NeRF", "point cloud",
            "image classification", "visual representation",
            "image restoration", "super resolution",
        ]
    },
    "RL": {
        "label": "强化学习",
        "color": "#eab308",
        "keywords": [
            "reinforcement learning", "reward model", "GRPO",
            "PPO", "DPO", "RLHF", "policy optimization",
            "self-play", "outcome reward", "process reward",
        ]
    },
    "Safety": {
        "label": "安全",
        "color": "#ef4444",
        "keywords": [
            "safety", "alignment", "jailbreak", "red team",
            "harmful", "toxicity", "bias", "fairness",
            "watermark", "copyright", "privacy", "robustness",
            "adversarial", "backdoor", "interpretability",
        ]
    },
    "Math": {
        "label": "数学推理",
        "color": "#06b6d4",
        "keywords": [
            "mathematical reasoning", "theorem proving", "formal",
            "Lean", "proof", "math competition", "arithmetic",
            "symbolic", "equation", "geometry",
        ]
    },
    "Code": {
        "label": "代码",
        "color": "#8b5cf6",
        "keywords": [
            "code generation", "coding", "software engineering",
            "program synthesis", "code repair", "debugging",
            "repository", "SWE-bench", "code completion",
        ]
    },
    "Speech": {
        "label": "语音",
        "color": "#14b8a6",
        "keywords": [
            "speech", "ASR", "TTS", "text-to-speech", "speech-to-text",
            "voice", "audio", "spoken language", "music",
            "speech recognition", "speech synthesis", "speech generation",
            "voice conversion", "voice cloning", "speech enhancement",
            "acoustic model", "prosody", "phoneme", "vocoder",
            "mel spectrogram", "audio codec", "neural codec",
            "audio captioning", "audio understanding", "audio language model",
            "singing", "speaker diarization", "full-duplex",
            "streaming ASR", "speech token", "speech codec",
        ]
    },
    "RAG": {
        "label": "RAG/检索",
        "color": "#64748b",
        "keywords": [
            "retrieval", "RAG", "retrieval-augmented",
            "embedding", "vector", "knowledge base",
            "search", "information retrieval",
        ]
    },
    "Data": {
        "label": "数据",
        "color": "#78716c",
        "keywords": [
            "synthetic data", "data curation", "annotation",
            "benchmark", "evaluation", "dataset",
            "data quality", "contamination",
        ]
    },
}


def detect_universities(text):
    """Detect university mentions in text, return (all_unis, hk_unis).
    CRITICAL: CUHK-Shenzhen and HKUST(GZ) are NOT HK universities."""
    text_lower = text.lower()
    found_unis = set()
    found_hk = set()

    # Check HK universities — but exclude mainland campuses
    for keyword, name in HK_UNIVERSITIES.items():
        kw_lower = keyword.lower()
        pos = text_lower.find(kw_lower)
        if pos < 0:
            continue
        # Found a match — now check if it's actually a mainland campus
        # Look at surrounding context (50 chars after the match)
        context_after = text_lower[pos:pos + len(kw_lower) + 50]
        is_mainland = False
        for excl in NOT_HK_EXCLUSIONS:
            if excl in context_after:
                is_mainland = True
                break
        if is_mainland:
            # It's a mainland campus — add as regular university, NOT as HK
            if "shenzhen" in context_after or "深圳" in context_after:
                if "CUHK" in name:
                    found_unis.add("香港中文大学（深圳）(CUHK-SZ)")
                else:
                    found_unis.add(name + " (Shenzhen)")
            elif "guangzhou" in context_after or "广州" in context_after or "(gz)" in context_after:
                if "HKUST" in name:
                    found_unis.add("香港科技大学（广州）(HKUST-GZ)")
                else:
                    found_unis.add(name + " (Guangzhou)")
        else:
            # Genuine HK campus
            found_hk.add(name)
            found_unis.add(name)

    # Check other universities
    for keyword in UNIVERSITY_KEYWORDS:
        if keyword.lower() in text_lower:
            found_unis.add(keyword)

    return list(found_unis), list(found_hk)


def classify_direction(title, summary):
    """Classify paper into AI research directions based on title + summary"""
    text = (title + " " + summary).lower()
    scores = {}
    for direction_id, info in AI_DIRECTIONS.items():
        score = 0
        for kw in info["keywords"]:
            if kw.lower() in text:
                score += 1
        if score > 0:
            scores[direction_id] = score

    # Return top 3 directions sorted by score
    sorted_dirs = sorted(scores.items(), key=lambda x: -x[1])
    result = [
        {"id": d[0], "label": AI_DIRECTIONS[d[0]]["label"], "color": AI_DIRECTIONS[d[0]]["color"]}
        for d in sorted_dirs[:3]
    ]

    # 如果是 Speech 方向，追加子方向 tag
    if any(d["id"] == "Speech" for d in result):
        sub_dirs = classify_speech_subdirection(title, summary)
        for d in result:
            if d["id"] == "Speech" and sub_dirs:
                d["subTags"] = sub_dirs
    return result


# 语音子方向分类
SPEECH_SUB_DIRECTIONS = {
    "ASR": {
        "label": "语音识别",
        "keywords": ["speech recognition", "ASR", "automatic speech recognition",
                     "streaming ASR", "end-to-end ASR", "Whisper", "CTC", "transducer",
                     "speech-to-text", "dictation", "transcription"]
    },
    "TTS": {
        "label": "语音合成",
        "keywords": ["text-to-speech", "TTS", "speech synthesis", "speech generation",
                     "neural TTS", "voice synthesis", "CosyVoice", "VITS",
                     "prosody", "expressive speech", "emotional speech"]
    },
    "Speech-LLM": {
        "label": "语音大模型",
        "keywords": ["speech language model", "audio language model", "speech LLM",
                     "spoken dialogue", "speech token", "speech codec",
                     "Qwen-Audio", "full-duplex", "speech understanding",
                     "audio understanding", "listen and speak"]
    },
    "VC": {
        "label": "语音转换",
        "keywords": ["voice conversion", "voice cloning", "speaker conversion",
                     "voice style transfer", "Seed-TTS", "zero-shot TTS"]
    },
    "SE": {
        "label": "语音增强",
        "keywords": ["speech enhancement", "speech separation", "noise reduction",
                     "beamforming", "dereverberation", "speech denoising"]
    },
    "SV": {
        "label": "说话人验证",
        "keywords": ["speaker verification", "speaker recognition", "speaker diarization",
                     "speaker identification", "speaker embedding", "voiceprint"]
    },
    "Music": {
        "label": "音乐生成",
        "keywords": ["music generation", "music synthesis", "singing",
                     "singing voice", "SkyMusic", "Suno", "music composition",
                     "melody", "accompaniment"]
    },
    "Codec": {
        "label": "音频编解码",
        "keywords": ["audio codec", "neural codec", "SpeechTokenizer",
                     "audio tokenizer", "sound codec", "audio compression",
                     "mel spectrogram"]
    },
    "AudioCap": {
        "label": "音频理解",
        "keywords": ["audio captioning", "audio caption", "audio event",
                     "sound event", "audio tagging", "audio-visual",
                     "audio question answering"]
    },
}


def classify_speech_subdirection(title, summary):
    """对 Speech 方向论文进一步细分子方向"""
    text = (title + " " + summary).lower()
    found = []
    for sub_id, info in SPEECH_SUB_DIRECTIONS.items():
        for kw in info["keywords"]:
            if kw.lower() in text:
                found.append({"id": sub_id, "label": info["label"]})
                break
    return found


# ══════════════════════════════════════
# 各公司搜索关键词
# ══════════════════════════════════════

COMPANY_QUERIES = {
    "huawei": {
        "name": "华为诺亚", "icon": "🏢",
        "keywords": ['"Huawei Noah"', '"Huawei Technologies"', '"Noah\'s Ark Lab"']
    },
    "bytedance": {
        "name": "字节Seed", "icon": "🌱",
        "keywords": ['"ByteDance"', '"Seed Team"', '"Doubao"', '"Seeduplex"', '"Seed-TTS"']
    },
    "alibaba": {
        "name": "阿里通义", "icon": "☁️",
        "keywords": ['"Alibaba"', '"Tongyi"', '"Qwen"', '"DAMO Academy"']
    },
    "deepseek": {
        "name": "DeepSeek", "icon": "🔍",
        "keywords": ['"DeepSeek"']
    },
    "moonshot": {
        "name": "月之暗面", "icon": "🌙",
        "keywords": ['"Moonshot AI"', '"Kimi"', '"MoonshotAI"']
    },
    "openai": {
        "name": "OpenAI", "icon": "🤖",
        "keywords": ['"OpenAI"']
    },
    "deepmind": {
        "name": "Google DeepMind", "icon": "🧠",
        "keywords": ['"DeepMind"', '"Google DeepMind"']
    },
    "anthropic": {
        "name": "Anthropic", "icon": "🔬",
        "keywords": ['"Anthropic"']
    },
    "meta": {
        "name": "Meta AI", "icon": "📘",
        "keywords": ['"Meta AI"', '"Meta FAIR"', '"Meta Platforms"', '"GenAI Meta"']
    },
    "nvidia": {
        "name": "NVIDIA", "icon": "💚",
        "keywords": ['"NVIDIA"', '"NVIDIA Research"']
    },
    "baidu": {
        "name": "百度", "icon": "🔴",
        "keywords": ['"Baidu Research"', '"Baidu Inc"', '"ERNIE Bot"', '"Qianfan"', '"Baidu"']
    },
    "kuaishou": {
        "name": "快手", "icon": "📹",
        "keywords": ['"Kuaishou"', '"Kuaishou Technology"', '"KwaiVGI"']
    },
    "didi": {
        "name": "滴滴", "icon": "🚕",
        "keywords": ['"DiDi Chuxing"', '"DiDi Global"']
    },
    "xiaomi": {
        "name": "小米", "icon": "📱",
        "keywords": ['"Xiaomi"', '"Xiaomi AI Lab"']
    },
    "stepfun": {
        "name": "阶跃星辰", "icon": "⭐",
        "keywords": ['"StepFun"', '"Step AI"', '"stepfun-ai"']
    },
    "taotian": {
        "name": "阿里淘天", "icon": "🛒",
        "keywords": ['"Taobao"', '"Alibaba Taotian"']
    },
    "antgroup": {
        "name": "蚂蚁集团", "icon": "🐜",
        "keywords": ['"Ant Group"', '"Ant Financial"', '"AntGroup"']
    },
    # ══ 语音专项监控公司（只关注语音方向）══
    "kunlun": {
        "name": "昆仑万维", "icon": "🏔️",
        "keywords": ['"Kunlun Tech"', '"SkyMusic"', '"Kunlun"'],
        "speech_only": True  # 标记：只保留语音相关论文
    },
    "suno": {
        "name": "Suno", "icon": "🎵",
        "keywords": ['"Suno"', '"Suno AI"'],
        "speech_only": True
    },
    "minimax": {
        "name": "MiniMax", "icon": "🔊",
        "keywords": ['"MiniMax"', '"Hailuo"'],
        "speech_only": True
    },
    "iflytek": {
        "name": "科大讯飞", "icon": "🗣️",
        "keywords": ['"iFLYTEK"', '"IFLYTEK"', '"Xunfei"'],
        "speech_only": True
    },
}

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom"
}


def search_arxiv(query, max_results=30):
    """Search arXiv API and return parsed entries (with retry on 429)"""
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    })
    url = f"{ARXIV_API}?{params}"
    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AI-Research-Radar/2.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)
            entries = []
            for entry in root.findall("atom:entry", NS):
                title = entry.find("atom:title", NS).text.strip().replace("\n", " ")
                full_summary = entry.find("atom:summary", NS).text.strip().replace("\n", " ")
                summary = full_summary[:300]
                published = entry.find("atom:published", NS).text.strip()
                arxiv_id = entry.find("atom:id", NS).text.strip()
                authors = [a.find("atom:name", NS).text for a in entry.findall("atom:author", NS)]

                # Get author affiliations (arxiv namespace)
                affiliations = []
                for a in entry.findall("atom:author", NS):
                    for aff in a.findall("arxiv:affiliation", NS):
                        if aff.text:
                            affiliations.append(aff.text.strip())

                categories = [c.get("term") for c in entry.findall("atom:category", NS)]
                comment_el = entry.find("arxiv:comment", NS)
                comment = comment_el.text.strip() if comment_el is not None and comment_el.text else ""
                pdf_link = ""
                for link in entry.findall("atom:link", NS):
                    if link.get("title") == "pdf":
                        pdf_link = link.get("href", "")

                # === NEW: Detect universities ===
                detect_text = " ".join(affiliations) + " " + comment + " " + full_summary + " " + " ".join(authors)
                all_unis, hk_unis = detect_universities(detect_text)

                # === NEW: Classify AI direction ===
                directions = classify_direction(title, full_summary)

                entries.append({
                    "title": title,
                    "summary": summary,
                    "published": published,
                    "arxivId": arxiv_id.split("/abs/")[-1] if "/abs/" in arxiv_id else arxiv_id,
                    "arxivUrl": arxiv_id,
                    "pdfUrl": pdf_link,
                    "authors": authors[:8],
                    "authorCount": len(authors),
                    "affiliations": affiliations[:10],
                    "categories": categories[:3],
                    "comment": comment[:200],
                    "universities": all_unis,
                    "hkUniversities": hk_unis,
                    "hasUniCollab": len(all_unis) > 0,
                    "hasHKCollab": len(hk_unis) > 0,
                    "directions": directions,
                    "collabConfidence": "confirmed" if affiliations else ("mentioned" if all_unis else "none"),
                    "pdfVerified": False,
                })
            return entries
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries:
                wait = 30 * (attempt + 1)
                print(f"  429 rate-limited, waiting {wait}s (retry {attempt+1}/{max_retries})...", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  Error: {e}", file=sys.stderr)
            return []
        except Exception as e:
            if attempt < max_retries:
                wait = 15 * (attempt + 1)
                print(f"  Error: {e}, waiting {wait}s (retry {attempt+1}/{max_retries})...", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  Error: {e}", file=sys.stderr)
            return []
    return []


def filter_by_date(entries, since_date):
    filtered = []
    for e in entries:
        try:
            pub = datetime.fromisoformat(e["published"].replace("Z", "+00:00"))
            if pub.date() >= since_date:
                filtered.append(e)
        except:
            filtered.append(e)
    return filtered


def deduplicate(entries):
    seen = set()
    unique = []
    for e in entries:
        if e["arxivId"] not in seen:
            seen.add(e["arxivId"])
            unique.append(e)
    return unique


def main():
    today = datetime.now().date()
    since = today - timedelta(days=7)

    print(f"Scanning arXiv papers since {since}...")

    # Load existing data to merge (incremental mode)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "..", "reports", "arxiv-daily.json")
    output_path = os.path.normpath(output_path)
    existing_data = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            print(f"Loaded existing data: {existing_data.get('totalPapers', 0)} papers")
        except:
            pass

    all_papers = {}
    total_uni = 0
    total_hk = 0

    for company_id, company_info in COMPANY_QUERIES.items():
        print(f"\n[{company_info['icon']}] {company_info['name']}...")
        company_papers = []

        for keyword in company_info["keywords"]:
            entries = search_arxiv(keyword, max_results=20)
            time.sleep(3)
            entries = filter_by_date(entries, since)
            company_papers.extend(entries)
            print(f"  {keyword}: {len(entries)} papers")

        company_papers = deduplicate(company_papers)
        company_papers.sort(key=lambda x: x["published"], reverse=True)

        # For speech_only companies, filter to keep only speech-related papers
        if company_info.get("speech_only"):
            speech_kws = AI_DIRECTIONS["Speech"]["keywords"]
            before = len(company_papers)
            company_papers = [
                p for p in company_papers
                if any(d["id"] == "Speech" for d in p.get("directions", []))
                or any(kw.lower() in (p["title"] + " " + p["summary"]).lower() for kw in speech_kws)
            ]
            if before != len(company_papers):
                print(f"  [speech_only] filtered {before} -> {len(company_papers)}")

        uni_count = sum(1 for p in company_papers if p["hasUniCollab"])
        hk_count = sum(1 for p in company_papers if p["hasHKCollab"])
        total_uni += uni_count
        total_hk += hk_count

        if company_papers:
            all_papers[company_id] = {
                "company": company_info["name"],
                "icon": company_info["icon"],
                "papers": company_papers,
                "count": len(company_papers),
                "uniCollabCount": uni_count,
                "hkCollabCount": hk_count,
            }
            print(f"  -> {len(company_papers)} unique, {uni_count} uni-collab, {hk_count} HK-collab")

    # Merge with existing data (keep old papers, add new ones)
    # CRITICAL: preserve PDF verification fields from old data
    if existing_data.get("companies"):
        for company_id, existing_company in existing_data["companies"].items():
            if company_id in all_papers:
                # Build lookup of old papers by arxivId
                old_papers_map = {p["arxivId"]: p for p in existing_company.get("papers", [])}
                # For new papers that also exist in old data, preserve PDF verification fields
                for new_paper in all_papers[company_id]["papers"]:
                    old_paper = old_papers_map.get(new_paper["arxivId"])
                    if old_paper:
                        # Preserve all PDF verification data from old paper
                        for field in ["pdfVerified", "pdfCompanies", "pdfUnis", "pdfHKUnis", "collabConfidence"]:
                            if old_paper.get(field) is not None and field in old_paper:
                                # Only preserve if old data had real verification
                                if field == "pdfVerified" and old_paper[field]:
                                    new_paper[field] = old_paper[field]
                                elif field == "collabConfidence" and old_paper.get("pdfVerified"):
                                    new_paper[field] = old_paper[field]
                                elif field not in ("pdfVerified", "collabConfidence") and old_paper.get("pdfVerified"):
                                    new_paper[field] = old_paper[field]
                        # Also preserve corrected university fields from fix-unis
                        if old_paper.get("pdfVerified"):
                            for field in ["universities", "hkUniversities", "hasUniCollab", "hasHKCollab"]:
                                if field in old_paper:
                                    new_paper[field] = old_paper[field]
                # Add old papers that aren't in new scan
                new_ids = {p["arxivId"] for p in all_papers[company_id]["papers"]}
                for old_paper in existing_company.get("papers", []):
                    if old_paper["arxivId"] not in new_ids:
                        all_papers[company_id]["papers"].append(old_paper)
                # Re-sort and update counts
                all_papers[company_id]["papers"].sort(key=lambda x: x["published"], reverse=True)
                all_papers[company_id]["count"] = len(all_papers[company_id]["papers"])
                all_papers[company_id]["uniCollabCount"] = sum(1 for p in all_papers[company_id]["papers"] if p.get("hasUniCollab"))
                all_papers[company_id]["hkCollabCount"] = sum(1 for p in all_papers[company_id]["papers"] if p.get("hasHKCollab"))
            elif existing_company.get("papers"):
                # Company not in new scan, keep old data entirely
                all_papers[company_id] = existing_company

    # Recalculate totals
    total_uni = sum(c.get("uniCollabCount", 0) for c in all_papers.values())
    total_hk = sum(c.get("hkCollabCount", 0) for c in all_papers.values())

    # Use earliest 'since' date
    old_since = existing_data.get("since", since.isoformat())
    final_since = min(old_since, since.isoformat())

    output = {
        "generatedAt": datetime.now().isoformat() + "Z",
        "since": final_since,
        "totalPapers": sum(c["count"] for c in all_papers.values()),
        "totalUniCollab": total_uni,
        "totalHKCollab": total_hk,
        "companies": all_papers
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "..", "reports", "arxiv-daily.json")
    output_path = os.path.normpath(output_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== Done! {output['totalPapers']} papers, {total_uni} uni-collab, {total_hk} HK-collab ===")


if __name__ == "__main__":
    main()
