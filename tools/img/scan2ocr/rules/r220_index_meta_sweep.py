#!/usr/bin/env python3
r"""Corpus-wide standing check: every published issue's index_category count
against its CSV row count.

Usage (from the repo root):
    .venv/bin/python tools/img/scan2ocr/rules/r220_index_meta_sweep.py [ISSUE ...]

With no arguments it sweeps every directory under issues/ that holds HTML.
Exit 1 if any issue's counts disagree.

WHY THIS EXISTS, AND WHY THE PER-ISSUE CHECK WAS NOT ENOUGH
-----------------------------------------------------------
MEASURED 2026-11-16: NINE published Sonderhefte -- SH8501..SH8601, SH8603,
SH09 -- carried ZERO index metadata, 253 CSV rows unapplied, for two separate
reasons that had nothing to do with each other:

  * r220 was classified `monthly` and pointed at the ANNUAL csvs until SH8602.
    The Sonderheft reader was written then and never back-applied.
  * `sonderheft_key()` could not form a key for SH09 and up, so r220 applied
    zero rows and said nothing.

r220's own Verification would have caught neither, and not because it was
skipped.  It is a PER-ISSUE check run ONCE, at build time, by the session that
is building that issue.  Both defects were introduced LATER, in a different
session, on a different issue -- and a per-issue check never looks back at an
issue that is already shipped.  Worse, on a Sonderheft it was vacuous:
`grep -c "^SH8603," Jahresinhaltsverzeichnis` finds 0 rows, 0 == 0 reports a
PASS, and the issue ships with nothing.

**A check that only ever runs forwards cannot find damage done behind it.**
Run this one after any change to r220, to either CSV, or to the issue
directories, and it answers for the whole corpus at once in about a second.

The count is the right invariant because it is the one thing both failures
break: a row that is not applied is a meta that is not there.  It will not
catch a row applied to the WRONG article (routing) -- that is the apply
script's own cross-page report and r220 Verification step 2.
"""

import csv
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

import r220_index_meta_apply as ap


# A KNOWN DIFFERENCE IS RECORDED WITH ITS REASON AND ITS EXACT SIZE, NEVER
# WAIVED.  `applied - csv` must equal the number here; any other value fails
# like an unlisted issue, so a second defect cannot hide behind a first.  An
# entry without a reason is not an entry.
KNOWN = {
    # The 1986 annual index is PRINTED in 8701 at pp95-98 and was not
    # transcribed as an article ("94 Noch mehr Tips zu Master-Text" carries
    # `64er.pages 94,99`, so 95-98 belong to no file).  Its own CSV row
    # `8701,95,Sonstiges,Sonstiges,Jahresinhaltsverzeichnis 86` therefore has
    # no article to sit in.  We hold that index as the CSV itself.
    "8701": (-1, "p95 Jahresinhaltsverzeichnis 86 -- pp95-98 are the printed "
                 "annual index, deliberately not transcribed as an article"),
    # 8502 and 8503 were among the first issues built and their index metas do
    # not come from this CSV: the wording differs on nearly every row ("Die
    # Stimme des Meisters: Voice Master" against the CSV's "Die Stimme des
    # Meisters - Test Voice Master"), the categories are a DIFFERENT taxonomy
    # ("Hardware-Test|Sprachausgabe" against "Hardware-Tests|Musik"), and some
    # carry THREE levels ("Listings zum Abtippen|Anwendung|Abtippen"), which
    # the two-column CSV cannot produce.  They also index items the CSV omits
    # (Checksummer, MSE, Autoboot).  Which source wins is the OWNER'S ruling,
    # open since 2026-11-17; until he rules, the sizes are pinned here so a
    # NEW divergence in those two issues still fails.
    "8502": (+5, "hand-made index taxonomy, not from the CSV -- owner's ruling open"),
    "8503": (+3, "hand-made index taxonomy, not from the CSV -- owner's ruling open"),
}


def csv_for(issue):
    if issue.startswith("SH"):
        return os.path.join(ROOT, "Gesamtinhaltsverzeichnis Sonderhefte.csv")
    m = re.match(r"^(\d{2})(\d{2})$", issue)
    if not m:
        return None
    return os.path.join(ROOT, f"Jahresinhaltsverzeichnis 19{m.group(1)}.csv")


def applied_count(d):
    n = 0
    for fn in glob.glob(os.path.join(d, "*.html")):
        n += io.open(fn, encoding="utf-8").read().count('name="64er.index_category"')
    return n


def main():
    issues = sys.argv[1:]
    if not issues:
        issues = sorted(
            os.path.basename(d)
            for d in glob.glob(os.path.join(ROOT, "issues", "*"))
            if os.path.isdir(d) and glob.glob(os.path.join(d, "*.html"))
        )

    bad, nocsv = [], []
    for issue in issues:
        d = os.path.join(ROOT, "issues", issue)
        path = csv_for(issue)
        if not path or not os.path.exists(path):
            nocsv.append(issue)
            continue
        # A row with NO category writes no index_category meta, on purpose
        # (see r220 "A BLANK CATEGORY IS UNKNOWN").  Those rows are not
        # expected to appear, so they are not counted here either.
        err = io.StringIO()
        real, sys.stderr = sys.stderr, err
        try:
            rows = ap.parse_csv(path, issue)
        finally:
            sys.stderr = real
        want = sum(1 for e in rows
                   if (e["category"].strip() or e["subcategory"].strip()))
        have = applied_count(d)
        delta, why = KNOWN.get(issue, (0, None))
        ok = (have - want) == delta
        flag = ("" if delta == 0 else f"   (known {delta:+d}: {why})") if ok \
            else "   <-- MISMATCH"
        print(f"  {issue:8s} csv {want:4d}   applied {have:4d}{flag}")
        if not ok:
            bad.append((issue, want, have, err.getvalue().strip()))

    if nocsv:
        print("\n  no index CSV for: " + " ".join(nocsv))
    if bad:
        print(f"\n*** {len(bad)} issue(s) disagree with the index CSV ***")
        for issue, want, have, msg in bad:
            print(f"    {issue}: csv {want}, applied {have}")
            if msg:
                for line in msg.splitlines():
                    print(f"        {line}")
        return 1
    known = [i for i in issues if i in KNOWN]
    print(f"\n  OK: {len(issues) - len(nocsv)} issue(s), every count agrees"
          + (f" ({len(known)} by a recorded difference: {' '.join(known)})." if known else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
