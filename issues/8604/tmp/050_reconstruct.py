#!/usr/bin/env python3
"""
Reconstruct OCR text from Tesseract TSV output with correct two-column reading order.

Reads 050_ocr.tsv, groups words into lines and blocks, assigns blocks to
left/right columns based on x-coordinate, then outputs text in proper
reading order (left column top-to-bottom, then right column top-to-bottom).
"""

import csv
from collections import defaultdict

INPUT  = "/Users/mist/Documents/git/64er-magazin.de/issues/8604/tmp/050_ocr.tsv"
OUTPUT = "/Users/mist/Documents/git/64er-magazin.de/issues/8604/tmp/050_ocr.txt"

PAGE_WIDTH = 2480
MIDPOINT = PAGE_WIDTH // 2  # 1240

# Step 1: Read level-5 rows with non-empty text
words = []
with open(INPUT, newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        if row["level"] == "5" and row["text"].strip():
            words.append({
                "block":    int(row["block_num"]),
                "par":      int(row["par_num"]),
                "line":     int(row["line_num"]),
                "word_num": int(row["word_num"]),
                "left":     int(row["left"]),
                "top":      int(row["top"]),
                "width":    int(row["width"]),
                "height":   int(row["height"]),
                "conf":     float(row["conf"]),
                "text":     row["text"],
            })

# Step 2: Group words into lines keyed by (block, par, line)
lines = defaultdict(list)
for w in words:
    key = (w["block"], w["par"], w["line"])
    lines[key].append(w)

# Sort words within each line by word_num
for key in lines:
    lines[key].sort(key=lambda w: w["word_num"])

# Step 3: Compute block-level info
block_info = {}
for key, wlist in lines.items():
    block_num = key[0]
    for w in wlist:
        if block_num not in block_info:
            block_info[block_num] = {
                "left":  w["left"],
                "top":   w["top"],
                "right": w["left"] + w["width"],
                "first_words": [],
            }
        info = block_info[block_num]
        info["left"]  = min(info["left"],  w["left"])
        info["top"]   = min(info["top"],   w["top"])
        info["right"] = max(info["right"], w["left"] + w["width"])

# Collect first few words per block for the summary
for key, wlist in sorted(lines.items()):
    block_num = key[0]
    if block_num in block_info and not block_info[block_num]["first_words"]:
        block_info[block_num]["first_words"] = [w["text"] for w in wlist[:8]]

# Assign column based on the block's leftmost x-coordinate
for bn, info in block_info.items():
    info["column"] = "LEFT" if info["left"] < MIDPOINT else "RIGHT"
    info["width"] = info["right"] - info["left"]

# Step 4: Print block summary
print("=" * 100)
print(f"{'Block':>5}  {'Left':>5}  {'Top':>5}  {'Width':>5}  {'Column':<6}  First words")
print("-" * 100)
for bn in sorted(block_info.keys()):
    info = block_info[bn]
    preview = " ".join(info["first_words"])[:70]
    print(f"{bn:>5}  {info['left']:>5}  {info['top']:>5}  {info['width']:>5}  {info['column']:<6}  {preview}")
print("=" * 100)
print()

# Step 5: Build paragraphs grouped by (block, par)
paragraphs = defaultdict(list)
for key, wlist in lines.items():
    block_num, par_num, line_num = key
    text_line = " ".join(w["text"] for w in wlist)
    top = min(w["top"] for w in wlist)
    paragraphs[(block_num, par_num)].append((line_num, text_line, top))

# Sort lines within each paragraph
for key in paragraphs:
    paragraphs[key].sort(key=lambda x: x[0])

# Step 6: Sort paragraphs by column then top
para_list = []
for (block_num, par_num), line_list in paragraphs.items():
    info = block_info[block_num]
    col_order = 0 if info["column"] == "LEFT" else 1
    top = min(t for _, _, t in line_list)
    text = "\n".join(txt for _, txt, _ in line_list)
    para_list.append((col_order, top, block_num, par_num, text))

para_list.sort(key=lambda x: (x[0], x[1]))

# Step 7: Write output
output_lines = []
prev_col = None
for col_order, top, block_num, par_num, text in para_list:
    col_name = "LEFT" if col_order == 0 else "RIGHT"
    if prev_col is not None and col_name != prev_col:
        output_lines.append("")
        output_lines.append("--- [right column] ---")
        output_lines.append("")
    prev_col = col_name
    output_lines.append(text)
    output_lines.append("")  # blank line between paragraphs

output_text = "\n".join(output_lines).rstrip() + "\n"

with open(OUTPUT, "w") as f:
    f.write(output_text)

print(f"Output written to {OUTPUT}")
print(f"Total paragraphs: {len(para_list)}")
print(f"Total words: {len(words)}")

# Print the full reconstructed text
print()
print("=" * 70)
print("RECONSTRUCTED TEXT")
print("=" * 70)
print(output_text)
