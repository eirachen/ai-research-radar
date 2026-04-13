"""Quick check of arxiv-daily.json paper stats"""
import json, os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(base, "reports", "arxiv-daily.json"), "r", encoding="utf-8") as f:
    d = json.load(f)

papers = []
for c in d["companies"].values():
    papers.extend(c["papers"])

uni = [p for p in papers if p.get("hasUniCollab")]
hk = [p for p in papers if p.get("hasHKCollab")]

print(f"Total: {len(papers)}, UniCollab: {len(uni)}, HKCollab: {len(hk)}")
print(f"Generated: {d.get('generatedAt','?')}")
print()

# Companies breakdown
print("=== Companies ===")
for key, c in d["companies"].items():
    print(f"  {c['company']}: {len(c['papers'])} papers")
print()

# HK collab papers
print("=== HK Collab Papers ===")
for p in hk:
    print(f"  [{p.get('published','')[:10]}] {p['title'][:70]}")
    print(f"    hkUnis: {p.get('hkUniversities', [])}")
    print(f"    authors: {p.get('authors', [])[:6]}")
    print(f"    company: searching...")
    # find which company
    for key, c in d["companies"].items():
        if p in c["papers"]:
            print(f"    company: {c['company']}")
            break
    print()

# Recent uni collab (last 3 days)
print("=== Recent UniCollab (>=2026-04-10) ===")
recent = [p for p in uni if p.get("published", "") >= "2026-04-10"]
for p in recent[:30]:
    print(f"  [{p.get('published','')[:10]}] {p['title'][:70]}")
    print(f"    unis: {p.get('universities', [])}")
    print(f"    authors: {p.get('authors', [])[:5]}")
    for key, c in d["companies"].items():
        if p in c["papers"]:
            print(f"    company: {c['company']}")
            break
    print()

# All uni collab papers count by date
print("=== UniCollab by date ===")
from collections import Counter
dates = Counter(p.get("published", "")[:10] for p in uni)
for dt in sorted(dates.keys(), reverse=True):
    print(f"  {dt}: {dates[dt]} papers")
