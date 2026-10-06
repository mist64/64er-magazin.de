# 000 — Orchestration: how to execute every other rule in this dir

**Applies to:** all — the meta-rule itself; it defines the `Applies to:` contract below and is read at the start of every issue of either kind.

**Goal:** define the meta-process that every numbered rule in this
directory is run under. Read this once at the start of an issue build;
re-read whenever a new agent or session takes over.

## BEFORE ANYTHING ELSE: name the issue

Every step imports one name for the issue being built, from `r000_issue.py`. It
has **no default**, so nothing runs until you set it:

```bash
echo 8612 > tools/img/scan2ocr/rules/ISSUE.txt     # one line, the issue id
```

`ISSUE.txt` is git-ignored: which issue a working tree is building is a local
fact. `ISSUE=8612` in the environment overrides it for a single run.

It used to be a hardcoded string in `r000_issue.py` that each issue had to
remember to edit, and **forgetting did not crash** -- every step read the
previous issue's descriptor and wrote the new issue's pages into the finished
issue's directories, on top of published work, silently. A build that cannot say
which issue it is now stops and tells you how to say so.

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

## THE FILES ARE THE DELIVERABLE, not the issue

An issue is published once. These files are read by every agent that builds
every issue after it, so **the point of a build is not that the agent working
it learns something — it is that this directory learns it.** The next agent
should need less help than the last one, and the run after that less again.

Two habits follow, and they are not optional.

**Write the rule BEFORE you send the correction.** When a run goes wrong and
someone supervising it works out why, the fix belongs in the `.md` first and
the message to the runner is then a pointer: *"pull, read r005 §the gate"*.
A correction delivered as prose in a message teaches one agent and evaporates.
8611's supervisor caught itself doing exactly that and had to go back.

**Record what was DISPROVED, not only what was true.** A plausible wrong
hypothesis costs the next agent the same cycle it cost this one, and nothing
in a rule warns them off it unless someone writes it down. `r005_masters_spread.md`
now carries "the thumb pool is not too smooth — measured, 2-6 levels" and "if
joint clamp is ~95 % then `W` is not the defect" for precisely that reason:
both were reasonable, both were wrong, both cost a cycle.

The test of a rule is not whether it is true. It is whether an agent who has
never seen this issue can act on it without asking.

## `Applies to:` — the issue-kind contract

Not every step exists for every issue. A **monthly** (`8609`) carries a
Leserforum and gets errata columns; a **Sonderheft** (`SH8601`) is one theme
end to end, with its own table-of-contents categories and none of the monthly's
recurring rubrics. Steps written for one and run against the other used to be
"skipped", which is indistinguishable in the record from a step nobody got to.

So **every `rNNN_*.md` in this directory carries an `Applies to:` line in its
header**, on its own line immediately under the H1 and before `**Goal:**`:

```
# 220 — Fill `64er.index_category` / `64er.index_title` from the annual CSV

**Applies to:** all — a monthly takes the annual Jahresinhaltsverzeichnis
CSV; a Sonderheft takes `Gesamtinhaltsverzeichnis Sonderhefte.csv`, keyed
`N/YY` in column 3 (`SH8602` → `2/86`). RE-CLASSIFIED 2026-10-03: the old
`monthly` rested on "no Sonderheft has a row in any of them", which is true
of the ANNUAL CSVs and ruled out one file rather than the input. SH8601
shipped with no index metadata as a result.

**Goal:** …
```

The value is exactly one of `all`, `monthly`, `sonderheft`, optionally followed
by ` — ` and the one-line reason. Machine-readable:

```bash
# -m1: the header line is the first hit in every file, so the illustrative
# examples further down THIS file do not pollute the listing.
grep -m1 -H '^\*\*Applies to:\*\*' tools/img/scan2ocr/rules/r[0-9][0-9][0-9]_*.md
```

The issue's kind comes from **`issues/<ID>/issue.json`**, field `kind`, loaded by
`r000_issue.py`. Never from the issue id, never from the directory name, never
from the orchestrator's memory of what this issue is.

### A kind mismatch is a RECORDED OUTCOME, never a silent skip

When the rule's `Applies to:` value is neither `all` nor the issue's `kind`, the
orchestrator does **not** dispatch it — and does **not** just move on. It writes
the outcome into `issues/<ID>/LOG.md`, in the same place and shape every other
step's result goes, before advancing to the next number:

```markdown
## Step 240 (rubric_banners) — not applicable — kind

Rule header: `Applies to: monthly`. `issues/SH8601/issue.json` → `"kind": "sonderheft"`.
Evidence: SH8601's `92 Bücher zum C 128.html` carries no `92-0.png`, and the
issue has no Editorial/Vorwort or Fehlerteufelchen article at all.
No files touched.
```

**The evidence must rule out the INPUT, not one file.** This example used to be
step 220, with `grep -c '^SH8601,' Jahresinhaltsverzeichnis 1986.csv` → 0 as
its evidence. That grep is true and the conclusion was wrong: a Sonderheft's
index lives in `Gesamtinhaltsverzeichnis Sonderhefte.csv`, keyed `N/YY`, so
220 applies to both kinds and has been re-classified. SH8601 shipped with no
index metadata because this example taught the skip. Before writing
`not applicable — kind`, ask what the input for THIS kind would be, and show
that it does not exist.

Three things are mandatory in that entry and all three are checkable:

1. **The literal phrase `not applicable — kind`** in the heading, so the whole
   chain's dispositions can be counted with one grep. Any other wording
   ("skipped", "N/A", "does not apply") is a defect — it makes the audit trail
   ungreppable.
2. **Both sides of the comparison, quoted**: the rule's `Applies to:` value and
   the descriptor's `kind`. A reader must be able to re-derive the decision
   without opening either file.
3. **One line of positive evidence that the step really had nothing to do** —
   the empty glob, the zero row count, the absent rubric. `Applies to:` says
   what we *expect*; the evidence line says what we *found*. This is what makes
   it a verified outcome rather than a declaration: the same discipline as every
   `## Verification` block in this directory. If the evidence line comes back
   NON-empty — a Sonderheft that does turn out to carry the thing — the
   classification in the rule header is wrong. Stop, tell the user, and fix the
   header; do not run the step behind the contract's back.

At the end of the issue, every number in the chain has exactly one `LOG.md`
disposition: ran-and-verified, `not applicable — kind`, or `not run — disabled`
(a step whose own rule header says DISABLED, as r145 does). A number with
neither is an unfinished issue, and that is precisely the state the old silent
skip made invisible.

`Applies to:` is a property of the RULE, not of the issue at hand. Do not edit a
rule's header to make a particular build go through. A rule that turns out to
apply to both kinds is re-classified `all` **with the evidence in the commit
message**, permanently, for every issue after it too.

## THE SHAPE OF A BUILD: TWO PAUSES, AND NOTHING ELSE INTERRUPTS THE OWNER

An issue build stops for its owner **exactly twice**. Between those two points
the chain runs unattended -- it does not ask, it does not wait, and it does not
experiment. Everything it needs in between is either in these files or derivable
from the scan; where it is not, that is a **defect in these files** and fixing it
is part of the work (see *THE SCAN IS THE ONLY INPUT*).

**NEVER COPY THE PREVIOUS ISSUE'S DESCRIPTOR.** `binding` and `paper` are
properties of the PHYSICAL COPY in the owner's hands, and the next issue in a
series is not bound or printed the same way just because it is next. 8612's
descriptor was copied from 8611's and silently inherited its `colors` path;
SH8601 is `binding: "sheet"` and the Sonderheft after it may be anything.
Write the descriptor fresh: copy only the SHAPE (which keys exist), never the
values. Both values come from PAUSE 1.

**PAUSE 1 — before step 005.** The two questions about the physical copy:
binding, and which pages are which paper. They cannot be answered from a scan,
and 005 grades nothing until they are. See the section below.

For `binding: spread` the paper answer is **fixed** until the spread variant
learns per-page classes: one measured profile under the legacy `colors` key,
wrapper graded with the interior (decided 2026-09-27, 8610 and 8611). A spread
descriptor carrying `paper` with `high_pages` is not honoured — every page is
graded with the single profile, silently. So ask the owner only to CONFIRM that,
not to choose.

**PAUSE 2 — the image boundary.** The chain runs from 005 to the end of the HTML
with **no cut figures**, then stops and hands over. What it delivers:

1. `issues/<ID>/*.html` complete in every respect that does not need a figure --
   text, tables, listings, metadata, headings, errata, the lot;
2. the **crop worklist**: every figure the pages call for, with page and caption,
   so the owner can cut them;
3. the **cover source** for `title.png` -- step 006 blocks on a hand-made 150 dpi
   `title.png` and the owner makes it from the scan. **This is handed over at
   005, not here** -- see *An OWNER DELIVERABLE is handed over the MOMENT it
   exists*, below. By PAUSE 2 it should already be in the owner's hands;
   re-state it here only as a reminder of what is outstanding;
4. **every owner decision accumulated since pause 1** (below).

Then the owner cuts the figures and makes `title.png`. Then the chain resumes:
place the images (150), build the PDF (006), re-run the end-of-issue gates.

**Step 006 is numbered early and RUNS LATE.** It is the issue PDF, it blocks on a
hand-made input, and the PDF comes last anyway (*THE PAGE IMAGE IS `masters600`*).
Numbering is not a schedule.

### An OWNER DELIVERABLE is handed over the MOMENT it exists — and the chain does not stop

PAUSE 2 is the point at which the chain **cannot make progress without the
owner**. It is not the point at which the owner first hears from it.

Two of the things PAUSE 2 hands over are **ready long before PAUSE 2**, and
both are work the owner does by hand, so every hour they sit unmentioned is an
hour of the owner's time the build is holding:

| deliverable | ready after | hand over |
|---|---|---|
| the **uncut, deskewed, colour-corrected 600 dpi pages** — `<tmp>/sheets600/` | **005** | `open <tmp>/sheets600` |
| the **150 dpi cover crop** for `title.png` | **005**, and on a `sheet` binding **005b** (it is a 25 % reduction of `<A4>/001.png` — `a4600` for `sheet`, `masters600` for `spread`; see r006) | `open <tmp>/title_source_150.png` |

**Owner, 2026-10-05:** as soon as either is available, **tell the owner and
`open` it — and do NOT stop.** Carry on with the next step in the same breath.
This is a notification, not a pause: the owner works on the title and reviews
the pages while the chain runs on, and the two only have to meet at PAUSE 2.

So, at the end of 005:

```bash
# the pages: all of them, uncut, deskewed, graded
open "$TMPDIR_ISSUE/sheets600"

# the cover crop, which is a FILE and not a recipe -- see below
open "$TMPDIR_ISSUE/title_source_150.png"
```

and say in the same message which is which, how many pages, and that nothing
is blocked.

**The cover crop is a FILE, not a recipe.** SH8602 documented the source
master, the traced page box, the target size and an export warning in its crop
worklist, and **made no file**, so the owner had to ask where it was. SH8603
produced `title_source_150.png` and that is the precedent. Make the file.

### Owner decisions ACCUMULATE; they are not raised when found

Several steps turn up something only the owner can settle:

| step | what it finds |
|---|---|
| 300 | a Futureteufelchen -- our own correction to the printed page. **Each one needs the owner's authorisation**, every time |
| 325 | a passage that reads wrong and may be the scan or may be the print |
| any | a reader-visible defect the rule cannot resolve from the page |

None of these is a reason to stop and ask. **Write it to `LOG.md` the moment it
is found** -- with the page, the evidence, and the question in one sentence --
and carry on. They are delivered as one list at pause 2, where the owner is
already looking at the issue. A question asked the moment it occurs costs the
owner a context switch and the chain its momentum; the same question asked with
nineteen others costs one sitting.

### What legitimately CANNOT pass at pause 2

The end-of-issue gates are written for a finished issue. At pause 2 the issue is
finished *except* for figures, so:

- **Gate 1, "No stray TODO", cannot pass** -- every unplaced figure is a `TODO`
  by design. That is the deliverable, not a failure. Report the count; do not
  hunt for a way to make the grep empty.
- Any check that renders or inspects the issue PDF cannot run -- 006 has not
  happened yet.

The per-rule verifications that touch a **cut figure file** are likewise partly
deferred. SURVEYED 2026-10-01 -- the blocks containing such a check are in
**r150** (6, it is the placing step), **r160** (1), **r200** (2), **r240** (2) and
**r300** (2). Defer only the checks that name a figure, not the whole block: the
rest of each verification is about text and must pass at pause 2 like any other.

Run every other gate. An agent that treats its own correct output as a failure
will keep working past the hand-off and start inventing figures.

### Keep `WORKFLOW_ERRATA.md` from the first confusion onward

The build is also a test of these files, and step 340 is where it reports.
**Its entries are written the moment the confusion happens, not at the end** --
once you have worked out what a rule meant you can no longer reconstruct what you
thought it meant, and that misreading is the finding. Signed off last; started
the first time a rule does not say what you need. See `r340_workflow_errata.md`.

Record the cost too -- wall-clock, and how many commands it took to recover.
Nobody can recover that number afterwards, and it is what ranks the fixes.

### If you are blocked, escalate to the ORCHESTRATOR, never to the owner

Giving up is allowed and is useful information. Say what you tried, which rule
sent you there, and what was missing. The orchestrator either tells you to carry
on -- the instructions were sufficient and you stopped early -- or fixes these
files and points you at the change. **The owner is interrupted at the two pauses
and for nothing else.**

## THE CHAIN'S FIRST ACTION — ask which binding, and which pages are which paper

**Before step 005 grades anything — before a scan is opened, before an output
directory is made — the operator is asked two questions about the physical
copy.** They are the first thing that happens in an issue build.

**`first_action()` lives ONLY in `r005_masters_sheet.py`.** The spread variant
has none, and this is a trap, not a detail: with `binding` absent — which is
the prescribed starting state, since `r000_issue.py` leaves it absent so 005
can ask — the only variant that can ask is the sheet one, and for a clip-bound
issue it answers *"this belongs to r005_masters_sheet"*, which is wrong.
`r005_masters_spread.py` refuses to load at all on an absent `binding`. Found
on 8611.

So for a SPREAD issue the two questions are answered before 005 is run at all,
as follows.

| question, in the owner's terms | descriptor key | what it decides |
|---|---|---|
| **How is this issue bound?** A3 sheets held with **clips**, or A4 sheets torn off a **glued** spine? | `binding` | the **edge maths** — which variant of step 005 runs |
| **Which pages are printed on which paper?** the good white stock, or the cheap interior stock? | `paper` | the **grade** — which colour profile makes each page |

This is the **only** thing step 005 refuses over. Everything else it publishes
and notes: parity, skew residual, page class, canvas fit, every number the grade
reports. Those are defects of a page, visible to a human in the artefact it
published. These two are neither defects nor measurements — they are decisions
only the owner can make, with the copy in hand, and **guessing either produces a
plausible-looking wrong result that no downstream check can see.**

### 1. `binding` — clip-bound or glue-bound

```
"spread"   CLIP-BOUND -- A3 sheets held with clips. The frame holds a facing
           pair; the inner edge is the facing page's colour boundary, with the
           clip holes as the fallback, and the holes get inpainted.
           -> r005_masters_spread          (8609 and the monthlies)
"sheet"    GLUE-BOUND -- A4 sheets torn off a glued spine. The frame holds one
           loose sheet; there is no facing page and no clip hole, and the inner
           edge is a torn fringe (verso) or a flush cut (recto).
           -> r005_masters_sheet           (SH8601)
```

The field is not new — `r000_issue.py` has validated it against that closed set
all along, and the VARIANTS section below is built on it. What was missing is
that **nothing asked for it**: an absent or wrong value picked the other
variant's edge maths in silence, and the other variant traces the facing page's
outer edge as this page's inner one, or hunts a torn fringe on a sheet that has
none. So `binding` is now optional in the *loader* — precisely so that step 005
gets to ask the question rather than the loader dying with "missing binding" —
and present-but-wrong is still fatal on the spot.

### 2. `paper` — which pages are on the good stock

**A magazine issue is not printed on one stock, and one white point cannot serve
two.** The separation works in the density domain, `d = -log10(rgb/W)`, so `W`
is the reference every tone is measured against. Grade a good white sheet
against a profile measured off yellowed paper and every light tone is reported
as carrying **less ink than it does** (highlights clamp to zero), and mid-tone
hue skews, because each channel is normalised by a differently wrong number.

The measurements this rule came out of, from SH8601:

- The whole issue was graded with **one** profile, measured off the **interior**
  stock: `W 209 175 157` with `LC 5 100 / LM 4 100 / LY 5 100 / LK 3 100`. That
  white point is the *yellowed 5th percentile* of the interior paper, chosen to
  stop yellow corners. Right for 144 pages.
- The interior is cheap paper that was **yellowish-grey when new** and has
  browned further. The **cover** is a folded A3 wrapper on high-quality stock —
  pages **001, 002, 147, 148** — and pages **149–152** are a bound-in Zahlkarte
  on high-quality white card.
- On those eight pages the profile is wrong, and step 005 **already said so**
  every run: they are the eight that take the ink-vs-bed edge finder, because a
  coated white sits 100+ city-block from that `W` and the paper mask cannot see
  them as paper at all. p151 (Zahlkarte) reported **ink kept 0.36, dark contrast
  91** on a master that is excellent by eye. The code's own note said the fix
  was *a second measured profile for that stock — a decision, not a looser
  constant here.*

**The decision:** two classes, one profile each, chosen per page.

| class | what it is | profile |
|---|---|---|
| `high` | white stock that was white when new — a cover wrapper, a bound-in card or insert | the **built-in anchor set**: `W 201 195 188, C 38 140 165, M 192 37 66, Y 201 159 61, K 16 17 17` and its overprints, with identity levels |
| `low` | the cheap interior stock, yellowish-grey from the start | the issue's **measured** `colors.txt` |

In the descriptor, `issues/<ID>/issue.json`:

```json
"binding": "sheet",
"paper": {
  "high": null,
  "low":  "/Users/mist/DNB/SH8601/master_2400/SH8601/colors.txt",
  "high_pages": [1, 2, 147, 148, 149, 150, 151, 152] }
```

- `high` / `low` — a path to a `colors.txt`, or `null` meaning **the built-in
  anchors with identity levels**. `null` is an answer, not a gap; a path that
  does not exist is a loud error rather than a silent fallback.
- `high_pages` — the printed page numbers on the good stock, 1-based, cover
  counted as 1. Everything not in the list is `low`. It is a **list and not a
  measurement** on purpose: the paper mask is blind to the other stock, which is
  the same fact that makes the grade wrong there, so there is nothing to defer
  to. `r000_issue.py` validates all of it loudly — unknown key, wrong type, a
  page outside `1..pages`, a duplicate, or a descriptor carrying both `paper`
  and the legacy whole-issue `colors`.

Every artefact step 005 writes stamps `grade-sha` **and** `paper-class`, so a
mixed-stock issue stays auditable: a master is stale when its `grade-sha` does
not match the current grade **of its own class**.

### What the operator gets asked with

The question is not a bare demand. Step 005 measures, on the 150 dpi thumbs and
in about 0.1 s a page, the evidence for answering it: **which pages took the
ink-vs-bed edge finder** (the strongest signal there is — and one-sided, since
it finds only the pages the paper mask is blind to) and **each page's own
white** against the low profile's `W`. It pre-fills `high_pages` from that and
says in the output that it is a guess to be checked against the copy.

Record both answers in `LOG.md` with the rest of step 005's disposition. A
descriptor that already carries them is not asked again — the questions are per
issue, not per run.

## VARIANTS — two programs at one step number

A step can exist in **two mutually exclusive variants** that do the same job for
physically different input. They live at the SAME number, distinguished by a
descriptive suffix on the name:

| file | for | selected when |
|---|---|---|
| `r005_masters_spread` | the scan frame holds a clipped SPREAD (the monthlies) | `"binding": "spread"` |
| `r005_masters_sheet` | the scan frame holds one loose SHEET, torn off a glued spine (SH8601) | `"binding": "sheet"` |

The closed set of legal values lives in `r000_issue.py` (`BINDINGS`), which
rejects a wrong one at load time and leaves an ABSENT one to step 005's opening
question — a typo'd `binding` would otherwise match
neither variant, or worse, be read as the other one.

Both write the identical contract — `<tmp>/masters600/NNN.png`, 600 dpi,
levelled, cut, graded, one per page — so every downstream step reads one
directory and neither knows nor cares which variant filled it.

**The selector is the issue descriptor's `binding` field**, from
`issues/<ID>/issue.json`, read via `r000_issue.py` — and it is **asked for as
the chain's first action** (see above), never assumed. "Never assumed" is not
"never measured": the binding is a fact of the paper and the thumbs show it in
one look, so bring the operator the evidence rather than the bare question.

| on a 150 dpi thumb | `spread` | `sheet` |
|---|---|---|
| inner side | the FOLD, then the neighbour half of the same A3 sheet, in frame | a torn or cut paper edge, backing beyond it |
| on the fold | **6 clip holes**, 3 vertical pairs, ~0.6 mm | nothing |
| foot | the yellow prop, ~7 mm | the bed |
| parity | even page -> neighbour RIGHT, odd -> LEFT | none |

One montage of `thumb/100.png` and `thumb/101.png` settles it. 8611 was
answered this way in about a minute; the operator confirms, they do not
divine it. Exactly one variant runs for a given issue. The other is recorded in `LOG.md` exactly like a kind mismatch,
with `binding` in place of `kind`:

```markdown
## Step 005 (masters_spread) — not applicable — binding

Variant selector: `issues/SH8601/issue.json` → `"binding": "sheet"` → the
`masters_sheet` variant runs. No files touched.
```

### This is NOT the `9b` mistake

The `9b` suffix, and the missing `23`, are why this directory numbers in tens
(see above). It is worth being explicit about the difference, because the two
look alike from a distance and only one of them is allowed:

|  | `9b` — forbidden | a variant suffix — allowed |
|---|---|---|
| what it meant | a step **inserted after** another one, once the numbers had run out | two **alternatives at one step**, one of which runs |
| how many run | both, in sequence | exactly one, chosen by the descriptor |
| why the suffix | there was no free number left | the number is right; the suffix names *which* variant |
| the fix | renumber in tens — done | nothing to fix; this is the intended shape |

A suffix that means "and then also do this" is a numbering failure: insert it at
its own number in tens. A suffix that means "or, for this kind of input, this
one instead" is a variant, and belongs at the shared number.

**The numbering-in-tens rule is unchanged.** Variants do not consume extra
numbers and do not license a `b` step. A third variant of the same step is
another suffix at the same number; a genuinely new step is the next free ten.

Naming: `rNNN_<step>_<variant>` — the step name first so the variants sort
together, the variant last and descriptive. Never `a`/`b`, never a number: the
suffix has to say what the variant is *for*, because the orchestrator picks it
from the descriptor and has to recognise it on sight.



## Where the issue PDF comes from

Step 006 owns it, and **the recipe is not in this directory**: it lives in
`tools/img/issue_pdf/README.md` beside the scripts that implement it —
searchable PDF/A, OCR rendered at 402 dpi, the delivered image 150 dpi
the colour-free pages as 600 dpi lossless JBIG2 and the rest 150 dpi guetzli,
quality binary-searched to land under the 100 MB ceiling -- that mixed build
(`make_issue_pdf_mixed.sh`, `MODE=allbw`) IS the default: on a full issue pure
guetzli does not fit at all, 103.3 MB on 8609 and 103.6 MB on 8610, both at
q84, which is guetzli's floor before the halftone smears. `r006_issue_pdf.md` says when it runs and
what is checked; it deliberately does not restate the recipe, because two
copies of a measured procedure drift.

Two things about its position. It comes **after 005**, because its only input
is the graded masters and re-grading a page makes every PDF page built from it
stale. It comes **before the editorial chain**, because the PDF's text layer
is an INDEPENDENT OCR of the same pages at 402 dpi where step 010 reads 300 —
and `issue_pdf`'s README records the measurement that at 300 dpi tesseract
truncates words at the image edges. Where the corpus shows a column-edge
truncation, that text layer often has the word.

### The one page a human always makes

The cover is cut and graded by step 005 like every other page, and then the
issue owner makes a cleaned-up `title.png` **at 150 dpi** from it by hand.
That single file serves twice: it is the cover the site shows, and it is
**page 1's image in the issue PDF** — not re-derived from the master, but used
as the 150 dpi master for that page. Every other page of the PDF comes
straight from step 005.

Step 006 therefore waits for it. A PDF built without it disagrees with the
published cover about what the cover looks like.

## The chain, and what the numbers used to be

The scan-to-corpus steps and the issue-build rules were two chains that met at
the `.md` with no shared vocabulary. They are one chain now, numbered in tens.
`LOG.md` entries in `issues/8607` and `issues/8608` name the OLD numbers and
were deliberately **not** rewritten — they record what was actually run. Read
them through this table.

| now | was | step |
|---|---|---|
| 005 | — | masters — the raw scan to the 600 dpi masters (variant by `binding`) |
| 005b | — | a4_window — the A4 crop, anchored on the 64'er logo (see r005_a4_window.md). **`sheet` only**: a `spread` issue's step 005 already writes the exact A4 window |
| 006 | — | issue_pdf — the searchable issue PDF, built from those masters. **Blocks on a hand-made `title.png`** — see below |
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
| 145 | — | extract_figures — **DISABLED** 2026-08-22. Do not run it; its `LOG.md` disposition is `not run — disabled` |
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
| 325 | — | read_for_sense (added 2026-08, SH8601) |
| 340 | — | workflow_errata — what these rules got wrong, written while it hurt. **Kept from the first confusion onward, signed off last** |

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
- Tool / dependency setup — run it inline, **without asking**. A missing
  tool is not a decision to escalate: `brew install <formula>`, `pip install`
  into the repo `.venv`, `cargo build --release` in `tools/img/*`. The user
  has standing permission for this (stated 2026-09-21, after `guetzli` —
  which `tools/img/issue_pdf` needs — had stopped a step for want of one
  command). Do it inline rather than in a sub-agent so the output is visible,
  say which version landed, and carry on. What still goes to the user is a
  tool that is not installable (a licence, a login, a missing input file),
  never the install itself.

The trigger for sub-agent dispatch is an **editorial** rule (040 onward) under
`tools/img/scan2ocr/rules/`. Program steps (010-030) the orchestrator runs
itself. Anything outside that directory is at the orchestrator's discretion.

## Verification rules mandatory

Every rule `.md` in this directory **must** include a `## Verification`
block with at least one runnable check. Without it, the orchestrator
has nothing to validate the sub-agent against. If you're writing a new
rule, write the verification block before the procedure section — that
forces clarity about what "done" means.

**A check that names a specific issue is a WORKED EXAMPLE from that issue, not a
command to run.** Thirteen of them across r060, r070, r080, r120 and r140 say
`issues/8607/…`, with expected values -- "expect 0", "~90+" -- measured on 8607
and true of no other issue. Substitute the issue you are building before running
one, and read its expected value as "this is what it looked like there", never
as a target for your own. Pasted verbatim, such a check reports on a finished
issue and passes while saying nothing about yours.

The verification block should:
- be runnable as shell (with `python3 -` heredocs where useful);
- exit non-zero or print a clearly flaggable result on failure;
- be cheap enough that running it after every sub-agent dispatch is
  acceptable.

### And the WRAPPERS are code, so run them

A `.sh` in this directory gets edited like prose and committed like prose,
and it is neither. Three ways it bit on one afternoon, all in one commit that
was read carefully and never executed:

- a `LANES=$("$PY" …)` line inserted **above** the `PY=` that defines it —
  `bash -n` passes, because the syntax is fine; the run dies in one second
  with `: command not found` and `xargs: -P : invalid`
- `$(basename "$0")` in a message, which is the caller's name, not the
  script's, whenever the header is sourced or piped
- `PY="${PYTHON:-python3}"` in two of the three wrappers, where bare
  `python3` has no numpy — a pre-existing trap that only surfaced when
  something finally ran the header

> **`bash -n` is not a test. Run the thing.** For a wrapper whose body is a
> long job, run its HEADER — everything above the first `seq`/`xargs` — and
> look at what it prints:
>
> ```sh
> sed -n '1,/^seq /p' rNNN_step.sh | sed '$d' | bash
> ```
>
> It exits 0 and prints the lane line, or the edit is not finished.

### A CHECK IS RUN BOTH WAYS BEFORE IT SHIPS

Against a file you know is **good**, and against one you know is **bad**. Not
one or the other. A check written from a defect and never run on a clean file
fails on correct output; a check written from a clean file and never run on a
defect passes everything.

This is not a theoretical risk: seven shipped, trusted checks were found
broken in one issue's build. They had five recognisable shapes — compare yours
against them:

- **a comparison that can never be true**: an awk field split landed on the
  data's own separator, so the test became `"bbo" < 350`, a string comparison.
  Zero hits on every page of three issues.
- **flagging by-design output as a defect**: every `<pre data-filename=…>` is
  empty on purpose; the check called each one an error.
- **a single-line grep against beautified HTML**: step 080 runs js-beautify,
  so markup the check expects on one line never is.
- **counting the whole file after the transform learned to skip part of it**:
  the transform started skipping fenced code; the check did not.
- **a threshold above its own documented calibration**: a finder shipped at
  1.40 against a docstring worked example of 1.35, and found nothing all issue.
- **a GNU flag that means something else here**: `grep` on this machine is
  ugrep, where `-Z` is `--fuzzy`, not NUL-output. `grep -rlZ … | while read -d
  ''` therefore looped zero times on every issue. Use `--null`, and prefer the
  long flag whenever the short one is doing something structural.
- **a tag pattern that matches a longer tag**: `<p[^>]*>` matches `<pre>`,
  because `[^>]*` eats the `re`. A sweep for code-in-paragraphs built on it
  reported every correct `<pre>` listing as a defect, and the corpus counts
  taken with it measured `<pre><code>` while claiming to measure `<p><code>`.
  Match the tag exactly: `<p(?:\s[^>]*)?>`.

**A check that fails on a good result is worse than no check**, because it
gets "fixed" by undoing the transform — that is how a corrected bug returns.
A check that never fires is worse still: it reports success, and an agent
writing "0 candidates" is telling the truth about nothing happening.

So: keep a known-bad fixture, or reconstruct one (`git stash` is forbidden —
copy the tree, or read the file out of an earlier commit). Plant a fault if
you have no natural one. **Say in the report that the check was seen to
fail**, not only that it passed.

### A check that matches MARKUP also matches comments ABOUT markup

An HTML comment explaining `<div class="q">` contains `<div class="q">`, and
every grep-based count over the file sees it. On 8611 a sub-agent's own
explanatory comment hid one excerpt from `r200`'s section count until it
noticed and reworded. `r270` learned this once already. Strip comments before
counting, or write the comment without the literal markup.

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
2. **`ls` every file the summary says it wrote.** A report that names an
   output is a claim, not evidence. On SH8604 a 160 sub-agent reported
   recording two `reviewed/` baselines with `R.record` — naming both paths,
   and quoting a re-run that said "all previously reviewed" — and neither
   file existed anywhere, in the repo or under `<tmp>`. Nothing downstream
   notices: a missing baseline reads as an empty one, which is exactly what a
   first run looks like. Check the path, and check the mtime.
3. Run the rule's `## Verification` block in the main session.
4. Read a few sample touched files (3–5 is usually enough).
5. Diff `git status --short` against the expected set of changes:
   files that should have been touched, and only those.
6. Report to the user with: sub-agent summary + verification result
   + suggested next action (commit / re-dispatch / decision needed).

## Commit & staging discipline (MANDATORY)

Two real incidents on the 8608 build trace to loose staging:
a rename-only commit that silently dropped four files' content edits
(the `git mv` staged instantly, the content edits never got staged and
were lost until re-applied), and 25 image crops swept into an unrelated
commit by `git add -A`. Both are preventable:

1. **Never `git add -A` / `git add .` during an issue build.** Stage by
   **explicit pathspec** of the rule's expected file set. Several rule
   scripts self-stage (`r060_md_to_html.sh`, `r070_html_cleanup.sh`,
   `r080_split.sh`, `r100_toc_category.sh` run `git add`/`git rm`), so the index may already
   be partly populated when you arrive — reconcile it deliberately, per
   file, before committing.

   **When TWO agents share one working tree, an explicit pathspec is not
   enough — commit by pathspec too.** The index is shared, so a rule script
   that `git add`s its output and a supervisor that commits a rule change
   land in the same commit, whichever of them runs `git commit` first. It
   happened three times on the 8611 build; on the third,
   `issues/8611/8611.html` — step 060's output, staged by its own script —
   went into a commit about r040 and r050's verification blocks.

   ```bash
   git commit -m "…" -- path/one path/two     # ignores the rest of the index
   ```

   **And a dispatched agent NEVER runs `git stash`.** It is the one git verb
   that reaches outside its own file scope by design: `git stash` takes the
   WHOLE working tree, including the other session's uncommitted work and
   your own edits to files the agent was never told about, and a
   `git stash pop` that hits a conflict leaves them half-restored. On 8611 a
   helper sub-agent ran `stash … pop` around its work while two sessions were
   writing; it happened to be clean, and it was luck rather than design.

   Nor `git checkout -- .`, `git restore .`, `git reset --hard`, or
   `git clean`. An agent that wants a pristine file reads it from `HEAD`
   (`git show HEAD:path > /tmp/…`) and leaves the tree alone. Put this in the
   dispatch briefing; the agent cannot infer it from the rule it was given.

   A pathspec commit takes those paths' working-tree content and leaves
   everything else staged for whoever staged it. `git add -A && git commit`
   is the exact opposite and must not be used by either side.
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

## Cross-cutting rule: AN AGENT CAN BE STOPPED MID-STEP — LEAVE NOTHING STRANDED

A sub-agent can be halted by the harness at any moment, with no report and no
warning ("no safety verdict for 10 responses in a row" is one way). You cannot
prevent it. Make it harmless instead:

- **The parent commits per ITEM, not per batch.** This is the whole difference.
  A stop during 8611's step 290 left three files edited, unverified and
  unattributed; a stop during the r190 pass left a clean tree, because each
  finished item had already been verified and committed.
- **A stopped agent's edits are UNVERIFIED — assess them, never assume them.**
  Read each against the brief and keep, or take a `git show HEAD:<path>` copy
  and redo. One of 8611's three was wrong against corpus precedent.
- **Never recover with `restore`, `checkout`, `reset` or `clean`.** The tree is
  shared: it may hold another agent's uncommitted work. Recover file by file.
  (`git stash` is already forbidden, for the same reason.)
- **When the harness starts refusing tool calls, stop calling gated ones.**
  Reading and searching need no verdict and keep working. Every retry of a
  blocked call spends one of the attempts before the hard stop, so a retry loop
  guarantees the stop it is trying to avoid.
- **Prefer one script over forty small commands.** Each call is an opportunity
  to be stopped, and a sub-agent that greps forty times has forty of them.

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
   oddity, or a deferred decision writes it to `LOG.md`.

   **A finding belongs to the step that FOUND it, not the step that will
   use it, and it is written down the moment it is found.** The steps that
   read a page — 080 with the scans and the annual index, 130, 170 — see
   things that only matter at 210, 220 or 280, when the page is no longer
   in front of anyone. On 8611: step 080 found that the p65 banner prints
   two lines and that the second, "Tips und Tricks zu Vizawrite (11)",
   makes this article part 11 of a series running since 8601 — a fact 220
   needs and cannot rediscover, because by then the evidence is a crop
   nobody is looking at. It also found the printed index gives "ProDisc im
   neuen Kleid" as p69 where the article is on p89, which only 220 can act
   on. Both went into `LOG.md` with the page and the evidence, at 080.

   A finding carried in someone's head, or in a message, is a finding lost.

   **And `LOG.md` is git-ignored, so it does not reach the next issue.** It
   is the audit trail for THIS build: what was found, what was decided, what
   is still owed. A decision that will recur — the same judgement call the
   next issue and the one after will face — belongs in the RULE, with the
   issues that made it. 8609, 8610 and 8611 each resolved the
   Wettbewerbe-versus-Listings category of a merged "Listing des Monats"
   independently, from evidence, identically, because the answer lived only
   in three ignored files. It is in `r100` now. At issue end,
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

## Cross-cutting rule: CHECK THE TOOLCHAIN BEFORE THE FIRST LONG SWEEP

`requirements.txt` at the repo root is the **site generator's** list, not the
chain's. A fresh clone whose venv was built from it runs no step of this chain.
The chain needs, in the repo venv:

```
numpy scipy pillow beautifulsoup4 soupsieve      # 005, 010, 020 and the HTML steps
opencv-python-headless                            # r005_a4_window only (binding "sheet")
pikepdf lxml PyPDF2 lunr python-dateutil pytz     # 006 issue_pdf, and generate.py
```

and on `PATH`: **tesseract 5.x with `deu`** (010), **imagemagick**, **poppler**
(`pdftoppm`), **ghostscript**, **qpdf**, **vice** (`petcat`, step 120), and a
**rust toolchain** to build `tools/img/cmyk_reconstruction` (005).

One command answers the whole question, and it belongs in the hour before a
sweep starts, not in the step that needs the import:

```bash
.venv/bin/python -c "import numpy,scipy,PIL,bs4,cv2,pikepdf,lxml,PyPDF2,lunr,dateutil,pytz; print('venv OK')"
for t in tesseract magick pdftoppm gs qpdf petcat cargo; do printf '%-9s %s\n' $t "$(command -v $t || echo MISSING)"; done
tesseract --list-langs | grep -qx deu && echo 'deu OK' || echo 'deu MISSING'
```

**Why before, and not when it fails.** The missing import is usually not at the
step that stops. MEASURED 2026-10-01, importing 8612 on a second machine: that
venv had five of the twelve packages, and because `cv2` is needed only by
`r005_a4_window` — which a `spread` issue skips — nothing would have noticed
until step 006, about **15 h** into the 005 sweep. The check above took seconds.

**A toolchain can also look absent when it is present.** A non-interactive
`ssh host 'cmd'` does not source `.zprofile`, so Homebrew is not on `PATH` and
every `command -v` says MISSING. Export `PATH=/opt/homebrew/bin:$PATH` in the
command, or run it through a login shell, before concluding anything is missing.

## Cross-cutting rule: THE SCAN IS THE ONLY INPUT — everything else is DERIVED

### Where the scans are

```
/Volumes/S/png/<ID>/NNN.png      the scan masters       -> the descriptor's scan_dir
/Volumes/S/png/<ID>/thumb/       150 dpi thumbnails     -> NOT an input. See below.
```

The masters are the input. A `thumb/` directory may or may not be sitting next to
them; it is derived data and the chain re-makes its own -- the descriptor's
`thumb_150` points into `<tmp>`, never here.

VERIFIED 2026-10-01: 47 issue directories, 8405 through 8612 plus the Sonderhefte.
**A master is an A3 sheet at 2400 dpi OR at 600 dpi, and ONE ISSUE CAN BE
BOTH.** Read each page's own resolution from its PNG `pHYs` chunk
(`magick identify -format '%x'`, px/cm x 2.54); never assume. MEASURED on
SH8602: pages 003-162 at 600 dpi (~5029x7188, ~63 MB), the wrapper and the
bound-in card -- 001, 002, 163-168 -- at 2400 (~20300x28751, ~850 MB). The raw
TIFFs are the same, so there is no higher-resolution original to go back to.
`r005_masters.scan_dpi()` reads it and cross-checks the frame height in mm,
because a wrong `pHYs` would rescale every millimetre constant in silence.

A 2400 dpi master runs to about 900 MB, so an issue is
~180 GB and nothing about it is cheap to re-make.

### A `thumb/` you FIND beside the scans is NOT an input — re-derive it

`/Volumes/S/png/<ID>/thumb/` is **derived data sitting in the input directory**,
and it is not trusted. It may not exist, and when it does you cannot tell what
made it. The evidence, on the scan volume itself:

- **Two generator scripts, and they disagree.** `create_thumbnails.sh` uses
  `convert -resize 6.25%` (Lanczos) and branches by page range because that
  issue's scans were *mixed resolution* -- 25% for its 600 dpi pages, 6.25% for
  its 2400 dpi ones. `create-thumbs.sh` uses `magick -scale 25%`: a different
  scale AND a different filter (`-scale` averages, `-resize` does not).
- **One of them skips files that already exist** ("Thumbnail exists, skipping"),
  so a `thumb/` directory can be a *mixture* of two methods.
- **Neither records which ran.** Nothing in the directory says.
- **They are not always there.** VERIFIED 2026-10-01: 8608, 8610, 8611 and 8612
  have a full set at 16:1; **8505 has 188 masters and no thumbs at all.**

**Why this is not pedantry.** Step 005 measures *skew* on the thumb and applies
that angle to the 2400 dpi master, and the `sheet` variant measures the paper
mask, the parity gate and the **colour pool** on it too. A thumb at the wrong
scale, or made with the wrong filter, does not fail -- it silently levels every
page by a wrong angle and grades it against the wrong paper, and nothing
downstream can see it. Worse, r005's thresholds (`lum > 170`, `max - min < 40`,
the "2-6 levels" validation) were measured on **8610's** thumbs, i.e. on one
particular filter at one particular scale. They do not transfer to a set made
the other way.

**So: if a step needs thumbs, the chain makes its own**, into `<tmp>/thumb150/`,
and the descriptor's `thumb_150` points THERE and never at the scan directory.

```bash
# Derive the thumbs this build will use. -scale, NOT -resize: see below.
mkdir -p "<tmp>/thumb150"
for m in <scan_dir>/[0-9][0-9][0-9].png; do
  # SCALE BY THE PAGE'S OWN dpi, never a fixed 6.25%. A MASTER IS 2400 dpi OR
  # 600 dpi, and an issue can be both: SH8602's interior (003-162) is 600 and
  # only its wrapper is 2400. Run verbatim with 6.25%, 160 of its 168 thumbs
  # came out 317x449 px -- 37.5 dpi, not 150 -- and step 005 could not run.
  d=$(magick identify -format '%x' "$m" | awk '{printf "%d", $1*2.54+0.5}')
  magick "$m" -scale $(awk "BEGIN{printf \"%.6f\", 150/$d*100}")% \
    "<tmp>/thumb150/$(basename "$m")"
done
```

**`-scale`, and the choice is measured, not stylistic.** The ratio is
`150 / the page's own dpi` -- 6.25% at 2400, 25% at 600 -- but the *filter*
decides the pixel values, and r005's thresholds
(`lum > 170`, `max - min < 40`) are pixel values. Compared against the thumbs
actually sitting beside the scans, on 8612 p050:

| derivation | mean abs diff | max |
|---|---|---|
| **`-scale 6.25%`** (16x16 box average) | **0.00** | **0** |
| `-filter Box -resize 6.25%` | 0.49 | 9 |
| `-filter Triangle -resize 6.25%` | 2.58 | 41 |
| `-resize 6.25%` (default Lanczos) | 2.77 | 39 |
| `-sample` / `-filter Point` | 7.54 | 101 |

`-scale` is byte-identical -- VERIFIED on 8612 p002, p050, p150 and on **8610
p050, the issue r005's numbers were measured on**. So this derivation reproduces
exactly the set every constant in r005 came from, and the constants transfer
unchanged. Plain `-resize` would have moved a third of the pixels by more than
two levels and up to 39, against a threshold whose window is 40 wide.

**THE NAME VARIES, THE RULE DOES NOT.** This is written about `thumb/`, but
what is actually beside the scans differs per issue: `thumb/` on 8612 and
SH8601, **`thumbs/` on SH8602**, plus `widths.txt`, `widths_debug.txt`,
`widths_preview/`, `rotate.log`, `thumbs.log`, `colors.txt`. **Every derived
artefact you find in the scan directory is untrusted, whatever it is called.**
Do not match on the name `thumb`; treat anything that is not a `NNN.png`
master as something a previous tool left behind. Re-derive what you need.

A thumb a build DERIVED is reproducible; a thumb it FOUND is an artefact of
whichever script ran last. The point is not that the found ones are wrong today
-- for 8612 they are identical to what this command makes. The point is that
you cannot know that without checking, and the check is the derivation.

**Then verify:** one thumb per master, no orphans either way, and every thumb's
width and height within **1 px** of its master's / 16 -- per page, because page
widths vary within an issue (8612 runs 20485 to 20862 px) and a set made from
different scans will not track them. Do NOT test for equality: masters are not
multiples of 16 and `-scale 6.25%` rounds to nearest, so a 20485 px master gives
a 1280 px thumb, not 1281. `ceil(w/16)` reports 9 false mismatches in 8612's
first ten pages; the 1 px test reports 0 of 200.

**NEVER WRITE INTO `/Volumes/S/png/`. Nothing stops you** -- the volume is
writable and the files are not mode-locked; the only thing protecting the only
irreplaceable input this project has is that you do not do it. Derived data goes
under the descriptor's `tmp`. If a step seems to want an output beside its input,
the step is wrong.

### Everything else, the chain made

**The chain has ONE input: the scan masters** (2400 dpi or 600 dpi; see above). Every other file it
reads, it made -- `masters600`, `sheets600`, `cmyk2400`, `geometry`, the OCR
blocks, the article HTML, the issue PDF -- or it is already in the repo, put
there by an earlier issue's run of this same chain.

There is no second input and no exception. A step that appears to need one is
either reading something derived (it is under `<tmp>`), something a previous
build published (it is under `issues/`), or a reference whose location that
step's own rule gives you -- r120's disk archive, the README's release table.
None of those is an input to the chain; they are places the rules already name.

**So a path in these rules that points outside the scan directory, the issue's
`<tmp>`, and the repo is a FOSSIL.** Earlier versions of this chain put derived
data in other places, and when the chain changed the data moved and the sentence
did not. Found 2026-10-01, all dead:

| rule | pointed at | what it is now |
|---|---|---|
| r150, r160 | `/tmp/64er_<YYMM>_pages/`, `/tmp/64er_<YYMM>_full.txt` | `<tmp>/masters600/NNN.png` and this issue's own OCR |
| r160 | `~/DNB/<YYMM>/<YYMM>-cmyk/600_cropped/<NNN>.tiff` | `<tmp>/masters600/NNN.png` — same page, already deskewed and cut |
| r130 | `issues/<YYMM>/64er_*.pdf`, `issues/<YYMM>/png/` | `<tmp>/masters600/NNN.png` and `<OUT_DIR>/blocks/pNNN.txt` / `NNN.labels.json`. Neither input exists during a build: the PDF is made at 006, after PAUSE 2, and there is no `png/` at all |
| r300, r330 | `~/DNB/64er_OCR/OCR-YYYY_MM_64er[_HIRES].pdf` | **gone.** For another issue use the repo's own `issues/<YYMM>/64er_19XX-XX.pdf`, or its scans |

**What to do when a path in a rule does not exist.** Do not hunt for it and do
not invent a replacement. Ask which of these it is:

- derived by this chain -> it is under the issue's `<tmp>`, and the rule naming
  anywhere else is stale. `masters600` is the page image (see the rule below);
- a *previous* issue's work -> it is in the repo, under `issues/<YYMM>/`;
- the scan -> the descriptor's `scan_dir`.

Then **record it in `WORKFLOW_ERRATA.md` and carry on** -- do not edit the rule
yourself mid-build. Editing a rule while running it means a later step reads
something different from what an earlier step did, and the record of what
actually went wrong is gone. The orchestrator harvests the errata into these
files **when the build is finished and `WORKFLOW_ERRATA.md` is complete**, never
during -- the same reason, and it does not care who holds the pen. The one
exception is a defect that BLOCKS the build: that is fixed at once, pushed, and
pointed out to the runner, and it is recorded in the errata as having moved
under the build. See r340. (If you are running without an orchestrator, fix it in the same
change as the work; a fossil path costs every future agent the same half hour.)

## Cross-cutting rule: the working directory must be DURABLE

`<tmp>` is the issue descriptor's `tmp`, and everything under it is derived --
masters, separations, OCR, geometry, overlays. Derived is not the same as
disposable:

- **Never under `/tmp` or `/private/tmp`.** Two independent reasons. (a)
  Leptonica rewrites a path beginning `/tmp/` to `$TMPDIR` and tesseract then
  cannot open step 010's work files at all (`FINDINGS.md` section 12);
  `r000_issue.py` refuses such a descriptor. (b) macOS deletes files under
  `/private/tmp` that have not been accessed for three days -- on 8610 that ran
  mid-chain and took `sheets600` 200 -> 11, `masters2400` 200 -> 10,
  `cmyk2400`, `geometry` and the assembled `<ID>.md` with it.
- **What losing it costs.** On 8611 (192 pages, lanes sized by the rule
  below): step 005 **1 h 46 on 11 lanes**, step 010 **78 s on 28**. On 8610
  (200 pages, a hardcoded 6 lanes everywhere): step 005 ~4.3 h, step 010
  ~30 min. Step 020 is ~15 min and one model call a page either way, since it
  is not sized by this machine. Nothing shippable is lost -- the repo holds
  every deliverable -- but a sweep you did not plan is still hours.

  **A timing figure in these files states its page count, its lane count and
  its date, or it is worse than nothing.** r010 carried "~15 minutes for 176
  pages" from the 6-lane era into a run that took 78 seconds, and a reader
  budgeting from it would have been out by a factor of ten.
- Put it beside the scans on a volume nobody cleans, e.g.
  `/Volumes/<disk>/tmp/<ID>` or `~/DNB/<ID>/tmp`, and say so in the descriptor.
  8610 stays at `/private/tmp/64er_8610` by the user's decision, knowing the
  cleaner: that is a choice to re-run, not a default to copy.

**`$TMPDIR_ISSUE` is the shell spelling of `<tmp>`. Export it once, at the top
of the run, and every `<tmp>` in these files is that variable:**

```bash
export TMPDIR_ISSUE=$(.venv/bin/python -c \
  'import json,sys; print(json.load(open("issues/'"$ISSUE"'/issue.json"))["tmp"])')
[ -d "$TMPDIR_ISSUE" ] || { echo "no <tmp> for $ISSUE"; exit 1; }
```

r190's Verification and r060's keep-a-copy both referred to `$TMPDIR_ISSUE`
with **nothing anywhere defining it** (SH8603: both 190 sub-agents substituted
their own scratch dirs, and two parallel parts would have collided on one
path had they not). A variable two rules read and no rule writes is a path
that silently resolves to the filesystem root. Export it, or run the steps
that use it from an environment that has.

## Cross-cutting rule: PARALLELISE TO HALF THE FREE RAM

Every step that fans out over pages locally — 005 masters, 010 OCR, 145 figure
extraction — sizes its lanes the same way, and none of them may hardcode a
number:

> **As many lanes as fit in HALF the free RAM, capped at cores − 4.**

**ALWAYS.** There is no step, no machine state and no deadline that exempts a
fan-out from this. FREE means free *at the moment the step starts*, read then,
never carried over from an earlier step in the same build — this box regularly
carries a **170–290 GiB model server** for another user, which appears and
disappears between steps.

Ask for it, never write it down:

```sh
LANES=$("$PY" -c 'import r000_issue; print(r000_issue.lanes(19))')
```

The one argument is **that step's measured peak for one lane**, in GB. It is
the only number worth arguing about and the only one a caller supplies.

**Half, and not all.** The other half is the margin that keeps a long run off
the swap when something else on the machine wants memory part-way through, and
a run that starts swapping is slower than one that never grew. The owner's
rule, stated 2026-09-27.

**Why it is asked and not written.** This box ran both ways inside one
afternoon: with a 350 GB model server resident — 116 GB free, memory-bound,
6 lanes was right — and then without it, 386 GB free, core-bound, 10. Any
constant in a `.sh` would have been wrong in half the day. The hardcoded
`-P 6` that all three steps carried was written when it was true and left
**26 of 32 cores idle** for two hours once it was not.

**The neighbour on this box is not just memory.** `~/DNB/llm/CLAUDE.md`
records that 32 concurrent `magick` processes drove the load to ~975 and the
inference watchdog killed the server; on 2026-08-05 a comparable load panicked
the machine outright, because the compositor missed its kernel check-ins while
the GPU was held. The lane count from this rule is what keeps that from
happening — a step that sizes itself by RAM also sizes itself by cores, and the
`cores − 4` cap is not decoration.

**`OMP_NUM_THREADS=1` stays.** It is what makes a lane exactly one core:
numpy and ImageMagick both thread by default, and two layers of parallelism on
one box contend instead of adding. Lanes are the only parallelism.

### Measuring a lane's peak

Run the step, and while it runs:

```sh
ps -axo rss,pcpu,comm | sort -rn | head
```

Take the largest steady RSS **per lane**, counting every process a lane owns at
once. MEASURED for 005 on 8611: **~19 GB** — python holding the 2400 dpi sheet
(~14 GB), or, while it waits on the separator, python idle (~9 GB) *plus*
`magick`'s own copy (~9 GB). ImageMagick at Q16 HDRI holds a 590 Mpx
4-channel page at 8 bytes a channel, which is where its share comes from.

**010 and 145 are still guessing at 3 GB.** That is a placeholder, not a
measurement; take the real number off the next run and put it in.

### NOT for model-call steps

020 classify, 020 evaluate and 145 judge fan out over **model calls**, and they
are bound by rate limits and by the credential race in `r000_llm.py` — four
concurrent processes sharing one OAuth file once took out pages 84-176 of an
overnight run. Their `LANES = 4` is a different constant answering a different
question. Leave it alone.

## Cross-cutting rule: PREFLIGHT the free space, before step 005

Step 005 is the only step that writes at the scan's full resolution, and the
footprint depends on that resolution. For a **2400 dpi** page it is ~**2.25 GB**
— `masters2400/NNN.png` plus `cmyk2400/NNN.tif` — so a 200-page monthly is
**~450 GB**, arriving over four hours with no check of its own. Running out at
hour three loses the sweep, not just the page.

For a **600 dpi** page it is roughly **1/16 of that**: there is no
`masters2400/NNN.png` at all (at 600 dpi the full-resolution render IS
`sheets600`), and `cmyk2400/NNN.tif` is written at the scan's own resolution.
So budget per page, not per issue — SH8602's 160 interior pages at 600 dpi and
8 wrapper pages at 2400 cost a fraction of what the formula below assumes.

So before dispatching 005:

```bash
ISS=$($PY -c 'import r000_issue; from r000_issue import ISSUE
i = r000_issue.load(ISSUE); print(i.tmp, i.pages)')
set -- $ISS
df -g "$(dirname "$1")" | tail -1         # free GB on the volume holding <tmp>
# Per page, at that page's OWN resolution: a 600 dpi page costs ~1/16 of a
# 2400 dpi one, so a fixed per-page figure over-books a mixed issue badly.
$PY - <<'BUDGET'
import glob, os
from PIL import Image
import r000_issue
Image.MAX_IMAGE_PIXELS = None
iss = r000_issue.load(r000_issue.ISSUE)
per = {2400: 2.25, 600: 2.25 / 16}          # GB per page, measured
tot = {}
for f in sorted(glob.glob(os.path.join(iss.scan_dir, "[0-9][0-9][0-9].png"))):
    with Image.open(f) as im:
        d = round(im.info.get("dpi", (0, 0))[0])
    d = min(per, key=lambda k: abs(k - d))
    tot[d] = tot.get(d, 0) + 1
print("budget: " + " + ".join("%d pages @%d dpi = %.0f GB" % (n, d, n * per[d])
                              for d, n in sorted(tot.items())) +
      "  ->  %.0f GB total" % sum(n * per[d] for d, n in tot.items()))
BUDGET
```

**Then make it a measurement, not a constant.** The profile gate already
renders three real pages before the four hours (`r005_masters_spread.md`,
*The gate*). Read the footprint off those three instead of trusting the
number above — different page count, different ink coverage, different
compression:

```bash
du -sm <tmp>/masters2400 <tmp>/cmyk2400   # after the 3 gate pages
```

### When it does not fit

**The 2400 dpi artefacts are ARCHIVE. Nothing after step 005 reads them.**
Verified by grep over every rule: 010 OCRs `masters600`, 145 cuts figures
from `masters600`, `sheets600` is the uncut 600 dpi sheet `cut` re-reads,
and `masters2400` / `cmyk2400` appear nowhere outside `r005_masters_*.py`.
Everything the rest of the chain needs is the 600 dpi tier, which is
roughly **1/40th** of the total.

So a volume that cannot hold the archive is not a blocker on the issue:

1. **Stream it off** — after each page, move `masters2400/NNN.png` and
   `cmyk2400/NNN.tif` to wherever the archive lives, or
2. **Do not write it** — the sweep still produces every deliverable.

Either way **say which in `LOG.md`**, because the archive is the only copy
of the separation and "we skipped it" must not be discovered years later by
its absence. What is NOT an option is starting the sweep and finding out.

### The other volume is not the answer

Check the free space on the volume holding the SCANS too before proposing
to move `<tmp>` there. 8610's 200 pages of 2400 dpi source are **159 GB**;
a disk that holds several issues' scans has no room for a working set on
top of them.

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
magick <SRC_DIR>/145.png -crop 2136x574+390+3736 +repage <scratch>/crop.png
```

> ### `text=` IS A 200-CHARACTER PREVIEW. A GREP MISS HERE IS NOT AN ABSENCE.
>
> `r010_blocks_index.py` writes `PREVIEW_CHARS = 200` of each block; `nw=` is
> the block's REAL word count. MEASURED on 8611: **1923 of 6834 blocks are
> truncated, and 104,726 words are in the OCR but not in this file** — a
> quarter of the blocks and most of the text on any page with a long one.
>
> This bit on 8611 p097. The 1541 schematic's explanatory paragraph was OCR'd
> into the diagram as one 331-word block; the index shows its first 200
> characters, which are all component labels, so `grep Reparaturkurs` came
> back empty and the paragraph was reported as never having been read. It had
> been. It was 250 characters in.
>
> **The full text is `<OUT_DIR>/NNN.labels.json`.** Grep that when the answer
> "it is not in the OCR" would change what you do:
>
> ```bash
> $PY - <<'PYEOF'
> import glob, json, sys
> NEEDLE = "Reparaturkurs"
> for f in sorted(glob.glob("<OUT_DIR>/*.labels.json")):
>     for b in json.load(open(f, encoding="utf-8")).get("blocks", []):
>         if NEEDLE.lower() in (b.get("text") or "").lower():
>             print(f.split("/")[-1], b.get("id"), b.get("label"))
> PYEOF
> ```
>
> Rules that grep the index for CONTENT rather than for a bbox — r130's
> caption search, r160's Pass 1 and Pass 3, r170's listing search, and this
> recipe — are all subject to this. Use the index to find *where* something
> is; use the JSON to decide whether it *exists*.

**COORDINATE SPACE -- read before cropping.** The bboxes are in pixels of the
graded **600 dpi master** (`SRC_DIR`), which is deskewed and cut to the
sheet's own traced edges on the issue canvas -- NOT exact A4; that is the
delivered PDF's geometry. They are
**not** in the delivered PDF's page space: the PDF page is neither deskewed nor
cropped, so the two differ by a rotation and an offset. Crop from the master,
never from a `pdftoppm` render. `frac=` is the same box as a fraction of the
page, for cropping a render at any other resolution.

For listings and tables, the caption block tells you the column (X, width W);
the code or table region usually sits **above** it in the same column -- walk
preceding blocks whose x-range overlaps to find its top edge.

Everything under `out/` is scratch -- never commit it.

## Cross-cutting rule: THE PAGE IMAGE IS `masters600` -- the PDF comes last

Every rule that needs to look at a page says so in its own words, and several
still say `pdftoppm -r 300 issues/<YYMM>/64er_19XX-XX.pdf ...`. **While the
issue is being built that file does not exist yet**: the PDF is assembled at
the END, by `tools/img/issue_pdf/`. A rule that renders from it cannot run at
all -- 8610 hit this in nine rules, and every sub-agent had to be corrected in
its dispatch. (Once the PDF exists its text layer is a candidate source, per
the section below; the page IMAGE is still this file.)

The render already exists, and it is better than a `pdftoppm` of the PDF would
be: **`<tmp>/masters600/NNN.png`**, 600 dpi, A4, deskewed, cut and graded by
step 005 -- the same file `r010` OCR'd and `r145` cuts figures from.

```bash
# The repo venv, not bare python3: r010_ocr_blocks imports numpy and scipy,
# which the system python does not have, so `python3` makes SRC silently EMPTY
# and every crop below then fails on "/NNN.png". MEASURED on 8611.
PY=${PYTHON:-.venv/bin/python}
SRC=$("$PY" -c 'import sys; sys.path.insert(0, "tools/img/scan2ocr/rules")
import r010_ocr_blocks as OB; print(OB.SRC_DIR)')     # <tmp>/masters600
magick "$SRC/145.png" -crop 2136x574+390+3736 +repage <scratch>/crop.png
```

- The bboxes in `<OUT_DIR>/blocks/pNNN.txt` are **in this file's pixels**
  (600 dpi), so a crop is the bbox verbatim -- no scaling, no offset. `frac=`
  is the same box for a render at any other resolution.
- **`NNN.labels.json` IS NOT IN MASTER PIXELS, and it says so itself.** The
  sentence above is true of `blocks/pNNN.txt` only. This recipe then sends you
  to the JSON for full text (see *the block index is a PREVIEW*, below), and
  that file's `bbox` is at **300 dpi** -- it carries `"ocr_dpi": 300` and
  `"ocr_size": [2728, 3594]` at the top, against a 600 dpi master of
  5457x7181. Cropping a `labels.json` bbox verbatim from `masters600` lands on
  the wrong region; SH8603 got p164's intro instead of the line it wanted, and
  x2 gave the line.
  MEASURED on SH8603 p001, block 2051, which appears in both files: the JSON
  has `bbox [1089, 920, 1643, 1323]`, and `blocks/p001.txt` has
  `bbox=1108x806+2178+1840` — the same box at exactly twice the coordinates
  (3286−2178 = 1108, 2646−1840 = 806). The factor is 2 for a 600 dpi master
  and **4 for a 2400 dpi one**, which is the reason not to hardcode it.
  So: **read `ocr_dpi` from the file rather than assuming either number**, or
  better, use the `bbox_frac` each block already carries, which is
  resolution-independent and needs no factor at all:

  ```bash
  magick <tmp>/masters600/164.png -crop "$($PY - <<'PYEOF'
  import json
  d = json.load(open('<OUT_DIR>/164.labels.json', encoding='utf-8'))
  W, H = 5457, 7181                      # the master, from `magick identify`
  b = next(b for b in d['blocks'] if b['id'] == 2051)
  x0, y0, x1, y1 = b['bbox_frac']        # not b['bbox']
  print('%dx%d+%d+%d' % ((x1-x0)*W, (y1-y0)*H, x0*W, y0*H))
  PYEOF
  )" +repage /tmp/block.png
  ```
- A lower-resolution look is `-resize 12%` of the same file, never a second
  render of something else.
- **No rule says `pdftoppm` any more.** This paragraph used to end "where a
  rule below says `pdftoppm`, read it as crop `masters600/NNN.png`" — a
  standing override that every sub-agent dispatch had to repeat, which is a
  note about a debt rather than a fix. 8611 hit it again at 090, so the six
  rules that still carried the instruction were changed instead: 090, 190,
  200, 210, 240 now name `masters600` at the resolution each asked for
  (`-resize 25%` for 150 dpi, `-resize 50%` for 300, the file itself for
  600). 170's mention survives because it WARNS against `pdftoppm`, which is
  the point.

## Cross-cutting rule: the PDF's text layer is a CANDIDATE SOURCE, not authority

**Since step 006 the delivered PDF does carry a text layer**, and it is not
the same OCR this chain runs: `issue_pdf` renders at **402 dpi** where step
010 reads **300**, and its README records why -- at 300 dpi tesseract
truncates words at the image edges.

So it is worth consulting and worth distrusting in equal measure. MEASURED on
SH8601 over 38 column-edge truncation candidates, anchored on the preceding
word so a longer form elsewhere on the page could not count: **10 recovered,
7 unchanged, 21 undecidable**. And on p090 it is actively worse -- `--psm 3`
interleaved a tinted box with the surrounding body columns and scrambled the
reading order, so a truncation there would be traded for an unknown
reordering.

Use it to GENERATE a candidate for a damaged word, then confirm that
candidate against the master crop. Never quote it as what the print says.

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

## Cross-cutting rule: CONSISTENCY WITH THE PAGE BEATS CONSISTENCY WITH ITSELF

Where the magazine is inconsistent, **the transcription is inconsistent in the
same places.** Match the page, site by site; do not normalise.

**THE MACHINE NAMES ARE NO LONGER THIS RULE'S EXAMPLE — they are its one
standing exception.** Owner, 2026-10-04: **"space. C 64, C 128, C 16, C 116,
VC 20."** This supersedes the 2026-08 decision for these names only; the rule
itself is unchanged for everything else.

Why the earlier decision did not survive contact with the page: on SH8603 the
body type sets a thin gap that measures neither a closed pair nor a word
space, so "match the page site by site" has no answer to give. r325 part A
alone read the same issue 165 spaced against 99 closed, and 210 had set the
bands closed. An instruction that cannot be carried out consistently produces
inconsistency of our own, which is worse than a house style, because it
masquerades as the paper's.

MEASURED over the published corpus, prose only (`<pre>` and `<code>`
excluded): **spaced 10,312 against closed 393** — `C 64` 5,762/232, `VC 20`
1,897/94, `C 128` 1,739/46, `C 16` 802/16, `C 116` 112/5. The spaced form was
already the archive's overwhelming practice, so this ruling tidies a 4 %
residue rather than overturning anything.

**What it does NOT touch:**

- program text — anything inside `<pre>` or `<code>`, where the string is
  typed in by a reader;
- the index CSVs' titles, which are quoted verbatim and carry `C16/VC20`;
- a filename or an `id`, which are already settled;
- any other `C`-plus-number that is not a machine (`C 64` the note, a column
  label, a formula).

(For the record: this paragraph used to say SH8601 has 344 sites of the
closed-up form. Measured now it has **5**, and the old figure does not
reproduce by any counting I can construct. Do not carry a number forward
without re-measuring it — r000 asks that of timing figures and it holds here
too.)

It follows from the rule this chain already lives by — *typos in print remain
typos in the HTML* — and it costs something real: the published text stays
uneven, and a reader may think we were careless. That is the correct trade. The
archive's claim is that it reproduces what was printed; a house style applied
over the top quietly breaks that claim everywhere it touches, and leaves no
record that it did.

The same reasoning governs `gibt's`/`gibt’s`, `Graphic`/`Grafik`, and any other
pair the paper does not settle: read the page, set what it sets.

**This is not a licence to preserve OUR errors.** A glyph we mis-read is ours
and gets fixed; a form the magazine chose is the magazine's and stays. The test
is always the crop, never the corpus frequency.

## Cross-cutting rule: NO PROCESS NOTES IN ANYTHING THAT SHIPS

Owner, 2026-10-06: **"do not add log messages to shipping code/data."**

Everything under `issues/` is published — the articles, `style.css`, the `prg/`
listings, the PDFs. A comment in any of them is read by a visitor, not by us.
So a shipping file never carries **why we did something, which issue revealed
it, what a check found, or whose decision it was.** That belongs in `LOG.md`,
in the commit message, and in these rule files, none of which ship.

What a shipping comment MAY say is what the thing IS. Compare, in
`issues/style.css`:

```css
--table-shaded: #D6D2B0;   /* a printed grey ground inside a table */   /* fine */
```

against the five-line block I first wrote above the same rule, explaining
SH8604 p46's backtracking table and what typesetting it away would cost a
reader. That is a commit message in a stylesheet. Removed.

**The house style is already there to copy** and it is terse: `/* Colors */`,
`/* light cyan */`, `/* Link Styling */` — 52 comments in `style.css`, none of
them longer than a line, none about history.

This generalises the rule r290 states for HTML comments inside articles
(*the marker is German because the comment is* — say it to the reader, not to
the checker). Same principle, every shipping artefact: a `.txt` listing's `;`
header records the program's errata state, not our reasoning; a PDF's metadata
is the house standard, not a build note.

## Cross-cutting rule: THE ISSUE YOU ARE WORKING ON IS THE SCOPE

Work on the issue in hand. **Do not take on work in another issue unless THIS
issue touches it.**

"Touches it" is a real relationship, not a pretext:

- this issue REPRINTS an article from another one, so the two transcriptions of
  one printed text disagree and the comparison names the error (r330 — SH8601
  fixed 14 such errors in 8510, 8511, 8512 and 8601);
- an erratum in another issue corrects a page THIS issue reprints;
- a shared tool, rule or template that this issue's work has proven wrong.

What does NOT qualify, however tempting: a defect merely *noticed* while working
here, and a corpus-wide gate result. MEASURED: running r310 over the whole
archive reports **327 HARD findings across 33 published issues** — 143 of them
one missing `</html>`, 61 `<li>` wrapping `<p>`, 62 a Discount `<ol type=>` bug.
Most are markup that predates the gate: r310 was written 2026-08-21, and 8409
was published in the repo 2024-08-20. **That is a corpus cleanup project with
its own decision to make, not this issue's tail.**

Report what you noticed, with evidence, and move on. Fixing another issue's
published HTML on your own judgement is the same mistake as fixing the
magazine's typos — you are changing something whose owner did not ask you to.

## Cross-cutting rule: CHANGING A TOOL MEANS MEASURING BEFORE AND AFTER, AND RECONCILING THE DIFFERENCE

**Never change a checker, a detector or a converter without running it both ways
over the same real data and accounting for every finding that appeared or
disappeared.** The delta is the evidence that the change did what you claim; a
new version whose output you have not diffed against the old is an assertion.

Three things the reconciliation must produce, and all three are load-bearing:

1. **The counts, before and after**, on the whole corpus the tool covers — not
   on the example that motivated the change.
2. **An explanation for every difference.** A finding that VANISHED is either a
   false positive correctly removed, or a real defect you have just gone blind
   to. A finding that APPEARED is either a real defect newly visible, or a false
   positive you have just introduced. There is no third case, and "the number
   got better" is not an explanation.
3. **The delta applied.** Newly visible defects get fixed, or recorded with
   their evidence. A tool change that surfaces work and leaves it unrecorded is
   worse than no change.

MEASURED on SH8601, each of these actually happened:

| change | before | after | what the delta was |
|---|---|---|---|
| dump cross-check: hand table -> `da65` | 13 | 13 | *the same 13* — two independent disassemblers agreeing, which is why the swap was trustworthy |
| `da65` symbol lines not skipped | 13 | 63 | 50 phantom mismatches: `L795C := $795C` is a definition, not an instruction |
| indirect addressing added | 25 | 13 | 12 phantom address gaps — `fmt()` raised, the caller swallowed it, `prev` never advanced |
| absolute operands padded | 15 | 13 | 2 syntax-rendering differences, `sta $fb,y` against the monitor's `sta $00fb,y` |
| layout pass on article 125 | 13 | 16 | 2 magazine errors that had been INVISIBLE inside `<p>`, plus 1 real tool fault — holding the count at 13 would have meant re-hiding them |
| bold detector: threshold 1.35 -> 1.50 | 4 found | 3 found | **a false negative**: a genuine `Composite.` at exactly 1.50 was lost, so the change was reverted |
| bold detector: paragraph-initial filter | 10 | 4 | 6 mid-sentence short words; all 4 survivors are the real terms |

Note the sixth row. A change can make the number look better and be wrong:
raising a threshold removed noise AND a real find. **Prefer a false positive to
a false negative wherever a human confirms each hit** — the confirming crop is
cheap, and a defect the tool stops reporting is invisible forever.

## Cross-cutting rule: A CHECK YOU HAVE NOT SEEN FAIL IS NOT A CHECK

**Before trusting any check, prove it can fail.** Run it against data that
should trip it — the pre-edit tree (`git archive HEAD`), a copy with the defect
reintroduced, a deliberately wrong input — and confirm it reports. A check that
has only ever printed "clean" has not been shown to test anything.

This is not caution. It is the single most repeated failure in this chain:
**fourteen separate verification checks have been wrong on first contact with
real data**, each written by someone confident it was right.

| check | what it actually did |
|---|---|
| r180 | name regex excluded a hyphen — 43 false failures |
| r190 | piped through `sort`, which exits 0, so the gate was an unconditional FAIL |
| r150 | filename regex excluded an underscore |
| r160 | counted `<table` inside HTML comments |
| r210 | id list was monthly-only, so `vorwort` never matched |
| r250 | counted comments as tags, and missed `<aside>` entirely |
| r260 | tested the first *letter* against German model numbers (`C 128`) |
| r270 | matched its own explanatory comment |
| r280 | canary string hardcoded from a different issue — 0 hits by construction |
| r300 | `for f in $(grep -rl …)` word-split on filenames containing spaces |
| r310 | flagged an adjudicated printed period it could never clear, so HARD could not reach 0 |
| drop-cap | examined only the first non-intro paragraph, and tested `islower()` alone — found 15 of 17 |
| r330 `verify` | matched dispositions by NUMBER, not text, so a renumbering silently re-pointed 2047 of them |
| cover guard | `magick compare` exits non-zero when images differ, so under `set -euo pipefail` it killed the build with an empty log — plus a threshold on the raw metric (~0.005 of a grey level) and a parse that rejected scientific notation |

The pattern is always the same: the check encodes what its author expected the
data to look like. The data is a 40-year-old magazine.

**Corollary — a gate that always reports the same number stops being read.**
Where a finding is adjudicated and correct as printed, record the adjudication
where the CHECK can see it, not only in LOG.md. Otherwise the count never
reaches zero and nobody looks again.

**Three mechanisms, and this line used to name only the one that was
withdrawn.** It pointed at r290's `PRINTED` comment beside the heading — which
r290 itself retired, because a rule saying "put this English token in a
comment" is a rule saying "write the comment in English", and 8611 duly
commented 22 of 22 in English. Use:

| what is blessed | where | shape |
|---|---|---|
| a whole finding CLASS, with a count | `issues/<ID>/adjudicated.txt` | `key  n  reason`, read by r310's `adjudications()`; r260 reads the same file |
| ONE instance, where the page is the evidence | an HTML comment, **in German**, within 400 characters before it | states what the printed page has or lacks — to the reader, not to the checker |
| an open LIST a gate hands you to walk | `issues/<ID>/reviewed/<key>.txt` | one item per line, via `r000_reviewed.py`; later runs report only the delta. **Commit it** — `.gitignore` whitelists `!issues/*/reviewed/` for exactly this, and without the record the next build has no baseline and the gate reports everything again |

The third is new with the SH8603 harvest and exists for the checks that are
not pass/fail at all: a correct issue produces a non-empty list from them every
run. SH8603 shipped 14 such lines from two r160 checks alone, **all 14
correct.** A list that cannot be emptied gets skimmed, and the one new line in
it gets skimmed with it.

An adjudication clears exactly its count. If the pages now hold more of the
class than the file declares, the extra ones were never looked at, and that is
a HARD failure — not a note. r310 printed `MORE than adjudicated` and exited 0
until the same harvest.

## Cross-cutting rule: SAY WHAT TO READ SEPARATELY FROM WHAT TO EDIT

When briefing a sub-agent, scope of ATTENTION and scope of MODIFICATION are two
different things, and collapsing them silently shrinks the work.

MEASURED on SH8601: a glyph sweep was briefed "do NOT touch … headings",
meaning *do not restructure them*. It read that as *do not look there*, so 247
headings went unswept — and `<h2>Die Befehle zur $priteprogrammierung</h2>`
survived a pass that fixed 100 instances of exactly that defect elsewhere in the
same issue.

So write both, explicitly: **"read everything including headings and table
cells; edit only the words, never the structure."** The same applies to the
other axis — which FILES may be touched — when several agents work one issue at
once.

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
tools/img/scan2ocr/rules/r320_coverage_check.py issues/<YYMM> <ocr-out-dir>
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

- **page coverage** — now the second half of the same script, and it needs
  only `issues/<YYMM>/` and the descriptor, so it still runs after `<tmp>` has
  been swept away. It lists every page 1..`pages` that no `64er.pages` claims.
  Ads and classifieds are the legitimate population and they are most of the
  list; read it anyway. The reason it cannot be skipped: the UNACCOUNTED half
  excludes listing blocks by design, so a page carrying NOTHING BUT one
  article's listing is claimed by nobody, enters the reconciliation nowhere,
  and its absence reads as silence. MEASURED on 8610: UNACCOUNTED 0.0% while
  **12 pages were unclaimed and editorial** — Super-Install's `(Schluß)` on
  p31, the Soundmonitor on 59/61/62/64, Speech-Basic's on p70, the MSE's on
  p78, the CP/M-Formatter on p91, Colorprint on 107-108, the Vizawrite
  converter on 183-184. The quickest way to read the list is a montage of the
  unclaimed pages' top 150 thumb rows: an ad has no rubric banner, a listing
  page has one.
  The annual `Jahresinhaltsverzeichnis` is **a hint to check on the masters**,
  not an authority: it caught two understated ranges in 8609 (71-74, 82-84),
  but on 8612 it was wrong in both directions — ads counted into a range, and
  the Centronics article given as 52—57 where it actually runs 52-67.

## A CHECK SHIPS ONLY ONCE IT HAS BEEN SEEN TO FAIL

Write the check, then **plant the fault it is meant to catch** and watch it
fire. A check that has never failed is not a check; it is a sentence that looks
like one, and it is worse than nothing because it buys false confidence.

MEASURED on 8612 — five shipped checks could not fail at all:

| rule | why it could never fail |
|---|---|
| r260 | `PYEOF && \` is not a valid heredoc terminator, so bash swallowed check 2 and Python died. Repaired, `&& echo FAIL` keyed on exit status (always 0) and printed FAIL on clean output |
| r220 | the routing check filtered on `p[1].isdigit()`, dropping every range row (`172—173`): 26 of 55 rows checked, and a planted misroute passed |
| r280 | checks 1-2 piped into `head`, which hid a planted fault as entry 20 of 23 |
| r240 | the editorial grep was unanchored with an unescaped `.`, so a planted `src="18-0.png"` passed |
| r320 | exited 0 on findings AND on `CANNOT RUN`, so every exit-code consumer read a pass |

Four of the five were found by planting a fault. None had ever been seen to
fail. Test **output non-empty**, not exit status, unless the script sets the
status deliberately — and never pipe a check's findings into `head`.

## End-of-issue gate: the issue must BUILD

```bash
.venv/bin/python generate.py --issues <ID> --future local
```

Exit 0 and no traceback. This is the only check that sees the issue the way
the site does, and it catches what no per-rule verification can:

- a missing `issues/<ID>/title.png` -- the generator stops dead on it. Make it
  by reducing `<A4>/001.png` by **25 %**, where `<A4>` is the directory the PDF
  reads: **`a4600` on a `sheet` binding, `masters600` on a `spread` one** (r006
  tables this). Both are 4961 x 7016, so the result is 1240 x 1754 -- **as a
  consequence, not a constant**: `make_issue_pdf.sh` COMPUTES the size it will
  accept and exits 1 on a mismatch.
  This line used to say "crop `masters600/001.png` to the traced page box in
  its stamp, resize to 1240 x 1754 (what every other issue uses)". On a sheet
  binding `masters600` is the traced-trim canvas and NOT the A4 cut -- SH8604's
  is 5457 x 7181 -- so that recipe squeezes the page 0.8 % horizontally to
  reach the number, and the "what every other issue uses" reads as a constant
  to copy. Reduce the A4 page instead: no crop, no resample decision, and it is
  the same file every other page of the PDF comes from.
- a `toc_category` outside the issue's own `toc.txt`, a duplicate `64er.id`, a
  malformed `64er.pages`.
- An issue with no PDF yet builds (8610 fixed the two sites that assumed one);
  the load-time `Warning: Missing PDF` is expected and not a failure.

The generator serves `out/` on :8000 when a `local` build finishes -- kill it.

## EVERY HTML COMMENT IS GERMAN, AND IS FOR THE READER

An HTML comment ships. It is part of the published page, so it is written for
whoever reads the source, in the language of the magazine.

**The test is HARM, not truth.** A comment earns its place only if a reader
would otherwise be misled or come to harm. "Die Leserfragen sind ohne Namen
gedruckt" is true, is about the print, and fails the test — the page already
shows it. "Druckfehler: Busy liegt an Pin 11, nicht an Pin 16" stops someone
miswiring a board, and passes.

So: **German, naming a print error a reader would otherwise act on, and saying
what is correct. Nothing else.** Never crop geometry, never a `masters600`
path, never a step number, never a date, never who decided, never an ordinary
absence the page already shows, and never a gate adjudication — those live in
`adjudicated.txt`.

House style, from the hand-built issues: *"Die beschriebenen Programme sind
weder abgedruckt noch befinden sie sich in 84XX/8404.D64 auf der 64'er
CD-ROM."* It states what the printed magazine has or lacks, addressed to a
reader.

MEASURED 2026-10-02: 383 comments across 42 issues, 99 of them English — and
the English ones sit almost entirely in the chain-built issues (8612 26/26,
8611 22/22, SH8601 14/16) while 8404, 8602 and SH8501 have none. These rules
taught the drift; this section ends it. 8612 went from 26 comments to 2.

## Deliberate deviations from print must be marked in place

The standing rule is that the printed page wins, and every review pass is told
so. That makes an intentional departure fragile: the next pass verifies against
the page, sees a mismatch, and faithfully undoes it.

So when the editor decides to depart from the print — a typesetting error worth
correcting rather than preserving — record it **in the file, at the point of
the change**, as an HTML comment saying what the print has and that the
difference is intentional:

```html
<!-- Bewusste Abweichung vom Druck: Im Heft steht eine einzige Überschrift
     "Kleines Assembler-Lexikon: TurboAss- und ASSI/M-Besonderheiten" über dem
     Lexikon-Kasten; die zweite Hälfte gehört aber zu diesen beiden Tabellen.
     Hier getrennt. -->
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

**r325 exists to narrow that gap, and cannot close it.** Every automated pass
is pattern-driven or diff-driven: it confirms suspicions and cannot have
suspicions of its own. r325 reads the whole issue for sense precisely because
of that, but it is still a reading — SH8601's `$priteprogrammierung` sat in an
`<h2>` through r280, r310, r320, r330 and a green build, and was found by the
owner opening the article.

So: report status, list what is still open, and wait. Do not write "the issue is
complete" or upload on your own judgement.

## Changing a PROGRAM FILE always goes to the user first

**This is about `prg/*.txt` — the runnable programs — and nothing else.** A
`<pre>` block inside an article is transcription of the printed page like any
other text: when it disagrees with the master, read the 600 dpi crop and
correct it, exactly as for prose. Do not escalate that. (SH8601's chain
escalated four such lines and should not have; they were fixed from the page
in the end.)

`prg/*.txt` are the programs readers typed in. Editing one — applying an
erratum, correcting a line, renumbering — is not a markup fix and is never
routine:

- **Tell the user before doing it, and show the exact before/after lines.**
- Record it in the file's `;` header in the corpus vocabulary (see r300), so
  the change is legible to the next reader.
- Keep the superseded line as a `;` comment rather than deleting it, so the
  disk's original state is recoverable from the file itself.
- **Test the result.** There is no harness — this is the procedure, and the
  emulator is the one for the machine the program is FOR (`x64sc` for a C64,
  `x128` for a C128, `xplus4` for a Plus/4). All are installed:

  ```bash
  petcat -w2 -l 0801 -o /tmp/t.prg -- issues/<ID>/prg/<name>.txt   # tokenise
  petcat -2 -o /tmp/back.txt -- /tmp/t.prg                          # and back
  diff issues/<ID>/prg/<name>.txt /tmp/back.txt   # ONLY the patched lines
  x64sc -warp -autostart /tmp/t.prg -limitcycles 60M \
        -exitscreenshot /tmp/t.png                                  # it runs
  ```

  **Say what this does and does not show.** A clean round trip proves the
  patched lines tokenise; the autostart proves the program loads and reaches
  its first screen without a `?SYNTAX ERROR`. Neither exercises the patched
  lines unless they lie on the path the program takes to that screen. When they
  do not — SH8507's 9550 and 20100 are only reached from deeper menu actions —
  record that limit with the result rather than reporting "tested".

  **AND WHEN THE PATCHED LINE IS NOT ON THAT PATH, DRIVE IT DIRECTLY.** The
  autostart cannot reach a line like SH8604's 115. Direct mode can: boot the
  emulator with the file, let it stop, set by hand whatever the line reads, and
  `GOTO` it.

  ```bash
  # one keyboard script; -keybuf feeds it after the autoload completes
  x64sc -warp -autostart /tmp/t.prg -limitcycles 120M \
        -keybuf $'\nq=1:n$="x"\ngoto115\n' \
        -exitscreenshot /tmp/t.png
  ```

  Read the screenshot. This proves the patched line EXECUTES, which the
  autostart does not; it does not prove the program reaches that line on its
  own. Say which of the two you did.

  **Three traps met while building such a test, all on SH8604:**

  - **`c1541 -write` into a copied D64 fails SILENTLY.** The masters are mode
    `r-x`, so the copy is too: `chmod u+w` the copy, and **read the file back
    out** before believing the write.
  - **A true-drive `LOAD` of a 100-block file exceeds 60M cycles.** Either
    raise `-limitcycles` or autostart the `.prg` directly, which is what the
    recipe above does.
  - A scratch D64 is a scratch file: it goes under `<tmp>`, never beside
    `issues/<ID>/prg/`.

The default remains: record the errata state, do not patch. Patch only when the
user asks for it.
