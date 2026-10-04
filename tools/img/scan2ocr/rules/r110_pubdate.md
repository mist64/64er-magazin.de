# 110 — `pubdate.txt` (publication date)

**Applies to:** all — the README's release table carries the Sonderheft dates too, and the file format is identical.

**But a Sonderheft's README bullet is usually a BOUND, not a date.** The table
carries "**vor** 14. Februar 2026", "ca. 20. September 2025", "**unbekannt"**,
and `Convert TT. Monat 20JJ` cannot read any of them. The Vorschau derivation
is monthly-only, and the Verification grep `"${YYMM:2:2}/${YYMM:0:2}"` matches
the MONTHLY bullet for the same digits (8602 → the 02/86 monthly) and breaks
outright on `SH8602`.

So for a Sonderheft: write the bound as a PROVISIONAL `pubdate.txt`, say in
LOG.md that it is provisional and which bullet it came from, and carry it to
PAUSE 2 as an owner decision. Never present a bound as a date.

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
OPERATOR's to give.** Write the DERIVED bullet and list it for the owner to
confirm at PAUSE 2 — that is not inventing one. Do not invent one that is not derived. The rule used to say "add one
first" without saying where the date comes from, which asks an agent to
write a number it has no source for.

Where it comes from, in order:

**THE PREVIOUS ISSUE PRINTS IT.** Every *Vorschau* page carries, in its
masthead banner beside the wordmark:

> `VORSCHAU 64'er   DIE NÄCHSTE AUSGABE ERSCHEINT AM 17.10.86`

That is the next issue's on-sale date, and it is the authority. Add 40 years
to it — the same day of the same month — and that is the bullet. 11/86's
came off 8610 p196, 12/86's off 8611 p188.

**Read it from the PAGE IMAGE, not the article text.** The date is set in
the banner, which is artwork; it is not in the Vorschau article's prose and
never reaches the HTML. This rule previously said "8610's Vorschau announces
the contents and no date" — written after reading the article body and
finding nothing, which is exactly the wrong place to look. Crop the top strip
of `masters600/<Vorschau page>.png`.

The Vorschau is the page whose banner reads **VORSCHAU 64'er** — near the end,
**5th to 7th from last** (188 of 192 on 8611, 196 of 200 on 8610, but **194 of
200 on 8612**, which is 7th). Find it in the 080 file list as `NNN Vorschau.html`
rather than counting back from the end. `toc_entries.txt` also names it (the
`Rubriken` entry `Vorschau`), but it does not exist yet at 110: step 090 runs
alongside, or produces it later.

So the plan date is **derived, not chosen** — and because it is, the operator
confirms it rather than invents it. Two issues ahead can be filled at once:
reading 8611 p188 supplies 12/86 before 8612 is imported at all.

*Sanity, not authority:* the original dates are Fridays and the same calendar
dates 40 years on are Saturdays, 28 days apart. If a derived date is neither
a Saturday nor ~28 days after the previous, re-read the banner.

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
