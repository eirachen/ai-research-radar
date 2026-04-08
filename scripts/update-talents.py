import json

f = open('reports/talent-notes.json', 'r', encoding='utf-8')
d = json.load(f)
f.close()

updates = {
    "Shi Qiu": {
        "name": "Shi Qiu",
        "university": "Peking University",
        "status": "senior undergrad (incoming PhD at UNC)",
        "homepage": "https://stephenqsstarthomas.github.io/",
        "scholar": "https://scholar.google.com/citations?user=wScRGY8AAAAJ",
        "direction": "Agentic AI / LLM Reasoning / Security",
        "advisor": "UNC Chapel Hill (incoming)",
    },
    "Graziano Blasilli": {
        "university": "Sapienza University of Rome",
        "status": "PhD student",
        "scholar": "https://scholar.google.com/citations?user=xpuos8EAAAAJ",
        "direction": "Visual Analytics / XAI / Cybersecurity",
    },
    "Marco Angelini": {
        "university": "Link Campus University / Sapienza",
        "status": "Assistant Professor",
        "homepage": "https://research.uniroma1.it/en/researcher/b22bb3eb3db0a0118a6bd4520a13c45f47cfa4864be391dc02b71b84",
        "direction": "Visual Analytics / XAI",
    },
    "Mengyu Zhou": {
        "name": "Mengyu Zhou",
        "university": "Microsoft Research Asia",
        "status": "Principal Researcher",
        "homepage": "http://zmy.io/index-zh.html",
        "scholar": "https://scholar.google.com/citations?user=Pvnsg6kAAAAJ",
        "direction": "NLP / Data Analytics",
    },
    "Yingshui Tan": {
        "university": "Alibaba Group",
        "status": "Staff Research Scientist",
        "scholar": "https://scholar.google.com/citations?user=13k5Sq0AAAAJ",
        "direction": "LLM / Safety / Alignment",
    },
    "Yunhao Feng": {
        "homepage": "https://github.com/Yunhao-Feng",
        "direction": "Agent Security / Backdoor / LLM Safety",
    },
    "Binod Bhattarai": {
        "university": "University of Aberdeen",
        "status": "Assistant Professor",
        "scholar": "https://scholar.google.com.hk/citations?user=PDEi58sAAAAJ",
        "direction": "ML / Medical Image / Computer Vision",
    },
    "Seungryul Baek": {
        "university": "UNIST",
        "status": "Associate Professor",
        "scholar": "https://scholar.google.com/citations?user=Mz1fab8AAAAJ",
        "direction": "Deep Learning / CV / Pose Estimation",
    },
    "Chenghao Zhang": {
        "university": "UPenn / CASIA",
        "status": "MS grad -> Kuaishou",
        "scholar": "https://scholar.google.com/citations?user=w3iQCSAAAAAJ",
        "lab": "Kuaishou Technology",
    },
}

count = 0
for key, upd in updates.items():
    if key in d["notes"]:
        for field, val in upd.items():
            d["notes"][key][field] = val
        count += 1
        print(f"Updated: {key}")
    else:
        print(f"Not found: {key}")

with open('reports/talent-notes.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print(f"Done. Updated {count}. Total: {len(d['notes'])}")
