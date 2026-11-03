# WORKFLOW_ERRATA — 8701

## 000 — the preflight's per-page budget is ~2.6x what a monthly measures (LIVE)

**What the rule says.** r000 *PREFLIGHT the free space*: "For a **2400 dpi** page it is
~**2.25 GB** — `masters2400/NNN.png` plus `cmyk2400/NNN.tif` — so a 200-page monthly is
**~450 GB**", and the BUDGET snippet hard-codes `per = {2400: 2.25, ...}  # GB per page, measured`.

**What I did.** Ran the arithmetic: 192 x 2.25 = 432 GB, which fits on neither volume
(~/DNB 118 GB free, /Volumes/S 384 GB). Read as written, 8701 cannot be built without
streaming the archive off or skipping it.

**What is actually true.** The last monthly's own <tmp> is the measurement: 8612 (200 pp,
spread, 2400 dpi) = 174 GB for the WHOLE working set, masters2400 60 GB + cmyk2400 93 GB,
~0.87 GB/page all-in; 8612's LOG measured 0.62 GB/page for the archive on its 25 gate pages.
So 8701 needs ~167 GB and fits on /Volumes/S. The 2.25 figure is ~2.6x high.

**Cost.** ~5 min and 3 commands (du over 8612/SH8607/SH8608 tmp) to avoid a false
"does not fit" and a needless stream-off/skip decision.

**Suggested.** Replace the constant with the measured one and keep the gate measurement:
"A 2400 dpi monthly page costs ~0.85 GB all-in (8612: 174 GB / 200 pp, of which archive
0.77); a Sonderheft page ~0.35 (SH8607: 65 GB / 184). `per = {2400: 0.9, 600: 0.06}`."

## 000 — two sections still say binding/paper are ASKED, after the 2026-11-02 ruling (LIVE)

**What the rule says.** *THE CHAIN'S FIRST ACTION — ask which binding, and which pages are
which paper*: "**the operator is asked two questions about the physical copy.** They are the
first thing that happens", and under PAUSE 1 for spread: "So ask the owner only to CONFIRM
that, not to choose." Earlier in the same file, *BINDING IS DERIVED FROM THE SCAN, NOT ASKED*
and *WHAT THE OWNER IS ASKED FOR* (2026-11-02): binding and paper are decided by the build.

**What I did.** Read both; followed the newer sections (derive binding from the 96/97
centre spread, paper = one interior profile per the spread variant) and asked nobody.

**Suggested.** Retitle the old section "THE CHAIN'S FIRST ACTION — derive binding and paper"
and change "ask the owner only to CONFIRM that" to "record it in LOG.md; it is not a question".

## 005 — the spread variant assumes the yellow prop; 8701 was scanned on a BLACK bed (LIVE)

**What the rule says.** r005_masters_spread *What the paper actually is*: "bottom | the yellow
prop | (250, 218, 113), ~40 px at 150 dpi = ~7 mm deep", and for a full-bleed page "the bottom
is the **prop's top boundary**, which `prop_mask` sees on any page whatever its ink";
"Fewer than 24 columns seeing the prop leaves the bottom at the frame's last row."

**What I found.** Median foot colour of the found thumbs at p050: 8610 `248 215 112`, 8611
`248 215 112`, 8612 `249 216 113`, **8701 `34 34 36`**. On 8701's derived thumbs the foot is a
near-black band 6.1-7.8 mm deep on every page measured (010 011 050 096 097 150), RGB ~33 34 35.
`prop_mask` (G-B > 50, mean > 120) cannot see it, so `prop_top()` returns None and every page that
takes the full-bleed bottom (covers, ads with ink to the trim, and every edges-anchored page
without a wordmark) gets its bottom at the frame's last row: window ~7 mm low, black bed inside
the master. Pages with paper at the foot still trace (the paper mask sees black as non-paper).

**Cost.** ~10 min, 4 commands. Caught BEFORE the sample sweep.

**Suggested.** "The foot under the sheet is the scan setup's, not a constant: the prop
(yellow, 8610-8612) or the black bed (8701). Measure it on the thumbs before 005 (median of the
bottom 25 thumb rows) and say which in LOG.md; `prop_top()` reads whichever the descriptor names."

## 005 — skew on a dark full-bleed page reads the bed, not the sheet (p051)
The coarse skew measure read −3.06° on p051, a level U.S. Gold ad: both the sheet and the art are level in the raw scan. The master came out rotated 3°, with bed and a yellow wedge at the foot. Verification check 3b does list the page, but ruling 14 only covers art printed tilted. A false skew on a level page is a separate class, and it has no check of its own.

## 005 — when the backing_top gate falls back to the frame row, the bed is kept (p178)
On p178 the gate correctly read the 14.6 mm line as ink, a photo running to the trim. It then used the frame row, which lies below the paper's real foot, so about 7 mm of black bed is now part of the master. Check 6 lists the page (dark 0.486) among the full-bleed ink pages, where it cannot be told apart from them. The only thing that showed it was looking at the page.

## 030 — the "von" side of a jump is read only from the classified stream
continuation_links() reads "Fortsetzung auf Seite N" from all blocks, which fixed the p127 class. The matching "Fortsetzung von Seite N" is still detected only in the stream. On 8701, step 020 labelled all four von markers `other` (p078, p099 ×2, p187). Three of five jumps were then left unjoined. No "has no article to rejoin" WARNING was printed, because no continuation segment was ever made. The verification's loss count is 0, because nothing was lost: it was attached to the wrong article.

## 050 — `<!` is not browser-safe
r050 leaves every `<` followed by a non-letter alone as safe. `<!` is the exception: the HTML5 tokenizer opens a markup declaration on it, so `<!>` renders as an empty bogus comment and the `!` disappears. 8701 prints `<!>` five times (Master-Text, the "Ausrufungszeichen-Funktion"); fixed by hand to `&lt;!&gt;`. The verification cannot see it either, because it applies the same "non-letter is safe" test.

## 120 — check 4 asserts on a mismatch the rule's own table says to leave
On 8701, `tabel. for-next` and `testbild 64` differ from the disk only inside REMs: Simons Basic token pairs `$64 xx` that re-tokenise as plain letters. r120's table gives a REM-only difference no action (SH8607 gap 3 is the same case). The verification still ends with `AssertionError: 2 listing(s) no longer re-tokenise`, so a correct build exits non-zero. The check should classify REM-only differences and pass them, naming them.

## 230 — the Verification block exits 0 even when it prints FAIL
On a copy with planted faults (TODO FORMULA, bare \frac, an unclosed \( and \[) every check printed its FAIL line, and the block still ended with exit 0. A caller that trusts the exit status passes a broken issue.

## 250 — check 1 fails on a formula block that starts with "Adresse"
8701 p74: `<p>Adresse von Punkt X,Y : INT(X/8) +Y*80<br>Bitnummer : …</p>` is a formula display in mid-prose. Check 1's "no digit in the label tail" exclusion misses it because "von Punkt X,Y " has no digit, so the Verification exits 1 on a correct issue for good. It is the same class as SH8603's "Adresse 43-56:".

## 240 — three checks that cannot pass on a correct issue
(a) The Editorial NOTE "banner not wrapped in <figure>" fires on the `<img class="inline">` shape the rule prescribes. (b) An article whose print has no banner (8701's Bücher, p144) gets a FAIL and a WARN with no N/A path. (c) The block assumes bash globbing; zsh prints "no matches found".

## 260 — the caps check counts letters inside HTML entities
"C 16 &amp; PLUS/4" (8701 p186) counts the a, m and p of `&amp;` as lowercase, reads 62 % upper and is never reported. Any caps heading with a named entity escapes the scan and the Verification alike. Fix: html.unescape() before counting.

## 270 — check 1 prints FAIL and exits 0
A planted `<a href>` printed "FAIL: <a href> left", and the block exited 0. Check 1 never sets rc=1, which is the same defect the block's own comment already fixes for check 2.

## 300 — the trailer check counts `<pre` as a paragraph
"2 corrections, 1 trailer -- same issue for all?" fires on every aside that holds a `<pre>` listing, because the `<p` pattern also matches `<pre`. The same `<p[^>]*>` trap r000 already records. And the status-comment FAIL on 8609/156 (Vizawrite) fires on a binary listing, which the rule itself says has no `;` header and is recorded in LOG.md instead.

## 230–300 — checks that print FAIL and exit 0, or fail on correct output (collected, per check)
| rule | check | on a fault | on a correct issue |
|---|---|---|---|
| 230 | the whole Verification block | prints FAIL (TODO FORMULA, bare \frac, unclosed \( and \[) and **exits 0** | exits 0 |
| 240 | Editorial "banner not wrapped in <figure>" | — | **NOTE fires** on the <img class="inline"> shape the rule prescribes |
| 240 | banner present / referenced | FAIL | **FAIL + WARN** where the print has no banner (8701 Bücher p144): no N/A path |
| 240 | Fachredakteur glob | — | zsh prints "no matches found" (the block assumes bash) |
| 250 | check 1, label-word <p> not tagged | WARN, exit 1 | **exit 1 for good** on 74's formula block "Adresse von Punkt X,Y : INT(X/8)…" |
| 260 | ALL CAPS heading | FAIL printed, **exit 0**; and a caps heading with an entity (`C 16 &amp; PLUS/4`) is never reported, because the a/m/p of &amp; count as lowercase | exits 0 |
| 270 | check 1, `<a href>` left | prints FAIL, **exit 0** (rc never set) | exits 0 |
| 300 | trailer count | — | **"look" fires** on every aside holding a <pre>, because `<p` also matches `<pre` |
| 300 | status-comment FAIL | — | **FAIL** on 8609/156 (a binary listing with no `;` header, which the rule itself sends to LOG.md) |
| 120 | check 4 (fixed by control) | — | asserted on REM-only round-trip differences |

## For the 8702 build
8702's Fehlerteufelchen corrects 8701 "Grafik für Hypra-Basic", p84. It is already in Fehlerteufelchen.md under "Ausgabe 2/87"; r300 applies it to issues/8701/83 Grafik für Hypra-Basic.html when 8702 is built.

## 320 — the coverage tool lags its rule on two sweeps
The rule says hand-typed listings are checked like prose and that noise/other blocks are swept for lost prose. `r320_coverage_check.py` skips every `listing-*` block and does not sweep noise/other, so on 8701 both were done by hand (/tmp/64er_8701_320/noise_sweep.py, listing_sweep.py, hand_lines.py). Its exit 0 therefore covers less than the rule claims.

## 330 — the rule recommends `diff --range`, and the tool has none
For a PARTIAL reprint (8701's Leserforum reprints eight quoted questions out of six earlier letters pages), r330 says to restrict the diff to the reprinted blocks. `r330_reprint_compare.py` has no range option, so each of the six pairs was diffed whole-article (~200 differences each, almost all PRINT) and the reprinted blocks were word-diffed by hand. The D- disposition lines live only in the git-ignored LOG.md.

## Futureteufelchen — six candidates CONSIDERED AND DECLINED by the owner, 2026-11-02
Owner, verbatim: "futureteufelchen: none of the suggested ones". 8701 ships with no Futureteufelchen, and every page below stays as printed. This list is kept so a later build does not raise the same ones again. (The full draft with verbatim quotes and the asides that were put up: <tmp>/FUTURETEUFELCHEN.md, crops in <tmp>/ft_crops/.)
Declined (each: page says → true; ground):
1. p24 Profis Q24, "Kassettenpuffer von Speicherstelle 631 bis 640" → 828–1019 (631–640 is the keyboard buffer); the C 64 memory map.
2. p27 Schleifen, line 50 printed run into line 40 (`…"TITEL"50 PRINT A$`) → a line of its own; line 30's GOTO 50.
3. p94/99 Master-Text, "Zeile 1010"/"Zeile 1020" → Listing 2 has lines 10–70 (input 50, question 60). "16 Zeichen" is correct.
4. p144 Die Axt im Haus, "Timerbaustein U20 (566)" → 556 (NE556); the C 64 board, and this issue's p15.
5. p74 C 128 tips, `WINDOW 0,0,29,24` (VDC in 40-character mode) → 0,0,39,24.
6. p79 C 16 tips, BEEPER commentary "LDA $F11" → $FF11; the disk DATA AD 11 FF.
Dropped earlier by the r300 test (internal slips, or the article's own advice covers it): p176 "40 Gewinner" with 31 printed; p74 7182/7183; p155 12 vs 9 Zeichen/s; p154 "Zeichen/Minute"; p152 "%1000 000" and "%0110 oder dezimal 134"; p82 DS$ pointer byte order; p74 colour RAM "$D800 bis $DFE8" (runs into CIA 1/2, but the article says POKEing it "hat nicht die gewünschte Wirkung" and gives SYS $6B17).
Lesson (control, now in r300): a Futureteufelchen records OUR repair or OUR divergence. "The magazine was wrong" alone is almost never ours to say, however actionable it looks. Print errors stay as printed (owner 2026-10-08).

## 340 — sign-off (2026-11-03): the issue is complete; ready for harvest
**Span.** The file was opened at 3c63825c (step 060, 2026-11-02) and was never harvested and reopened mid-build, so it covers 000 through 330 and the post-PAUSE-2 placement in one span. Check 2 passes on its own history.
**Entries, by r340's three categories:**
- LIVE (written within minutes of the confusion): 000 ×2, 005 ×3, 030, 050, 120, 230, 240, 250, 260, 270, 300, 320, 330.
- SAME SESSION: "230–300 collected", which consolidated the per-check rows at control's request hours later; "For the 8702 build"; "Futureteufelchen declined".
- LATER: none.
**Suggested fixes (check 4 counts 15 without one).** None of those 15 needs a proposal any more: control already landed each fix in the rules during this build. d79af746 has the 8701 harvest (005 skew guard / foot fit / narrow leaf / six-punch fill; 030 marker; 050 Pass 3; r100 ADS fold; r120 REM-only; r200 author meta; r300 "ours only"); 127a19ab has the r240 adjudicated banners and shape skip; 408ae936 has r330 --partial. The fix for each entry is therefore the commit, not a sentence here. Still open with control:
  - r330 --partial must never be the only read (a moved block is hidden), and the rule must say the whole-article numbering is of record;
  - r005 BED_RUN_LOOK_MM floor (2.0 mm missed p028/p103/p147).
**A rule that saved me:** r330's "remap by CONTENT, never by offset" twice turned a failing verify (after the THEIRS application, and after step 150's banner) into a clean one-for-one remap instead of a renumbering guess. r150's "an undelivered row is an answer" kept six declined crops from being typeset over the owner's decision.
