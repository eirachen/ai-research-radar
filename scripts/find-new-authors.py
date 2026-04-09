"""Find papers with new (untracked) authors for talent research"""
import json

def main():
    with open("reports/arxiv-daily.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    with open("reports/talent-notes.json", "r", encoding="utf-8") as f:
        talent_data = json.load(f)
    
    existing_names = set(talent_data.get("notes", {}).keys())
    
    # Collect all recent uni-collab papers with new authors
    new_author_papers = []
    for company_id, company_data in data["companies"].items():
        for paper in company_data.get("papers", []):
            if not paper.get("hasUniCollab"):
                continue
            if paper["published"] < "2026-04-06":
                continue
            new_authors = [a for a in paper["authors"] if a not in existing_names]
            if new_authors:
                new_author_papers.append({
                    "company": company_data["company"],
                    "title": paper["title"],
                    "arxivUrl": paper["arxivUrl"],
                    "pdfUrl": paper.get("pdfUrl", ""),
                    "published": paper["published"],
                    "authors": paper["authors"],
                    "new_authors": new_authors,
                    "universities": paper.get("universities", []),
                    "hkUniversities": paper.get("hkUniversities", []),
                    "hasHKCollab": paper.get("hasHKCollab", False),
                    "directions": [d["label"] for d in paper.get("directions", [])],
                    "affiliations": paper.get("affiliations", []),
                })
    
    # Sort: HK first, then newest first
    new_author_papers.sort(key=lambda x: (not x["hasHKCollab"], x["published"]))
    new_author_papers.reverse()
    
    print(f"Papers with new authors: {len(new_author_papers)}")
    all_new = set()
    for p in new_author_papers:
        all_new.update(p["new_authors"])
    print(f"Total unique new authors: {len(all_new)}")
    
    # Deduplicate by arxivUrl
    seen_urls = set()
    unique_papers = []
    for p in new_author_papers:
        if p["arxivUrl"] not in seen_urls:
            seen_urls.add(p["arxivUrl"])
            unique_papers.append(p)
    
    print(f"Unique papers: {len(unique_papers)}")
    print()
    
    for i, p in enumerate(unique_papers):
        hk = " [HK!]" if p["hasHKCollab"] else ""
        print(f"=== Paper {i+1}{hk}: {p['company']} ===")
        print(f"Title: {p['title']}")
        print(f"URL: {p['arxivUrl']}")
        print(f"PDF: {p['pdfUrl']}")
        print(f"Published: {p['published']}")
        print(f"Universities: {p['universities']}")
        print(f"Directions: {p['directions']}")
        print(f"All authors: {p['authors']}")
        print(f"NEW authors to track: {p['new_authors']}")
        print()

if __name__ == "__main__":
    main()
