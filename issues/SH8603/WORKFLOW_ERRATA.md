# SH8603 — workflow errata

Kept from the first confusion onward (r340). Harvested at the end, not during.

## 005 — the paper pre-fill proposes 1 of the 8 high-stock pages

**What the rule says.** r005_masters_sheet.md, *What the step offers as
evidence*: "The step pre-fills `high_pages` with what the edge-finder evidence
points at and says, in the output, that it is a guess to be checked against
the copy."

**What happened.** The pre-fill was `[1]`. The step's own evidence list (b)
then put 179, 002, 180, 181–184 at 59–122 city-block from the interior p50,
with a gap to the next page (p071, 21), and those seven plus 001 are exactly
the 2400 dpi pages, i.e. the wrapper and the card. SH8602 met the same case
(its LOG: "the paper mask sees 0.11–0.52 of these frames as interior paper").

**What is true.** The edge finder is one-sided (the rule says so); the
own-white gap is the stronger signal on these two Sonderhefte, and the scan
dpi split is a free third witness. No cost here beyond a montage (≈2 min);
the risk is an operator pasting `[1]` back unread.

**Suggested.** Pre-fill from the union of the edge-finder set and the pages
past the own-white gap, and print the per-page scan dpi beside each.

## 005 — "measure K on the darkest solid black" gives no procedure, and the obvious one measures the bed

**What the rule says.** r005_masters_spread.md, *EXCEPT K*: "when measuring
`W`, also take the darkest solid black across the interior and move the `K`
anchor to it if it sits below the built-in." The `W` measurement beside it is
a runnable snippet; this one is a sentence. (The sheet rule does not mention K
at all; the pointer came in a relay from control.)

**What I did.** Reused the W snippet's body box (10–90 % × 3–97 %) with
"lum < 70, low chroma, eroded". Every one of 176 pages reported ~40 000 solid
black px at 31 27 27: on a SHEET-variant thumb the frame holds the near-black
bed around the sheet, and a fixed fractional box does not exclude it. The bed
(raw ~21–40) is in the same range as printed black, so the answer looked
plausible.

**What is true.** Restricting to the sheet's own paper bbox (rows/cols > 30 %
paper, 2.5 mm inset) and looking at the mask on p073 put it on the printed
banner bars: p50 30 27 27, above K 16 17 17. Same number by luck — the bed and
this issue's black read alike — but on an issue with a darker black the first
method would have reported the bed. Cost ~5 min, 3 commands.

**Suggested.** A snippet for K next to the W one, cropping to the sheet (not a
frame fraction) for a sheet-variant thumb, and saying "look at the mask on the
darkest page" as part of it. Put the requirement in r005_masters_sheet.md too.

## 005 — the sheet Verification still names `figures600` (SH8602 found it; not harvested)

**What the rule says.** r005_masters_sheet.md Outputs and Verification 1, 4, 6
read `R.OUT_FIGURE` / `figures600`. **What is true.** Unchanged since SH8602's
entry: the code writes no `figures600` and has no `OUT_FIGURE`; checks 1, 4
and 6 die on `AttributeError` pasted verbatim. SH8602's errata (deleted in
56b7e343) had this as "005 — the sheet Verification names an output the code
no longer writes", plus check 4's printed-footer false positive (166/168
there, 165/184 here). Neither landed in r005_masters_sheet.md or HARVEST.md.
**What I did.** Same adaptation as SH8602: checks run on `masters600`/
`sheets600`, the footer band read as print. Cost ~5 min.
**Suggested.** Check the harvest of SH8602's 005 entries; it looks as if they
were dropped.
