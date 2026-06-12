# 8 — `pubdate.txt` (publication date)

**Goal:** write the single-line publication date for the issue. The
generator (`generate.py`) reads `issues/<YYMM>/pubdate.txt` and uses it
to (a) schedule when the issue becomes public on
`www.64er-magazin.de` and (b) order articles within the issue (each
article is offset a few hours from the issue's pubdate based on its
sort index).

The site re-publishes each historical issue **exactly 40 years after
its original print release**. The authoritative table of
release dates per issue lives in the project's top-level `README.md`
("Exakt 40 Jahre nach der ursprünglichen Veröffentlichung erscheint
hier jeden Monat eine neue Ausgabe" / "Ausgabe N/YY: TT. Monat 20JJ").

## File format

A single date line, ISO `YYYY-MM-DD`, trailing newline:

```
2026-06-14
```

That's the whole file. No comments, no metadata.

## How to derive the date

1. Open `README.md` and find the bullet for this issue (e.g.
   `07/86: 14. Juni 2026`). For special issues (Sonderhefte) the same
   list also includes their dates.
2. Convert the German `TT. Monat 20JJ` to `YYYY-MM-DD`.
3. Write `issues/<YYMM>/pubdate.txt` with that one line.

If `README.md` doesn't yet have a bullet for the issue — update
`README.md` first (the README is the single source of truth for the
publication schedule), then copy the date into `pubdate.txt`.

## Usage

There is no script for this step; it's a one-line text file.

```bash
echo 2026-06-14 > issues/8607/pubdate.txt
```

## Verification

```bash
# Format is exactly one ISO date, ending in a newline:
python3 - <<'PY'
import datetime, sys
fp = 'issues/8607/pubdate.txt'
s = open(fp).read()
assert s.endswith('\n'), 'file must end in a newline'
lines = s.splitlines()
assert len(lines) == 1, f'expected 1 line, got {len(lines)}'
datetime.date.fromisoformat(lines[0])   # raises if malformed
print(f'{fp}: {lines[0]} OK')
PY

# Cross-check that the date matches the README schedule:
grep -E "$(basename "$(dirname pubdate.txt)" | sed -E 's#^([0-9]{2})([0-9]{2})$#0\2/\1#')" README.md
```

A small build check (will refuse if pubdate is in the future without
`--future`):

```bash
.venv/bin/python generate.py --issues <YYMM> local
# or, while the issue is still future-dated:
.venv/bin/python generate.py --issues <YYMM> --future local
```

## Lessons / things to watch

- The pubdate must be **today or earlier** for `generate.py` to include
  the issue in a normal (non-`--future`) build; otherwise the
  generator asserts and skips it. Use `--future` while preparing an
  issue ahead of its release date.
- Don't invent a date or pull one off the magazine's cover month — the
  cover month is always one month later than the actual print release
  (issue 7/86 came out mid-June 1986, not in July). The README's
  bullet is the only source of truth.
- The publication date is the same calendar day for every reader, but
  the article sort within the issue is staggered (a few hours per
  article, see `generate.py:article_pubdate`) so RSS / Mastodon
  appearance is spread out across the day.
