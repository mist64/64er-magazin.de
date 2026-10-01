# 170 — Transcribe `<pre>TODO</pre>` listings from the printed scan

**Applies to:** all — listings printed but not shipped on disk occur in both kinds.

**Goal:** turn every `<pre>TODO</pre>` placeholder (and the lone
`<p>TODO LISTING</p>` if any) into a verbatim transcription of the
printed listing from the magazine scan. These are listings that the
print published but the source D64 did not ship — they're "additional
listings not on disk" (Pascal, Z80 asm, MSE hex blocks, raw 6502
disassembly of in-ROM code, short BASIC snippets).

This rule fires after rule 130 (place_figures) has done its work — that
step's "emit `<pre>TODO</pre>` for unfound listings" behaviour
generates the placeholders.

## What `<pre>TODO</pre>` means

Some listings are printed in the magazine but do NOT ship as a file
on the disk — either because they're a one-shot pre-step that
produces something else, the disk omitted them for space, the print
is an assembler disassembly of an in-ROM routine, or the language is
non-C64 (Pascal, Z80 asm). Even so, rule 130 emits a `<figure>` block
with the verbatim caption and `<pre>TODO</pre>` as the body so the
gap is visible in the rendered HTML. Rule 170's job is to OCR the
printed listing into the `<pre>` body.

## A COMPLETE MSE OR CHECKSUMMER LISTING IS RECREATED AS A DISK FILE

**The disk not carrying it was a mistake, not a fact to preserve.** The
magazine printed these two formats precisely so a reader could reconstruct the
program byte for byte: a Checksummer listing carries a per-line sum, an MSE
listing a per-line checksum over its hex. A transcription that satisfies those
numbers IS the program. So it does not stay as page text — it goes into
`issues/<ID>/prg/` like any disk file, and the article references it:

| printed as | recreate | markup |
|---|---|---|
| Checksummer BASIC | `petcat -w<ver> -l <addr>` the transcription, keep the petcat text as `prg/<name>.txt` (house opener `;<name>.prg ==0801==`, plus `;version=` where the dialect is not V2) | `<pre data-filename="<name>" data-name="<Name>" data-checksummer="<1\|2\|3>"></pre>` — EMPTY; the generator tokenises the file and recomputes the sums for display |
| MSE hex | decode the hex to the binary with `tools/mse.py`, write `prg/<name>.prg` | `<pre data-filename="<name>.prg" data-name="<Name>" data-mse=mse1></pre>` |

`data-checksummer` is the Checksummer VERSION the article printed — 1, 2 or 3;
the corpus carries 81, 114 and 32 of each, so all three are live. Getting it
wrong changes every displayed sum.

**Prove it before you write it**, and say so in the report: the recomputed sums
equal every printed one, and where the listing's DATA is a known binary, the
bytes equal it. 8610's MSE-Lader satisfied all 107 printed `<nnn>`, all 86 of
its own loader sums, and its DATA bytes equal `prg/mse.prg[$0801..$0EAB]`.

**What stays inline** is what cannot be a disk file:

- a PARTIAL listing — an erratum's corrected lines (8610's `80` Listing 2 is
  lines 1390-1450 of a program printed in `Sonderheft 3/86`), a fragment quoted
  inside prose;
- a listing in no reconstructable format — a screen dump, Pascal source, an
  assembler disassembly of in-ROM code, anything with no checksums to prove.

## Cropping listing regions from the page scan

Don't guess crop coordinates by trial-and-error. Step 010 already wrote the
block index; grep it for the `Listing` caption line:

```bash
OUT_DIR=$(python3 -c 'import sys; sys.path.insert(0, "tools/img/scan2ocr/rules")
import r010_ocr_blocks as OB; print(OB.OUT_DIR)')
grep -i "listing" "$OUT_DIR/blocks/p<NNN>.txt"
# → block=22 label=body bbox=825x84+195+1955 frac=... text= Listing 1. Komprimierte ...
```

The bbox tells you the caption's column (`X`, width `W`) and
top-edge (`Y`). The listing code sits **above** the caption in the
same column. Walk preceding blocks whose x-range overlaps the
caption's x-range — the topmost is your crop's top edge. Add ~50 px
padding.

One-shot crop — **from the master, not from a PDF render**:
```bash
# The repo venv, not bare python3: r010_ocr_blocks imports numpy and scipy,
# which the system python does not have, so `python3` makes SRC silently EMPTY
# and every crop below then fails on "/NNN.png". MEASURED on 8611.
PY=${PYTHON:-.venv/bin/python}
SRC=$("$PY" -c 'import sys; sys.path.insert(0, "tools/img/scan2ocr/rules")
import r010_ocr_blocks as OB; print(OB.SRC_DIR)')
magick "$SRC/<NNN>.png" -crop <W>x<H>+<X>+<Y> +repage /tmp/64er_<YYMM>_listing.png
```

The bbox is in the master's pixels. The master is deskewed and cut to the sheet's own traced edges (exact A4 is
the delivered PDF, not the master) and
the delivered PDF page is neither, so the two spaces differ by a rotation and an
offset — cropping these coordinates out of a `pdftoppm` render lands in the
wrong place. See r000, "page block index".

## A LOCAL OCR MODEL READS HEX DUMPS BYTE-PERFECTLY — measured

MEASURED 2026-10-01 on 8611 p59, a page of MSE hex (45 lines of
`addr : b0..b7 cs`, the last 360 bytes of `3D-CODE`). The truth is not a
judgement here: `issues/8611/prg/3d.code.prg` is the hand-transcribed,
checksum-satisfying binary, load `$4000`, so every printed line must equal the
eight bytes at that address.

| reading | lines | addresses not in the prg | byte-perfect lines | wrong bytes |
|---|---|---|---|---|
| tesseract (`ocr/out/059.txt`) | 41 | 5 | 25/36 | **28/288 = 9.72%** |
| `mlx-community/GLM-OCR-8bit`, column crops | 45 | 0 | **45/45** | **0/360 = 0.00%** |

GLM-OCR's 45 addresses are contiguous `$4a60`–`$4bc0` with no gaps and the last
line ends exactly at the binary's final byte `$4bc7`. Where tesseract read
`42360`, `cA4`, `Aad8`, `4650` and `£fO £8`, it read `4a60`, `c4`, `4ad8`,
`4b50` and `f0 f8`.

**Two conditions, both necessary.** Fed a whole dense page it degenerates into a
token loop (a run of `20 20 20…`) and it reads *across* a three-column dump,
emitting one output line per printed row rather than per listing line. Both go
away on a **single-column crop with a modest `max_tokens`**, which is what the
0.00% was measured on — and cropping the region is what this rule already does.

**What this does and does not say.** It is a comparison against *tesseract*, the
chain's general OCR. It is **not** a comparison against the vision sub-agent this
rule dispatches today, which has not been scored this way. What it establishes is
that a 1.6 GB local model is a credible transcriber for this step: free, offline,
repeatable, and — because an MSE line carries its own checksum and a complete
listing must equal the `.prg` byte for byte — **self-verifying**, so a wrong byte
is caught by the rule's existing gates rather than trusted.

Run it standalone, not through the oMLX server:

```python
import mlx_vlm                                     # in ~/.omlx-07
model, processor = mlx_vlm.load("/Users/mist/omlx-models-doc/GLM-OCR-8bit")
```

**Use the API, not `python -m mlx_vlm.generate`.** MEASURED on one 2825x3995
page: through the API it bills 14,415 prompt tokens and returns correct output;
through the CLI, with no `--resize-shape` passed, the same file yields boxes in a
~1000 px space and then a token loop. That is the observation. The *cause* is not
established — the CLI's `--resize-shape` defaults to `None` and it only resizes
when set, so the likelier culprit is how it builds the prompt rather than a
downscale. Either way the API path is the one that works; do not infer from this
that the model or the quant is at fault, which is what the loop first looked like.

## Briefing for the sub-agent

The sub-agent must:

1. Crop from the graded **600 dpi master** (`SRC_DIR`), not from a PDF render:
   the bboxes in the block index are in the master's pixel space, and 600 dpi
   is more resolution than a `-r 300` render anyway — small monospace listing
   text needs every pixel.
2. For every `<pre>TODO</pre>` placeholder in `issues/<YYMM>/*.html`:
   - Read the adjacent `<figcaption>` to identify which listing + page.
   - tesseract-locate the caption's bbox in the rendered page.
   - `magick` crop the listing region above (or beside) the caption
     with ~50px padding.
   - Dispatch a **sub-sub-agent** to OCR the crop and return the text.
     The sub-sub-agent gets: crop path, language (BASIC / Pascal /
     6502 asm / MSE hex), the anti-memory rule, the verbatim-typo
     rule.
   - Splice the OCR text into the `<pre>` via the shell `head + cat +
     tail` pattern (NOT the Edit tool — multi-line code retyped via
     Edit is a memory write, forbidden).
3. Also resolve any `<p>TODO LISTING</p>` (the rule 060 markdown→html
   conversion sometimes emits this as a paragraph placeholder for
   inline declarations) — replace with an unwrapped `<pre>` block if
   the printed text is short and uncaptioned, or with a
   `<figure>`-wrapped one if it has a Listing N caption.
4. Beautify touched files (`npx --yes js-beautify --type html
   --indent-size 4 --wrap-line-length 0 --replace`). **Verify
   beautify did not collapse `<pre>` content** — it shouldn't, but
   double-check.
5. **Do not commit.** Return a per-listing table: file, listing
   number, language, line count, source page, any `[ILLEGIBLE]`
   lines, any unfilled placeholders.

Critical preservation rules (per anti-memory + verbatim-typo
principle):
- Preserve exact whitespace, indentation, column alignment, line
  numbers as printed.
- Preserve old German spelling (`daß`, `muß`, `ß`).
- Preserve printed typos verbatim (`einstellungsjahr` vs
  `einstelljahr` inconsistencies, missing commas in floats, mixed
  case opcode bytes, `>91 AND <64` impossible logical conditions).
- Preserve BASIC checksummer brackets (`<238>`, `<004>`) on Checksummer
  listings — **and then USE them: a checksummed listing can be PROVEN, and
  proving it is mandatory.** The magazine printed those numbers so a reader
  could find a typo; they do the same for a transcription, and they are the
  only check in this rule that does not depend on someone's eyes.

  ```bash
  # BASIC: tokenise the transcription, recompute, compare to the print.
  # -w2 for V2, -w3 for BASIC 3.5 (C16/Plus4), -w70 for the C128 -- the
  # WRONG dialect gives wrong sums, so a mismatch may be the dialect, not
  # the transcription (see r120's round-trip check).
  petcat -w2 -l 0801 -o /<scratch>/l.prg -- /<scratch>/l.pet
  .venv/bin/python -c "from tools import checksummer; ..."   # v3 per line
  # MSE hex: every line carries its own checksum byte
  .venv/bin/python -c "from tools import mse; ..."
  ```

  MEASURED on 8610, where all three printed listings proved out:

  | listing | proof |
  |---|---|
  | `76` Listing 2, the MSE-Lader (107 lines) | all 107 printed `<nnn>` reproduced, all 86 of the loader's own line sums, and its DATA bytes equal `prg/mse.prg[$0801..$0EAB]` |
  | `80` Listing 1, the Viza.Key erratum (MSE1 hex) | all five line checksums recomputed, and the assembled bytes are identical to 8609's disk `viza.key.prg` |
  | `80` Listing 2, the Matrix-Editor erratum | all seven printed values reproduced under `-w3` (BASIC 3.5) |

  **The checksum does not only verify — it DECIDES.** A C64 graphic character
  is a glyph a human cannot reliably name from a scan: on 8610's Matrix-Editor
  the sums settled `CBM-@` in line 1410, `CBM-T` in 1420, ten `SHIFT-*` runs
  and a `SHIFT--`, none of which the eye could have called. Where a listing
  carries checksums, transcribe, compute, and let the arithmetic pick the
  character — then say in the report which lines the checker confirmed.

  A listing with NO printed checksums (a screen dump, a Pascal fragment) has no
  such proof: say so, and fall back to a second independent read.

  ### WHICH DIRECTION: read the print, or generate from the disk?

  **The checksums decide that too.** Both directions end in the same
  comparison — a computed sum against the printed sum — but they test
  different claims, and only one of them is the claim you need:

  | | tests | |
  |---|---|---|
  | read the print, then compute | *did I read the printed bytes correctly?* | no proof the disk matches |
  | generate from the disk, then check every printed sum | ***are the disk's bytes the printed bytes?*** | the stronger claim |

  So where the page carries checksums, **generating the lines from `prg/` and
  then verifying every printed checksum against them is sound, and better than
  reading hex by eye** — a human cannot match an arithmetic gate over a
  hundred lines of hex. 8611's 89 was done this way: 132 MSE lines, every
  printed checksum recomputed from the disk bytes, every one equal.

  Two conditions, and they are what make it not circular:

  1. **The printed checksums must be read from the PAGE, independently.**
     Generate the bytes if you like; never generate the sums you are checking
     them against. That is the whole proof.
  2. **A visual pass over the crops is then a sanity check, not the
     evidence** — and say so in the report. A reader primed by a generated
     line sees what it says, which is exactly why the arithmetic has to be
     the thing that decides. 8611 raised this against its own method, which
     is the right instinct; the answer is that the checksum does not care
     what you looked at.

  With NO checksums on the page, generate-first is unsafe for precisely the
  reason 8611 feared: there is nothing independent to catch a disk-print
  divergence, and the eye confirms what it was shown. Read first, twice.
- **NEVER fabricate the `<figcaption>`.** The caption belongs to the
  print, not to you. Transcribe it verbatim from step 010's block index
  or a 600 dpi scan crop (the PDF text layer is void, see r000); if you cannot read it, leave a bare `Listing N.` (no
  title) and flag it — do not compose a plausible descriptive title.
  A made-up caption is a defect even when it reads plausibly. Equally,
  do not delete a genuine caption as "invented" without a scan check:
  8608/142 `Listing 1. Laufzeit-Testschleife in »C«` IS printed in
  bold on p145, so it is correct, not a fabrication.
- Preserve assembler comment columns and semicolons.
- Pascal `:=`, `BEGIN`/`END`, `THEN`/`ELSE`, `ARRAY [n..m] OF`
  exactly.

## Verification

```bash
dir=issues/<YYMM>

# 1. no <pre>TODO</pre> left
grep -l '<pre>TODO</pre>' "$dir"/*.html && echo "  FAIL: <pre>TODO</pre> survived"

# 2. no <p>TODO LISTING</p> left
grep -l '<p>TODO LISTING</p>' "$dir"/*.html && echo "  FAIL: TODO LISTING survived"

# 3. every <figcaption>Listing N…</figcaption> has a non-empty <pre>
#    body before it (filled, not the placeholder)
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
bad = 0
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    # for each <figure> with a Listing figcaption, ensure the <pre>
    # body is not empty / not "TODO"
    for m in re.finditer(r'<figure[^>]*>(.*?)</figure>', s, re.DOTALL):
        body = m.group(1)
        if not re.search(r'<figcaption>Listing\s+\d+', body): continue
        pre_m = re.search(r'(<pre[^>]*>)(.*?)</pre>', body, re.DOTALL)
        if pre_m:
            # A <pre data-filename=…> is EMPTY BY DESIGN: generate.py fills it
            # from prg/ at build time. Without this the check fails on every
            # issue that has disk listings at all -- 35 times on 8611 -- which
            # is the r040 all-zero case again: a check that reports the normal
            # state as a fault gets ignored, and then it is not a check.
            if 'data-filename' in pre_m.group(1):
                continue
            inner = pre_m.group(2).strip()
            if inner in ('', 'TODO'):
                print(f"  empty Listing pre in {f}"); bad += 1
sys.exit(1 if bad else 0)
PY
)" "$dir"

# 4. spot-check: every transcribed BASIC listing has line numbers at
#    the start of MOST lines. A block that is CLEARLY BASIC (a majority
#    of lines already start with a line number) but where a sizeable
#    minority don't is the signal that OCR ate some line-number
#    prefixes — flag it. Pure-asm / Pascal blocks (0% digit-starts)
#    are NOT BASIC and are correctly left unflagged.
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(r'<pre[^>]*>(.*?)</pre>', s, re.DOTALL):
        body = m.group(1)
        if not body.strip(): continue
        lines = [l for l in body.splitlines() if l.strip()]
        if len(lines) < 10: continue
        digit_starts = sum(1 for l in lines if re.match(r'\s*\d', l))
        frac = digit_starts / len(lines)
        # 0% → not BASIC (asm/Pascal), fine. >=60% → healthy BASIC.
        # Between: looks like BASIC with some numbers eaten by OCR.
        if 0 < frac < 0.6:
            print(f"  {f}: <pre> looks like BASIC but only "
                  f"{digit_starts}/{len(lines)} lines start with a digit "
                  f"— OCR may have eaten line numbers")
PY
)" "$dir"
```

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). To make that failure mode
impossible here, every `<pre>TODO</pre>` the sub-agent transcribes
must be backed by **runnable verifier evidence pasted verbatim into
the report**:

- For each transcribed listing, paste the crop path used
  (the master page + the bbox from `<OUT_DIR>/blocks/p<NNN>.txt`) so the orchestrator can re-open the same
  image and spot-check 2-3 lines against what landed in the `<pre>`.
- For each listing, paste the first and last 2 lines of the splice
  output (the lines that anchor the OCR to a specific position in the
  print) so the orchestrator can confirm no header or trailer was
  silently dropped.
- For each `[ILLEGIBLE]` marker, paste the line number in the print
  and a one-line reason ("smudge across columns at line 47").
- For each unfilled placeholder, paste the page number and a one-line
  reason it could not be located.

**No verifier output, no claimed transcription.** A listing reported
without the crop path + first/last line evidence is treated as
un-applied; the orchestrator will re-dispatch. "Trust me, I OCR'd it"
is never acceptable — multi-line code retyped from memory is the
canonical anti-memory violation.

## Notes / lessons

- The 8607 sweep transcribed 9 placeholders across 4 articles
  (36 Modem, 79 T&T Profis, 85 C128 Reise, 136 Pascal-Kurs). Pascal
  is the most common "not on disk" language in any issue — the disk
  format is C64-specific, so non-C64 source code never ships.
- Watch out for the `<p>TODO LISTING</p>` pattern (single paragraph
  placeholder) vs. the rule 130 `<figure><pre>TODO</pre>` pattern
  (full figure wrapper). They're emitted by different upstream
  steps and resolve to different shapes.
- `js-beautify` is well-behaved with `<pre>` by default but worth
  checking once after the run.
- 300 dpi is the right target resolution for listing OCR. The
  150 dpi figure-placement scans are too coarse for column-aligned
  asm code.
- The "Listing N body references without a `<figure>`" check this
  step's sub-agent can produce is useful follow-up data — sometimes
  the OCR pipeline dropped a whole listing, not just left a TODO
  placeholder.

## Listing captions: drop the "how to type this in" pointer

The print appends a cross-reference to the MSE/Checksummer instructions, which
live on a page that does not exist as such in the HTML:

```
Listing. Das Programm »fsd64.obj« bitte mit dem »MSE« abtippen. Hinweise siehe Seite 51
Listing 2. Demoprogramm zu »Shrinksprite«. Bitte die Eingabehinweise auf Seite 51 beachten.
Listing »Copy 1520« geben Sie bitte mit dem MSE (siehe Seite 51) ein
```

Keep the instruction ("bitte mit dem MSE eingeben"), drop the page pointer
(`Hinweise siehe Seite 51`, `… auf Seite 51 beachten`, `(siehe Seite 51)`).

Same for standalone continuation pointers in the body — `Listing und
Beschreibung ab Seite 54`, `Fortsetzung auf Seite …` — these are layout
navigation and are omitted entirely.