import json

d = json.load(open("c:/Users/eirachen/WorkBuddy/20260407122917/ai-research-monitor/reports/arxiv-daily.json", encoding="utf-8"))
t = json.load(open("c:/Users/eirachen/WorkBuddy/20260407122917/ai-research-monitor/reports/talent-notes.json", encoding="utf-8"))
notes = set(t["notes"].keys())

print("=== Talent notes keys:", notes)
print()

matched = 0
unmatched = 0
for cid, c in d["companies"].items():
    for p in c["papers"]:
        if not p.get("hasUniCollab"):
            continue
        authors = p.get("authors", [])
        found = []
        for a in authors:
            if a in notes:
                found.append(a)
            else:
                for key in notes:
                    if a in key or key in a:
                        found.append(f"{a} -> {key}")
                        break
        status = "MATCH" if found else "NO MATCH"
        if found:
            matched += 1
        else:
            unmatched += 1
        print(f"[{c['company']}] {p['title'][:60]}")
        print(f"  Authors: {authors[:5]}")
        print(f"  Unis: {p.get('universities', [])[:3]}")
        print(f"  {status}: {found if found else 'NO known authors in talent-notes'}")
        print()

print(f"=== Total: {matched} matched, {unmatched} unmatched")
