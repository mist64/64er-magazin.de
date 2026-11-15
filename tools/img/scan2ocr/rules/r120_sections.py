#!/usr/bin/env python3
r"""r120 check 3: map every disk section to the article it feeds, and FAIL loudly.

    $PY tools/img/scan2ocr/rules/r120_sections.py issues/<ID>

Run it at STEP 120 TIME, against the step-120 `prg.txt` -- by the time an issue
is published, 130 has moved every placed listing into its article and the
separators are gone with it (8611's and 8612's published prg.txt have no
numbered separator at all).

WHY THIS IS A SCRIPT AND NOT A COUNT.  The orphan count can only see files
before the FIRST separator; a dropped MID-disk separator merges its files into
the previous article with the count unchanged.  The mapping shows that merge in
one line.  See the rule for the measurements.

WHY IT ASSERTS INSTEAD OF PRINTING.  The version of this check that lived in
the rule as a heredoc skipped any separator it could not find a page number in,
and skipping was silent: on SH09 all 25 separators are spelled `-------s.102----`,
no separator matched its `-+\d+`, every one was taken for a frame bar, and the
check printed NOTHING and exited 0 on an issue with 59 listings in 21 sections.
A mapping with no sections in it is a broken check, not a clean issue, so that
is now the loudest failure here.
"""
import glob, os, re, sys

# The page number a separator carries, by spelling.  ORDER MATTERS, and the
# generic dash-digit form must come LAST.  Every dialect here was measured on a
# real disk; do not loosen one to "any digit in the name" -- SH09's own disks
# carry `-------c128-----` and `----nur 1541----`, which a loose pattern reads
# as page 128 and page 1541.
DIALECTS = [
    # SH09 and on: `-------s.102----`, `-------s.99/100-` (one section, two pages)
    ("s.NN",        r"s\.(\d+)(?:/(\d+))?"),
    # SH8608: `----------c16-10`, `--------vc20-123` -- machine, then the page.
    # `vc20-NN` is caught by the `c20-` branch; spelling the `v` out would need
    # a second alternative for no gain.
    ("machine-NN",  r"c(?:16|64|116|128|20)-(\d+)"),
    # 8611, SH8604: `--------------24` -- dashes, then the page, then dashes
    ("dashes-NN",   r"-(\d+)-*$"),
]


def classify(name):
    for tag, pat in DIALECTS:
        m = re.search(pat, name)
        if m:
            return tag, [int(g) for g in m.groups() if g]
    return None, []


def article_pages(root):
    """printed page -> [article file], from each article's 64er.pages."""
    pages = {}
    for f in sorted(glob.glob(os.path.join(root, "*.html"))):
        m = re.search(r'64er\.pages" content="([^"]+)"',
                      open(f, encoding="utf-8").read())
        if not m:
            continue
        for part in m.group(1).split(","):
            a, _, b = part.strip().partition("-")
            a = re.sub(r"[a-z]$", "", a.strip())
            b = re.sub(r"[a-z]$", "", (b or a).strip())
            if a.isdigit() and b.isdigit():
                for n in range(int(a), int(b) + 1):
                    pages.setdefault(n, []).append(os.path.basename(f))
    return pages


def main(root):
    text = open(os.path.join(root, "prg.txt"), encoding="utf-8").read()
    pages = article_pages(root)

    # The separator population is NOT "comments with dashes in them": it is every
    # directory entry of type `del`.  A del file is a separator, always -- which
    # is why this needs no guess about how the bars are drawn.
    #
    # THE UNIT IS THE <figure>, NOT THE data-filename.  A binary listing carries
    # its name TWICE -- once on the <pre> and once on the download <div> -- so
    # counting filenames double-counts every raw binary and the accounting line
    # reads 86 placed where the truth is 59 (measured on SH09).
    event = re.compile(r'<!--\s*0\s+"([^"]*)"\s+del\s*-->'            # a separator
                       r'|<!--[^>]*\.[Dd]64[^>]*-->'                  # a disk side
                       r'|(<!--(?!\s*0\s).*?-->)'                    # a prose note
                       r'|<figure[^>]*>[^\n]*',                       # a listing
                       re.DOTALL)
    # A PROSE NOTE MAY NOT BE MATCHED WITH `[^>]*`.  130's dispositions quote
    # the HTML they talk about -- SH09's turbotapecopy note contains
    # `<pre>TODO</pre>` -- so a `>`-free body stops at the first tag and the
    # note goes unseen: measured, the one orphan that HAD been explained read
    # as unexplained.

    sections, orphans, nonpage = [], [], []
    cur = None
    side = None
    note = None                     # the prose comment sitting above the next figure
    for m in event.finditer(text):
        whole, name, prose = m.group(0), m.group(1), m.group(2)
        if whole.startswith("<figure"):
            fn = re.search(r'data-filename="([^"]+)"', whole)
            fname = fn.group(1) if fn else "(typed, no disk file)"
            if cur is None:
                orphans.append((side, fname, note))
            else:
                sections[-1]["files"].append(fname)
            note = None
            continue
        if name is not None:
            tag, pgs = classify(name)
            if tag:
                cur = (name, tag, pgs)
                sections.append({"side": side, "name": name, "dialect": tag,
                                 "pages": pgs, "files": []})
            else:
                nonpage.append((side, name))
            note = None
            continue
        if prose is not None:
            note = prose.strip()
            continue
        # A SECOND DISK SIDE RESETS THE SECTION.  Without this, side B's files
        # fall under side A's LAST separator and count as placed: measured on
        # 8611, where side B has nine files and no separators of its own, and
        # the orphan count read 1 where the truth was 10.
        side = re.search(r'([^\s/]+\.[Dd]64)', whole).group(1)
        cur = None
        note = None

    figures = text.count("<figure")
    placed = sum(len(s["files"]) for s in sections)

    print(f"{root}: {figures} figures, {len(sections)} sections, "
          f"{len(nonpage)} non-page del entries, "
          f"{len(pages)} printed pages claimed by {len(set(sum(pages.values(), [])))} articles")
    bad = []

    # NO ARTICLE METADATA IS NOT "NO ARTICLE COVERS THIS PAGE".  Run against a
    # scratch directory holding only a prg.txt, the mapping has nothing to map
    # TO, and the first version of this script answered every section with
    # `NO ARTICLE COVERS THIS PAGE` -- 18 of them on SH09, a flood of false
    # findings where the truth is one missing input.  Two kinds of absent input
    # (HARVEST 11) : say which one this is and stop.
    if not pages:
        print("\nFAIL\n  * no article HTML with a `64er.pages` meta in "
              f"{root} -- the mapping has nothing to map to.  Point this at the "
              "issue directory (its *.html beside its prg.txt), not at a "
              "scratch copy holding the prg.txt alone.")
        return 1
    for s in sections:
        arts = [a for p in s["pages"] for a in pages.get(p, [])]
        flag = "" if arts else "   <- NO ARTICLE COVERS THIS PAGE"
        if not arts:
            bad.append(f"section {s['name']!r} -> page {s['pages']}: no article covers it")
        print(f"  {s['side']}  {s['name']!r:20s} {s['dialect']:11s} "
              f"page {','.join(map(str, s['pages'])):8s} -> "
              f"{', '.join(sorted(set(arts))) or '-'}{flag}")
        print(f"      {len(s['files'])} files: {', '.join(s['files'][:8])}"
              f"{' ...' if len(s['files']) > 8 else ''}")

    # EYEBALL THESE ONCE.  A separator the dialects do not read is listed, never
    # skipped quietly: an all-dash frame bar and a `-- basic-kurs --` name bar
    # belong here, a section does not.
    if nonpage:
        print("\n  del entries carrying no page number (frames, names, machines):")
        for sd, n in nonpage:
            print(f"      {sd}  {n!r}")

    # AN ORPHAN IS A TRIAGE ITEM, NOT AUTOMATICALLY A FAILURE.  Every SH09-era
    # disk opens with an intro screen that sits before the first separator and
    # is never placed (leser-info is closed, owner 2026-10-07), so a check that
    # simply fails on an orphan goes red on a correct build.  What may not
    # happen is an orphan NOBODY HAS SAID ANYTHING ABOUT: the disposition is the
    # prose comment 130 writes above the figure, and that comment is what turns
    # this green.
    if orphans:
        print(f"\n  ORPHAN listings, under no section ({len(orphans)}):")
        for sd, f, nt in orphans:
            print(f"      {sd}  {f}")
            print(f"          {nt if nt else '<- NO COMMENT SAYS WHERE THIS GOES'}")
        unexplained = [f for _, f, nt in orphans if not nt]
        if unexplained:
            bad.append(f"{len(unexplained)} orphan listings with no comment: "
                       + ", ".join(unexplained))

    # THE VACUOUS CASE IS THE LOUDEST ONE -- and it has two causes that must not
    # be confused: the wrong FILE, or a dialect this script cannot read.
    if figures and not sections:
        if not nonpage:
            bad.append("there are no disk directory entries in this prg.txt at "
                       "all, so this is a POST-130 file: 130 has already moved "
                       "the placed listings into their articles and taken the "
                       "separators with them.  Run this against the step-120 "
                       "prg.txt (git show <the 120 commit>:issues/<ID>/prg.txt).")
        else:
            bad.append("NO SECTION AT ALL was recognised while the issue has "
                       f"{figures} listings and {len(nonpage)} directory "
                       "entries -- the separators on this disk are spelled in a "
                       "dialect DIALECTS does not know.  Read the del entries "
                       "above, add the spelling, and re-run.  Do not read this "
                       "as a clean issue.")
    if figures != placed + len(orphans):
        bad.append(f"accounting: {figures} figures but {placed} placed + "
                   f"{len(orphans)} orphans")

    if bad:
        print("\nFAIL")
        for b in bad:
            print("  *", b)
        return 1
    print("\nOK -- every listing sits under a section whose page an article covers.")
    print("   Now READ the mapping: a section whose file count jumped is a "
          "merge, which is invisible to any count.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
