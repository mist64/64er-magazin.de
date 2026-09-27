# 110 — `pubdate.txt` (publication date)

**Applies to:** all — the README's release table carries the Sonderheft dates too, and the file format is identical.

**Goal:** write the single-line publication date for the issue. The
generator (`generate.py`) reads `issues/<YYMM>/pubdate.txt` and uses it
to (a) schedule when the issue becomes public on
`www.64er-magazin.de` and (b) order articles within the issue (each
article is offset a few hours from the issue's pubdate based on its
sort index).

The site re-publishes each historical issue **exactly 40 years after
its original print release**, and the plan for that lives in the
project's top-level `README.md` ("Exakt 40 Jahre nach der
ursprünglichen Veröffentlichung erscheint hier jeden Monat eine neue
Ausgabe" / "Ausgabe N/YY: TT. Monat 20JJ").

**The README is the PLAN. `pubdate.txt` is the RELEASE.** They agree
when an issue ships on its planned day and they diverge when it does
not -- 8610 was planned for 19 September 2026 and released on the 27th.
When they disagree, `pubdate.txt` is right and the README bullet stays
as it was: it is the record of what was originally scheduled, not a
value to be reconciled. **Never edit a README bullet to match a
pubdate.** The only time this rule writes to the README is when the
issue has no bullet at all.

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

If `README.md` doesn't yet have a bullet for the issue — and for every
issue after the last one planned, it does not — **the plan date is the
OPERATOR's to give.** Do not invent one. The rule used to say "add one
first" without saying where the date comes from, which asks an agent to
write a number it has no source for.

Where it comes from, in order:

1. **The magazine's own announcement**, where it prints one. The
   Sonderheft bullets cite theirs as page references —
   `Sonderheft 6/85 (Top-Themen): ca. 18. Oktober 2025 <!-- 8511/S.139 -->`
   — because the monthly that preceded them printed an on-sale date. Check
   the previous issue's *Vorschau* first. The monthly bullets carry no such
   comment: 8610's Vorschau announces 11/86's contents and no date.
2. **Otherwise the established cadence**, which the operator confirms. It
   is a **Saturday, 28 or 35 days after the previous issue**, keeping to
   mid-month — MEASURED over the last eight planned dates, six of which are
   the 2nd or 3rd Saturday and the gaps alternate 28/35 to stay there.
   The rhythm is the point: one issue a month, 40 years on.

Whichever it is, the operator says it, and the bullet records it.

**If the issue ships on a different day, only `pubdate.txt` changes.**
The user sets it (`pubdate.txt` is a publishing decision, not an import
step); the README bullet keeps the planned date.

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

# Print the README's planned date beside it. This is a LOOK, not a gate:
# a mismatch means the issue slipped, which is normal and is exactly what
# pubdate.txt exists to record. Do not "fix" either side to agree.
# README bullets are "MM/YY: TT. Monat 20JJ" (e.g. "08/86: 19. Juli 2026").
# Pass the issue id EXPLICITLY — the old `dirname pubdate.txt` form was a
# no-op (`dirname pubdate.txt` is always ".", so the sed produced nothing
# and grep matched every line). For issue YYMM, grep "MM/YY":
YYMM=8608                                  # this issue's id
grep "${YYMM:2:2}/${YYMM:0:2}" README.md   # 8608 → grep "08/86" README.md
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
