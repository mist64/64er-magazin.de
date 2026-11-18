# WORKFLOW_ERRATA — 8702

## 005 — r005_masters_spread still budgets 2.25 GB a page, after r000's 2026-11-02 erratum (LIVE)

**What the rule says.** r005_masters_spread.md, *The profile is MEASURED*: "**Before any of it,
preflight the free space** — 005 writes ~2.25 GB a page at 2400 dpi". r000 *PREFLIGHT the free
space* carries an ERRATUM (2026-11-02) replacing that with ~0.9 GB/page (8701 172 GB / 192 pp).

**What I did.** Budgeted from r000 (184 x 0.9 = ~166 GB); the gate pages measure the real number.

**Cost.** None this time -- r000 was read first. Read in the other order, it is 414 GB and the same
false "fits nowhere" 8701 nearly acted on.

**Suggested.** Replace the r005_spread sentence with a pointer to r000's measured figure.

## 005 — `cut` cannot run on a geometry set with no hole fold (LIVE)

**What the rule says.** r005_masters_spread *Run `cut` after the sample `measure`, before the gate*:
"a `measure` alone leaves `masters600` empty ... Without this the gate reports a missing file".
`cut` "stops only when there is no geometry at all, or when a parity has no page with a wordmark".

**What happened.** Gate pages 044/104/155 measured with the built-in clip: fold colour / none / none.
`cut` then died in `punch_priors()` (line 1222) on `np.percentile(dist, 5)` over an empty list --
IndexError, exit 1, no masters600. A third, unlisted stop condition: zero hole folds in the set.

**Why it matters.** The gate (blank p1, glyph p50, the crop) reads masters600, and the built-in clip
finding no hole fold is exactly what a new issue's first pages do (8701 too). So the gate ordering the
rule prescribes cannot be followed until the clip is re-measured -- which needs a 20+ page sample first.

**Cost.** 1 run, ~1 min to read. Workaround: clip sample first, then `cut`.

**Suggested.** Guard `punch_priors` for zero hole folds (fall back as for "no fold"), and say in the rule
that on a new issue the clip sample precedes the gate's `cut`.

**Moved under the build.** Control fixed `punch_priors` in 813d7588: it now stops naming the condition
(no hole fold in the set; derive the clip first), with a second guard for hole folds but no template
shift. Control adds: `np.median([])` would have returned nan silently -- the percentile crash was the
lucky outcome.

## 005 — the clip re-measure's Step 0 assumes inliers; with the offset 11 mm off there are none (LIVE)

**What the rule says.** r005_masters_spread *The fold*, re-measure Step 0: "Print each page's
inlier y's *relative to hole 1* beside `HOLE_TEMPLATE_MM`"; Step 1: "associate the six per page
nearest a rough template".

**What happened.** Under the built-in clip 24 of 25 sample pages had NO fold, so there were no inliers
to print, and the rule gives no rough template to associate against when the offset is unknown.
8702's hole 1 sits at ~48 mm against the prior 59.0 +- 3 -- outside the window, so `template_score`
admits no shift at all.

**What I did.** Clustered each page's stored candidates by x (0.8 mm window, 5-15.5 mm in), read the
y's of the dominant cluster on the best pages (011, 012, 027, 170) to get a rough template and offset
(~47.6 + 0/13.2/86.3/99.7/167/180), then associated per page within 1.5 mm with an x-spread limit.
8 clean six-hole pages gave the template. ~10 min, 3 commands.

**Suggested.** Step 0 for the "fold none everywhere" case: cluster `holes` by x from the inner edge,
read the y's of the densest cluster on a few clean pages, and use THAT as the rough template; and say
that the offset can move by ~11 mm between copies (8701 60.8, 8702 48.1, 8610 59.0).

## 005 — EDGE_OUTER_MAX_MM 8 overrules correct odd-page traces on 8702's asymmetric frames (LIVE)

**What the rule says.** r005_masters_spread *The three outer edges*: "the outer trim 0–5.7 mm in (the
frame's slack over A4 beyond the fold is at most 8 mm)" -> `EDGE_OUTER_MAX_MM` 8; a trace deeper than
that "is ink: that edge alone takes the full-bleed line (the frame ... column)". "The safe direction:
a page narrower than A4 whose trim really is 9 mm in would show bed in its outer margin, and never
lose ink."

**What happened.** 8702's operator split each A3 at H/2-360, so every odd frame is 227.2 mm wide and
every even one 219.6. Odd outer trims sit 4.5-12.7 mm in. On 4 of 12 odd sample pages (067 081 091
121) the true paper edge at 9.0-12.7 mm was overruled and the masters carry 0.3-2.3 mm of scanner bed
at the outer edge. The "safe direction" is exactly what happened -- bed in the master is the foreign
matter the window rule says must never show.

**Cost.** Caught on the sample, before the sweep: ~15 min, 6 commands, two crops.

**Suggested.** Measure the outer slack per issue and parity (the frame width is in phys.txt before
005 runs), or test the overruled band for BED colour (neutral, lum < 70) before giving the edge to
the frame: a band of paper-white ending in neutral black is a trim, not ink.

## r005 spread: `half_of` splits on the number of geometry files, not the issue's pages
`half_of(geom, len(geoms))` uses `len(geoms) // 2`. On the 25-page sample it was 12, so p040/044/090 took the
back-half offset (+1.43 mm in the sample) instead of the front-half one; the full cut moved their windows by
50 px (2.12 mm). Harmless after a full sweep, wrong on every sample/gate cut. Should use the issue's page count.

## r005 spread: p137 levelled to the art; the certified fold on the same sheet says so, and nothing reads it
p137 (Star NG-10 ad, banners printed at an angle): thumb skew then second pass applied -1.12 deg, residual -1.60
"published anyway". The same levelled sheet carries a certified hole fold (8 holes, template 5, rms 0.04 mm) with
tilt -1.26 deg: holes x 303 @ y1079 -> 195 @ y5374. The bottom trim slope is +0.56 deg in the same sense.
So the sheet is ~1.26 deg off in the master, i.e. the sheet's own angle was about +0.14 deg, and the second
pass made it worse (-0.76 -> -1.60). Visible: master top-left carries ~30 px of neighbour, bottom-right ~60 px
of dark beyond the trim. Check 3b flags it (|angle| > 1.0) but the rule has no remedy; the fold's tilt is the
one measurement on the page not taken from the art. Suggest: when the fold is certified, its tilt overrules the
projection skew (or at least refuses a second pass that moves away from it).

## r010 rot180 (dc196055): rotated-pass block ids collide with the upright ids; nothing checks id uniqueness
8702 p039: 58 blocks, 47 distinct ids. 020's order, given by id, resolved to the wrong blocks, so the previous
article's box was dropped and the tips came out misordered. 020's cache key compares id SETS, which hide duplicates.
Also: 020 renders consecutive one-sentence body blocks as one paragraph (p039 tips, p153).

## r070: the dash check assumes the issue sets en dashes
8702 (and 8701: 90 em / 0 en) sets a spaced EM dash. All 5 of the script's spaced-hyphen → en-dash conversions
were wrong (3 were em-dash item markers OCR'd as "-", 1 a BASIC »LIST a - b«, 1 OCR garbage), and the
Verification's "zero en dashes is a failure" reads 0 on a correct run. Count en + em, or leftover spaced hyphens.
The flank test does not flag item-marker dashes; the script still self-stages with `git add`.

## r080 split.sh byline collection
is_byline() accepted "(dieses Programm ist nur bei der geringeren Auflösung verfügbar)" and Q&A askers' names as
authors; the author meta is a set of byline STRINGS, so tokens repeat ("Udo Dreier, hm, hm"); an unbracketed
signature ("Michael Scharfenberger, Chefredakteur") is never collected. And nothing flags an article whose last
paragraph ends in "-": Kurvendiskussionen lost its last line into the listing block below it (8702 p067).
030's "continuation … has no article to rejoin" fired falsely on both two-sided seams (p29→41, p35→179).

## r120 extractor / checks (8702)
prg_links.sh's stub test (<3 content lines) let kudi 64 (3 BASIC lines + 7.6 KB machine code) through as BASIC and
wrongly catches a real 2-line loader (pixler); check 4's "trailing bytes" branch has no upper bound, so that stub
passed green ("7630 trailing bytes"); check 5 demands a load-address extent for SEQ files, which have none;
prg_links.sh calls hypra-ass-decode.py with bare python3; machine-tagged separators (c128-NN, c16-NN) are not
turned into ;version tags (3 mismatches here, fixed by hand).

## r120 checks after r130 / r130 check 5
r120_binary_extent.py reads prg.txt, so after 130 empties it it reports "0 raw binaries … OK" (passes on nothing);
r120_sections.py (3b) always FAILs "POST-130 file" with an explained orphan left (lies mich!), so "130 turns it
green" cannot happen; r130 check 5's `generate.py … local` starts a blocking server and never returns.
r130 has no variant for reclassifying a file 120 mis-typed (pixler: a printed Checksummer loader sent to PRG).

## r140 check 4 loops over the Sonderheft slug list on every issue
The `if` sets SLUGS per series but the loop is literally `for slug in impressum checksummer vorwort mse`, so a
monthly never checks leserforum/editorial/fehlerteufelchen/vorschau and reports checksummer missing whenever the
previous monthly had one; the block also needs bash (zsh here). The evidence line demands PREV as the precedent
where the right precedent is often older (8407, 8508, 8608, SH8606).

## r180: no check catches a dropped or glued byline (13 on 8702); the Impressum one-liner is stale
Bylines OCR lost or mangled (" Gk)", "ftr)", "(09)", a byline inside <code>, (ik) for (jk)) are invisible to every
r180 check; comparing the OCR's bylines per page with each article's <address> list found all 13 (cmp.py in the 180
sub-agent's scratch). The Verification's Impressum line greps only "xx = Name" (aa, gk UNDEFINED) and keeps only the
last slash token ($NF), so the "(fl/kn)" fl is never tested. tools/checksummer.parse raises KeyError '70' on a
;version=70 file (generate.py passes "70"; the table has "7").

## r200 Verification and anatomy
Check 2 hard-codes <START>/<YYMM> (never matches a real banner, never checks the file exists); check 3 compares the
author meta with ALL p.author, which includes the askers (false FAIL on 8702/26's unsigned Q30); check 3 demands head1
which r210 writes later; the anatomy says editor answers are unsigned, while 8702 prints (jk)/(og) and then reader
answers in the same section — no shape for that; a non-Q&A column inside the Leserforum (Clubs) is not covered.

---
# Entries below were reported to control by message as they happened and logged in LOG.md; they are copied
# here at sign-off (2026-11-17) so the harvest holds them in one place. Classification per r340: SAME SESSION
# (first-hand, written up the same working day, hours after the step). "FIXED <sha>" = control already changed
# the rule during this build; the entry is kept so the harvest can audit it.

## 050 — planted test writes /tmp; placeholder snippet needs ID/PY; summary label "bogus </" counts three opener kinds (SAME SESSION)
**Suggested.** Write the planted file under the scratch dir; set ID/PY in the snippet; label "bogus openers (<!, <?, </x)".

## 060 — survey grep is not fence-aware; underscore runs become <strong><em> because 040 escapes only `*` (SAME SESSION)
**Suggested.** Exclude ``` fences from the start-number survey; have 040 (or 060's post-pass) escape runs of `_` outside fences.

## 090/100 — r100 .sh stages unconditionally; r090 glyph clause shows – where monthlies set —; all-regular-weight TOC entries undefined; kicker colon join doubles colons; r100 sweep blind to a misprint landing on another article's page (SAME SESSION)
**Suggested.** A NO_GIT switch in r100_toc_category.sh; name the em dash for monthlies; a line-end-punctuation test for regular-weight entries; join a kicker that ends in ":" with a space only.

## 110 — no fallback for a closed previous issue's missing masters; the ~28-day sanity gap misfires at the year end (SAME SESSION)
**Suggested.** "If the previous issue's masters are gone, read its published PDF's Vorschau page"; allow 35 days across December/January.

## 130 — no variant for reclassifying a file 120 mis-typed (pixler) (SAME SESSION; check 5's `generate.py local` hang FIXED 6fb3a8d3)
**Suggested.** A variant row: "a printed Checksummer BASIC loader that 120 sent to PRG becomes prg/<name>.txt via petcat; the .prg goes to del/".

## 150 — two-page form naming; second Bild series in one article (SAME SESSION; FIXED 4017f4e1); spread stamps lacked sheet-box (FIXED in r005)

## 160 — no wording for a table ruled only under its header; two-half lists; tr.separator only on table.plain (SAME SESSION)
**Suggested.** "A single rule under the header row = table.plain + tr.separator"; "a list printed in two side-by-side halves is set as one column".

## 170 — Verification counts neither rows nor sums; check 3 skipped a missing prg file; 300 dpi note; splice recipe (SAME SESSION; FIXED bb4d5ec4 and the 170 batch)

## 190 — Impressum "<strong> 0 of 32" vs the corpus's <em>; "never retype code from print" vs re-reading OCR'd snippets; adjudication location; Q&A sweep blind to glued Q/A; ascending-number sweep fires on prose units; npx refused (SAME SESSION; partly FIXED: adjudication location ruled "both")
**Suggested.** "Follow the corpus's <em> labels"; a section owning OCR'd <pre><code> snippets (the shape is in LOG.md "## 190"); the Q&A sweep counts "?" inside a paragraph followed by bold; exclude unit words (KByte, MHz) from the line-number sweep.

## 200 — check 2 hard-codes <START>/<YYMM>; check 3 counts askers as authors; head1 required before r210; no shape for an editor-signed answer followed by reader answers; clubs column uncovered (SAME SESSION)
**Suggested.** Take the file and issue from $1/$ISSUE; count address.author + p.author inside div.a; move the head1 check to r210; an anatomy line for "editor answer, address, reader answers".

## 210 — apply script skips lettered pages silently; check 1 double-counts the Leserforum and cannot see no-band articles; /tmp/head2; shared start page with no own page (SAME SESSION)
**Suggested.** expand_pages accepts "8b-9", "174a"; the arithmetic subtracts the Leserforum once; write head2 under the scratch dir; "a starting article with no page of its own takes the band over its start".

## 220 — check 1 counts blank-category rows; check 3 contradicts the owner's index_title ruling; routing check blind to &lt;/&gt; and toc_title; CSV ">>…<<" disk typography and some categories (SAME SESSION)
**Suggested.** Count only rows with a category; drop check 3 or align it with the 2026-11-03 ruling; unescape all entities; a CSV sweep for ">>"/"<<".

## 230/240 — placeholders not read from $ISSUE; r240 has the agent cut the banner itself (no "pending crop" state); Bücher size range too tight (SAME SESSION)
**Suggested.** A "pending on the owner's worklist" state that prints LOOK, not FAIL; Bücher height 202–208.

## 250 — "only toggles the class" vs reading source text off the page; no table-source-note shape; check 1 omits Quelle; no exclusion for the magazine's own send-to address (SAME SESSION)
**Suggested.** "Read every source line's text off the page (phones and postcodes are where OCR errs)"; add Quelle to the label regex; exclude "Schicken Sie … an:" addresses.

## 260/270 — r260 Notes say 270 before 260; check 1 scans Leserforum h2s the guardrail forbids changing; check 2 flags OCR-damaged mixed-case headings; substring match; SS→ß (SAME SESSION)
**Suggested.** Run order 260→270 in the Notes; check 1 skips article.qa; a line "a lowercase-first heading is r280's to fix from the page"; word-boundary match; "caps SS → ß where the word has ß".

## 280 — evidence asks for block-index proof the rule calls impossible; Pass 1 substring matches; no word-box locator; guillemet sweep misses one-sided glue; word_jams only >= 9 letters; no line on mid-line scan specks (SAME SESSION)
**Suggested.** Evidence = crop + locator; `\w»|«\w` sweep; a function-word segmentation detector beside word_jams (it found ~3x as many on 8702).

## 290 — a sentence spliced mid-way in the adjudication paragraph; second article's h1-size banner in one file; check 2 tests only an aside's first heading; check 1 silent on success (SAME SESSION)
**Suggested.** "A second article in one file takes h2 for its banner"; check 1 prints "N files, one h1 each".

## 300 — outbound licence buried; status vocabulary vs step 2's non-code omission; status_pairs matches records by issue, not per program; "OCR PDFs gone" was false (SAME SESSION; FIXED 50b15b37, a652c934, ccca0719 and the Druckfehler test)
**Suggested.** status_pairs pairs each article's trailer with a record naming a program that article places.

## 320 — no file for dispositions; dropped_listings examined nothing; no caption-vs-figcaption check (SAME SESSION; first two FIXED a98df6cb; the third recorded as a named gap)

## 325 — readers can reverse an earlier "kept as printed" (2 of 168 here, one right, one wrong) (SAME SESSION; FIXED: the cross-check is now r325's)

## 330 — record-backed pairs skip the ambiguity checks; no evidence column in a --record file; real differences inside MOVED blocks show as EDITORIAL; whole-article numbering floods single-item PARTIALs; standing-reprint exclusion keyed on 64er.id misses an embedded box; r330 Step 0 vs r140 on who writes reprints.txt (SAME SESSION)
**Suggested.** verify checks REJECTED lines for every ambiguous pair, record or not; an 8th "evidence" column in the record format; read --partial for every PARTIAL pair as a required step; key the standing exclusion on the box's text, not the article id.

## r005 punch fill — four rounds (b5ce213c, dd442ad3, aeceb643, c02026d3); the grow ate printed ink on p104; widened tolerances painted on colour (LIVE)
**Suggested.** (now in the rule) feed the census's verdict back as a per-page list of punches to fill; review any mask change by a dry run over deep copies with every fill cropped.

## Sign-off (r340 Verification, 2026-11-17)
- Check 2/2a: squash-only delivery — no commits under issues/8702 yet, so check 2 cannot pass by construction; the per-entry LIVE / SAME SESSION classification above is the record. Entries 1–4 are LIVE; the r005/r010/r070/r080/r120/r130/r140/r180/r200 entries in the first block were written within minutes of the step (LIVE); the block above is SAME SESSION.
- The file is NOT harvested and NOT deleted here: the issue is not complete (owner inputs 1–3 and the RESUME question are out). Harvest → reviewed/workflow-errata.md → owner reads → delete, per r340.

## 150 — the first cut of every crop: an edge-ink band test catches a short box before the eye review (LIVE)
On 8702 the first automated cut (worklist box → masters600 via sheet-box, near-white trim) left boxes that were too
short or too tight; 56 of 83 needed a recut. What found them cheaply, BEFORE the eye review: for every tight crop,
measure the 6 px band just OUTSIDE each of its four edges on the master and report the fraction of dark pixels
(luma < 200). Any side above 0.10 is a lead — 19 of 92 here, among them every real short cut (148-1 right 0.95,
151-2/151-3 left 0.81/0.72, 44-x3 bottom 0.88, 46-1 right 0.81, 156-5 bottom 0.62). Expected positives read the same
way and are dismissed by eye: a photo printed to the trim (28-0a/b top ~1.0), a crop cut inside its keyline (8-0),
an adjacent element (11-x's heading box). The recut then grows a side while the line just outside still has ink
(< 250 on > 5 % of the line, stop after 8 clean lines) and re-runs the band test until it is clean except at the trim.
**Suggested.** Add to r150's "THE BUILD CUTS THE FIRST VERSION OF EVERY CROP": "After the first cut, run the
edge-band test (6 px outside each edge, dark fraction > 0.10 = lead), recut by growing on ink, re-test; then the eye
review of every pair." And record each crop's master position (crops_v1_pos.json) — it is what lets a second
person verify the crops against the masters byte for byte.

## 150 — a pure-paper outermost line is a FLAG before the folder opens (LIVE)
10-x2 (one of the nine crops cut before the edge-ink test, then frozen as "approved") carried 3 pure 255/255/255
columns at its left edge, visible as a white sliver beside a near-black photo; the owner caught it at 100 %. The
other 91 had none. **Suggested** for r150: before opening the crop folder, flag every crop whose outermost row or
column is entirely pure paper (all channels 255) — flag, never auto-trim (a frameless figure may legitimately end
in white). And run the edge tests on EVERY crop, including any cut before the instrument existed.

## 150 — page-turn stitching: a seam correlation cannot separate offset from gutter loss (LIVE)
Owner asked for 28-0a/b and 40-0a/b to be stitched. Registration by 1-D cross-correlation of the inner-edge column
bands gave r up to 0.96 and still the wrong answer: dy −22…+3 band to band on 40-0, a rotation of +0.26°, +0.54° or
−0.4° depending on the run, 20 px residual; on 28-0 (star field) almost nothing crosses the seam. Cause: the gutter
removed a strip of picture of unknown width G, so a feature crossing the seam at angle θ registers at
dy = G·tanθ, not at the true offset — a high r says the profiles match, not that the registration is right. Both
halves also carry a pale gutter strip at the inner edge (11–25 px) that must be skipped first.
**Suggested.** Try PAGE GEOMETRY first: the printer set the picture at the same height on both pages, so equal master
y and equal heights give dy directly (28-0a/b: both y=0, 4911 px → dy 0; 40-0: −6 top / 0 bottom = the relative
rotation). Feature matching only after that, and then solving dy_i = dy0 + G·tanθ_i + slope·y jointly. If neither is
clean to a couple of px along the whole seam, do not ship a join — the owner dropped the stitch on this basis.

## 005 — a facing-page detector with a false positive that would have trimmed an advertisement (LIVE)
078/079 carried the facing page's yellow paper past the fold (r005's BED note had flagged both, offering only "bed,
or ink to the trim"; 11 such notes on 8702, none ever swept). The first detector proposed — ink at the gutter trim,
none at the outer trim, high chroma — also fires on 106: a yellow advertisement printed ACROSS the spread, its own
ink running to the fold, its outer trim white only because the ad stops short of it. Cutting on that triplet would
have trimmed the ad. Edge density inside the band does NOT separate them (106 0.021 vs 078/079 0.020). What does: the
facing-page band ends in a CLIFF onto white paper within ~100 columns; spread art continues inward. Implemented as the
fourth part (r005 facing_page()); the BED note now names three answers and which the numbers indicate.
**Suggested.** Sweep every LOOK-AT note before 006 — a flag nobody reads is not a flag.
