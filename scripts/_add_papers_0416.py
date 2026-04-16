"""
2026-04-16 增量更新脚本
arXiv API 被 429 限流，手动添加通过 RSS feed 和网页发现的新论文
"""
import json, os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARXIV_JSON = os.path.join(SCRIPT_DIR, "..", "reports", "arxiv-daily.json")

# 新论文数据（来自 arXiv RSS feed + 网页 4/15-4/16）
NEW_PAPERS = {
    "bytedance": [
        {
            "title": "Seedance 2.0: Advancing Video Generation for World Complexity",
            "summary": "Seedance 2.0 is a new native multimodal audio-video generation model. It adopts a unified, efficient, large-scale multimodal joint audio-video generation architecture supporting text, image, audio and video inputs with comprehensive multimodal content reference and editing capabilities.",
            "published": "2026-04-15T17:59:40Z",
            "arxivId": "2604.14148",
            "arxivUrl": "https://arxiv.org/abs/2604.14148",
            "pdfUrl": "https://arxiv.org/pdf/2604.14148",
            "authors": ["Team Seedance", "De Chen", "Liyang Chen", "Xin Chen", "Feng Cheng", "Jie Wu"],
            "authorCount": 171,
            "affiliations": ["ByteDance"],
            "categories": ["cs.CV"],
            "comment": "",
            "universities": [],
            "hkUniversities": [],
            "hasUniCollab": False,
            "hasHKCollab": False,
            "directions": [
                {"id": "Vision", "label": "视觉", "color": "#ec4899"},
                {"id": "Multimodal", "label": "多模态", "color": "#a855f7"},
                {"id": "Speech", "label": "语音", "color": "#14b8a6",
                 "subTags": [{"id": "Codec", "label": "音频编解码"}]}
            ],
            "collabConfidence": "none",
            "pdfVerified": False,
        },
        {
            "title": "SparseBalance: Load-Balanced Long Context Training with Dynamic Sparse Attention",
            "summary": "Sparse attention alleviates computational bottlenecks in long-context LLM training but exhibits extreme heterogeneity in distributed training. We propose SparseBalance, a novel algorithm-system co-design framework achieving up to 1.33x end-to-end training speedup.",
            "published": "2026-04-15T13:18:07Z",
            "arxivId": "2604.13847",
            "arxivUrl": "https://arxiv.org/abs/2604.13847",
            "pdfUrl": "https://arxiv.org/pdf/2604.13847",
            "authors": ["Hongtao Xu", "Jianchao Tan", "Yuxuan Hu", "Pengju Lu", "Hongyu Wang", "Xunliang Cai", "Mingzhen Li", "Weile Jia"],
            "authorCount": 11,
            "affiliations": ["ByteDance"],
            "categories": ["cs.LG", "cs.AI"],
            "comment": "",
            "universities": [],
            "hkUniversities": [],
            "hasUniCollab": False,
            "hasHKCollab": False,
            "directions": [
                {"id": "Infra", "label": "Infra", "color": "#22c55e"},
                {"id": "LLM", "label": "LLM", "color": "#3b82f6"}
            ],
            "collabConfidence": "none",
            "pdfVerified": False,
        },
    ],
    "alibaba": [
        {
            "title": "YOCO++: Enhancing YOCO with KV Residual Connections for Efficient LLM Inference",
            "summary": "Cross-layer key-value (KV) compression has proven effective for efficient LLM inference. We propose YOCO++, adding weighted residual connections to YOCO. At 50% KV cache compression, YOCO++ achieves state-of-the-art and surpasses standard Transformer.",
            "published": "2026-04-15T07:05:14Z",
            "arxivId": "2604.13556",
            "arxivUrl": "https://arxiv.org/abs/2604.13556",
            "pdfUrl": "https://arxiv.org/pdf/2604.13556",
            "authors": ["You Wu", "Ziheng Chen", "Yizhen Zhang", "Haoyi Wu", "Chengting Yu", "Yuchi Xu", "Wenbo Su", "Bo Zheng", "Kewei Tu"],
            "authorCount": 9,
            "affiliations": ["Alibaba DAMO Academy", "ShanghaiTech University"],
            "categories": ["cs.CL"],
            "comment": "",
            "universities": ["ShanghaiTech University"],
            "hkUniversities": [],
            "hasUniCollab": True,
            "hasHKCollab": False,
            "directions": [
                {"id": "Infra", "label": "Infra", "color": "#22c55e"},
                {"id": "LLM", "label": "LLM", "color": "#3b82f6"}
            ],
            "collabConfidence": "mentioned",
            "pdfVerified": False,
        },
        {
            "title": "Correct Prediction, Wrong Steps? Consensus Reasoning Knowledge Graph for Robust Chain-of-Thought Synthesis",
            "summary": "We address the fundamental challenge of ensuring reasoning quality in chain-of-thought synthesis. We propose Consensus Reasoning Knowledge Graph (CRKG) that distills collective reasoning patterns from multiple expert models to generate robustly correct reasoning chains.",
            "published": "2026-04-15T17:55:00Z",
            "arxivId": "2604.14121",
            "arxivUrl": "https://arxiv.org/abs/2604.14121",
            "pdfUrl": "https://arxiv.org/pdf/2604.14121",
            "authors": ["Zipeng Ling", "Shuliang Liu", "Shenghong Fu", "Yuehao Tang", "Seonil Son", "Yao Wan", "Xuming Hu"],
            "authorCount": 7,
            "affiliations": [],
            "categories": ["cs.CL"],
            "comment": "",
            "universities": ["香港科技大学（广州）(HKUST-GZ)"],
            "hkUniversities": [],
            "hasUniCollab": True,
            "hasHKCollab": False,
            "directions": [
                {"id": "LLM", "label": "LLM", "color": "#3b82f6"},
                {"id": "RAG", "label": "RAG/检索", "color": "#64748b"}
            ],
            "collabConfidence": "mentioned",
            "pdfVerified": False,
        },
    ],
    "deepmind": [
        {
            "title": "HiVLA: A Visual-Grounded-Centric Hierarchical Embodied Manipulation System",
            "summary": "We propose HiVLA, a visual-grounded-centric hierarchical framework that explicitly decouples high-level semantic planning from low-level motor control. HiVLA significantly outperforms state-of-the-art end-to-end baselines on long-horizon skill composition and fine manipulation.",
            "published": "2026-04-15T17:50:07Z",
            "arxivId": "2604.14125",
            "arxivUrl": "https://arxiv.org/abs/2604.14125",
            "pdfUrl": "https://arxiv.org/pdf/2604.14125",
            "authors": ["Tianshuo Yang", "Guanyu Chen", "Yutian Chen", "Zhixuan Liang", "Yitian Liu", "Zanxin Chen", "Chunpu Xu", "Haotian Liang", "Jiangmiao Pang", "Yao Mu", "Ping Luo"],
            "authorCount": 11,
            "affiliations": [],
            "categories": ["cs.CV", "cs.AI", "cs.RO"],
            "comment": "",
            "universities": ["香港大学 (HKU)"],
            "hkUniversities": ["香港大学 (HKU)"],
            "hasUniCollab": True,
            "hasHKCollab": True,
            "directions": [
                {"id": "Agent", "label": "Agent", "color": "#f97316"},
                {"id": "Vision", "label": "视觉", "color": "#ec4899"},
                {"id": "Multimodal", "label": "多模态", "color": "#a855f7"}
            ],
            "collabConfidence": "mentioned",
            "pdfVerified": False,
        },
    ],
}


def main():
    with open(ARXIV_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    added_total = 0

    for company_id, papers in NEW_PAPERS.items():
        if company_id not in data["companies"]:
            print(f"  WARNING: company '{company_id}' not in data, skipping")
            continue

        existing_ids = {p["arxivId"] for p in data["companies"][company_id]["papers"]}

        for paper in papers:
            if paper["arxivId"] in existing_ids:
                print(f"  SKIP (exists): {paper['arxivId']} {paper['title'][:50]}")
                continue

            data["companies"][company_id]["papers"].insert(0, paper)
            added_total += 1
            print(f"  + ADD [{company_id}]: {paper['arxivId']} {paper['title'][:50]}")

        # Recalculate counts
        company = data["companies"][company_id]
        company["count"] = len(company["papers"])
        company["uniCollabCount"] = sum(1 for p in company["papers"] if p.get("hasUniCollab"))
        company["hkCollabCount"] = sum(1 for p in company["papers"] if p.get("hasHKCollab"))

    # Update totals
    data["totalPapers"] = sum(c["count"] for c in data["companies"].values())
    data["totalUniCollab"] = sum(c.get("uniCollabCount", 0) for c in data["companies"].values())
    data["totalHKCollab"] = sum(c.get("hkCollabCount", 0) for c in data["companies"].values())
    data["generatedAt"] = datetime.now().isoformat() + "Z"

    with open(ARXIV_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nDone! +{added_total} papers. Total: {data['totalPapers']}")


if __name__ == "__main__":
    main()
