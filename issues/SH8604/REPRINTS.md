# SH8604 — reprint leads

The Adventure-Sonderheft reprints the two house input aids that had already run
in the monthlies. This list is a set of **leads, not findings**: each one comes
from a measurement, and has to be confirmed against both printed pages (r330
step 1) before anything is diffed.

## How the leads were found

Not carried over from anything. Measured twice on this issue's own built
articles:

- step 140: per-block 6-word-shingle overlap of each article against all 1970
  corpus articles (`LOG.md`, step 140). It wrote `reprints.txt`, which names
  the same two originals by `<issue>/<64er.id>` (`8603/checksummer`,
  `8602/mse`); this file names them by start page, the key r330's `resolve`
  takes. Both read the same record.
- step 330, 2026-10-05: the share of each SH8604 article's 8-word sequences
  (prose only, `<pre>`/`<code>` removed, lower-cased, machine names closed up)
  that also occur in a published article anywhere in `issues/`; and, per
  block, every corpus article sharing at least half of that block's 8-word
  sequences. It found the same two leads and nothing else.

The number is a hint, not a verdict.

## Leads

| SH8604 article | claimed original | evidence (overlap) |
|---|---|---|
| Checksummer 64 V3 | 8603/55 | 0.91 (`8603/55 Checksummer 64 V3`, 12 blocks). Also SH8602/6 0.96, SH8507/6 0.81, SH8603/76 0.72: the same house text, reprinted throughout; SH8602/6 is itself a reprint of 8603/55, and 8603/55 is the latest monthly printing before this issue |
| MSE - Abtippen sicher und leicht gemacht | 8602/57 | 0.93 (`8602/57 MSE - Abtippen sicher und leicht gemacht`, 11 blocks). Also SH8602/7 0.95 (itself a reprint of 8602/57), SH8505/8 and SH8506/18 0.87, 8508/54 (10 blocks) |

## Not leads

- `162 Impressum` — 0.83 to SH8603's Impressum (and 0.73–0.74 to every other
  Sonderheft's): the shared masthead, not a reprint.
- `3 Warum Adventure_` — 0.03–0.05 to the other Sonderhefte' editorials
  (one house phrase per block). Not the same text.
- `111 Der kleine Hobbit` — 0.03 to 8607/84 Fehlerteufelchen: a later erratum
  quoting this issue (rule 300's business), not an original.
- `119`, `161`, `81` — 0.00–0.02 to SH8502 adventure articles: shared phrases
  only. Every other article: no 8-word sequence in the corpus.
