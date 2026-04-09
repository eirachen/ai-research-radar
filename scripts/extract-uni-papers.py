"""Extract university collaboration papers and existing talent for analysis"""
import json
import sys

def main():
    with open("reports/arxiv-daily.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Load existing talent
    with open("reports/talent-notes.json", "r", encoding="utf-8") as f:
        talent_data = json.load(f)
    
    existing_names = set(talent_data.get("notes", {}).keys())
    print(f"=== Existing talent entries: {len(existing_names)} ===")
    
    # Collect all uni-collab papers from recent 3 days
    uni_papers = []
    for company_id, company_data in data["companies"].items():
        for paper in company_data.get("papers", []):
            if paper.get("hasUniCollab") and paper["published"] >= "2026-04-06":
                uni_papers.append({
                    "company": company_data["company"],
                    "title": paper["title"],
                    "arxivUrl": paper["arxivUrl"],
                    "pdfUrl": paper.get("pdfUrl", ""),
                    "published": paper["published"],
                    "authors": paper["authors"],
                    "authorCount": paper.get("authorCount", len(paper["authors"])),
                    "affiliations": paper.get("affiliations", []),
                    "universities": paper.get("universities", []),
                    "hkUniversities": paper.get("hkUniversities", []),
                    "hasHKCollab": paper.get("hasHKCollab", False),
                    "directions": paper.get("directions", []),
                    "comment": paper.get("comment", ""),
                })
    
    # Sort: HK first, then by date
    uni_papers.sort(key=lambda x: (not x["hasHKCollab"], x["published"]), reverse=False)
    uni_papers.sort(key=lambda x: x["hasHKCollab"], reverse=True)
    
    print(f"\n=== Recent uni-collab papers (since Apr 6): {len(uni_papers)} ===")
    hk_count = sum(1 for p in uni_papers if p["hasHKCollab"])
    print(f"HK collab: {hk_count}")
    
    for i, p in enumerate(uni_papers):
        hk_tag = " [HK!]" if p["hasHKCollab"] else ""
        print(f"\n--- Paper {i+1}{hk_tag} ---")
        print(f"  Company: {p['company']}")
        print(f"  Title: {p['title'][:80]}")
        print(f"  Published: {p['published']}")
        print(f"  URL: {p['arxivUrl']}")
        print(f"  Authors ({p['authorCount']}): {', '.join(p['authors'][:6])}")
        print(f"  Affiliations: {', '.join(p['affiliations'][:5])}")
        print(f"  Universities: {', '.join(p['universities'][:5])}")
        print(f"  Directions: {', '.join(d['label'] for d in p['directions'][:3])}")
        
        # Check which authors are already tracked
        new_authors = [a for a in p["authors"] if a not in existing_names]
        tracked = [a for a in p["authors"] if a in existing_names]
        if tracked:
            print(f"  Already tracked: {', '.join(tracked)}")
        if new_authors:
            print(f"  New authors: {', '.join(new_authors[:6])}")

if __name__ == "__main__":
    main()
