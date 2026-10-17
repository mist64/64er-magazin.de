# SH8606 — WORKFLOW_ERRATA (third file; follows the harvest f6954f8b)

Reopened 2026-10-17 for one owner change after the issue was closed. One entry.

## 150 — a delivered `-0` is not evidence of the lead slot, and the lead-slot exception keys on that suffix [LIVE]

**What the rule says.** r150, *What is NOT a figure*: a cartoon is omitted
unless the text references it or the print labels it. *EXCEPT IN THE LEAD
SLOT*: a drawing is cropped when it "sits directly under the article's
headline", "is the article's `<page>-0`, i.e. nothing else occupies the lead
slot", and is "set as an opening illustration, not dropped into leftover
space further down". And *A CROP THAT ARRIVES IS PLACED*.

**What I did.** `108-0.png` — a cartoon (boy with spread arms before a
computer, "Deine Manieren lassen ganz schön zu wünschen übrig!" / "Rüülps!"),
no printed caption, never referenced by the prose — had been placed in
f39d844e (2025-10-23) and stood through this build's 150 (which placed the
new delivery and did not re-judge the 62 files already there). It sat at line
223 of 532, between two paragraphs on interrupt handling, i.e. in leftover
space, not under the headline. Owner, 2026-10-17: "cropping SH8606/108-0 was a
mistake, remove file and dont img src it." Removed in this reopen: `git rm`
of the PNG and the whole bare `<figure>` (no figcaption to keep); r150
Verification 1-5 clean at 78 files / 78 references, r310 HARD 0, generate.py
exit 0, no 330 pair for 108.

**What it cost.** One owner correction after closure and a reopen.

**Suggested.** In *EXCEPT IN THE LEAD SLOT*, replace the second bullet "it is
the article's `<page>-0`, i.e. nothing else occupies the lead slot" with:
"nothing else occupies the lead slot — judged from the PAGE, not from the
file name. A `-0` suffix is a claim the cropping tool made, not evidence of
position: SH8606's `108-0` carried it while sitting mid-article at line 223 of
532. Check the master: the drawing must be under the headline and above the
intro or first body paragraph." And in *A CROP THAT ARRIVES IS PLACED*, add:
"This governs the delivery of the current build. Crops already in the
directory from an earlier hand are re-judged against this section at 150
(one `ls` plus the placed line number per `-0`/`-00` file is enough); an old
`-0` sitting mid-article is the leftover-space case and goes to the owner as a
candidate for removal, with its position as the evidence."
