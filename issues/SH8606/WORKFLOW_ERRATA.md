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
