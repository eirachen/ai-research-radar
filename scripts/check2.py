import json
d=json.load(open("c:/Users/eirachen/WorkBuddy/20260407122917/ai-research-monitor/reports/arxiv-daily.json",encoding="utf-8"))
notes=["Ye Tian","Chengcheng Wang","Jinyi Hu","Tyler Zhu","Thomas Jiralerspong","Guhao Feng"]
found = 0
for cid,c in d["companies"].items():
    for p in c["papers"]:
        for a in p["authors"]:
            for n in notes:
                if a==n or n in a or a in n:
                    found += 1
                    print("MATCH:", a, "~", n, "in", p["title"][:50])
print("Total matches:", found)
