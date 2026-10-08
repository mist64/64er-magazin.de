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
