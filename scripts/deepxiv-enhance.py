#!/usr/bin/env python3
"""
DeepXiv 增强脚本：用 DeepXiv SDK 补全 arxiv-daily.json 中论文的元数据
- TLDR 摘要
- 关键词 (keywords)
- 引用数 (citations)
- 领域分类增强 (directions)
- 校企合作检测增强：从论文 Introduction 段提取合作机构信息
"""
import json, os, sys, time, re

# Token
DEEPXIV_TOKEN = "QNSYeXO16pknnegsSpbPf4cYzCwXGYvTTlgvM8ixKYQ"

# 领域关键词映射（用于从 DeepXiv keywords 推断方向）
DIRECTION_KEYWORDS = {
    "LLM": ["language model", "LLM", "GPT", "pretraining", "fine-tuning", "RLHF", "alignment",
             "scaling law", "reasoning", "chain-of-thought", "instruction tuning", "tokenizer"],
    "Multimodal": ["multimodal", "vision-language", "image-text", "video understanding",
                   "visual grounding", "CLIP", "diffusion", "text-to-image", "image generation"],
    "Infra": ["distributed training", "inference", "quantization", "pruning", "MoE",
              "mixture of experts", "parallelism", "memory efficient", "KV cache", "speculative decoding"],
    "Speech": ["speech", "TTS", "ASR", "audio", "voice", "sound", "spoken", "acoustic",
               "music", "Seed-TTS", "Seeduplex", "duplex", "codec"],
    "Agent": ["agent", "tool use", "function calling", "planning", "autonomous"],
    "RL": ["reinforcement learning", "reward model", "PPO", "DPO", "GRPO"],
    "RAG": ["retrieval", "RAG", "knowledge base", "embedding", "vector"],
    "Safety": ["safety", "alignment", "red team", "jailbreak", "hallucination", "trustworthy"],
    "Code": ["code generation", "code review", "programming", "software engineering"],
    "Vision": ["object detection", "segmentation", "3D", "point cloud", "NeRF", "video generation"],
    "Math": ["mathematical", "theorem proving", "formal verification", "symbolic"],
    "Data": ["data curation", "synthetic data", "benchmark", "evaluation"],
}

def load_token():
    """从 .env 或环境变量加载 token"""
    token = os.environ.get("DEEPXIV_TOKEN", DEEPXIV_TOKEN)
    return token

def infer_directions_from_keywords(keywords, existing_directions):
    """从 DeepXiv 返回的关键词推断论文方向"""
    if not keywords:
        return existing_directions
    
    kw_text = " ".join(keywords).lower()
    
    # existing_directions 可能是 [{id:'LLM', label:'...'}, ...] 或 ['LLM', ...]
    existing_ids = set()
    for d in (existing_directions or []):
        if isinstance(d, dict):
            existing_ids.add(d.get("id", ""))
        elif isinstance(d, str):
            existing_ids.add(d)
    
    new_ids = set(existing_ids)
    for direction, triggers in DIRECTION_KEYWORDS.items():
        for trigger in triggers:
            if trigger.lower() in kw_text:
                new_ids.add(direction)
                break
    
    # 如果有新增方向，返回更新后的列表（保持原有 dict 格式）
    if new_ids == existing_ids:
        return existing_directions
    
    # 构建新列表，保留原有的 dict 项，新增的用简单 dict
    result = list(existing_directions or [])
    for nid in new_ids - existing_ids:
        result.append({"id": nid, "label": nid, "color": "#6b7280"})
    return result

def enhance_papers(json_path, max_papers=50, only_unenhanced=True):
    """用 DeepXiv 增强论文元数据"""
    from deepxiv_sdk import Reader, AuthenticationError, RateLimitError, NotFoundError
    
    token = load_token()
    reader = Reader(token=token)
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    enhanced_count = 0
    skipped = 0
    errors = 0
    
    for company_id, company_data in data.get("companies", {}).items():
        for paper in company_data.get("papers", []):
            arxiv_id = paper.get("arxivId", "")
            if not arxiv_id:
                continue
            
            # 去掉版本号后缀 (2604.06339v1 -> 2604.06339)
            arxiv_id_clean = re.sub(r'v\d+$', '', arxiv_id)
            
            # 跳过已增强的
            if only_unenhanced and paper.get("deepxivEnhanced"):
                skipped += 1
                continue
            
            if enhanced_count >= max_papers:
                print(f"Reached max_papers limit ({max_papers}), stopping.")
                break
            
            try:
                # 获取 brief（TLDR + 关键词 + 引用数）
                brief = reader.brief(arxiv_id_clean)
                if not brief or not isinstance(brief, dict):
                    paper["deepxivEnhanced"] = True
                    skipped += 1
                    continue
                
                # 提取数据
                tldr = brief.get("tldr", "")
                keywords = brief.get("keywords", [])
                citations = brief.get("citation_count", 0)
                github_url = brief.get("github_url", "")
                
                # 更新论文数据
                if tldr:
                    paper["tldr"] = tldr
                if keywords:
                    paper["deepxivKeywords"] = keywords
                    # 用关键词增强方向分类
                    old_dirs = paper.get("directions", [])
                    new_dirs = infer_directions_from_keywords(keywords, old_dirs)
                    if new_dirs != old_dirs:
                        paper["directions"] = new_dirs
                        print(f"  Directions: {old_dirs} -> {new_dirs}")
                if citations:
                    paper["citations"] = citations
                if github_url:
                    paper["githubUrl"] = github_url
                
                paper["deepxivEnhanced"] = True
                enhanced_count += 1
                
                title_short = (paper.get("title", ""))[:50]
                print(f"[{enhanced_count}] {company_data['company']}: {title_short}")
                print(f"  TLDR: {(tldr or '')[:80]}...")
                print(f"  Keywords: {keywords[:5]}")
                print(f"  Citations: {citations}, GitHub: {github_url or 'N/A'}")
                
                # 限速：每秒1个请求
                time.sleep(1)
                
            except NotFoundError:
                print(f"  [SKIP] {arxiv_id_clean} not found in DeepXiv")
                paper["deepxivEnhanced"] = True  # 标记为已尝试
                skipped += 1
            except RateLimitError:
                print(f"  [RATE LIMIT] Daily limit reached, stopping.")
                break
            except AuthenticationError as e:
                print(f"  [AUTH ERROR] {e}")
                break
            except Exception as e:
                err_msg = str(e)
                if "Invalid" in err_msg or "not found" in err_msg.lower() or "Bad request" in err_msg:
                    # DeepXiv 还没收录这篇论文，正常跳过
                    paper["deepxivEnhanced"] = True
                    skipped += 1
                    continue
                print(f"  [ERROR] {arxiv_id_clean}: {e}")
                errors += 1
                if errors > 20:
                    print("Too many real errors, stopping.")
                    break
        
        if enhanced_count >= max_papers:
            break
    
    # 保存
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDone! Enhanced: {enhanced_count}, Skipped: {skipped}, Errors: {errors}")
    return enhanced_count

if __name__ == "__main__":
    json_path = os.path.join(os.path.dirname(__file__), "..", "reports", "arxiv-daily.json")
    max_papers = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    enhance_papers(json_path, max_papers=max_papers)
