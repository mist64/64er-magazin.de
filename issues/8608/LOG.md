# 8608 — Placement log (rule 10: place figures)

## Unplaced disk-infrastructure files (no article home)

The following three files sit on disk 8608A.D64 *before* the first
per-article separator (`--------------53`). They are disk boot / entry
/ checksum / MSE tooling that belongs to no single article. Per the
orchestrator's user-confirmed decision they are **not placed** into any
article HTML and remain listed in `prg.txt`:

- `leser-info!` — disk boot/reader-info screen (auto-run banner of the
  Programm-Service-Diskette), not an article listing.
- `checksummer` — the 64'er Checksummer V3.0 typing-aid utility, used to
  enter the BASIC listings; a general disk utility, not article-bound.
- `mse.prg` — the MSE (Maschinensprache-Editor) hex-entry utility used to
  type in the MSE listings; general disk tooling, not article-bound.

These are left in `issues/8608/prg/` (and `prg/del/`) and referenced in
`issues/8608/prg.txt` only.
