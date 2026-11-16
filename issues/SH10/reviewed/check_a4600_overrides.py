#!/usr/bin/env python3
"""RED when a trace failure has no disposition, or ANY recorded override is not in the delivered page.
Run with ISSUE=SH10; optional arguments: other a4600 and masters600 directories to read.

SH10's copy of issues/SH09/reviewed/check_a4600_overrides.py, with its coverage defect fixed:
the SH09 script kept ONE record per page (a dict keyed by page), so a page's second override line
silently replaced its first and the first fell out of coverage while the check stayed green; and it
accepted any OVERRIDE anywhere in a stamp. Here:

1. every master the step called 'uncropped sheet' is named in reviewed/a4600-overrides.txt
2. EVERY record line is checked (a page may carry several): each directory it names must hold a stamp
   with an OVERRIDE line that names THAT record's script
3. the per-page override count is reported, so a missing one shows as a number, not as silence

This is a stamp test: it cannot see pixels changed under an intact stamp.
"""
import re, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import r000_issue
iss = r000_issue.load(r000_issue.ISSUE)
tmp = Path(iss.tmp)
dirs = {"a4600": Path(sys.argv[1]) if len(sys.argv) > 1 else tmp / "a4600",
        "masters600": Path(sys.argv[2]) if len(sys.argv) > 2 else tmp / "masters600"}
rec = Path(iss.issue_dir) / "reviewed" / "a4600-overrides.txt"
records = []                                   # (page, verdict, [dirs], script)
if rec.exists():
    for ln in rec.read_text(encoding="utf-8").splitlines():
        if ln.strip() and not ln.startswith("#"):
            f = ln.split()
            i = next(k for k, x in enumerate(f) if x.endswith(".py"))
            records.append((f[0], f[1], f[2:i], f[i]))
pages = {p for p, *_ in records}
bad, n = [], 0
for f in sorted((tmp / "masters600").glob("*.stamp.txt")):
    n += 1
    if re.search(r"^page-class\s+uncropped sheet$", f.read_text(encoding="utf-8"), re.M) and f.name[:3] not in pages:
        bad.append(f"{f.name[:3]}: trace failed, no line in {rec.name}")
per_page = defaultdict(list)
for p, verdict, where, script in records:
    for d in where:
        st = (dirs[d] / f"{p}.stamp.txt").read_text(encoding="utf-8")
        ok = any("OVERRIDE" in ln and script in ln for ln in st.splitlines())
        per_page[p].append(f"{d}:{script}:{'ok' if ok else 'MISSING'}")
        if not ok:
            bad.append(f"{p}: recorded as {verdict} in {d} by {script}, but no OVERRIDE line in that stamp names it "
                       f"-- re-run reviewed/{script}")
print(f"{n} master stamps read, {len(records)} override record(s) on {len(pages)} page(s), {len(bad)} defect(s)")
for p in sorted(per_page):
    print(f"  {p}: {len(per_page[p])} override check(s) -- " + ", ".join(per_page[p]))
for b in bad:
    print("  RED", b)
sys.exit(1 if bad else 0)
