# WORKFLOW_ERRATA — SH09

## r005_masters_sheet: check 3 and the step's skew read the bed on a small card, and nothing says so
Rule: r005_masters_sheet.md, Verification check 3; r005_masters.skew_peakiness is not imported by the sheet variant at all, only by the spread.
On a page where the card fills half the frame, measure_skew's ink mask on the raw thumb IS the bed: p164 threshold 81.7, ink fraction 0.495, 99.9 % of it lum < 40. So the step levels on the bed's outline.
Numbers, step line / raw thumb peak / card box on the master, normal and rot90, with peak (SKEW_PEAK_MIN 6.0):
  p163 +0.54 -> -0.02 / 6.41 / -0.48 peak 2.81, rot90 -0.50 peak 22.23
  p164 -0.02 -> -0.02 / 10.94 / +0.54 peak 11.15, rot90 +0.44 peak 5.78
  p165 +0.58 -> -0.02 / 6.11 / -0.48 peak 2.43, rot90 -0.58 peak 23.42
  p166 -0.10 -> -0.10 / 9.59 / +0.34 peak 14.18, rot90 +0.42 peak 5.33
  controls p100 peak 18.62, p050 27.35 (rot90 peaks 4.09, 3.03).
DISPROVED, control's and my first reading, a type-at-90 blind instrument: peakiness on the raw thumb passes (10.94 > 6.0) because the bed has a sharp profile. A peakiness gate on check 3 reading the thumb would not have fired on p164. And check 3's +0.54 was not noise: read on the card box, two orientations agree within 0.1 on each page. It is the step's -0.02 that is blind.
Check 3 itself reads the whole canvas including fabricated white, so card-box cropping is what made the number mean something.
Consequence on this issue: all four card pages deliver 0.3-0.6 deg out, inside the 0.1-0.7 spread r005 records; left, per control. p163 and p165 were tilted BY the step (raw print ~0, levelled by +0.5 on the bed's outline).
Cost: 3 commands, about 10 minutes.

### Parallelism, measured directly on the raw thumbs (my earlier "parallel on p163/p164" was not a measurement)
It read the step's log-line edges. L and T of all four cards touch the frame (card x0=0, y0=0), so those readings describe the scanner frame. Only R and B are edges of the card.
Common sign (calibrated by rotating p163 +1 deg: edge T +0.87, print -0.94, so print is negated here): R / B / print (horizontal, rot90)
  p163 -0.07 / -0.57 / 0.00, 0.00
  p164 -0.56 / 0.00 / -0.52, -0.52
  p165 -0.02 / -0.55 / 0.00, 0.00
  p166 -0.11 / +0.25 / -0.22, -0.36
Print follows R within 0.07 on 163-165, and 0.11-0.25 on 166. No page's print is parallel to B: 0.5 deg off on 163-165, 0.47-0.61 on 166. B-R flips sign front to back (-0.50, +0.56, -0.53, +0.36), as a card cut out of square does when turned over.
Delivered a4600, print against the page rectangle, horizontal / rot90: 163 -0.48/-0.50, 164 +0.54/+0.44, 165 -0.62/-0.58, 166 +0.36/+0.46. The window is axis-aligned in the master, so a parallel trim does not straighten print against the delivered rectangle.

### Resolved by control: option 2, levelled on the print; this entry belongs with r005_masters_sheet.md, KNOWN DEFECT, OPEN -- THE SKEW MASK MUST EXCLUDE THE BED
The chain's documented convention levels on the type and accepts the trim not parallel (r005_masters_sheet.md, *What the paper actually is*), so the four cards were the only pages not levelled on their type. issues/SH09/reviewed/level_cards.py, masters600 and a4600, one angle and one pivot per page. Other 164 pages untouched. sheets600 and cmyk2400 not touched.
| page | angle, orientation | print vs page box before | after, residual (peak) | print vs R, vs B (survive any rotation) | 010 blocks old -> new |
| 163 | -0.50 rot90 | -0.50 (22.23) | 0.00 (60.49) | 0.07, 0.57 | 34 -> 20 |
| 164 | +0.54 horizontal | +0.54 (11.15) | 0.00 (21.38) | 0.04, 0.52 | 26 -> 24 |
| 165 | -0.56 rot90 | -0.58 (23.42) | 0.00 (51.18) | 0.02, 0.55 | 40 -> 37 |
| 166 | +0.32 horizontal | +0.34 (14.18) | 0.00 (26.34) | 0.11-0.25, 0.47-0.61 | 25 -> 24 |
The card reads about 0.5 deg out of square, and that stays (a reading: the sign flip front to back fits it; not proved). 163/165's tilt was introduced by the step; 164/166's came off the glass, which is placement, not a property of the card.
Angles were chosen at the maximum of the skew score's peak, not by measure_skew's refinement at full resolution: on p165 that refinement read -0.44 and left -0.12 at the reduced scale, peak 25.93, against -0.56, peak 50.81. Full-resolution reading of the result is +0.12. r005's docstring prefers the full-resolution refine; on a card with print in two directions it did not find the best angle.
A measurement taken on an edge the scanner frame cut is not a measurement: my first parallelism statement read L and T, which on all four are frame edges.
**Suggested.** check 3 and measure_skew read a mask that excludes the bed (ink inside the card box only, found from the frame's dark border), and Verification check 3 reads print angle on the card box, not the whole canvas; say in the sheet rule that L/T edges touching the frame are frame edges.

## r040: the intro readout has no owner for a false hit
The script prints every line-start `>` and says each has to be an intended intro; the rule never says who acts on a false one or how, and r080's intros>1 is the only stated backstop. p074 `> ANLEGEN` was a listing wrap, and r080 would only have flagged a second intro, not said what it was. Cost: a crop. Took the reading that 040 resolves it, moving the line into the fence as printed.
**Suggested.** add: "A false hit (a listing wrap, a quoted prompt) is 040's to resolve: move the line back into its fence as printed and log page and reason; r080's intros>1 is only a backstop."

## r050: the placeholder check cannot find the placeholder case
`grep -nE '&lt;[a-z]+&gt;' ... | grep -E '<(p|s|b|i)>'` run on the HTML matches every line that opens a paragraph, since `<p>` is on all of them: 13 hits on SH09, all false, and none of them the real ones. And the real ones escaped it twice: p114 prints one key per line, so no line carries both shapes, and `<a>` and `<q>` are not in its list. The prose clause ("comma-separated run") does not cover a per-line list either. Found with a tag count over the .md, which listed exactly `<a> <s> <q>`. Took the reading that neighbours on adjacent lines count, and escaped all three.
**Suggested.** replace the grep with a per-line scan of the .md for `<[a-z]>` tag tokens outside fences (`grep -noE '<[a-z]+>'` filtered against the real tags), and say that a key list printed one per line counts as the placeholder case.

## r060: the list survey over-reports by design and says nothing about how to read it
29 hits, 21 of which simply continue the previous number. Only 8 are the defect the section describes. Reduced by comparing each to the preceding item; the rule could say so. Cost: small.
**Suggested.** add: "Compare each hit with the preceding list item; a hit that continues its predecessor's number is not the defect. Report the two counts separately."

## r070: the flank test converts OCR noise into an en dash, and is only asked about bare numbers and quotations
A speck read as `-` between two words of a sentence is not on either list unless it happens to fit the suspect shape. p012 was a suspect by luck (a digit follows); p014 `verwendete - Befehl LOAD` was not, and I found it only because a kept-list scan printed it. Two confirmed; the other 163 conversions were not checked against the page, so more may exist. Neither the script nor the rule has a shape for this.
**Suggested.** add a third suspect shape to the flank test: a converted `-` with a lowercase word on both sides (`word - word` mid-sentence), and list every conversion with its page so the bulk can be spot-read.

## r070: resolving U+201A can be larger than the character
The table gives kinds for the mark alone. p003's site sat in a paragraph interleaved with OCR of a picture, including a false `<h3>`. Rewrote that passage from the page as the most defensible resolution, since a resolved mark inside garbage is not a resolved site. It changes the h3 count against 030, which nothing else in the chain expects.
**Suggested.** add: "Where the U+201A site sits inside OCR of a picture, resolve the site from the page as a passage, and record any heading count change for 030 in LOG.md."

## r080_split: the byline test accepts a mixed-case word in brackets
Rule: *Notes / lessons*, "An all-parenthesised paragraph is not automatically a byline". `(ungeSHIFTet)` on p113 (a key list heading) passed: no digit, no `=`, not `.isupper()`. It became an `<address>` and went into the author meta beside the real author. Found only by reading the wrapper's output against a heads list; the multi-byline check does count it, as one more byline in a file with one. Repaired by hand. Cost: small, but it would have published a false author.
**Suggested.** add to the byline test: reject a bracketed word that is mixed case inside one token (`ungeSHIFTet`), and cross-check every new `<address>` against the article's author meta before writing it.

## r080_split: the pair check's anchored inline regex still matches a key table
Rule: *Verification — list multi-intro / multi-byline files*. The rule says the anchored form hits only editor codes and full names. On SH09 `&lt;+> = Blättern (vor)` (same article) ends a paragraph in `(vor)` and reports `bylines=2`. Cost: one look. Same class as the 135 distinct words the anchoring was to remove.
**Suggested.** extend the anchored inline regex to require a name-like token (capitalised word, or `/xx` editor code) inside the brackets, so `(vor)`, `(zurück)` and similar key-table words do not match.

## r080_split: pages by table, and no list of what is unclaimed
Rule: *WHICH PAGES BELONG IN 64er.pages*. It says "carries only an article's listing". p47, p81 and p83 carry only a table, and 030 omitted them the same way, with their text. Took the reading that a table page in the run is claimed like a listing page. The rule gives no step that enumerates pages no spec claims, though that is the input for the whole section; made one by hand from the 28 specs and looked at 46 pages at thumb scale. Cost: 3 montages.
Also unstated: where to correct the spaced spec. Corrected the h1s in the consolidated file before running the script, so one pass of the wrapper produces the specs and nothing is rewritten after it.
**Suggested.** add a step that lists every page no spec claims, from the specs and the page count, before the section is applied, and say: "a page in an article's run that carries only a table is claimed like a listing page."

## r080_split: the Verification block is literal `issues/8607`
Same stale-literal class the rule itself records for the pair check. Substituted SH09 throughout, in a scratch script. Cost: small.
**Suggested.** replace the literal `issues/8607` in the Verification block with `issues/$ID`, set from ISSUE.

## r090_toc_txt: "the bold title and only that" has no answer when the bold line is a kicker
p005 prints bold `Eingabehilfen` with `Checksummer 64 V3` in regular weight below it. Read literally the entry would be `Eingabehilfen`, which matches no filename; r100 compares the two. Corpus (SH8604, 8605, 8606) has `Checksummer 64 V3`, so that went in. The kicker survives only in the toc_title, by r100 kicker clause. Cost: one corpus grep.
**Suggested.** add: "When the bold line is a kicker above the title, the entry is the title line; the kicker goes to the toc_title per r100. Check against the corpus's earlier printings."

## r100_toc_category: the coverage check cannot pass on a misprinted start page that lands on an unclaimed page
r090 says a wrong printed page goes into toc_entries.txt as printed. p005 prints Checksummer 64 V3 at 99; the article is p97 and 98/99 are ads, so the check prints `NO ARTICLE for Rubriken entry Checksummer 64 V3 p99` on a correct issue, and `adjudicated.txt`s `omitted-` key says the wrong thing (not omitted). r090 precedent, SH8604 MSE 95/94, did not show this, the misprint fell inside the article. Disproved: that the output means a dropped piece; the 080 LOG and the p103/p108 captions pointing at Seite 97 settle it. Left as printed and red; the check needs a way to declare a misprinted page. Also its message says `Rubriken entry` for every section.
**Suggested.** give the coverage check a declared-misprint key (e.g. `misprinted-start <title> <printed> <real>` in adjudicated.txt) so a known Inhalt misprint reads OK, and make the message name the section instead of `Rubriken entry`.

## r110_pubdate: the README look cannot run on a post-SH8 id
The block takes `YYMM=${ID#SH}`, so SH09 gives `09`, and `$((10#${YYMM:2:2}))` aborts: `10#: invalid integer constant`. The id has no year, the bullet is `Sonderheft 9/86` (README line 63). Read by hand. The rule cadence list and its "write the bound as PROVISIONAL ... carry to PAUSE 2" also do not cover a pubdate the owner has already set before the step runs; left unchanged per dispatch. Also: `will refuse if pubdate is in the future without --future` was not what I measured: `ArticleDatabase` with `--issues SH09` and no `--future` loaded SH09 at 2026-12-05, because the gate is `not (build_future or build_issues)`: naming the issue bypasses it. Only a whole-site build without `--future` skips it.
**Suggested.** make the README look accept a year-less Sonderheft id (SH09 and later): read the README bullet by issue number, not from `${ID#SH}`; and say what to do when the owner has already set pubdate before the step runs (leave it, log it).

## r090 check 3 / r110 build check: `generate.py ... local` wipes out/ under a running server
generate.py does rmtree on out/ before writing, and a sibling server (`generate.py --issues SH8502 SH8503 SH8604 --future local`, pid 3044) was serving it. Not run. Loaded `ArticleDatabase` alone instead (import with argv, no generation), which is where `ERROR: category not in toc.txt` is raised. Passes for SH09; Missing PDF warning expected at this stage. Article pages not rendered.
**Suggested.** say: "Never run `generate.py … local` while another session serves out/; check with `lsof -i :8000` first, or load ArticleDatabase alone for the category check."

## r120
Check 3b prints NOTHING on SH09 and exits 0. The disk's separators are `-------s.30-----`; `-+(\d+)` cannot cross the `s.`, so every section reads as a frame bar and is skipped. Not a pass: the check said nothing. Confirmed by running an adapted copy (`s\.(\d+)`, last numbered page carried forward, <tmp>/scratch_120/check3b_sNN.py), which maps every section. Same shape as the rule's SH07 gap 1. Also it keeps one article per page, so a shared page (103, 111, 157) shows only the last one sorted.
The rule's section-to-article statement (`NN` is the page) is wrong by a few pages where the disk followed a misprinted Inhalt: 99, 137, 143 here; 99 maps to an ad. Read them against the Inhalt's misprints list.
Check 4 and the rule cannot see a disk file SHORTER than the print when it is not BASIC: turbotapecopy (273 bytes on disk, 1216 printed) raises nothing here. Found only by reading a `Name :` header against the load address; cost one page crop. A header sweep is cheap and no rule asks for it at 120.
**Suggested.** fix check 3b's separator regex to `s\.(\d+)` with the last numbered page carried forward, keep every article on a shared page, and add a header sweep at 120 that compares each MSE/Name header's load address and length with the disk file.

## r130_place_figures: the listing TODO is not the crop worklist's source
The dispatch said figures get TODO markers from which the crop worklist is built, every figure with page and caption. r130 defines a marker only for a listing, `<pre>TODO</pre>`; r000's gate text says "every unplaced figure is a TODO"; r150's list comes from r150_figure_captions.py and looking at pages. I placed no Bild marker, since no rule gives one its shape, and recorded pages for listing TODOs in LOG.md. Cost: a page of reading in r000, r150, and a precedent diff of SH8608's 130 commit, which has no Bild marker either.
**Suggested.** say in r130 which marker a Bild TODO takes (or that figures get none, and r150's list comes from r150_figure_captions.py plus a page look), and make r000's gate text match it.

## r130_place_figures: `data-checksummer` has no method for choosing the version
*"Look at how the issue you are on prints its checksums"* does not say a version can change inside one article. Assuming 3 on Floppy-Kurs gave 1 of 12 on Listing 14, which read as print/disk divergence. Computing all versions over the program and aligning against the printed sum column separates them: 11 of 12 at V2, 135 of 138 at V3 on EDDI in the same article. DISPROVED: that a mismatch at V3 means a different program. Tesseract reads the slashed zero as 8, 9 or 6, so compare with those as one class. Cost: three passes.
**Suggested.** add: "Compute every checksum version over the program and align against the printed sum column, per listing; a version can change inside one article. Treat a slashed zero read as 8/9/6 as one class."

## r130_place_figures: an uncaptioned program printed in the running text is not named
SH09/64 prints four BASIC demos in body type, no caption, each with a disk file. The Variants table assumes a figure with a caption. SH8608/79, the same article for the C 16, keeps `<pre><code>` and a download; the dispatch asks for the embed where a disk file exists. Took: embed without figcaption where print equals disk (2), transcription plus download where it differs (2).
**Suggested.** add a Variants row: "program printed in body type without caption and with a disk file: embed without figcaption where print equals disk, transcription plus download where it differs."

## r130_place_figures: check 7's duplicate has no working home
Check 7's duplicate on 18b has no stated home here: the rule points at r000_reviewed.py key r130-dup-listing, and no file on disk uses that key (grep over rules/*.py and issues/*/reviewed/). Recorded in LOG.md only.
**Suggested.** create the `r130-dup-listing` key in r000_reviewed.py, or point check 7 at a file that exists.

## r006 / r000: the marks census has no recipe for finding marks, only for gating them
r000 fixes the size (lum < 153 after a 2x2 opening) and the survive test by path, and r006 says the sweep is a LOOK. Neither says how to get a census from 168 pages when the look resolves about 0.5 mm at best. An isolated-component census at 1 mm gap returned 13,138 components, 232,785 when OCR word boxes were used as the mask (hex listings fail it wholesale). Took four detectors plus a look at all pages at ~63 dpi: 3 mm isolation, chroma above the page's own ink median, small survivors with no neighbour within 1.7 mm, and PDF-layer words beginning U+201A. Stated the miss in marks.txt: a mark under ~0.5 mm close to a glyph. Cost: about an hour's measuring. 8701's numeric gate is only in that issue's marks.txt; took it, and measured it on the images extracted from the PDF.
**Suggested.** add a census recipe: isolation, chroma above the page's ink median, small survivors without neighbours, and PDF words beginning U+201A, plus a thumb-scale look at every page; state the detection limit (about 0.5-0.85 mm from a glyph) in marks.txt.

## r000: "below the cutoff" sends a large hand note to the record if it is pencil
p111 carries a 26 x 3.8 mm grey note. At 35 % it leaves 49 scattered black pixels, longest run 3, so by the gate it does not survive and is recorded, not surfaced. A reader sees faint dust there. The rule is explicit, so I followed it; the gate's run/count numbers are designed for specks, and whether a large note reduced to dust counts as surviving is not stated. Reported to the orchestrator with the crop coordinates.
**Suggested.** add to the gate: "A hand note whose area at 600 dpi is larger than X mm² surfaces whatever survives at 35 %; the run/count numbers are for specks." (Ruled by control on SH09: p111 went up.)

## r000: the contone gate surfaces specks a reader cannot see as marks
72 of the 110 surfaced are on contone pages, most 0.2-0.4 mm, many inside a printed tint, because at 150 dpi one dark pixel off a light ground passes 40 grey levels. 8701 surfaced the same class and the owner ruled them all plate. Left as the gate says. A size floor for contone would cut the owner's queue by more than half; that is the rule's call.
**Suggested.** the owner ruled on 8701 and SH09 that contone specks are plate; state in the gate that surfaced contone specks below a size the owner sets are recorded, not queued. (Control ruled no size floor on SH09; this records the open question.)

## r006: the mixed build's cover gate ran before the cover changed under it
title.png was replaced 20 s into the mixed build (01:41:04 banner, 01:41:24 file), after the build's own gate had run, and the mixed build never refreshes NNN_150.png. The cache was still from the RGBA file. Nothing in the build would have said so: the gate had passed, and the difference is under its threshold anyway. Regenerated 001_150.png by r006's recipe at 01:41:48, before any guetzli-q*/001.jpg existed (first 01:43:13). Cost: nothing, by timing luck.
**Suggested.** add: "After any change to title.png, regenerate 001_150.png before the mixed build passes page 1, and check its mtime against title.png's."

## r006: "*Verification 4* every page exact A4" reads the page box, and the OCR layer's box is the one that counts
Passes: 164 pages 595.34 x 841.97 pt, the card 421.61 x 595.16 pt on all four, from `.ocrcache/NNN.pdf`. Noted only because the 0.34 pt excess over A4 (4961 px at 600 dpi tagged 402 via 67 %) is a property of the recipe, and the check has no stated tolerance.
**Suggested.** give Verification 4 its tolerance: "exact A4 within 0.5 pt, read from the OCR layer's page box (.ocrcache/NNN.pdf)".

## r160_fill_tables: evidence block against the sweeps
Evidence-in-report asks one pasted line and disposition per candidate block walked. The rule's narrow-column sweep returned 1271 on SH09, and the same rule calls it a hint list that finds nothing. Took: dispositions for the heading-word sweep and the walk's finds; the 1271 counted, not skimmed. DISPROVED nothing about them; say which the rule wants.
**Suggested.** say whether the evidence block wants one disposition per hint (it should not for the narrow-column sweep) or per walked block: "Disposition the walk's finds and the heading-word sweep; count the narrow-column hints."

## r160_fill_tables: beautify beside a concurrent step
Step 9 `js-beautify --replace` rewrites whole files while 170 edits the same files, which a dispatch forbids in other words. Took: beautify a copy of a fresh read, compare all <pre> and the non-whitespace text, write only if the file has not moved. All 16 came back byte-identical (the tool was first seen to reformat a planted file), so nothing was written.
**Suggested.** replace "beautify every touched file" with: "beautify a copy, compare <pre> and non-whitespace text, and write only if the file has not moved since it was read."

## r160_fill_tables: dash separator column not named
A glossary printed `TERM – text` has no rule: the dash is a separator or a character. SH8608 keeps a `=` column. dBase Tabellen 1-7 dropped it, Floppy Tabellen 14-16 keep a column, 64'er-DOS Tabelle 1 keeps it in the key cell. Three readings in one issue, each by a different hand.
**Suggested.** add: "A `TERM – text` glossary keeps the dash as its own column (the SH8608 `=` precedent), unless the print sets it inside the term."

## r000 briefing: many images in one turn are dropped
Twenty contact sheets read in one call came back `[media removed: request limit]` with no error; so did later batches of seven. Cost: the whole walk twice. A sub-agent reported the same on its montages. About four images per turn survived.
**Suggested.** replace with r000's image-cap rule (look once, `[media removed]` is a stop); this entry is superseded by it.

## r170_transcribe_todo_listings
Column crops: the rule says single column but not to check the left edge. Page margins here move 100 px between odd and even pages; a fixed x clipped the first address digit on about 25 crops, and GLM then wrote `1f1` for `11f1`, with no error. Cost one re-run of 80 crops. Detect each page's column start first.
*Prove it* assumes the row sum protects the address. MSE1's sum covers only the address's low byte, so `de49` for `0e49` passes; the check has to hold the address column contiguous as well.
r170_score_hex_ocr.py is named as the method for checksums but has 8611's prg hard-coded and scores against a known file; it cannot check a listing with no file. Row check written from tools/mse.py instead.
Rule item 4 says beautify every touched file; with a concurrent step on the same files the dispatch forbids it. No statement which wins. Took the dispatch.
Reverse column of a monitor dump: neither r170 nor r150 says what to do when the hex beside it fixes the glyph but the blob is unreadable. Took bytes to `<span class="inverted">`; 8505's text is the precedent for typing the column at all.
**Suggested.** add: detect each page's column start before cropping; check address contiguity alongside the row sum (MSE1 covers only the low byte); name tools/mse.py for listings without a file; and say the inverse column goes to `<span class="inverted">` when the bytes fix it.

## r160_fill_tables: range rule names page ranges only
*A PAGE RANGE IS SET WITH A HYPHEN* gives its reason from the page metadata, and SH09's byte ranges (`000–001`, `3–6`, en dash in print, 30 px against the hyphen's 15 at 600 dpi) are not pages. Its corpus count is all `N-N` cells, though, and its "odd one out" argument fits: 73 byte-range key cells in article 30 are hyphens. Took: hyphen for numeric ranges, print's en dash inside words. Say whether the rule means every numeric range.
**Suggested.** extend *A PAGE RANGE IS SET WITH A HYPHEN* to every numeric range in a key cell (byte ranges included), and keep the print's dash only inside words.

## r180_author_meta
*A missing byline means LOOK AT THE PAGE* says a line went with the byline, and stops there: not who restores it, while r190's page walk also claims dropped text. On SH09 four articles (110, 119, 120, 139) each lost two column-end lines into one interleaved listing block with the byline. I restored those lines here, since an `<address>` after `anzufin-` reads as damage, and left everything else on the page to r190. Reading picked, not stated by the rule.
Check 5 counts entries and never compares order. 080's wrapper wrote 92's meta sorted and deduped (`Boris Schneider, ev, D. Hein, ...`, body starts `Dieter Hein/bj`), which the Bücher section forbids, and no check said so. It passed check 5 with 14 entries against 18 names. Only a per-file comparison of the meta to the split `<address>` tokens found it; that comparison gave 0 mismatches over the issue once fixed, so it would serve as check 6.
Check 3 with a Sonderheft as PREV keys on the exact title, so a Q&A rubric is flagged whenever the previous issue's title differs (94 here against SH8608's `Fragen und Antworten zum C 16`). Expected, answered in reviewed/.
**Suggested.** add: "A byline missing with column-end lines: 180 restores the lines taken with it; the rest of the page walk is 190's." And add check 6: compare each file's author meta with its `<address>` tokens, order included. Check 3 should key Sonderheft rubrics on the rubric, not the exact title.

## r000: the torn edge's fill residue survives into the PDF and reaches the marks queue
p130 +4903+6727: in the raw the spot is the torn edge beside the bed; a4600 and the JBIG2 carry a line of specks there, no mark on paper. r000 calls such a trace ours and says fix, not surface. 005 is frozen for this issue, so it stays in the file with a note and the pair stands as a named FAIL. Only the raw panel showed it: a graded left panel looks like any speck. Cost: one wrong line handed over once. Control's rulings superseded two entries of mine above: p111 now goes up, and no size floor.
**Suggested.** add to the fill rule: "A trace of the torn-edge fill in a4600 is ours: fix it in the master, or name the page as a FAIL in a4600-overrides.txt when the step is frozen." Show the raw panel beside graded ones in every surfaced crop.

## r190_layout_fixups
Column interleave where the text wraps round a picture (SH09 p30): r190 lists lost drop caps, split paragraphs, dropped paragraphs; not this. OCR lines from two columns alternate inside one `<p>`, with word fragments (`einzuBetriebssystem`, `manipufiere`). Read as: block moves, plus the few words the OCR mangled, each from a crop. Cost: about 6 crops.
`1.1 Dateiarten` run into the end of the preceding `<p>`: the *headings that swallowed body text* row covers the other direction only. Same fix; say so.
The verification block runs over `issues/<ID>/*.html`; with 190 split in two agents the sweeps report the other's half-done files. I ran them on a copy of my five. A split dispatch should say so.
**Suggested.** add rows: "Column interleave around a picture: move blocks, then fix the mangled words from a crop" and "a heading run into the preceding `<p>`: split it". Say a split dispatch runs the Verification sweeps on its own files only.

## r006: a report named a file my own re-run had deleted
The generator for the supplement crops empties its folder first. I wrote supplement/INDEX.txt, re-ran the generator to fix a crop, and reported the INDEX without listing it again; it no longer existed and the orchestrator wrote one. Cost: one wrong claim and a repeat of work. `ls` what you name, after the last step that writes there.
**Suggested.** add to the hand-back rule: "`ls` every file you name after the last command that writes in its directory."

## r190_layout_fixups: no method for code scrambled past moving blocks
The rule's guardrail says code in <pre> comes from the existing HTML, never retyped from print, and the dispatch says repair by moving blocks. SH09's article 64 (p64-78) had listing lines shredded across <p> and <pre>, comments detached from instructions, and two printed listings with no text at all. Moving cannot restore a line whose OCR is `IDA #841`. The brief's "`<pre>` is transcription, read the crop and fix it" points the other way. I took the brief, retyped from the page, and logged it. Cost: the largest single edit of the step. Rule should say which wins, and whether a dropped listing is 190's or 170's: 170 only fills `<pre>TODO</pre>`, so nobody owns one that never got a marker.
**Suggested.** say which wins for code shredded past moving: "a listing whose lines cannot be recovered by moving is retyped from the page, and a dropped listing with no marker is 170's (190 inserts the `<pre>TODO</pre>`)."

## r190_layout_fixups / r000 briefing: reads of the same image again and again
Image results leave the visible context after a few turns and read as `[media removed: request limit]`, which looks like a failed read. I re-read pages many times to "confirm" them, well over 300 needless reads. Disproved: that those reads had failed; the text taken from them on p68 matched on re-read. Write the reading down when the image is in view, once, and do not treat the placeholder as a failure.
**Suggested.** superseded by r000's image-cap rule (look once, write it down, a placeholder is a stop, not a failed read).

## r000: the marks census gates colour on darkness
The population is built from lum<153, and the chromatic class needs >= 12 black px on top. A coloured pencil stroke (SH09 p110: red, lum about 205, 3 mm long) has none, so it never reached a sheet, though the census's own `chroma` class had found it. Only a later page reading caught it, by chance, at 25 %. The rule says the master decides surfacing, the gate only describes; the population should follow. Read every clustered chroma component on bilevel pages: 40 tiles on SH09, one sheet, cost minutes. Found 4 of 115.
**Suggested.** build the census population from the union of lum<153 and the chroma class, and read every clustered chroma component on bilevel pages.

## r220_index_meta: both Sonderheft checks assume the id form SH86NN
Verification derives the key with `YY=${ISSUE:2:2}; MM=${ISSUE:4:2}`, and the routing check with `int(code[4:6])`. For `SH09` the first gives YY=09, MM empty, `10#: invalid integer constant`, and the second a ValueError. The key this rule itself asks for from Sonderheft 9 on, `9/86`, cannot be derived from the id at all: the year is not in it. Cost: two reruns; I set the key by hand and passed `SH8609` to the routing check only to reach 9/86. `r220_index_meta_apply.py` not run, nothing to apply. The rows come back empty either way, so the outcome stands, but a future SH id with rows would break here too.
**Suggested.** derive the key from the README's Sonderheft number for year-less ids (SH09 on), and make the routing check accept `SH\d{2}` without int(code[4:6]).

## r240_rubric_banners: the check's Bücher glob misses a Bücher article by another name
The rule says Bücher "can stay filename-glob" as titles equal the rubric. SH09's is `92 Buchbesprechungen`, under a printed BÜCHER band, and the check prints `Bücher: N/A (no article in this issue)`, which is false. Harmless under `not applicable — kind`; p92 had to be read to rule out the input. Counting by head1 would see it, as r210 already learned for Leserforum.
**Suggested.** make the Bücher check count by head1/rubric band, as r210 does for Leserforum, not by filename glob.

## r200_leserforum: the Verification block uses $PY and never sets it
Checks 3, 4, 5 fail outright unless PY is set by hand; the other blocks set it. Also the rule has no row for answers partly signed by readers: SH09 94 has 4 of 22. Read as the monthly Leserforum and SH8605/155 do it: p.author in the div.a, no author meta.
**Suggested.** set PY at the top of the Verification block, and add a row: "answers partly signed by readers keep p.author inside the div.a, no author meta" (SH8605/155 precedent).

## r210_head_meta: `&` advice stops at the corpus total
It reports 159 literal against 52 `&amp;` and calls both fine, and the literal form reads as the one to pick. Recent Sonderhefte differ: SH8605-08 carry 26 `&amp;`, 0 literal. I wrote literal first and redid it. Cost: one sed.
**Suggested.** add: "Recent Sonderhefte (SH8605-08) use `&amp;` throughout; match the issue's own neighbours, not the corpus total."

## r280_ocr_word_cleanup
- OCR `\¬` is a lost glyph, not a hyphen. p65 labels `X- beziehungsweise \¬Register`; the HTML had `-Register`, print `Y-|Register`. Neither the spaced-¬ sweep as a dash nor any spell check names it: the token reads as a valid suspended compound. Found by a leading-hyphen grep. One site in SH09. A sweep for `\\¬` over labels.json would have found it directly.
- "Always finish with a contextual read" has no size. SH09 prose is 59764 words (r290-free, tables and pre out). Not read end to end; stand-ins named in LOG. Which is enough is not stated. Disproved: the jam detector finds much here, 138 candidates, 0 real jams; both real jams (`istes`, `Daer`) were under its 9-letter floor and came from the full unknown-word list.
- `## Verification` also matches `### Verification step` as a substring: a script taking the first hit runs the wrong fence. Cost one run, rc 1 on `<NNN>`. Anchor on the whole line.
- Correction to the entry above, jam detector: 138 candidates, 0 real jams on SH09. `istes` and `Daer` sit under its 9-letter floor; `dashheißteslliegt` does not split into two known words. All three came from the full unknown-word list.
**Suggested.** add a sweep for `\¬` over labels.json; give the contextual read a size (e.g. every article in full, or name the stand-in method and its coverage); and anchor the Verification fence on the whole line `## Verification`.

## r280
The contextual read has no class for a speck the OCR read as punctuation and the HTML kept: `und. Datenfelder` p92, `'Leider` p93. Valid token, no jam, passes quote balance and the spell checks. Found by a word-pair diff of the HTML against labels.json plus a pattern grep (stray `'` at word start, period before lowercase); the same diff shows every place an earlier step changed print, which is how `»Müllers«` against printed `»Müllers»` p114 surfaced: a print error had been repaired in place, against the standing ruling, and no log named it. Cost: little, the diff is 60 lines. Method 2 (words absent from the OCR) sees neither case. Reading the rule's "method-2" as a bigram diff is what I did; the rule does not say it.
**Suggested.** add the paragraph-level word diff of the HTML against labels.json as method 2's second half, with a pattern grep for stray `'` at word start and a period before lowercase.

## r280 (contextual read)
The classes name valid-word jams and lost words, not punctuation invented from a speck: 64 had `kann. .Der`, `wurde..Der` and a lone `"` before `ausgehend`, plus `O`/`0` in `$OF` and `zwischen O und 15`. All were in the OCR, so the method-2 list cannot show them, and no sweep ran on them. Cost nothing here: a prose-only grep for `\. ?\.`, a stray `"`, ` -,`, `\$[0-9A-Z]*O` found them in seconds. A token-level diff of article prose against labels.json was also useful as a reading aid, but it agrees wherever the HTML inherited the OCR, so it is no substitute for the crop.
**Suggested.** add a prose-only grep for `\. ?\.`, a stray `"`, ` -,` and `\$[0-9A-Z]*O` to the contextual read.
## r280
The contextual read found errors the method-2 list cannot show: a word that is in the OCR passes it. Article 30 p43 `aber –` came from a margin speck the OCR read as `-`; no check looks at a dash at line end against the page. p52 `Positionieren` is a word the HTML corrected against a print `Positonieren`: it looked like nothing, only a word diff of paragraph against OCR showed it. p56 `$C0000` came from the OCR's `$CO000`: an O->0 fix without a length check on the address. Cost: none, found here. A paragraph-level word diff against labels.json took one script and gave these three; r280 could name it.
**Suggested.** add: "a dash at line end against the page, and every O->0 address fix with a length check."

## r280: a reader dispatch should state the table count
The closing-read brief named paragraphs, not tables. Article 30's reader reported done with Tabelle 12 read only at 12 % and Tabelle 8's last row cut off; I read both on the page. State the number of tables per reader up front and ask for each one's verdict.
**Suggested.** add to the dispatch template: "State each reader's table count and ask for each table's verdict."

## r300: case (c) has no disposition word
`Every aside carries a disposition comment` gives three words, and `the comment is mandatory wherever a PROGRAM could be affected`. A conditional erratum, r300's (c), says only what never to write. Datev's 12/86 POKEs fit none: the disk has not got them, and they are not print errors. Left without a status comment, per the `stays unmarked` paragraph, though that paragraph is about a decision the owner has yet to take and this is not one. It cost a corpus search: one conditional precedent, SH8606 Giga-CAD, which patched instead.
**Suggested.** case (c) has its word now (`Bedingte Korrektur, nicht angewendet`, and reviewed/errata_status.txt for a binary): ruled by control on SH09. Keep the entry for the harvest record.

## r300: harvest misses a correction outside a rubric
The rule names rubrics and the index. 8501's correction of 8411's listing mix-up is an unheaded `<aside>` in the course's own next part, and it decides what print and disk mean for Listing 6 here. Found by grepping the part for `Listing 6`. Fehlerteufelchen.md also begins at 1/86, so 8504's Floppy-Kurs item is not in it: a reprint of a 1984-85 original needs the rubric files.
**Suggested.** add: "Also grep each original's NEXT parts of a series for unheaded corrections (`<aside>`, `Listing N`), and use the rubric files for 1984-85 originals, which Fehlerteufelchen.md does not cover."

## r300 / generate.py: known reader-facing divergence
The print-derived `dos v3 mse.prg` renders `PROGRAMM : DOS V3 MSE` where print says `dos v3`, because the MSE header takes the filename. Ruled for a later generate.py fix (CORPUS_QUEUE item 3); stays in SH09.
The values `#$01` and `#$00` in article 30's Futureteufelchen come from the printed DATA lines on p53, not from the erratum's text, which prints `LDA #$ …`.
**Suggested.** ruled for CORPUS_QUEUE 3; keep for the harvest record. Add to r300: "When a Futureteufelchen's values come from the page, not the erratum, say so in LOG.md."

## r150_place_images
- No name for one picture printed across a page turn. A cut comes from one sheets600 file, so it is two cuts; `*-0a`/`-0b` means two pictures in SH8608's 56-0a..c. Used 30-0a, 30-0b for SH09 p30/p31. The rule's "a table across two pages is ONE crop" does not say whether it reaches photos. Cost: a judgement call.
- The lead-slot test reads "directly under the headline, before the body" but does not treat a framed drawing beside the intro, top of column 2, under a full-width headline (SH09 p106, p139). Read as lead slot: no text above it in its column. SH8608's p105/p144, with body text above, were disproved as a parallel.
- SH8608's worklist quotes coordinates on masters600; the owner cuts from sheets600 and the two differ in canvas and offset per page (SH09: up to 86 px). The rule does not say which frame a row's geometry is in. Measure on sheets600.
**Suggested.** ruled by control on SH09 (f4f601b7): name a page-turn picture `-0a/-0b`, the lead-slot test is per-column geometry, and worklist geometry is on sheets600 named in its header.

## r150_place_images (the lead slot does not promote a cartoon) — owner ruling on the crop delivery, SH09 p106, p139
- The worklist header says "Cartoons and ads are left out." The lead-slot test says a framed drawing directly under the headline beside the intro is a lead picture. On SH09 p106 (man with an axe at a table of papers) and p139 (figure in a TURBO FORMAT shirt leaving a door marked 1541) one object met both. The worklist went with the lead slot (rows 106-0, 139-0), and the owner left them out on 2026-11-14: "the others are comics i decide to omit". Articles 106 and 139 ship without a lead picture.
- This is the same site as the lead-slot bullet above, seen from the other side: that bullet made the slot per-column geometry so the two drawings qualified, and this ruling says qualifying does not make a cartoon a lead picture. One finding for the harvest, not two.
- Cost: two worklist rows the owner had to rule out at delivery, and a gap report that turned out to be a decision.
**Suggested.** Add to r150's lead-slot test: "The lead slot places a picture; it does not decide whether a drawing is one. A signed or captionless cartoon in the lead slot is a cartoon, and the worklist leaves it out under its header line (owner, SH09 p106/p139)."

## r150_place_images (a page-turn picture can come back joined) — the SH09 crop delivery, 30-0
- The worklist asked for 30-0a (p30) and 30-0b (p31) under the `-0a/-0b` ruling above. The owner delivered one 30-0.png, 5851x6204, both halves joined across the fold and cut out onto white. Measured: each half is a pixel copy of the regraded sheets600 (template match 1.000); the p31 half sits 17 px lower than a plain abutment and the sheets overlap by 43 px, so the join is aligned on content; a band about 10 mm wide across the fold is retouched; three looks across it show no step. Placement and name are with control for a ruling.
- The rule has no case for a joined delivery, and its file-name convention only covers the two-cut form.
**Suggested.** Add to r150 next to the page-turn naming: "If the owner delivers a page-turn picture joined, place the one file under the base name (`30-0`) as one figure. Before placing, check the join: each half against its own sheets600 page, the alignment, and the seam."

## r325_read_for_sense (A SPACING QUESTION IS ARITHMETIC) — reader M, SH09 article 30
The typewriter face of article 30 draws '#', '<' and '>' wider than a cell (52-53 px at 41.5 px pitch) and leaves 16-30 px on both sides, and its typist used gaps of about half a cell (operand at +3.56 cells, word gaps of 30-34 px). The rule assumes every gap is a whole number of cells; here "GET#1" spans 6 cells and "ST<>64" 8, with no way to say on which side of the wide glyph the blank sits. Cost: two lines left unedited and handed to control (p040 L1032). Reading taken: round the half-cell columns where every candidate rounds the same way (Listings 9/10: HTML held), leave the text where the side is undecidable. Also unstated: whether titles/notes inside a listing box, broken at the box width, join like wrapped comments; I joined them (Listings 9, 10, 12).
**Suggested.** ruled by control on SH09 (ae7ff984): across a wide glyph compare the same construct by pixel landmarks; prose broken at a box width joins with a space, code without.

## r330 (diff normalisation and record classifier) — reader U, pairs 30 ← 8410/153, 8411/117
- The end-of-line hyphen join fires mid-line on a suspended hyphen whose next word is not in the closed set (`und oder bzw sowie wie etc usw`). SH09 p36 prints »zum B-W- einen USER-Befehl«, and our HTML has it right. The diff showed `B-Weinen` against 8411's `B-R einen`, which reads like an OCR error of ours. The page settled it (O10). The rule says the join is for a broken word; `X- einen` with the hyphen glued to an uppercase token is never one. Cost: one crop. Disproved: the reading that our text is damaged there.
- The record classifier filed `U1` / `Ul` (8411, D-083) as EDITORIAL `rewritten`. A 1/l swap is the most common OCR slip there is, and it reached no reader. The rule says only a CANDIDATE can be a transcription error, so a two-character token that differs by one glyph should be CANDIDATE. I reported it as a side observation and did not change the row, as the brief requires.
**Suggested.** exempt a hyphen glued to an uppercase token (`B-W- einen`) from the end-of-line join, and class a one-glyph difference in a short token (`U1`/`Ul`) as CANDIDATE, not EDITORIAL.

## r005_masters_sheet (the paper-yellowing field: a page stamped NOT APPLIED) — owner report, SH09 p031
The step wrote `NOT APPLIED` into one stamp of 168 (masters600/031.stamp.txt: `field identity -- NOT APPLIED`, `page-class uncropped sheet`, `NOT CROPPED: the trace gave 149.0 x 297.4 mm`) and passed. No verification aggregates the stamps. A page that had silently lost its yellowing correction shipped, and the owner's eye caught it, not a check. Control's sweep: it is the only such stamp in the corpus.
The rule is explicit that a page whose box fails FIELD_PAGE_MM gets the identity stamp. It is silent on what happens next. recover_031.py later repaired p031's bed in a4600 but never the field.
Measured on the delivered page: 99-100 % of the paper in the outer 6 mm of the fore and top edges is tinted, R-B up to +16.1; the class median is 0-1 %.
Why the trace failed: its left edge latched onto the outer boundary of the photo bleeding off the gutter, at 61.2 mm, so the width read 149 mm. The real page box can be measured by hand: 210.2 x 297.8 mm.
Re-graded in scratch with that box and the existing field_low.txt, the fore edge 0-3 mm drops from +14.6/99 % to +1.2/5 % and the top from +16.1/100 % to +0.8/1 %, which is the class median. Numbers in reviewed/colour-030-031.txt.
Cost: an owner report, two measurements and a scratch re-grade, plus whatever fix the owner rules after delivery.
**Suggested.** a gate in r005's Verification that fails while any stamp of the run says `NOT APPLIED` or `NOT CROPPED`, unless a reviewed/ override for that page also supplies a page box and applies the class field on it. The override that fixes the geometry must fix the field in the same step.

## r120 check 5 / r170 (MSE hex): the header's end address is EXCLUSIVE, measured, not to be re-derived
A printed MSE header `Name : <name>  ssss eeee` gives the first address AFTER the program: the file holds eeee − ssss bytes. Confirmed on 14 of 14 printed binaries in SH09 (r120 check 5) and in the corpus on cctm1a (8611, a4c0 a7cc = 780 bytes), hyplatos 2 (8609, 0801 3591 = 11664) and smon teil 4 (8502, cbf1 ce0a = 537). tools/mse.py, the site's own renderer, computes the header end the same way: it renders turbotapecopy mse.prg's 1216 bytes as `C350 C810`, matching the print. SH09's turbotapecopy turned on this: the disk's byte past the printed end ($01 at $C810) is a D64 tail the page never showed, not a row the print lost. The crop agrees: column 3 ends at c808 with clean paper below. Each build re-derived this; it cost a corpus search.
**Suggested.** state it in r120 check 5 and in r170's MSE row: "An MSE header's end address is exclusive (eeee − ssss bytes); a disk file 1-3 bytes longer carries a D64 tail." Also r170's MSE row: "where the disk file has the program's name and is incomplete, write the print-built file as `<name> mse.prg` beside it (SH09 `dos v3 mse.prg`, `turbotapecopy mse.prg`)".

## r005_masters_sheet (the bed drop): it painted print white inside the page and wrote nothing anywhere — owner report, SH09 p030
- The last block of level_and_trace() drops every frame-touching component of `lum < BED_LUM (70) | prop_mask` whose share outside the line-traced page exceeds BED_OUTSIDE_FRAC (0.5). It drops the component WHOLESALE, including the part deep inside the page. process() then writes masters600 as `graded[keep] = sheet600[keep]`, 255 elsewhere. A dark photo that runs off the trim joins the bed beyond it, the bed outweighs it, and the photo goes too. The rule's own comment names the hazard ("a full-bleed PHOTO that runs off the torn edge … p006"); the 0.5 guard assumes the photo outweighs the bed it touches.
- MEASURED, all 168 SH09 pages, read-only with the step's own level_and_trace (reviewed/bed_drop_*.py):
  - p030: 1716.5 mm² inside the page, 2.79 % of it, one component reaching 48.7 mm deep: the 1541 chassis of the lead photo, joined to the bed at the page turn. masters600 = sheets600 in 97.00 % of the page, and every differing pixel is exactly 255. Drive region luminance 154.1 → 219.7.
  - p167: 186.2 mm², reaching 23.7 mm: the olive ground at the foot of the back cover.
  - p168: 15.3 mm², reaching 3.6 mm, PROP branch: a yellow shape at the bleed is read as the yellow prop. It is outside the delivered window, so it did not ship.
  - p031: 2947.7 mm² would have gone, the other half of the same photo. It was discarded only because locate() replaced keep (NOT CROPPED, then regrade_031.py's hand box).
  - Legitimate removals: 45 more components, bed at the trim, deepest 4.45 mm (p017), largest 13.8 mm².
- NOTHING SAID SO. There was no note and no stamp line. The PDF build and the marks census both read the damaged masters600/a4600, and neither looks for a pure-255 patch inside a picture. The owner found it by eye in the PDF. sheets600 and the owner's crops were never affected: they are taken before keep.
- Repaired by override for SH09, reviewed/rebed_030_167.py. The predicate: a doomed component is not dropped if its part inside the line-traced page reaches more than 10 mm from the line box's edge (EDT, 600 dpi). It is per component, because a per-pixel cap would still eat the outer 10 mm of a bleeding photo (p167's median depth is 5.3 mm). The paper-yellowing field anchors are pinned to r005's own keep, so sheets600 stays pixel-identical.
- The eleven other r005 issues (8610 8611 8612 8701 SH8602-SH8608) were NOT swept. Owner 2026-11-14: "just do this issue." The question was asked and deliberately deferred. The instrument is reviewed/bed_drop_dropinst.py (about 37 s and 6 GB per page).
**Suggested.** In r005: "The bed drop removes only components whose part inside the line-traced page reaches no more than 10 mm from its edge (SH09: legitimate ≤ 4.45 mm, defects ≥ 23.7 mm). Any drop that removes more than a few mm² inside the traced page is NOTED in the stamp with its area and depth." In r005's Verification: "Fail when masters600 and sheets600 differ by a pure-255 component of more than N mm² that lies more than 2 mm inside the page box." In r006: "Before shipping, look for pure-255 patches inside the contone areas of a4600."

## r006 (bilevel cutoff): a page soft in the scan is broken by the global 35 % threshold — owner report, SH09 p099; PARKED by the owner
- p099's top-left column is SOFT IN THE SCAN, not in our processing (control's measurements): raw gradient 5.25 against 7.74 in the sharp right column of the same page, and raw stroke-core median luminance 90 against 58. sheets600 and a4600 change it by about 5 levels, so the chain neither caused it nor can undo it.
- The global BILEVEL_THRESHOLD of 35 % = 89 then bisects those strokes. 47.8 % of the ink the master holds fails to ship on the left column, against 23.6 % on the right, where 23.6 % is ordinary antialiased edge and correct. A legible soft scan becomes an illegible broken one.
- Remedies identified and NOT taken: FORCE_CONTONE for the page; a local adaptive threshold for the class; a re-scan, the only thing that recovers real detail. The owner set it aside on 2026-11-14 ("never mind. lets wait for the color fix.").
- What was measured before it was parked, so it is not lost: a glyph-level pass over all 144 bilevel pages (<tmp>/instruments/glyphsweep.py). A glyph is a component of grey < 150 with 40-6000 px and a bbox ≤ 200 px; a BROKEN glyph keeps < 40 % of its pixels at the cutoff. Results:
  - The median page breaks 0.3 % of glyphs in its worst 4x2 cell, p90 4 %.
  - Above that, looked at one crop each: real text damage on p099 (33 % of glyphs in its worst cell) and p125 (an ad caption, 29.5 %); thinned but readable on p078 (typewriter listing, 9.6 %), p110 (hex dump) and p141 (dashes).
  - The other flags (p127, 085, 139, 138, 046, 017, 003, 091, 092) are screened tints and halftone photos dissolving into dots, which is the cutoff's design.
  - Priced, not built: FORCE_CONTONE at q97 costs 0.76-0.96 MB a page against JBIG2's 0.25-0.48 MB. A 50 % per-page threshold reads best on p099 and p078 and is about the JBIG2 size. It is a tooling change, because the JBIG2 cache is keyed on the global value.
  - NOTHING WAS BUILT OR CHANGED for this: no FORCE_CONTONE, no threshold change, no page re-encoded; the shipped PDF is as it was. The extent across the CORPUS is unmeasured.
**Suggested.** In r006: "A bilevel page whose worst column loses more than ~10 % of its glyphs at the cutoff (glyphs keeping < 40 % of their pixels) is not shipped bilevel without a look. The remedies, in order: FORCE_CONTONE for the page, a per-page threshold, a re-scan."
