"""
Test: Download arXiv PDF first page, extract author-affiliation pairs
"""
import urllib.request
import pdfplumber
import tempfile
import os
import re

# Test with HingeMem paper
pdf_url = "https://arxiv.org/pdf/2604.06845v1"

print("Downloading PDF...")
req = urllib.request.Request(pdf_url, headers={"User-Agent": "AI-Research-Radar/2.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    pdf_data = resp.read()

# Save to temp file
tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
tmp.write(pdf_data)
tmp.close()

print(f"PDF size: {len(pdf_data)} bytes")

# Extract first page text
with pdfplumber.open(tmp.name) as pdf:
    page1 = pdf.pages[0]
    text = page1.extract_text()

os.unlink(tmp.name)

print("\n=== FIRST PAGE TEXT (first 2000 chars) ===")
print(text[:2000] if text else "NO TEXT EXTRACTED")

# Try to parse author-affiliation
# Common patterns:
# Author1 1, Author2 2, Author3 1,2
# 1 University A  2 Company B
print("\n=== ANALYSIS ===")
lines = text.split('\n') if text else []
for i, line in enumerate(lines[:30]):
    print(f"  L{i}: {line.strip()[:120]}")
