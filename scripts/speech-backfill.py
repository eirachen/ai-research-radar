"""
语音领域专区回填脚本
1. 用更丰富的语音关键词重新扫描所有已有论文
2. 为匹配的论文补标 Speech direction
3. 统一 direction label 格式（"Speech" label 应为 "语音"）
"""
import json, os, sys, re

# 增强版语音关键词（比 scan-arxiv.py 中的更全面）
SPEECH_KEYWORDS = [
    # 核心语音技术
    "speech", "ASR", "TTS", "text-to-speech", "speech-to-text",
    "voice", "audio", "spoken language", "music",
    "speech recognition", "speech synthesis", "speech generation",
    "voice conversion", "voice cloning", "voice clone",
    "speech enhancement", "speech separation", "speech denoising",
    # 模型/系统名
    "Seed-TTS", "Seeduplex", "CosyVoice", "VALL-E", "Bark",
    "Whisper", "MusicGen", "AudioLDM", "SoundStorm", "XTTS",
    "FireRedASR", "Qwen-Audio", "Qwen2-Audio",
    "MiniMax-Speech", "MiniMax Music", "MARS5",
    # 技术术语
    "acoustic model", "prosody", "phoneme", "vocoder",
    "mel spectrogram", "waveform", "audio codec", "neural codec",
    "sound event", "audio captioning", "audio understanding",
    "audio language model", "audio LLM", "LALM",
    "singing", "melody", "speaker", "diarization",
    "duplex", "full-duplex", "streaming ASR",
    "end-to-end speech", "speech token", "speech codec",
    "SoundStream", "EnCodec", "DAC",
    # arXiv 分类
    "eess.AS", "cs.SD",
]

SPEECH_DIRECTION = {"id": "Speech", "label": "语音", "color": "#14b8a6"}

def has_speech_direction(directions):
    return any(d.get("id") == "Speech" for d in (directions or []))

def match_speech(title, summary, categories, deepxiv_kw=None):
    """Check if paper matches speech domain using enhanced keywords."""
    text = (title + " " + summary).lower()
    cats = " ".join(categories or []).lower()
    
    score = 0
    matched = []
    for kw in SPEECH_KEYWORDS:
        if kw.lower() in text or kw.lower() in cats:
            score += 1
            matched.append(kw)
    
    # Also check deepxivKeywords if available
    if deepxiv_kw:
        dkw_text = " ".join(deepxiv_kw).lower()
        for kw in SPEECH_KEYWORDS:
            if kw.lower() in dkw_text:
                score += 1
                matched.append("dxkw:" + kw)
    
    return score, matched

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "..", "reports", "arxiv-daily.json")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    total_papers = 0
    already_speech = 0
    newly_tagged = 0
    label_fixed = 0
    
    for cid, company in data.get("companies", {}).items():
        for paper in company.get("papers", []):
            total_papers += 1
            
            # Fix inconsistent label: "Speech" → "语音"
            for d in (paper.get("directions") or []):
                if d.get("id") == "Speech" and d.get("label") != "语音":
                    d["label"] = "语音"
                    d["color"] = "#14b8a6"
                    label_fixed += 1
            
            if has_speech_direction(paper.get("directions")):
                already_speech += 1
                continue
            
            # Check if this paper should be tagged as Speech
            title = paper.get("title", "")
            summary = paper.get("summary", "")
            tldr = paper.get("tldr", "")
            categories = paper.get("categories", [])
            deepxiv_kw = paper.get("deepxivKeywords", [])
            
            score, matched = match_speech(
                title, summary + " " + tldr, categories, deepxiv_kw
            )
            
            if score >= 2:  # Need at least 2 keyword matches
                # Add Speech direction
                dirs = paper.get("directions", [])
                dirs.append(SPEECH_DIRECTION.copy())
                paper["directions"] = dirs
                newly_tagged += 1
                print(f"  + [{company['company']}] {title[:70]}...")
                print(f"    matched: {matched[:5]}")
    
    print(f"\n=== Speech Backfill Summary ===")
    print(f"Total papers scanned: {total_papers}")
    print(f"Already had Speech tag: {already_speech}")
    print(f"Newly tagged as Speech: {newly_tagged}")
    print(f"Label format fixed: {label_fixed}")
    print(f"Total Speech papers now: {already_speech + newly_tagged}")
    
    # Save
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {json_path}")

if __name__ == "__main__":
    main()
