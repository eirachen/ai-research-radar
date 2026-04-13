"""Generate summary stats for the intelligence report"""
import json, os
from collections import Counter, defaultdict

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(base, "reports", "arxiv-daily.json"), "r", encoding="utf-8") as f:
    d = json.load(f)

# Papers by company, sorted by date
print("=== Papers by Company (latest first) ===")
for key, c in sorted(d["companies"].items(), key=lambda x: len(x[1]["papers"]), reverse=True):
    papers = c["papers"]
    recent = [p for p in papers if p.get("published", "") >= "2026-04-07"]
    print(f"\n{c['company']} ({len(papers)} total, {len(recent)} since Apr 7)")
    for p in sorted(papers, key=lambda x: x.get("published",""), reverse=True)[:5]:
        dirs = [dd["label"] for dd in p.get("directions", [])]
        uni = "✅HK" if p.get("hasHKCollab") else ("🎓" if p.get("hasUniCollab") else "")
        print(f"  [{p.get('published','')[:10]}] {p['title'][:65]} {uni} {dirs}")

# Direction distribution
print("\n\n=== Direction Distribution ===")
dir_counter = Counter()
for c in d["companies"].values():
    for p in c["papers"]:
        for dd in p.get("directions", []):
            dir_counter[dd["label"]] += 1
for label, count in dir_counter.most_common():
    print(f"  {label}: {count}")

# Recent highlights (last 7 days)
print("\n\n=== All Papers Since Apr 7 ===")
all_recent = []
for key, c in d["companies"].items():
    for p in c["papers"]:
        if p.get("published", "") >= "2026-04-07":
            all_recent.append((c["company"], p))
all_recent.sort(key=lambda x: x[1].get("published",""), reverse=True)
for company, p in all_recent:
    dirs = [dd["label"] for dd in p.get("directions", [])]
    uni = " [HK]" if p.get("hasHKCollab") else (" [Uni]" if p.get("hasUniCollab") else "")
    print(f"  [{p.get('published','')[:10]}] {company}: {p['title'][:60]}{uni} {dirs}")
