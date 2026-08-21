#!/usr/bin/env python3
"""330 -- the deterministic half of the reprint comparison.

Rule 330 (`r330_reprint_compare.md`) is an editorial rule: the judgement it asks
for -- *which side misread its own printed page* -- is a reading of a 600 dpi
crop and cannot be scripted.  What CAN be scripted, and must be, so that two
runs of the rule produce the same list to argue about:

  resolve   `YYMM/PAGE` -> the published article file whose `64er.pages` range
            covers PAGE.  Never by filename: the filename carries the START
            page, and four of SH8601's seven leads point into the middle of a
            multi-page article (`8506/16` lives in `16-24,26-28`).

  diff      two article HTMLs -> a numbered, stable list of textual
            differences, with the markup, the whitespace and the end-of-line
            hyphenation taken out of the way first.

The normalisation is deliberately narrow.  It removes only what is an artifact
of *storage* -- tags, entities, line wrapping, soft hyphenation.  It does NOT
touch spelling, case, punctuation, quotation marks, dashes or numbers, because
those are exactly the places a transcription error hides.  A normaliser that
tidied `»` to `"` would delete the finding it was run to produce.

Nothing here decides anything.  Every difference it prints goes to a human (or
a sub-agent reading the scan) for a disposition; see the rule .md.

stdlib only, on purpose -- this runs at the end of an issue build, where a
missing wheel must not be the reason the last gate did not run.
"""

from __future__ import annotations

import argparse
import difflib
import glob
import html.parser
import io
import os
import re
import sys
import unicodedata

# Block-level elements whose text is compared, each becoming one aligned unit.
BLOCK_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "li", "dt", "dd", "figcaption", "address",
    "td", "th", "caption", "blockquote",
}

# Never compared.  <pre>/<code> hold program listings, which are not
# transcribed prose: they come from the Programm-Service disk via rule 120 and
# are byte-identical or deliberately different for reasons rule 300 owns.
SKIP_TAGS = {"head", "script", "style", "pre", "code", "noscript", "template"}

PAGES_META = re.compile(r'<meta\s+name="64er\.pages"\s+content="([^"]*)"', re.I)
ISSUE_META = re.compile(r'<meta\s+name="64er\.issue"\s+content="([^"]*)"', re.I)
TITLE_TAG = re.compile(r"<title>(.*?)</title>", re.I | re.S)

# A hyphen followed by whitespace between two word characters, the lowercase
# continuation marking it as a broken word rather than a compound.
SOFT_HYPHEN = re.compile(r"(\w)[-‐­]\s+([a-zäöüßéèàçñ])")

TOKEN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


class Block:
    __slots__ = ("role", "text", "tokens", "index", "hyphen_joins")

    def __init__(self, role, text, index, hyphen_joins):
        self.role = role
        self.text = text
        self.index = index
        self.hyphen_joins = hyphen_joins
        self.tokens = TOKEN.findall(text)

    def __repr__(self):
        return f"<Block {self.index} {self.role} {self.text[:40]!r}>"


class _Extractor(html.parser.HTMLParser):
    """HTML -> a list of block-level text runs, in document order."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self._buf = []
        self._role = None
        self._skip = 0

    # -- helpers ---------------------------------------------------------
    def _flush(self):
        if self._role is not None:
            raw = "".join(self._buf)
            text, joins = normalise(raw)
            if text:
                self.blocks.append(Block(self._role, text, len(self.blocks), joins))
        self._buf = []
        self._role = None

    # -- parser callbacks ------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self._skip += 1
            return
        if self._skip:
            return
        if tag == "br":
            self._buf.append(" ")
            return
        if tag in BLOCK_TAGS:
            self._flush()
            cls = dict(attrs).get("class", "").split()
            self._role = tag + ("." + cls[0] if cls else "")

    def handle_startendtag(self, tag, attrs):
        if tag == "br" and not self._skip:
            self._buf.append(" ")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
            return
        if self._skip:
            return
        if tag in BLOCK_TAGS:
            self._flush()

    def handle_data(self, data):
        if not self._skip and self._role is not None:
            self._buf.append(data)


def normalise(raw):
    """Storage artifacts out, everything else untouched.

    Returns (text, hyphen_join_count).  The joins are counted rather than
    silently swallowed: a broken word that survived into published HTML is
    itself a defect worth reporting, even though it must not be allowed to
    drown the diff.
    """
    text = unicodedata.normalize("NFC", raw)
    # Space-like characters that mean "space" and nothing else.
    text = text.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    text = text.replace("​", "").replace("﻿", "")
    text, joins = SOFT_HYPHEN.subn(r"\1\2", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text, joins


def extract(path):
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    ex = _Extractor()
    ex.feed(src)
    ex.close()
    ex._flush()
    meta = {
        "path": path,
        "label": os.path.basename(os.path.dirname(os.path.abspath(path))) or path,
        "pages": (PAGES_META.search(src).group(1) if PAGES_META.search(src) else "?"),
        "issue": (ISSUE_META.search(src).group(1) if ISSUE_META.search(src) else "?"),
        "title": (TITLE_TAG.search(src).group(1).strip() if TITLE_TAG.search(src) else "?"),
    }
    return meta, ex.blocks


# ---------------------------------------------------------------------------
# resolve
# ---------------------------------------------------------------------------

def parse_pages(spec):
    """`16-24,26-28` -> {16..24, 26..28}."""
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+)\s*-\s*(\d+)$", part)
        if m:
            out.update(range(int(m.group(1)), int(m.group(2)) + 1))
            continue
        m = re.match(r"^(\d+)", part)
        if m:
            out.add(int(m.group(1)))
    return out


class ResolveError(Exception):
    """The reference could not even be looked up (bad syntax, no such issue)."""


def resolve(repo, ref):
    """`8506/16` -> EVERY published article in issues/8506 covering page 16.

    Every one, always.  A magazine page routinely carries the end of one
    article and the start of the next, so a page number is not a key: page 47
    of 8601 is the last page of `44 Die neuen Laufwerke Commodore-1570/1571`
    (`44-47`) AND the first page of `47 Gestatten: Wordstar` (`47-48`), and the
    Sonderheft's retitled `Test: WordStar` is a reprint of the second.
    Returning the first covering match would have picked the wrong one and
    hidden that there was a choice at all.

    This function therefore never selects.  Callers get the whole list.
    """
    m = re.match(r"^(SH)?(\d{4})[/ ](\d+)$", ref.strip(), re.I)
    if not m:
        raise ResolveError(f"cannot parse reference {ref!r}; want e.g. 8506/16")
    issue = (m.group(1) or "").upper() + m.group(2)
    page = int(m.group(3))
    issue_dir = os.path.join(repo, "issues", issue)
    if not os.path.isdir(issue_dir):
        raise ResolveError(f"no such issue directory: {issue_dir}")
    hits = []
    for path in sorted(glob.glob(os.path.join(issue_dir, "*.html"))):
        with open(path, encoding="utf-8") as fh:
            head = fh.read(8192)
        m2 = PAGES_META.search(head)
        if m2 and page in parse_pages(m2.group(1)):
            t = TITLE_TAG.search(head)
            hits.append((path, m2.group(1), t.group(1).strip() if t else "?"))
    return issue, page, hits


def content_match(a_blocks, b_blocks, min_sim=0.45):
    """How much of two articles' prose is shared, as (block %, word %).

    An ORDERING aid for a shared page, nothing else.  Two of SH8601's seven
    leads are retitled in the Sonderheft (`Test: WordStar` for
    `Gestatten: Wordstar`, `Der C128D im ersten Test` for `Der C128 D im
    ersten Test`), so the title cannot disambiguate and the text has to.  It
    still does not decide -- see the rule .md, step 2.
    """
    pairing = align(a_blocks, b_blocks, min_sim)
    aligned = sum(1 for x, y in pairing if x is not None and y is not None)
    denom = max(len(a_blocks), len(b_blocks)) or 1

    def bag(blocks):
        c = {}
        for blk in blocks:
            for t in blk.tokens:
                if len(t) >= 4 and t[0].isalpha():
                    k = t.lower()
                    c[k] = c.get(k, 0) + 1
        return c

    ba, bb = bag(a_blocks), bag(b_blocks)
    shared = sum(min(v, bb.get(k, 0)) for k, v in ba.items())
    floor = min(sum(ba.values()), sum(bb.values())) or 1
    return 100 * aligned // denom, 100 * shared // floor


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------

def similarity(a, b):
    return difflib.SequenceMatcher(None, a.text, b.text, autojunk=False).ratio()


def align(a_blocks, b_blocks, min_sim):
    """Pair the two block lists.

    Anchor on exact matches first (SequenceMatcher over the normalised block
    texts), then pair what is left inside each unmatched region by best
    similarity above `min_sim`.  A re-set reprint keeps most paragraphs word
    for word, so the anchors are plentiful and the fuzzy pass only has to cope
    with the genuinely re-edited ones.

    Yields (a_block | None, b_block | None) in document order.
    """
    sm = difflib.SequenceMatcher(
        None, [b.text for b in a_blocks], [b.text for b in b_blocks], autojunk=False
    )
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out.append((a_blocks[i1 + k], b_blocks[j1 + k]))
            continue
        left = list(a_blocks[i1:i2])
        right = list(b_blocks[j1:j2])
        pairs = []
        for x in left:
            best, best_r = None, min_sim
            for y in right:
                r = similarity(x, y)
                if r > best_r:
                    best, best_r = y, r
            if best is not None:
                pairs.append((x, best))
                right.remove(best)
        paired_left = {id(x) for x, _ in pairs}
        merged = []
        pair_by_left = {id(x): y for x, y in pairs}
        for x in left:
            merged.append((x, pair_by_left.get(id(x))) if id(x) in paired_left else (x, None))
        for y in right:
            merged.append((None, y))
        merged.sort(key=lambda p: (p[0].index if p[0] else 10**6 + p[1].index))
        out.extend(merged)
    return out


def window(tokens, lo, hi, context):
    pre = " ".join(tokens[max(0, lo - context):lo])
    mid = " ".join(tokens[lo:hi])
    post = " ".join(tokens[hi:hi + context])
    return pre, mid, post


def diff_report(a_path, b_path, context=6, min_sim=0.45, out=sys.stdout):
    a_meta, a_blocks = extract(a_path)
    b_meta, b_blocks = extract(b_path)
    A, B = a_meta["label"], b_meta["label"]
    w = max(len(A), len(B))

    print("=" * 78, file=out)
    for meta in (a_meta, b_meta):
        print(
            f'{meta["label"]:<{w}}  {meta["path"]}\n'
            f'{"":<{w}}  issue={meta["issue"]}  pages={meta["pages"]}  title={meta["title"]!r}\n'
            f'{"":<{w}}  blocks={len(a_blocks) if meta is a_meta else len(b_blocks)}'
            f'  words={sum(len(x.tokens) for x in (a_blocks if meta is a_meta else b_blocks))}',
            file=out,
        )
    print("=" * 78, file=out)

    n = 0
    pairing = align(a_blocks, b_blocks, min_sim)
    aligned = sum(1 for x, y in pairing if x is not None and y is not None)
    for x, y in pairing:
        if x is not None and y is not None and x.text == y.text:
            continue
        if x is None or y is None:
            n += 1
            side = B if x is None else A
            blk = y if x is None else x
            print(f"\nD-{n:03d}  BLOCK ONLY IN {side}  <{blk.role}>", file=out)
            print(f"  {side:<{w}}: {blk.text}", file=out)
            print(f"  {(A if x is None else B):<{w}}: (nothing aligned)", file=out)
            continue
        sm = difflib.SequenceMatcher(None, x.tokens, y.tokens, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            n += 1
            pre_a, mid_a, post_a = window(x.tokens, i1, i2, context)
            pre_b, mid_b, post_b = window(y.tokens, j1, j2, context)
            role = x.role if x.role == y.role else f"{x.role}|{y.role}"
            # difflib's opcode names describe turning A into B, which reads
            # backwards at review time ("INSERT" on the side that is MISSING
            # the words).  Name the side instead; nobody has to hold the
            # direction of the transform in their head.
            kind = {"replace": "DIFFERS",
                    "insert": f"ONLY IN {B}",
                    "delete": f"ONLY IN {A}"}[tag]
            print(f"\nD-{n:03d}  {kind}  <{role}>", file=out)
            print(f"  {A:<{w}}: …{pre_a} 〈{mid_a}〉 {post_a}…", file=out)
            print(f"  {B:<{w}}: …{pre_b} 〈{mid_b}〉 {post_b}…", file=out)

    ja = sum(x.hyphen_joins for x in a_blocks)
    jb = sum(x.hyphen_joins for x in b_blocks)
    if ja or jb:
        print(
            f"\nNOTE  end-of-line hyphenation joined before diffing: "
            f"{A}={ja}, {B}={jb}.  Normalised out of the diff above, but a "
            f"broken word in published HTML is its own defect -- check them.",
            file=out,
        )
    # An alignment rate is a shape, not a verdict.  A re-set reprint pairs
    # nearly every paragraph; two unrelated articles pair almost none.  It is
    # a cheap sanity light on the lead -- the confirmation itself is the
    # printed page (see the rule .md, step 1), never this number.
    denom = max(len(a_blocks), len(b_blocks)) or 1
    print(f"\nALIGNED: {aligned}/{denom} blocks paired ({100 * aligned // denom}%)", file=out)
    print(f"DIFFS: {n}", file=out)
    return n


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------

VERDICTS = {"CONFIRMED", "PARTIAL", "NOT-A-REPRINT", "UNRESOLVED"}
CAND_LINE = re.compile(r"^\s*[-*]\s+(CANDIDATE|REJECTED)\s+`([^`]+)`")
DISPOSITIONS = {"OURS", "THEIRS", "PRINT", "UNRESOLVED"}
DISP_LINE = re.compile(r"^\s*[-*]\s+D-(\d{3})\s+([A-Z-]+)\b")
STEP_HEAD = re.compile(r"^##\s+Step\s+330\b", re.M)
NEXT_H2 = re.compile(r"^##\s+(?!#)", re.M)


def _cells(line):
    parts = [c.strip() for c in line.strip().strip("|").split("|")]
    return [re.sub(r"^`|`$", "", c) for c in parts]


def _log_section(log_text):
    m = STEP_HEAD.search(log_text)
    if not m:
        return None
    rest = log_text[m.end():]
    nxt = NEXT_H2.search(rest)
    return rest[: nxt.start()] if nxt else rest


def verify(repo, issue_dir):
    problems = []
    issue_dir = issue_dir.rstrip("/")
    reprints = os.path.join(issue_dir, "REPRINTS.md")
    log = os.path.join(issue_dir, "LOG.md")

    if not os.path.isfile(log):
        print(f"FAIL: {log} does not exist")
        return 1

    section = _log_section(open(log, encoding="utf-8").read())
    if section is None:
        print(f"FAIL: {log} has no '## Step 330 …' section")
        return 1

    rows = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        c = _cells(line)
        if len(c) < 4 or c[0] in ("verdict",) or set(c[0]) <= set("-: "):
            continue
        rows.append(c)

    if not os.path.isfile(reprints):
        print(f"OK: no {reprints}; nothing claimed, {len(rows)} pair(s) recorded anyway")
    else:
        claimed = set()
        in_leads = False
        for line in open(reprints, encoding="utf-8"):
            if line.startswith("## Leads"):
                in_leads = True
                continue
            if in_leads and line.startswith("## "):
                in_leads = False
            if in_leads and line.strip().startswith("|"):
                c = _cells(line)
                if len(c) >= 2 and c[1] not in ("claimed original",) and not set(c[1]) <= set("-: "):
                    for part in c[1].split("+"):
                        if re.search(r"\d{4}/\d+", part):
                            claimed.add(part.strip())
        logged = {r[2] for r in rows}
        for lead in sorted(claimed):
            if lead not in logged:
                problems.append(f"lead {lead} from REPRINTS.md has no row in the Step 330 LOG table")

    def subsection(key, lead, want_lead):
        """The `###` chunk naming this issue's file (and the lead, if needed)."""
        heads = list(re.finditer(r"^###\s.*$", section, re.M))
        for k, m in enumerate(heads):
            if key not in m.group(0):
                continue
            if want_lead and lead not in m.group(0):
                continue
            end = heads[k + 1].start() if k + 1 < len(heads) else len(section)
            return section[m.end():end]
        return None

    for r in rows:
        verdict, sh_file, lead = r[0], r[1], r[2]
        monthly = r[3] if len(r) > 3 else "—"
        key = os.path.basename(sh_file)
        if verdict not in VERDICTS:
            problems.append(f"{lead}: verdict {verdict!r} not one of {sorted(VERDICTS)}")
            continue

        # Re-resolve the lead ourselves.  The whole point: a page number is not
        # a key -- a magazine page carries the end of one article and the start
        # of the next -- so a row naming exactly one monthly file proves nothing
        # about whether there was a choice to make.  8601/47 resolves to TWO
        # articles, and the wrong one is the first in sort order.
        try:
            _, page, cands = resolve(repo, lead)
        except ResolveError as e:
            cands = []
            if verdict not in ("NOT-A-REPRINT", "UNRESOLVED"):
                problems.append(f"{lead}: {e} -- an unlookupable lead is UNRESOLVED, not {verdict}")
                continue
        cand_paths = {os.path.abspath(c[0]) for c in cands}

        if verdict == "UNRESOLVED":
            if monthly != "—":
                problems.append(f"{lead}: UNRESOLVED must leave the monthly file column as '—'")
            chunk = subsection(key, lead, True)
            if chunk is None:
                problems.append(f"{lead}: UNRESOLVED with no '### …{key}… ← {lead}' subsection "
                                "-- an unresolved lead must be reported, not merely marked")
                continue
            listed = [m.group(2) for line in chunk.splitlines()
                      for m in [CAND_LINE.match(line)] if m]
            if len(listed) != len(cands):
                problems.append(
                    f"{lead}: resolves to {len(cands)} candidate(s) but the subsection lists "
                    f"{len(listed)} -- every candidate considered must be named for review")
            else:
                print(f"OK: {key} ← {lead} — UNRESOLVED, {len(cands)} candidate(s) reported")
            continue

        if verdict == "NOT-A-REPRINT":
            continue

        # CONFIRMED / PARTIAL: the named monthly must be one the page actually
        # resolves to, and every other candidate must be explicitly rejected.
        if not cands:
            problems.append(f"{lead}: resolves to no article, so it cannot be {verdict}")
            continue
        if os.path.abspath(os.path.join(repo, monthly)) not in cand_paths:
            problems.append(f"{lead}: the monthly file in the table is not one of the "
                            f"{len(cands)} article(s) covering page {page}: {monthly}")
            continue
        if len(cands) > 1:
            chunk = subsection(key, lead, True) or subsection(key, lead, False)
            rejected = set()
            if chunk:
                for line in chunk.splitlines():
                    m = CAND_LINE.match(line)
                    if m and m.group(1) == "REJECTED":
                        rejected.add(os.path.abspath(os.path.join(repo, m.group(2))))
            others = cand_paths - {os.path.abspath(os.path.join(repo, monthly))}
            missing_rej = others - rejected
            if missing_rej:
                problems.append(
                    f"{lead}: page {page} is shared by {len(cands)} articles; the other "
                    f"candidate(s) must be named on a '- REJECTED `…` — why' line: "
                    + ", ".join(sorted(os.path.relpath(x, repo) for x in missing_rej)))
                continue
            # A rejection line proves a choice was WRITTEN DOWN, not that it was
            # right.  So cross-check it the one way a script honestly can: if a
            # rejected candidate shares far more text with this issue's article
            # than the chosen one does, the recorded decision contradicts the
            # text and a human has to look again.  The scores do not decide
            # which article is the original -- they only refuse to let a
            # first-hit pick wear a rejection line as cover.
            try:
                _, sh_blocks = extract(os.path.join(repo, sh_file))
                chosen_score = content_match(sh_blocks, extract(os.path.join(repo, monthly))[1])
                for other in sorted(others):
                    o = content_match(sh_blocks, extract(other)[1])
                    if chosen_score[0] * 2 <= o[0] and chosen_score[1] < o[1]:
                        problems.append(
                            f"{lead}: the REJECTED `{os.path.relpath(other, repo)}` shares far "
                            f"more text with {key} ({o[0]}% blocks / {o[1]}% words) than the "
                            f"chosen `{monthly}` does ({chosen_score[0]}% / {chosen_score[1]}%). "
                            "Re-read both printed pages before this row stands.")
            except OSError as e:
                problems.append(f"{lead}: could not score the candidates: {e}")
                continue
            print(f"NOTE: {lead} was ambiguous ({len(cands)} candidates); "
                  f"{len(others)} explicitly rejected")
        for p in (sh_file, monthly):
            if not os.path.isfile(os.path.join(repo, p)):
                problems.append(f"{lead}: file named in the LOG table does not exist: {p}")
        if problems and any(lead in p for p in problems):
            continue
        buf = io.StringIO()
        n = diff_report(os.path.join(repo, sh_file), os.path.join(repo, monthly), out=buf)
        # The dispositions for this pair live under the `###` subsection whose
        # heading names this issue's file.  Anchor on the heading LINE, not on
        # the first occurrence of the basename anywhere in the section -- that
        # is the table row above, and cutting the chunk there would end it at
        # the very heading we are looking for.
        chunk = None
        heads = [m for m in re.finditer(r"^###\s.*$", section, re.M)]
        for k, m in enumerate(heads):
            if key not in m.group(0):
                continue
            if verdict == "PARTIAL" and lead not in m.group(0):
                continue  # one subsection per original, disambiguated by lead
            end = heads[k + 1].start() if k + 1 < len(heads) else len(section)
            chunk = section[m.end():end]
            break
        if chunk is None:
            problems.append(f"{lead}: no '### …{key}…' disposition subsection")
            continue
        seen = {}
        before = len(problems)
        for line in chunk.splitlines():
            m = DISP_LINE.match(line)
            if m:
                i, tok = int(m.group(1)), m.group(2)
                if tok not in DISPOSITIONS:
                    problems.append(f"{key} D-{i:03d}: disposition {tok!r} not one of {sorted(DISPOSITIONS)}")
                if i in seen:
                    problems.append(f"{key} D-{i:03d}: dispositioned twice")
                seen[i] = tok
        missing = [i for i in range(1, n + 1) if i not in seen]
        extra = [i for i in seen if i > n]
        if missing:
            problems.append(f"{key}: {len(missing)} difference(s) with no disposition: "
                            + ", ".join(f"D-{i:03d}" for i in missing[:10])
                            + (" …" if len(missing) > 10 else ""))
        if extra:
            problems.append(f"{key}: disposition for a difference the diff no longer reports: "
                            + ", ".join(f"D-{i:03d}" for i in sorted(extra)))
        # The table's own counts must agree with the dispositions below it --
        # otherwise a summary row can quietly say "all editorial" over a list
        # that says otherwise.
        if len(r) >= 9:
            try:
                stated = int(r[4])
                buckets = [int(x) for x in r[5:9]]
            except ValueError:
                problems.append(f"{lead}: D / OURS / THEIRS / PRINT / UNRESOLVED must be numbers")
            else:
                if stated != n:
                    problems.append(f"{lead}: table says D={stated}, the diff reports {n}")
                if sum(buckets) != stated:
                    problems.append(f"{lead}: OURS+THEIRS+PRINT+UNRESOLVED={sum(buckets)} != D={stated}")
                actual = [sum(1 for t in seen.values() if t == d)
                          for d in ("OURS", "THEIRS", "PRINT", "UNRESOLVED")]
                if actual != buckets:
                    problems.append(f"{lead}: table counts {buckets} != dispositions {actual} "
                                    "(OURS, THEIRS, PRINT, UNRESOLVED)")

        if len(problems) == before:
            print(f"OK: {key} ← {lead} — {n} difference(s), all dispositioned")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"\nOK: {len(rows)} pair(s) verified")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="r330_reprint_compare.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("resolve", help="YYMM/PAGE -> the published article covering that page")
    r.add_argument("ref", help="e.g. 8506/16, 8512/78, SH8508/137")
    r.add_argument("--repo", default=".", help="repository root (default: cwd)")
    r.add_argument("--against", metavar="HTML",
                   help="this issue's article; orders shared-page candidates by shared text "
                        "(an ordering aid -- it never picks one)")

    d = sub.add_parser("diff", help="numbered textual differences between two article HTMLs")
    d.add_argument("a", help="this issue's article (the reprint)")
    d.add_argument("b", help="the published monthly's article")
    d.add_argument("--context", type=int, default=6, help="tokens of context each side (default 6)")
    d.add_argument("--min-similarity", type=float, default=0.45,
                   help="below this, two blocks are not the same paragraph (default 0.45)")

    v = sub.add_parser("verify", help="the rule's gate: every lead has a verdict, every difference a disposition")
    v.add_argument("issue_dir", help="e.g. issues/SH8601")
    v.add_argument("--repo", default=".", help="repository root (default: cwd)")

    args = ap.parse_args(argv)

    if args.cmd == "verify":
        return verify(args.repo, args.issue_dir)

    if args.cmd == "resolve":
        try:
            issue, page, hits = resolve(args.repo, args.ref)
        except ResolveError as e:
            print(f"UNRESOLVED: {e}")
            return 1
        if not hits:
            print(f"UNRESOLVED: no article in issues/{issue} has page {page} in 64er.pages.")
            print("  The original is in an issue that is not imported yet.  Record the lead")
            print("  as UNRESOLVED for human review; this is not a refutation of the lead.")
            return 1

        scored = []
        sh_blocks = None
        if args.against:
            if not os.path.isfile(args.against):
                raise SystemExit(f"r330: no such file: {args.against}")
            _, sh_blocks = extract(args.against)
        for path, pages, title in hits:
            score = content_match(sh_blocks, extract(path)[1]) if sh_blocks else None
            scored.append((score, path, pages, title))
        if sh_blocks:
            scored.sort(key=lambda r: r[0], reverse=True)

        for score, path, pages, title in scored:
            print(f'{path}\n  pages={pages}  title={title!r}')
            if score:
                print(f'  content match vs {os.path.basename(args.against)}: '
                      f'{score[0]}% of blocks, {score[1]}% of words')

        if len(hits) == 1:
            return 0

        print(f"\nAMBIGUOUS: page {page} is shared by {len(hits)} articles.")
        print("  A magazine page carries the end of one article and the start of the next,")
        print("  so the page number does NOT identify the original.  Do not take the first")
        print("  or the highest-scoring one.  Disambiguate by CONTENT -- read this issue's")
        print("  article against each candidate's printed page (step 1 of the rule).  The")
        print("  lead's title is a hint, not authority: two of SH8601's leads are retitled.")
        if not sh_blocks:
            print("  Re-run with --against <this issue's article.html> to order the")
            print("  candidates by shared text before you read the pages.")
        print("  If the pages cannot separate them, the lead is UNRESOLVED -- report it")
        print("  for human review; never guess.")
        return 2

    for p in (args.a, args.b):
        if not os.path.isfile(p):
            raise SystemExit(f"r330: no such file: {p}")
    diff_report(args.a, args.b, context=args.context, min_sim=args.min_similarity)
    return 0


if __name__ == "__main__":
    sys.exit(main())
