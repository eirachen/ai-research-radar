"""Find new authors from HK collab papers that are NOT yet in talent-notes.json"""
import json, os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(base, "reports", "arxiv-daily.json"), "r", encoding="utf-8") as f:
    arxiv = json.load(f)
with open(os.path.join(base, "reports", "talent-notes.json"), "r", encoding="utf-8") as f:
    talents = json.load(f)

existing = set(talents.get("notes", {}).keys())

# Get all HK collab papers
hk_papers = []
for key, c in arxiv["companies"].items():
    for p in c["papers"]:
        if p.get("hasHKCollab"):
            hk_papers.append((c["company"], p))

print(f"HK collab papers: {len(hk_papers)}")
print(f"Existing talents: {len(existing)}")
print()

for company, p in hk_papers:
    print(f"=== [{p.get('published','')[:10]}] {p['title'][:70]} ===")
    print(f"  Company: {company}")
    print(f"  hkUnis: {p.get('hkUniversities', [])}")
    print(f"  All authors: {p.get('authors', [])}")
    new_authors = [a for a in p.get("authors", []) if a not in existing]
    old_authors = [a for a in p.get("authors", []) if a in existing]
    print(f"  Already in DB: {old_authors}")
    print(f"  NEW (need research): {new_authors}")
    print(f"  arXiv: {p.get('arxivUrl','')}")
    print(f"  PDF: {p.get('pdfUrl','')}")
    print()

# Also get recent (>=2026-04-07) non-HK uni collab papers
print("\n=== Recent non-HK UniCollab (>=2026-04-07) ===")
for key, c in arxiv["companies"].items():
    for p in c["papers"]:
        if p.get("hasUniCollab") and not p.get("hasHKCollab") and p.get("published","") >= "2026-04-07":
            new_authors = [a for a in p.get("authors", []) if a not in existing]
            if new_authors:
                print(f"  [{p.get('published','')[:10]}] {p['title'][:60]}")
                print(f"    Company: {c['company']}")
                print(f"    Unis: {p.get('universities', [])}")
                print(f"    NEW authors: {new_authors[:5]}")
                print(f"    arXiv: {p.get('arxivUrl','')}")
                print()
