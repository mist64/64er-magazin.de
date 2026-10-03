# SH8602 — reprint leads

The Tips & Tricks Sonderheft reprints articles that had already run in the
monthlies. This list is a set of **leads, not findings**: each one comes from a
measurement, and has to be confirmed against both printed pages (r330 step 1)
before anything is diffed.

## How the leads were found

Not carried over from anything. Measured 2026-10-04 on this issue's own built
articles: the share of each SH8602 article's 8-word sequences (prose only,
`<pre>` removed, lower-cased) that also occur in a published article anywhere
in `issues/`. Every article with a match of 0.05 or more is listed below;
everything else scored nothing. The number is a hint, not a verdict — a
heavily re-edited reprint scores low, and a shared masthead scores high.

## Leads

| SH8602 article | claimed original | evidence (overlap) |
|---|---|---|
| Checksummer 64 V3 | 8603/55 | 0.92 (also SH8507/6 0.79, SH8503/6 0.71 — the same tool, reprinted throughout) |
| MSE - Abtippen sicher und leicht gemacht | 8602/57 | 0.96 (also SH8506/18, SH8505/8 0.91) |
| Alle Tasten-, Zeichen- und Steuercodes | 8404/114 + 8405/104 + 8407/148 | 0.20 / 0.22 / 0.19 — a multi-part series merged into one article |
| Synthetische Steuerzeichen | 8406/114 + 8407/136 | 0.48 / 0.28 — two parts merged |
| So macht man Programme schneller | 8410/54 + 8412/44 | 0.55 / 0.22 — two parts merged |
| Debugging - Fehlersuche in Basic-Programmen | 8407/46 | 0.83 |
| Ordnung ist das halbe Leben | 8505/77 | 0.74 |
| POKEs, die Sie kennen sollten | 8410/91 | 0.41 |
| Die besten Tips und Tricks | SH8501/94, 8412/85, 8506/80 | 0.14 / 0.13 / 0.08 — individual tips, probably collected from several issues |

## Not leads

- Impressum — 0.89 to SH8601's Impressum: the shared masthead, not a reprint.
- Directory dreispaltig gedruckt — 0.13 to 8609/61 Fehlerteufelchen: that
  erratum quotes this article's line 420.
- Das Salz in der Suppe — 0.05 to SH8601's Vorwort: house phrases.
