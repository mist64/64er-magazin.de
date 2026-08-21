# 000 — Orchestration: how to execute every other rule in this dir

**Goal:** define the meta-process that every numbered rule in this
directory is run under. Read this once at the start of an issue build;
re-read whenever a new agent or session takes over.

The build pipeline is a chain of substantive, sometimes editorial
transformations. It has **two kinds of step**, and they are run differently:

- **Program steps** (010, 020, 030) are code that runs to completion:
  `tools/img/scan2ocr`, scan -> per-page corpus -> one consolidated `.md`.
  The orchestrator **runs them itself**, checks the exit status, and runs the
  step's Verification block. There is nothing to dispatch: the judgement inside
  them is already a model call the program makes per page.
- **Editorial steps** (040 onward) are prose specs applied to the HTML. These
  are the ones dispatched to a sub-agent, per the rule below.

Both kinds carry a mandatory Verification block. The dispatch rule below applies
to editorial steps; for a program step, "verify the sub-agent's work" becomes
"verify the program's output".

Numbers go in **tens**, zero-padded to three digits so they sort lexically.
Tens so a step can be inserted forever without renumbering a single reference --
which is exactly what `9b` and the missing `23` were symptoms of.

Running the editorial steps in-line in the main conversation thread is the wrong
shape: each one chews up context the user is paying for, and it skips the second
pair of eyes the verification block in each rule was designed to provide.


## The chain, and what the numbers used to be

The scan-to-corpus steps and the issue-build rules were two chains that met at
the `.md` with no shared vocabulary. They are one chain now, numbered in tens.
`LOG.md` entries in `issues/8607` and `issues/8608` name the OLD numbers and
were deliberately **not** rewritten — they record what was actually run. Read
them through this table.

| now | was | step |
|---|---|---|
| 010 | — | ocr_blocks — OCR the scans into measured blocks |
| 020 | — | classify — labels, reading order, roles, per-page markdown |
| 030 | — | assemble — pages back into articles, one `<YYMM>.md` |
| 040 | 1 | escape_asterisks |
| 050 | 2 | escape_tags |
| 060 | 3 | md_to_html |
| 070 | 4 | html_cleanup |
| 080 | 5 | split |
| 090 | 6 | toc_txt |
| 100 | 7 | toc_category |
| 110 | 8 | pubdate |
| 120 | 9 | prg_from_d64 |
| 130 | 10 | place_figures |
| 140 | 11 | 64er_id |
| 150 | 12 | place_images |
| 160 | 13 | fill_tables |
| 170 | 14 | transcribe_todo_listings |
| 180 | 16 | author_meta |
| 190 | 17 | layout_fixups |
| 200 | 18 | leserforum |
| 210 | 19 | head_meta |
| 220 | 20 | index_meta |
| 230 | 21 | formulas_mathjax |
| 240 | 22 | rubric_banners |
| 250 | 24 | p_source |
| 260 | 25 | heading_case |
| 270 | 26 | strip_autolink_artifacts |
| 280 | 27 | ocr_word_cleanup |
| 290 | 28 | heading_hierarchy |
| 300 | 29 | fehlerteufelchen_errata |

Two rules were removed rather than renumbered:

- **9b** (blocks index) — step 010 already OCR'd every page and knows every
  bbox; a second tesseract pass over the same paper could and did disagree.
- **15** (author bio `<aside>`) — a bio box is one more tinted box, and the
  reliable evidence for a tinted box is the scan, not the prose inside it.
  Rule 190 owns every aside now.

There was never a 23.

## The rule

For every numbered rule in this directory:

1. **Dispatch the actual execution to a sub-agent.**
   - Brief the sub-agent with the rule's path (`tools/img/scan2ocr/rules/N_<name>.md`),
     the relevant inputs (issue dir, worklist files, PDF text, existing
     mapping decisions, etc.), and the variant-specific calls it has to
     make. The rule `.md` is designed to be self-contained — pass it as
     the agent's primary instruction source.
   - Tell the sub-agent to **not commit** anything; the orchestrator
     verifies first.
   - Ask for a structured summary: files touched, per-target table,
     TODOs, orphans, anything the sub-agent skipped or couldn't decide.
2. **Verify the sub-agent's work yourself, in the orchestrator.**
   - Run the `## Verification` block of the rule. Every rule .md in
     this directory has one (or must — see "Verification rules
     mandatory" below).
   - Spot-check a sample of the touched files by reading them — not by
     trusting the sub-agent's summary.
   - If verification fails, decide whether to re-dispatch with
     corrections, fix locally for a small slip, or escalate to the user.
     Always flag the failure to the user; don't silently retry.
3. **Only then surface the result to the user.**
   - Report the sub-agent's summary + your verification result + the
     proposed next step (commit, redispatch, ask for input, …).

## When the rule is "do it once for this issue"

A few rules are inherently editorial and one-shot per issue (e.g. the
`toc.txt` transcription, the `pubdate.txt` write). Those still go to a
sub-agent — the sub-agent's job is the transcription work, and the
orchestrator validates against the project's conventions (formatting,
spelling, cross-references). Don't shortcut just because the output is
small.

## When NOT to dispatch

- Truly trivial single-file edits the user explicitly directed (e.g.
  "fix this typo on line 17 of file X"). The sub-agent overhead isn't
  worth it.
- Status checks / lookups that don't write anything (`grep`, `git
  log`, `ls`, reading a file). Just do them in-line.
- Tool / dependency setup (`brew install`, `npm install`) — run
  inline so the user sees the output and can intervene.

The trigger for sub-agent dispatch is an **editorial** rule (040 onward) under
`tools/img/scan2ocr/rules/`. Program steps (010-030) the orchestrator runs
itself. Anything outside that directory is at the orchestrator's discretion.

## Verification rules mandatory

Every rule `.md` in this directory **must** include a `## Verification`
block with at least one runnable check. Without it, the orchestrator
has nothing to validate the sub-agent against. If you're writing a new
rule, write the verification block before the procedure section — that
forces clarity about what "done" means.

The verification block should:
- be runnable as shell (with `python3 -` heredocs where useful);
- exit non-zero or print a clearly flaggable result on failure;
- be cheap enough that running it after every sub-agent dispatch is
  acceptable.

## Briefing template for a sub-agent dispatch

Use this skeleton when invoking the `Agent` tool for a rule:

> You are executing rule `tools/img/scan2ocr/rules/N_<name>.md` for issue YYMM.
> **Read that file first and follow it as the spec.** Below are the
> inputs and what I need back.
>
> ## Inputs
> - `<paths to worklist / PDF text / mapping files / etc.>`
> - any pre-flight decisions the user has already made
>
> ## Output
> 1. The transformations described in the rule.
> 2. **Do NOT commit.** Leave changes uncommitted; I'll verify and
>    commit.
> 3. Return a structured report: `<table or list per the rule's
>    end-of-session summary section>`, plus every TODO/orphan/skip.

The template is intentionally short — the rule itself carries the
procedural detail.

## How the orchestrator re-enters after the sub-agent

When the completion notification arrives:

1. Read the sub-agent's summary message.
2. Run the rule's `## Verification` block in the main session.
3. Read a few sample touched files (3–5 is usually enough).
4. Diff `git status --short` against the expected set of changes:
   files that should have been touched, and only those.
5. Report to the user with: sub-agent summary + verification result
   + suggested next action (commit / re-dispatch / decision needed).

## Commit & staging discipline (MANDATORY)

Two real incidents on the 8608 build trace to loose staging:
a rename-only commit that silently dropped four files' content edits
(the `git mv` staged instantly, the content edits never got staged and
were lost until re-applied), and 25 image crops swept into an unrelated
commit by `git add -A`. Both are preventable:

1. **Never `git add -A` / `git add .` during an issue build.** Stage by
   **explicit pathspec** of the rule's expected file set. Several rule
   scripts self-stage (`r060_md_to_html.sh`, `r080_split.sh`,
   `r100_toc_category.sh` run `git add`/`git rm`), so the index may already
   be partly populated when you arrive — reconcile it deliberately, per
   file, before committing.
2. **Rules that BOTH edit content AND rename** (rule 260 is the prime
   case: it rewrites the h1/`<title>` *and* `git mv`s the file) are the
   danger zone. `git mv` records with 100% similarity ("0 insertions")
   if the content matches; if you staged the rename before the content
   edit landed, the content is silently lost. Stage the content edit
   and the rename together, then verify (next step).
3. **Post-commit verification is mandatory — verify HEAD, not the
   working tree.** After every commit run:
   ```bash
   git show --stat HEAD          # file list matches the expected set?
   git status --short            # MUST be clean; a dirty tree = something unstaged
   ```
   For a content+rename rule, additionally `git show HEAD -- "<new path>" | head`
   and confirm the content diff is non-empty (not a bare rename).
   Checking the *working tree* passed verification while the *commit*
   was empty is exactly how the rule 260 loss went unnoticed.
4. **Commit large binary source assets in their OWN commit.** The scan
   PDF (`64er_19xx-xx.pdf`, ~95 MB) and image-crop batches are permanent
   git objects — don't let them ride along in a metadata/content commit.
   On 8608 the 94 MB source PDF landed inside the "rule 100 toc_category"
   commit, making a metadata change weigh 206 MB and muddying the diff.
   Stage binaries deliberately, on their own, with a message that says so
   — the commit boundary is the only place this stays legible in history.

## Scope confinement (every sub-agent brief)

Add to every dispatch: **the sub-agent may write only the files its
rule owns.** All scratch/rendered artifacts go under
`/tmp/64er_<YYMM>_*` or `issues/<YYMM>/_tmp/` — never loose in the issue
directory. (8608 accumulated `Archive.zip`, `out.txt`,
`png/{bw,c,…}/` and stray page crops in the issue dir from agents
overstepping.) A sub-agent that renders/crops for its own OCR must
delete or /tmp-scope those files; the issue dir holds only shippable
content.

## End-of-issue gates (run before declaring an issue done)

The per-rule verifications catch per-rule failures; these catch what
falls between rules:

1. **No stray TODO.** `grep -rn 'TODO' issues/<YYMM>/*.html` must be
   empty, OR every hit must be an entry in `LOG.md` explicitly
   dispositioned (transcribed, or user-acknowledged permanent). Ad-hoc
   markers (`TODO VERIFY LISTINGS ABOVE!`) are invisible to the
   per-rule greps (which each match only their own marker vocabulary),
   so only this generic sweep catches them.
2. **Article-set completeness.** Compare the split article set against
   the printed TOC page entries AND the previous issue's recurring
   rubrics (Editorial, Aktuelles, Leserforum, Fehlerteufelchen, Bücher,
   **Impressum**, Vorschau). Every printed-TOC entry must have a
   matching start-page file. On 8608 the Impressum (printed p.163) was
   dropped before rule 080 and nothing noticed — the next issue's rule 180
   then has no Impressum to expand editor initials from.
3. **LOG.md is the audit trail — every rule contributes.** Any rule
   that finds a body-text gap, an un-transcribable region, a print
   oddity, or a deferred decision writes it to `LOG.md`. At issue end,
   **every `LOG.md` "known gap" must be explicitly dispositioned**
   (fixed, or user-acknowledged as permanent) — a scope note like
   "out of table scope, not repaired" must not be the final word on a
   reader-visible defect (e.g. 8608's truncated `84` intro).
4. **No unfilled placeholder comments.** Commented-out
   `<!-- <meta name="…" content="XXX"> -->` templates left by rule 080
   are either filled by their owning rule or deleted — they must not
   ship as litter (8608 shipped 44 stale `toc_title` placeholders).

## Lessons / things to watch

- A sub-agent without a verification gate is just a different opaque
  black box. The verification is the point.
- Sub-agents are happiest with concrete pre-flight decisions: if the
  rule allows judgment (e.g. picking categories, picking a section
  for an orphan listing), make those calls in the orchestrator first
  and pass them in. The sub-agent then has only mechanical work left.
- When a sub-agent says "I couldn't decide X", that's a signal to the
  orchestrator to make the call (or ask the user) and re-dispatch —
  not to accept the half-finished state.

## Per-rule constraints the orchestrator must enforce

- **Rule 080 (split): paired articles never get split.** Two h1-style
  banners on non-adjacent pages can belong to one editorial unit (same
  product/topic, same author, overview + deep-dive). The merged file
  carries two `<p class="intro">`, two `<address class="author">`, and
  a comma-joined `<meta name="64er.pages">`. See the *Paired articles
  — never split* section in `tools/img/scan2ocr/rules/r080_split.md` for the
  signals, the merged-HTML shape, canonical examples in
  `issues/8607/`, and the verification one-liner. Before dispatching
  rule 080 (or any earlier rule that produces the consolidated `.md`),
  brief the sub-agent on this constraint so it doesn't re-introduce a
  second `<h1>` based on the printed banner alone.

## Cross-cutting recipe: page block index (blocks/pNNN.txt)

Several steps (130 place_figures, 160 fill_tables,
170 transcribe_todo_listings, 210 head_meta, 240 rubric_banners) need the bbox of a
specific region on a page -- a caption, a listing block, a header strip, a
banner illustration. The common primitive is a per-page **block index**: one
line per layout block giving its bbox, its label and a short text preview.

**It is an output of step 010**, written by `r010_blocks_index.py` to
`<OUT_DIR>/blocks/pNNN.txt`.

`<OUT_DIR>` throughout the rules means the issue's working directory, which is a
constant at the top of `r010_ocr_blocks.py` and is **not** inside the repo. Ask
the module rather than assuming a path:

```bash
OUT_DIR=$(python3 -c 'import sys; sys.path.insert(0, "tools/img/scan2ocr/rules")
import r010_ocr_blocks as OB; print(OB.OUT_DIR)')
ls "$OUT_DIR/blocks/" | head
``` There is nothing to schedule and nothing to wait for:
step 010 has already OCR'd every page and already knows every bbox, so the index
is a projection of data we have rather than a second OCR pass. It costs no OCR
and cannot disagree with the corpus.

(This replaces the old rule `9b`, which re-ran tesseract over the delivered PDF
and reduced the TSV with awk. Two OCR passes over the same paper could and did
disagree.)

Lines look like:

```
block=16 label=body bbox=2136x574+390+3736 frac=0.0786,0.5325,0.5093,0.6143 text= 8910 Landsberg 2300 Kiel ...
block=1001 label=header bbox=564x116+2298+240 frac=0.4633,0.0342,0.577,0.0507 text= Aktuelles
```

Grep for the caption / heading / header text you need, then crop:

```bash
grep -iE "listing|tabelle|bild" <OUT_DIR>/blocks/p145.txt
magick <SRC_DIR>/145.png -crop 2136x574+390+3736 +repage /tmp/64er_<YYMM>_crop.png
```

**COORDINATE SPACE -- read before cropping.** The bboxes are in pixels of the
graded **600 dpi master** (`SRC_DIR`), which is deskewed and A4-cropped. They are
**not** in the delivered PDF's page space: the PDF page is neither deskewed nor
cropped, so the two differ by a rotation and an offset. Crop from the master,
never from a `pdftoppm` render. `frac=` is the same box as a fraction of the
page, for cropping a render at any other resolution.

For listings and tables, the caption block tells you the column (X, width W);
the code or table region usually sits **above** it in the same column -- walk
preceding blocks whose x-range overlaps to find its top edge.

Everything under `out/` is scratch -- never commit it.

## Cross-cutting rule: the PDF has no usable text layer

The delivered PDF's text layer is a re-OCR of the same scan. It is **not**
independent evidence, and on a scanned issue it is **void** -- agreeing with it
proves nothing, and disagreeing with it proves nothing either.

There are exactly two authoritative sources for what the print says:

1. **step 010's block index** -- `<OUT_DIR>/blocks/pNNN.txt`, one line per block
   with its bbox and text, produced by the pipeline's own OCR of the graded
   master;
2. **a 600 dpi crop of the master** at that bbox, read with your own eyes.

Every rule that asks a sub-agent to evidence a word-level claim must ask for one
of those two. Do not ask for a `pdftotext` cross-check: it is the thing being
checked wearing a different hat. This is stated once, here, because it was
previously restated per rule and the restatements disagreed -- two rules called
`pdftotext` void while two others demanded it as the mandatory evidence form,
each citing rule 280 as the authority.

## Cross-cutting rule: OCR cleanup granularity

Every rule that touches article body text inherits the same
anti-memory granularity rule. Word-level OCR substitutions (e.g.
`darsteUen` → `darstellen`, `0PEN` → `OPEN`, lost-space fixes,
multi-hyphen artifacts) **are allowed** even when the agent recognises
them from context — they're word-by-word fixes the surrounding text
confirms. Re-typing a sentence or paragraph from memory because the
result reads better is **forbidden**, no matter how plausible each
individual change looks.

The granularity boundary is **one word at a time, nothing larger**.
If a passage seems to need broader cleanup, the answer is to OCR the
scan again (or hand the section back to the user), not to compose a
rewrite.

That is the whole rule; it is written out here rather than referenced, because a
sub-agent is briefed with a rule file and cannot resolve a link to anyone's
memory. Rules that need it link **here**.

Make this explicit in every sub-agent brief that involves body-text
editing — it's the difference between a faithful archive and a
modernised paraphrase.

## Cross-cutting rule: resolve editorial ambiguity from prior issues

Whenever a rule involves an **editorial judgment call** — category
assignment, TOC wording/granularity, article pairing, banner/heading
choices, byline handling, layout placement, and the like — and the
current issue's inputs don't settle it, **look at how prior issues in
`issues/*` handled the analogous case before deciding.** The already-
published issues are the canonical precedent; the repo *is* the style
guide.

Procedure:

1. **Grep the committed output of prior issues** for the analogous
   article/section (by filename pattern, `<meta>` value, `toc.txt`
   line, etc.). Prefer the most recent issues, but scan several — a
   single neighbour can be an outlier.
2. **Follow the dominant pattern**, not the first hit. If e.g. 8 of 9
   issues categorise a call-for-submissions page as bare `Wettbewerbe`
   and one uses a sub-line, the bare form wins; note the outlier but
   don't copy it.
3. **Only escalate to the user when precedent is absent or genuinely
   conflicting** (no clear majority). When you do, present the
   precedent you found and your recommendation — don't ask cold.
4. Record the precedent you relied on in the sub-agent brief and in the
   report, so the decision is auditable and the next issue inherits it.

This is the default for *every* rule with an editorial degree of
freedom. "Check the other issues" beats "ask the user" beats "guess" —
in that order.

## Cross-cutting rule: know which source is authoritative before "correcting"

Before you change a value because it "looks wrong," identify **which
source is the ground truth for that specific field**, and check *that*
source — not a different one that merely looks related. Several
near-misses and one real regression on 8608 all share this shape:
"correcting" a value against the wrong authority.

- `index_title` / `index_category` → the **Jahresinhaltsverzeichnis CSV**,
  not the in-issue headline/TOC (rule 220). 8608/142 `Drei C-Compiler`
  was wrongly "fixed" to `Der` from the headline.
- A `<figcaption>` / `Listing N.` caption → the **scan** of that page,
  not plausibility or `pdftotext` (rules 130/160/170). 8608/142's
  `Listing 1. Laufzeit-Testschleife in »C«` was almost deleted as
  "invented" — it is printed in bold on p145.
- Body text wording, incl. impossible-looking values → the **scan**;
  a genuine print typo (a backwards address range `49152-48165`, a
  dropped digit) stays verbatim (r000 "OCR cleanup granularity",
  r280 "it's not a German word, so it must be OCR").

The failure mode is always the same: reasoning from a *related but
non-authoritative* artifact (the headline, another OCR layer, "it reads
wrong"). When the authoritative source and a related one disagree, that
disagreement is usually *expected*, not an error — confirm against the
right source before touching anything, and when unsure, leave it.

- **Any sub-agent dispatched to apply a per-candidate rule must include
  verifier evidence inline in its report.** See the
  `## Evidence-in-report requirement` section of each rule for the
  rule-specific evidence form. A fix reported without evidence is
  treated as un-applied and re-dispatched — the orchestrator does NOT
  re-do the verification itself. This rule exists because of the
  `internsiv` regression: a sub-agent claimed verbal verification it
  never ran, and a print typo was "corrected" into something the print
  never said.

## End-of-issue gate: the coverage check

Before an issue is called finished, run the omission gate:

```bash
tools/img/scan2ocr/rules/r030_coverage_check.py issues/<YYMM> <ocr-out-dir>
```

Every block the classifier kept must appear in the article claiming its page.
Investigate each `UNACCOUNTED` hit and record the disposition — a hit is either
content that was dropped, or an explainable false positive (a restored drop-cap,
a deliberately deleted duplicate, a table whose cells now split the text).

This exists because **omission is the one defect class that reads as correct.**
Every other check in the chain — spell-checks, markup greps, beautify, tag
balance, the build — passes cleanly on an article that is missing a paragraph, a
table, a heading or its last line. 8609 shipped with all four before a
page-by-page read found them, and reading every page by hand does not scale.

Two cheaper companions worth running at the same time:

- **page coverage**: every page in the issue is claimed by an article, or is
  knowingly an ad / classifieds page. Gaps are missing articles; the annual
  `Jahresinhaltsverzeichnis` gives the authoritative page range per article and
  caught two understated ranges in 8609 (71-74, 82-84).
- **dangling cross-references**: text that says `Bild 3` / `Tabelle 2` /
  `Listing 4` while the article has no such caption. A reference with no target
  usually means the figure and its caption were dropped together.

## Deliberate deviations from print must be marked in place

The standing rule is that the printed page wins, and every review pass is told
so. That makes an intentional departure fragile: the next pass verifies against
the page, sees a mismatch, and faithfully undoes it.

So when the editor decides to depart from the print — a typesetting error worth
correcting rather than preserving — record it **in the file, at the point of
the change**, as an HTML comment saying what the print has and that the
difference is intentional:

```html
<!-- deviates from print, deliberately: p150 sets one heading
     "Kleines Assembler-Lexikon: TurboAss- und ASSI/M-Besonderheiten"
     over the Lexikon box, but the second half belongs to these two
     tables. Split here; do not "restore" it to the printed form. -->
```

Mark both ends when the change moves text between two places, so whichever end a
reviewer looks at first explains itself. Note it in the issue's `LOG.md` too.

This is the counterpart to preserving genuine print typos: `eröfffnet`,
`Machin Lightning` and `WOUTP x10,y10` stay because nobody decided otherwise —
a deviation only exists where someone deliberately made one, and then it needs
to be legible as such.

## Never declare an issue complete without the user signing off

An issue is finished when **the user says it is**, not when the checks pass.
The rule chain, r310, the coverage gate and a green build together establish
that nothing *detectable* is outstanding — they do not establish that the issue
is right. Every substantive defect class in 8609 was found by a human looking
at a page after the automated checks were already green.

So: report status, list what is still open, and wait. Do not write "the issue is
complete" or upload on your own judgement.

## Changing a listing ALWAYS goes to the user first

`prg/*.txt` are the programs readers typed in. Editing one — applying an
erratum, correcting a line, renumbering — is not a markup fix and is never
routine:

- **Tell the user before doing it, and show the exact before/after lines.**
- Record it in the file's `;` header in the corpus vocabulary (see r300), so
  the change is legible to the next reader.
- Keep the superseded line as a `;` comment rather than deleting it, so the
  disk's original state is recoverable from the file itself.
- **Test the result** — the listing must still load and run. See r320 for the
  x128 harness.

The default remains: record the errata state, do not patch. Patch only when the
user asks for it.
