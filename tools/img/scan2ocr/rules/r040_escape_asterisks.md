# 040 — Escape literal `*` in the OCR `.md`

**Applies to:** all — a character-class transform on the `.md`; no issue-specific input.

**Goal:** prevent the markdown→HTML converter from interpreting literal asterisks (BASIC multiplication, ESC sequences, wildcards, "(***)" markers, …) as emphasis. Keep real `**bold**` spans intact.

## Rule

For every contiguous run of `*` in the file:
- **length == 2** → keep **only if it pairs within the paragraph**; an unpaired
  `**` is a literal and is escaped.
- **any other length** (1, 3, 4, …) → escape each `*` to `\*`.

"Length 2 is always bold" is false. 8612's Protext article renders space
padding as asterisks — `Der**Mann*schläft.` / `Der*Mann**schläft.` — so each
line carries one literal `**`, which this rule kept as a bold delimiter. All of
the fence-aware checks read 0, because an unpaired delimiter is invisible to a
pair count.

That covers:
- `*` (one) → `\*` (BASIC multiply, wildcard, literal star)
- `***` → `\*\*\*` (three literal asterisks)
- `****` → `\*\*\*\*` (four literal asterisks)
- `**foo**` → `**foo**` (unchanged, real bold)

### The same pass escapes a leading `#` that is not a heading

A body line that starts with `#` becomes an ATX heading. SH8603 p164 prints a
bullet wrapping onto `#1281/1282=$0501/0502.` (`#` for decimal, against `$`
for hex); Discount needs no space after the `#`, so 060 shipped
`<h1>1281/1282=$0501/0502.</h1>` — the `#` lost, and a 52nd `<h1>` created
that 080 then split articles on.

**THE TEST IS THE SPACE.** A real ATX heading has whitespace after its hashes;
the defect is a hash run with none. 030 emits `#`, `##` AND `###` — article
titles, section headings and sub-headings — so anything narrower than the
space test eats real headings: a version that exempted only lines carrying
`[digit` (on the false belief that 030 emits nothing but `# Title [pages]`)
escaped all 69 of SH8604's `##`/`###` and stopped that build at 040.

## Usage

```bash
tools/img/scan2ocr/rules/r040_escape_asterisks.sh issues/8607/8607.md
```

The script rewrites the file in place. Idempotent: re-running is a no-op once it's clean (escaped `\*` doesn't match the unescape-eligible pattern).

## Verification

The script's own closing summary is fence-aware, and says so (`outside
fences`). It was not: on SH8603 it counted the whole file and printed
`solitary=2` for two asterisks it had just correctly left alone inside
listings — reporting its own correct output as a defect, which is exactly what
the docstring below warns about. A check that fails on a good result gets
"fixed" by undoing the transform.

All three asterisk counts are over the text **outside fenced code**, and all
three should be **zero**. Inside a fence an unescaped `*` is correct — see the
rule above — so a whole-file count reports the right answer as a failure.

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

Expected: zero solitary, zero 3+ runs.

**And the headings, which is a BEFORE/AFTER count — the one check above cannot
make.** The asterisk counts all read zero while 040 was eating SH8604's 69
sub-headings, because an escaped heading is not an unescaped asterisk. Run this
against the 030 handover and the file 040 just rewrote:

```bash
$PY - <tmp>/ocr/<YYMM>.md issues/<YYMM>/<YYMM>.md <<'PYEOF'
import re, sys
def heads(path):
    n = {}
    for line in open(path, encoding='utf-8'):
        m = re.match(r'^(#{1,6})\s', line)
        if m:
            n[len(m.group(1))] = n.get(len(m.group(1)), 0) + 1
    return n
before, after = heads(sys.argv[1]), heads(sys.argv[2])
for lvl in sorted(set(before) | set(after)):
    b, a = before.get(lvl, 0), after.get(lvl, 0)
    print('%-7s %4d -> %4d  %s' % ('#' * lvl, b, a, 'OK' if a == b else 'LOST %d' % (b - a)))
print('escaped \\# lines  :', sum(1 for l in open(sys.argv[2], encoding='utf-8')
                                 if l.lstrip().startswith('\\#')))
PYEOF
```

Expected: **every level unchanged**. A `LOST` at any level means the escape
reached a real heading, and the fix is the lookahead, never deleting the check.
The `\#` line count is a readout: it should equal the number of genuine
no-space hash runs in the issue, which is normally 0 and was 1 in SH8603. The `**bold**` pair count is
**invariant by construction** — the escape rule only rewrites runs of
length ≠ 2, so it never touches a length-2 `**` delimiter. There's no
"before" count to compare against; the invariant is that the escape
pass cannot change it. (The count is printed only as a sanity readout,
not a pass/fail check.)

## Notes / lessons

- The naive `** → SENTINEL / * → \* / SENTINEL → **` swap mis-handles 3+-runs (left-pairs `***` as `** + *` instead of three literals). Use the run-length rule instead.
- **A line-start `* ` IS a bullet, and the script converts it to `- ` before
  escaping.** The old Note here claimed "list bullets in this project are always
  `-`, never `*`, so escaping every solitary `*` won't break lists" — false
  twice over: SH8602 had 9 such lines, SH8603 13 (the printer checklist,
  pp47–49), all escaped as the Note promised was safe and all left rendering as
  literal asterisks for 190 to rebuild by hand.
  Only the line start converts. MEASURED on SH8603's 030 handover outside
  fences: 7 line-start `* ` lines, all 7 bullets of that checklist — and 7 lines
  with a mid-paragraph ` * `, among them `POKE 44,30:POKE 30 * 256,0:NEW`. A
  blanket swap rewrites BASIC multiplication into a dash that 070 then makes an
  en dash. SH8604 has 0 of the line-start shape, so the pass fires only where
  the shape is actually there.
- **A run-together bullet list is 190's, not 040's.** Where the OCR glues the
  next item onto the previous line (`… keine Hürde sein. * Der
  Commodore-Zeichensatz …`, SH8603 p47) the marker is mid-line and
  indistinguishable from multiplication, so it stays escaped. r190 rebuilds it
  from the page.
- The script is idempotent because `\*` matches neither the solitary nor the 3+-run pattern.
- The hash lookahead is `(?![#\s])`, not `(?!\s)`: a greedy `#+` backtracks. On
  `## Heading` it matches `##`, fails the space lookahead, backtracks to a single
  `#` whose next character is `#`, and escapes the heading after all.
