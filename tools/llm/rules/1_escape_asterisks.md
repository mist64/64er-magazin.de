# 1 — Escape literal `*` in the OCR `.md`

**Goal:** prevent the markdown→HTML converter from interpreting literal asterisks (BASIC multiplication, ESC sequences, wildcards, "(***)" markers, …) as emphasis. Keep real `**bold**` spans intact.

## Rule

For every contiguous run of `*` in the file:
- **length == 2** → keep (it's a `**bold**` delimiter).
- **any other length** (1, 3, 4, …) → escape each `*` to `\*`.

That covers:
- `*` (one) → `\*` (BASIC multiply, wildcard, literal star)
- `***` → `\*\*\*` (three literal asterisks)
- `****` → `\*\*\*\*` (four literal asterisks)
- `**foo**` → `**foo**` (unchanged, real bold)

## Usage

```bash
tools/llm/rules/1_escape_asterisks.sh issues/8607/8607.md
```

The script rewrites the file in place. Idempotent: re-running is a no-op once it's clean (escaped `\*` doesn't match the unescape-eligible pattern).

## Verification

After running, all three counts should be **zero**:

```bash
python3 -c "
import re, sys
s = open(sys.argv[1]).read()
print('unescaped solitary *:', len(re.findall(r'(?<!\\\\)(?<!\\*)\\*(?!\\*)', s)))
print('3+ contiguous runs   :', len(re.findall(r'\\*{3,}', s)))
print('**bold** pairs       :', len(re.findall(r'\\*\\*[^*]+?\\*\\*', s)))
" issues/8607/8607.md
```

Expected: zero solitary, zero 3+ runs, **bold** pair count unchanged from before.

## Notes / lessons

- The naive `** → SENTINEL / * → \* / SENTINEL → **` swap mis-handles 3+-runs (left-pairs `***` as `** + *` instead of three literals). Use the run-length rule instead.
- List bullets in this project are always `-`, never `*` — so escaping every solitary `*` won't break lists.
- The script is idempotent because `\*` matches neither the solitary nor the 3+-run pattern.
