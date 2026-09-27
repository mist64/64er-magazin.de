# 040 — Escape literal `*` in the OCR `.md`

**Applies to:** all — a character-class transform on the `.md`; no issue-specific input.

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
tools/img/scan2ocr/rules/r040_escape_asterisks.sh issues/8607/8607.md
```

The script rewrites the file in place. Idempotent: re-running is a no-op once it's clean (escaped `\*` doesn't match the unescape-eligible pattern).

## Verification

All three counts are over the text **outside fenced code**, and all three
should be **zero**. Inside a fence an unescaped `*` is correct — see the rule
above — so a whole-file count reports the right answer as a failure.

```bash
$PY - issues/<YYMM>/<YYMM>.md <<'PYEOF'
import re, sys
def outside_fences(s):
    """The file's text with every ```-fenced region blanked out.

    A CHECK MUST BE AS FENCE-AWARE AS THE TRANSFORM IT CHECKS. When 040 and 050
    stopped escaping inside fences, these blocks went on counting the whole file
    and began FAILING ON CORRECT OUTPUT -- 040 reported 4 solitary asterisks,
    all 4 correctly left alone inside listings. A check that fails on a good
    result gets "fixed" by undoing the transform, which is how a corrected bug
    comes back.
    """
    out, infence = [], False
    for line in s.splitlines(keepends=True):
        if line.lstrip().startswith('```'):
            infence = not infence
            out.append('\n')
            continue
        out.append('\n' if infence else line)
    return ''.join(out)

s = outside_fences(open(sys.argv[1], encoding='utf-8').read())
print('unescaped solitary *:', len(re.findall(r'(?<!\\)(?<!\*)\*(?!\*)', s)))
print('3+ contiguous runs   :', len(re.findall(r'\*{3,}', s)))
print('**bold** pairs       :', len(re.findall(r'\*\*[^*]+?\*\*', s)))
PYEOF
```

Expected: zero solitary, zero 3+ runs. The `**bold**` pair count is
**invariant by construction** — the escape rule only rewrites runs of
length ≠ 2, so it never touches a length-2 `**` delimiter. There's no
"before" count to compare against; the invariant is that the escape
pass cannot change it. (The count is printed only as a sanity readout,
not a pass/fail check.)

## Notes / lessons

- The naive `** → SENTINEL / * → \* / SENTINEL → **` swap mis-handles 3+-runs (left-pairs `***` as `** + *` instead of three literals). Use the run-length rule instead.
- List bullets in this project are always `-`, never `*` — so escaping every solitary `*` won't break lists.
- The script is idempotent because `\*` matches neither the solitary nor the 3+-run pattern.
