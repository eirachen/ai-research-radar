"""
添加 2026-04-14 发现的港校新人才到 talent-notes.json
"""
import json
import os
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(script_dir, "..", "reports", "talent-notes.json")
path = os.path.normpath(path)

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

today = "2026-04-14"

new_talents = {
    # ===== 港校教授 =====
    "Qifeng Chen": {
        "name": "陈启峰 (Qifeng Chen)",
        "university": "香港科技大学 (HKUST)",
        "isHK": True,
        "status": "副教授 (Associate Professor)",
        "advisor": "Stanford PhD 2017",
        "lab": "HKUST CSE & ECE",
        "homepage": "https://cqf.io/",
        "scholar": "https://scholar.google.com/citations?user=lLMX9hcAAAAJ",
        "direction": "计算机视觉 / 图像合成 / 生成式AI / 自动驾驶 / 具身AI",
        "gradYear": "N/A (Faculty)",
        "statusNote": "21名在读博士生，23名已毕业博士生。也在HKUST(GZ)挂靠。InsEdit论文通讯作者。",
        "editedAt": today,
        "contactInfo": {
            "emails": ["cqf@ust.hk"],
            "wechat": [],
            "phone": [],
            "cv": [],
            "social": {"github": ""},
            "scannedAt": today,
            "hasContactKeywords": True,
            "hasContact": True
        }
    },
    "Taku Komura": {
        "name": "Taku Komura",
        "university": "香港大学 (HKU)",
        "isHK": True,
        "status": "教授 (Professor)",
        "advisor": "Edinburgh → HKU 2020",
        "lab": "HKU CGVU Lab",
        "homepage": "https://www.cs.hku.hk/index.php/people/academic-staff/taku",
        "scholar": "https://scholar.google.com/citations?user=TApLOhkAAAAJ",
        "direction": "角色动画 / 计算机图形学 / 机器人",
        "gradYear": "N/A (Faculty)",
        "statusNote": "17,256引用。SATO论文资深作者。CGVU Lab负责人。",
        "editedAt": today,
        "contactInfo": {
            "emails": ["taku@cs.hku.hk"],
            "wechat": [],
            "phone": [],
            "cv": [],
            "social": {},
            "scannedAt": today,
            "hasContactKeywords": True,
            "hasContact": True
        }
    },
    "Xiaojuan Qi": {
        "name": "戚晓娟 (Xiaojuan Qi)",
        "university": "香港大学 (HKU)",
        "isHK": True,
        "status": "副教授 (Associate Professor)",
        "advisor": "Oxford Postdoc → HKU",
        "lab": "HKU Deep Vision Lab / CVMI Lab",
        "homepage": "https://xjqi.github.io/",
        "scholar": "https://scholar.google.com/citations?user=bGn0uacAAAAJ",
        "direction": "3D视觉 / 深度学习 / AI / 医学图像分析",
        "gradYear": "N/A (Faculty)",
        "statusNote": "46,727引用。AniGen论文通讯作者。ECE系。",
        "editedAt": today,
        "contactInfo": {
            "emails": [],
            "wechat": [],
            "phone": [],
            "cv": [],
            "social": {},
            "scannedAt": today,
            "hasContactKeywords": False,
            "hasContact": False
        }
    },
    "Bo Yang": {
        "name": "杨波 (Bo Yang)",
        "university": "香港理工大学 (PolyU)",
        "isHK": True,
        "status": "助理教授 (Assistant Professor)",
        "advisor": "DPhil Oxford 2020",
        "lab": "PolyU vLAR Group (Visual Learning and Reasoning)",
        "homepage": "https://www.polyu.edu.hk/comp/people/academic-staff/prof-yang-bo/",
        "scholar": "https://scholar.google.com/citations?user=VqUAqz8AAAAJ",
        "direction": "机器学习 / 3D计算机视觉 / 机器人学习",
        "gradYear": "N/A (Faculty)",
        "statusNote": "PhysInOne CVPR2026论文通讯作者。39人大团队，与Meta合作。",
        "editedAt": today,
        "contactInfo": {
            "emails": ["bo.yang@polyu.edu.hk"],
            "wechat": [],
            "phone": [],
            "cv": [],
            "social": {},
            "scannedAt": today,
            "hasContactKeywords": True,
            "hasContact": True
        }
    },
    
    # ===== 港校学生（已验证） =====
    "Rui Xu": {
        "name": "徐瑞 (Rui Xu)",
        "university": "香港大学 (HKU)",
        "isHK": True,
        "status": "博士在读 (2024.9-)",
        "advisor": "Taku Komura (HKU)",
        "lab": "HKU CGVU Lab",
        "homepage": "https://ruixu.me/",
        "scholar": "https://scholar.google.com/citations?user=3C85rOsAAAAJ",
        "direction": "计算机图形学 / 3D视觉 / 几何处理 / 生成模型",
        "gradYear": "~2028",
        "statusNote": "SIGGRAPH 2023最佳论文奖！China3DV 2026新星奖。SATO第一作者。山大本硕→HKU PhD。在Deemos实习。20+篇论文，极高产。",
        "editedAt": today,
        "contactInfo": {
            "emails": ["ruixu1999@connect.hku.hk", "xrvitd@163.com"],
            "wechat": [],
            "phone": [],
            "cv": [],
            "social": {"github": "github.com/xrvitd", "twitter": "@xrvitd"},
            "scannedAt": today,
            "hasContactKeywords": True,
            "hasContact": True
        }
    },
    "Yi-Hua Huang": {
        "name": "黄一华 (Yi-Hua Huang)",
        "university": "香港大学 (HKU)",
        "isHK": True,
        "status": "博士在读（第三年）",
        "advisor": "Xiaojuan Qi (HKU)",
        "lab": "HKU CVMI Lab",
        "homepage": "https://yihua7.github.io/website/",
        "scholar": "https://scholar.google.com/citations?user=zLil53UAAAAJ",
        "direction": "3D/4D生成 / 重建 / 仿真与编辑",
        "gradYear": "~2027",
        "statusNote": "AniGen SIGGRAPH2026第一作者。中科院计算所硕士→HKU PhD。多篇CVPR/SIGGRAPH/NeurIPS一作。曾在VAST和腾讯实习。",
        "editedAt": today,
        "contactInfo": {
            "emails": [],
            "wechat": [],
            "phone": [],
            "cv": [],
            "social": {"github": "yihua7"},
            "scannedAt": today,
            "hasContactKeywords": False,
            "hasContact": False
        }
    },
    "Zhefan Rao": {
        "name": "饶哲凡 (Zhefan Rao)",
        "university": "香港科技大学 (HKUST)",
        "isHK": True,
        "status": "博士在读 (MPhil 2023毕业后转PhD)",
        "advisor": "Qifeng Chen (HKUST)",
        "lab": "HKUST Qifeng Chen Lab",
        "homepage": "",
        "scholar": "https://scholar.google.com/citations?user=8yjKlAEAAAAJ",
        "direction": "图像/视频编辑 / 扩散模型",
        "gradYear": "待确认",
        "statusNote": "InsEdit共同第一作者。2023年MPhil毕业后继续读PhD。",
        "editedAt": today
    },
    "Xuanhua He": {
        "name": "何轩华 (Xuanhua He)",
        "university": "香港科技大学 (HKUST)",
        "isHK": True,
        "status": "博士在读",
        "advisor": "Qifeng Chen (HKUST)",
        "lab": "HKUST Qifeng Chen Lab",
        "homepage": "",
        "scholar": "",
        "direction": "待确认",
        "gradYear": "待确认",
        "statusNote": "InsEdit论文作者，确认在Qifeng Chen实验室名单中。",
        "editedAt": today
    },
}

# Add new talents
added = 0
skipped = 0
for name, info in new_talents.items():
    if name not in data["notes"]:
        data["notes"][name] = info
        added += 1
        print(f"  ADDED: {name} ({info['university']})")
    else:
        skipped += 1
        print(f"  SKIPPED (exists): {name}")

data["generatedAt"] = datetime.now().isoformat() + "Z"

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nDone: +{added} new, {skipped} skipped, total = {len(data['notes'])}")
