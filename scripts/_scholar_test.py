#!/usr/bin/env python3
"""
CUHK CSE Faculty + Citation lookup via scholarly
Step 1: Use known Scholar IDs to get citation counts
"""
import json, time, sys

# CUHK CSE Faculty with Scholar IDs (from official website)
FACULTY = [
    {"name": "Evangeline F.Y. Young", "title": "Professor & Chairman", "area": "AI, VLSI CAD", "scholar_id": "dRpbUkMAAAAJ"},
    {"name": "Pheng Ann Heng", "title": "Choh-Ming Li Professor", "area": "AI, Computer Graphics, VR Medical", "scholar_id": "OFdytjoAAAAJ"},
    {"name": "Michael Rung Tsong Lyu", "title": "Choh-Ming Li Professor", "area": "ML, Big Data, Software Engineering", "scholar_id": "uQnBgK0AAAAJ"},
    {"name": "Chi Wing Fu", "title": "Professor", "area": "AI, HCI, CV, AR/VR", "scholar_id": "e5AJDrEAAAAJ"},
    {"name": "Tsung-Yi Ho", "title": "Professor", "area": "ML, VLSI CAD, Quantum Computing", "scholar_id": "TRDUYkAAAAAJ"},
    {"name": "Irwin King", "title": "Professor", "area": "Deep Learning, NLP, Social Computing", "scholar_id": "MXvC7tkAAAAJ"},
    {"name": "Jimmy Ho Man Lee", "title": "Professor", "area": "AI, Constraint Satisfaction", "scholar_id": "3IV-UTsAAAAJ"},
    {"name": "Patrick P.C. Lee", "title": "Professor", "area": "Cloud Computing, Distributed Systems", "scholar_id": "gyRtVVEAAAAJ"},
    {"name": "Sinno Jialin Pan", "title": "Professor", "area": "Deep Learning, ML", "scholar_id": "P6WcnfkAAAAJ"},
    {"name": "Zili Shao", "title": "Professor", "area": "Embedded Systems, Big Data", "scholar_id": "HlxIVWYAAAAJ"},
    {"name": "Yufei Tao", "title": "Professor", "area": "ML, Databases, Data Mining", "scholar_id": "3FmJBHkAAAAJ"},
    {"name": "Qiang Xu", "title": "Professor", "area": "AI, VLSI CAD, Cyber Security", "scholar_id": "eSiKPqUAAAAJ"},
    {"name": "Bei Yu", "title": "Professor", "area": "Deep Learning, VLSI CAD, CV", "scholar_id": "tGneTm4AAAAJ"},
    {"name": "Yu Cheng", "title": "Associate Professor", "area": "Deep Learning, ML, CV", "scholar_id": "ORPxbV4AAAAJ"},
    {"name": "Qi Dou", "title": "Associate Professor", "area": "Deep Learning, Medical Image, Robotics", "scholar_id": "iHh7IJQAAAAJ"},
    {"name": "Wei Meng", "title": "Associate Professor", "area": "Software, Cyber Security", "scholar_id": "CBLnYLEAAAAJ"},
    {"name": "Henry Hong Xu", "title": "Associate Professor", "area": "Big Data, Distributed Systems", "scholar_id": "BZHzIFIAAAAJ"},
    {"name": "Ming-Chang Yang", "title": "Associate Professor", "area": "Computer Architecture, Storage", "scholar_id": "sVkR5hYAAAAJ"},
    {"name": "Farzan Farnia", "title": "Assistant Professor", "area": "Deep Learning, ML, Optimization", "scholar_id": "GYPCqcYAAAAJ"},
    {"name": "Shaohua Li", "title": "Assistant Professor", "area": "DL, Cyber Security, Compilers", "scholar_id": "MwJw4YwAAAAJ"},
    {"name": "Yu Li", "title": "Assistant Professor", "area": "Bioinformatics, DL, Healthcare", "scholar_id": "8YHZx-AAAAAJ"},
    {"name": "Xiao Liang", "title": "Assistant Professor", "area": "Cryptography, Quantum Computing", "scholar_id": "pUCv_e4AAAAJ"},
    {"name": "Zhiding Liang", "title": "Assistant Professor", "area": "Computer Architecture, Quantum", "scholar_id": "bsLRScYAAAAJ"},
    {"name": "Shengchao Liu", "title": "Assistant Professor", "area": "AI for Science, Bioinformatics", "scholar_id": "F1ws3XUAAAAJ"},
    {"name": "Weiyang Liu", "title": "Assistant Professor", "area": "Generative AI, LLMs, CV", "scholar_id": "DMjROf0AAAAJ"},
    {"name": "Songtao Lu", "title": "Assistant Professor", "area": "AI, DL, ML, Optimization", "scholar_id": "LRsjX7kAAAAJ"},
    {"name": "Liwei Wang", "title": "Assistant Professor", "area": "DL, ML, CV, NLP", "scholar_id": "qnbdnZEAAAAJ"},
    {"name": "Zhengrong Wang", "title": "Assistant Professor", "area": "DL, Architecture, Distributed Systems", "scholar_id": "h_GwGfQAAAAJ"},
    {"name": "Hanrui Zhang", "title": "Assistant Professor", "area": "AI, ML, Theory", "scholar_id": "vzr_L0EAAAAJ"},
    {"name": "Shi Qiu", "title": "Research Asst Professor", "area": "DL, HCI, Medical Image, CV", "scholar_id": "OPNVthUAAAAJ"},
    {"name": "Mengya Xu", "title": "Research Asst Professor", "area": "AI Medical, DL, Robotics, CV", "scholar_id": "Uq5qvyAAAAAJ"},
    # By courtesy / Adjunct
    {"name": "Hong Cheng", "title": "Professor (courtesy)", "area": "DL, ML, Big Data", "scholar_id": "s3lQL7YAAAAJ"},
    {"name": "Hongsheng Li", "title": "Assoc Prof (courtesy)", "area": "CV, DL", "scholar_id": "BN2Ze-QAAAAJ"},
    {"name": "Dahua Lin", "title": "Assoc Prof (courtesy)", "area": "CV, DL", "scholar_id": "GMzzRRUAAAAJ"},
    {"name": "Guoliang Xing", "title": "Professor (courtesy)", "area": "Embedded AI, Systems", "scholar_id": "kI5JKs8AAAAJ"},
    {"name": "Sibo Wang", "title": "Assoc Prof (courtesy)", "area": "Databases", "scholar_id": "b2gLqsgAAAAJ"},
    {"name": "Jiaya Jia", "title": "Adjunct Professor", "area": "ML, CV, Computational Photography", "scholar_id": "XPAkzTEAAAAJ"},
    {"name": "Tien Tsin Wong", "title": "Adjunct Professor", "area": "Graphics", "scholar_id": "05U81tIAAAAJ"},
]

print(f"=== CUHK CSE Faculty: {len(FACULTY)} with Scholar IDs ===")
print("Fetching citation counts via scholarly...\n")

from scholarly import scholarly

results = []
for i, f in enumerate(FACULTY):
    try:
        author = scholarly.search_author_id(f["scholar_id"])
        citations = author.get("citedby", 0) or 0
        interests = author.get("interests", [])
        f["citations"] = citations
        f["interests"] = interests
        f["scholar_url"] = f"https://scholar.google.com/citations?user={f['scholar_id']}"
        results.append(f)
        flag = " ⭐" if citations >= 10000 else (" ✅" if citations >= 1000 else "")
        print(f"  [{i+1:2d}/{len(FACULTY)}] {f['name']:<30s} | {citations:>7,d} citations | {f['title']}{flag}")
        time.sleep(1.5)  # gentle
    except Exception as e:
        print(f"  [{i+1:2d}/{len(FACULTY)}] {f['name']:<30s} | ERROR: {e}")
        f["citations"] = -1
        results.append(f)
        if "429" in str(e) or "blocked" in str(e).lower():
            print("  ⚠️ Rate limited! Stopping.")
            break
        time.sleep(3)

# Sort by citations
results.sort(key=lambda x: x.get("citations", 0), reverse=True)

print(f"\n=== Results: {len(results)} faculty ===")
over1k = [r for r in results if r.get("citations", 0) >= 1000]
over10k = [r for r in results if r.get("citations", 0) >= 10000]
print(f"Citations >= 1,000: {len(over1k)}")
print(f"Citations >= 10,000: {len(over10k)}")

with open("reports/_cuhk_cse_faculty.json", "w", encoding="utf-8") as fp:
    json.dump(results, fp, ensure_ascii=False, indent=2)
print("Saved to reports/_cuhk_cse_faculty.json")
