import json
d = json.load(open("reports/arxiv-daily.json", "r", encoding="utf-8"))
for co in d["companies"].values():
    for p in co["papers"]:
        dirs = p.get("directions", [])
        if any(x.get("id") == "Speech" for x in dirs):
            speech_pos = next(i for i, x in enumerate(dirs) if x.get("id") == "Speech")
            print(f"  {len(dirs)} dirs | Speech@{speech_pos} | {co['company']}: {p['title'][:55]}")
            # print actual direction IDs
            print(f"    IDs: {[x.get('id') for x in dirs]}")
