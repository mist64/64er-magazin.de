# 340 — `WORKFLOW_ERRATA.md`: what these rules got wrong, written while it hurt

## THE FILE'S LIFECYCLE: kept, harvested, then DELETED

`WORKFLOW_ERRATA.md` is written throughout the build and committed, harvested
into these rules once the issue is COMPLETE — never earlier — and then
**deleted**. It is a hand-over, not an archive: once its content is in the
rules, a copy beside the issue is a second place for the same statement to
drift from. The harvest itself is recorded in
`tools/img/scan2ocr/rules/HARVEST.md`, which says what was decided and where it
landed, and the commits carry the detail.

Owner, 2026-10-04: "we also collect. we apply the errata at the END" and "when
applied, delete all errata md files".

### A HARVEST THAT CHANGES A CLAIM GREPS FOR THE OLD ONE

Rules cross-reference each other, and a rule's claim is usually repeated in a
code comment somewhere. Changing it in one place leaves the chain
self-contradictory, which is worse than the original defect because the next
build gets two answers. **After each harvest edit, grep the whole rule set
AND the code comments for the statement you just replaced.**

MEASURED: checking SH8604's entries against HEAD at finalisation turned up
four such leftovers from harvests that had landed elsewhere — r000's hand-over
table still called the cover crop a reduction of `masters600/001.png` after
4408be0e made it `<A4>`; `r005_masters_sheet.py:195` still called a confident
parity disagreement "a failure" after the rule had changed it to NOTED;
r005's rule pre-filled `high_pages` from the union of witnesses while the code
used the edge finder alone; and r005's Verification 4 comment still said it
reads `sheets600` after the check had moved to `masters600`. All four were
found by reading, not by a check — the grep is the check..

**Applies to:** all — every issue is run by an agent reading these files, so
every issue is also a test of them.

**Goal:** `issues/<ID>/WORKFLOW_ERRATA.md` — the build's account of **where
these rules failed it**: what did not make sense, what was not stated, what was
stated and was wrong, and what it had to do differently from what it was told.

This is the only step whose subject is the chain itself. Everything else in this
directory turns a scan into an issue; this one turns a build into better rules.

## It is written AS YOU WORK, not at the end

The entry is written **the moment the confusion happens**, in the step that hit
it, before the workaround is found. Afterwards is too late and not by a little:
once you have worked out what a rule meant, you cannot reconstruct what you
thought it meant, and that misreading is the entire finding. Within an hour the
memory is "r160 was a bit unclear"; at the moment it is "r160 told me to render
the issue PDF, which does not exist yet, so I went looking for a renderer".

The same reasoning as `LOG.md` (r000, *LOG.md is the audit trail*): a finding
carried in someone's head, or in a message, is a finding lost. **Step 340 is the
last step only in the sense that it is signed off last.** An errata file first
touched at step 340 is a file written from memory, and it is worth very little.

## It is NOT `LOG.md`

| | subject | fate |
|---|---|---|
| `LOG.md` | **this issue** — content gaps, print oddities, owner decisions | git-ignored; dies with the build |
| `WORKFLOW_ERRATA.md` | **these rules** — where the instructions failed | committed; it is the whole point |

A finding about the magazine goes to `LOG.md`. A finding about the instructions
goes here. When one causes the other — a rule was unclear, so a page got built
wrong — write both, and say so in each.

## What an entry contains

One entry per confusion, under a `## <step> — <one-line summary>` heading:

- **What the rule says.** Quote it. A paraphrase loses the ambiguity, which is
  usually the finding.
- **What you did with it**, including the wrong turn. The wrong turn is the
  evidence; a note that only records the right answer cannot explain why the
  rule produced a wrong one.
- **What is actually true**, and how you established it.
- **What it cost** — wall-clock, and how many commands it took to recover. This
  is the number that ranks the fixes, and nobody can recover it later.
- **Suggested.**: the sentence the rule should have carried. Use that word —
  check 4 below looks for it, along with the older "what would have prevented
  it" phrasing. An entry with no proposal is an observation, not an erratum.
  Write the sentence. "Should be clearer" is not a finding.

Also record the inverse, because it is just as useful and nobody ever writes it
down: **a rule that saved you.** A warning that stopped you doing the obvious
wrong thing is the strongest evidence a rule is earning its length, and length is
what these files are always under pressure to lose.

## Say when a rule was fine and you were not

Not every stumble is the rules' fault. A step you misread, skimmed, or ran out of
order is worth recording **as that** — it says the rule is correct but easy to
miss, which is a different fix (placement, a heading, a cross-reference) from a
rule that is wrong. An errata file that blames the instructions for everything is
one an orchestrator cannot act on.

## Usage

```bash
# first touch: at the FIRST confusion, whenever that is -- not at step 340
$EDITOR issues/<ID>/WORKFLOW_ERRATA.md
```

There is no script. The file is prose, committed with the issue.

## Verification

```bash
ID=8612   # the issue being built

# 1. It exists and is not a stub.
test -s "issues/$ID/WORKFLOW_ERRATA.md" || echo "FAIL: missing or empty"

# 2. It was written DURING the build, not after it. Its first commit must not be
#    the last commit of the issue -- a file whose only commit is the final one
#    was written from memory, which this rule exists to prevent.
first=$(git log --diff-filter=A --format=%H -- "issues/$ID/WORKFLOW_ERRATA.md" | tail -1)
last=$(git log -1 --format=%H -- "issues/$ID/")
[ -n "$first" ] && [ "$first" != "$last" ] \
  && echo "OK: first written at $first, before the final commit" \
  || echo "WARN: written in a single commit -- was it kept as you worked?"

# 3. Every entry names a step, and the steps named exist.
#    .md OR .py: not every step is a markdown rule.  r310 exists only as
#    r310_issue_invariants.py and r150 only as r150_figure_captions.py plus
#    r150_place_images.md, so SH8603's entries about r310 were all reported
#    "FAIL: no rule r310" -- a correct entry failing a check about itself.
grep -oE '^## r?[0-9]{3}' "issues/$ID/WORKFLOW_ERRATA.md" | grep -oE '[0-9]{3}' | sort -u |
while read s; do
  # ONE glob, then filter -- `ls a.md b.py c.sh` fails as soon as any ONE of
  # the three is unmatched (and under zsh the unmatched glob is itself an
  # error), so the three-pattern form reported FAIL for all 24 of SH8603's
  # steps, including the ones whose .md is right there.
  ls tools/img/scan2ocr/rules/r${s}_* 2>/dev/null | grep -qE '\.(md|py|sh)$' \
    || echo "FAIL: no rule r$s"
done

# 4. An entry that proposes nothing is an observation, not an erratum.
#    Every entry should carry a concrete replacement sentence.
#
#    "Suggested" IS THE MARKER THIS CHAIN ACTUALLY USES.  The pattern knew only
#    "would have prevented" and "should (have) said|carried|state", so SH8603's
#    13 "**Suggested.**" entries -- each carrying a concrete replacement -- were
#    every one of them reported as "no proposed fix".  A check that rejects the
#    house style is a check about its own vocabulary.  Write the marker as
#    **Suggested.** and this passes; the older phrasings still count.
#    REPORT THE COUNT, then the first few.  On SH8603 the old pattern flagged
#    41 of 42 entries and the repaired one still flags 28: the vocabulary was
#    half the problem and the other half is real -- most entries describe the
#    defect without ever writing the replacement sentence.  41 lines of output
#    is a gate nobody reads; a count with a sample is one you can act on.
awk '/^## /{h=$0; n=0}
     /[Ss]uggested|would have prevented|should (have )?(said|carried|state)/{n++}
     /^## /&&p&&!pn{c++; if (c<=5) print "  no proposed fix: " p}
     {p=h; pn=n}
     END{printf "  %d entr%s with no proposed fix (target 0)\n", c+0, (c==1?"y":"ies")}' \
  "issues/$ID/WORKFLOW_ERRATA.md"
```

## Lessons / things to watch

- **An empty errata file is a finding too, and a suspicious one.** No build has
  ever run these 4,000-odd lines of rules without hitting something. An empty
  file usually means the entries were never kept, not that nothing happened.
- **Do not fix the rule yourself mid-build.** Record it and carry on. Editing a
  rule while running it means the next step reads something different from what
  the previous one did, and the record of what actually went wrong is gone.

- **And neither does the orchestrator.** The harvest happens when this file is
  COMPLETE -- the issue finished, signed off, step 340 closed -- and not a step
  earlier. The reason is the one above, and it does not care who is holding the
  pen: a rule edited at step 160 means steps 040-150 ran against text that no
  longer exists, and the build stops being a single test of a single set of
  rules. Half a harvest also re-reads worse than none, because the entries that
  were applied are gone from the file and the ones that were not look like the
  whole story.

  **The single exception is a BLOCKING defect** -- the build genuinely cannot go
  on. That is not a harvest, it is an unblocking, and it is reported to the
  runner as a change to pull. It is still written in this file, with the fact
  that it was fixed mid-build and why, because a later reader needs to know the
  rules moved under the build. Everything else waits.
- **One exception:** a rule that is actively dangerous — it would destroy work, or
  write outside the issue — is stopped at once and escalated, not recorded and
  obeyed.
