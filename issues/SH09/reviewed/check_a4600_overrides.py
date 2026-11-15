#!/usr/bin/env python3
"""RED when a trace failure has no disposition, or a recorded override is not in the delivered page.
Run with ISSUE=<id>; optional arguments: other a4600 and masters600 directories to read.

1. every master the step called 'uncropped sheet' is named in reviewed/a4600-overrides.txt
2. every page recorded there carries OVERRIDE in the stamp of every directory its record names.  r005_a4_window.py and
   r005_masters_sheet.py rewrite the stamp along with the pixels, so re-running them without the script fails here.

This is a stamp test: it cannot see pixels changed under an intact stamp.
"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import r000_issue
iss = r000_issue.load(r000_issue.ISSUE)
tmp = Path(iss.tmp)
dirs = {"a4600": Path(sys.argv[1]) if len(sys.argv) > 1 else tmp / "a4600",
        "masters600": Path(sys.argv[2]) if len(sys.argv) > 2 else tmp / "masters600"}
rec = Path(iss.issue_dir) / "reviewed" / "a4600-overrides.txt"
listed = {}
if rec.exists():
    for ln in rec.read_text().splitlines():
        if ln.strip() and not ln.startswith("#"):
            f = ln.split()
            i = next(k for k, x in enumerate(f) if x.endswith(".py"))
            listed[f[0]] = (f[1], f[2:i], f[i])
bad, n = [], 0
for f in sorted((tmp / "masters600").glob("*.stamp.txt")):
    n += 1
    if re.search(r"^page-class\s+uncropped sheet$", f.read_text(), re.M) and f.name[:3] not in listed:
        bad.append(f"{f.name[:3]}: trace failed, no line in {rec.name}")
for p, (verdict, where, script) in listed.items():
    for d in where:
        if "OVERRIDE" not in (dirs[d] / f"{p}.stamp.txt").read_text():
            bad.append(f"{p}: recorded as {verdict} in {d}, but that stamp has no OVERRIDE -- re-run reviewed/{script}")
print(f"{n} master stamps read, {len(listed)} override(s) recorded, {len(bad)} defect(s)")
for b in bad:
    print("  RED", b)
sys.exit(1 if bad else 0)
