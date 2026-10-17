# SH8608 — WORKFLOW_ERRATA (third file; follows the harvest f6954f8b)

Reopened 2026-10-17 for one owner change after the issue was closed. One entry.

## 080 / 150 — a headline prefix set as reversed type on a tint band is lost at OCR, and nothing downstream looks for it [LIVE]

**What happened.** p94 prints, between the lead drawing and the headline, a
grey band with "Text-Manager" in white display type, and under it the black
headline "Briefe schreiben leichtgemacht". OCR's heading block 16
(`blocks/p094.txt`) reads only `Briefe schreiben leichigemacht`; no block on
the page reads the band. The crop `94-0.png` ends at the drawing's frame and
does not include the band either. So the prefix existed nowhere in the
edition. Owner caught it; fixed under r260 to
`Text-Manager – Briefe schreiben leichtgemacht` (control's ruling: a dash for a
program name, en dash per this issue's own `Cave – Sternenkampf im
Labyrinth`): h1, `<title>`, `git mv` of the file. `toc_entries.txt` already
reads `Text-Manager` — it records the printed Inhaltsverzeichnis, a different
artefact — and `toc.txt` lists categories only, so neither changed. r220: 40/40
applied, 0 misroutes, orphan rows = the one already reviewed (p157); the
existing `index_title` ("Briefe schreiben leicht gemacht") still differs from
`<title>` and stays. r260 Verification clean, r310 HARD 0, generate.py exit 0.
No 330 pair for 94.

**What would NOT have caught it — measured.** "`toc_title` not contained in
the `<h1>`" was the obvious detector. Before this fix it flagged 4 of SH8608's
5 articles that carry a `toc_title` (94, 79, 129, 132) and 12 of SH8606's 19.
I looked at the three SH8606 hits that have exactly 94's TOC shape, "Name –
headline" with the headline as `<h1>`: 122 (`ROM 80 – …`), 134
(`Charset-Master – …`), 155 (`Super-Hardcopy – …`). None prints a prefix; on
each page the `<h1>` is the whole headline and the TOC simply names the piece
differently. So, one true hit in 16, and r080 already records the same verdict
for the converse substring test. Do not build it.

**What cost it.** Reversed type (white on black or on a tint) is exactly what
the OCR does not read, and the band sat in the gap between the two things the
chain does look at: the lead crop above it and the heading block below it.
r080's *look at the opening picture* covers display type INSIDE a photograph,
and is gated on "the headline did not come from the page's own text"; here it
did, so that check never fired.

**Suggested.** In r080, at the point where the `<h1>` is decided, drop the gate
and widen the look: "Look at the page from the top of the lead image to the
first body line, not only at the heading block. A kicker or program-name prefix
is often set as reversed type on a black or tinted band (SH8608/94
`Text-Manager` over `Briefe schreiben leichtgemacht`), and OCR returns no block
for it. If one is there, it is part of the headline: a standing rubric joins
with a colon, a program or product name with a dash, en or em per the issue's
own existing titles." And in r150, where a lead crop's bounds are judged: a
crop that stops just above a band of display type is a reason to check that the
band's words are in the `<h1>`.
