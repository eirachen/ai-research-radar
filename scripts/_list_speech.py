"""List all Speech papers and fix false positives."""
import json

with open("reports/arxiv-daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== All Speech-tagged papers ===")
count = 0
false_positives = []
for cid, c in data["companies"].items():
    for p in c["papers"]:
        dirs = [d["id"] for d in (p.get("directions") or [])]
        if "Speech" in dirs:
            count += 1
            title = p.get("title", "")[:80]
            cats = p.get("categories", [])
            is_audio_cat = any(cat in ["eess.AS", "cs.SD"] for cat in cats)
            
            # Check for false positives (papers that have "DAC" match but aren't speech)
            text = (p.get("title", "") + " " + p.get("summary", "")).lower()
            speech_core = any(kw in text for kw in ["speech", "asr", "tts", "voice", "audio", "spoken", "music", "singing"])
            
            marker = "✅" if (is_audio_cat or speech_core) else "⚠️ FALSE?"
            print(f"  {count}. {marker} [{c['company']}] {title}")
            print(f"     cats={cats} dirs={dirs}")
            
            if not (is_audio_cat or speech_core):
                false_positives.append((cid, p["arxivId"]))

# Remove false positives
if false_positives:
    print(f"\n=== Removing {len(false_positives)} false positives ===")
    for cid, arxiv_id in false_positives:
        for p in data["companies"][cid]["papers"]:
            if p["arxivId"] == arxiv_id:
                p["directions"] = [d for d in p["directions"] if d["id"] != "Speech"]
                print(f"  - Removed Speech from: {p['title'][:60]}")
    
    with open("reports/arxiv-daily.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    count -= len(false_positives)

print(f"\nFinal Speech paper count: {count}")
