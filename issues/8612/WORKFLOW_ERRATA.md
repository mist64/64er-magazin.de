# 8612 — workflow errata

Kept from the first confusion onward (r340). Each entry: what the rule says, what
I did with it, what is true, what it cost, the sentence that would have prevented it.

## 000 — r000 and r340 disagree on whether the builder edits a rule mid-build

- **What the rules say.** r000 *THE FILES ARE THE DELIVERABLE*: "Write the rule
  BEFORE you send the correction"; *THE SCAN IS THE ONLY INPUT*: "Then fix the
  rule, in the same change as the work." r340 *Lessons*: "**Do not fix the rule
  yourself mid-build.** Record it and carry on."
- **What I did.** Read both in the first ten minutes and could not tell which
  applies to me, the issue orchestrator, as opposed to the supervising session.
  Decided: I record here and leave rule edits to `64er_control` unless a rule
  is actively dangerous (r340's own exception).
- **Cost.** ~2 min of rereading; no wrong action yet.
- **What would have prevented it.** r000 should say *who*: "The SUPERVISOR
  edits the rules (the fix goes in the `.md` first, then the pointer to the
  runner). The RUNNER does not; it records in WORKFLOW_ERRATA.md and carries on
  — except for a fossil path or a dangerous instruction, which it fixes in the
  same change as the work."

## 000/005 — PAUSE 1 asks "which pages are which paper", but a spread issue cannot use the answer

- **What the rules say.** r000 *PAUSE 1*: "binding, and which pages are which
  paper ... 005 grades nothing until they are." r005_masters_spread *This
  variant takes ONE profile*: "A spread descriptor that carries `paper` with
  `high_pages` is not honoured — every page is graded with the single profile,
  silently ... a spread issue uses the legacy whole-issue `colors` key".
- **What I did.** Prepared to ask the owner the paper question, then found in
  r005_masters_spread that for a spread the answer is fixed by decision (8610,
  8611: all pages low, wrapper slightly grey). So the question is still asked,
  but as "confirm the 8610/8611 decision", not as an open choice.
- **Cost.** ~3 min.
- **What would have prevented it.** r000's PAUSE 1 table should carry one
  line: "For `binding: spread` the paper answer is fixed until the spread
  variant learns per-page classes: one measured profile under the legacy
  `colors` key, wrapper graded with the interior (decided 2026-09-27). Ask the
  owner only to confirm that."

## 340 — "committed; it is the whole point", but `.gitignore` ignores it

- **What the rule says.** r340 table: "`WORKFLOW_ERRATA.md` | these rules |
  committed; it is the whole point". Verification 2 checks its first commit.
- **What is true.** `.gitignore:30` `issues/*/*` ignores every file directly in
  an issue dir, and the re-include list (`*.html *.png *.svg *.txt *.pdf prg/
  REPRINTS.md issue.json`) has no `WORKFLOW_ERRATA.md`.
  `git check-ignore -v issues/8612/WORKFLOW_ERRATA.md` → `.gitignore:30`.
  `git ls-files 'issues/*/WORKFLOW_ERRATA.md'` → empty: no issue has ever
  committed one, so r340's Verification 2 has never been able to pass.
- **What I did.** Noticed on the first `check-ignore` after creating it. Will
  commit with `git add -f` unless told otherwise; flagged to 64er_control.
- **Cost.** 1 min, 2 commands. Would have been silent: a plain `git add` of
  an ignored path prints a hint and stages nothing.
- **What would have prevented it.** `.gitignore`: `!issues/*/WORKFLOW_ERRATA.md`
  beside `!issues/*/REPRINTS.md`, with the same one-line reason.

## Resolutions (by 64er_control)

- 340/.gitignore: fixed in 21c24724 (`!issues/*/WORKFLOW_ERRATA.md`); verified
  with `git check-ignore` — errata visible, LOG.md still ignored.
- 000 vs 340 on rule edits: r000 now says it outright. With an orchestrator
  present, the runner records and the orchestrator edits.

## 000 — "every thumb exactly 1/16 of its own master's width" is not exact

- **What the rule says.** r000 *A thumb/ you FIND*: "every thumb exactly 1/16
  of its own master's width -- per page".
- **What I did.** I checked with ceil(w/16) and got 9 "mismatches" in the first
  ten pages (001: 20485 px → 1280, not 1281). Masters are not multiples of 16.
  `-scale 6.25%` rounds to nearest. Rechecked as |thumb − master/16| < 1 on
  both axes: 0 of 200 mismatched. Also AE = 0 against the found thumbs on p002,
  p100, p199.
- **Cost.** ~3 min, 2 commands.
- **What would have prevented it.** "every thumb's width and height within
  1 px of its master's / 16 (masters are not multiples of 16; magick rounds)".
- Harvest policy (owner, df96514e): this file is applied only once the issue
  is complete and 340 is closed. The exception is a blocking defect, which is
  fixed mid-build and recorded here as such. Mid-build rule changes so far:
  21c24724 (.gitignore, blocking for r340's commit) and df96514e (this policy).
  r000's text on rule edits also changed with 21c24724, at setup, before step
  005 ran.

## 005 — the clip re-measure procedure runs `measure` twice when the candidates are already stored

- **What the rule says.** r005_masters_spread, *The tell*: "1. Run `measure`
  with `HOLE_TEMPLATE_Y0_TOL_MM` widened enough not to bind (20 mm) ... Then
  re-run the sample and confirm the hole count reaches 6".
- **What I did.** Step 0 (gaps relative to hole 1) needed no re-measure. Every
  page's `holes` list in geometry/NNN.json is the full candidate set, so I
  associated the candidates to an approximate template directly and read off
  the spacing and shift. I confirmed the new clip by replaying `fit_fold` over
  the stored candidates, which the rule's own *Notes* say is a pure function of
  them. This saved two sample re-measures of ~17 min each.
- **Rule that saved me.** Step 0 itself. Without it I would have widened the
  tolerance first; with it the cause was visible in one table.
- **What would have prevented the detour.** Replace 1-3 with: "Read the
  candidates from the sample's geometry/*.json (no re-measure needed), take
  the six per page nearest a rough template, and average. Confirm by replaying
  `fit_fold` over the stored candidates with the new `clip` in the descriptor."

## 005 — the gate snippet reads masters600, which needs a `cut` the rule does not mention

- **What the rule says.** *The gate*: the snippet opens `R.OUT_MASTER / f"{stem}.png"`.
  *Two phases*: `cut` "is re-run alone after ... any `measure`".
- **What I did.** I noticed masters600 was empty after the sample `measure` and
  ran `cut` over the 25 sample pages. It fits over whatever geometry is present
  (an indicative 9-10 page fit per parity). The sweep's wipe-and-cut supersedes it.
- **Cost.** 1 min.
- **What would have prevented it.** Put "run `cut` after the sample `measure`.
  The gate reads the master, and the sample fit is throwaway" before the snippet.

## 005 — the `colors` path: the rule's example is relative, every descriptor is absolute

- **What the rule says.** r005_masters_spread line ~102: `"colors": "issues/<ID>/colors.txt"`.
- **What is true.** `git show HEAD:issues/8611/issue.json` and 8610's both carry the
  ABSOLUTE path `/Users/mist/Documents/git/64er-magazin.de/issues/<ID>/colors.txt`,
  and so does 8612's (copied from 8611). 64er_control thought 8611 was relative;
  it is not. The disagreement is between the rule's example and every real
  descriptor, not between issues. Whether r000_issue resolves a relative path
  against the repo root or the cwd (steps run from rules/) I did not test.
- **Cost.** 1 min.
- **What would have prevented it.** State in r000_issue's docstring which form is
  intended and how a relative one resolves, and make r005's example match.

## 005 — skew is measured on the TYPE, so an ad with tilted artwork is rotated to the art

- **What the rule says.** r005_masters_spread *Skew and grade*: "The skew is measured on
  the thumb, applied to the 2400 dpi scan, and re-measured ... a residual still over it
  after that is NOTED and the page publishes anyway." r005_masters.py: the crop
  excludes the sheet edges "to measure ... the type angle" rather than the guillotine.
- **What happened.** p183's art is printed ~6.6° tilted. The ±3° coarse sweep clamped at
  −3.3, and the second pass added the residual: −6.60 applied. The NOTE says only
  "SKEW still −0.26 deg". Nothing flags that the applied angle is twice the sweep's own
  range. p117 (−1.72) and p140 (+2.02) are the same class inside the range, and they
  carry NO note at all. Found only by looking at the four no-fold/no-logo masters.
- **Cost.** ~10 min, 6 commands, plus an owner decision at PAUSE 2.
- **What would have prevented it.** (a) Verification check 5 or 8 should list pages
  with |skew.angle| > 1° as LOOK AT, since a clipped sheet is rarely more than ~1°
  off and every case here was art. (b) The re-level pass should refuse a total angle
  outside SKEW_COARSE and NOTE it. (c) The rule should say what to do with an
  art-tilted page; it has no per-page override today.

## 030 — the verification block says `python3`, the trap r000 already names

- **What the rule says.** r030 *Verification*: `python3 - <<'PY'  import r030_assemble as A`.
  r000 *THE PAGE IMAGE IS masters600* warns that bare `python3` has no numpy and
  "makes SRC silently EMPTY".
- **What I did.** Ran it with `.venv/bin/python` from the start, because r000 warned me.
  (The rule saved me.)
- **What would have prevented it.** Replace `python3` with `$PY` (= `.venv/bin/python`)
  in r030's three snippets, as r010 and r020 already do.

## 030 — `FORTSETZUNG` regex has no tolerance for one OCR slip

- **What is true.** On 8612 p042 the marker reads "Fortsetzung aug Seite 195". The regex
  `Fortsetzung\s+(auf|von)\s+Seite\s+(\d+)` misses it, the continuation strands, and the
  only signal is one "has no article to rejoin" line in a 12-minute log.
- **What would have prevented it.** Either `(a\w{1,2}|von)` in the regex, or r030's
  Verification should list every stranded continuation as a LOOK AT with its
  `Fortsetzung` block text from both pages, so the orchestrator sees OCR versus print
  asymmetry in one command (it took me 3 commands).

## 030/040 — nothing says to copy <tmp>/ocr/<ID>.md to issues/<ID>/<ID>.md

- **What the rules say.** r030: "`<YYMM>.md` ... <- the handover to step 040", and
  `ISSUE_MD` "points into the issue's working directory, not into the repo". r040's
  verification and usage operate on `issues/<YYMM>/<YYMM>.md`.
- **What I did.** Found the copy only in issues/8611/LOG.md ("re-copied from
  <tmp>/ocr/8611.md").
- **Cost.** 2 min, 2 commands.
- **What would have prevented it.** r030 *Outputs*: "Then `cp <tmp>/ocr/<ID>.md
  issues/<ID>/<ID>.md`. That copy is what 040 onward edit. It is not committed
  (`.md` is ignored); 060 commits the HTML."

## 040 — "length 2 is always bold" is false, and no check sees an unpaired `**`

- **What the rule says.** "**length == 2** → keep (it's a `**bold**` delimiter)." The
  Verification's `**bold** pairs` is "a sanity readout".
- **What is true.** 8612's Protext article shows space padding as `*`:
  "Der**Mann*schläft." / "Der*Mann**schläft." Each line has one literal `**`, kept as
  "bold" (sub-agent found it; I confirmed). The fence-aware checks all read 0.
- **Also found by the sub-agent.** The script's own printout is not fence-aware
  (`solitary=2` on correct output). The Rule section has no fence exception; it lives only
  in the .sh comment.
- **Cost.** ~3 min orchestrator time, plus the sub-agent's.
- **What would have prevented it.** Add a check that lists lines with an odd number
  of `**` outside fences (an unpaired delimiter is a literal), and change the rule
  to "length 2 → keep IF it pairs within the paragraph; else escape".

## 050 — "`<`+non-letter is browser-safe" is false for `</`

- **What the rule says.** "Patterns that already start with a non-letter (e.g. `< CBM >`,
  `<10`, `<\*>`) won't be matched and stay as-is — they're already browser-safe because
  HTML requires a letter immediately after `<` for a tag."
- **What is true** (sub-agent found it; I confirmed). For `</` the HTML5 tokenizer drops
  `</>` entirely and treats `</`+non-letter as a bogus comment that eats text to the next
  `>`. 8612 l.2903 "durch </> dargestellt" would have lost the `</>`.
- **Also.** The "Idempotent: lookbehinds for `\`" sentence describes a script that no
  longer exists. Idempotency comes from writing entities. The script's own count is not
  fence-aware. The prose whitelist lists `big`, the code does not.
- **What would have prevented it.** "…browser-safe — EXCEPT `</` followed by a
  non-letter (`</>`, `</1>`), which the HTML tokenizer swallows; escape those too."
  Plus a check: `re.findall(r'</[^A-Za-z]', outside_fences)` must be empty.

## 070 — the script `git add`s silently, and it is not idempotent on `'’`

- **What the rule says.** "In-place rewrite, idempotent (re-running on a cleaned file is a
  no-op)." Nothing about staging.
- **What is true** (sub-agent found both; I confirmed the first by reading the script).
  - `r070_html_cleanup.sh` ends `git add "$1" 2>/dev/null || true`. r000 warns that
    self-staging scripts plus a shared index have swept files into the wrong commit three
    times, but r000's list of self-staging scripts (060, 080, 100) omits 070.
  - `''` → `"` runs before the curly folding, so `TEDMON'’s` became `TEDMON''s`, and a
    second run would make it `TEDMON"s`. Also, `''` → `"` is wrong for a math double prime
    (`P''`, 8612 L2577), which survived only by that ordering accident.
- **Cost.** ~3 min orchestrator time.
- **What would have prevented it.** Add 070 to r000's list of self-staging scripts (or
  drop the line). Fold curly quotes FIRST, then `''`. Say whether `''` can be legitimate
  (a prime/double prime in a formula is).

## 080 — no rule for joining a continuation: where its text goes, and the "Fortsetzung" lines

- **What the rule says.** Nothing. r030 strands a continuation when the marker is OCR'd or
  one-sided, and r080 never mentions continuations.
- **What happened.** The sub-agent (briefed by me) decided both from precedent: drop the printed
  "Fortsetzung von/auf Seite N" lines (git grep finds none kept in 85xx/86xx), and splice the jump's
  text where the jump line was (reading order), not at the end of the file.
- **What would have prevented it.** r080: "A `[Fortsetzung von Seite N]` section from 030 is
  joined to its host at the host's `Fortsetzung auf Seite M` line (reading order), the printed
  Fortsetzung lines are dropped, and the host's page spec gains M."
- Also (sub-agent): Verification 2's `tr '?/:' '_'` does not mirror the script's sanitiser
  (`<>:"/\|?*+`), and the rule's prose says only `? / :` are sanitised.

## 110 — "The Vorschau is the 5th-from-last page" is false on 8612

- **What the rule says.** "The Vorschau is the **5th-from-last page** of a monthly (188 of 192
  on 8611, 196 of 200 on 8610)".
- **What is true.** 8612 has 200 pages and its Vorschau is p194, 7th from last. Found by the
  sub-agent; I confirmed on the banner crop. The fallback the rule names (`toc_entries.txt`)
  does not exist at 110, because 090 runs at the same time or produces it later.
- **Also.** Whether an agent may write the DERIVED next-issue bullet before the operator confirms
  it is stated both ways ("the OPERATOR's to give. Do not invent one" vs "derived, not
  chosen").
- **What would have prevented it.** "The Vorschau is the page whose banner reads VORSCHAU 64'er
  — near the end, 5th-7th from last; find it in the 080 file list (`NNN Vorschau.html`). Write
  the derived next-issue bullet and list it for the owner's confirmation at PAUSE 2."

## 100 — the toc_title helper reads a file 090 no longer writes; the editorial sentence contradicts the corpus

- **Sub-agent's findings, confirmed by me from its output.**
  - `r100_toc_title_apply.py` expects `issues/<ID>/_tmp/toc_entries.json`. 090 writes
    `toc_entries.txt` (TSV), and the helper's SECTION_TO_TOC_CATEGORY lacks Einsteiger-Teil, Hardware
    and Software-Hilfen.
  - The rule says "If this issue's TOC files its opening piece under a heading, that heading is its
    category", but 8608-8611 all ship the editorial with `""` although their TOCs list it under
    Rubriken.
  - The script stages with `git add -u issues/<ID>`, which stages EVERY tracked modification in the
    directory (here WORKFLOW_ERRATA.md), not just "each rewritten file".
- **What would have prevented it.** Point the helper at toc_entries.txt (or retire it and say so).
  Restrict the opening-piece sentence to Sonderhefte. Stage by explicit file list.

## 120 — the sub-agent found four gaps; recorded as found

- "`NN` is the article's start page" is false for 54/57/78 on 8612. Those are listing pages
  inside 51, 52 and 74, and they resolve only through `64er.pages`.
- No path for BASIC at a load address not ending in 01 (find c128 at $242B). The extractor
  routes it to PRG and petcat produces garbage. The relink-to-$1C01 workaround is the sub-agent's.
- The stub test (`< 3 content lines`, "last statement is a bare SYS") misses a stub whose
  SYS is the FIRST statement with CR-bearing tail text (4gewinnt meister). Only check 4 caught it.
- No path for a line-linked plain-ASCII assembler source (hyperscreen ii.s). Neither
  data-assembler branch decodes it.
- The re-decode recipe leaves `;del/<n>.prg` and leading blank lines, which 8611's files do not have.
- **What would have prevented these.** One sentence each in r120 (above). Plus: "a separator
  NN is the PAGE the listings sit on; map it through 64er.pages, not filenames".

## 130 — fossil paths in Inputs (r000's fossil table misses r130)

- **What the rule says.** r130 *Inputs*: "`issues/<YYMM>/64er_*.pdf` — for verbatim captions" and
  "The page-scan PNGs under `issues/<YYMM>/png/`".
- **What is true.** Neither exists during a build (the PDF is made at 006, after PAUSE 2; there is no
  png/). r000's *THE PAGE IMAGE IS masters600* names the right source, and r000's fossil table lists
  r150/r160/r300/r330 but not r130. Also `/tmp/64er_<YYMM>_full.txt` is a /tmp path (r000: never /tmp).
- **Cost.** 1 min; I briefed the sub-agent with <tmp>/masters600 and the block index instead.
- **What would have prevented it.** Add r130 to the fossil table, and replace both lines with
  `<tmp>/masters600/NNN.png` and `<OUT_DIR>/blocks/pNNN.txt` / `NNN.labels.json`.

## 000/145 — a DISABLED step has no disposition in r000's vocabulary, and is missing from the chain table

- **What the rules say.** r000: "every number in the chain has exactly one `LOG.md` disposition:
  ran-and-verified, or `not applicable — kind`". r000's chain table has no 145, yet r000's lanes
  section and THE PAGE IMAGE section speak of "145 figure extraction" / "r145 cuts figures from".
  r145 itself opens "DISABLED — 2026-08-22. Do not run this step."
- **What I did.** Logged "not run: DISABLED (rule header)", which is a third disposition r000 does not admit.
- **What would have prevented it.** Add 145 to r000's chain table marked DISABLED, and admit
  "not run — disabled" as a disposition (or drop 145 from the lanes text).

## 160 — Pass 3 "mechanical, NOT a visual scan" in the Briefing contradicts the normative "the VISUAL WALK is the mechanism"

- Found by the 100-195 sub-agent. On 8612 the walk found all six uncaptioned tables and the sweeps found none
  (the same as 8611). Tesseract returns nothing on halftone-tinted boxes without `-blur 0x1.5 -threshold 55-60%`.
  Check #5's `Tabelle (\d+)` misses OCR-damaged `Tabelle ]` and every Bild-captioned table. Check #7 flags the
  Bild-captioned `<figure><table>` shape the rule itself requires.
- **What would have prevented it.** Delete the Briefing sentence; add the tint pre-filter to step 4; make
  check #5 `(Tabelle|Bild) [\d\]lI]+` and exempt Bild captions in #7.

## 160 — "Auf einen Blick" boxes: the rule says no figcaption from a title above a table; precedent uses one

- Found by the 8-99 sub-agent. r160: "**Do NOT promote section headings or bold titles above a table to
  `<figcaption>`**". 8609/22 and 8610/176 put "Auf einen Blick: …" into a `<figcaption>`. 8612 follows the rule
  (h2 + bare table), so the corpus is now split. Also silent: a label printed INSIDE the box (Stückliste),
  a Bild holding tables AND drawings (p61 Bild 7), and market overviews whose tables are only referenced generically.
- **What would have prevented it.** One sentence naming the "Auf einen Blick" box and its shape, and
  a scoped Verification variant for split runs.

## 130 — I queued two owner decisions that r170 already answers (my miss, not the rules')

- I read r130 and r000 *Changing a PROGRAM FILE* and queued "copy 8611's seq-trans.ob?" and "render
  hyperscreen ii.s?" for the owner. r170 prescribes both: recreate a printed MSE listing as a new prg/ file, and
  transcribe printed source. Found when I read r170, so no owner time was spent.
- **The rules were fine; I read ahead too little.** A pointer in r130's TODO section, "a `<pre>TODO</pre>`
  is r170's, which recreates MSE/Checksummer listings as disk files; do not escalate it", would have caught it.

## 180 — expand initials (rule) vs keep initials (every published meta); checks 4 and 5 broken

- Found by the sub-agent. The rule: "Initial → full name comes from the previous issue's Impressum, period". Its
  own examples and 8609-8611 keep initials. Check 4's bracket `[…\- ]` is "invalid character range" under BSD grep,
  so it silently passes. Check 5 counts one entry per <address>, but `(Name/xx)` yields two, so it flags correct metas
  (6 files in published 8611 too).
- **What would have prevented it.** Say "keep the initials as printed" (or fix the corpus). Use `[…., -]` in check 4.
  Split each address on `/` in check 5.

## 005 — KNOWN LIMITATION (owner, 2026-10-01): art-tilted ads are levelled to the art; accepted for 8612

- p183: art printed ~6.6° tilted. `measure_skew`'s coarse sweep SKEW_COARSE (-3.0, 3.0, 0.2) clamps at -3.3 (fine
  span ±0.3 around -3.0); the re-level pass then adds the re-measured residual -3.30, for -6.60 applied, residual
  -0.26 (the only NOTE). p140 +2.02° and p117 -1.72° are the same class inside the sweep range and carry NO note.
  Paper is square in all three thumbs; the masters show the sheet rotated, with prop/bed wedges. All three are ads,
  so no article text is affected. **Owner: accept, no code change for 8612.**
- Diagnosable next time by: |skew.angle| > 1° together with fold none and logo none on the same page.
- The fix, if it ever matters: a per-page skew override in r005, or refusing a total angle outside SKEW_COARSE.

## C3 / tools/mse.py — the MSE last line is shorter than the print, BY DECISION (owner, 2026-10-01)

- **What the print does.** The 1986 MSE printed a full 8-byte last line; bytes past the end address are whatever was in
  memory, checksum over all 8. MEASURED: 8612 p72 seq-trans `ff 00 ff`; 8611 p88 47erw `00 00 00 00 00`; 8611 p88 49erw
  `e6 7b a9 fc`; 8510 p144 timer-test `ff 00 ff 00 …`; 8502 p86 cursorsteuerung `00 a0`.
- **Why it cannot be rebuilt.** The bytes are in NO file. The prg stops at the end address, and the 8611A.D64 sector tail
  after SEQ-TRANS.OB is `00 00 00`. The checksum cannot tell `00 00 00` from `ff 00 ff`.
- **What the renderer does.** `dumpMSE1` sums only bytes with `c+i < e`, so our shorter line still checksums like the
  magazine's, and a reader typing it gets a working program. The gap is faithfulness, not correctness.
- **What was rejected.** A zero-pad changes 311/377 corpus listings in 31 issues, most then disagreeing with print. A
  per-listing `tail` variant (0/377 change; reproduces 8612 p72 exactly) exists at
  /Users/mist/DNB/8612/tmp/scratch_mse/mse.diff. It would need a generator hook plus 377 unverifiable hand
  transcriptions. **Owner: leave mse.py unchanged.**
- **Separate defect, out of 8612's scope, not investigated.** 8510 timer-test and SH8505 dump c000 ship prgs ONE byte
  longer than the printed range.
- Lesson kept: the change was approved and still measured first (r000). Measuring found it would have rewritten 311 shipped listings.

## 006 — a master can be silently overwritten by the cover export, and nothing checks master size against its stamp

- `masters600/001.png` was found as a 1240x1754 Affinity Photo export (19:58, quarantine xattr "Affinity Photo 2"), almost
  certainly saved over the master while title.png was being made from it. The stamp still said 4961x7016. r006's
  freshness check ("title.png older than the cover master") PASSES in this case. Fixed by re-running r005 `cut`
  (deterministic): 001 restored to 4961x7016, and the other 199 masters byte-identical before/after (shasum).
- **What would have prevented it.** r006 pre-build check: every masters600/NNN.png has the stamp's master-px. And tell
  the owner to export title.png to a new path (or work from a copy).
- **Also found by the sub-agent.**
  - make_issue_pdf_mixed.sh runs NCPU magick jobs, each with full OpenMP threads (load ~900, 25+ min stall). With
    `MAGICK_THREAD_LIMIT=1` it took minutes. This is the same oversubscription r000's lanes rule warns about.
  - r006's "all caches keyed on existence" omits `.ocrcache/pageclass.tsv` and `.ocrcache/jbig2/*.jb2`; both go stale after a re-grade.
  - The README says page 1 is "resized to page-1 dimensions"; the script refuses to resize.
  - The chroma snippet uses undefined `w, h`.

## 190 — the rule's step list is built around TODO markers that no step produces; the real work is in no step

- Both 190 sub-agents (8-39, 100-195) found zero TODO markers. The work was: 31+ lost drop caps, paragraphs split
  mid-sentence, headings that swallowed body text, lost headings, p.source debris, a dropped paragraph, and the
  Impressum rebuild. None of it is a step in r190; all of it came from my brief.
- Conflicts found: interview labels are "bold italic" per the rule but roman in 8612's print (page won). Dash lists: the
  rule says <ul> on a real glyph, while 8609-8611 keep `<p>— …</p>`. The aside test (tint/rule) misses a typeface-only box
  (Werner Paul bio). The never-split heading lists <pre>/<aside>, but its check covers only figure/table, and the
  Verification has no never-split or empty-<p> check at all. `/tmp/skipped_files.txt` is hardcoded. Word-level fixes
  inside <pre> are not addressed. The Impressum has no owning rule.
- **What would have prevented it.** A step "restore lost drop caps (one letter, from the crop)" and a step "split
  headings that swallowed body text". A never-split + empty-<p> check in Verification. An owner for the Impressum.

## 006 — I presented a MEASURED quantity (FORCE_CONTONE) as an owner decision; and "~50 mm²" is not a threshold

- **What happened.** I listed the chroma-area candidates with my own "force? yes/no/owner's call" column and argued 004, 114,
  125 and 042 out ("scanner backdrop", "neighbour leaf", "only a cast", "hairline"), offering 186 (68.5 mm²) as optional.
  r006: "**Anything above ~50 mm² carries real ink; below it is the scanner.** There is no judgement here." The owner's
  correction: FORCE_CONTONE is whatever the measurement yields, here 10 pages.
- **What in r006 failed to stop me.** The method (the code snippet) and the deciding sentence are ~20 lines apart, and the
  sentence is mid-paragraph after a table of 8611 numbers. Nothing near the FORCE_CONTONE usage line says "the list is the
  measurement's output".
- **The tilde.** "~50 mm²" gives no answer for a page at 48 or 52 while claiming "no judgement". Either state an exact
  number or admit a band that goes to the owner. (Not changed by me; recorded.)
- **What would have prevented it.** Put beside `FORCE_CONTONE=`: "= every bilevel page whose 3x3-opened chroma area exceeds
  50 mm² (exact). Not a choice; report the table."
- Also: three masters (001, 037, 073) carry the Affinity Photo xattr — the pages the owner cut crops from. Only 001's
  content was overwritten (shasums). Integrity check that works: re-run `cut` and compare all 200 shasums; 199/199 were
  byte-identical to the original sweep's output.

## 006 — RULE DEFECT: r006 thresholds TOTAL chroma area; it must be the LARGEST CONNECTED REGION (found by 64er_control)

- r006's method sums every 3x3-opened chroma pixel on the page. Fringing on body text vanishes under a 3x3 opening, but
  fringing on DISPLAY type is thicker than the kernel: 8612 p186's headline left 28 fragments (greys with a blue cast,
  R≈G, B +15-18) summing to 68.5 mm², the largest 27.9. The owner: "186 clearly b/w. if you measure something different,
  you're not measuring right."
- Measured (total / largest / blobs / 5x5-opened total): 180 2174.0/2153.6/7/2146.1; 152 2869.2/248.0/1788/969.5;
  022 136.2/136.2/1; 024 127.7/124.1/13; 125 94.8/89.6/13/63.5; 172 78.2/78.2/1; 114 75.8/58.7/5/74.2;
  004 3853.9/1504.5/1472/1977.7; **186 68.5/27.9/28/46.5 (fringe)**; **042 56.6/15.4/39/0.0 (fringe)**.
  Largest-blob separates cleanly: real ≥ 58.7, fringe ≤ 27.9.
- **And no area measure can tell printed ink from the scanner bed.** 004's chroma is the navy backdrop beside the narrower
  reply card (`mean > 25` lets a dark bed with a colour cast through). I excluded it as not ink; it ships bilevel = black,
  as 8611's 004 did.
- Final FORCE_CONTONE="022 024 114 125 152 172 180". The first build (with 004, 042, 186) was stopped in its OCR phase;
  nothing shipped.
- **Fix for r006.** Threshold the largest connected component (not the sum); state that display-type fringing survives a
  3x3 opening; exclude chroma lying outside the traced paper (the bed). "There is no judgement here" is only true once
  the measure is right.
- **Two defects, not one** (control): (1) total area vs largest component — the fringe problem (186, 042); (2) no exclusion
  of chroma outside the traced paper — the bed problem (004). Fix (2) would have removed 004 automatically; fix (1) alone would not.
- **The review was what caught it.** On 8611 the owner waived the page-input review; on 8612 they reviewed, and that is the
  only reason 186 was caught before shipping. r006's "a build started without that review is to be stopped" earned its place.

## 210 — the helper is half-converted from 300 dpi; a headerless start page has no rule

- `r210_head_meta_apply.py` uses `2480` and `x < 1240` (300 dpi page geometry) on 600 dpi block coordinates, so on 8612 it
  picked fragment blocks as head2 on 6 pages, missed one, and kept junk ("Aktuell |", "Hardwa", "C 123"). Its output was
  unusable; the sub-agent read every value off crops instead.
- "The start page's header is authoritative" has no fallback for a start page printed without a running head (52, a
  full-bleed photo opener). I used the first headed page. Check 1's expected-count formula is off by one (Leserforum
  carries head1), and the check cannot detect a head1 on an excluded rubric. `html.escape` writes `&#x27;` for the apostrophe
  in "64'er Extra" where the corpus has a literal `'`.
- **What would have prevented it.** Use page-relative fractions (`frac=`) in the helper; add "no running head on the
  start page → use the article's first headed page"; fix the count formula.

## 220 — the routing check skips every range row; the apply script routes by start page before 64er.pages

- Found by the sub-agent. The check's filter `p[1].isdigit()` drops rows like `172—173`, so it checked 26 of 55 rows,
  and a planted range-row misroute passed silently. The script sent the 320-KByte Aktuell item (inside 11 Aktuell, 11-14)
  to 14 Scorpio by exact start page, and the check then flags the CORRECT route. "Run from the issue directory" contradicts
  the Verification paths (repo root). Correcting a CSV typo can make the value equal <title> and delete it (step 3 after step 4).
- **What would have prevented it.** Parse the first integer before `—`. Route by `64er.pages` coverage plus an h2 match
  inside a multi-page rubric. One stated cwd.

## 006 — the mixed build writes no CreationDate/ModDate and no dc:title; r006's house standard needs them

- `make_issue_pdf_mixed.sh` output on 8612 had Title and Author but no CreationDate/ModDate and no XMP dc:title. 8611's LOG
  shows the same ("after the exiftool stamp"). r006 states the four fields and the exiftool repair recipe, but not that
  every mixed build needs the stamp.
- **What would have prevented it.** End make_issue_pdf_mixed.sh with the exiftool stamp (Title, dc:title, dates =
  file mtime), or say in r006 "the mixed build always needs this; run it after every build".

## 240 — the editorial reference check is unanchored; the Bücher banner is "never cp" and "you can cp" in one file

- Found by the sub-agent. The editorial loop greps `"$page-0.png"` (unanchored, `.` unescaped) and accepts `src="18-0.png"`
  (planted, passed). The other loops were already anchored. There is no shape check for the editorial. The rule is
  written as if the banners do not exist yet (find/crop/insert), while in practice 150 has placed the owner's cuts and
  240 is an audit. Step 3 "never `cp` the previous one" contradicts the Notes "You can `cp` the prior issue's".
- **What would have prevented it.** Anchor the editorial grep like the others; add an editorial shape check; reframe
  r240 as "audit the banners 150 placed"; delete one of the two cp sentences.

## 250 — check 4 flags figures/downloads/hidden blocks after a source, and rejects `</aside>`

- Found by the sub-agent. It accepts only h2/h3/aside/</section>/</article>/source as the next block, so every source followed
  by an r150/r170-placed figure or download is flagged (6 on 8612, 6 on 8611, 5 on 8610). A source that is the last child of
  an aside is also rejected. The trigger list omits <aside>. In-issue page pointers ("Anleitung auf Seite N") are unmentioned.
  "This rule only toggles the class attribute" is contradicted in practice by every OCR-damaged source line.
- **What would have prevented it.** Skip figure/download/display:none blocks before reading the next tag; accept </aside>;
  one line on in-issue pointers (plain <p>, per 8611/50).

## 260 — the Verification block does not run (heredoc terminator), and its FAIL fires on clean output

- Found by the sub-agent. `PYEOF && \` is not a valid heredoc terminator, so bash swallows check 2 and Python dies
  ("unterminated string literal"). Once fixed, `&& echo FAIL` keys on exit status (always 0), so it prints FAIL on every run.
  Check 2 has no exemption for a heading opening with a symbol (`§202a StGB`). Step 5's js-beautify options are unstated.
- **What would have prevented it.** Terminator alone on its line; test output non-empty, not exit status; exempt
  leading non-letters; name r080's beautify options. This is r000's "the WRAPPERS are code, so run them" in a .md.

## 280 — the two-engine check can never decide; the character-count heuristic would keep real OCR errors

- Found by the 100-195 sub-agent over ~260 fixes. The "second engine" (the block index) is the HTML's own ancestor, so it always
  shows the same oddity: the "engines disagree → apply" branch never fired once. Every fix rested on the crop. The block-index
  .txt truncates at ~300 chars (labels.json has the full text), so the rule's grep misses most body text.
- "Wrong number of letters → print typo, leave it; apply this heuristic FIRST" would have KEPT verlier→verliert,
  Textbildschirm→Textbildschirms, emem→einem, Pawrn, zusätzliicher, COME!I, all OCR adds/drops proven on the crop.
  It contradicts the rule's own "Doubled letters" section and "the test is the crop".
- Verification checks 1-2 pipe into `head` (a planted fault was hidden as entry 20 of 23) and never fail.
- **What would have prevented it.** Make the crop the decision and the block index a locator (via labels.json). Demote the
  letter-count heuristic to "a hint that it MAY be a print typo — decide on the crop". Drop `head` and make 1-2 fail on hits.

## 280 — the hex hard exception keeps known-wrong hex; the briefing forbids <pre> while the worklists put <pre> items on 280

- The exception ("Skip Pass 2 substitution when the token starts with `$`") exists to stop valid hex being "corrected".
  It has no case for OCR damage that makes the token INVALID hex (`$ddOd`, `$ffel`, `10le`, `$FDO0`: O and l are not hex
  digits). The sub-agent held them; I applied them after checking the crop.
- **What would have prevented it.** "A token that is not valid hex (contains O, l, I, …) is OCR damage: fix it from the crop."
  And one sentence on whether <pre> is in 280's scope (every agent had <pre> worklist items).

## 320 — the gate exits 0 on findings AND on CANNOT RUN; 8612's losses were all in blocks the classifier never kept

- Found by the sub-agent. Exit status 0 with UNACCOUNTED hits, with a planted deletion, and with "CANNOT RUN". Any exit-code
  consumer reads every case as a pass. The three real 8612 losses were a `noise`-labelled block (p19), a line absent from
  labels.json (p23), and merged column tops (p163). The gate cannot see any of them; earlier steps had found them by eye. A
  sweep of noise/other blocks gave 71 screenable candidates (all figure text). The probe threshold flips on large table
  blocks. r000's coverage section still recommends "dangling cross-references", which r320 calls TRIED AND REJECTED. The
  Jahresinhaltsverzeichnis ranges were wrong in both directions here (ads included; Centronics 52—57 vs 52-67).
- **What would have prevented it.** Exit non-zero on hits and on CANNOT RUN. Add the noise/other-block sweep as a companion.
  Delete the cross-reference line from r000. Call the index ranges "a hint to check on the masters".
