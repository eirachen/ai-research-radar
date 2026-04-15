"""Temp: check arxiv-daily.json stats"""
import json, os
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports", "arxiv-daily.json")
d = json.load(open(path, "r", encoding="utf-8"))
print(f"Generated: {d['generatedAt']}")
print(f"Since: {d['since']}")
print(f"Total: {d['totalPapers']} papers, {d['totalUniCollab']} uni, {d['totalHKCollab']} HK")
for k, v in d["companies"].items():
    papers = v.get("papers", [])
    # Find newest paper date
    dates = [p["published"][:10] for p in papers]
    newest = max(dates) if dates else "N/A"
    # Count papers from Apr 12-14 (weekend + today)
    recent = [p for p in papers if p["published"][:10] >= "2026-04-12"]
    print(f"  {k}: {v['count']} total, {len(recent)} since Apr12, newest={newest}")
