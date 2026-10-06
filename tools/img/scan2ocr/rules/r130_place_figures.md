# 130 — Place `<figure>` tags for the extracted listings

**Applies to:** all — placing the extracted listings into their articles is kind-independent.

**Goal:** turn the worklist `issues/<YYMM>/prg.txt` into real, placed
listing figures inside each per-article HTML, and finish each one with
the actual program name (`data-name`) and verbatim caption
(`<figcaption>`) from the printed magazine.

This step has **no automation**. It's editorial: every `<figure>`
block in `prg.txt` has to be matched to an article, dropped into the
right spot in that article, and have its two placeholders filled.
The verification at the end is automatable; the placement decisions
are not.

## Inputs

- `issues/<YYMM>/prg.txt` — the worklist produced by the previous
  step. Sections are delimited by HTML comments naming the disk's
  per-article separator file (e.g.
  `<!-- 0    "--------------36" del  -->` ⇒ "everything below this,
  until the next separator, belongs to the article whose start page
  is 36").
- `issues/<YYMM>/prg/` — the actual `.txt` / `.prg` files.
- `<OUT_DIR>/blocks/pNNN.txt` and `NNN.labels.json` — for verbatim captions.
  (This used to name `issues/<YYMM>/64er_*.pdf`, which does not exist during a
  build: the PDF is made at step 006, after PAUSE 2. The concatenation target
  used to be a `/tmp` path, which r000 forbids — write it under `<tmp>`.)
- `issues/<YYMM>/<page> ….html` — the article files to receive
  figures.
- `<tmp>/masters600/NNN.png` — the page image, when the block text is wrong,
  fall back to reading the scan visually. (There is no `issues/<YYMM>/png/`;
  r000's *THE PAGE IMAGE IS masters600* names the one real source.)

**A `<pre>TODO</pre>` is r170's work, not an owner question.** r170 prescribes
both halves: it recreates a printed MSE/Checksummer listing as a new `prg/`
file, and it transcribes printed source. Do not escalate either to the owner.
(On 8612 two such questions were queued before r170 was read, and withdrawn.)

**Every disk-backed listing's range is compared with the print.** Where the
file's first or last line number differs from the printed listing, add
`data-range="<first>-<last>"` (comma-separated runs allowed) so the page shows
what the magazine showed. The download stays the **full** file. `data-range` is
implemented in `generate.py` (:679, :721, honoured by the checksummer path) and
16 issues already use it.

**A padded printed last row needs no `data-range` and no note.** An MSE dump's
final row is short whenever the program's length is not a multiple of eight,
and the print sometimes pads it with the bytes that followed in memory, giving
that row a different checksum. We render from the `.prg` and so emit the real
short row. Owner, 2026-10-05: *"we don't reproduce this."* Not a print/disk
divergence, no aside — see r170, *THE PRINTED LAST ROW MAY BE PADDED*.

**`data-range` is BASIC-only.** It selects by LINE NUMBER, so a binary has no
way to express the same thing — and a binary's range mismatch is just as real:
SH8603 had printed dumps whose address span differs from the disk file's. Until
there is an address form, report the mismatch at PAUSE 2 (it is a print/disk
difference, so r300's standing ruling applies) and record the printed span in
the caption or in LOG.md. Do not silently ship the full dump as if it matched.

MEASURED on 8612: 2 of 38 disk listings start before the print — `79 yankee
doodle` (file from 10, print from 100) and `input-routine` (file from 1, print
from 10000) — and none end after it. The test is **fidelity to the print**,
nothing else.

## Procedure

For each `<figure>` block in `prg.txt`, in order:

1. **Find the article.** The section separator above it gives the
   article's start page; the file is the one whose name begins with
   that page number. Section separators of the form
   `----M/YY-NN` point at issue M/YY's article — those listings are
   reprints belonging to that older issue, not the current one
   (place them or report them per the rules below).
2. **Find the body reference.** Inside the target HTML, look for the
   first text mention like `(Listing 1)`, `Listing 1.`, `(Assembler-
   Listing)`, etc. That's where the figure goes. The figure block
   must be inserted **after** the `</p>` of the paragraph containing
   that first mention, never splitting a paragraph.

   **Which of the two placement rules wins — owner ruling, 2026-10-04.** This
   rule says both "insert after the `</p>` of the paragraph containing that
   first mention" and "at article scope, the byline ends the prose and listings
   follow", and never said which applies when:

   - **A SHORT listing that belongs to the explanation** — a course step, a
     trick — goes **INLINE**, after the paragraph that first names it. It is
     meant to be read as part of the text.
   - **A LONG listing that is a useful program on its own** goes at the **END**,
     after the byline.

   When in doubt, ask what a reader would do with it: type it to USE it (end),
   or read it to UNDERSTAND the text (inline).

   **AND THE CONSEQUENCE, which the ruling did not spell out: PRINT ORDER
   WINS, so from the first listing placed at the END, every LATER-NUMBERED
   listing goes there too.** An article's listings are one sequence, and
   splitting it means the end block starts at a lower number than the inline
   ones that follow it. SH8604's 81 is the case: Listing 1 is the 372-line
   Gerüst, a program in its own right, so it is end-placed — and then 2
   onwards cannot go inline. Dateiverwaltung hit the same wall from the other
   side and produced "Listing 16 after 26", which is check 4 reporting the
   ruling working as intended, not a defect in the article.

   **Follow the PRINT over first mention when the two disagree.** SH8604's
   Listing 14b is first named after 15's anchor but printed directly under 14;
   first-mention placement would have moved it past 15. The page is the
   evidence (r000: CONSISTENCY WITH THE PAGE BEATS CONSISTENCY WITH ITSELF).
3. **Fill `data-name`.** Use the user-visible program name from the
   article body, not the raw on-disk filename
   (e.g. `data-name="Vectors"`, not `data-name="vectors.boot"`).
   Must be unique within the article **per element kind** — a
   listing's `<pre data-name="X">` and its sibling
   `<div class="binary_download" data-name="X">` intentionally share
   the name (they're the display + download of the same program).
4. **Fill `<figcaption>`.** Take the verbatim caption from the
   magazine — typically `Listing N. …` (note the trailing dot after
   `N`). Use step 010's block index first; if it disagrees with the scan on a
   program name, trust the article body's spelling (the body uses
   the name multiple times; the caption is a single OCR target).
   **NEVER fabricate a caption.** Every word of the `<figcaption>`
   must be read off the printed page — step 010's block index or a
   600 dpi scan crop (the PDF text layer is void --
   see r000, "the PDF has no usable text layer"). A plausible-sounding descriptive title you compose
   yourself is still a fabrication and is forbidden. If you cannot
   locate/read the printed caption, do NOT invent one: leave a bare
   `Listing N.` (no title) or the placeholder, and flag it in your
   report for a human. "Reads plausibly" is not "is in the print" —
   but do the reverse check too before deleting a caption as
   "invented": 8608/142 `Listing 1. Laufzeit-Testschleife in »C«`
   IS printed in bold on p145 (blocks p145 confirms it), so it is a
   correct caption, not a fabrication.
5. **Remove the placed block from `prg.txt`.** That keeps `prg.txt`
   as a running "remaining work" list. Drop the section comment too
   when its block is empty.
6. **Walk the listing tail in printed Listing-N order.** When the
   article has more than one listing, after all are placed, reorder
   them so the captions read `Listing 1`, `Listing 2`, … in
   sequence; disk-directory order is usually not the print order.

## Variants — which HTML shape to use

| File classification | HTML shape | Why |
|---|---|---|
| BASIC source (`prg/<name>.txt` present, `.prg` in `prg/del/`) | `<pre data-filename="<name>"></pre>` (no `.prg` suffix) | Generator renders petcat text; binary download materialised via `petcat2prg`. |
| MSE binary (`prg/<name>.prg`) | `<pre data-filename="<name>.prg" data-name="…" data-mse=mse1></pre>` + sibling `<div class="binary_download" data-filename="<name>.prg" data-name="…">` | MSE hex dump + download. |
| Hypra-Ass source | `<pre data-filename="<name>.src" data-assembler="hypra-ass"></pre>` | Auto-decoded by generator. Master file is `prg/<name>.prg` or `prg/<name>.txt`. Add `data-charset="lower"` when the PRINTED listing is mixed case — see r120. |
| Top-Ass source | `<pre data-filename="<name>.prg" data-assembler="top-ass"></pre>` | Auto-decoded. |
| Compiled / binary-only download | `<div class="binary_download" data-filename="<name>.prg" data-name="…">` alone | No printed listing to display. |
| Hidden BASIC companion (no printed listing, but section separator assigns it to this article) | wrap a `<pre data-filename="<name>">` (no `.prg`) inside `<div style="display: none;">` | Materialises a download link without rendering content. |
| Hidden binary companion | `<div class="binary_download" data-filename="<name>.prg" data-name="…">` | Same intent; CSS hides body and shows only the download link. |
| Printed assembler OUTPUT (address + hex + source) with only the SOURCE on disk | transcribe the PRINT (r170 method), prove the hex column against the assembled/disk binary, and offer the source as a download | Never the source file under the printed caption: a different PRESENTATION of the same program fails "fidelity to the print" as surely as a different line range. SH8602/13 Listing 3. **When a printed listing replaces a disk embed, keep the disk file as a `binary_download`** — dropping the `<pre data-filename>` silently removed the download. |
| Printed listing not on the disk (e.g. one-shot pre-step, in-ROM disassembly) | `<figure><pre>TODO</pre><figcaption>Listing N. …</figcaption></figure>` | Records that the print has it; future pass OCRs the printed bytes into the `<pre>`. |

For inline-typed listings (e.g. Z80 asm, Pascal source typed by a
contributor and arriving outside `prg/`), **never re-type a non-trivial
listing from memory**. Splice the source file's bytes into the article
via shell I/O (`cat source.txt`), then read back the result to verify.

## Rules / things to watch

- **An MSE hex dump is a C64 MSE dump, and not every binary is one.** The
  table below defaults a binary to `data-mse=mse1`, which renders MSE's own
  row format and addresses. SH8603's C16 and VC 20 binaries are printed as
  **TEDMON dumps, VC-20 monitor dumps, or the game's own input-program
  format** — `tacco` dumps at file−$200 with its own row layout and a 16-bit
  row sum, `penco` in 25-byte rows — so `mse1` would print addresses the
  magazine never set. Read the printed dump's shape before choosing, and where
  it is not MSE, the `<pre>` carries the dump as printed and the download
  carries the file.
- **Where this rule and r170 both touch a caption, r170 wins on page
  pointers.** This rule says captions are verbatim; r170 says drop a standalone
  "… auf Seite N" pointer. The same printed caption can be both ("Bitte
  beachten Sie die Eingabehinweise auf Seite 76"), and no precedence was
  stated. The pointer goes: it is a print navigation aid that means nothing on
  a web page, and what remains of the caption is still verbatim.
- **Captions are verbatim.** Trailing dot after `Listing N`, German
  typography (`»…«`), exact punctuation. Read from the PDF text layer
  first; fall back to scan-visual only when the layer is broken.
- **`data-name` is unique per article PER ELEMENT KIND.** Two
  `<pre>` figures in one HTML can't share it, and two
  `<div class="binary_download">` siblings can't share it — but a
  listing's `binary_download` sibling **intentionally shares its
  `data-name`** with the `<pre>` it downloads. Verifier #3 exempts
  exactly that `<pre>`/`binary_download` pairing (see the `.sh`
  implementation, which subtracts each div name once from the pre
  count).
- **`data-filename` base name max 16 characters** (the C 64 file
  system's hard limit).
- **`.txt` header line** must be `;<filename>.prg ==ADDR==` with
  `<filename>` matching the file's base name and `ADDR` matching the
  decoded load address.
- **Credit external contributors** — `;Eingetippt von Name` as the
  first line of contributor-typed `.txt`, or `<!-- Eingetippt von Name
  -->` for HTML-inline listings.
- **Placement style.** Three article shapes, three placements:

  1. **One big program** — article describes a single program with
     multiple `<h2>` sub-sections covering its modules / facets
     (e.g. `67 Die ideale Ergänzung` Master-Text-Drucker driver
     suite, `50 Das Rhythm Construction Set (R.C.S.)`,
     `73 Vectors`, `49 Variosystem`): **all listings in a single
     block at the very end, after the byline, before
     `</article>`** (or before a Fehlerteufelchen aside if
     present).

  2. **Sub-articles of small tools** — column of independent small
     programs with their own bylines per sub-section (Tips &
     Tricks Einsteiger / Profis / C 16, Aktuelles, CP/M-Ecke,
     Hypra-Basic, Newsroom): **listing AFTER the tip's byline at
     the very end of that tip section**. Pattern: tip body prose →
     `<address class="author">(byline)</address>` → `<figure>`
     listing + `<div class="binary_download">` companions → next
     section's `<h2>`.

  3. **Tutorial** — article teaches a concept or technique with
     short illustrative snippets (Kurs / Hilfreiche Grundlagen /
     Reise durch …): **small listings inline**, placed mid-prose
     where the tutorial introduces them. The print typeset is the
     ground truth: tutorial code snippets are usually 3-10 lines
     and tightly interleaved with explanatory text. Don't move
     them to the article tail — that breaks the pedagogical flow.
     Examples: 133 Computer-Simulation, 136 Pascal-Kurs,
     139 Basic zu Assembler, 150 Grafik für Profis, 85 Reise
     durch den C 128.

  **How to pick:**
  - One author, one program → shape 1.
  - Multiple `<h2>` sub-sections each with its own author/byline →
    shape 2.
  - "Kurs", "Teil N", "Grundlagen", "Reise durch …", inline body
    code snippets that teach a concept → shape 3.
  - **Test:** are the article's `<h2>` sub-sections describing the
    SAME program's facets? Then end-of-article. Are they unrelated
    sub-programs with their own author / their own caption? Then
    per-section. In 8607 `67 Die ideale Ergänzung` (Master-Text-
    Drucker) has sub-sections `Text via RS232 senden`,
    `Der Zeichensatz-Editor`, `Editor`, `Hauptmenü` — all parts of
    ONE driver suite → all 6 listings belong at end.
  - **Within a tip section, listing goes AFTER the byline at the
    very end of that section**, never between body paragraphs.
    Pattern: tip body prose → `<address class="author">(byline)</address>`
    → `<figure>` listing + `<div class="binary_download">` companions
    → next sub-section's `<h2>`. Don't break the body prose by
    sticking the listing inline near the first `(Listing N)`
    reference, even when the body refers to it inline — keep the
    body block intact and append the listing after the byline.
  - **At article scope, byline ends the prose, listings follow.**
    Same shape: body → byline → listings → (Fehlerteufelchen aside
    if present) → `</article>`.
- **Disk variants of the same program** (e.g. two load-address builds
  of the same BLOCK routine): the printable source goes in the
  `<figure>`; each variant's binary download goes as a sibling
  `<div class="binary_download">` right below.
- **Listings present in `prg/` but not in any article.** Boot screens,
  utility reprints from previous issues, leftover demos: don't shove
  them into Impressum or a random article. Report them at the end of
  the session, and if no decision is given, append an entry to
  `issues/<YYMM>/LOG.md`. Better an unplaced file than a wrong
  placement.
- **References without a file.** If the article body mentions
  `(Listing N)` and there's nothing in `prg/` for it, emit
  `<figure><pre>TODO</pre><figcaption>Listing N. …</figcaption></figure>`
  with the verbatim caption, so the gap is visible in the build.
  Never silently drop a printed Listing N.

## SHAPES THE RULE DID NOT NAME — measured on SH8604

- **A data file of a "nur auf Diskette" program is a HIDDEN
  `binary_download`, named by its C64 filename — never an MSE `<pre>`.**
  Room files, texts, charsets and save games are not listings and have no
  printed dump. SH8604's disk C holds 101 of them and the `prg.txt` template
  wraps every raw file in an MSE `<pre>`, so the pile arrives pre-proposed
  wrongly (see r120, *A DATA FILE TYPED `prg`*). Also say in the body which
  single file the reader LOADs; with 101 names in the directory, nothing else
  does.
- **`data-checksummer` exists and this rule never mentioned it.** SH8602 uses
  it 9 times; 8611 and 8612 never do. Look at how the issue you are on prints
  its checksums before deciding.
- **The evidence requirement assumes the body says "Listing".** 6 of SH8604's
  11 placement articles never use the word, and 4 have no separate byline to
  place an end block after. Where there is no "Listing N" mention, the evidence
  is the printed ADJACENCY — which page, which column, above or below what —
  and that is what goes in the report.
- **`data-name` for a course listing the body never names**: take the
  caption's short form. SH8604's 81 Listing 3 and 58 Listings 9/10 have no
  name in the body at all (58's was in text the OCR lost).
- **One listing, one caption repeated on every page it runs across.**
  SH8604's Odyssey prints "Listing. »Odyssey« (Fortsetzung auf Seite 97)" and
  then "… (Schluß)". Take the FIRST occurrence, drop the continuation
  pointer per r170, and keep a print typo such as the bare "Listing." as
  printed — captions are verbatim.
- **One listing with two unrelated captions on two pages** (SH8604 Listing 16,
  p20 and p21) and **a binary whose MSE file is longer than the printed span**
  (2 bytes, which `data-range` cannot express) are both print/disk differences.
  They go to the owner under the section below, not into a judgement here.
- **Check 5 cannot run mid-chain**: the build dies on the missing `title.png`.
  Copy the issue to a scratch directory with a stand-in `title.png` and run it
  there.

## A print/disk difference is the OWNER's call — see r300

Where a figure, a caption, a line range or a listing on the page disagrees with the disk file this step is placing, **stop and report it with the evidence**; it is a PAUSE 2 decision and not this step's. The full ruling, with the three shapes it covers, is in r300 under *EVERY PRINT/DISK DIFFERENCE IS AN OWNER DECISION, ALWAYS*. Do not take a previous issue's answer as a precedent.

## An element you cannot place does NOT go at the end

Owner, 2026-10-06. A table, figure or listing whose print position cannot be
determined is placed **where it fits best** — for a numbered series, between
its neighbours — never appended to the bottom of the article, which reads as
the conclusion and lands after the byline's closing run. The rule, the
reasoning and the check are in **r150, *NEVER LEAVE AN ORPHAN AT THE END***,
and they cover all three kinds.

## Verification

```bash
dir=issues/<YYMM>

# 1. prg.txt is empty (every listing placed) — or only contains
#    listings explicitly marked "no home in this issue" with a note.
wc -l "$dir/prg.txt"

# 2. Every <figure>'s data-filename resolves to a file in prg/ or prg/del/:
python3 - "$dir" <<'PY'
import os, re, sys
d = sys.argv[1]; pdir = os.path.join(d, 'prg'); ddir = os.path.join(pdir, 'del')
have = set(os.listdir(pdir)) | (set(os.listdir(ddir)) if os.path.isdir(ddir) else set())
missing = set()
for f in os.listdir(d):
    if not f.endswith('.html'): continue
    for m in re.finditer(r'data-filename="([^"]+)"', open(os.path.join(d,f)).read()):
        fn = m.group(1)
        # BASIC variant: data-filename has no .prg suffix; expect <fn>.txt
        cand = fn + '.txt' if not fn.endswith('.prg') else fn
        if cand not in have: missing.add(f"{f}: {fn} -> {cand}")
for x in sorted(missing): print(x)
PY

# 3. Every <figure data-name> within an article is unique PER ELEMENT
#    KIND. A <pre data-name="X"> and its sibling
#    <div class="binary_download" data-name="X"> intentionally share
#    the name — EXEMPT that pairing (this check counts <pre> and
#    <div> names separately and allows each div name to cancel one
#    pre name, matching r130_place_figures.sh's verifier #3):
python3 - "$dir" <<'PY'
import os, re, sys, collections
d = sys.argv[1]
for f in os.listdir(d):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    pres = re.findall(r'<pre [^>]*data-name="([^"]+)"', s)
    divs = re.findall(r'<div class="binary_download" [^>]*data-name="([^"]+)"', s)
    pre_count = collections.Counter(pres)
    for n in divs: pre_count[n] -= 1   # a div may share one pre's name (MSE pair)
    dup = [n for n, c in pre_count.items() if c > 1]
    if dup: print(f"{f}: duplicate <pre data-name> {dup}")
    div_dup = [n for n, c in collections.Counter(divs).items() if c > 1]
    if div_dup: print(f"{f}: duplicate binary_download data-name {div_dup}")
PY

# 4. Listing-N captions in each article are in print order. Grep ONLY
#    figcaptions (like verifier #7) — a bare `Listing [0-9]+` grep also
#    matches body prose ("siehe Listing 3") and false-flags out-of-order.
#
#    THE INLINE AND END BLOCKS ARE TWO SEQUENCES, NOT ONE.  The 2026-10-04
#    ruling puts a long self-contained listing at the end, after the byline,
#    and leaves short explanatory ones inline -- so an article with both has
#    a lower number after a higher one BY CONSTRUCTION.  Comparing across the
#    byline reported "Listing 16 after 26" on SH8604's Dateiverwaltung, which
#    is the ruling working.  Split at the byline and order each side.
$PY - "$dir" <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    # the LAST byline ends the prose; everything after it is the end block
    cut = max([m.end() for m in
               re.finditer(r'</address>', s)] or [0])
    for part, where in ((s[:cut], 'inline'), (s[cut:], 'end block')):
        prev = 0
        for m in re.finditer(r'<figcaption[^>]*>(?:<[^>]+>)*\s*Listing\s+(\d+)',
                             part, re.IGNORECASE):
            n = int(m.group(1))
            if n < prev:
                print(f"{f}: {where}: Listing {n} after {prev} (out of order)")
                break
            prev = n
PY

# 5. Build the issue and confirm no listing-related errors:
.venv/bin/python generate.py --issues <YYMM> --future local 2>&1 | grep -iE 'listing|prg|figure|binary_download' | head

# 6. Every <figcaption>Listing N…</figcaption> must have a description
#    after "Listing N.". Bare `<figcaption>Listing N</figcaption>` is
#    the failure mode (8607/`96 Neues vom Hypra-Basic.html` shipped
#    10 of these). The caption text after the listing label should be
#    at least 3 words.
#
#    BUT CAPTIONS ARE VERBATIM, AND SOME PRINTED ONES ARE SHORT.  "Listing 2.
#    »INT«" is the whole caption on the page, and the >=3-words test called
#    12 of SH8603's captions bare.  A printed caption of one or two words is
#    correct by this rule's own "captions are verbatim"; what the test is
#    actually looking for is a caption that is ONLY the label.  So: fail on
#    nothing after "Listing N.", and report a 1-2 word description as a look.
python3 - "$dir" <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(
            r'<figcaption[^>]*>(?:<[^>]+>)*\s*(Listing\s+\d+[a-z]?\.?)([^<]*)',
            s, re.IGNORECASE):
        rest = m.group(2).strip().lstrip('.').strip()
        # ONLY AN EMPTY DESCRIPTION IS A FAILURE.  A printed caption of one or
        # two words is correct under "captions are verbatim": SH8603 has 18 of
        # them -- "Listing »Hamurabi«", "Listing zu »YAATZEE«", "Listing 2.
        # Maschinencode-Programm »Tacco«" -- and the >=3-word test called every
        # one bare.  What this check is for is a caption that is ONLY the label,
        # which is 8607/96's shape.
        if not rest:
            print(f"  FAIL {f}: nothing after {m.group(1)!r}")
        elif len(rest.split()) < 3:
            print(f"  look {f}: {m.group(1)!r} + {rest[:40]!r}"
                  " -- short; verbatim on the page?")
PY

# 7. Listing-N sequence must be gap-free per article. Per-article
#    collect every Listing-N number from <figcaption>; if the sequence
#    skips any integer between min and max, report. 8607 example:
#    `79 Tips & Tricks für Profis.html` jumped 1→2→4 (Listing 3
#    missing) before second-pass review.
python3 - "$dir" <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    # ALSO FLAG DUPLICATES.  sorted(set(...)) collapses them, so a
    # renumbering that leaves the set gap-free -- {1,2,2,3} -- passed the
    # gap test while the article printed two Listing 2s.  Count first --
    # and count the LABEL, `14` and `14b`, not the integer: SH8604's
    # Dateiverwaltung prints both, and an integer-only count calls them a
    # duplicate.  The gap test below stays on the integers, where 14b is
    # correctly not a number of its own.
    labels = [m.group(1).lower()
              for m in re.finditer(
                  r'<figcaption[^>]*>(?:<[^>]+>)*\s*Listing\s+(\d+[a-z]?)',
                  s, re.IGNORECASE)]
    # A DUPLICATE CAN BE CORRECT: the magazine prints two MACHINE VARIANTS
    # under one number -- 8408/151 has "Listing 1 … (C 64)" and "Listing 1
    # … (VC 20)", likewise Listing 2.  That is the page, so it is not a
    # defect; record it under r000_reviewed.py (key r130-dup-listing) rather
    # than weakening the test.  MEASURED over the corpus: 2 articles report,
    # one of them this legitimate shape.
    dup = sorted({x for x in labels if labels.count(x) > 1})
    if dup:
        print(f"  {f}: DUPLICATE listing numbers {dup}")
    all_n = [int(re.match(r'\d+', x).group()) for x in labels]
    nums = sorted(set(all_n))
    if nums and nums != list(range(min(nums), max(nums)+1)):
        missing = [n for n in range(min(nums), max(nums)+1) if n not in nums]
        print(f"  {f}: listing-number gaps {missing}")
PY
```

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression — print typo treated as OCR error
because no block-index check was actually performed). To make that
failure mode impossible here, every placement the sub-agent applies
must be backed by **runnable verifier evidence pasted verbatim into
the report**:

- For each `<figure>` placed, paste the one body-text line that
  contains the first `Listing N` mention (the placement anchor), e.g.
  ```
  79 Tips & Tricks für Profis.html → "…wie in Listing 1 zu sehen ist…"
  ```
  so the orchestrator can confirm the figure landed after that
  paragraph's `</p>`.
- For each article touched, paste the verifier's post-fix output from
  check #4 (Listing-N sequence) and check #7 (gap detector) showing
  the article's sequence is now contiguous (or that the gap is
  intentionally documented in `LOG.md`).
- For each `prg/` file left unplaced, paste one line stating which
  section separator it sat under and why no article matched.

**No verifier output, no claimed placement.** A figure placement
reported without the body-text anchor line + the post-fix verifier
output is treated as un-applied; the orchestrator will re-dispatch.
"Trust me, I placed it correctly" is never acceptable.

## End-of-session summary

When the placement pass is done, surface a table for spot-checking:

| Article | Listings placed | Binary companions | Notes / `TODO`s |
|---|---|---|---|

…with one row per article that received a figure, and an explicit
list of:
- every `<pre>TODO</pre>` placeholder (with the reason: pre-step
  not on disk, in-ROM disassembly, OCR pending, …),
- every body-text `Listing N` reference for which **no** figure was
  added, and why (e.g. errata referencing an earlier issue),
- every `prg/` file that ended up in no article, and why.

Without this table the user can't pinpoint where to spot-check.

## Notes / lessons

- **Bare `Listing N` captions.** 8607's `96 Neues vom
  Hypra-Basic.html` shipped 10 figcaptions of the form `<figcaption>
  Listing N</figcaption>` with no description at all — the trailing
  caption text was dropped during placement. Verifier #6 catches
  this. Every print `Listing N.` caption in 64'er has a trailing
  description; if you can't find one in the PDF text layer, fall
  back to the scan.
- **Listing-number sequence gaps.** 8607's `79 Tips & Tricks für
  Profis.html` was placed with listings 1, 2, and 4 — Listing 3 was
  silently omitted because no `prg/` file matched it. Verifier #7
  catches this. When a gap is real (the print really does skip a
  number), document it explicitly in the end-of-session summary or
  in `LOG.md`; otherwise treat the gap as a placement bug and find
  the missing listing.
