"""The rules import each other by bare name from rules/, and r005_masters
loads the ISSUE descriptor at import.  Tests exercise pure functions on
synthetic arrays, so the descriptor only has to resolve -- 8610's does."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rules"))
