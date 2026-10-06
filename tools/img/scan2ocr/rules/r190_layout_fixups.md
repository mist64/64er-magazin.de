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
2. **Walk every page against its crop and repair what the import lost.** This
   is the bulk of the step and it is NOT marker-driven: both 190 sub-agents on
   8612 found **zero** TODO markers, and everything below came out of the
   orchestrator's brief instead of this rule.

   | What to find | How |
   |---|---|
   | **lost drop caps** — one letter dropped from the start of a paragraph | the first word reads wrong ("er Computer"); read the letter off the crop. 31+ on 8612 |
   | **paragraphs split mid-sentence** | a `</p><p>` where the sentence continues; rejoin |
   | **headings that swallowed body text** | an `<h2>`/`<h3>` running on into prose; split at the printed heading's end |
   | **lost headings** | a printed heading that arrived as an ordinary paragraph |
   | **`p.source` debris** | leftover source markup inside the paragraph |
   | **a dropped paragraph** | compare paragraph counts against the crop, column by column |

   The **Impressum** is rebuilt here too — it had no owning rule at all before
   this, and 8612's was rebuilt from the crop under this step.

3. Walk every `<p>TODO …</p>` marker in `issues/<YYMM>/*.html` (there may be
   none; that is normal, not a reason to stop):

   | Marker | Action |
   |---|---|
   | `TODO PRE` | Look at the following `<p>…<br>…</p>` block. If the print shows monospace code, fold into `<pre>…</pre>`. If the print shows a real numbered/bulleted list, convert to `<ol>`/`<ul>` instead (and delete the marker). |
   | `TODO INDENTATION` / `TODO INDENTED` | Look at the print indentation. If code → `<pre>`. If prose with visual indent for nested enumeration → `&nbsp;`-prefixed `<br>` inside `<p>`. If real nested list → nested `<ul>`/`<ol>`. |
   | `TODO ASIDE` | Wrap the following heading + paragraphs + closing `<address>` in `<aside>`. Delete the marker. Author bios included — they are asides like any other. |
   | `TODO BOX` | Same as TODO ASIDE if the print shows a boxed callout. If the print shows indented monospace code with no box border, use `<pre>` instead. |
   | `TODO FORMULA` / `TODO FORMULAS` | **SKIP** — editorial (math markup decision). Report unfilled. |
   | `TODO ALL BOXES LIKE BELOW` | **SKIP** content reconstruction — fresh OCR of multiple boxes is out of scope. |
   | `TODO two boxes with text` (or similar content stubs) | **SKIP** content reconstruction. |

4. Light general formatting sweep:
   - Delete `<p>` paragraphs containing only `&nbsp;` or only
     whitespace.
   - Drop a trailing `<br>` immediately before `</p>`.
   - Convert prose-looking enumeration to `<ul>` / `<ol>` **only**
     when the print shows a real bullet glyph or number prefix on
     each item; if the print is just numbered prose ("1. ein,
     2. zwei, 3. drei" running text), leave it as `<p>`/`<br>`.
5. Beautify touched files (`npx --yes js-beautify --type html
   --indent-size 4 --wrap-line-length 0 --replace`). **Verify
   `<pre>` blocks survived** (js-beautify preserves them by default
   but sanity-check after each run).
6. **Do not commit.** Return per-marker action table + general-sweep
   summary + list of explicitly-skipped FORMULA / content markers.

Critical guardrails:
- Anti-memory: code inside `<pre>` must come from the existing HTML
  (the OCR import has the bytes); never retype from print.
- "Only convert to lists when print shows a marker glyph" — applies
  here exactly as it does in the markdown→HTML conversion rules.
  Enumeration-looking prose without a real bullet stays `<p>`/`<br>`.
- **A legend whose print aligns COLUMNS is a `table class="plain"`, not a `<br>`
  chain.** Syntax/Parameter blocks, and `a) b) c)` option lists with `1 =` /
  `2 =` values, set label, value and description in hanging columns; a `<br>`
  chain loses that alignment and the reader loses which value goes with which
  label. (Owner review, SH8602/89.)
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
    # <p[^>]*> ALSO MATCHES <pre>: [^>]* eats the "re". That version reported
    # every correct <pre> listing as a defect. Match the tag exactly.
    for m in re.finditer(r'<p(?:\s[^>]*)?>(.*?)(?=</p>|<p(?:\s[^>]*)?>)', s, re.S):
        t = m.group(1)
        if len(BAS.findall(t)) >= 2 or len(ASM.findall(t)) >= 2:
            kind = 'in <p><code>' if '<code>' in t else 'in BARE <p>'   # both are defects
            print(f"  listing {kind}: {os.path.basename(f)}: {re.sub(r'\s+', ' ', t)[:64]}")
PYEOF
```

Two BASIC line numbers each followed by a keyword is the threshold: one is
ordinary prose quoting a line, two is a listing. Expect a handful per issue —
around 7 to 14 on recent ones — so a flood means the pattern broke.

**The code form in this corpus is `<pre>`, in every case.** A snippet quoted
inside the prose flow is `<pre><code>` — 289 published, 34 in 8609, 52 in 8610,
44 in 8611 — and TRUE `<p><code>` does not occur in any recent issue at all (0
in 8607, 8609, 8610 and 8611). So every hit this sweep reports is a defect, in
one of two forms:

| step 020 label | markup | what it is in print |
|---|---|---|
| `listing-standalone` / `listing-inline` | `<pre>` (with `<code>` inside) | either kind of printed code |
| `body` on code | **the defect** — a bare `<p>`, or a `<p><code>` | code the classifier took for prose |

Expect **zero** on a correctly built recent issue; SH8504 has seven. The real
ones come from step 020 giving a short code block the `body` role — on 8611,
assembler in 151 and Prolog in 181. When you move one into `<pre>`, check the
line breaks survived, and restore them from the crop if not.

### The sweep above misses a listing that was BROKEN UP

It looks for code-shaped text inside one `<p>`, keyed on lines that start with a
number and a BASIC keyword. Two common manglings defeat it:

- the lines are **space-joined into one paragraph**, so nothing starts a line:
  `10 SUMME1 = 50 + 25 20 SUMME2 = 60 + 40 30 PRINT SUMME1`
- the statement is an **assignment**, so there is no keyword after the number
- the listing is **split one line per `<p>`**, so no single paragraph holds two

8611 had seven of these and the sweep reported none. What survives every
mangling is that a listing's LINE NUMBERS ASCEND:

```bash
$PY - issues/<YYMM> <<'PYEOF'
import glob, os, re, sys
P = re.compile(r'<p(?:\s[^>]*)?>(.*?)</p>', re.S)
# Uppercase after the number is what separates code from prose: German text is
# full of "Bit 4 und 5" and "Register 25", and BASIC in this corpus is CAPS.
# Without the [A-Z]{2} this floods -- 39 hits on a clean issue, 2 with it.
NUM = re.compile(r'(?:^|[\s>])(\d{1,5})\s+(?=[A-Z]{2})')
def run_len(ns):
    best = cur = 1 if ns else 0
    for a, b in zip(ns, ns[1:]):
        cur = cur + 1 if b > a else 1
        best = max(best, cur)
    return best
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.html'))):
    texts = [re.sub(r'<[^>]+>', ' ', m.group(1))
             for m in P.finditer(open(f, encoding='utf-8').read())]
    for t in texts:                                   # joined into one <p>
        if run_len([int(x) for x in NUM.findall(t)]) >= 3:
            print(f"  joined listing: {os.path.basename(f)[:38]}: {t.strip()[:50]}")
    run = []                                          # split one line per <p>
    for t in texts + ['']:
        m = NUM.match(' ' + t.strip())
        if m:
            run.append((int(m.group(1)), t.strip()))
            continue
        if run_len([n for n, _ in run]) >= 3:
            print(f"  split listing:  {os.path.basename(f)[:38]}: {run[0][1][:50]}")
        run = []
PYEOF
```

Three ascending numbers, not two, because prose quotes one line often and two
rarely. MEASURED: 8609 and 8610 score **0**, 8607 4, SH8601 5, and 8611 scored
4 before its listings were fixed and 2 after — the residue is prose, so read
each hit rather than trusting the count. Both real ones on 8611 were in the 4.

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
leave them unmarked — **but read the next paragraph before you do, because it
is the half that was missed twice.** Draw precedent from the monthlies only — the Sonderhefte
are a separate series and bold the Impressum labels: MEASURED, **9 of 12
Sonderhefte use `<strong>`**, 2 use `<em>` (SH8602 and SH8603, the two most
recent, which is why the latest precedent misleads) and 1 marks neither. Use
`<strong>`. Fidelity to the artefact is
the job of the page image and the PDF, which keep every one of those bolds; the
HTML owes the reader that two issues of the same magazine look alike.

This does **not** license dropping emphasis that carries meaning. A bold
lead-in that separates one Q&A item from the next is structure, and structure
is content. The test is whether the emphasis distinguishes *this* text from the
text beside it, or merely decorates a field name the layout already sets apart.

**The precedent applies only where the structure survives WITHOUT the bold.**
SH8603's `11 Fragen und Antworten zum C 16 und VC 20` prints three levels —
centred bold headings with a rule, **bold flush-left questions**, roman
indented answers — and shipped through every step with the questions as plain
`<p>`: **0 `<strong>` in the whole file**, question and answer
indistinguishable to a reader. The owner found it by reading. No gate looked,
because the paragraph above reads like permission and this one like a caveat.

So, as a procedure rather than a principle: where the bold is the ONLY thing
separating one item from the next, mark it as printed. Where other markup
already carries the structure — a heading, a `<dl>`, a table cell, an
`<aside>` — leave it unmarked and follow the monthlies.

**And check it.** An article whose print bolds paragraph starts and whose HTML
has no `<strong>` and no headings between those paragraphs is the shape:

```bash
# Q&A-shaped articles whose questions are UNMARKED.  A hit is a LOOK, not a
# failure: read the crop and decide.  r190's find_bold is the locator (see the
# ink-fraction section) and the 600 dpi crop settles it.
#
# THE SHAPE IS THE ALTERNATION, not the question mark.  Three narrower
# versions of this check all failed, and each failure named an exclusion:
#   * "0 <strong> and 0 headings in the file" -- SH8603's article 11 had 16
#     headings from its first commit.  The three printed levels were centred
#     headings, bold questions, roman answers; only the QUESTIONS were
#     unmarked, so a file-level test could never see it.
#   * no attribution test -- the monthlies separate question from answer with a
#     short "(Reader Name)" line (8611/29 and 8612/26, Profis helfen
#     Einsteigern).  That line IS the structure, so those are correct.
#   * no length test -- a rhetorical question ending an ordinary paragraph
#     matched (SH8602/20 "Wo sind die Computer-Detektive? Haben Sie's
#     gemerkt?").  A real Q&A question is SHORT and its answer is LONG.
#
# Two exclusions stay by rule rather than by shape: LESERFORUM, which is this
# section's own precedent (0 of 31 marked), and an INTERVIEW, whose questions
# the print sets roman -- see "Three conflicts settled on 8612".  MEASURED
# over the whole archive with those in place: 3 articles, of which 8604/8 is
# the interview.  SH8603's article 11 as first committed scores 10.
$PY - issues/<ID> <<'PYEOF'
import glob, io, os, re, sys
sys.path.insert(0, 'tools/img/scan2ocr/rules')
import r000_reviewed as R
TXT = lambda t: re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip()
items = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.html'))):
    if 'Leserforum' in f:
        continue
    s = io.open(f, encoding='utf-8').read()
    i = s.find('<article'); b = s[i:s.rfind('</article>')] if i >= 0 else s
    raw = re.findall(r'<p(?: class="[^"]*")?>(.*?)</p>', b, re.S)
    txt = [TXT(r) for r in raw]
    bare = 0
    for n, (r, t) in enumerate(zip(raw, txt)):
        if not t.endswith('?') or not (20 <= len(t) <= 250):
            continue
        if '<strong>' in r or '<em>' in r:
            continue
        nxt = txt[n + 1] if n + 1 < len(txt) else ''
        if re.fullmatch(r'\(.{2,40}\)', nxt):   # attribution separates them
            continue
        if len(nxt) < 400:                       # a question, then a long answer
            continue
        bare += 1
    if bare >= 3:
        items.append('%s: %d unmarked question paragraph(s)'
                     % (os.path.basename(f), bare))
new = R.delta(sys.argv[1], 'r190-qa-unmarked', items)
R.report('unmarked Q&A questions', new, len(items), sys.argv[1], 'r190-qa-unmarked')
PYEOF
```

## Three conflicts settled on 8612

- **Interview labels are ROMAN, not bold italic.** This rule called them "bold
  italic"; 8612's print sets them roman. The page won.
- **Dash lists stay `<p>— …</p>`, with an EM dash, whatever 070 produced.**
  070 turns a printed spaced hyphen into an EN dash, so a dash list arrives
  here as `–` and three of SH8604's four 190 sub-agents kept it; a 280 agent
  then "harmonised" the one that had written `—` to match them, which is the
  wrong direction. MEASURED over the corpus: **em 165, en 1.** Set the em dash
  and do not let the en dash 070 produced decide it.
  A **connective line inside a dash list** — a bare "und" between two items,
  SH8604's article 58 — is not an item: keep it as a `<br>` line within the
  preceding `<p>`, so the list does not gain a member the print does not have.
- The rule says to build a `<ul>` when the
  print shows a real dash glyph, but 8609-8611 all keep the paragraph form.
  Precedent wins, as the section above says.
- **The never-split rule yields to the PRINT when the box is physically above.**
  r190 moved 48's liability box below the Info source because never-split said
  so, while p50 prints it **above**. Where the printed order is unambiguous, it
  decides. (And the aside test keys on tint or a rule, so it misses a box set
  off by TYPEFACE alone — the Werner Paul bio on 8612.)

**An aside's heading is one level below the article's highest section heading.**
See r290: `h2` when the body has `h2` sections of its own, `h3` when the aside
would otherwise be the only `h2` or would outrank the body.

Write the skipped-file list under `<tmp>`, never `/tmp` (r000).

## Verification

```bash
dir=issues/<YYMM>
PY=${PYTHON:-.venv/bin/python}

# 1. no in-scope TODO marker survives
# `sort` exits 0 on empty input, so piping into it and testing THAT printed
# the FAIL line unconditionally -- including on a clean issue.  Test the grep.
grep -hoE 'TODO (PRE|INDENTATION|INDENTED|ASIDE|BOX)' "$dir"/*.html \
  | sort -u | grep . && echo "  FAIL: in-scope TODO survived"

# 2. expected-skip TODO markers may still exist
grep -lE 'TODO FORMULA|TODO ALL BOXES|TODO two boxes' "$dir"/*.html \
  > "$TMPDIR_ISSUE/skipped_files.txt"
echo "  expected skipped markers in $(wc -l < "$TMPDIR_ISSUE/skipped_files.txt" | tr -d ' ') file(s):"
cat "$TMPDIR_ISSUE/skipped_files.txt"
# TMPDIR_ISSUE is this issue's <tmp>. r000 forbids /tmp, which this was.

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

# 3b. nothing in the never-split list was split, and no empty <p> survives.
#     The never-split rule names <pre> and <aside>, but the check covered only
#     figure and table -- and there was no empty-<p> check at all.
$PY - "$dir" <<'NEVERSPLIT'
import os, re, sys
d = sys.argv[1] if len(sys.argv) > 1 else "."
for f in sorted(os.listdir(d)):
    if not f.endswith(".html"):
        continue
    s = open(os.path.join(d, f), encoding="utf-8").read()
    for tag in ("pre", "aside", "figure", "table"):
        if len(re.findall(r"<%s\b" % tag, s)) != len(re.findall(r"</%s>" % tag, s)):
            print("  %s: <%s> unbalanced -- a never-split block was split" % (f, tag))
    n = len(re.findall(r"<p>\s*(?:&nbsp;|\s)*</p>", s))
    if n:
        print("  %s: %d empty <p>" % (f, n))
NEVERSPLIT

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

**And the move is a DEPARTURE FROM PRINT POSITION, so record it.** On SH8603
this moved tables and figures that the page floats MID-article to after the
byline in **9 files** — the rule is right that a byline must not be split, but
the result is an element no longer where the reader saw it, and nothing marked
that. It is also in tension with *restore in print position* for boxes, and
with the 8612 ruling two sections up that the printed order decides where a
box goes when it is unambiguous.

So: the closing run wins, because a split byline misattributes text, which is
worse than a moved float. But **list every element this rule moves in LOG.md
with its printed position**, and where the element is a numbered Bild or
Tabelle, its caption already tells the reader which one it is. Where the float
is mid-article in print and its caption does NOT number it, prefer moving it
to just BEFORE the closing run rather than after the byline, so it stays
inside the article's body.

## BEFORE RESTORING A "MISSING" PASSAGE, CHECK IT IS NOT ALREADY THERE

SH8603's 190A reported *Missing section "Kleiner Epson ganz groß" restored*
in article 43 and restored it under its `<h2>`. **The text was not missing.**
030 had glued it onto the end of the article's opening paragraph in raw OCR
form, so the issue shipped the section TWICE — and 280A noticed only because
a stray `©` survived in the raw copy. The same pass left two paragraphs in
article 6 ending with a copy of the heading it had split out.

The check that was run compared the restored words against the OCR, which can
only confirm the text EXISTS — that is the opposite of the question being
asked. **The question is whether it is already in the FILE.**

So, two steps, both mandatory:

1. **Before restoring anything**, grep the article for the passage's first
   eight words and its last eight words. A hit means it is already there,
   possibly glued into a neighbouring paragraph by 030, and the job is to
   SPLIT it out rather than to add it.
2. **After any restoration or heading split**, run the repeated-window sweep
   below. It found exactly these two cases.

```bash
# A DUPLICATED PASSAGE, which is what a wrong "restoration" leaves behind.
# PROSE ONLY: a <table> repeats cell patterns by nature ("a) 1, 2, 3 b) 1, 2
# min. 10; max. 25,4" across printer columns), a <pre> repeats listing lines,
# and a pin-name legend repeats its own vocabulary -- swept with those in, all
# four of SH8603's first hits and all of 8612's were tables, i.e. correct
# output reported as a defect.  MEASURED with them out: 1 to 4 hits per issue.
# A hit is a LOOK: read both occurrences and decide which (if either) belongs.
$PY - issues/<ID> <<'PYEOF'
import glob, io, os, re, sys
sys.path.insert(0, 'tools/img/scan2ocr/rules')
import r000_reviewed as R
W = 12
STRIP = re.compile(r'<(pre|code|table)\b.*?</\1>', re.S)
items = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.html'))):
    s = io.open(f, encoding='utf-8').read()
    i = s.find('<article'); b = s[i:s.rfind('</article>')] if i >= 0 else s
    b = STRIP.sub(' ', b)
    words = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', b)).split()
    seen, last = {}, -99
    for n in range(len(words) - W + 1):
        k = ' '.join(words[n:n + W]).lower()
        if k in seen and n - seen[k] >= W:
            if n - last > W:
                items.append('%s: w%d and w%d  "%s"'
                             % (os.path.basename(f), seen[k], n, k[:62]))
            last = n
        seen.setdefault(k, n)
new = R.delta(sys.argv[1], 'dup-passages', items)
R.report('duplicated prose passages', new, len(items), sys.argv[1], 'dup-passages')
PYEOF
```

## Nobody owns a lost drop cap before 190

030 and 080 leave them; r310 gates them only at the very end, by which time
the fix is a re-read of every affected crop. SH8603's 190 read **~38** of them
off the crops as part of its own pass, which is the right place but was never
anybody's instruction.

So it is 190's: as part of the bold/italic pass, scan for a paragraph whose
first word is not a word (`er Computer`, `as Programm`, `enn Sie`) and read
the dropped letter off the 600 dpi crop. 8612 had 31+, SH8603 ~38 — this is
not a rare defect, it is one per two or three articles.

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
