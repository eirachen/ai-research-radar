import json

d = json.load(open("c:/Users/eirachen/WorkBuddy/20260407122917/ai-research-monitor/reports/arxiv-daily.json", encoding="utf-8"))
t = json.load(open("c:/Users/eirachen/WorkBuddy/20260407122917/ai-research-monitor/reports/talent-notes.json", encoding="utf-8"))
existing = set(t["notes"].keys())

# Collect all uni-collab papers with their authors and universities
papers = []
for cid, c in d["companies"].items():
    for p in c["papers"]:
        if p.get("hasUniCollab"):
            papers.append({
                "title": p["title"][:60],
                "company": c["company"],
                "authors": p["authors"],
                "universities": p.get("universities", []),
                "hkUniversities": p.get("hkUniversities", []),
                "arxivUrl": p.get("arxivUrl", ""),
                "pdfUrl": p.get("pdfUrl", ""),
            })

print(f"Total uni-collab papers: {len(papers)}")
print(f"Already in talent-notes: {existing}")
print()

# List all unique authors from uni-collab papers, skip existing
all_authors = {}
for p in papers:
    for a in p["authors"]:
        if a not in existing and a not in all_authors:
            all_authors[a] = {
                "papers": [],
                "universities": set(),
            }
        if a in all_authors:
            all_authors[a]["papers"].append(f"[{p['company']}] {p['title']}")
            all_authors[a]["universities"].update(p["universities"])

# Sort by number of papers (most prolific first)
sorted_authors = sorted(all_authors.items(), key=lambda x: -len(x[1]["papers"]))

print(f"Unique new authors to investigate: {len(sorted_authors)}")
print()
for name, info in sorted_authors[:30]:
    unis = ", ".join(info["universities"]) if info["universities"] else "?"
    print(f"  {name} | unis: {unis} | papers: {len(info['papers'])}")
    for pp in info["papers"][:2]:
        print(f"    - {pp}")
