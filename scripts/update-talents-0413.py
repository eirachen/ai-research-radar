"""
Update talent-notes.json with new authors found from today's HK collab papers.
Only adds new entries; does NOT overwrite existing entries that have editedAt.
"""
import json, os
from datetime import datetime

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
talent_path = os.path.join(base, "reports", "talent-notes.json")

with open(talent_path, "r", encoding="utf-8") as f:
    data = json.load(f)

notes = data.get("notes", {})
today = datetime.now().strftime("%Y-%m-%d")

# New talents to add (only high-confidence, verified data)
new_talents = {
    # === From "Reasoning Patterns" paper (CityU + USTC + Meituan + ZJU) ===
    "Zhaoyi Li": {
        "name": "Zhaoyi Li",
        "university": "中国科学技术大学 (USTC) & 香港城市大学 (CityU) 联合培养",
        "isHK": True,
        "status": "博士生 (2022入学USTC, 2023入学CityU)",
        "advisor": "魏颖 (Ying Wei) / 连德富 (Defu Lian) / 宋令奇 (Linqi Song)",
        "lab": "",
        "homepage": "https://zhaoyi-li21.github.io/",
        "scholar": "https://scholar.google.com/citations?user=qtDqcwkAAAAJ",
        "direction": "LLM推理 / 组合泛化 / 可解释性",
        "gradYear": "~2027",
        "statusNote": "ICLR2026*2, 国家奖学金, 美团LongCat实习",
        "editedAt": today
    },
    "Gangwei Jiang": {
        "name": "Gangwei Jiang",
        "university": "中国科学技术大学 (USTC) & 香港城市大学 (CityU) 联合培养",
        "isHK": True,
        "status": "博士生 (2020入学USTC, 2022入学CityU)",
        "advisor": "待确认",
        "lab": "",
        "homepage": "https://gangwjiang.github.io/",
        "scholar": "https://scholar.google.com/citations?user=8lykHA8AAAAJ",
        "direction": "机器学习",
        "gradYear": "待确认",
        "statusNote": "Google Scholar 889次引用",
        "editedAt": today
    },
    "Ranran Shen": {
        "name": "申冉冉 (Ranran Shen)",
        "university": "中国科学技术大学 (USTC)",
        "isHK": False,
        "status": "博士生",
        "advisor": "Pan Peng",
        "lab": "",
        "homepage": "https://ranran-shen.github.io/",
        "scholar": "https://scholar.google.com/citations?user=BvA-wRQAAAAJ",
        "direction": "算法 / 图论",
        "gradYear": "待确认",
        "statusNote": "NeurIPS2023",
        "editedAt": today
    },
    "Ying Wei": {
        "name": "魏颖 (Ying Wei)",
        "university": "浙江大学 (Zhejiang University)",
        "isHK": False,
        "status": "百人计划研究员/博导",
        "advisor": "",
        "lab": "",
        "homepage": "http://wei-ying.net/",
        "scholar": "https://scholar.google.com/citations?user=5UpFdKsAAAAJ",
        "direction": "迁移学习 / 持续学习 / AI for Science",
        "gradYear": "",
        "statusNote": "曾任CityU助理教授, Google Scholar 6569引用",
        "editedAt": today
    },
    "Defu Lian": {
        "name": "连德富 (Defu Lian)",
        "university": "中国科学技术大学 (USTC)",
        "isHK": False,
        "status": "教授/博导/计算机学院副院长",
        "advisor": "",
        "lab": "",
        "homepage": "https://faculty.ustc.edu.cn/liandefu",
        "scholar": "https://scholar.google.com/citations?user=QW0ad4sAAAAJ",
        "direction": "推荐系统 / 数据挖掘 / 深度学习",
        "gradYear": "",
        "statusNote": "国家优青",
        "editedAt": today
    },
    
    # === From "Bit-by-Bit" paper (HKUST + CityU + ZJU) ===
    "Sirui Han": {
        "name": "韩斯睿 (Sirui Han)",
        "university": "香港科技大学 (HKUST)",
        "isHK": True,
        "status": "助理教授 / HKGAI LLM部门主管",
        "advisor": "",
        "lab": "HKUST EMIA / HKGAI",
        "homepage": "https://siruihan.com/",
        "scholar": "https://scholar.google.com/citations?user=ootCmkEAAAAJ",
        "direction": "AI安全/法律对齐/高效LLM/多模态AI",
        "gradYear": "",
        "statusNote": "法学+CS双博士, 30+博士生, 50+顶会论文, 3300万+港元科研经费",
        "editedAt": today
    },
    "Jiacheng Liu": {
        "name": "Jiacheng Liu",
        "university": "香港科技大学 (HKUST)",
        "isHK": True,
        "status": "待确认",
        "advisor": "待确认",
        "lab": "",
        "homepage": "",
        "scholar": "",
        "direction": "待确认",
        "gradYear": "",
        "statusNote": "Bit-by-Bit QAT论文作者, 注意同名者(ECE spintronics方向)需区分",
        "editedAt": today
    },
    "Qiyuan Zhu": {
        "name": "Qiyuan Zhu",
        "university": "香港科技大学 (HKUST)",
        "isHK": True,
        "status": "博士生 (2024入学)",
        "advisor": "Sirui Han (待确认)",
        "lab": "",
        "homepage": "",
        "scholar": "",
        "direction": "待确认",
        "gradYear": "~2028",
        "statusNote": "本科西安交通大学, OpenReview确认HKUST PhD 2024-",
        "editedAt": today
    },
    "Xintong Yang": {
        "name": "Xintong Yang",
        "university": "香港科技大学 (HKUST)",
        "isHK": True,
        "status": "待确认",
        "advisor": "待确认",
        "lab": "",
        "homepage": "",
        "scholar": "",
        "direction": "待确认",
        "gradYear": "",
        "statusNote": "Bit-by-Bit QAT论文作者",
        "editedAt": today
    },
    "Chao Li": {
        "name": "Chao Li",
        "university": "浙江大学 (Zhejiang University)",
        "isHK": False,
        "status": "待确认",
        "advisor": "",
        "lab": "",
        "homepage": "",
        "scholar": "",
        "direction": "模型量化",
        "gradYear": "",
        "statusNote": "Bit-by-Bit QAT论文通讯作者",
        "editedAt": today
    },
    "Yike Guo": {
        "name": "Yike Guo",
        "university": "香港科技大学 (HKUST)",
        "isHK": True,
        "status": "校长/讲座教授",
        "advisor": "",
        "lab": "",
        "homepage": "",
        "scholar": "",
        "direction": "数据科学/AI",
        "gradYear": "",
        "statusNote": "HKUST校长, Bit-by-Bit QAT论文通讯作者",
        "editedAt": today
    },
    
    # === From "AudioKV" paper (SJTU EPIC Lab + HKUST-GZ) ===
    # Xuming Hu already in DB. Other authors are from SJTU, not company.
    # Only add SJTU authors that are university-side
    "Linfeng Zhang": {
        "name": "Linfeng Zhang",
        "university": "上海交通大学 (SJTU)",
        "isHK": False,
        "status": "待确认",
        "advisor": "",
        "lab": "EPIC Lab",
        "homepage": "",
        "scholar": "",
        "direction": "音频语言模型 / 高效推理",
        "gradYear": "",
        "statusNote": "AudioKV论文作者, SJTU EPIC Lab",
        "editedAt": today
    },
}

added = 0
skipped = 0
for key, talent in new_talents.items():
    if key in notes:
        existing = notes[key]
        # Don't overwrite if user manually edited
        if existing.get("editedAt"):
            print(f"  SKIP (already exists, editedAt={existing['editedAt']}): {key}")
            skipped += 1
            continue
        # Update empty fields only
        for field, value in talent.items():
            if field == "editedAt":
                continue
            if not existing.get(field) and value:
                existing[field] = value
                print(f"  FILL {key}.{field} = {value}")
        existing["editedAt"] = today
        skipped += 1
    else:
        notes[key] = talent
        added += 1
        print(f"  ADD: {key} ({talent.get('university', '?')})")

data["notes"] = notes
data["lastUpdated"] = datetime.now().isoformat() + "Z"

with open(talent_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nDone! Added: {added}, Skipped: {skipped}, Total: {len(notes)}")
