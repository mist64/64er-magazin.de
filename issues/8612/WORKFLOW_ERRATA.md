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
