#!/usr/bin/env python3
"""
The one place scan2ocr learns WHERE an issue lives.

Every step used to carry its own absolute paths -- five of them, hand-edited per
issue (`r010:51,52`, `r020_classify:35`, `r020_evaluate:46,47`,
`r020_collect:24`).  That was survivable while 8609 was the only issue and
became a trap the moment a second one appeared: the five had to be changed
together, in step order, and a half-edited chain does not fail.  It reads page
006 of one issue and writes it into another issue's `out/`.

So: one descriptor per issue, `issues/<ID>/issue.json`, next to the published
HTML it eventually becomes, and ONE knob for the whole chain -- the `ISSUE`
constant below.  Every program reads it from here:

    from r000_issue import ISSUE
    ISS     = r000_issue.load(ISSUE)
    SRC_DIR = ISS.masters600
    OUT_DIR = ISS.out_dir

That keeps scan2ocr's convention intact (constants at the top of the file, no
CLI knobs, no env knobs -- see CLAUDE.md): `ISSUE` IS the constant, and every
path below it is derived rather than typed.  What changed is WHERE it lives.
Seven programs each declaring their own copy meant seven edits per issue, and a
half-edited chain does not fail -- it draws one issue's boxes on another's page.
r020_classify carried a hand-written cross-check against r010's copy for exactly
that reason; that check is gone along with the duplication it guarded.  Two
issues cannot be half-swapped now, because there is only one thing to swap.

The descriptor holds what is genuinely a property of the ISSUE -- where its
scans landed, how many pages it has, whether the frame holds a spread or a
loose sheet.  It does NOT hold tuning: thresholds, dpi, model names and prompts
stay as commented constants in the step that uses them, where the comment
explaining the measured value can sit beside it.

    { "id": "SH8601", "kind": "sonderheft", "binding": "sheet", "pages": 152,
      "scan_dir": "/Users/mist/DNB/SH8601/master_2400/SH8601",
      "thumb_150": "/Users/mist/DNB/SH8601/master_2400/SH8601/thumb",
      "tmp":       "/Users/mist/DNB/SH8601/tmp",
      "colors":    "/Users/mist/DNB/SH8601/master_2400/SH8601/colors.txt",
      "pdf":       "64er_Sonderheft_1986-01.pdf" }

Everything under `<tmp>/` is DERIVED here and never spelled out in the
descriptor, because the layout of the working directory is a property of the
pipeline, not of the issue.  Adding an issue is therefore six paths and no
thought about where `ocr/out` goes.
"""

import json
import os

# ---------------------------------------------------------------------------
# CONSTANTS  (no CLI knobs, no env knobs -- see CLAUDE.md)
# ---------------------------------------------------------------------------

# THE per-issue knob, for the entire chain.  Steps 010, 020 (classify, collect,
# evaluate), 030 and 320 import this name instead of declaring one each, so
# switching issues is this one line and nothing else.  It belongs here because
# this is the module whose subject IS the issue: everything below derives from
# it, and nothing above it needs to be told which issue is meant.
#
# The value is both the directory name under <repo>/issues/ and the "id" inside
# issues/<ISSUE>/issue.json -- load() refuses to run if the two disagree.
#
#     "SH8601"   Sonderheft 1/86, 152 pages, loose sheets
#     "8609"     the September 1986 monthly, 176 pages, clipped spreads
ISSUE = "SH8601"

# The descriptors live with the issues they describe: <repo>/issues/<ID>/.  That
# directory already IS the issue as far as the site generator is concerned (its
# HTML, its PDF, its toc.txt), so the scan chain's view of the same issue
# belongs beside them rather than in a private registry that can drift out of
# step with what actually got published.
#
# This file sits at <repo>/tools/img/scan2ocr/rules/, so the repo root is four
# directories above the one holding it.  Derived from __file__ and not from the
# working directory: the steps are run from rules/ (the .sh wrappers cd there,
# so the sibling modules import by bare name) while r320 is run from the repo
# root, and a relative path would mean different things to the two.
_RULES_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(_RULES_DIR))))
ISSUES_ROOT = os.path.join(REPO_ROOT, "issues")
DESCRIPTOR_NAME = "issue.json"

# Keys the descriptor MUST carry.  Checked as a set rather than read with
# .get(): a missing "tmp" would otherwise surface hundreds of lines later as a
# file written to a path beginning "None/", which is recoverable but only after
# a sweep has already run.
REQUIRED_KEYS = ("id", "kind", "binding", "pages", "scan_dir", "thumb_150",
                 "tmp", "pdf")
# ...and the ones that may be absent or null.  `colors` is the measured colour
# profile for the sheet; without it the grade falls back to its built-in anchor
# set, so an issue with no profile still renders.
OPTIONAL_KEYS = ("colors", "masters600")

# `kind` is editorial (it decides how the issue is titled and dated downstream),
# `binding` is mechanical: it selects which variant of step 005 runs, and the
# two variants cut the page apart in incompatible ways.  Both are checked
# against a closed set here, because a typo in `binding` would not fail -- it
# would quietly match neither variant, or worse, be read as the other one.
KINDS = ("monthly", "sonderheft")
BINDINGS = ("spread",   # the frame holds a clipped SPREAD  -> r005_masters_spread
            "sheet")    # the frame holds one loose SHEET   -> r005_masters_sheet

# --- the derived layout under <tmp>/ -----------------------------------------
# Step 005 writes the 600 dpi masters here and steps 010 and 145 read them.  ONE
# directory, whichever variant of 005 ran: that is the contract that lets the
# rest of the chain not care whether the scan was a spread or a sheet.
#
# NOTE -- this is `masters600`, not the `master600/final` that the retired
# scan2mrc used to produce.  The rename is deliberate: `final` meant "the last
# of scan2mrc's several master renderings", a distinction that no longer exists
# now that step 005 owns everything between the raw scan and r010's input.
MASTERS_SUBDIR = "masters600"

# ...with ONE escape hatch, `masters600` in the descriptor.  8609's masters were
# rendered years before step 005 existed and sit in the old scan2mrc layout at
# <tmp>/master600/final.  Re-rendering 176 pages to satisfy a directory name
# would be silly, and worse, it would make the "8609 is unchanged" gate compare
# new pixels against an old corpus -- the gate's whole point is that the pixels
# did NOT move.  So an issue may name the directory its masters already live in.
# New issues never set this; they get the derived path and step 005 fills it.

# The OCR working directory and everything in it.  OUT_DIR is a working
# directory -- json, digests, per-page tsv leftovers, two kinds of overlay --
# so the human-facing collections (review/, the reports) sit BESIDE it rather
# than inside it.
OCR_SUBDIR = "ocr"
OUT_SUBDIR = "out"        # per-page blocks, digests, overlays, article text
TRUTH_SUBDIR = "truth"    # the vision reading, ground truth for r020_evaluate
REVIEW_SUBDIR = "review"  # r020_collect's flat pNNN.png + pNNN.txt triage pile
REPORT_NAME = "report.jsonl"
WORST_NAME = "WORST.txt"
ARTICLES_NAME = "articles.json"
HYPHENS_NAME = "hyphens.json"

# Loaded descriptors, keyed by id.  Steps import each other freely (r030 pulls
# constants out of r020_classify, which pulls them out of r010), so the same
# descriptor is asked for several times per process; caching makes the repeats
# free and, more usefully, guarantees they all see the same object.
_CACHE = {}


class Issue:
    """One issue's identity and every path derived from it.

    Attributes are plain strings and ints, deliberately: they are assigned
    straight to the SRC_DIR / OUT_DIR constants at the top of each step, and
    those must stay greppable as the paths they have always been.
    """

    def __init__(self, d, issue_dir):
        # --- straight out of the descriptor ---------------------------------
        self.id = d["id"]
        self.kind = d["kind"]              # "monthly" | "sonderheft"
        self.binding = d["binding"]        # "spread" | "sheet" -- picks step 005
        self.pages = int(d["pages"])       # printed pages, cover counted as 1
        self.pdf = d["pdf"]                # file name inside issue_dir
        self.scan_dir = d["scan_dir"]      # raw 2400 dpi scans, NNN.png
        self.thumb_150 = d["thumb_150"]    # 150 dpi thumbs of the same
        self.tmp = d["tmp"]                # the working directory, everything below

        # The measured colour profile, or None.  Declared-but-absent is treated
        # as absent rather than as an error, because the profile is MEASURED off
        # the scans by a later hand: the descriptor names where it will land,
        # and the grade uses its built-in anchors until it does.
        colors = d.get("colors")
        self.colors = colors if colors and os.path.exists(colors) else None

        # --- where the issue lives in the repo -------------------------------
        self.issue_dir = issue_dir
        self.descriptor = os.path.join(issue_dir, DESCRIPTOR_NAME)
        self.pdf_path = os.path.join(issue_dir, self.pdf)

        # --- the derived working layout --------------------------------------
        override = d.get("masters600")
        self.masters600 = override or os.path.join(self.tmp, MASTERS_SUBDIR)
        self.ocr_dir = os.path.join(self.tmp, OCR_SUBDIR)
        self.out_dir = os.path.join(self.ocr_dir, OUT_SUBDIR)
        self.truth_dir = os.path.join(self.ocr_dir, TRUTH_SUBDIR)
        self.review_dir = os.path.join(self.ocr_dir, REVIEW_SUBDIR)
        self.report = os.path.join(self.ocr_dir, REPORT_NAME)
        self.worst = os.path.join(self.ocr_dir, WORST_NAME)
        # The assembled issue is named after the issue, so two of them in one
        # tree cannot overwrite each other even by accident.
        self.issue_md = os.path.join(self.ocr_dir, self.id + ".md")
        self.articles_json = os.path.join(self.ocr_dir, ARTICLES_NAME)
        self.hyphen_cache = os.path.join(self.ocr_dir, HYPHENS_NAME)

    @property
    def page_range(self):
        """1..pages inclusive -- what every per-page sweep iterates.

        A property rather than a stored range so that `pages` stays the single
        statement of how long the issue is.
        """
        return range(1, self.pages + 1)

    def __repr__(self):
        return f"<Issue {self.id} {self.kind}/{self.binding} {self.pages}pp>"


def load(issue_id):
    """Read issues/<issue_id>/issue.json and return an Issue.

    Every failure here is fatal and loud.  A step that cannot say where its
    input is must not start: the alternative is a sweep that runs to completion
    against the wrong issue's masters and reports a number for it.
    """
    if issue_id in _CACHE:
        return _CACHE[issue_id]

    issue_dir = os.path.join(ISSUES_ROOT, issue_id)
    path = os.path.join(issue_dir, DESCRIPTOR_NAME)
    if not os.path.exists(path):
        raise SystemExit(f"r000_issue: no descriptor at {path} -- "
                         f"ISSUE = {issue_id!r} names an issue that has none")

    with open(path, encoding="utf-8") as fh:
        try:
            d = json.load(fh)
        except json.JSONDecodeError as e:
            raise SystemExit(f"r000_issue: {path} is not valid JSON: {e}")

    missing = [k for k in REQUIRED_KEYS if k not in d]
    if missing:
        raise SystemExit(f"r000_issue: {path} is missing {', '.join(missing)}")
    unknown = [k for k in d if k not in REQUIRED_KEYS and k not in OPTIONAL_KEYS]
    if unknown:
        raise SystemExit(f"r000_issue: {path} has unknown key(s) "
                         f"{', '.join(unknown)} -- a typo'd key is silently "
                         f"ignored otherwise")
    # The id is stated twice -- in the directory name and in the file -- so that
    # a descriptor copied to seed a new issue and then not edited is caught here
    # rather than by writing 152 pages of SH8601 into 8609's out/.
    if d["id"] != issue_id:
        raise SystemExit(f"r000_issue: {path} says id={d['id']!r} but sits in "
                         f"issues/{issue_id}/")
    if d["kind"] not in KINDS:
        raise SystemExit(f"r000_issue: {path} kind={d['kind']!r}, "
                         f"expected one of {KINDS}")
    if d["binding"] not in BINDINGS:
        raise SystemExit(f"r000_issue: {path} binding={d['binding']!r}, "
                         f"expected one of {BINDINGS} -- binding selects which "
                         f"variant of step 005 runs")

    iss = Issue(d, issue_dir)
    _CACHE[issue_id] = iss
    return iss


if __name__ == "__main__":
    # Not a step: running the module prints what a descriptor resolves to, which
    # is the fastest way to check a new issue before a sweep touches anything.
    import sys
    for name in (sys.argv[1:] or sorted(
            n for n in os.listdir(ISSUES_ROOT)
            if os.path.exists(os.path.join(ISSUES_ROOT, n, DESCRIPTOR_NAME)))):
        iss = load(name)
        print(iss)
        for key in ("descriptor", "scan_dir", "thumb_150", "tmp", "colors",
                    "masters600", "ocr_dir", "out_dir", "truth_dir",
                    "review_dir", "report", "worst", "issue_md",
                    "articles_json", "hyphen_cache", "pdf_path"):
            print(f"    {key:14s} {getattr(iss, key)}")
