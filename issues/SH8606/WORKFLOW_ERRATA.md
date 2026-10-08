# SH8606 — WORKFLOW_ERRATA

Kept as the build runs (r340). One entry per place the instructions failed it.

## 000 — `ISSUE.txt` is one file per working tree, and two builds share this tree

**What the rule says.** r000, *BEFORE ANYTHING ELSE*: "`echo 8612 >
tools/img/scan2ocr/rules/ISSUE.txt` … `ISSUE.txt` is git-ignored: which issue
a working tree is building is a local fact. `ISSUE=8612` in the environment
overrides it for a single run." r000_issue.py: "survives across shells, and is
what an issue build sets once at the start".

**What I did.** Started as instructed, found `ISSUE.txt` already reads
`SH8608` — the sibling build's, in the same working tree (`git worktree list`
shows one tree). Writing `SH8606` into it would have pointed every one of the
sibling's subsequent steps at my descriptor, silently, which is exactly the
failure the file exists to prevent. So this build never touches `ISSUE.txt`
and prefixes EVERY command with `ISSUE=SH8606`; the shell does not persist
between calls, so the prefix is per command, not per session.

**What it cost.** ~2 min to notice; the risk, had I not, was the sibling's
next step writing SH8608 pages into SH8606's `<tmp>`.

**Suggested.** In r000 *BEFORE ANYTHING ELSE*: "When two builds share one
working tree (`git worktree list` shows one), `ISSUE.txt` belongs to whichever
started first; the second build uses `ISSUE=<ID>` on every command and never
writes the file. The `.sh` wrappers inherit the environment, so the prefix
works for them too."

## 005 — "r006 carries the method" for the colour census, but r006's method needs masters600

**What the rule says.** r005_masters_sheet.md witness 2: "Sweep for colour and
for markings over EVERY page, independent of dpi (r006 has the measure)".
r006's measure (*THE COLOUR TEST MISSES THIN COLOURED LINES*) opens
`master` = `masters600/NNN.png`, resizes 600→150 and applies the largest-blob
≥ 50 mm² / strong-chroma ≥ ~10 mm² test with a paper mask or a 4 mm edge band.

**What I did.** The census is wanted BEFORE PAUSE 1 (markings go to the owner
with the PAUSE 1 evidence), when no master exists. The only thing r006's
recipe can run on here is the thumb, and the rule does not say so. I ran what
SH8608's errata describes instead — fraction of thumb pixels with chroma
`max-min > 80`, cropped 3-93 % x 4-96 % — plus a second column at chroma ≥ 60,
and an overlay montage of the top twelve. Result on SH8606: sat>80 is 0.000 %
on every one of the 176 interior pages and 4.7-19.1 % on the four wrapper
pages; the chroma ≥ 60 tail (0.2-0.38 % on 009 022 020 023 006 120 …) is the
frame border plus halftone fringing inside p009's dithered title art, which at
600 dpi is black screen on paper. No hand marking found.

**What it cost.** ~5 min deciding which measure to run, one wrong cwd.

**Suggested.** In witness 2: "Before PAUSE 1 the census runs on the THUMBS:
fraction of pixels with chroma > 80 inside 3-93 % x 4-96 %, plus an overlay
of every page above 0.015 %; attribute each hit PLATE / HAND / FOXING by eye.
r006's blob test is the second pass, on masters600, after 005."

## 005b — recovery C's "luminance profiles" cannot be read off the GRADED master on a dark-ground page

**What the rule says.** r005_a4_window.md, recovery C: "A failed page whose
ground is full-bleed dark … is cut from row and column luminance profiles: the
prop shows as a step at the foot, the bed as a plateau darker than the page.
MEASURED on SH8602/155: … dark-brown ground ~10 against bed ~3". And: "Cut
from `masters600`".

**What I did.** Took the row/column luminance of `masters600/151.png` (the
te-wi ad, full-bleed dark brown). The grade had pushed the ground to lum 3–5
and the bed sits at 0–8, so no step separates them; the only steps were the
lit prop at the foot and the fabricated white beyond the raw frame. Went back
to the RAW 150 dpi thumb, where the ground is lum 27–29 with R−B 3–4 and the
bed lum 5 (left) / 23 (right) with R−B 0–1: the sheet's trim is a clean step in
both profiles there. Scaled ×4 into the master frame (sheet-box 0 0, so master
frame == levelled sheet frame; the centre-band reading is first-order invariant
under the 0.20° levelling). Window anchored on that corner, 1.2 mm beyond the
trim mirror-filled.

**What it cost.** ~15 min and three measurement scripts before the thumb was
tried.

**Suggested.** In recovery C: "Read the profiles off the RAW thumb (or the
raw scan), never the graded master: on a dark ground the grade sends the ground
to within a few levels of the bed (SH8606 p151: ground 3–5, bed 0–8). On the
thumb use colour too — the ground is warm (R−B ≥ 2), the bed neutral. Scale
the trim ×(600/150) into the master; the levelling moves a centre-band edge by
under a pixel. And fill the strip beyond the trim by MIRRORING the page
(r005's fill rule), because a full-bleed dark page has no paper white to
paint."

## 005 — the levels were "identity until measured" and nothing said WHEN the measurement is due

**What the rule says.** r005_masters_sheet.md, *Two papers, two profiles*:
"The levels stay the identity because nobody has measured that stock; a level
line is a per-ink contrast decision that must be measured, not guessed."
r005_masters_spread.md: "The level lines stay identity until they are measured
as the p99 of each ink over bare interior paper. That measurement is still OPEN
on 8610". Every sister profile (8610, SH8602–SH8605, SH8608) ships `L* 0 100`.

**What I did.** Shipped identity levels like every issue before, ran the full
17-minute sweep, and found at Verification 6 that the paper graded to 236–248
instead of 255 on every window. Spent ~40 min and five measurement scripts
establishing why (tight pool, 4–7 levels of headroom, bare-paper ink p99 of
11/11/13/7 %), tried the W percentile first because the rule's W section is
long and its levels sentence is one line, and only then ran the p99 recipe —
which worked at once. Result: a second full sweep.

**What it cost.** ~1 h and a 17-minute sweep plus 005b and 010 repeated.

**Suggested.** Make the level measurement part of the three-page gate, before
the sweep: "After the gate pages are rendered, measure the p99 of C/M/Y/K over
three bare-paper patches of their `cmyk2400/NNN.tif`. If any ink's p99 is
above ~5 %, the paper will not clamp (SH8606: 11/11/13/7 % → paper 236–248);
set that ink's level low point to its p99 and re-render the gate pages. Check
the paper p50 reaches 255 AND glyph p50 stays within the sister issues' range
(SH8606: 38–43 after, 27–33 before)." And in the W section: "A W whose joint
clamp is already ~97 % does not fix grey paper — the levels do."

## 005 — Verification 7b fails a correct master at the field window's boundary

**What the rule says.** 7b: "every master names the FIELD that made it … or
the IDENTITY digest, which is what a page whose traced box the field could not
be anchored on must carry", re-deriving `anchored = field_box_ok(w, h)` from
the stamp's `page-size`.

**What I did.** p168's stamp says `page-size 209.3 x 301.0 mm` and `FIELD not
applied: … 301.0 mm is outside the 205-212 x 293-301 mm`: the step tested the
unrounded height (just over 301) and stamped identity. The check reads the
rounded 301.0, `field_box_ok` says anchored, and it asserts the master is
STALE. It is not; the step's own decision is in the stamp.

**What it cost.** ~5 min.

**Suggested.** 7b should trust the stamp's own `field` line ("NOT APPLIED")
over its re-derivation when the page-size is within 0.05 mm of a
`FIELD_PAGE_MM` bound — or the stamp should carry the unrounded size.

## 005 — a rule was fine and I was not: a fix's blast radius is a PAPER CLASS, not an artefact

**What the rule says.** r005_masters_sheet.md, *Two papers, two profiles*: the
`high` class is graded with the built-in anchors and identity levels; the
`low` class with the issue's measured `colors.txt`. Every stamp carries
`paper-class`.

**What I did.** After measuring the level lines into `colors.txt` I told
control that the re-sweep would refresh `sheets600` and `title_source_150.png`
and that *the owner's title crop therefore carries the grey paper*. The first
half is true (the files are rewritten); the second does not follow: the grey
paper was a `low`-class defect and the cover is `high` — its stamp reads
`paper-class high`, `profile (none -- the built-in anchors, identity levels)`,
`grade-sha cec3ff863b36`, and nothing in LC/LM/LY/LK reaches it. The re-sweep
rewrites the cover with identical pixels. Control caught it; the owner was
nearly asked to re-crop a title for nothing.

**What it cost.** One wrong sentence to the owner's channel; nothing re-done.

**Suggested.** In r005's *The stamp* section: "When a grade changes, say
which PAPER CLASS changed and check that the artefact you are worried about
is in that class — `grep paper-class <tmp>/masters600/NNN.stamp.txt` — before
telling anyone it is stale. A profile edit to `colors.txt` touches the `low`
class only; the wrapper and any card are untouched by it."

## 005 — Verification 3 re-measures skew on the GRADED master and reports the grade, not the geometry

**What the rule says.** Check 3: "RESIDUAL SKEW of the published masters is ~0
— re-measured, not trusted", `R.measure_skew()` on `masters600/NNN.png`
reduced ×4.

**What I did.** Ran it after both sweeps. p147 read +0.00° on the first pass
and +0.22° on the second — same scan, same traced edges (`L +0.00 R −0.21
T +0.02 B −0.24`), same page size 207.4 × 299.5 mm, same step log line
`skew +0.00 -> +0.00`; the only change between the passes was the level lines.
So the check read the grade's contrast change as a rotation. 004/072/115 at
±0.12° on both passes are the same thing at a smaller size.

**What it cost.** ~5 min, one grep of both logs.

**Suggested.** Say which artefact each check reads and what it can therefore
see: the STEP measures skew on the raw levelled sheet and asserts the
residual there; check 3 re-measures on the GRADED master, where a change of
grade changes the projection profile, so a non-zero reading means "look at
the step's own line for this page", not "the page is tilted". Compare against
the step's `skew a -> b` log line before calling a page tilted. (Same family as
7b: a check that reads a different artefact from the step it checks.)
