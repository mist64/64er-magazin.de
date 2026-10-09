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

## 140 (and every Verification block) — a bash loop over `$SLUGS` passes silently under zsh

**What the rule says.** r140 check 4: `SLUGS="impressum checksummer vorwort
mse"` … `for slug in $SLUGS; do … done`, inside a fenced ```bash block. Every
rule's Verification is "runnable as shell" (r000).

**What happened.** The 140 sub-agent ran the block in this machine's default
shell, zsh, where `for slug in $SLUGS` does not word-split: the loop ran once
over the whole string, `prev` came back empty, the test short-circuited and
check 4 printed nothing — the silent pass in the safe direction that r140's
own text warns about for an empty PREV. Re-run under `bash`, it reported the
four slugs correctly, and a planted rename of `impressum` was caught. This
session's own shell is zsh too, so any Verification block that word-splits a
variable (`$PAGES`, `$SLUGS`, `set -- $ISS`) has the same hole unless run
through `bash`.

**What it cost.** One re-run; the agent noticed because `prev=NONE` looked
wrong.

**Suggested.** In r000 *Verification rules mandatory*: "The blocks are bash.
Run them with `bash <<'EOF' … EOF` (or `bash -c`), never pasted into an
interactive zsh: zsh does not word-split `$VAR` in `for x in $VAR`, so a loop
over a space-separated list runs once and reports nothing." And quote the
list literally where the rule can (`for slug in impressum checksummer …`).

## 120 — check 4 reads the `.txt` as UTF-8 while generate.py tokenises it as latin-1

**What the rule says.** Verification check 4: `listing = open(…, encoding="utf-8",
errors="replace").read()` … `petcat … input=listing.encode()`; and the same
rule's *A `.txt` IS BYTES* section: "`generate.py` reads the listing and pipes
it to petcat as **latin-1** rather than UTF-8", citing `der kl. hobbit`'s `$A0`
after REM as a byte that only a raw latin-1 byte can express.

**What happened.** The 120 sub-agent ran check 4 both ways on SH8606 (same
result here, 32/19, because apfel_bas's `$CD` could be expressed in petcat's
own text convention) and noted that a `.txt` carrying a raw byte ≥ $80 — the
exact fix the rule prescribes for the Hobbit — cannot pass check 4 as written:
`errors="replace"` turns the byte into U+FFFD and `.encode()` emits three UTF-8
bytes. The check contradicts the remediation it sits beside.

**What it cost.** Nothing on this issue; it is a trap for the next one with a
`$A0` REM banner.

**Suggested.** Check 4 opens and encodes the listing as `latin-1`, exactly as
`generate.py:petcat2prg` does, "so a pass here is a pass on the site" (the
rule's own words two lines above the code).

## r170 — a whole-listing crop that is still on the worklist has no deferred state

r170's *An unreadable PETSCII glyph is never guessed* sends the listing to r150's crop worklist, and the crop arrives only at PAUSE 2 — but r170's Verification check 1 ("no `<pre>TODO</pre>` left") and check 3 ("empty Listing pre") fail on the placeholder in the meantime, with no wording that says this is the expected state. r200 has exactly this clause for its banner ("A BANNER NOT CUT YET IS NOT A FAILURE — it is PAUSE 2 work … DEFERRED to after PAUSE 2"). On SH8606 it is Grafik 2000's Listing 2 (p120, screen printout with reverse-video glyphs, no checksums): the placeholder stays, the checks report it on every run until the owner delivers `114-l2.png`.

**Suggested.** Add to r170's Verification, after check 3: *A `<pre>TODO</pre>` whose figure is on r150's crop worklist (a whole-listing crop, named `<page>-lN.png`) is DEFERRED to after PAUSE 2, like r200's banner; list it by name in LOG.md and re-run checks 1 and 3 once the crop is placed.* And name the crop file convention (`<article-page>-l<N>.png`, as SH8602's `20-l6.png`) in the PETSCII section, so the worklist entry is written the same way every time.

## r240 — the Sonderheft evidence line is stale: the 1986 Vorworte DO carry a `3-0.png`

r240's *Applies to* says "zero `<page>-0.png` on any Editorial/Vorwort … across `SH8501`–`SH8508`" and *Sonderhefte: there is no rubric banner* repeats that the Vorwort "holds no image at all". MEASURED: `issues/SH8602/3-0.png`, `SH8603/3-0.png`, `SH8604/3-0.png`, `SH8605/3-0.png` all exist (≈353x502 each) and are placed `<figure><img src="3-0.png" alt="Titelseite eines 64'er-Sonderhefts »…«: …">` directly after the `<h1>` — reproductions of the issue's own cover, set between the Vorwort's columns. SH8606's p3 prints the same thing and the owner delivered `3-0.png` for it. The step-150 agent had to establish the precedent by grepping the corpus because r240's text pointed the other way (toward the monthlies' `<img class="inline">` portrait), and the orchestrator's brief (mine) called it a "portrait" on the strength of r240's sentence.

The conclusion (r240 is `not applicable — kind`) still holds: the cover reproduction is an ordinary figure that r150 places, not a rubric banner.

**Suggested.** Replace the evidence line with the measured one: *"A 1986 Sonderheft's Vorwort carries a reproduction of the issue's own cover as `3-0.png` (SH8602–SH8606), placed by r150 as `<figure><img>` after the `<h1>` with a »Titelseite …« alt — it is not the monthlies' editor portrait and not this rule's banner."* And add the same sentence to r150's title-image section so the next build does not have to rediscover the shape.

## r210 — the apply script's size gates reject every band of this issue, and it writes caps verbatim

`r210_head_meta_apply.py` run dry on SH8606 (`total=27 to_fill=6 skipped=1 flagged=26`): it found a head1 on 6 of 27 start pages and NO head2 anywhere, although all 26 interior start pages carry a legible black running-head bar. MEASURED on the step-010 header blocks: the `GRAFIK-ERWEITERUNG` blocks are 1730–1856 px wide (the script's `HEADER_W_MAX` is 1600), a one-line combined band is 4244–4252 px, and the `C64` blocks on the start pages are 218–246 px tall (`HEADER_H_MAX` 200) because step 010 boxes the whole bar, glyphs and ground. The six words it did read it would have written in CAPS (`EINGABEHILFEN`, `HARDCOPY`) and with the machine name closed (`C64`), both against this rule's own text; and `vorwort` is not in its `SKIP_IDS`, so the front matter is treated like a body article. The values had to be read off 27 band crops by hand (<tmp>/scratch_210/heads.md), which is what the rule's "vision-only" path already describes — so nothing was lost, but the script is not a shortcut on a Sonderheft whose bar is a filled black band.

**Suggested.** Either raise the gates to what a filled bar measures (block height ≤ 260 px, width unbounded when the block sits in the top 4 % of the page) and normalise the output (caps → German capitalisation, `C64` → `C 64`), or say in the rule that the script is calibrated for the monthlies' thin two-line heads and that a Sonderheft with a black bar goes the crop route from the start.

## r006 — the repo copy of the PDF vanished again (second occurrence after SH8604); timeline

Control (2026-10-09, ~07:40) reports `issues/SH8606/64er_Sonderheft_1986-06.pdf` gone while the `<tmp>` copy (`/Users/mist/DNB/SH8606/tmp/64er_Sonderheft_1986-06.pdf`, mtime 2026-10-09 03:33, sha256 `780eaa1c…`) survives. What this session knows, with timestamps:

- 03:33 the mixed build wrote the PDF into `<tmp>`; it was copied into `issues/SH8606/` right after and opened for the owner (uncommitted by design).
- The copy was still there at **≈04:00–04:05**: the step-170 sub-agent's `git status` (quoted in its hand-back) and my own `git status --short -- issues/SH8606` before the 150/170 commit (04:24) both list `?? issues/SH8606/64er_Sonderheft_1986-06.pdf`; the step-150 sub-agent (finished ≈03:55) also saw "only the untracked PDF" in `git status`.
- From the 150/170 commit onward every status check in this session was piped through `grep -v pdf`, so the next evidence is negative: the step-210 band reader (ran ≈05:05–05:10) reported WORKFLOW_ERRATA.md as the only non-SH8608 modification in `git status`, which means the untracked PDF was **already gone by ≈05:10**. Window: 04:05–05:10.
- What this session did to `issues/SH8606/` in that window: `git add -- <pathspec>` / `git commit -- <pathspec>` at 04:24, 04:53, 04:55 (never `-A`, never clean/checkout/stash/reset); `r150_figure_captions.py --write` (writes figure_captions.txt only); my apply170.py (rewrites three HTML files); js-beautify on HTML files by the 160/180/190 passes; creation of `reviewed/dup-passages.txt`. Sub-agents 160 (04:10–04:50) and 190 (04:55–05:19) were briefed "no git commands that change state" and reported only read-only `git diff --stat`/`git status`. Nothing in the session addressed the `.pdf` path. The sibling build (SH8608) shares the tree.

**Suggested.** r006 should say that the delivered copy in `issues/<ID>/` is not durable between sessions on this shared tree and must be re-copied from `<tmp>` (whose copy is the one verified) before the owner is pointed at it — and every status check in a build log should print the PDF line unfiltered, so the next disappearance gets a timestamp instead of a window.

## r300 — the Verification's per-file loop hangs in this environment

The trailer check runs `grep -rl --null 'class="fehlerteufelchen"' "$dir"/*.html | while IFS= read -r -d '' f; do …; done`, with a comment that `--null` (not `-Z`) is what makes it work under ugrep. MEASURED on SH8606: in this build's shell `grep` is a shell function the harness defines, which execs its own ugrep build (`ugrep 7.8.4`) with `--null` passed through — and the output is **newline-separated, no NUL byte** (`… | od -c` shows plain `\n`). So `read -d ''` never sees a terminator, the loop blocks forever, and the whole Verification block was moved to the background by the 120 s timeout with nothing after line 13 executed. The checks were re-done by hand (one aside, two trailers in issue order, one status comment, four links, no self-link, no placeholder, aside last before `</article>`).

**Suggested.** Drop the NUL pipeline: `for f in "$dir"/*.html; do grep -q 'class="fehlerteufelchen"' "$f" || continue; $PY - "$f" <<'PYEOF' … PYEOF; done` needs no `-Z`/`--null` at all and is immune to which grep answers. The same `--null`-with-ugrep pattern should be grepped for across the other rules' Verification blocks.

## r300 — "EVERY PRINT/DISK DIFFERENCE IS AN OWNER DECISION" is over-broad; it escalated three house-style cases

The sentence predates two owner rulings this build already works under (print errors stay as printed unless a reprint lacks its original's erratum; an unimportant listing/disk difference gets a German HTML comment) and it ignores the repo's own precedents: 12 `<!-- Disk-Version bereits korrigiert -->` and 8 `<!-- Korrektur im Programm angewendet -->` sites, each with a matching `;inkl. Fehlerteufelchen M/YYYY (Zeilen …)` header note in `prg/*.txt` (e.g. `issues/8604/prg/autochange.txt:3`, `issues/8410/prg/Zinseszinsrechnu.txt:92`). MEASURED on SH8606: the sentence sent three items up as PAUSE 2 owner-list entries — the 10/86 MPS 802 correction (disk still pre-erratum → patch with the commented original above, house shape), the `listing 2`/`listing 4` header notes (disk already corrected → `Disk-Version bereits korrigiert`), and the optional loader line 65 (erratum says "nur erforderlich, wenn …" → header note, no patch, no status comment). Control ruled all three from the repo in one message (2026-10-09, after the resume); none needed the owner, and the 10/86 block sat without its status comment through the pause because of it.

**Suggested.** State the defaults in r300: (a) disk already carries every corrected line → `Disk-Version bereits korrigiert` + the `;inkl.` header note, after checking EACH line the erratum names; (b) disk still pre-erratum → apply in the house shape (`;vor Fehlerteufelchen M/YYYY` / `;<old line>` / corrected line) + `Korrektur im Programm angewendet` + header note, touching ONLY the lines the erratum names (the same `sys` arguments recur in other paths of the same file); (c) an erratum line the magazine itself calls conditional → header note only. Escalate only a difference that changes what the program does and has no erratum to lean on.
