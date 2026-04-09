"""Add newly discovered talent to talent-notes.json"""
import json
from datetime import datetime

def main():
    with open("reports/talent-notes.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    notes = data.get("notes", {})
    
    # New talent entries discovered 2026-04-09
    new_entries = {
        "Xuming Hu": {
            "name": "胡旭明 (Xuming Hu)",
            "university": "香港科技大学（广州）(HKUST-GZ)",
            "isHK": True,
            "status": "助理教授",
            "advisor": "",
            "lab": "AI Thrust, HKUST (GZ)",
            "homepage": "https://xuminghu.github.io/",
            "scholar": "https://scholar.google.com.hk/citations?user=dbBKbXoAAAAJ",
            "direction": "NLP / 大语言模型 / 语音",
            "gradYear": "",
            "statusNote": "2024年入职HKUST-GZ，清华博士，AudioKV论文通讯作者",
            "editedAt": "2026-04-09"
        },
        "Yunfan Gao": {
            "name": "Yunfan Gao",
            "university": "同济大学",
            "isHK": False,
            "status": "博二",
            "advisor": "王昊奋教授",
            "lab": "Knowledge Computing Lab, Tongji University",
            "homepage": "https://tongji-kgllm.github.io/people/gao-yunfan/",
            "scholar": "https://scholar.google.com/citations?user=qIFESOwAAAAJ",
            "direction": "RAG / LLM / 知识图谱",
            "gradYear": "~2028",
            "statusNote": "RAG Survey高引论文一作(6600+引用)，与阿里通义合作HingeMem",
            "editedAt": "2026-04-09"
        },
        "Haofen Wang": {
            "name": "王昊奋 (Haofen Wang)",
            "university": "同济大学",
            "isHK": False,
            "status": "长聘教授/博导",
            "advisor": "",
            "lab": "Knowledge Computing Lab, Tongji University",
            "homepage": "https://tongji-kgllm.github.io/people/wang-haofen/",
            "scholar": "https://scholar.google.com/citations?user=1FhdXpsAAAAJ",
            "direction": "知识图谱 / NLP / RAG",
            "gradYear": "",
            "statusNote": "同济大学设计创意学院长聘教授，知识图谱专家，OpenSPG开源项目",
            "editedAt": "2026-04-09"
        },
        "Zeliang Zhang": {
            "name": "Zeliang Zhang",
            "university": "University of Rochester",
            "isHK": False,
            "status": "博士在读",
            "advisor": "Chenliang Xu",
            "lab": "Department of Computer Science, University of Rochester",
            "homepage": "https://zhangaipi.github.io/",
            "scholar": "https://scholar.google.com/citations?user=7nLfsSgAAAAJ",
            "direction": "对抗鲁棒性 / 张量学习 / MoE",
            "gradYear": "待确认",
            "statusNote": "本科HUST，曾在Microsoft Research实习，MoE剪枝论文与Bin Yu合作",
            "editedAt": "2026-04-09"
        },
        "Nikhil Ghosh": {
            "name": "Nikhil Ghosh",
            "university": "UC Berkeley (PhD) / Flatiron Institute (postdoc)",
            "isHK": False,
            "status": "博士后研究员",
            "advisor": "Bin Yu (PhD advisor)",
            "lab": "Center for Computational Mathematics, Flatiron Institute",
            "homepage": "https://nikhilgsh.github.io/",
            "scholar": "https://scholar.google.com/citations?user=aWuTVvAAAAAJ",
            "direction": "深度学习理论 / MoE",
            "gradYear": "",
            "statusNote": "2024年Berkeley博士毕业，现Flatiron Institute博后(2024-2027)",
            "editedAt": "2026-04-09"
        },
        "Mingchen Zhuge": {
            "name": "Mingchen Zhuge",
            "university": "KAUST",
            "isHK": False,
            "status": "博三",
            "advisor": "Juergen Schmidhuber",
            "lab": "AI Initiative, KAUST",
            "homepage": "https://metauto.ai/",
            "scholar": "https://scholar.google.com/citations?user=Qnj6XlMAAAAJ",
            "direction": "多模态Agent / 代码生成 / 递归自改进",
            "gradYear": "~2026",
            "statusNote": "Neural Computers论文一作，5700+引用，METAUTO项目主导者",
            "editedAt": "2026-04-09"
        },
        "Haozhe Liu": {
            "name": "Haozhe Liu",
            "university": "KAUST (PhD) / NVIDIA Research",
            "isHK": False,
            "status": "NVIDIA Research Scientist",
            "advisor": "Juergen Schmidhuber (PhD)",
            "lab": "NVIDIA Research (Song Han & Enze Xie team)",
            "homepage": "https://haozheliu-st.github.io/",
            "scholar": "https://scholar.google.com/citations?user=QX51P54AAAAJ",
            "direction": "多模态生成 / 视频生成 / 强化学习",
            "gradYear": "",
            "statusNote": "KAUST博士毕业，现NVIDIA研究员，与百度合作Neural Computers",
            "editedAt": "2026-04-09"
        },
        "Ernest K. Ryu": {
            "name": "Ernest K. Ryu",
            "university": "UCLA / Seoul National University",
            "isHK": False,
            "status": "助理教授",
            "advisor": "",
            "lab": "Department of Mathematics, UCLA",
            "homepage": "https://ernestryu.com/",
            "scholar": "https://scholar.google.com/citations?user=CNOqUZoAAAAJ",
            "direction": "凸优化 / 深度学习理论",
            "gradYear": "",
            "statusNote": "2020-2024首尔国立大学助理教授，2024起UCLA，数学优化理论专家",
            "editedAt": "2026-04-09"
        },
        "Jiangning Zhang": {
            "name": "张江宁 (Jiangning Zhang)",
            "university": "浙江大学 / 腾讯优图",
            "isHK": False,
            "status": "即将入职助理教授(ZJU-100)",
            "advisor": "",
            "lab": "APRIL Lab, Zhejiang University / YouTu Lab, Tencent",
            "homepage": "https://zhangzjn.github.io/",
            "scholar": "https://scholar.google.com/citations?user=2hA4X9wAAAAJ",
            "direction": "视频生成 / Embodied AI / 基础模型",
            "gradYear": "",
            "statusNote": "2026年4月入职浙大百人计划助理教授，现腾讯优图首席研究员，6700+引用",
            "editedAt": "2026-04-09"
        },
        "Teng Hu": {
            "name": "Teng Hu",
            "university": "上海交通大学",
            "isHK": False,
            "status": "博士在读",
            "advisor": "Ran Yi / Lizhuang Ma",
            "lab": "School of Electronic Information and Electrical Engineering, SJTU",
            "homepage": "",
            "scholar": "https://scholar.google.com/citations?user=Jm5qsAYAAAAJ",
            "direction": "计算机视觉 / 视频生成",
            "gradYear": "待确认",
            "statusNote": "2022年本科毕业于上交，OpenAI合作Evolution of Video Generative Foundations论文一作",
            "editedAt": "2026-04-09"
        },
        "Ran Yi": {
            "name": "Ran Yi",
            "university": "上海交通大学",
            "isHK": False,
            "status": "副教授/博导",
            "advisor": "",
            "lab": "Digital Media and Computer Vision Lab, CS Dept, SJTU",
            "homepage": "https://yiranran.github.io/",
            "scholar": "https://scholar.google.com/citations?user=y68DLo4AAAAJ",
            "direction": "计算机视觉 / 计算机图形学",
            "gradYear": "",
            "statusNote": "SJTU计算机科学与工程系副教授，4100+引用",
            "editedAt": "2026-04-09"
        },
        "Alberto Marchisio": {
            "name": "Alberto Marchisio",
            "university": "NYU Abu Dhabi",
            "isHK": False,
            "status": "博士后/研究组长",
            "advisor": "Muhammad Shafique",
            "lab": "eBRAIN Lab, NYU Abu Dhabi",
            "homepage": "https://ebrain4everyone.com/albertomarchisio",
            "scholar": "https://scholar.google.com/citations?user=6QPlLnAAAAAJ",
            "direction": "机器学习 / 硬件架构 / 神经形态计算",
            "gradYear": "",
            "statusNote": "TU Wien博士，现NYUAD研究组长，Transformer嵌入式推理优化",
            "editedAt": "2026-04-09"
        },
        "Muhammad Shafique": {
            "name": "Muhammad Shafique",
            "university": "NYU Abu Dhabi",
            "isHK": False,
            "status": "教授",
            "advisor": "",
            "lab": "eBRAIN Lab, NYU Abu Dhabi",
            "homepage": "https://ebrain4everyone.com/",
            "scholar": "",
            "direction": "高效AI / 硬件设计 / 神经形态计算",
            "gradYear": "",
            "statusNote": "NYUAD工程部教授，eBRAIN实验室主任，TRAPTI论文通讯作者",
            "editedAt": "2026-04-09"
        },
        "Zining Zhu": {
            "name": "Zining Zhu",
            "university": "Stevens Institute of Technology",
            "isHK": False,
            "status": "助理教授",
            "advisor": "",
            "lab": "Explainable and Controllable AI Lab (ECAI Lab)",
            "homepage": "https://www.stevens.edu/profile/zzhu41",
            "scholar": "https://scholar.google.com/citations?user=Xr_hCJMAAAAJ",
            "direction": "NLP / 可解释AI / 可信AI",
            "gradYear": "",
            "statusNote": "多伦多大学博士(Vector Institute)，LLM可解释性与控制，与阿里通义合作",
            "editedAt": "2026-04-09"
        },
        "Xuyang Liu": {
            "name": "刘旭洋 (Xuyang Liu)",
            "university": "四川大学 → 香港理工大学 (PolyU)",
            "isHK": True,
            "status": "硕三 → 即将读博 (PolyU)",
            "advisor": "待确认",
            "lab": "",
            "homepage": "https://xuyang-liu16.github.io/",
            "scholar": "",
            "direction": "多模态大语言模型 / 高效LLM",
            "gradYear": "待确认",
            "statusNote": "四川大学硕士在读，2026秋入读PolyU博士，AudioKV论文作者，阿里通义实习",
            "editedAt": "2026-04-09"
        }
    }
    
    added = 0
    for key, entry in new_entries.items():
        if key not in notes:
            notes[key] = entry
            added += 1
            print(f"+ Added: {key} ({entry['university']})")
        else:
            # Don't overwrite manually edited entries
            existing = notes[key]
            print(f"~ Exists: {key} (editedAt={existing.get('editedAt', 'N/A')})")
    
    data["notes"] = notes
    data["generatedAt"] = datetime.now().isoformat() + "Z"
    
    with open("reports/talent-notes.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nTotal: {len(notes)} entries ({added} new)")

if __name__ == "__main__":
    main()
