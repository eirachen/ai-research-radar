"""Check talent-notes.json stats"""
import json, os
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports", "talent-notes.json")
d = json.load(open(path, "r", encoding="utf-8"))
notes = d["notes"]
print(f"Total talents: {len(notes)}")
hk = [n for n in notes.values() if n.get("isHK")]
print(f"HK talents: {len(hk)}")
# Check if our new paper authors are already in the database
check_names = [
    "Qifeng Chen", "Zhefan Rao", "Xuanhua He", "Yanheng Li",
    "Taku Komura", "Rui Xu", "Xiaojuan Qi", "Yi-Hua Huang", "Yuting He",
    "Bo Yang", "Siyuan Zhou"
]
for name in check_names:
    if name in notes:
        n = notes[name]
        print(f"  FOUND: {name} -> {n.get('university', '?')} (HK={n.get('isHK')})")
    else:
        print(f"  NEW: {name}")
