# SH8601 — reprint leads

The Sonderheft reprints articles that had already run in the monthlies. This
list is a set of **leads, not findings**: it was carried over from the earlier
PDF-OCR `SH8601.md` (deleted 2026-08-21, commit history has it), which is not
trusted for anything. Every entry has to be re-confirmed against the printed
page once the scan chain has produced this issue's own corpus.

## Why we keep it

A reprint is **built like every other article** — OCR'd from the scan, split,
placed, published. Nothing is copied over from the monthly's HTML.

The value is downstream: after the issue is built, each reprint gets **compared
against its already-published monthly**. Two independent transcriptions of the
same printed text disagree exactly where one of them mis-transcribed, so the
diff is a transcription-error finder for both sides.

**The two versions do not have to be identical.** The magazine re-set and
re-edited reprints — different standfirst, cut paragraphs, corrected or newly
introduced typos. Those are real differences and both sides keep what they
print. **Errors that are in the magazine STAY.** The comparison finds *our*
errors, never the magazine's.

## Leads

| SH8601 article | claimed original | evidence quoted by the old analysis |
|---|---|---|
| Rundgang durch die Hardware des C128 | 8506/16 + 8507/17 | MMU, Configuration Register, "bis zu 32 KByte ROM eingeblendet" |
| Der C128D im ersten Test | 8601/43 | "professionellen PC-Look", "Spitznamen…Diesel" |
| Ein Monitor ist genug | 8510/16 | "Kaum hatten wir die ersten C128" |
| 80-Zeichen-Grafik für den C128 | 8512/78 | identical, and the text itself says "Ausgabe 12/85" |
| Test: WordStar | 8601/47 | "WSPAR.COM…Centronics-Schnittstelle über den User-Port" |
| Turbo-Pascal auf dem C128 | 8511/30 | "PACKED wird vom Turbo-Pascal Compiler ohne Murren" |
| ~~Basic 7.0 – das starke Basic~~ **Das ist der C 128** | 8506/16 + 8507/17 | "DATA-Orgien und wüster GOTO-Dschungel" — **the quoted sentence is in *Das ist der C 128*, not in the Basic 7.0 article.** SETTLED 2026-08-23: *Das ist der C 128* IS the reprint; *Basic 7.0 – das starke Basic* is not a reprint at all |

The deleted file also carried `TODO Wiederholung` markers in place of the body
text of the first five of these — i.e. those articles were never transcribed at
all in that file. One more reason it is worth nothing.

## Claimed original content

Listed by the same analysis as *not* reprints, and equally unverified:

Vorwort · Welche Floppy für den C128? (near 8601/44 in topic, different text) ·
Rushhour für CP/M auf dem 1541-Laufwerk · Kein Bild ohne Monitor · Kabelsalat ·
Sprites und Shapes auf dem C128 · Apfelmännchen (references 8511/80, new text) ·
Roulette C128 · CP/M auf dem C128 · Multiplan · dBase II · Der etwas andere C64 ·
Das ist der Commodore 128 · Basic 7.0 – Programme strukturiert · Software für den
C128 · Der C128 am Telefon · Der Basic-Interpreter des C128 · Tips & Tricks zum
C128 · C128 um 35% schneller · Rätselfreunde aufgepaßt!

## Resolution status, checked 2026-08-21

Every claimed source monthly is published in this repo, so the comparison has
something to compare against. Resolving each lead by page number:

| lead | resolves to | note |
|---|---|---|
| 8506/16 + 8507/17 | *Erster ausführlicher Test PC 128 (Teil 1)* / *… C 128, Teil 2* | a two-part C128 test; the Sonderheft's *Rundgang durch die Hardware des C128* would be drawn from both, retitled |
| 8601/43 | *Der C128 D im ersten Test* | title matches |
| 8510/16 | *Ein Monitor ist genug* | title matches exactly |
| 8512/78 | *80-Zeichen-Grafik für den C 128* | title matches |
| 8601/47 | *Gestatten: Wordstar* | retitled to *Test: WordStar* here, plausible |
| 8511/30 | *Turbo-Pascal auf dem C 128* | title matches |
| 8506/16 → *Basic 7.0 – das starke Basic* | **SETTLED: the lead named the wrong Sonderheft article** | 8506/16 is the C128 test, and 8506 carries no Basic 7.0 article (its only Basic piece is *Macro-Basic* on p137). The evidence sentence sits in *Das ist der C 128*, which IS the reprint of the two-part test. *Basic 7.0 – das starke Basic* is a Basic 7.0 command reference by a different author and is not a reprint |

The last row is the reason these are leads and not findings: **confirm every one
against the printed page before diffing**, and be ready to conclude that an
article is not a reprint at all.


## Settled 2026-08-23 — *Das ist der C 128* (pp 96-97, 100-109)

**CONFIRMED reprint of 8506/16 and 8507/17**, the two-part monthly test, re-set
for the Sonderheft. `REPRINTS.md` had it as *not* a reprint while crediting its
evidence sentence to the *Basic 7.0* article.

What settled it, and why the naive measure said otherwise: only ~9% of the
words are byte-identical across the two printings, which reads like a rewrite —
but the aligned blocks are the SAME TEXT differing by one systematic
substitution. **The monthly says `PC 128`; the Sonderheft says `C 128`,** the
machine having been renamed between the two printings, and that token appears in
nearly every paragraph. Figure and table numbers are renumbered with it
(`Tabelle 1` → `Tabelle 3`), and the prose carries light editorial polish
(`verursachte` → `verursacht hat`, `Abspeichern` → `Speichern`, `Programms` →
`Programmes`).

Measured: 256 of 549 blocks align; 11 of the 18 `<h2>` headings appear verbatim
in 8506/16 and 3 more in 8507/17 — 14 of 18.

**A systematic rename defeats a similarity score.** Where two printings of one
text disagree on a product name, word-identity understates the overlap badly;
read the aligned blocks before concluding a rewrite.
