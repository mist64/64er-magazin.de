# 64er-magazin.de

An art project that republishes the *64'er Magazin* exactly 40 years after each
original print release. One issue a month, built from 2400 dpi scans into
published HTML plus a PDF. `README.md` is the public page and carries the
release schedule; everything below is how the work is done.

## Building an issue — start here

**[`tools/img/scan2ocr/rules/r000_orchestration.md`](tools/img/scan2ocr/rules/r000_orchestration.md)**

That file is the entry point for the whole chain: scans → OCR → article HTML →
figures → metadata → checks → PDF. It defines the numbered rules
(`rNNN_name.{md,sh,py}` in the same directory), what runs in what order, which
steps apply to which kind of issue, and what a step has to prove before it is
done. Read it before touching anything under `issues/<YYMM>/`.

Its own first sections answer the questions a new build asks: which physical
binding this issue has, which paper profile grades it, where the working
directory goes, and how much free disk the sweep needs.

## The one standing rule

**The files are the deliverable, not the issue.** An issue is published once;
these rules are read by every agent that builds every issue after it. When a
run teaches you something, it goes into the `.md` *before* it goes into a
message to anyone — a correction delivered as prose teaches one agent and
evaporates. Record what was **disproved** as carefully as what was true: a
plausible wrong hypothesis costs the next agent the same cycle it cost you.

The test of a rule is not whether it is true. It is whether an agent who has
never seen this issue can act on it without asking.

## Layout

| | |
|---|---|
| `issues/<YYMM>/` | one directory per issue: article HTML, figures, `prg/`, `issue.json`, `colors.txt`, the PDF |
| `issues/style.css` | the site's stylesheet |
| `generate.py` | builds the site from `issues/` |
| `tools/img/scan2ocr/` | the import chain (`rules/` holds the numbered steps) |
| `tools/img/issue_pdf/` | the issue PDF build |
| `tools/` | `checksummer.py`, `mse.py`, `assembler_decode.py` and the other listing decoders |

## Git

Commit as the rules say. **Do not push unless asked.**
