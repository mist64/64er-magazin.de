#!/usr/bin/env python3
"""
Stage D of the article-corpus pipeline: an issue's pages -> one issue markdown.

    out/NNN.labels.json  ->  <ID>.md   every article, in issue order
                         ->  articles.json   the structure, machine-readable

Stage C answers "what is on THIS page".  Stage D answers the questions that
only exist once the pages are put back together:

  1. Where does an article begin and end?  A page can hold the end of one and
     the start of the next, so the unit is the PARAGRAPH, not the page.
  2. A paragraph running over a page break is one paragraph.  Every page
     boundary was a false paragraph break until this stage existed.
  3. An article interrupted by twenty pages of listings resumes later --
     "Fortsetzung auf Seite 146".  However many the issue prints; each is
     confirmed in BOTH directions before it is joined.
  4. A hyphen at a line end was left as a marker by stage A because no local
     rule resolves it.  Here it finally gets resolved.

Only the FIRST of those needs judgement, and it gets one LLM call for the whole
issue: the running heads, the table of contents and the headline fragments are
all evidence about the same question, and they only make sense together.
Everything else in this file is deterministic.
"""

import hashlib
import json
import os
import re
import sys

import r000_issue
from r000_issue import ISSUE
import r000_llm as llm
from r020_classify import (PARA_INDENT_MIN_PX, ROLE_PREFIX,
                           SOURCE_HTML, SOURCE_JOIN, ends_dangling,
                           join_runons, join_text, page_paragraphs)

# ---------------------------------------------------------------------------
# CONSTANTS  (no CLI knobs, no env knobs -- see CLAUDE.md)
# ---------------------------------------------------------------------------

# The ONE knob, and it lives in r000_issue -- imported above, not declared
# here.  Everything below is derived from issues/<ID>/issue.json, so there is no
# second path, and no second ISSUE, to forget when the issue changes.  See
# r000_issue.py.
ISS = r000_issue.load(ISSUE)

PAGES = ISS.page_range
OUT_DIR = ISS.out_dir
ISSUE_MD = ISS.issue_md
ARTICLES_JSON = ISS.articles_json
# Resolved hyphens are cached, because the answer for a given broken word never
# changes and one issue holds thousands of distinct ones (3459 in 8609).
# Delete to re-ask.
HYPHEN_CACHE = ISS.hyphen_cache

# The magazine's own cross-reference, printed at the foot of a page whose
# article resumes later and at the head of the page where it does.  Both are
# apparatus: once the article is assembled they are not just redundant but
# wrong, since the text runs straight through.  The page range in the title
# carries what they said.
FORTSETZUNG = re.compile(r"Fortsetzung\s+(auf|von)\s+Seite\s+(\d+)", re.I)

# The issue's contents, the one place that names the major articles and the page
# each starts on.  It is NOT a fixed page pair and must not be compiled in: 8609
# sets it on 6-7, older monthlies on 4-5, and a Sonderheft wherever its front
# matter happens to end (SH8507's first article is page 3).  So the pages are
# FOUND, from stage B's own labels, by toc_pages() below.
#
# Two things make finding them harder than "every toc-labelled block":
#   - stage B labels the COVER "toc" as well, and the cover is nothing but OCR
#     noise off display type;
#   - a page deep in the back matter can carry far MORE toc-labelled text than
#     the contents page does -- 8609's p171 (the year's index) scores 7973
#     characters against the real contents pages' 2129 and 2079.
# Both are excluded by looking only in the front matter, after the cover.  A
# score threshold alone would pick the wrong page; a "highest score" alone would
# pick the back matter.
TOC_FRONT_MATTER = 16    # last page that can plausibly hold the contents
TOC_SKIP_COVER = 1       # page 1 is the cover: display type, not a contents list
TOC_MIN_CHARS = 300      # a contents page is dense; a stray toc label is not
TOC_MAX_PAGES = 4        # a contents spread, generously; more means the label is wrong

# The byline in this magazine sits in parentheses at the very end of the last
# paragraph, welded onto the sentence by the OCR because that is how it is
# printed.  Two forms, MEASURED at 41 occurrences each:
#   (bs)                    an editor's initials -- a news item written in house
#   (Knut Smoczyk/tr)       a reader's name, then the editor who took it in
# Both end in exactly two lowercase letters.  Two and not three: three starts
# matching German abbreviations, and nobody in this issue signs with three.
# A byline is always its own paragraph.
BYLINE = re.compile(r"\s*\((?:[^()]{2,45}?/)?[a-zäöü]{2}\)\s*\.?\s*$")

# Headline fragments, the table of contents and the running heads are all shown
# to the model; this is how much of a paragraph it needs to recognise one.
SNIPPET = 160
PREV_SNIPPET = 90

# Unique broken words per LLM call.  Large enough that the whole issue is ~18
# calls, small enough that one bad reply costs little.
HYPHEN_BATCH = 200

# What `kind` licenses the model to EXPECT.  Not what to find: the evidence
# still decides, and the note says so in both branches.  A monthly is a bundle
# of departments, standing columns and features; a Sonderheft is one theme end
# to end, where the running head names the section of the book and every piece
# under it prints its own headline -- so nearly everything is an article and a
# department would be the exception.  Getting this backwards is expensive in one
# direction only: a missed boundary merges two articles, a false one strands the
# second half of an article with no headline.
KIND_NOTES = {
    "monthly": (
        "This is a MONTHLY issue: expect several DEPARTMENTS and standing "
        "COLUMNS (a news run, a reader-mail rubric, tips columns) among the "
        "feature articles. Expect, do not assume -- the evidence below decides."),
    "sonderheft": (
        "This is a SONDERHEFT (special issue): one theme from cover to cover. "
        "The running head normally names the SECTION OF THE BOOK, and every "
        "piece under it prints its own headline, so nearly every unit is an "
        "ARTICLE and a DEPARTMENT is the exception rather than the rule. It is "
        "still possible -- but it needs the same evidence as anywhere else, "
        "namely a run with no headline of its own."),
}

# The prompt is issue-AGNOSTIC.  Everything that is true of one issue only --
# which runs are departments, which are columns, what the columns are called --
# is EVIDENCE, and reaches the model through {toc} and {candidates}, which are
# read off this issue's own contents page and running heads.  It used to name
# 8609's departments and columns inline; that is a compiled-in answer to the
# question being asked, and it is wrong for every other issue -- a Sonderheft
# has neither.  {kind_note} says what shape to EXPECT, never what to find.
BOUNDARY_PROMPT = """You are reassembling one issue of the German home-computer magazine
"64'er" (issue {issue_id}) from its pages back into its articles.
{kind_note}

Below is one entry per CANDIDATE ARTICLE BOUNDARY, in reading order, together with
the running head printed on that page and the table of contents. Decide for each
candidate whether an article actually begins there.

A candidate is one of:
  page-start  the first paragraph of a page. Usually NOT a new article -- most
              pages continue the one before -- but an article that begins at the
              top of a page with its headline lost to OCR begins here.
  title       a paragraph the page-level pass judged to be a headline.
  cont-marker a "Fortsetzung von Seite N" cross-reference.
  after-cont  a paragraph on a page that resumes an interrupted article. The
              page may ALSO carry the end of the article that ran onto it from
              the previous page, and nothing marks where one stops and the
              other starts except the sense of the text.

Actions:
  start     an article begins at this paragraph. Give its clean "title".
            Normally the paragraph IS the headline and is consumed as the title.
            For a DEPARTMENT (see below) the title is the running head instead
            and the paragraph is the first item heading inside it, so add
            "keep_heading": true and it stays in the text as a section heading.
  continue  no boundary; the paragraph stays where it is, rendered as it is.
  resume    only for "after-cont": the interrupted article's continuation ENDS
            before this paragraph, and from here the page goes back to the
            article that was running before it. Use it when the paragraph
            plainly belongs to a different subject -- above all when it
            continues a sentence or a word broken off at the foot of the
            PREVIOUS page. At most one "resume" per continuation, and none at
            all when the continuation runs to the end of the page.
  drop      the paragraph must be REMOVED from the corpus. Use this for:
            - a display headline OCR split into fragments: mark the FIRST
              fragment "start" with the whole headline assembled as its title,
              and every following fragment "drop".
            - a headline repeated on a continuation page.
            - a "Fortsetzung von/auf Seite N" cross-reference.
            - a section divider that is not an article: a page or banner that
              only names the part of the magazine that follows.

Rules:
- The running head is the strongest evidence. Consecutive pages under the same
  running head normally belong together; a change of running head is almost
  always a boundary. What the head does NOT settle is whether the run is one
  department, one column, or several separate articles -- see the next rules.
- A DEPARTMENT is one article, however many items it holds. A department is a
  run of consecutive pages under the same standing running head, where the
  magazine prints NO headline naming the department itself -- typically a news
  run or a reader-mail rubric. The department is one article whose title is the
  running head, and every item headline inside it is "continue", so it renders
  as a section heading. It ends where the running head changes.
  This is the ONE case where the running head becomes a title, because there is
  no other headline for the whole run. Decide it from the evidence below: if
  some paragraph or contents line DOES name the run, it is not a department.
- A COLUMN is likewise one article, but the magazine DOES print its headline.
  That printed headline is the article title, and the item headlines under it
  are "continue" -> section headings. Each item having its own byline does not
  make it an article. The column ends at the next column headline or at an
  unrelated article.
  A shared running head alone never merges anything: a head can cover many pages
  that are NOT part of any column, with full articles of their own sitting under
  it. Merge on the headline, not on the head.
- A column or department name is a STANDING name: it names no subject of its
  own and reads as the name of a section of the magazine. A headline that names
  a specific product, program, machine, person or event is an ARTICLE even when
  it shares a page with others. When in doubt about a headline that names a
  subject, make it an article.
- WORKED EXAMPLE, from a DIFFERENT issue (a 1986 monthly). Read it for the
  shape of the reasoning, not for its names -- none of these names is evidence
  about the issue you are reassembling:
    * "Aktuelles" ran pages 8-12 under that running head with no headline of its
      own anywhere -> ONE department, titled from the head, 22 news items as
      section headings.
    * "Tips & Tricks für Einsteiger" printed its own headline over eight tips,
      each with its own byline -> ONE column, titled from the printed headline,
      the eight tips as section headings. The bylines did not make them articles.
    * The running head "Tips & Tricks" ALSO covered pages 62-96, most of which
      carried full articles ("Module für Hypra-Basic", "HiRes Colossal"). The
      shared head merged none of them.
    * "Professionell und preiswert" (a Forth compiler test) and "Jetzt können
      sich die Computer-Freaks in Österreich freuen" name a subject, so they
      were articles even though they shared pages with other matter.
- If the headline text is repeated in the candidate because OCR read it twice
  ("Professionell und preiswert - Professionell und preiswert"), give it once.
- Many headlines are SET IN CAPITALS. Give those in normal German case, the way
  the contents page prints them: "DIE 1541 IM NEUEN KLEID" -> "Die 1541 im
  neuen Kleid". Leave a headline that is already mixed case exactly as it is.
- The table of contents below is THIS issue's own, transcribed from its printed
  contents page. It lists the major articles and their starting pages. Use it to
  fix titles and starting pages, and read it as the issue's own statement of
  which names are sections and which are articles. Do NOT assume it is complete:
  it omits short items. If it is empty, this issue's contents page did not
  survive OCR -- go by the running heads and the headlines alone.
- The title you return is what the READER sees, corrected for obvious OCR
  damage ("Comnuter" -> "Computer"). Do not invent, translate or expand it, and
  do not add the page number.
- Outside the DEPARTMENT case above, never use the running head as the title:
  it names the section, not the item. If the candidate paragraph IS the headline
  -- a short line, often set in capitals -- that headline is the title.
- Prefer "continue" when unsure. A missed boundary merges two articles; a false
  one cuts an article in half and strands its second half without a headline.

Return ONLY a JSON object, no prose, no code fence:
{{"boundaries": {{"<id>": {{"action": "start|continue|resume|drop", "title": "...",
                        "keep_heading": true}}, ...}}}}
"title" is required for "start" and omitted otherwise; "keep_heading" only on a
department's opening "start". Every id must appear.

TABLE OF CONTENTS:
{toc}

CANDIDATES:
{candidates}
"""

HYPHEN_PROMPT = """These words were broken across a line end in a German magazine printed in
1986. The break is marked with the character U+00AC (the "not" sign), which
stands for the hyphen the compositor printed at the line end. Resolve each one.

There are exactly three cases:
  soft hyphen  the break is only typographic: Zei¬chensatz -> Zeichensatz
  compound     the hyphen is part of the word: Sprite¬Block -> Sprite-Block
  suspended    the hyphen stands for an omitted second half, and a space
               follows it: Groß¬und -> "Groß- und"

Two traps specific to 1986 German, both of which occur in this issue:
- Pre-reform orthography splits "ck" as "k-k": Druk¬ker -> Drucker,
  Blök¬ken -> Blöcken. But Druck¬kopf is a genuine compound and stays
  Druckkopf. Judge by whether the joined word is a real word.
- Pre-reform orthography also splits "ß"/"ss" differently and writes daß,
  muß, außerdem. PRESERVE the 1986 spelling. Never modernise anything.

Any punctuation attached to the word is part of the word: keep it.
Do not correct spelling, do not fix other OCR errors, do not change case.
If a fragment is too damaged to resolve, join it without a hyphen.

Return ONLY a JSON object mapping each input word to its resolved form, no
prose, no code fence:
{{"Zei¬chensatz": "Zeichensatz", "Groß¬und": "Groß- und", ...}}

WORDS:
{words}
"""


# ---------------------------------------------------------------------------
# The paragraph stream
# ---------------------------------------------------------------------------

def page_stream():
    """Every page's paragraphs, in issue order, as one flat list.

    Returns (stream, pageinfo) where stream is a list of dicts
    {page, role, text} and pageinfo maps a page to its running heads and to the
    first-line indent of its first paragraph -- which is what decides whether
    that paragraph continues the one at the foot of the page before."""
    stream, pageinfo = [], {}
    for page in PAGES:
        f = os.path.join(OUT_DIR, f"{page:03d}.labels.json")
        if not os.path.exists(f):
            continue
        rec = json.load(open(f, encoding="utf-8"))
        paras = page_paragraphs(rec, f"{page:03d}")
        heads = [b["text"].strip().replace("\n", " ")
                 for b in rec["blocks"] if b["label"] == "header"]
        toc = [b["text"].strip() for b in rec["blocks"] if b["label"] == "toc"]
        pageinfo[page] = {"heads": heads, "toc": toc}
        # Each paragraph carries its OWN first-line indent, which is what says
        # whether it continues the paragraph before it or opens a new one.  Not
        # the page's first indent: after a continuation splice the paragraph
        # being joined is not the first one on its page, and reading the page's
        # instead welded the assembler course onto an unrelated notice on p140.
        for role, text, _starts, indent in join_runons(paras):
            if text.strip():
                stream.append({"page": page, "role": role,
                               "text": text.strip(), "indent": indent})
    return stream, pageinfo


def continuation_links():
    """Every "Fortsetzung auf Seite N", read off the page it is printed on.

    Taken from ALL of stage A's blocks rather than from the classified stream,
    because the marker is apparatus: step 020 has no reason to keep it in the
    corpus and different runs decide differently.  MEASURED -- one sweep labelled
    p127's "Fortsetzung auf Seite 169" a footer, it left the stream, and the
    second half of "Wie funktioniert ein Computer?" was stranded on p169 as an
    article of its own.  Whether a line is article text is a judgement; whether
    it is printed on the page is not, and only the second may decide where an
    article resumes."""
    out = {}
    for page in PAGES:
        path = os.path.join(OUT_DIR, f"{page:03d}.labels.json")
        if not os.path.exists(path):
            continue
        for b in json.load(open(path, encoding="utf-8"))["blocks"]:
            for direction, target in FORTSETZUNG.findall(b.get("text", "")):
                if direction.lower() == "auf":
                    out[page] = int(target)
    return out


def candidates(stream):
    """Indices into the stream that could be where an article begins -- or, on a
    page that resumes an interrupted article, where it stops doing so.

    Page 146 is the case that forces the last kind: it carries the second half
    of the p30 printer survey AND the end of the MPS 802 review that ran onto it
    from p145, with nothing between them but a change of subject.  Every
    paragraph after a continuation marker is therefore offered as a candidate."""
    out = []
    seen_page, in_cont = set(), None
    for i, p in enumerate(stream):
        kind = None
        if p["page"] not in seen_page:
            seen_page.add(p["page"])
            kind = "page-start"
            in_cont = None                     # a continuation never spans pages
        if in_cont is not None:
            kind = "after-cont"
        if p["role"] == "title":
            kind = "title"
        m = FORTSETZUNG.search(p["text"])
        if m:
            kind = "cont-marker"
            if m.group(1).lower() == "von":
                in_cont = p["page"]
        if kind:
            out.append((i, kind))
    return out


def toc_pages(pageinfo):
    """Which pages of THIS issue hold its printed contents.

    Front matter only, cover excluded, dense pages only, at most a spread's
    worth -- see the TOC_* constants for why each of those is needed.  Returns
    page numbers in reading order, or () when the contents did not survive OCR,
    which is reported rather than papered over: the boundary call is markedly
    worse without them and the operator should know which run this was."""
    scored = []
    for page, info in pageinfo.items():
        if not (TOC_SKIP_COVER < page <= TOC_FRONT_MATTER):
            continue
        n = sum(len(t) for t in info.get("toc", ()))
        if n >= TOC_MIN_CHARS:
            scored.append((n, page))
    scored.sort(reverse=True)
    return tuple(sorted(p for _, p in scored[:TOC_MAX_PAGES]))


def brief(stream, cands, pageinfo):
    """The one payload the model sees: every candidate with the evidence around
    it, plus the issue's table of contents."""
    pages = toc_pages(pageinfo)
    if pages:
        print(f"contents page(s): {', '.join(str(p) for p in pages)}", flush=True)
    else:
        print("WARNING: no contents page found in the front matter -- the "
              "boundary call runs on running heads and headlines alone",
              flush=True)
    toc = []
    for page in pages:
        toc += pageinfo.get(page, {}).get("toc", [])
    # what each page ended on, so a paragraph that resumes an article broken off
    # at the foot of the previous page can be recognised as one
    page_tail = {}
    for p in stream:
        page_tail[p["page"]] = p["text"]
    cont_pages = {stream[i]["page"] for i, k in cands if k == "cont-marker"}
    lines = []
    last_page = None
    for n, (i, kind) in enumerate(cands):
        p = stream[i]
        if p["page"] != last_page:
            last_page = p["page"]
            heads = " | ".join(dict.fromkeys(pageinfo[p["page"]]["heads"])) or "(none)"
            lines.append(f'\n--- page {p["page"]}  running head: {heads}')
            if p["page"] in cont_pages:
                prev_pages = [q for q in page_tail if q < p["page"]]
                if prev_pages:
                    lines.append(f'    page {max(prev_pages)} ended on: '
                                 f'"{page_tail[max(prev_pages)][-PREV_SNIPPET:]}"')
        prev = stream[i - 1]["text"][-PREV_SNIPPET:] if i else ""
        lines.append(f'[{n}] {kind:<11} role={p["role"]:<10} '
                     f'text="{p["text"][:SNIPPET]}"')
        if prev:
            lines.append(f'     ...preceded by: "{prev}"')
    return "\n".join(toc)[:6000], "\n".join(lines)


def ask_boundaries(stream, cands, pageinfo):
    """One LLM call for the whole issue.  Cached in articles.json's sidecar so a
    re-render costs nothing; delete the cache to re-ask."""
    toc, cand_text = brief(stream, cands, pageinfo)
    prompt = BOUNDARY_PROMPT.format(issue_id=ISS.id,
                                    kind_note=KIND_NOTES[ISS.kind],
                                    toc=toc, candidates=cand_text)
    # Keyed on the whole question, not just its length.  A cached verdict is
    # only valid for the exact stream AND the exact prompt it answered -- stage
    # B lost a whole sweep to a cache that survived a change it should not have.
    key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    cache = ARTICLES_JSON + ".boundaries"
    if os.path.exists(cache):
        old = json.load(open(cache, encoding="utf-8"))
        if old.get("key") == key:
            return {int(k): v for k, v in old["boundaries"].items()}
        print("boundary cache answers a different question, re-asking", flush=True)
    reply = llm.call(prompt, "")
    m = re.search(r"\{.*\}", reply, re.S)
    if not m:
        raise RuntimeError(f"no JSON in boundary reply: {reply[:300]}")
    got = json.loads(m.group(0))["boundaries"]
    json.dump({"key": key, "n": len(cands), "boundaries": got},
              open(cache, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {int(k): v for k, v in got.items()}


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------

def split_articles(stream, cands, verdict):
    """The stream, cut at every confirmed boundary, with dropped paragraphs
    removed.  Anything before the first boundary is not article text.

    A "Fortsetzung von Seite N" always cuts, whatever the model said about it,
    and the piece it opens is a CONTINUATION rather than an article: it has no
    headline of its own and belongs to something twenty pages back.  The
    cross-references themselves are apparatus and never survive -- the assembled
    article runs straight through the jump they describe."""
    action = {i: verdict.get(n, {}) for n, (i, _) in enumerate(cands)}
    segments, cur, before_cont = [], None, None
    for i, p in enumerate(stream):
        a = action.get(i, {})
        m = FORTSETZUNG.search(p["text"])
        if m and m.group(1).lower() == "von":
            before_cont = cur
            cur = {"kind": "cont", "title": None, "start": p["page"],
                   "resumes": int(m.group(2)), "at": p["page"], "paras": [], "pages": []}
            segments.append(cur)
            continue
        if m:                                   # "...auf Seite N": where it goes
            if cur is not None:
                cur["hands_to"] = int(m.group(2))
            continue
        if a.get("action") == "drop":
            continue
        # the continuation is over and the page goes back to what it interrupted
        if a.get("action") == "resume" and before_cont is not None:
            cur, before_cont = before_cont, None
        if a.get("action") == "start":
            cur = {"kind": "article", "title": (a.get("title") or p["text"]).strip(),
                   "start": p["page"], "paras": [], "pages": []}
            segments.append(cur)
            # The headline paragraph becomes the article title and is not
            # repeated in the body -- unless this is a department, whose title is
            # the running head ("Aktuelles"): there the paragraph is the first
            # item heading and has to stay.
            if p["role"] == "title" and not a.get("keep_heading"):
                cur["pages"].append(p["page"])
                continue
        if cur is None:
            continue
        cur["paras"].append(p)
        cur["pages"].append(p["page"])
    for s in segments:
        s["pages"] = sorted(set(s["pages"]))
    return segments


def merge_continuations(segments, hands_off=None):
    """Splice each continuation into the article that hands off to its page.

    The link is between PARAGRAPHS, not pages: p142 carries the end of the
    assembler course and then the start of "Kennen Sie Ihren Drucker?", and
    p169 carries the end of "Wie funktioniert ein Computer?" under a headline
    the page had reprinted.  Keying on the page an article STARTS on gets both
    wrong -- it swallowed the drucker article whole and stranded the computer
    one inside its neighbour.

    Confirmed in both directions: the article that says "auf Seite 169" must
    also cover the page that page 169 points back to.  All five jumps in this
    issue are symmetric, so a one-way match is evidence of a misread."""
    # An article hands off from whichever of its pages carries the marker, so
    # the link survives step 020 dropping that block from the corpus.
    hands_off = hands_off or {}
    resumes_on, out = {}, []
    for s in segments:
        if s.get("hands_to"):
            resumes_on[s["hands_to"]] = s
        for pg in s.get("pages", ()):
            if pg in hands_off and hands_off[pg] not in resumes_on:
                resumes_on[hands_off[pg]] = s
    for s in segments:
        if s["kind"] == "article":
            out.append(s)
            continue
        host = resumes_on.get(s["at"])
        if host is None or s["resumes"] not in host["pages"]:
            print(f'p{s["at"]}: continuation from p{s["resumes"]} has no article '
                  f'to rejoin, kept as its own', flush=True)
            s["kind"], s["title"] = "article", f'[Fortsetzung von Seite {s["resumes"]}]'
            out.append(s)
            continue
        host["paras"] += s["paras"]
        host["pages"] = sorted(set(host["pages"] + s["pages"]))
        # a continuation that hands on again keeps the chain pointing at the host
        if s.get("hands_to"):
            resumes_on[s["hands_to"]] = host
    return out


def join_across_pages(article):
    """A paragraph does not stop at a page break.  Same test as the column
    break inside a page -- the continuation is not indented, or the paragraph
    before it ends on a word that cannot end a sentence -- because it is the
    same physical fact: the compositor simply ran out of page."""
    out, last_page = [], None
    for p in article["paras"]:
        # tracked separately from out[-1], which keeps the page it started on
        # after a join: read off out[-1] instead, EVERY paragraph of the new
        # page looks like the first one and the whole page merges into a single
        # paragraph.  Measured on p146, whose second paragraph was swallowed.
        first_of_page = p["page"] != last_page
        last_page = p["page"]
        if (out and first_of_page and p["role"] == "body"
                and out[-1]["role"] == "body"
                and (p["indent"] < PARA_INDENT_MIN_PX
                     or ends_dangling(out[-1]["text"]))):
            out[-1] = dict(out[-1], text=join_text(out[-1]["text"], p["text"]))
            continue
        out.append(p)
    article["paras"] = out


def split_bylines(article):
    """(bs) at the end of the last paragraph is a byline, not a sentence.  Kept
    verbatim, but always as its own paragraph."""
    out = []
    for p in article["paras"]:
        m = BYLINE.search(p["text"]) if p["role"] == "body" else None
        if m and p["text"][:m.start()].strip():
            out.append(dict(p, text=p["text"][:m.start()].rstrip()))
            out.append(dict(p, role="byline", text=m.group(0).strip().rstrip(".")))
        else:
            out.append(p)
    article["paras"] = out


# ---------------------------------------------------------------------------
# Hyphens
# ---------------------------------------------------------------------------

def dehyphenate(articles):
    """Resolve every U+00AC marker via one LLM pass over the DISTINCT broken
    words.  Distinct rather than per occurrence because the answer is a property
    of the word: "Druk¬ker" is "Drucker" wherever it appears, and the issue's
    4287 marks are only 3459 different words."""
    words = set()
    for a in articles:
        for p in a["paras"]:
            words.update(re.findall(r"\S*¬\S*", p["text"]))
    cache = (json.load(open(HYPHEN_CACHE, encoding="utf-8"))
             if os.path.exists(HYPHEN_CACHE) else {})
    todo = sorted(w for w in words if w not in cache)
    for i in range(0, len(todo), HYPHEN_BATCH):
        batch = todo[i:i + HYPHEN_BATCH]
        reply = llm.call(HYPHEN_PROMPT.format(words="\n".join(batch)), "")
        m = re.search(r"\{.*\}", reply, re.S)
        if not m:
            print(f"hyphens {i}: no JSON in reply, batch skipped", flush=True)
            continue
        got = json.loads(m.group(0))
        # Only answers to words that were asked about; a hallucinated key would
        # otherwise poison the cache for every later run.
        cache.update({k: v for k, v in got.items() if k in set(batch)})
        json.dump(cache, open(HYPHEN_CACHE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"hyphens: {min(i + HYPHEN_BATCH, len(todo))}/{len(todo)}", flush=True)

    missing = [w for w in words if w not in cache]
    if missing:
        print(f"WARNING: {len(missing)} broken words unresolved, marker kept: "
              f"{missing[:5]}", flush=True)
    pat = re.compile(r"\S*¬\S*")
    for a in articles:
        for p in a["paras"]:
            p["text"] = pat.sub(lambda m: cache.get(m.group(0), m.group(0)), p["text"])
    return len(words) - len(missing)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def page_range(pages):
    """[12-14, 17].  A page carrying two articles appears in both ranges, which
    is lossy for that page and correct for both articles."""
    runs, start, prev = [], None, None
    for p in pages:
        if start is None:
            start = prev = p
        elif p == prev + 1:
            prev = p
        else:
            runs.append((start, prev))
            start = prev = p
    if start is not None:
        runs.append((start, prev))
    return "[" + ", ".join(f"{a}-{b}" if a != b else str(a) for a, b in runs) + "]"


def render_article(article):
    chunks = [f'# {article["title"]} {page_range(article["pages"])}']
    source = []

    def flush():
        if source:
            chunks.append(SOURCE_HTML % SOURCE_JOIN.join(source))
            source.clear()

    for p in article["paras"]:
        role, text = p["role"], p["text"].strip()
        if not text:
            continue
        if role == "source":
            source.append(text)
            continue
        flush()
        if role == "code":
            chunks.append("```\n" + text + "\n```")
        elif role == "byline":
            chunks.append(text)
        elif role == "title":
            # a headline the model did not make an article start: it is a
            # heading inside this one
            chunks.append("## " + text)
        else:
            chunks.append(ROLE_PREFIX.get(role, "") + text)
    flush()
    return "\n\n".join(chunks)


def main():
    stream, pageinfo = page_stream()
    cands = candidates(stream)
    print(f"{len(stream)} paragraphs, {len(cands)} candidate boundaries", flush=True)

    verdict = ask_boundaries(stream, cands, pageinfo)
    segments = split_articles(stream, cands, verdict)
    n_cont = sum(1 for s in segments if s["kind"] == "cont")
    print(f'{len(segments) - n_cont} articles, {n_cont} continuations to splice', flush=True)
    articles = merge_continuations(segments, continuation_links())

    for a in articles:
        join_across_pages(a)
        split_bylines(a)
    n = dehyphenate(articles)

    open(ISSUE_MD, "w", encoding="utf-8").write(
        "\n\n".join(render_article(a) for a in articles) + "\n")
    json.dump([{"title": a["title"], "pages": a["pages"],
                "range": page_range(a["pages"]),
                "paragraphs": len(a["paras"]),
                "chars": sum(len(p["text"]) for p in a["paras"])}
               for a in articles],
              open(ARTICLES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"{len(articles)} articles, {n} broken words resolved -> {ISSUE_MD}", flush=True)
    for a in articles:
        print(f'  {page_range(a["pages"]):<16} {a["title"][:60]}')


if __name__ == "__main__":
    sys.exit(main())
