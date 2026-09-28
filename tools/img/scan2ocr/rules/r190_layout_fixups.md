# 190 — Fix line breaks, lists, indentation, inline callouts

**Applies to:** all — mechanical formatting markers, no issue-specific input.

**Goal:** resolve the mechanical formatting TODO markers the OCR/import
pipeline leaves behind: `<p>TODO PRE</p>`, `<p>TODO INDENTATION</p>`,
`<p>TODO INDENTED</p>`, `<p>TODO ASIDE</p>` (non-bio), `<p>TODO
BOX</p>`, plus general line-break / empty-paragraph / list-marker
cleanup.

This rule explicitly **excludes** content-reconstruction TODO markers:
`TODO FORMULA` (math markup is editorial), `TODO ALL BOXES LIKE
BELOW` (needs fresh OCR of box content), and content placeholders
like `<p>TODO two boxes with text</p>`. Those belong to a separate
editorial pass.

This rule handles every `<aside>` callout — methodology, contest,
feature list, warning, and author bio alike. (Author bios used to be rule `15`'s own pass; that rule was removed, because a
bio box is simply one more tinted box and the reliable evidence for a tinted box
is the scan, not the prose inside it.

⚠️ Step 010 *measures* a screened background — the pure-white pixel fraction is
0.004–0.009 on a tint against 0.668–0.719 on paper, two orders of magnitude, see
`FINDINGS.md` — but it does **not yet emit an aside marking** into the corpus.
Until it does, finding the boxes is this rule's own job, from the scan.)

## Briefing for the sub-agent

The sub-agent must:


```bash
# The repo venv, not bare python3: r010_ocr_blocks imports numpy and scipy,
# which the system python does not have, so `python3` makes SRC silently EMPTY
# and every crop below then fails on "/NNN.png". MEASURED on 8611.
PY=${PYTHON:-.venv/bin/python}
SRC=$("$PY" -c 'import sys; sys.path.insert(0, "tools/img/scan2ocr/rules")
import r010_ocr_blocks as OB; print(OB.SRC_DIR)')     # <tmp>/masters600
```

1. The page image is `"$SRC/NNN.png"` from `masters600` — 600 dpi, A4,
   deskewed. For a 300 dpi look, `-resize 50%` of that; never a render of
   the issue PDF, which does not exist until step 006. See r000, *THE PAGE
   IMAGE IS `masters600`*.
2. Walk every `<p>TODO …</p>` marker in `issues/<YYMM>/*.html`:

   | Marker | Action |
   |---|---|
   | `TODO PRE` | Look at the following `<p>…<br>…</p>` block. If the print shows monospace code, fold into `<pre>…</pre>`. If the print shows a real numbered/bulleted list, convert to `<ol>`/`<ul>` instead (and delete the marker). |
   | `TODO INDENTATION` / `TODO INDENTED` | Look at the print indentation. If code → `<pre>`. If prose with visual indent for nested enumeration → `&nbsp;`-prefixed `<br>` inside `<p>`. If real nested list → nested `<ul>`/`<ol>`. |
   | `TODO ASIDE` | Wrap the following heading + paragraphs + closing `<address>` in `<aside>`. Delete the marker. Author bios included — they are asides like any other. |
   | `TODO BOX` | Same as TODO ASIDE if the print shows a boxed callout. If the print shows indented monospace code with no box border, use `<pre>` instead. |
   | `TODO FORMULA` / `TODO FORMULAS` | **SKIP** — editorial (math markup decision). Report unfilled. |
   | `TODO ALL BOXES LIKE BELOW` | **SKIP** content reconstruction — fresh OCR of multiple boxes is out of scope. |
   | `TODO two boxes with text` (or similar content stubs) | **SKIP** content reconstruction. |

3. Light general formatting sweep:
   - Delete `<p>` paragraphs containing only `&nbsp;` or only
     whitespace.
   - Drop a trailing `<br>` immediately before `</p>`.
   - Convert prose-looking enumeration to `<ul>` / `<ol>` **only**
     when the print shows a real bullet glyph or number prefix on
     each item; if the print is just numbered prose ("1. ein,
     2. zwei, 3. drei" running text), leave it as `<p>`/`<br>`.
4. Beautify touched files (`npx --yes js-beautify --type html
   --indent-size 4 --wrap-line-length 0 --replace`). **Verify
   `<pre>` blocks survived** (js-beautify preserves them by default
   but sanity-check after each run).
5. **Do not commit.** Return per-marker action table + general-sweep
   summary + list of explicitly-skipped FORMULA / content markers.

Critical guardrails:
- Anti-memory: code inside `<pre>` must come from the existing HTML
  (the OCR import has the bytes); never retype from print.
- "Only convert to lists when print shows a marker glyph" — applies
  here exactly as it does in the markdown→HTML conversion rules.
  Enumeration-looking prose without a real bullet stays `<p>`/`<br>`.
- Every `<aside>` callout is this rule's territory — methodology,
  contest, feature list, warning, author bio.

## `TODO PRE` HAS NO PRODUCER — so find the listings yourself

The marker table above tells you what to do with `TODO PRE`, and **nothing in
this repository emits it.** Step 030 does not; no script does. The only
occurrences outside this rule are two that *shipped* in published SH8504/110,
with their BASIC listings still sitting in `<p>` underneath them. So the
handling has been dead for the whole recent run.

The cause upstream is step 020 giving a short `listing-inline` block the `body`
role instead of a code role. Until that is fixed, sweep for it here:

```bash
$PY - issues/<YYMM> <<'PYEOF'
import glob, os, re, sys
KW = r'(?:REM|PRINT|POKE|DATA|FOR|IF|GOTO|GOSUB|INPUT|READ|NEXT|OPEN|SYS|LET|DIM|END)'
BAS = re.compile(r'(?:^|<br>|\n)\s*\d{1,5}\s+' + KW, re.I)
# MNEMONICS MUST BE LINE-ANCHORED AND CARRY AN OPERAND. An unanchored \bdec\b
# matches BASIC's DEC( function and German prose; that version produced 135
# blocks corpus-wide, effectively all false.
ASM = re.compile(r'(?:^|<br>|\n)\s*(?:lda|sta|jsr|jmp|ldx|ldy|cmp|beq|bne|inx|iny|adc|sbc|asl|lsr)\s+[#$(]', re.I)
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.html'))):
    s = open(f, encoding='utf-8').read()
    for m in re.finditer(r'<p[^>]*>(.*?)(?=</p>|<p[^>]*>)', s, re.S):
        t = m.group(1)
        if len(BAS.findall(t)) >= 2 or len(ASM.findall(t)) >= 2:
            kind = 'in <p><code>' if '<code>' in t else 'in BARE <p>'
            print(f"  listing {kind}: {os.path.basename(f)}: {re.sub(r'\s+', ' ', t)[:64]}")
PYEOF
```

Two BASIC line numbers each followed by a keyword is the threshold: one is
ordinary prose quoting a line, two is a listing. Expect a handful per issue —
around 7 to 14 on recent ones — so a flood means the pattern broke.

**Most of what it prints is CORRECT, so read the `<code>` column first.**
A multi-line `<p><code>` is this corpus's established form for a snippet quoted
inside the prose flow — 201 of them are published, 14 in 8609, 29 in 8610, 24 in
8611 — and converting those to `<pre>` would be the damage, not the repair. The
three forms, and step 020's own labels decide between them:

| step 020 label | markup | what it is in print |
|---|---|---|
| `listing-standalone` | `<pre>` | a captioned listing set off from the text |
| `listing-inline` | `<p><code>` | a snippet quoted inside a paragraph |
| `body` on code | **the defect** | code with no code markup at all |

So act only on the **BARE `<p>`** hits — code the sweep found with no `<code>`
and no `<pre>` around it. Expect **0 to 3** of those on a recent issue (8611
had one, 8610 three) against a handful of correct `<p><code>` ones. The
`<code>` form starts at 8609: 8607 and earlier have no `<p><code>` at all and
many more bare hits, so do not read them as precedent for a new issue. For those, check whether the line breaks survived as
well: restoring the markup means restoring the lines from the crop, not just
adding a tag.

## The two finders are calibration instruments, not detectors

`r190_find_bold.py` and `r190_find_italic.py` may decide nothing on a real
issue. Two limits to know before spending time on them:

- **Calibrate `HEAVY` per issue, as the docstring demands, and never raise it
  to quieten an issue.** The shipped default (1.40) sits above the docstring's
  own worked example (1.35); measure a known-bold word and a known-roman word
  on the page in hand. `find_italic` is noise at any threshold.
- **A finder cannot see what the OCR did not return.** Where tesseract merged
  or dropped the words — lexicon headwords, for instance — no ink-fraction
  threshold exists at any value. Go to the 600 dpi crop instead.

## Where PRINT and CORPUS PRECEDENT disagree, precedent wins

The print bolds things the monthlies have never marked: Impressum field labels
(`<strong>` in **0 of 32**) and Leserforum question lead-ins (**0 of 31**) are
bold on the page and unmarked in every monthly issue. Follow precedent and
leave them unmarked. Draw precedent from the monthlies only — the Sonderhefte
are a separate series and eight of them do bold the Impressum labels. Fidelity to the artefact is
the job of the page image and the PDF, which keep every one of those bolds; the
HTML owes the reader that two issues of the same magazine look alike.

This does **not** license dropping emphasis that carries meaning. A bold
lead-in that separates one Q&A item from the next is structure, and structure
is content. The test is whether the emphasis distinguishes *this* text from the
text beside it, or merely decorates a field name the layout already sets apart.

## Verification

```bash
dir=issues/<YYMM>

# 1. no in-scope TODO marker survives
# `sort` exits 0 on empty input, so piping into it and testing THAT printed
# the FAIL line unconditionally -- including on a clean issue.  Test the grep.
grep -hoE 'TODO (PRE|INDENTATION|INDENTED|ASIDE|BOX)' "$dir"/*.html \
  | sort -u | grep . && echo "  FAIL: in-scope TODO survived"

# 2. expected-skip TODO markers may still exist
grep -lE 'TODO FORMULA|TODO ALL BOXES|TODO two boxes' "$dir"/*.html \
  > /tmp/skipped_files.txt
echo "  expected skipped markers in $(wc -l < /tmp/skipped_files.txt | tr -d ' ') file(s):"
cat /tmp/skipped_files.txt

# 3. <pre> well-formed
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    o = len(re.findall(r'<pre\b', s)); c = len(re.findall(r'</pre>', s))
    if o != c: print(f"  pre mismatch in {f}: open={o} close={c}")
PY
)" "$dir"

# 4. <aside> well-formed
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    o = len(re.findall(r'<aside\b', s)); c = len(re.findall(r'</aside>', s))
    if o != c: print(f"  aside mismatch in {f}: open={o} close={c}")
PY
)" "$dir"
```

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). To make that failure mode
impossible here, every TODO-marker resolution the sub-agent applies
must be backed by **runnable verifier evidence pasted verbatim into
the report**:

- For each `TODO PRE` / `TODO INDENTATION` / `TODO INDENTED`
  resolution, paste a one-line print-classification note: which page,
  which marker, and which of {`<pre>`, `<ul>`, `<ol>`,
  `&nbsp;`-flattened prose} the print's visual structure mandates.
  E.g. `76 Tips & Tricks p.76 → indented monospace code, no bullet
  glyph → <pre>`.
- For each `TODO ASIDE` / `TODO BOX` resolution, paste a one-line
  confirmation that the print shows a boxed callout (or, for the
  `<pre>` fallback, that it shows indented monospace without a box).
- For each prose→list conversion, paste the one-character bullet
  glyph the print uses (dash, dot, em-dash) so the orchestrator can
  confirm the marker exists. Per the lists-need-marker rule, no
  marker means no `<ul>`/`<ol>`.
- For each explicitly-skipped marker (`TODO FORMULA`, `TODO ALL
  BOXES LIKE BELOW`, content stubs), paste a one-line reason.

**No verifier output, no claimed resolution.** A resolution reported
without the print-classification note is treated as un-applied; the
orchestrator will re-dispatch. "Trust me, I looked at the scan" is
never acceptable.

## Notes / lessons

- 8607 had 4 TODO PRE markers in `76 Tips & Tricks für Einsteiger`
  alone — when one article has several, eyeball the print first to
  see whether they're code, list, or numbered prose; they need not
  all be the same shape.
- `157 Maintext 64` had a 40-item Funktionsübersicht where the
  print showed real dash bullets — that's a `<ul>`, not a
  `&nbsp;`-flattened paragraph.
- `36 Modem mit Wählautomatik`'s monitor-patch stanzas read as
  TODO BOX but were really indented monospace — `<pre>` was the
  right shape, not `<aside>`.
- The `49 Variosystem` C.A.E. "TODO two boxes with text" and the
  10 `TODO FORMULA` placeholders are explicitly out of scope and
  must be left for an editorial pass — flagging them in the report
  is enough.


## Set-off boxes become `<aside>` — decided by BACKGROUND, not by content

The magazine sets sidebars apart visually and the OCR keeps only the words, so
this can only be settled by looking at the page. Any block printed on a **grey
background** or inside a **ruled border** is an `<aside>`:

- grey box: *Computerzeit für Grafikfreunde* (8609 p9), *Floppy und
  Dateiverwaltung* (p11), the manufacturer-address block of the printer
  market survey (p146)
- ruled box: *Die Kuriositätenecke* (p11), and **every `Lebenslauf`** — the
  author-biography box that accompanies a *Listing/Anwendung des Monats* is
  always a bordered box, so always an `<aside>`

Shape rules:
- The aside's heading is an **`<h2>`**.
- **An aside need not have a heading at all** — the p146 address block is a
  grey box with no title; wrap it in a bare `<aside>` rather than inventing one
  or tagging it `<p class="source">`.
- Two adjacent boxes are two asides. A dropped heading makes them look like one:
  *Floppy und Dateiverwaltung* had lost its heading and was swallowed by the
  *Kuriositätenecke* box above it. If an aside contains a second
  `<address class="author">`, suspect a merged neighbour.

## Never split the last paragraph from its `<p class="source">`

An image or table must not be emitted between an article's final paragraph and
its source/`Info:` footer — they belong together. Put the `<figure>` or
`<table>` **after** the source line.

Check: for every `<p class="source">`, the block immediately before it must not
be a `<figure>` or `<table>`.

## NEVER SPLIT THE AUTHOR AWAY FROM THE TEXT THEY WROTE

Extending the rule above: the closing run of an article — **last paragraph →
`<address class="author">` → `<p class="source">`** — is a unit. **Nothing may
be emitted inside it: not a `<figure>`, not a `<table>`, not a `<pre>`, not an
`<aside>`.** Move whatever the layout floated in there **after** the closing
run.

**This rule used to say "image or table", and that is exactly why it kept being
missed.** SH8601 had five bylines split off — by `<pre>`, by `<figure>`, by
`<table>`, and by combinations — and only the figure/table ones were even
describable as defects under the old wording. A listing between a paragraph and
its byline separates the author from their text just as completely as a picture
does. Corpus-wide the broadened rule finds 129.

Seen in 8609 on `124 Wie funktioniert ein Computer?`, where Bild 3 landed
between the final paragraph and the byline.

Check: walking the article in document order, no `<figure>`/`<table>` may sit
between the last body `<p>` and the trailing `<address>`/`<p class="source">`.

## Interview speaker labels are bold

In an interview the magazine sets the speaker label in **bold italic, including
the colon**, and the turn runs on in roman:

```html
<p><strong>64'er:</strong> Commodore ist der erfolgreichste Anbieter …</p>
<p><strong>Winfried Hoffmann:</strong> Das hat sicherlich viele Gründe. …</p>
```

The OCR drops the face, so the labels arrive as plain text and the turns look
like ordinary paragraphs. Mark every label — the interviewer's (`64'er:`) as
well as each interviewee's.

**Do not take the absence of this markup elsewhere as precedent.** The corpus
carries 24 plain `<p>64'er: ` across earlier issues; that is the same defect
propagating, not a house style. A review agent on 8609 left the labels
unmarked for exactly that reason and was wrong. When an existing issue and the
printed page disagree, the page wins.

Related: the abbreviated forename in a speaker label (`M. Grewe:`) is the
construct that Discount's alpha-list extension eats — see r060.
