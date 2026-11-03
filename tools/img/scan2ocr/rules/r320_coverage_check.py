#!/usr/bin/env python3
"""Reconcile the OCR blocks the CLASSIFIER KEPT against the published HTML.

Stage B (r020) decides which blocks on a page are article content and records
them in <page>.labels.json as "order".  Everything it kept must therefore end up
in the article that claims that page.  A kept block whose text appears nowhere
in that article is content dropped between the scan and the published page —
the failure mode that no spell-check or markup grep can see, because what
survives reads perfectly well.

Listing blocks are excluded: the disk .txt is the correct petcat rendering while
the OCR reading of the printed listing is garbled ('mps 891' for 'mps 801'), so
they never match and would drown the signal.

That exclusion leaves a hole, and it has been fallen into: a page that carries
NOTHING BUT one article's listing is claimed by no 64er.pages, so it never
enters the reconciliation at all and its absence reads as silence.  8610's
Listing 3 filled p156-157 and the article's meta said "152-153, 155"; coverage
reported 0.0% unaccounted while two whole pages were unclaimed.  So the second
half of this check walks the page NUMBERS, 1..pages, and reports every one no
article claims.  Ads are the legitimate population and they are most of it --
the check prints the list, a human reads it, and a page with a listing on it
cannot hide in the middle of it.
"""
import glob, html, io, json, os, re, sys

import r000_issue
from r000_issue import ISSUE

# The ONE per-issue knob, imported from r000_issue as everywhere in scan2ocr.
# Both sides of the reconciliation come from it, which is the point: comparing
# one issue's OCR against another issue's HTML reports a coverage figure that
# means nothing, and it cannot happen while there is a single name to get wrong.
ISS = r000_issue.load(ISSUE)

ISSUE_DIR = sys.argv[1] if len(sys.argv) > 1 else ISS.issue_dir
OCR       = sys.argv[2] if len(sys.argv) > 2 else ISS.out_dir
SHINGLE, MIN_WORDS, THRESH = 4, 12, 0.25

# THE NOISE SWEEP EMITS CANDIDATES; IT MUST EMIT FINDINGS.
# MEASURED on 8701: p33's three pin tables were lost -- printed inside the
# yellow panels, labelled `noise` by step 020, and carried by neither the crop
# nor the HTML.  This sweep PRINTED one of them, in the middle of 138 lines,
# and it was not read.  Three faults, and the third is the one that matters:
#   (a) no exit status and no count in the verdict, so it read as informational;
#   (b) 138 lines of OCR debris off photos and ads, with the one that mattered
#       19th and nothing ranking it;
#   (c) IT NEVER ASKED THE QUESTION THE OTHER HALF OF THIS SCRIPT ASKS --
#       is this text anywhere in the HTML?  Without that test every line needs
#       a human judgement the script could have made itself, and the default
#       reading ("figure text, carried by the crop") was never contradicted.
# The other two tables were never printed at all: MIN_WORDS = 12 and they come
# to 4 and 10 words.  A pin table, a legend and a parts list are SHORT BY
# NATURE, so that floor excluded exactly the population this failure lives in.
#
# So a noise block is now scored, not listed:
#   real  = share of its tokens that are words seen in the published corpus
#           -- kills "ss i n a en be ch 4 x ig 02 au o rn w 8";
#   found = share of its 3-word shingles present in THIS issue's HTML
#           -- kills text we did publish;
#   score = real * (1 - found), printed in score order.
# MEASURED: 234 blocks -> 32, with p33 FIRST; at a floor of 6, 383 -> 56 and
# two of the three p33 tables are in.
NOISE_MIN_WORDS = 6        # a table is short by nature; 12 hid two of three
NOISE_REAL_MIN = 0.5       # below this it is OCR debris, not language
NOISE_FOUND_MAX = 0.5      # at or above this we published it

# A SHINGLE CANNOT READ A TABLE, AND A TABLE IS WHAT THIS CHECK WAS FIXED FOR.
# MEASURED on 8701, immediately after the rewrite above: p33's three pin tables
# were typeset -- as `<table>`, which is what the print shows -- and the sweep
# still called all three NOT FOUND.  Every word was in the HTML.  The reason is
# the shape: a cell stream normalises to "1 luminanz 2 masse 3 audio out", and
# the OCR block's 3-word shingle "luminanz masse audio" occurs nowhere in it,
# because the row numbers sit between the words.  Five more blocks (p35, p48,
# p61, p162, p170) failed the same way, all of them tables.
#
# So the check that was written to catch the p33 loss could not see the p33
# FIX.  A gate whose matcher assumes prose order reports every table as lost,
# which is the loudest possible false positive in the one population this sweep
# exists for -- short, number-interleaved text.
#
# The second test asks the question without the ordering assumption: is every
# distinctive word of this block ALREADY ON THE PAGE?  It is all-or-nothing at
# 0.9, because for a table, a legend or a parts list that is the right question
# and the only one a shingle can't ask.
#
# BUT A VOCABULARY MATCH IS NOT A PHRASE MATCH, AND IT DOES NOT GET TO SILENCE
# A BLOCK.  TESTED while writing this: a paragraph that is genuinely gone, whose
# words happen to scatter through its own article in another order, scores 0.92
# on the set test.  If `found` simply absorbed that, the fix would have bought
# six table false positives at the price of a new way to lose a paragraph
# silently -- which is the failure this whole sweep exists to prevent.
#
# So there are THREE outcomes, not two, and the weak one is NAMED:
#   found by shingle  -> silent; we published this text.
#   vocabulary only   -> its own short list, to be eyeballed. A typeset table
#                        lands here and is correct; a reordered lost paragraph
#                        lands here too and is not, and the list is small
#                        enough that the difference is visible at a glance.
#   neither           -> the ranked list that needs a disposition each.
# A gate may downgrade evidence. It may not make the block disappear.
NOISE_SET_MIN = 0.9        # all-or-nothing: a set match is weak, so demand all


def corpus_vocab(issues_dir):
    """Every word of 4+ letters in the published corpus, as the 'is this
    language' test.  Built from the HTML we ship, so it needs no word list and
    cannot drift from the German the magazine actually prints."""
    voc = set()
    for f in glob.glob(os.path.join(issues_dir, '*', '*.html')):
        try:
            t = io.open(f, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        for tok in norm(re.sub(r'<[^>]+>', ' ', t)):
            if len(tok) >= 4:
                voc.add(tok)
    return voc

norm = lambda t: re.sub(r'[^a-z0-9]+', ' ', t.lower()).split()

page2art, arttext = {}, {}
for f in sorted(glob.glob(ISSUE_DIR + '/*.html')):
    s = io.open(f, encoding='utf-8').read()
    m = re.search(r'64er\.pages" content="([^"]*)"', s)
    if not m: continue
    i = s.find('<article')
    # UNESCAPE AFTER STRIPPING TAGS, never before: &lt;F3&gt; unescaped first
    # becomes <F3> and is then removed as a tag. Without this the entity text
    # normalises to 'lt f3 gt' and never matches the OCR's 'f3', which both
    # invents false positives and hides a real one whose text turns on < > &.
    arttext[f] = ' '.join(norm(html.unescape(
        re.sub(r'<[^>]+>', ' ', s[i:s.rfind('</article>')] if i >= 0 else s))))
    # A LETTERED page ('169a', '193b') is r080's convention for two articles
    # sharing a start page. `part.isdigit()` is False for it, so both articles
    # claimed NO pages and p169's blocks fell to whichever article's range
    # covered 169 -- four spurious UNACCOUNTED findings on 8612. Strip the
    # suffix: the letter orders the two articles, it is not part of the page.
    def _pg(tok):
        mm = re.match(r'^(\d+)[a-z]?$', tok.strip())
        return int(mm.group(1)) if mm else None
    for part in m.group(1).split(','):
        part = part.strip()
        if '-' in part:
            lo, hi = (_pg(x) for x in part.split('-', 1))
            rng = range(lo, hi + 1) if lo is not None and hi is not None else []
        else:
            one = _pg(part)
            rng = [one] if one is not None else []
        for p in rng: page2art.setdefault(p, []).append(f)

listings = ' '.join(' '.join(norm(io.open(f, encoding='utf-8', errors='replace').read()))
                    for f in glob.glob(ISSUE_DIR + '/prg/*.txt'))

missing, kept_total, pages_read = [], 0, 0
listing_low, unordered, other_unordered = [], [], {}
for p, arts in sorted(page2art.items()):
    try:
        lab = json.load(open(f'{OCR}/{p:03d}.labels.json'))
    except FileNotFoundError:
        continue
    pages_read += 1
    keep = {str(i) for i in lab.get('order', [])}
    if not keep: continue
    hay = ' '.join(arttext[a] for a in arts) + ' ' + listings
    for b in lab.get('blocks', []):
        w = norm(b.get('text', ''))
        lbl = str(b.get('label', ''))
        # THE TWO POPULATIONS THIS USED TO DROP, AND WHY THEY ARE BACK.
        # r320's rule says hand-typed listings are checked like prose and that
        # noise/other blocks are swept for lost prose. This script checked
        # neither: a `listing-*` label was skipped outright, and a block the
        # model left out of `order` was never looked at -- which is exactly
        # where a dropped paragraph goes. So `exit 0` covered less than the
        # rule claimed, and on 8701 both sweeps were done BY HAND afterwards.
        #
        # They are reported SEPARATELY and do not set the exit status, because
        # both are noisy for reasons that are not defects: listing OCR garbles
        # ('mps 891' for 'mps 801', see the head of this file) so a low match
        # is expected, and a noise block is usually page furniture. The point
        # is that a human now SEES them without writing a script first.
        if str(b.get('id')) not in keep:
            # SCOPE IT TO WHAT THE RULE ASKS FOR.  Everything outside `order`
            # is 293 blocks on 8701, and a 293-line dump is read by nobody --
            # the same failure as not sweeping at all.  The rule's population
            # is NOISE and OTHER, where a dropped paragraph goes: 138 here,
            # and fewer once the word floor bites.  The rest (ad, caption,
            # listing-standalone, toc) are their own rules' business and are
            # summarised by label so their absence is visible without
            # burying the list that has to be read.
            if lbl in ('noise', 'other', ''):
                if len(w) >= NOISE_MIN_WORDS:
                    unordered.append((p, lbl or 'unordered', w, hay))
            elif len(w) >= MIN_WORDS:
                other_unordered[lbl] = other_unordered.get(lbl, 0) + 1
            continue
        if lbl.startswith('listing'):
            if len(w) >= MIN_WORDS:
                probes = [' '.join(w[i:i+SHINGLE])
                          for i in range(0, max(1, len(w) - SHINGLE), max(1, len(w)//12))]
                hit = sum(1 for pr in probes if pr in hay)
                if probes and hit / len(probes) < THRESH:
                    listing_low.append((p, lbl, round(hit/len(probes), 2), len(w),
                                        ' '.join(w[:16])))
            continue
        if len(w) < MIN_WORDS: continue
        kept_total += 1
        probes = [' '.join(w[i:i+SHINGLE]) for i in range(0, len(w) - SHINGLE, max(1, len(w)//12))]
        hit = sum(1 for pr in probes if pr in hay)
        if probes and hit / len(probes) < THRESH:
            missing.append((p, b.get('label'), round(hit/len(probes), 2), len(w),
                            ' '.join(w[:16]), [a.split('/')[-1][:30] for a in arts]))

# The noise sweep is SCORED HERE, before anything is printed, so its count
# can go in the verdict line -- see the comment there.
VOC = corpus_vocab(os.path.dirname(os.path.abspath(ISSUE_DIR.rstrip('/'))))
scored, vocab_only = [], []
for p_, lab, w, hay in unordered:
    # THE DENOMINATOR IS EVERY TOKEN, NOT JUST THE LONG ONES.  Scored over the
    # long tokens alone, "m 0208 os 0 j oon go" has ONE qualifying token, it is
    # in the corpus, and the block scores real=1.00 -- debris reading as perfect
    # German.  OCR debris is mostly one- and two-character fragments, so making
    # them count against the score is what separates it from language.
    real = sum(1 for t in w if len(t) >= 4 and t in VOC) / len(w) if w else 0.0
    sh = [' '.join(w[i:i+3]) for i in range(max(1, len(w) - 2))]
    found = sum(1 for x in sh if x in hay) / len(sh) if sh else 0.0
    # The set test, for the table-shaped text the shingle test cannot read --
    # see NOISE_SET_MIN above.
    toks = [t for t in w if len(t) >= 4]
    hayset = set(hay.split())
    sset = sum(1 for t in toks if t in hayset) / len(toks) if toks else 0.0
    if real < NOISE_REAL_MIN:
        continue                       # OCR debris, not language
    if found >= NOISE_FOUND_MAX:
        continue                       # published, as a phrase
    if sset >= NOISE_SET_MIN:
        vocab_only.append((p_, lab, len(w), real, round(sset, 2),
                           ' '.join(w[:16])))
        continue
    scored.append((real * (1 - found), p_, lab, len(w), real, found, sset,
                   ' '.join(w[:16])))
scored.sort(reverse=True)

# A SWEPT <tmp> LOOKS EXACTLY LIKE A CLEAN ISSUE: every page raises
# FileNotFoundError, kept_total stays 0, and the old summary printed
# "UNACCOUNTED 0 (0.0%)" -- a pass, from a check that never ran. Say so and exit
# non-zero instead; the unclaimed-pages half below needs no OCR and still runs.
if pages_read == 0:
    print(f'CANNOT RUN: no <page>.labels.json under {OCR}')
    print('  The OCR intermediates are gone (swept <tmp>?). This half of the')
    print('  check reconciles kept blocks against the HTML and needs them.')
    print('  Rebuild them, or run this on an issue whose <tmp> still exists.\n')
else:
    # THE VERDICT LINE IS THE ONE LINE THAT GETS READ.  On 8701 the operator
    # carried "UNACCOUNTED 54" into the LOG, dispositioned those 54, and
    # recorded the gate as done -- the noise section further down never
    # entered the verdict, so it read as informational and went unread with a
    # lost pin table in it.  A finding that is not in the headline is not a
    # finding.  The noise count is appended once it is known, below.
    verdict = (f'pages {len(page2art)}   kept prose blocks {kept_total}   '
               f'UNACCOUNTED {len(missing)}'
               f'   ({100*len(missing)/max(1,kept_total):.1f}%)')
# --- the two populations the rule asks for, reported, not asserted ----------
if pages_read:
    # Both counts, because the verdict line is the one line that gets read --
    # and a vocabulary-only match is the quietest place a paragraph can hide.
    print(verdict + f'   NOISE NEEDING A DISPOSITION {len(scored)}'
                    f'   FOUND BY VOCABULARY ONLY {len(vocab_only)}\n')
    for p_, lab, frac, n, txt, arts in missing:
        print(f'p{p_:<4} {lab:<9} match={frac:<5} words={n:<4} {arts}')
        print(f'      "{txt}…"')
print(f'\nLISTING BLOCKS below the threshold {len(listing_low)} — OCR of a listing'
      f' garbles, so a low match here is usually the OCR, not a loss. Read them.')
for p_, lab, frac, n, txt in listing_low:
    print(f'  p{p_:<4} {lab:<18} match={frac:<5} words={n:<4} "{txt}…"')

print(f'\nNOISE/OTHER BLOCKS OF REAL WORDS NOT FOUND IN THE HTML: {len(scored)}'
      f' of {len(unordered)} — EACH NEEDS A DISPOSITION, highest score first.')
print(f'  (score = real x (1 - found); real = share of words in the published'
      f' corpus, found = share of 3-word shingles already in this issue,'
      f' set = share of its words on the page in any order)')
for sc, p_, lab, n, real, found, sset, txt in scored:
    print(f'  p{p_:<4} {lab:<9} score={sc:.2f} real={real:.2f} found={found:.2f}'
          f' set={sset:.2f} words={n:<4} "{txt}…"')
if vocab_only:
    print(f'\nFOUND BY VOCABULARY ONLY: {len(vocab_only)} — every word is on the'
          f' page but no phrase of three matches. EYEBALL EACH.')
    print(f'  A typeset table reads this way and is correct (the row numbers sit'
          f' between the words). A lost paragraph whose words happen to scatter'
          f' through its own article reads this way too and is NOT.')
    for p_, lab, n, real, sset, txt in vocab_only:
        print(f'  p{p_:<4} {lab:<9} set={sset:.2f} real={real:.2f}'
              f' words={n:<4} "{txt}…"')
if unordered and not scored and not vocab_only:
    print('  none — every out-of-order noise block is OCR debris or already published')
if other_unordered:
    print('  (also outside the order, each its own rule\'s business: '
          + ', '.join(f'{k} {v}' for k, v in sorted(other_unordered.items())) + ')')

# --- pages no article claims ------------------------------------------------
# Needs only the HTML and the descriptor, so it still runs when <tmp> has been
# swept away and the OCR output is gone -- which is when it is most useful.
unclaimed = [p for p in range(1, ISS.pages + 1) if p not in page2art]
print(f'\nUNCLAIMED PAGES {len(unclaimed)} of {ISS.pages} — ads are the legitimate '
      f'population; a listing or a figure here means some 64er.pages is short')
for p in unclaimed:
    what = ''
    try:
        lab = json.load(open(f'{OCR}/{p:03d}.labels.json'))
        keep = {str(i) for i in lab.get('order', [])}
        labels = sorted({str(b.get('label', '?')) for b in lab.get('blocks', [])
                         if str(b.get('id')) in keep})
        what = '  kept: ' + ', '.join(labels) if labels else '  kept: nothing'
    except FileNotFoundError:
        pass
    print(f'  p{p:<4}{what}')

# EXIT STATUS -- the comment above has said "exit non-zero" since it was
# written, and nothing ever did. This script exited 0 with UNACCOUNTED hits,
# exited 0 with a planted deletion, and exited 0 on CANNOT RUN, so every
# exit-code consumer read all three as a pass.
#
# UNCLAIMED PAGES is informational: ads are the legitimate population there,
# so it does not affect the status. So are the two sweeps above -- they are
# read, not asserted (see their comment in the loop). What changed is that
# `exit 0` no longer claims a coverage the script never attempted.
if pages_read == 0:
    sys.exit(2)      # could not run -- not a pass
if missing:
    sys.exit(1)      # real findings
