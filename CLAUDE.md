# 64er-magazin.de

Scanned issues of the German Commodore magazine *64'er*, republished forty
years to the month. One directory per issue under `issues/<ID>/`: `YYMM` for a
monthly (`8612`), `SH YYMM` for a Sonderheft (`SH8602`).

## Building an issue

The whole process lives in `tools/img/scan2ocr/rules/` as a numbered chain of
rules — `rNNN_name.md` is the rule, `rNNN_name.{py,sh}` its code.

**Read `tools/img/scan2ocr/rules/r000_orchestration.md` first, before anything
else and before touching any file.** It is the contract: the step chain and
each step's disposition, the two points at which a build stops for its owner,
where the 2400 dpi masters are and that they are the only input, which Python
to use, and the conventions every step shares. A build that starts without it
repeats mistakes the file already records.

Then read the rule for the step you are on. Each one carries its own
Verification block; run it.

The issue being built comes from `tools/img/scan2ocr/rules/ISSUE.txt`
(git-ignored) or the `ISSUE` environment variable. There is no default — a
step with neither refuses to run.

`tools/img/scan2ocr/rules/HARVEST.md` records which rules were changed in
response to which build, and why.

## The site

`generate.py` builds the static site from `issues/`. Run it with the repo venv
(`.venv/bin/python`), never bare `python3`.
