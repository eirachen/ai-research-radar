"""
2026-04-16 归属修正 + universities 修正脚本
根据 PDF 验证结果修正 arxiv-daily.json
"""
import json, os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARXIV_JSON = os.path.join(SCRIPT_DIR, "..", "reports", "arxiv-daily.json")

def find_paper(data, arxiv_id):
    """Find paper by arxivId across all companies"""
    for cid, cdata in data["companies"].items():
        for p in cdata["papers"]:
            if p["arxivId"] == arxiv_id:
                return p, cid
    return None, None

def main():
    with open(ARXIV_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    fixes = 0

    # Fix 1: SparseBalance (字节) - PDF shows UCAS (中科院大学)
    p, cid = find_paper(data, "2604.13847")
    if p:
        p["universities"] = ["University of Chinese Academy of Sciences"]
        p["hasUniCollab"] = True
        print(f"  FIX universities: SparseBalance -> UCAS (字节×中科院大学)")
        fixes += 1

    # Fix 2: Correct Prediction CRKG - PDF shows HKUST-GZ + PolyU
    # HKUST-GZ 不是港校, PolyU 是港校!
    p, cid = find_paper(data, "2604.14121")
    if p:
        p["universities"] = ["香港科技大学（广州）(HKUST-GZ)", "香港理工大学 (PolyU)"]
        p["hkUniversities"] = ["香港理工大学 (PolyU)"]
        p["hasUniCollab"] = True
        p["hasHKCollab"] = True
        p["collabConfidence"] = "uni_only"  # PDF 没看到公司
        print(f"  FIX universities: CRKG -> HKUST-GZ + PolyU (港校: PolyU)")
        fixes += 1

    # Fix 3: AVID - 蚂蚁集团 × SJTU × CUHK
    # 需要检查是否在 antgroup 或其他公司下
    p, cid = find_paper(data, "2604.13847")  # 先用 SparseBalance 的做参考
    # 搜索 AVID 论文
    for company_id, company_data in data["companies"].items():
        for paper in company_data["papers"]:
            if "AVID" in paper.get("title", "") and "Audio-Visual" in paper.get("title", ""):
                paper["universities"] = ["Shanghai Jiao Tong University", "香港中文大学 (CUHK)"]
                paper["hkUniversities"] = ["香港中文大学 (CUHK)"]
                paper["hasUniCollab"] = True
                paper["hasHKCollab"] = True
                print(f"  FIX universities: AVID [{company_id}] -> SJTU + CUHK (港校: CUHK)")
                fixes += 1
                break

    # Fix 4: HiVLA - 确认 Ping Luo 来自 HKU
    p, cid = find_paper(data, "2604.14125")
    if p:
        p["universities"] = ["香港大学 (HKU)", "Shanghai AI Laboratory"]
        p["hkUniversities"] = ["香港大学 (HKU)"]
        p["hasUniCollab"] = True
        p["hasHKCollab"] = True
        print(f"  FIX universities: HiVLA -> HKU + Shanghai AI Lab (港校: HKU)")
        fixes += 1

    # Recalculate all counts
    for company_id, company_data in data["companies"].items():
        company_data["uniCollabCount"] = sum(1 for p in company_data["papers"] if p.get("hasUniCollab"))
        company_data["hkCollabCount"] = sum(1 for p in company_data["papers"] if p.get("hasHKCollab"))

    data["totalUniCollab"] = sum(c.get("uniCollabCount", 0) for c in data["companies"].values())
    data["totalHKCollab"] = sum(c.get("hkCollabCount", 0) for c in data["companies"].values())
    data["generatedAt"] = datetime.now().isoformat() + "Z"

    with open(ARXIV_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {fixes} fixes applied. UniCollab: {data['totalUniCollab']}, HKCollab: {data['totalHKCollab']}")


if __name__ == "__main__":
    main()
