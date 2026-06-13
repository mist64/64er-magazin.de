# 0 — Orchestration: how to execute every other rule in this dir

**Goal:** define the meta-process that every numbered rule in this
directory is run under. Read this once at the start of an issue build;
re-read whenever a new agent or session takes over.

The build pipeline (rules 1 through N) is a chain of substantive,
sometimes editorial transformations. Doing them in-line in the main
conversation thread is the wrong shape: each one chews up context the
user is paying for, and it skips the second pair of eyes the
verification block in each rule was designed to provide.

## The rule

For every numbered rule in this directory:

1. **Dispatch the actual execution to a sub-agent.**
   - Brief the sub-agent with the rule's path (`tools/llm/rules/N_<name>.md`),
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

The trigger for sub-agent dispatch is a rule under
`tools/llm/rules/`. Anything outside that directory is at the
orchestrator's discretion.

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

> You are executing rule `tools/llm/rules/N_<name>.md` for issue YYMM.
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

## Cross-cutting recipe: page block index (blocks.txt)

Several rules (12 place_images, 13 fill_tables, 14 transcribe_listings,
19 head_meta, 22 rubric_banners) need to know the bbox of a specific
region on a rendered page — a caption, a listing block, a header
strip, a banner illustration. The common primitive is a per-page
**block index**: one line per layout block giving its bbox and a
short text preview, derived from a tesseract TSV pass.

**Build it ONCE per issue via rule 23.** That rule produces
`issues/<YYMM>/_tmp/blocks/p<NNN>.txt` for every page. Run it after
the PDF is in the issue dir and before any rule that needs bboxes
dispatches. The cost is ~1-2 seconds per page, ~5 minutes for a
full issue.

The on-demand single-page recipe below is the fallback when rule 23
hasn't been run yet (one-off table or listing OCR work):

```bash
# render the page once
mkdir -p /tmp/64er_<YYMM>_pages_300
pdftoppm -r 300 issues/<YYMM>/64er_19XX-XX.pdf \
  /tmp/64er_<YYMM>_pages_300/p -png -f <N> -l <N>

# tesseract TSV → blocks index
tesseract /tmp/64er_<YYMM>_pages_300/p-<NNN>.png /tmp/64er_<YYMM>_p<NNN>_ocr -l deu tsv

awk -F'\t' 'NR>1 && $1==5 && $12!="" {
  b=$3;
  if (!(b in minL) || $7<minL[b]) minL[b]=$7;
  if (!(b in minT) || $8<minT[b]) minT[b]=$8;
  if (!(b in maxR) || $7+$9>maxR[b]) maxR[b]=$7+$9;
  if (!(b in maxB) || $8+$10>maxB[b]) maxB[b]=$8+$10;
  text[b]=text[b]" "$12;
}
END {
  for (b in text) {
    printf "block=%s bbox=%dx%d+%d+%d text=%s\n",
      b, maxR[b]-minL[b], maxB[b]-minT[b], minL[b], minT[b],
      substr(text[b],1,200);
  }
}' /tmp/64er_<YYMM>_p<NNN>_ocr.tsv | sort > /tmp/64er_<YYMM>_p<NNN>_blocks.txt
```

The output lines look like:
```
block=22 bbox=825x84+195+1955 text= Listing 1. Komprimierte Version ...
block=45 bbox=840x39+1321+3256 text= Tabelle 2. Hier die entwirrte ...
```

Grep for the caption / heading / header text you need:
```bash
grep -i "listing" /tmp/64er_<YYMM>_p<NNN>_blocks.txt
grep -iE "tabelle|steckbrief" /tmp/64er_<YYMM>_p<NNN>_blocks.txt
```

Then read the `bbox=WxH+X+Y` and crop with `magick`. For listings
and tables, the caption block tells you the column (X, width W);
the code/table region usually sits **above** in the same column —
walk preceding blocks whose x-range overlaps to find its top edge.

`/tmp/64er_<YYMM>_p<NNN>_blocks.txt` is scratch — never commit it.

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
rewrite. See the `feedback_print_verbatim` memory for the full rule.

Make this explicit in every sub-agent brief that involves body-text
editing — it's the difference between a faithful archive and a
modernised paraphrase.
