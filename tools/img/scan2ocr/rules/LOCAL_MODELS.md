# Can this chain run with no online model?

Measured 2026-10-01 on **mimac** (M3 Ultra, 512 GB, Metal wired cap 486 GB) while
importing 8612. This is a report of what was tested and what the numbers were, so
the work can be picked up later. **Nothing references this file, and no rule
depends on it.** Where a measurement changed a rule, the rule carries it:
`r020_classify.md` (which model), `r000_llm.py` (what a local model is for, and
the image token ceiling), `r170_transcribe_todo_listings.md` (hex OCR),
`r000_orchestration.md` (toolchain preflight).

## Verdict in one line

**Not yet.** The mechanical half of the chain is local today and in one case
*better* than what ships. Step 020 is the blocker, the 14 agent-driven steps are
unproven, and none of the large models the machine can hold has been tested.

## What "no online model" actually means

36 numbered steps have a rule file. **22 have a runnable script**; **14 are
agent-driven** — rule text only, 4,356 lines of it, where an agent reads the rule
and exercises judgement:

    agent-driven: r006 r090 r110 r140 r160 r180 r200 r230 r240 r250 r260 r270 r290 r300
    biggest:      r300 = 640 lines, r006 = 533, r160 = 452, r250 = 387, r290 = 376, r180 = 353

Only **four** places call a model from inside a program (`r000_llm`):
`r020_classify`, `r020_evaluate`, `r030_assemble`, `r145_judge_figures`. Those are
a config change plus a quality question.

The other 14 are the hard part: today **Claude Code is the executor**. Going local
means a local model must *be* the agent, not merely answer calls. Two data points
exist: GLM finished step 110 correctly in six calls, and it failed an open-ended
task earlier (60 steps, 67 bash calls, no output). Bounded task with an explicit
method and a step budget: yes. "Read this 640-line rule and apply judgement":
untested.

## The setup used

| | |
|---|---|
| server | oMLX 0.7.0.dev4 on `:8080`, **MLX safetensors only** (no GGUF) |
| model | `GLM-5.3-Flash-oQ4e`, 320B/18B active, multimodal, 1M ctx, **169 GB on disk, 170–191 GiB resident** |
| specialists | `~/omlx-models-doc`: GLM-OCR-8bit (1.6 GB), dots.ocr-8bit (4.4 GB), PaddleOCR-VL-1.6-MLX-8bit (1.1 GB) — run standalone via `mlx_vlm` in `~/.omlx-07`, never through the server |
| headroom | keep weights at or below ~380–400 GB for long context (per llm-config). **Everything below used 169 GB or less.** |

## Step by step, what was measured

| step | result |
|---|---|
| **005, 010** masters + OCR | **already local** — programs and tesseract, no model |
| **110** pubdate | **pass.** GLM wrote `2026-11-14` alone, caught its own missing trailing newline, passed all three checks the rule names. 6 calls, ~40 s of generation |
| **170** listings | **better than today.** See below — 0 of 360 hex bytes wrong against the verified `.prg`, where tesseract gets 9.72% wrong |
| **160** dense mark matrix | **pass with geometry doing the cells.** Vision 100% on dense rows, 0% on sparse; a 40-line geometric reader covers the sparse ones exactly |
| **020** classify | **fail.** 90.4% of block labels, and the misses are systematic |
| **030, 145** | not tested |
| the 14 agent-driven steps | one success (110), one failure, 4,356 lines unexercised |

## Step 020 — the blocker

GLM-5.3 was given `r020_classify.PROMPT` **unmodified**, with the same overlay and
digest, on 15 pages of 8611 spanning every `page_kind`, diffed against the Opus
verdict that shipped.

| | `low` | `high` |
|---|---|---|
| block labels agreeing | 90.4% (639/707) | 90.7% on the 9 hardest (559/616; `low` scored 89.6% on the same 9) |
| reading order identical | 12/15 pages | 7/9 |
| `page_kind` identical | 11/15 pages | 6/9 |
| cost | 50 s/page — **2.8 h** per issue | 183 s/page — **10.2 h** |

`high` buys **+1.1 points for 3.7x the time**, and it is a reshuffle rather than a
gain: it fixed p006 (9/17 -> 16/17) and p059 (30/39 -> 39/39) and broke p136
(113/113 -> 106/113) and p102 (63/63 -> 59/63).

**Read the 90.4% with the taxonomy in hand.** Two thirds of the disagreements
(49 of 68) are GLM saying `noise` where Opus said `ad`. `ARTICLE_LABELS` is
`{heading, body, listing-inline}`, so both are excluded alike — that class costs
overlay colours and nothing else. The damage is elsewhere and is of three kinds:

- **p094** — all 39 labels agreed, and id35 was **dropped from the reading order**.
  That block is 80 words of body text. **Text lost**, and label agreement cannot
  see it.
- **p075** — two `noise` blocks promoted to `body`. Their text is
  `'e! N e! 8/2 5/64/1'` and `'issen Si erfüger >-Interfa'`, read off a screened
  tint. **Garbage injected.**
- **p006** — 8 of 17 `toc` blocks relabelled `heading`/`body`, including `INHALT`
  and a 243-word entry list, plus a reading order where Opus correctly returned
  `[]`. **The contents page injected into an article.**

Blocks crossing the corpus boundary: ~1.6%. Small, but the content of that 1.6%
is lost text and injected garbage, which are defects rather than degradation.

## Where a local model is already better: program listings

8611 p59 is 45 lines of MSE hex (`addr : b0..b7 cs`, the last 360 bytes of
`3D-CODE`). `issues/8611/prg/3d.code.prg` is the hand-transcribed,
checksum-satisfying binary, load `$4000` — so truth is byte-level and not a
judgement.

| reading | lines | addresses not in the prg | byte-perfect lines | wrong bytes |
|---|---|---|---|---|
| tesseract (`ocr/out/059.txt`) | 41 | 5 | 25/36 | **28/288 = 9.72%** |
| GLM-OCR-8bit, column crops | 45 | 0 | **45/45** | **0/360 = 0.00%** |

GLM-OCR's addresses are contiguous `$4a60`-`$4bc0`, no gaps, last line ending
exactly at the binary's final byte `$4bc7`. Where tesseract read `42360`, `cA4`,
`Aad8`, `4650`, `£fO £8` it read `4a60`, `c4`, `4ad8`, `4b50`, `f0 f8`.

**As a comparison layer** (both readings, disagreements adjudicated by the `.prg`),
over the 34 lines both read = 272 byte comparisons:

    agree and both right   260  (95.6%)   nobody needs to look
    agree and both wrong     0            no shared blind spot on this page
    disagree                12  (4.4%)    the review surface
       of which: tesseract wrong, vision right  12  (100%)
                 vision wrong, tesseract right   0

Plus tesseract claimed seven addresses absent from the program and missed eleven
the vision model read. A misread address writes bytes to the wrong place in
memory, which is a dead program rather than a typo.

Two conditions are necessary: a **single-column crop** (a whole dense page makes
GLM-OCR loop) and a modest `max_tokens`. Scorer: `r170_score_hex_ocr.py`, with a
negative control — corrupting 3 bytes and 1 address makes it report exactly
"1 bad address, 42/44 perfect, 3/352 wrong".

## Dense mark matrices — 8608/29 Tabelle 1

The largest hard table in the corpus and still **untranscribed**: it shipped as
two pictures, `29-t1a.png` and `29-t1b.png`, with no `<table>` in the article.
73 rows x 12 columns. The column header is vertical digits on two lines (`1 1 1`
over `1 2 3 4 5 6 7 8 9 0 1 2`), the marks are `+` / `-` / `x`, most cells are
**blank and blank is a value**, and it is dot-matrix output, not typeset.

Page 31 holds 38 of the rows. Cut into its printed sections at native 600 dpi from
`/Volumes/S/cmyk/8608-cmyk/600_cropped/031.tiff`, each strip carrying the digit
header composited above it:

| section group | GLM-5.3 rows exact | cells |
|---|---|---|
| dense (sections 1-4) | **16/16** | **192/192 = 100%** |
| sparse (5a, 5b, 6, 7 — blanks dominate) | **0/22** | **0/264 = 0%** |

Not a middling 42% — a perfect score and a total failure, averaged. On the sparse
sections it ran 88-91 s each and hit the 2000-token cap with nothing parseable.
Counting empty space is where it breaks.

tesseract on the same strips: two of sixteen dense rows recoverable, and the
sparse rows are not wrong but **unrecoverable** — truth `+..+....++++` returns as
`+ + ++ ++`, six marks with no way to know which of twelve columns they occupy.

**Each layer caught the other.** A geometric reader (column centres from the
printed digit header, each cell classified by the shape of its ink) produced all
38 rows — but called every `x` a `+`, because its test was "some pixel column
holds ink for >=80% of the glyph height" and this dot-matrix `x` has a
near-vertical centre. GLM read section 1 row 4 as `++x+++++++++` where the reader
said `++++++++++++`; the scan says GLM was right. Fixed by testing the width of
ink at the TOP of the glyph — narrow for `+`, wide for `x`. The corrected reader
was then verified by eye on 4 of the 8 sections, including a sparse one.

**Implication for the layering.** For a mark grid the bottom layer should not be
OCR at all: OCR destroys horizontal position, which is the only thing carrying the
meaning. Geometry reads the cells; the model reads the row labels (real words) and
adjudicates the glyph classification, which is the one judgement geometry gets
wrong. That is a sharper version of what `r160` already says.

## `reasoning_effort` is an honesty dial, not a quality dial

This decides unattended viability more than any accuracy number.

8611 p99's frequency table misprints the G# row: 485 is `0x1E5`, so Lo-Hex should
be `E5` and Lo-Dez `229`; the magazine prints `E3` and `227` (the Futureteufelchen).
GLM returned **E3 / 227 in 4 runs of 4**, at both efforts and both framings — it
read the paper instead of doing the arithmetic. tesseract's text for that page
contains **neither** value, so the answer came from the image alone.

Asked for the same row against **p94**, where the table stops at F# above a printed
"Fortsetzung auf Seite 99":

| effort | answer |
|---|---|
| `low` | `Lo-Hex=F2 Lo-Dez=242` — **fabricated**, plausible, unhedged |
| `high` | quoted the continuation note, said the table ends at F#/419, declined |

On a crop that landed on a different article, `high` described the 16-KByte
micro-switch wiring actually in frame and refused again.

So: **`low` where the answer is certainly in the image and a script checks it;
`high` wherever "it is not here" is a possible answer.** For a chain running
overnight, a model that invents rather than stops is worse than no model.

## Image resolution: there is a ceiling, and 2576 px is already at it

Prompt tokens billed for one image of 8611 p99:

| pixels | Mpx | prompt tokens |
|---|---|---|
| 452x640 | 0.3 | 408 |
| 910x1288 | 1.2 | 1535 |
| 1821x2576 | 4.7 | **3865** — the cap |
| 3642x5152 | 18.8 | **3865** — 4x the pixels, same cost, same detail |
| 2480x7016 | 17.4 | 1941 — a tall strip gets **less** |

`IMAGE_LONG_EDGE = 2576` in `r000_llm.py`, tuned to Opus's limit, is therefore also
right for GLM. More pixels buy nothing and a long thin crop buys less than nothing.
To read a small region, crop so the region fills a roughly page-shaped frame.
Specialists differ: dots.ocr takes 11.3 Mpx (~2824x3994, ~14.4k image tokens),
GLM-OCR 9.6 Mpx, PaddleOCR-VL 4.06 Mpx.

## The document specialists

| model | size | verdict |
|---|---|---|
| **GLM-OCR-8bit** | 1.6 GB | **the win.** Byte-perfect on hex (above); transcribed a four-column contents page with dot leaders accurately. Loops on a whole dense page; reads across columns on a multi-column dump. Both fixed by single-column crops |
| **dots.ocr-8bit** | 4.4 GB | emits layout + reading order as JSON, elements already in reading order. On the 5 of 15 test pages it completed with article blocks, pairwise reading-order agreement with Opus was 100%, 100%, 98.5%, 100%, 92.2%. **Looped on 5 of 15** — all dense pages. 74-102 s/page |
| **PaddleOCR-VL-1.6** | 1.1 GB | loops on a layout prompt, as expected: its own card says the transformers path does element-level recognition only; page layout comes from PP-DocLayout in the official pipeline. Untried as the designed pair |

**None of them follows a custom output schema.** Asked for `<index> <type> <quote>`
lines plus a page type, GLM-OCR just transcribed the page as markdown — accurately,
in its own format. They are fixed-task models. Their taxonomies are generic
(`Caption`, `Text`, `Section-header`, `Table`, `Title`, `Picture`…) and cannot
express `toc` vs `body` or `kleinanzeige` vs `ad`, which is precisely the
distinction GLM-5.3 got wrong at 020.

**Use the Python API, not `python -m mlx_vlm.generate`.** MEASURED on one
2825x3995 page: through the API it bills 14,415 prompt tokens and returns correct
output; through the CLI, with no `--resize-shape` passed, the same file yields
boxes in a ~1000 px space and then a token loop. The *cause* is not established —
the CLI's `--resize-shape` defaults to `None` and it only resizes when set, so the
likelier culprit is how it builds the prompt. Do not infer the model or the quant
is at fault, which is what the loop first looked like.

## Operational findings

- **A non-interactive `ssh host 'cmd'` does not source `.zprofile`**, so Homebrew is
  off `PATH` and every `command -v` reports MISSING when the tool is installed.
- **`requirements.txt` is the site generator's list, not the chain's.** A venv built
  from it runs no step. Now documented with a one-command preflight in
  `r000_orchestration.md`.
- **An unattended agent needs transport retry.** A run died twice on
  `[Errno 65] No route to host` while `ping` showed 0% loss and `curl` from the same
  host returned 200. Cause: a reject route for the server's subnet sitting behind
  the per-host ARP entry; when that entry ages out the next `connect()` falls
  through. Fixed with one persistent keep-alive connection per run plus an
  ARP-warming ping before any reconnect.
- **`r160`'s vision-crop path is stale.** It says
  `~/DNB/<YYMM>/<YYMM>-cmyk/600_cropped/<NNN>.tiff`; the files are at
  `/Volumes/S/cmyk/<YYMM>-cmyk/600_cropped/`, and `~/DNB` holds only 8611 and 8609.
  Only 8611 has `masters600` on disk.

## What has NOT been tested

1. **Every large model the machine can hold.** Everything above ran on 169 GB or
   less. Untried: `mlx-community/Qwen3-VL-235B-A22B-Instruct-4bit` (~130 GB),
   DeepSeek-V4.1's vision weights (already on disk, `~/omlx-models-v41`, needs a
   server switch), `Qwen2.5-VL-72B-Instruct-8bit` (73 GB, in the LM Studio cache).
   **Step 020 is where this would matter and it is the one thing not done.**
2. **`r020_evaluate` with a local model.** The project's own harness for exactly
   this question — a vision model transcribes each page, scored on recall /
   precision / order against the pipeline. Opus's baseline on 8611 (173 pages):
   recall 0.930, precision 0.975, order 0.999, headings 0.893. A local run must
   write to a separate `truth-glm/`, because `truth/` is cached per page and
   overwriting it destroys the comparison.
3. **Any of the 14 agent-driven steps beyond 110.**
4. **Steps 030 and 145**, the other two `r000_llm` callers.
5. **German.** The specialists' cards list English/Chinese/multilingual; German is
   not advertised. It read 1986 German correctly in every test here, but that is
   observation, not a guarantee.

## Suggested order to pick this up

1. Run `r020_evaluate` with GLM into `truth-glm/`, starting with the six pages
   `WORST.txt` already flags (p182, p187, p75, p28, p55, p36). Cheap, and it is the
   project's own metric rather than a proxy.
2. If that falls short, test Qwen3-VL-235B-4bit on the same 15 pages. This is the
   one honest use of the 512 GB.
3. Hand a local model one real agent-driven step end to end — r240 or r260, not
   r300 — and see whether it can follow a 300-line rule unsupervised.
4. Finish 8608/29 Tabelle 1 (page 32 holds the remaining ~35 rows) as the dense
   mark-matrix proof, geometry for cells and the model for labels.
