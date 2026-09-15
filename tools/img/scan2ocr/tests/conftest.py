"""The rules import each other by bare name from rules/, and r005_masters
loads the ISSUE descriptor at import.  Tests exercise pure functions on
synthetic arrays, but r005_masters_spread SystemExits at import if the
descriptor's binding is not "spread" (its own binding check) -- so the
descriptor must resolve to a spread issue, not merely resolve at all."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rules"))

# The default ISSUE (see r000_issue.py) may be a sheet issue; pin it to 8610
# so importing r005_masters_spread here does not hit its binding SystemExit.
import r000_issue
r000_issue.ISSUE = "8610"
