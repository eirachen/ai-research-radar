"""
手动添加 2026-04-14 发现的新论文到 arxiv-daily.json
arXiv API 被 429 限流，改用 web fetch + PDF verification 获取
"""
import json
import os
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "..", "reports", "arxiv-daily.json")
json_path = os.path.normpath(json_path)

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# New papers found via web fetch on 2026-04-14
# All PDF-verified for affiliations
new_papers = [
    # ---- InsEdit: HKUST + CityU + Celia Research HK ----
    {
        "company_id": "alibaba",  # 基于 HunyuanVideo（腾讯）但不属于任何现有分类，暂不归入公司
        "skip": True,
        "note": "InsEdit 基于 HunyuanVideo-1.5 但由 HKUST/CityU/Celia 独立完成，非腾讯论文"
    },
    # ---- TAIHRI: Tencent Robotics X + 清华深圳 ----
    # 腾讯不在我们监控列表中，但与清华合作值得记录
    {
        "company_id": "taihri_skip",
        "skip": True,
        "note": "TAIHRI 是腾讯 Robotics X 论文，腾讯目前不在监控公司列表中"
    },
    # ---- PhysInOne: PolyU + Meta ----
    {
        "company_id": "meta",
        "paper": {
            "title": "PhysInOne: Visual Physics Learning and Reasoning in One Suite",
            "summary": "We present PhysInOne, a large-scale synthetic dataset addressing the critical scarcity of physically-grounded training data for AI systems. PhysInOne provides 2 million videos across 153,810 dynamic 3D scenes, covering 71 basic physical phenomena in mechanics, optics, fluid dynamics, and magnetism.",
            "published": "2026-04-10T15:27:27Z",
            "arxivId": "2604.09415v1",
            "arxivUrl": "http://arxiv.org/abs/2604.09415v1",
            "pdfUrl": "https://arxiv.org/pdf/2604.09415v1",
            "authors": ["Siyuan Zhou", "Hejun Wang", "Hu Cheng", "Jinxi Li", "Dongsheng Wang", "Junwei Jiang", "Bo Yang", "Chuhang Zou"],
            "authorCount": 39,
            "affiliations": ["Hong Kong Polytechnic University", "Meta"],
            "categories": ["cs.CV", "cs.AI", "cs.LG"],
            "comment": "CVPR 2026. 2M videos, 153K 3D scenes, 71 physical phenomena",
            "universities": ["香港理工大学 (PolyU)"],
            "hkUniversities": ["香港理工大学 (PolyU)"],
            "hasUniCollab": True,
            "hasHKCollab": True,
            "directions": [
                {"id": "Vision", "label": "视觉", "color": "#a855f7"},
                {"id": "Data", "label": "数据", "color": "#64748b"},
                {"id": "Multimodal", "label": "多模态", "color": "#ec4899"}
            ],
            "collabConfidence": "confirmed",
            "pdfVerified": True,
            "pdfCompanies": ["Meta"],
            "pdfUnis": ["Hong Kong Polytechnic University", "Syai Singapore"],
            "pdfHKUnis": ["Hong Kong Polytechnic University"]
        }
    },
    # ---- DACO: CVPR 2026 多校合作 (tested on QwenVL) ----
    # 仅使用 QwenVL 做实验，非阿里直接论文，跳过公司归类
    {
        "company_id": "daco_skip",
        "skip": True,
        "note": "DACO CVPR2026 仅使用 QwenVL 评测，非阿里直接论文"
    },
]

# 纯港校论文（非公司论文但港校相关，记入日报但不归入公司 JSON）
hk_only_papers = [
    {
        "title": "InsEdit: Towards Instruction-based Visual Editing via Data-Efficient Video Diffusion Models Adaptation",
        "arxivId": "2604.08646v1",
        "published": "2026-04-09T17:59:02Z",
        "affiliations": ["HKUST", "Celia Research HK", "CityU"],
        "hkUniversities": ["香港科技大学 (HKUST)", "香港城市大学 (CityU)"],
        "authors": ["Zhefan Rao", "Bin Zou", "Haoxuan Che", "Xuanhua He", "Chong Hou Choi", "Yanheng Li", "Rui Liu", "Qifeng Chen"],
        "pdfVerified": True,
        "note": "HKUST 陈启峰团队 + CityU + Celia Research HK，基于 HunyuanVideo-1.5 做视频编辑"
    },
    {
        "title": "Strips as Tokens: Artist Mesh Generation with Native UV Segmentation",
        "arxivId": "2604.09132v1",
        "published": "2026-04-10T09:13:09Z",
        "affiliations": ["HKU", "ShanghaiTech", "Shandong University", "Texas A&M", "Deemos Technology"],
        "hkUniversities": ["香港大学 (HKU)"],
        "authors": ["Rui Xu", "Dafei Qin", "Kaichun Qiao", "Taku Komura"],
        "pdfVerified": True,
        "note": "HKU Taku Komura 团队，ACM TOG，3D mesh 生成"
    },
    {
        "title": "AniGen: Unified S3 Fields for Animatable 3D Asset Generation",
        "arxivId": "2604.08746v1",
        "published": "2026-04-09T20:22:06Z",
        "affiliations": ["HKU", "VAST", "CUHK", "Tsinghua"],
        "hkUniversities": ["香港大学 (HKU)", "香港中文大学 (CUHK)"],
        "authors": ["Yi-Hua Huang", "Zi-Xin Zou", "Yuting He", "Xiaojuan Qi"],
        "pdfVerified": True,
        "note": "HKU 戚晓娟团队 + VAST + CUHK 何雨婷，ACM TOG，可动画3D生成"
    },
]

# Add PhysInOne to meta
for item in new_papers:
    if item.get("skip"):
        continue
    cid = item["company_id"]
    paper = item["paper"]
    
    if cid in data["companies"]:
        # Check if paper already exists
        existing_ids = {p["arxivId"] for p in data["companies"][cid]["papers"]}
        if paper["arxivId"] not in existing_ids:
            data["companies"][cid]["papers"].insert(0, paper)
            data["companies"][cid]["papers"].sort(key=lambda x: x["published"], reverse=True)
            data["companies"][cid]["count"] = len(data["companies"][cid]["papers"])
            data["companies"][cid]["uniCollabCount"] = sum(1 for p in data["companies"][cid]["papers"] if p.get("hasUniCollab"))
            data["companies"][cid]["hkCollabCount"] = sum(1 for p in data["companies"][cid]["papers"] if p.get("hasHKCollab"))
            print(f"Added {paper['arxivId']} to {cid}")
        else:
            print(f"Skipped {paper['arxivId']} (already in {cid})")
    else:
        print(f"Company {cid} not found in data")

# Recalculate totals
data["totalPapers"] = sum(c["count"] for c in data["companies"].values())
data["totalUniCollab"] = sum(c.get("uniCollabCount", 0) for c in data["companies"].values())
data["totalHKCollab"] = sum(c.get("hkCollabCount", 0) for c in data["companies"].values())
data["generatedAt"] = datetime.now().isoformat() + "Z"

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nUpdated: {data['totalPapers']} papers, {data['totalUniCollab']} uni, {data['totalHKCollab']} HK")
print(f"\nHK-only papers found (not in company list):")
for p in hk_only_papers:
    print(f"  - {p['title']} ({', '.join(p['hkUniversities'])})")
