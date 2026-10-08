# SH8608 — WORKFLOW_ERRATA

Kept as the build runs (r340). One entry per place the instructions failed it.

## 005 — "r005_field.py runs FIRST, once" cannot run before PAUSE 1

**What the rule says.** r005_masters_sheet.md, *Run*: "`$PY r005_field.py   # ONCE, first`"
and "**`r005_field.py` runs first, once per issue**". The control brief for this
build repeated it: "`r005_field.py` runs FIRST, once, and it is not optional".

**What I did.** Planned to run it right after the descriptor and `colors.txt`,
before reporting PAUSE 1. `grep` showed `r005_field.py:714` calls
`R.first_action()`, which refuses an issue with no `binding`. So "first" means
"first after PAUSE 1", not "first thing in the build" — on an issue whose binding
is still open it cannot run at all.

**What it cost.** One grep, ~1 min; nothing run wrong.

**Suggested.** In *Run*: "`r005_field.py` runs once, AFTER PAUSE 1 is fully
answered and BEFORE the sweep — it calls `first_action()`, so with `binding` or
`paper` unanswered it refuses exactly as the sweep does."

## 005 — the colors.txt snippet cannot run before PAUSE 1 either

**What the rule says.** r005_masters_sheet.md: "**MEASURE `colors.txt` BEFORE
PAUSE 1, not after.** … The measuring method is in `r005_masters_spread.md`".
That method's snippet does `import r005_masters_spread as R` and iterates
`R.ISS.page_range` / `R.THUMB_DIR`. r000 says of the same module:
"`r005_masters_spread.py` refuses to load at all on an absent `binding`."

**What I did.** Did not run the snippet; wrote the same pool (body box
10-90 % x 12-88 %, `lum > 170`, `max-min < 40`, interior pages only) directly
against `<tmp>/thumb150`, plus the K check from *EXCEPT K*. Also note the snippet
pools `R.ISS.page_range` — ALL pages, wrapper included — while its comment says
"INTERIOR pages only"; nothing in it excludes `high_pages`.

**What it cost.** ~3 min, one script.

**Suggested.** Give r005_masters_sheet.md its own snippet that imports only
`r000_issue` (which loads with `binding` absent), reads `thumb_150`, and
excludes `paper.high_pages` explicitly — the step that must run before PAUSE 1
must not depend on a module that refuses to load before PAUSE 1.

## 005 / 006 — "2400 dpi marks colour" misses colour pages AND hand marks at 600 dpi

**What the rule says.** r005_masters_sheet.md, witness 2: "The owner scans
COLOUR pages at 2400 dpi and everything else at 600", refined to "read it as
'the owner SAW colour here'", with manual colour markings described as a reason
a page is at 2400. The control brief: "Some of those pages are at 2400 because
the owner's copy carries a MANUAL COLOUR MARKING".

**What I did.** Inspected the six interior 2400 dpi pages (004 010 015 021 025
034) for a marking-only page, as briefed: all six carry genuine plate colour
(printed red display type, blue type, rainbow logo, tinted illustration; 034's
script price is a printed face with a printed red rule). Then, unprompted, ran a
saturated-pixel census (chroma > 80) over ALL 166 thumbs and found:

- **plate colour on five 600 dpi pages**: 009 (15.8 % saturated), 026 (12.1),
  020 (4.5), 031 (3.3), 162 (0.7) — red ad, tinted diagrams, red rules,
  rainbow logo;
- **the hand marking is on a 600 dpi page**: p003, green highlighter over three
  lines of the Einleitung. Not at 2400 at all.

So on this issue dpi is neither sufficient nor necessary for colour, and the
marking the owner warned about would not have been found by looking where the
rule points.

**What it cost.** ~10 min, five commands. Without the census the p003 marking
would have reached r006 as a "colour page" or the PDF silently.

**Suggested.** In witness 2: "dpi is a HINT about colour, not a census. Run a
saturated-pixel census over every thumb (chroma `max-min > 80`, off the bed),
view the hits, and attribute each to PLATE or HAND before PAUSE 1. On SH8608
five colour pages were at 600 dpi and the one hand marking (p003, highlighter)
was on a 600 dpi page." And the same pointer in r006's plate-vs-hand section.

## 005 — the own-white gap does not separate the back cover leaf on SH8608

**What the rule says.** Witness 1: "The wrapper and any bound-in card sit far
from the interior with a clear gap", read per dpi, ties settled by the leaf
partner.

**What I did.** Computed it with the program's `paper_evidence()` against this
issue's `W 188 169 158`. 2400 dpi: 002 157, 165 136, 166 134 (wrapper/card),
then 164 99, 034 95, 025 94, 021 92, **163 87**, 010 80, 004 77, 015 77, 001 57.
The back cover leaf 163/164 lands INSIDE the 2400 interior band; only the
owner's answer puts it on the good stock. No contradiction — the owner answered
— but the witness would not have found it. Also: absolute distances are not
comparable to the rule's quoted SH8604 figures, because own-white is p90 of the
sheet and W is p2 of the pool; the 600 dpi interior baseline here is 60-70, not
~0-20.

**What it cost.** ~2 min.

**Suggested.** "Own-white is the sheet's p90 against the pool's p2, so the
interior baseline is ~60-70, not 0. A printed-tint back cover (SH8608 163/164)
does not separate from 2400 dpi interior colour pages; only the owner's answer
places it."

## 000 — a rule that saved me: read dpi from pHYs

The pHYs warning (r005 witness 2, and the control brief) gave the census in one
pass: 154 @ 600, 12 @ 2400, matching the brief exactly. Keep it.

## 000 — a rule that saved me: "LOOK at the mask on the darkest page"

The K check's darkest page (p135, 31 27 27) was confirmed on the rendered mask
to sit on the printed checksum bars of the listing, none in the bed. Cheap, and
the only way to know.

## 005 — the rules moved under this build at PAUSE 1 (0be19821)

Recorded per r340: control fixed the three PAUSE 1 findings above mid-build
(`0be19821`, r005_masters_sheet.md and r006_issue_pdf.md) — the colors.txt
recipe now imports `r005_masters_sheet`, "field runs first" now says "first of
the 005 programs, after PAUSE 1", and the dpi witness is no longer the
instrument for colour or markings. Nothing already done needed redoing: the
profile reproduces to the same p2 (188 169 158). Steps from here on run against
the post-`0be19821` text.

## 005 — the census that found p003 is not yet a step

**What the rule says.** After `0be19821`: "Sweep for colour and for markings
over EVERY page, independent of dpi (r006 has the measure)".

**What I did, with numbers.** On the 150 dpi thumbs, cropped 3-93 % x 4-96 % to
stay off bed and prop, the fraction of pixels with chroma `max-min > 80`.
Yellowed interior paper sits at chroma ~45, so 80 is clear of it. Results:
2400 dpi pages 1.0-25.1 %; 600 dpi 009 15.8, 026 12.1, 020 4.5, 031 3.3,
003 0.80, 162 0.74; then a tail from 005 at 0.19 % down, which on an overlay
(saturated px outlined, original colour kept) is orange foxing specks at the
margins only — no strokes. p003's 0.80 % was the highlighter. The deciding step
was LOOKING at the overlay of every hit above ~0.015 %, not the number: p003
and p162 score alike (0.80 / 0.74) and one is a hand, the other the rainbow logo.

**What it cost.** ~10 min, five commands. Cheap enough to run every issue.

**Suggested.** A step-005 item before PAUSE 1: "Run the saturation census
(chroma > 80 on the thumbs, off bed and prop) over every page, montage an
overlay of every page above 0.015 %, and attribute each hit PLATE / HAND /
FOXING in LOG.md. A number cannot tell a highlighter from a logo; the overlay
can." Ideally as a script beside r005_field.py so it is not re-typed.

## 005 — the Run section prescribes one process; r000 requires lanes

**What the rule says.** r005_masters_sheet.md *Run*: "`$PY r005_masters_sheet.py
# every page`" and "~45 s per page; ~2 h for 152 pages". r000: "Every step that
fans out over pages locally — 005 masters, … — sizes its lanes … none of them
may hardcode a number", `lanes(19)` for 005.

**What I did.** The program has no fan-out of its own (no `lanes(`, no pool),
so "every page" as written is one serial process. Ran it as
`xargs -P $(lanes(19)) -n 1 … r005_masters_sheet.py`, 2400 dpi pages queued
first. lanes(19) = 9 on this box today.

**What it cost.** One grep, ~1 min.

**Suggested.** In *Run*: "the program is serial; fan it out —
`seq 1 N | OMP_NUM_THREADS=1 xargs -P $("$PY" -c 'import r000_issue;
print(r000_issue.lanes(19))') -n 1 "$PY" r005_masters_sheet.py` — and queue the
2400 dpi pages first; 19 GB is their peak, a 600 dpi page needs far less."
