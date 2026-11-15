# Corpus queue — cross-issue findings, parked for assignment

Findings about **already-published issues** that a build turned up while working
on a different one. They are not the live build's work (r000: *the issue you are
working on is the scope*), and they are not control's either — control parks and
assigns; a sibling does them.

**This file exists because the queue kept living in a conversation.** A
multi-session queue must live in the repo, not in a scratchpad and not in a
summary: the scratchpad is wiped between sessions and a summary loses the
measurement. Every item here therefore carries **the check that re-establishes
it**, so the assignee never has to trust a remembered number — including when
the number here turns out to be stale.

Published HTML is edited freely; published PDFs and masters are not re-made
(owner). So everything here is an HTML, metadata or tools change.

---

## 1. `issues/8412/139` — IECOUT is `$FFA8`, the file says `$FFA5`

The Kernal table on p139 lists `IECOUT` and `IECIN` with the SAME address.

    grep -n 'IECOUT' -A1 "issues/8412/139 In die Geheimnisse der Floppy eingetaucht (Teil 3).html"
    # line 47-48: IECOUT  $FFA5      <- wrong
    # line 53-54: IECIN   $FFA5      <- right

**Confirmed three ways**: two routines cannot share one vector; `$FFA8` is CIOUT
and `$FFA5` ACPTR; and SH09 p39, which reprints this series, prints `IECOUT
$FFA8` / `IECIN $FFA5`. Found by SH09's 300 agent reading 8412 p139 at full
resolution. **Re-read 8412 p139 before editing** — the builder that reported it
did not re-read it itself, and the one-character fix is only safe if the page,
not the inference, says so.

## 2. `issues/8411/117` — the disk's listing NUMBER is not the print's

Reported by the same agent: line 218's `Listing 6` caption carries the sort
program, while p120 prints the long write-protect program as Listing 6, whose
text is in no HTML. **The disk file names are the suspect, not the caption.**
MEASURED here: `issues/8411/prg/floppyk.listing5.txt` and
`issues/SH09/prg/floppyk.listing6.txt` are the IDENTICAL program (the short
write-protect, lines 100-260), and `8411/prg/floppyk.listing6.txt` is a
directory sorter. So the disk's `listingN` numbering and the print's listing
numbering diverge across these two issues, and r130 placed by the filename.

    diff <(grep -oE '^ *[0-9]+ .*' "issues/8411/prg/floppyk.listing5.txt") \
         <(grep -oE '^ *[0-9]+ .*' "issues/SH09/prg/floppyk.listing6.txt")

**Open 8411 pp 117-120 and read the printed listing numbers** before touching
anything; then fix the captions AND check the other floppyk listings in both
issues. A rule note for r130 (a filename's number is not evidence) belongs with
the fix.

## 3. The MSE header carries OUR filename, not the printed program name

`generate.py:723` passes `data_filename` into `tools/mse.py`, which uppercases
it and strips `.PRG`, so a **print-derived** file whose name we invented leaks
its suffix into a reader-facing header: SH09's `dos v3 mse.prg` renders
`PROGRAMM : DOS V3 MSE` where the print says `dos v3`, and
`ker v4 (ex-smon).prg` renders `KER V4 (EX-SMON)`.

    grep -rhoE 'data-filename="[^"]*"[^>]*data-mse' issues/*/*.html | sort -u | grep -E '\(|mse'

The faithful fix is an explicit MSE-header name (e.g. `data-mse-name`) with the
filename as the default; renaming the files is not available, because the
print-derived program and the disk binary are different programs that would
want the same name. **A tools change touching every issue's rendered listings,
so it goes to the owner with the next push, not into a build.** Check first
whether any of `basic-ex_mse`, `break mse`, `change mse`, `pg-mse` are DISK
names (faithful) rather than ours — the survey above does not distinguish them.

## 4. `issues/8604/12` — index title says Interpol, the article says Interpool

    grep -n 'Interpol' "issues/8604/12 DFÜ-News.html"
    # line 13: <meta name="64er.index_title" content="DFÜ-News: Interpol">
    # line 21: <h2>Interpool</h2>, and the body says Interpool throughout

The print decides. (8612/174's "Visit Interpol" is a game menu and correct —
do not sweep on the word alone.)

## 5. Fehlerteufelchen asides with no issue trailer

    for f in issues/*/*.html; do grep -q 'class="fehlerteufelchen"' "$f" &&
      ! grep -q "<!--\s*64'er" "$f" && echo "$f"; done

**3 files today**; an earlier count of 4 was of ASIDES, and a file can hold two.
Count asides, not files, when working it.

## 6. Thirteen published files carrying `&#x27;`

    grep -rl '&#x27;' issues/*/*.html | wc -l      # 13

An entity where the character belongs. Mechanical, but read one before
sweeping — the apostrophe in `64'er` is typographic and the files differ.

## 7. r320 noise sweep over SH8605-SH8608's Fable-labelled HTML

The four Sonderhefte whose HTML was labelled by Fable. Intermediates are at
`~/DNB/<ID>/tmp`. Parked since 8701 closed (2026-11-03); never assigned.

## 8. ~98 published articles showing contents wording over the year index

Measured earlier in a control session, NOT re-measured here. **Re-measure
before acting**; the number is the kind that drifts as issues are added.

## 9. Two index titles in 8705

Same provenance as 8. Re-measure.

## 10. The census recall test with planted ground truth

Not a published-issue item — a rules measurement, parked deliberately. r000
records the design: synthetic strokes of known length and luminance drawn across
a word, through a margin and in white space on copies of a couple of bilevel
pages, census run unchanged, report which surface. It is the only instrument
that escapes the circularity of testing recall against a census the same
populations built. Do it after SH09 closes.

## 11. `issues/8609/156` — a status comment no file records

    $PY tools/img/scan2ocr/rules/r300_status_pairs.py issues/8609
    # FAIL 156 Tips und Tricks zu Vizawrite (Teil 9).html: carries a status
    #      comment citing 10/1986, but no prg/*.txt header ... names any of them

The aside claims `Disk-Version bereits korrigiert` for the 10/1986 erratum, and
nothing in `issues/8609/prg/` says so: `viza.patch.bas.txt` and
`viza.patch.quell.txt` carry only their `;name.prg ==addr==` line, while
`viza.key.prg` and `viza.umlaute.prg` are MSE-rendered BINARIES with no header
line to carry a note at all.

**Pre-existing, not a regression** — the check that preceded
`r300_status_pairs.py` failed on it identically, so the line has been red
(or unrun) since the status check was added. Two possible truths and the page
decides which: the claim is right and the record is missing (add the header to
`viza.patch.bas.txt`), or the erratum concerns one of the binaries, in which
case 8609 needs a `reviewed/errata_status.txt` line exactly as SH09 does. Read
8609's own Fehlerteufelchen and 10/1986's text before writing either.

**This is the same shape as SH09 article 113**, which is worth knowing: a binary
program with an erratum and nowhere to record it is not a one-off, it is a
condition the corpus already contains.

## 12. Fifteen assembler listings whose comment columns we collapsed

The print aligns an assembler listing's comment column; fifteen `<pre>` blocks
in four issues set every comment one space after the operand instead. That is
our normalisation over the paper, which r000's *CONSISTENCY WITH THE PAGE BEATS
CONSISTENCY WITH ITSELF* forbids, and it was found because SH09's reader L
cited `SH8608/79` as precedent for doing the same — the reprint's HTML was
evidence of the habit, not of the page.

MEASURED 2026-11-14. SH8608 p80 prints `LDA #$01`, a wide gap, then
`;LOGISCHE FILENUMMER 1`; `issues/SH8608/79 Dateiverwaltung mit dem C 16 in
Maschinensprache.html` line 120 has one space. Of 250 assembler `<pre>` blocks
in `issues/`, 15 collapse every comment this way, in **8601, SH8601, SH8602 and
SH8608**. The other 235 keep some column structure, so this is a 6 % residue
and not a house style to be undone everywhere.

Re-establish:

```bash
.venv/bin/python - <<'PY'
import glob, re
for f in glob.glob("issues/*/*.html"):
    h = open(f, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"<pre(?![^>]*data-filename)[^>]*>(.*?)</pre>", h, re.S):
        ls = [l for l in m.group(1).split("\n")
              if re.search(r"\b(LDA|LDX|LDY|STA|JSR|JMP|BNE|CMP)\b", l)]
        cm = [l for l in ls if ";" in l]
        if len(ls) >= 3 and cm and all(re.search(r"[^ ] ;", l) for l in cm):
            print(f)
            break
PY
```

The test is crude — it finds a block where EVERY comment is one space after the
operand, so a partly normalised block passes it. Treat 15 as a floor.

Each one needs its page measured at its own pitch (r325, *A SPACING QUESTION IS
ARITHMETIC*) and the arithmetic recorded beside the fix. **Do not run it from
SH09's reading**: each issue's own page decides its own columns.

## 13. Three published issues' step-330 tables are off by one

`r330_reprint_compare.py` paired a block by token bag normalised over the
SMALLER bag, so a short block matched any long block containing its words.
Fixed 2026-11-14 with a two-sided coverage test (`MOVED_COVER`). The fix
changes what the tool reports for pairs already dispositioned, and three
published issues now fail their own gate by exactly one difference:

| issue | pair | table says | the tool now reports |
|---|---|---|---|
| SH8604 | 8602/57 | 7 | 6 |
| SH8605 | 8602/57 | 15 | 14 |
| SH8608 | 8512/146 | 1958 | 1957 |

MEASURED on SH8608's `10 Basic-Kurs für C 16-Einsteiger.html` against
`8512/146`: **78 of its 85 MOVED pairings were spurious** — `FAST` against an
87-word paragraph, `POKE` against another, `Insert` against *Flagge für
INSERT-Modus*, table headings against unrelated prose, every one at sequence
similarity below 0.3. The D count barely moves because a dropped pairing
becomes two one-sided blocks, but the RECORD changes a great deal: 78 cascades
of invented differences become honest "block only in X" lines.

Re-establish:

```bash
for i in SH8604 SH8605 SH8608; do printf "%-8s " $i
  .venv/bin/python tools/img/scan2ocr/rules/r330_reprint_compare.py verify issues/$i | tail -1
done
```

Each needs its LOG table's count corrected and the one affected difference
re-dispositioned — small, but it is a published issue's record, so do it
deliberately and per issue. **The wider question is not queued and should be:**
every 330 record made before this fix rests partly on bag-only pairings, and
nobody has measured how many of SH8607's 23 pairs or SH8603's 17 are affected.

## 14. 8612/21 carries no reprint note, and SH10 is its ORIGINAL

MEASURED on SH10, 2026-11-15, at step 330 Step 0: article 27 matches
`8612/21 Schneider-Test` at 0.82–0.95 over three blocks, and **SH10 is the
earlier print** — it reached the kiosk "Ende September 1986", and 8612/40 cites
"Sonderheft 10/86" itself. So 8612 reprints SH10, and our corpus has the pair
the other way round purely because we publish chronologically and shipped 8612
first.

Step 140 had dismissed it as "not a lead" for exactly that reason: the
direction was inverted, so the usual test (is the OTHER issue already
published?) answered the wrong question.

**What is owed:** `8612/21` is published with no reprint note pointing at
SH10. Whether a reprint note belongs in the LATER-published but EARLIER-printed
direction is itself a question nobody has answered — the metadata has only ever
run one way. Decide the convention once, then apply it to this pair.

**Not urgent, and not SH10's work:** the pair was diffed as an OCR cross-check
with no credit claimed either way, per r330, *THE DIRECTION CAN BE REVERSED*.

## 15. The traced top/bottom line can take a skew the page does not have

SH10 p002 lost 869.9 mm² of print from a white wedge along the top of the page.
It looks exactly like the bed drop that `BED_REACH_MM` now caps, and it is a
different defect: measured per 500 px column the band is 0, 203, 174, 149, 123,
97, 71, 46, 20, 0 px deep — **a straight line falling 25.8 px per 500, i.e.
−2.95°**. A connected-component flood has a ragged boundary; a line fit is
straight. This is `t.keep`'s own top line, from `trace(tops, …)` at
`r005_masters_sheet.py:1977`, taken off an ink/bed edge on a page where print
runs to the scan edge, with nothing above the print for the tracer to find.

p002 currently carries a hand override (`regrade_002.py`, recorded in
`a4600-overrides.txt` with both-ways figures). **That override exists only
because this rule is not written yet.**

THE SHAPE OF THE GUARD, not yet measured: a top or bottom line more than about
1° off the page's own skew, where the opposite edge is near level, is not a
page edge — on p002 the bottom line sits at −0.09°, so the two disagree by
2.86°. Refuse the outlier and fall back to the scan edge, or to the opposite
edge's angle.

WHAT HAS TO BE MEASURED FIRST, corpus-wide: the distribution of (top angle −
bottom angle) over every page of every issue with a working tree. The guard's
threshold has to sit above the honest disagreement a real paste-up produces —
r005 already records that **two printed straights that agree are a scan
rotation, two groups that disagree are the paste-up** (SH10 001/002 and
167/168), so some disagreement is real and must survive.

**Deliberately NOT bundled with `BED_REACH_MM`.** Both change `t.keep`, and
one 3 h re-derive that moves two things cannot say which one moved the result.
Land this on its own, with its own before-and-after ink sweep. When it lands,
p002's override should become redundant; its record says so.
