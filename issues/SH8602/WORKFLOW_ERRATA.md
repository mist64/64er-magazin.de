# SH8602 — workflow errata (r340)

Written as the build goes. Newest at the bottom.

## 005 — the scans are MIXED RESOLUTION and step 005 hardcodes 2400 dpi

**What the rules say.** r000, *Where the scans are*: "`/Volumes/S/png/<ID>/NNN.png`
the 2400 dpi masters". r005_masters_sheet.py: `SCAN_DPI = 2400`,
`SCAN_REDUCE = SCAN_DPI // MASTER_DPI  # 4`. r000's thumb recipe: one command,
`magick "$m" -scale 6.25%` for every master.

**What I did.** Ran the thumb recipe verbatim over all 168 masters. 160 of the
thumbs came out ~317 × 449 px — 37.5 dpi, not 150.

**What is true.** SH8602's pages **003–162 are 600 dpi** (`5029 × 7188` px,
`236.22 px/cm`, ~63 MB); only **001, 002, 163–168** are 2400 dpi
(~20300 × 28751, ~850 MB). The raw TIFFs in `/Volumes/S/scan/SH8602/` are the
same (~72 MB interior, ~1 GB cover), so no 2400 dpi copy of the interior
exists. r000 *does* hint at this — `create_thumbnails.sh` "branches by page
range because that issue's scans were *mixed resolution*" — but as a reason to
distrust found thumbs, not as a property the chain must handle. Re-derived the
interior thumbs with `-scale 25%`; all 168 are now 1256–1349 px wide.

**Cost.** ~5 min, 4 commands to notice and re-derive. The real cost is
downstream: step 005 sheet cannot run on 160 of 168 pages as written.

**What would have prevented it.** r000 thumb recipe: "Scale each master by
`150 / its own dpi` (read `%x` from the PNG), never a fixed 6.25 % — SH8602 is
600 dpi on 003–162." And r005: `SCAN_DPI` per page from the PNG header.

## 005 — the sheet variant asks for a "measured colors.txt" and says nowhere how to measure one

**What the rule says.** r005_masters_sheet.md: "`low` — the cheap interior
stock … this issue's **measured** `colors.txt`". The procedure for measuring
`W` lives only in r005_masters_spread.md, *The profile is MEASURED for this
issue's paper*; the sheet rule points at SH8601's existing file.

**What I did.** Found no `colors.txt` beside SH8602's scans (correctly — r005
spread says the profile lives in the repo) and went looking in the sheet rule
for the procedure; it is not there. Took it from the spread rule.

**Cost.** ~3 min, 3 commands.

**What would have prevented it.** One line in the sheet rule's *Two papers*
section: "For a new issue, measure `paper.low` as in r005_masters_spread.md
*The profile is MEASURED* (pool interior thumbs, low percentile) and write it
to `issues/<ID>/colors.txt`."

## 005 — the mixed-resolution fix, as made (moved under the build)

The resolution problem above BLOCKED step 005, so it was fixed at once
(r000: "a defect that BLOCKS the build … is fixed at once … recorded in the
errata as having moved under the build"). The owner, asked at PAUSE 1, chose
this over a rescan.

- `r005_masters_sheet.py`: new `scan_dpi(scan)` reads the PNG pHYs, snaps to
  `SCAN_DPIS = (600, 2400)`, and cross-checks that the frame is 250–350 mm tall
  at that resolution (else `PageFailed`). The reduction is per page:
  `dpi // MASTER_DPI`, so 4 at 2400 (unchanged) and 1 at 600. A 600 dpi page
  has no `masters2400/NNN.png`; its full-resolution render goes to scratch,
  because there it IS `sheets600`. `cmyk2400/NNN.tif` is still written (the
  separation, at the scan's own dpi). Every stamp gains `scan-dpi`.
- **Before/after, measured** on p050 (600 dpi) and p163 (2400 dpi):
  - p050 before: traced **53.2 × 76.0 mm**, published as an uncropped sheet
    (every mm constant read at a quarter scale). After: **209.2 × 296.9 mm**,
    A4 class, own-paper white 255, dark contrast 251.
  - p163 before → after: `masters600`, `sheets600`, `masters2400` and `debug600`
    all **pixel-identical** (`magick compare -metric AE` = 0); the profile
    is byte-identical; the stamp differs by the one added `scan-dpi 2400` line.
- **Consequence for r005's Verification 1** ("every page produced all six
  artefacts"): it now has to expect no `masters2400/NNN.png` for a 600 dpi
  page. Not edited mid-build; harvest it.
- The lane peak (19 GB) is a 2400 dpi number; a 600 dpi lane is ~1/16 of it.
  Sized by the rule anyway (`lanes(19)` → 10).

## 005 — the sheet Verification names an output the code no longer writes

**What the rule says.** r005_masters_sheet.md, Outputs and Verification 1, 4, 6:
`<tmp>/figures600/NNN.png` "the figure master — r145 reads this", read through
`R.OUT_FIGURE`.

**What is true.** `r005_masters_sheet.py` has no `OUT_FIGURE` and writes no
`figures600/`; its outputs are `masters600`, `masters2400`, `sheets600`,
`cmyk2400`, `debug600` (`OUT_DIRS`). Only the module docstring still says
`figures600`. Pasted verbatim, checks 1, 4 and 6 die with `AttributeError`
before checking anything.

**What I did.** Ran them with `figures600` replaced by the directory that
exists. Recorded which in LOG.md, per check.

**Cost.** ~5 min reading code to establish it.

**What would have prevented it.** Outputs/Verification rewritten against
`OUT_DIRS`: `sheets600/NNN.png` is the uncropped graded sheet, and the
figure-render check (6) has to say which of the two existing renders is
uncurved, or be dropped.

## 005 — Verification 4 flags 166 of 168 pages on the printed footer

**What the rule says.** Check 4: "a 6 mm band inside the TRACED PAGE's own
four edges holds no bed and no prop — except where full-bleed art
legitimately reaches the trim." It prints numbers; it does not say what
"holds no bed" means numerically, and its worked table was SH8601's.

**What is true.** SH8602 prints a black `SONDERHEFT` bar, the 64'er logo and
the folio 3–5 mm above the foot on every interior page, so the bottom band
reads 10–28 % "dark" (lum < BED_LUM) on almost every page. Looked at 007 and
009 at the foot: print, no bed. A per-page printout of 168 lines in which
nearly every line is non-zero is not read by anyone.

**Also:** check 6's premise (figures600 is the UNCURVED render) does not hold
for what exists: `sheets600` measures glyph p50 21/24/19/20 on
050/100/120/150, identical to `masters600`. Both carry the curve. The
"fidelity" render the rule promises figure cuts does not exist in the
current code.

**What would have prevented it.** Check 4 should compare against a band
1–2 mm *outside* the trim line (where only bed can be), or exclude rows that
are dark across ≥ 40 % of the width in one run (a printed bar), and state a
threshold. Check 6 should be rewritten against what the code writes.

## 040 — the script does not implement the rule's "length 2 only if paired"

**What the rule says.** "length == 2 → keep only if it pairs within the
paragraph; an unpaired `**` is a literal and is escaped." **What is true.**
`r040_escape_asterisks.sh:39` keeps every length-2 run unconditionally
(`return m.group(0) if n == 2`); the Verification still says the bold count is
"invariant by construction". No effect on SH8602 (no `**` outside fences);
the next issue with an unpaired `**` ships it as a bold delimiter. The script
also calls bare `python3`. And the Notes' "List bullets in this project are
always `-`" is false for this OCR output: SH8602 has 9 `* ` bullet lines,
which become literal `\*`. Found by the 040 sub-agent; ~1 min.

## 120 — "the same root with the SH naming" points at the wrong disk

**What the rule says.** "For Sonderhefte the file lives under the same root
with the SH naming." **What I did.** Looked for `SH86*`, found
`SH8X/SH86A.D64` / `SH86B.D64` — a plausible "SH 86, sides A/B" — and nearly
took it. Its directory (Dateiverwaltung, Haushaltskasse, Floppy, Sound) is not
this issue. **What is true.** Sonderheft disks are numbered by the magazine's
running Sonderheft number, not by year: `SH0X/SH01.D64` is SH 1/86 (SH8601's
prg.txt names it), `SH0X/SH02.D64` is SH 2/86 — header "sonderheft 2/86",
separators matching this issue's pages. **Cost.** ~5 min, 6 commands.
**What would have prevented it.** "Sonderheft N/86 is
`~/tmp/64er-Disketten/SH0X/SH0N.D64`; confirm by the disk header
(`sonderheft N/86`). `SH8X/SH8nA/B` are other Sonderhefte — do not match on
the year."

## 050 — rule and script disagree on `</`+non-letter, and on why it is idempotent

"EXCEPT `</` followed by a non-letter … Escape those too": the script's regex
`<(/?[a-zA-Z][^<>\n]*?)>` needs a letter after `/`, so `</>` passes through,
and the Verification uses the same letter-first regex so it cannot see it
either. The "lookbehinds for `\`" given as the idempotence reason are not in
the script (it is idempotent because entities carry no `<`). Moot on SH8602
(0 occurrences). An unclosed `<`+letter (`31 <A AND`) is not discussed;
Discount happens to escape it. Found by the 050 sub-agent.

## 060 — `<ol>` without `start=` silently renumbers; nothing checks it

**What the rule says.** "`<ol type="a">` in a converted file is a **bug
signature**" — the only list defect it names. **What is true** (060 sub-agent,
SH8602): Discount emits no `start=`, so every printed list not starting at 1
shows from 1 (9 lists here), a list interrupted by prose becomes one-item
`<ol>`s that all say "1." (~20 here), two adjacent lists fuse and continue
numbering, and a BASIC line `1000. PRINT …` loses its line number entirely —
the same silent text loss as `M. Grewe`, by another route. The corpus carries
one `<ol start=` in 130+ `<ol>`, so earlier issues probably shipped this
unseen. Also: the rule's `<p><pre>` example does not reproduce on Discount
3.0.2.0 (post-pass unwrapped 0; its regex also misses `<p> <pre>`); a literal
`\*` inside a raw `<p class="source">` block ships as `\*`; and the "`<br` >
0" spot-check passes on hand-written `<br>` alone.
**What would have prevented it.** A 060 check: every `<ol>` whose source line
begins with N≠1, or a number ≥ 100 (a BASIC line), is listed for 190 with
its source line; and `<ol start="N">` named as the fix.
**Cost.** None yet; found by the 060 sub-agent, fixes owed at 190.

## 070 — the script still has the ordering bug its rule says was fixed

"Order matters: fold the curly quotes FIRST, then `''`. As shipped, `''` →
`"` ran before…" — `r070_html_cleanup.sh` still lists `("''", '"')` before
the curly folding. The rule also says a formula's double prime must be left,
while its table and script convert every `''`. And the rule file's own curly
characters have been flattened to ASCII in places, so table rows read
`"` → `"`. No effect on SH8602 (one `''`, OCR garbage). Found by the 070
sub-agent.

## 080 — Verification 4 rejects the lettered pages the same rule demands

`grep -vE 'content="[0-9,\- ]+"'` flags every `NNNa`/`NNNb`, which "Three
conventions" requires; and nothing says the FILENAME keeps the plain number
(the corpus does: 8507, 8508). The splitter turns ANY `<p>(…)</p>` into a
byline, and its DOTALL regex can span paragraphs — SH8602 got 7 false
bylines and one `<address>` that swallowed two paragraphs and broke the
`<head>`; a post-split check ("every `<address>` matches `(Name/)xx`") would
have caught them. The "escaped HTML text" sentence does not describe the
code (it strips tags, keeps entities). The script calls bare `python3`.
Also: which `64er.issue` form a Sonderheft takes is shown only by the Usage
example (`'Sonderheft 7/86'`), and SH8601 shipped `SH8601` — I briefed from
the outlier first. Found by the 080 sub-agent; correction ~3 min.

## 110 — the Sonderheft case is "all" in the header and monthly in the body

"Applies to: all — the README's release table carries the Sonderheft dates
too". It carries bounds ("**vor** 14. Februar 2026", "ca.", "unbekannt"),
which "Convert `TT. Monat 20JJ`" cannot read; the Vorschau derivation is
monthly-only; the Verification grep `"${YYMM:2:2}/${YYMM:0:2}"` with 8602
digits matches the MONTHLY 02/86 bullet (and breaks on `SH8602`). Nothing
says what to do with a bullet that holds a bound. Wrote a provisional date and
carried it to PAUSE 2. Found by the 110 sub-agent.

## 090 — small inaccuracies

"Find the TOC pages in the issue's PDF (usually pages 6–7…)" — names the PDF
the next block forbids, and assumes two pages (this Sonderheft: one, p5).
"entry is the printed entry text" — title only, or title + subtitle? and
what of entries not printed at all (Eintipphilfen, Impressum)? Check 2 says
"run once all toc_category metas are filled", but from 080 on every file
carries `XXX`, so before 100 it fails rather than being vacuous. "Normalised to
Title Case" is wrong for German ("Listings zum Abtippen"). Found by the 090
sub-agent.
