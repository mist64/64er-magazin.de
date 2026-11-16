# SH10 workflow errata

Kept from the first confusion onward (r000, r340). Each entry: what I needed, what the rule said, what it cost.

**Sign-off (step 340, 2026-11-16).** Under the squash-only order nothing under issues/SH10 is committed before the final squash, so r340 check 2 cannot be evidence (0 adds at sign-off -- verified); per the revised r340 the per-entry classification below is the primary record. The file was NOT committed early to make check 2 pass.

- `000 — The brief's "already verified" scan figures were the operator's ` -- LIVE (entry text, 2026-11-15) / LATER for its **Suggested.** line, added 2026-11-16 at 340
- `005 — No way to set a worker count of 1 on r005_field.py` -- LIVE (entry text, 2026-11-15) / LATER for its **Suggested.** line, added 2026-11-16 at 340
- `005 — r005_masters_sheet.md's thumb rule and the 2400/600 mix: no conf` -- LIVE (entry text, 2026-11-15) / LATER for its **Suggested.** line, added 2026-11-16 at 340
- `000 — The venv has neither tifffile nor skimage` -- LIVE (entry text, 2026-11-15) / LATER for its **Suggested.** line, added 2026-11-16 at 340
- `000 — A `pgrep -f` waiter matches itself` -- LIVE (entry text, 2026-11-15) / LATER for its **Suggested.** line, added 2026-11-16 at 340
- `150 — r150 has no shape for an uncut figure (step 150, ~17:00)` -- LIVE (entry text, 2026-11-15) / LATER for its **Suggested.** line, added 2026-11-16 at 340
- `150 — A split Bild series surfaced only at 160 (step 160, ~18:20)` -- LIVE (entry text, 2026-11-15) / LATER for its **Suggested.** line, added 2026-11-16 at 340
- `160 — An invented table row entered at WORKLIST time, not at typeset t` -- SAME SESSION
- `005 — The bed drop's reach into the page was unbounded (031, 163): fix` -- SAME SESSION
- `005 — A wrong traced TOP line on a page whose print runs to the scan e` -- SAME SESSION
- `000 — Renumbering pages: every NNN-keyed store, not only the raws (thu` -- SAME SESSION
- `005 — r005b's OVERRIDE guard and a master re-derive` -- SAME SESSION
- `006 — The colour gate cannot see a pale colour halftone (020): fixed m` -- SAME SESSION
- `006 — Step 5's own title template still said "Sonderheft NN/YY" for SH` -- SAME SESSION
- `006 — The mixed build writes its own log; the OCR cache inputs are mad` -- SAME SESSION
- `310 — A genuine printed lettered list has no stated replacement for `<` -- LIVE
- `320 — Brief Q5's "pages 020 labelled listing-standalone" names a BLOCK` -- LIVE
- `010 — A range given as one quoted argument OCRs nothing and exits 0` -- LIVE
- `340 — Check 2 cannot pass under the owner's no-commit-until-the-squash` -- LIVE

## 000 — The brief's "already verified" scan figures were the operator's prose (moved under the build)
The brief listed 000MISSING.txt's dpi split (4 wrapper + 19 singles @2400) as "already verified on disk -- do not re-derive". r000 says read each page's own pHYs and never assume. I followed r000, and pHYs says 25 @2400, not 23. Control ruled that the measurement wins and wrote a section into r000 the same day. Cost: none, because r000 was followed. It would have cost wrong numbers in LOG.md if the brief had been obeyed.

**Suggested.** r000: "A brief's 'already verified' is a claim like any other: the page's own pHYs decides; say so in the brief template." (LIVE)

## 005 — No way to set a worker count of 1 on r005_field.py
The owner's serial-image override (control, 10:00) asks to "set the worker count to 1 explicitly" where a step offers one. r005_field.py offers none: it calls r000_issue.lanes(lane_gb) and Pool(lanes), and neither reads an environment variable. Without editing tools/ (forbidden to the builder), the only way to run it serially was to wrap it: `python -c "import r000_issue; r000_issue.lanes=lambda *a,**k:1; runpy.run_path('r005_field.py', run_name='__main__')"`. The same applies to any later step that fans out through lanes(). What the rule should have: an override in lanes() itself (e.g. `LANES_MAX` in the environment) that every tool honours, so a machine-wide owner order is one export and not a per-tool wrapper. Cost: one grep, about 2 min.

AMENDED 12:37 (owner 11:08, via control, on measured rates): the serial order is revised, not replaced. The 2400 dpi pages stay serial (one page alone peaks ~19-21 GB and sets the issue's RAM peak); the 143 pages at 600 dpi run in 3 lanes (~2 GB each), and step 010 also runs in 3 lanes. Rates from the sweep's own mtimes: ~31 s per 600 dpi page, 5:21-8:37 per 2400 dpi page, so the 25 pages at 2400 are ~69% of a ~4 h serial sweep. For r005_masters_sheet.py the lane count is the `xargs -P` of the rule's fence, not LANES: the program has no pool. What the rule should have said: a mixed-dpi issue's lane count is per dpi stage (the 2400 stage bounds the RAM), not one number for the step.

**Suggested.** (applied by control mid-build: LANES honoured in r000_issue.lanes()). (LIVE)

## 005 — r005_masters_sheet.md's thumb rule and the 2400/600 mix: no confusion
Recorded only as a pass: the -scale 150/dpi recipe produced 168/168 thumbs within 1 px on a mixed issue.
   -> Fixed by control at ~10:20 (moved under the build): r000_issue.lanes() honours LANES from the environment. r010/r005_spread/r145 .sh now use LANES="${LANES:-...}". From here on every step runs as `LANES=1 OMP_NUM_THREADS=1 MAGICK_THREAD_LIMIT=1`. The r005_field run started 10:04 (pid 54848) is still on the monkey-patch.

**Suggested.** none -- a rule that held; keep it. (LIVE)

## 000 — The venv has neither tifffile nor skimage
numpy, scipy, cv2 and PIL are there; skimage and tifffile are not. `import tifffile` (a measuring snippet of mine, reading cmyk2400) raised ModuleNotFoundError: harmless, read via PIL / magick instead. A rule fence reaching for either needs another route. Cost: one failed call.

**Suggested.** r000's environment section: "the venv has numpy/scipy/cv2/PIL, not skimage/tifffile -- read TIFF via PIL or magick." (LIVE)

## 000 — A `pgrep -f` waiter matches itself
`until ! pgrep -f r005_masters_sheet; do sleep 3; done` never ends: the waiting shell's own command line contains the pattern. It cost 6 idle minutes on the critical path (12:39-12:45). Wait on an output file, or on a PID taken before the wait, never on a pattern that the waiter's own text carries. Builder's error, not the rule's.

**Suggested.** r000 conventions: "wait on a PID captured before the wait (`while kill -0 $pid`), never on `pgrep -f <pattern>` -- the waiting shell matches itself." (LIVE; and it recurred tonight: three such loops were still alive at 06:xx and had to be killed.)

## 150 — r150 has no shape for an uncut figure (step 150, ~17:00)
r000 says "every unplaced figure is a TODO"; r150 places only delivered PNGs and ~L720 implies TODOs exist. The sub-agent stopped rather than invent a placeholder that could ship. Control ruled: the worklist + placement plan is the only artefact; no HTML. What the rule should have said: exactly that, and where the plan lives. Cost: one stop and one ruling.
Also: r150 names no path for the worklist (SH09's <tmp>/crop_worklist.txt was followed), and its first-reference rule has no case for a series the print labels "Teil N" while the prose says "Plan N" (84-x1..x4: anchored at the first text naming the whole set).

**Suggested.** r150: "An uncut figure produces only the worklist row and the placement plan (<tmp>/crop_worklist.txt, <tmp>/r150/placement_plan.txt); never a placeholder in the HTML." (LIVE)

## 150 — A split Bild series surfaced only at 160 (step 160, ~18:20)
150's worklist excluded the typeset members of four series (10, 71, 101, 126); r160's "a numbered series is all typeset or all cropped" says the whole series goes on the worklist. The conflict was visible only once 160 had typeset them. Supplement of 8 (+2 for the TEDMON dumps) handed after the owner had started cutting. What r150 should say: apply r160's series rule WHEN WRITING the worklist.

**Suggested.** r150: "When writing the worklist, apply r160's series rule: a Bild series is all cropped or all typeset, so one cropped member puts the whole series on the list." (LIVE)

## 160 — An invented table row entered at WORKLIST time, not at typeset time (101 Bild 2)
What happened: after the owner's "typeset all ten" ruling I wrote the plan line "101-2 as a 3-column table with an explicit GND-tie row (Userport 1 & A, 12 & N -> Centronics 16, joined to 33 and 19..30)". r160b executed it faithfully and the HTML carried a spanning row that is nowhere in the print -- accurate electronics, still a fabrication. The owner found it on the served site. The drawing (a bracket, a dangling pin) cannot be carried by a 3-column table, which is what invited the gloss. What is true: the plate is a drawing; typeset as a drawing (<pre><code> with box-drawing, precedent 8701/170, SH8603/60, SH8607/6) it needs no explanation. Cost: one owner find on a published-looking page, ~30 min. Then I introduced the opposite error retypesetting it (`D0` for the printed letter `DO`) -- inherited from the old table, caught by control.
**Suggested.** r160: "A typeset plan names what is DRAWN or SET, never what it means. If a plan line contains a sentence that explains the figure, it is a gloss and does not ship; a figure a grid cannot carry is typeset as the drawing, not as a table plus prose." (SAME SESSION)

## 005 — The bed drop's reach into the page was unbounded (031, 163): fixed mid-build
r005_masters_sheet.py's doomed-component block deleted a whole bed-coloured component touching the frame if > BED_OUTSIDE_FRAC of it lay outside the trace -- at any depth. On 031 it whitened a slate panel 30.7 mm deep with its reversed text; on 163 it cut flame spikes into an olive field. The owner asked "why does the bed correction bleed so far into the page, EVER?". Control capped the reach (BED_REACH_MM, 5.0 then 0.5 after a fit-residual measure over all 168: 141 pages drop 0 px inside the line, 22 more only <= 0.34 mm jitter). Fixed mid-build because it shipped damage; the whole 005 re-derived twice (~3 h + 3 pages). Cost: ~5 h of wall-clock including my proxy measure, which measured depth from the page BOX, not the traced line, and so could not bound D.
**Suggested.** (applied: BED_REACH_MM 0.5, "validated on SH10 only; no extrapolated-corner wedge here"). And r005's check: "print lost = sheets600 ink where masters600 is fabricated white INSIDE the page box, with an 800x800 control window first; classify regions by depth from the edge." (SAME SESSION)

## 005 — A wrong traced TOP line on a page whose print runs to the scan edge (002)
002's ink/bed top line came out at -2.95 deg (the other three within 0.18); r005 painted the wedge outside it white as fabricated margin -- the top of "Profi" and the black ground. Not the bed drop: a straight wedge (25.8 px per 500 = tan 2.95). Repaired by reviewed/regrade_002.py (keep OR-ed with the box's top/left bands, bed check BEFORE the run). The seven pages whose boundary detection fails (001 002 008 022 023 031 163) are all 2400 dpi print-to-the-trim pages: there is no paper-to-bed transition to find. Control queued CQ15 (trace guard).
**Suggested.** r005: "A top/bottom line more than ~1 deg off the page's own skew, against a near-level opposite edge, is refused in favour of the scan edge" -- and until then: "a print-to-the-trim page is checked for print lost at its edges before it is accepted." (SAME SESSION)

## 000 — Renumbering pages: every NNN-keyed store, not only the raws (thumb150, a4win)
The owner's reorder (cards to the end) renamed /Volumes/S raws and their thumb/. tmp/thumb150 -- the descriptor's thumb_150, from which r005 measures skew and picks the edge finder -- was not renamed, so the six moved pages traced against the old page's thumb: new 163 lost 254 px of width, finders flipped, and NOTHING raised. Caught because each page's paper fraction followed its number (new 163 read old 163's 0.147). Then r005b's own cache (a4win/measured.json + NNN.npz) reused the bad-tail measurements: the cards unified to 3518 px instead of 3500, again silently. Fix: re-made thumbs (each equal to its mapped old one, mean |d| 0.0), moved the six cache entries aside. Cost: one extra 2400 dpi pass of six pages (~35 min) and one 005b re-run.
**Suggested.** r000: "A page renumbering reaches EVERY store keyed by page number, whether or not the descriptor names it: scan_dir, thumb_150, a4win (measured.json + NNN.npz), the PDF .ocrcache, ocr/out|truth|review, the marks panels, every reviewed/ override script and its record. Re-derive rather than permute; afterwards assert that each moved page's measurements follow its PIXELS (equal to its old mapped page), not its number." (SAME SESSION)

## 005 — r005b's OVERRIDE guard and a master re-derive
After re-deriving a master that already had an a4600 override (level_001), r005b over all pages stopped at 001: "carries an OVERRIDE ... RECUT_OVERRIDE=1 to proceed". It wrote nothing (verified). Right behaviour: moved the old a4600/001 aside (copy kept), re-cut 1/31/163 only, re-applied level_001. A RULE THAT SAVED ME -- it is what keeps an override from being silently reverted.
**Suggested.** r005b: one sentence beside the guard: "after re-deriving an overridden page's MASTER, move its old a4600 aside and re-cut that page alone, then re-apply its override script -- RECUT_OVERRIDE is for dropping the override, not for re-cutting under it." (SAME SESSION: written ~10:00, hours/half an hour after the event)

## 006 — The colour gate cannot see a pale colour halftone (020): fixed mid-build
The classifier (50 dpi, blur 1.5, chroma 12 %, erode) read p020's pale colour photograph as 0.00079 against a 0.002 cut; my preflight (chroma > 80) was blind the same way. The owner saw it in the trial. Per-pixel chroma >= 50 at 600 dpi separates cleanly (contone >= 0.0188, bilevel <= 0.00006, 020 0.0061); lowering the blurred cut instead fires on 162's cream window edge. Control added the dot-level column (classifier: colour if EITHER measure says so). Neutral grey screens (127, 136) are still invisible to it by design and ship contone only via FORCE_CONTONE.
**Suggested.** (applied in make_issue_pdf_mixed.sh). r006: "A forced page's contone class is the FORCE list's, not the classifier's -- report the two separately so 37 is never read as 'the classifier found 37'." (SAME SESSION)

## 006 — Step 5's own title template still said "Sonderheft NN/YY" for SH09+: fixed by control
I built with the tag "Sonderheft 10/86" from r006's Run block; r006's prose (owner, 2026-11-14) says "Sonderheft N" from SH09, no year. Caught at step 5's Verification by reading the table, stamped with exiftool (incremental). r006's -Author also wrote a non-standard XMP pdf:Author no other issue has (removed with -XMP-pdf:Author=; streams sha-identical). Control fixed all three command sites and the -Author.
**Suggested.** (applied). r006: "When an owner correction changes a value the rule also shows in a COMMAND, grep the old value across every fence." (SAME SESSION)

## 006 — The mixed build writes its own log; the OCR cache inputs are made by hand
Run with `>> build.log`, the mixed build exited 1 in one second with an empty log: it redirects itself to <output>.build.log (line 126). There it said exactly what was missing (the 8 pruned pages' NNN.pdf/_150.png, "this script never makes them", with the commands), and then that page 1's cache did not carry title.png. Both refusals were right and saved a wrong PDF. Cost: ~10 min of looking in the wrong log.
**Suggested.** r006 Run: "The mixed build's output goes to <output>.build.log, not to your redirect -- read that file; a pipeline exit code says nothing." (SAME SESSION: written ~10:00, hours/half an hour after the event)

## 310 — A genuine printed lettered list has no stated replacement for `<ol type="a">`
r060 calls `<ol type="a">` a bug signature (eaten initials, OCR'd 1.) and r310 makes it HARD, but 28's two lists are real `a) … b)` lists, intact. Corpus form, counted: `<p>a) …</p>` 41x in 26 chain-built files (control: 123 vs 4 corpus-wide), never as `<li>`. Cost: one corpus count.
**Suggested.** r060/r310: "A genuine printed lettered list is set as one `<p>a) …</p>` per item, as printed -- never `<ol type>`." (LIVE)

## 320 — Brief Q5's "pages 020 labelled listing-standalone" names a BLOCK label as a page kind
My first Q5(b) selector keyed page_kind == listing-standalone and found 0 pages -- a hollow answer of the kind r320 warns about. listing-standalone is a block label; the p116 failure shape is an article page whose kept `order` is empty. Re-run on that: 12 pages, only p116 carries prose (in the HTML). Also: Q4 and Q5(b) stayed open from the brief's writing to step 320 (~a day) because nothing tracked them. Cost: two passes.
**Suggested.** r320: "The listing-standalone check is over article/mixed pages whose 020 `order` is EMPTY (every block taken for listing), not over a page kind; a selector that matches no page is a check that did not run -- report its population first." (LIVE)

## 010 — A range given as one quoted argument OCRs nothing and exits 0
`r010_ocr_blocks.sh "163 168"` (my quoting) printed `seq: invalid floating point argument: 163 168`, OCR'd nothing, rebuilt the blocks index without those pages, and exited 0. Caught by counting the outputs. Builder's error; the script let it pass.
**Suggested.** r010_ocr_blocks.sh: "validate the range (two integers) and exit non-zero otherwise." (LIVE)

## 340 — Check 2 cannot pass under the owner's no-commit-until-the-squash order
r340 check 2 wants the errata file's first commit before the issue's last. Under the standing order "one squashed commit at the end, permission asked every time" nothing of SH10 is committed during the build, so the file is untracked until the squash and check 2 WARNs by construction. The entries above carry LIVE / SAME SESSION / LATER instead (check 2b's categories). Also: the first seven entries were written as "## 1." etc., which check 3 cannot read; re-headed with their steps at 340.
**Suggested.** r340 check 2: "Under the squash-only order, check 2 is not evidence; mark each entry LIVE / SAME SESSION / LATER instead, and head every entry `## NNN —`." (LIVE)
