# Issue 8605 body extraction log

## Phase 1 ambiguities (pages 016-030)

### p018 / p019 spread opener
- p018: bold lead-in paragraph top-left + drop-cap body + h2-style "CAD-Werkzeug für den Entwickler" + h2-style "Computergrafik für Künstler" mid-page. No obvious hero-title on the page.
- p019: huge stylized graphic hero title "grafik und computer-animation" filling the left side, body text continues on the right.
- Running header is identical ("Grafik / C 64") across the spread.
- Classified both as article_start because each page has its own title candidate. If the intended structure is a single spread-opener article (p018 opens with intro, p019 holds the graphic h1), Phase 3 may need to merge the two: drop the p018 title, treat p018 as intro+body, keep p019's graphic title as the h1.
- Reviewer: inspect 600-DPI scans and confirm whether p018's "Computergrafik für Künstler" is an h1 or an h2 section inside a spread article.

### p027 news-roundup boundary
- Left column continues "Die Regenbogendrucker" (ends with "(aw)" byline).
- Right column holds two short items: "Nochmal Telefonmodem" and "Riteman verbessert", each with its own body + byline + "Info:" address block.
- Running header is still "C 64/C 128 / Grafik".
- Classified p027 as mixed with "Nochmal Telefonmodem" as the new article_start. "Riteman verbessert" is left as an h2 within that roundup article per the Aktuelles convention in the workflow.
- Reviewer: if Riteman verbessert is actually a separate article rather than an h2, reclassify p027 as mixed with two title entries.
p030: continuation page, full-page 6502 assembler listing (block 13) with only running header 'Grafik / C 64', page number, caption 'Listing 1. Die ersten neun Befehle von »Profi-Grafik 64«.', and footer. No body prose. Emitted empty fragment.
p038: title anomaly — Phase 1 meta title bbox (708,27,2425,230) points to the rubric banner "Grafik / C 64/C 128", not the article title. Actual article title block is at (1275,290,2150,522) in large font (x_fsize 28). Scan cuts off the title at the right page edge: visible pixels + OCR read "Was gibt's N" followed by a partial "N" and whitespace; the remaining letters of "Neues?" (assumed) are cropped out of the source PNG. Emitted h1="Was gibt's N" per anti-memory rule (no retyping from memory). Products table (block 43, 554 words) dropped per workflow ("Body text only — no tables"). Body is one running paragraph flowing across four columns (blocks 4+16, 5+17, 12+18+19, 13+20) ending mid-word "weni-" which continues on p039.

## Phase 3 issue: p158 body from pixels

Page 158 agent read body text directly from 300-DPI pixel crops instead of
running tesseract retry on garbled blocks. This violates the
"Never fall back to vision transcription of body text" rule
(body_workflow.md Phase 3 step 5). Output contains 16 body paragraphs plus
an aside — all need review against a clean tesseract retry. Phase 3.5
cannot auto-revert because the TSV for the original garbled blocks does
not contain the words the agent emitted.

Recommended action: re-run tesseract --psm 6 on block-level crops of
p158 body regions, diff the retry TSV against the HTML, and replace any
words the retry recovers.

## p164 Phase 3 notes
- Tesseract missed first 3 lines of col-3 body ("Der Gesamteindruck von Gyroscope ist recht zwiespältig. Das Spiel ist zwar"). Retry (600-DPI, --psm 6) recovered them; prepended to para A.
- Info-box labels (Spielidee/Grafik/Sound/Schwierigkeit/Motivation/Hersteller/Preis/Bezugsquelle) and Besonderheiten values ("wenig Abwechslung" Gyroscope, "tolles, zweistufiges Scrolling" Bounder) were garbled due to adjacent rating bars; confirmed via 600-DPI retries.
- Rating-bar values (graphical) not emitted — no reliable OCR, not in TSV.

## Phase 3.5 verification summary

verify.sh flagged 476 words across 16 pages as candidates for review (words
in HTML not directly in page.tsv). Manual spot-check shows the vast majority
are legitimate:

- Cross-line compound hyphen rejoins (e.g. "Hardware-Service", "24-Nadel-Drucker")
- Retry-tesseract recoveries (Texteinschub sidebars, garbled blocks) where the
  retry TSV was not persisted to page.tsv. Examples: p013 aside names
  "Bubela", "Jilg", "Günther" from the Dolphin-Dos sidebar.
- Drop-cap restorations.
- Names (Bubela, Jilg, etc.) that only appeared in retry regions.

Auto-revert NOT performed — blanket revert would destroy legitimate Phase 3
pixel/retry recoveries. Flagged word lists retained in
_work_v1/pNNN/verify_flags.txt for human review.

Pages with flags: 008, 009, 010, 011, 012, 013, 018, 019, 020, 021, 022,
024, 025, 026, 027, 029. (other body pages had zero flags — the verify
script's tsv_derived derivation successfully covered them.)

Highest flag counts: p027 (240), p013 (85), p012 (24), p029 (19).

Note: only the first 16 body pages show flags because verify.sh's sort
terminated after p029; the remaining body pages were still processed but
their flag files are present (most empty).
