# 325 — Read the whole issue, for sense

**Applies to:** all — OCR damage is a property of the scan, not of the issue kind.

**Goal:** find the transcription errors that no pattern can describe, by READING
every word of every article as a reader would, and confirming each suspicion
against the printed page.

---

## Why this exists: every other pass is blind in the same way

By the time this step runs, the issue has been through r280 (word cleanup),
r290 (headings), r310 (invariants), r320 (omission) and r330 (reprint
comparison). Every one of them is **pattern-driven or diff-driven**:

| pass | what it does | what it cannot see |
|---|---|---|
| r280 | substitutes from a fixed table of confusions | anything not on the table |
| a glyph sweep | greps for `©`, `%`, `$`, unbalanced `»«`, `O`/`0`, `l`/`1` | anything nobody thought to grep |
| r310 | regex invariants over the markup | prose that is valid HTML |
| r320 | counts blocks kept against blocks dropped | whether the kept text is *right* |
| r330 | diffs a reprint against its original | the articles with no reprint, and errors BOTH printings share |

They confirm suspicions. They cannot have suspicions of their own.

MEASURED on SH8601: after all of the above had run and the issue was believed
finished, the owner opened an article and read
`<h2>Die Befehle zur $priteprogrammierung</h2>`. Valid HTML, plausible shape,
wrong — and invisible to every gate. That is the class this step is for.

**And a scope note in a brief is a scope note in the result.** SH8601's glyph
sweep was told "do not touch headings" — meaning *do not restructure them* —
and it read that as *do not look there*. The 247 headings went unswept, which is
exactly where the example above was hiding. **Say what to READ separately from
what to EDIT.**

## What is in scope

Everything in the article except listings:

- every `<p>`, including `<p class="intro">` and `<p class="source">`;
- **every heading, `<h1>`–`<h6>`** — see above;
- `<figcaption>`, `<aside>`, `<address class="author">`, and **table cells** —
  a wrong digit in a register table reads as plausible and is wrong;
- screen dumps, monitor dumps and command syntax that sit in `<p>` rather than
  `<pre>` — they are prose as far as the markup is concerned.

**`<pre>` — ONLY THE DISK'S IS OUT OF SCOPE.** The distinction is the attribute,
not the tag:

| | source | proofread? |
|---|---|---|
| `<pre data-filename="…">` | the generator fills it from `prg/` | **no** — the disk owns it |
| `<pre>` with text in the file | somebody typed it from the page | **YES — it is transcription like any other** |

MEASURED on SH8601: 31 blocks are disk-backed and **68 are hand transcriptions**
— 44 of them in one article. They are the monitor dumps, screen dumps and short
code examples the magazine sets INSIDE the body text, and no listing is missing
on their account: every `Listing N` the articles cite has its own figure.

**A brief that says "skip `<pre>`" therefore leaves the least-checked text in the
issue unchecked.** Mine did, and the blocks it excused read `1da` for `lda`,
`#804` for `#$04`, `bp1` for `bpl`, `a 00645` for `a 00b45`. Say
"skip `<pre data-filename>`" instead.

### An assembler dump CHECKS ITSELF — use that, do not eyeball hex

A wrong byte is indistinguishable from a right one by reading. But a monitor
dump carries the same information twice, so the two halves can be cross-checked
mechanically before anyone looks at a page:

```
a 00b40  a2 04     ldx #$04
  ^addr  ^bytes    ^mnemonic + operand
```

1. **The bytes encode the mnemonic.** Disassemble `a2 04` — it must be
   `ldx #$04`. A mismatch is either OCR damage or a magazine error, and either
   way it is a candidate that a reader would never have spotted.
2. **Addresses advance by instruction length.** `a 00b40` + 2 bytes must be
   followed by `a 00b42`. A gap or a repeat localises the damage to one line.

Run both over every dump, THEN take the survivors to the page. This is how a
hex pass reaches accuracy that reading cannot: the machine finds the candidates,
and vision decides each one — the same division of labour as everywhere else in
this chain, applied to material where human reading is weakest.



## What to look for

Read for MEANING, not for patterns. **If a sentence makes you re-read it, that
is the signal.** The recurring shapes, as a prompt rather than a checklist:

- a word that is neither German nor a product/technical term — `$priteprogrammierung`,
  `Tarthau<steine`, `wenri`;
- lost or inserted word spaces — `StringinFAC`, `damitderZ80`, `Zwischenkabelangeschlossen`;
- a glyph substituted for a plausible neighbour — `©` for C, `%` for `?«`,
  `$` for S, `l` for 1, `O` for 0, `»` read as s;
- a sentence that does not parse, a clause that contradicts itself, a number
  that cannot be right in its context;
- a heading that is really a paragraph tail, or that has swallowed listing text;
- hex addresses and figures mangled — `$8 A27`, `$lfff`, `154l`.

## ALWAYS VERIFY WITH VISION

**Every candidate, without exception**, before it is changed:

1. **Locate** — the block index at `<tmp>/ocr/out/blocks/pNNN.txt` gives bboxes;
   the article's pages are in its `64er.pages` meta. For a precise line,
   `pdftotext -f N -l N -bbox <issue pdf>` gives word boxes (PDF pt × 600/72 =
   600 dpi px). Use it **only as a locator**.
2. **Crop and LOOK** — `masters600/NNN.png` at that box, read with your own
   eyes, magnified where the glyph is ambiguous. SH8601 needed 200–400% to tell
   a digit `1` from a lower-case `l`, and a wide round capital `O` from a zero.
3. **Decide from what you saw.** Never from the PDF's text layer: it is raw
   tesseract, i.e. the thing being checked wearing a different hat — see r000,
   *the PDF's text layer is a CANDIDATE SOURCE, not authority*.

Nothing here is unverifiable. Every word is on a page available at 600 dpi; the
only genuine exception is print too damaged to read, which SH8601 never once
produced.

## TYPOS IN PRINT REMAIN TYPOS IN THE HTML

This is the whole discipline of the step, and the reason a reading pass is
dangerous without it: a reader who has just found three real errors is primed to
"fix" the fourth thing that looks wrong.

MEASURED on SH8601, all verified at magnification and all KEPT:

```
Beipielprogramm                p090      nebenanderliegene       8512 p78
80x200 = 1600 Byte             p054      »MANDELBROT1»           p046
zwischen $0 uns $1fff          p060      »Punkt löschen»         p054
Listing 1. Alle »ALLE SPRITES« p043      «SPRITE 4,1,6,1,1,0,0«  p103
»Rescue on Fractalus,          p106      dem »%«-Zeichen         p081
Warte- / stehenden             p104      GRAFIK (for GRAPHIC)    p054
```

You are finding OUR misreadings of the page. You are never correcting the
magazine. When the page prints the odd thing, record it as printed and move on.

## A MAGAZINE ERROR THAT MISLEADS IS A FUTURETEUFELCHEN CANDIDATE — RECORD IT

*Typos in print remain typos in the HTML* is about the TEXT, and it does not
change. But where the page is not merely mis-set but actually MISLEADING — an
arithmetic result that is wrong, a cross-reference to something that does not
exist, a figure numbered against its own caption — the archive has a place to
say so beside the text without altering it: `<aside class="futureteufelchen">`,
see r300.

**You do not add one.** Reading is how candidates are found; adding one is the
issue owner's call, case by case. Record the passage, what appears wrong, and
the crop — then move on. A list of candidates is a report, never a worklist.

## Granularity

Word-level substitutions only — r000's *OCR cleanup granularity* applies in
full. Do not rewrite sentences, do not "improve" wording, do not modernise
spelling (`daß`, `muß`, `Adreß` stay).

## How to run it

Split the issue by WORD COUNT, not by article count, and give each reader three
to five articles of roughly equal weight — SH8601's 29 articles are 80,242
prose words, which balanced into seven groups of ~11,400. Tell each reader what
is peculiar about its articles: a reference table of ROM entry points, a
masthead of names and addresses, a bibliography, an ISBN list, a crossword. That
is where the errors nothing else can see actually live.

Readers must work in small steps and report as they go. A reader that goes
silent for a long stretch gets killed by the watchdog and loses its work.

## Verification

1. Every fix carries `was -> is`, the page, and the crop it was read from.
2. Every REJECTED candidate is recorded too, with the same evidence — the
   rejects are how the next run knows what the magazine really prints, and
   SH8601's reject list is the table above.
3. Each reader states its honest coverage: what it read in full, and what (if
   anything) it skimmed.
4. `generate.py --issues <ID> --future --join` exits 0.

## Recorded in LOG.md

The fix table, the reject table, and the coverage statement, per reader.
