#!/usr/bin/env python3
"""Decode Top-Ass / Hypra-Ass PRG files.

Top-Ass stores assembler source as tokenized BASIC. Tokens $81-$b8 encode
6502 mnemonics; the same tokens preceded by '.' ($2e) encode assembler
directives. This decoder reverses both mappings.

Hypra-Ass uses the same storage format. There are two source variants:

1. **Raw Hypra-Ass .prg** — the file as written by Hypra-Ass on the C64.
   Mnemonics are stored as BASIC tokens ($81-$B8); directives are stored
   as `'.' + token`. Use ``decode_prg_bytes()``.

2. **Petcat-detokenized .txt** — the same file run through petcat. Mnemonic
   tokens have been expanded to plain ASCII text (so `'LDA'` etc. appears
   in the byte stream). The text is then re-tokenized by `petcat2prg` to
   give a synthetic PRG whose only BASIC tokens are the ones from the
   original BASIC starter line (SYS, `*`, `=`, ...). Use
   ``decode_bytes(..., topass=False)``.

Top-Ass mode (``decode_bytes(..., topass=True)``) operates on raw Top-Ass
.prg files directly — same byte layout as Hypra-Ass raw but with full
directive names emitted (`.DEFINE` rather than `.EQ`).

The mnemonic table was extracted from the interleaved string
'LSLLCAASSICABLORRSCDEJJTTTTTTIPPPIDRNCSCSCCSRPDBBBBBBBBB
 DTDDMDNTTNPSISROOBPEOMSXAYASXNLHLNETOLELELLETHERPMVVCCNE
 AAXYPCDXYCXLTRALRCYCRPRAXAYXSYPAAXYSPCCIIVDDIPXKLICSCSEQ'
found in the ASE v2.0 binary.

The directive table was extracted from the null-terminated string table
starting at 'UNTIL' in the same binary.

Usage:
  assembler_decode.py <file.prg>             # Hypra-Ass raw .prg (decode tokens)
  assembler_decode.py --petcat <file.prg>    # petcat-tokenized .txt (passed
                                              # through petcat2prg first)
  assembler_decode.py --topass <file.prg>    # Top-Ass raw .prg
"""

import sys

# BASIC V2 token table ($80-$CB)
BASIC_TOKENS = [
    'END', 'FOR', 'NEXT', 'DATA', 'INPUT#', 'INPUT', 'DIM', 'READ',    # $80-$87
    'LET', 'GOTO', 'RUN', 'IF', 'RESTORE', 'GOSUB', 'RETURN', 'REM',   # $88-$8f
    'STOP', 'ON', 'WAIT', 'LOAD', 'SAVE', 'VERIFY', 'DEF', 'POKE',     # $90-$97
    'PRINT#', 'PRINT', 'CONT', 'LIST', 'CLR', 'CMD', 'SYS', 'OPEN',    # $98-$9f
    'CLOSE', 'GET', 'NEW', 'TAB(', 'TO', 'FN', 'SPC(', 'THEN',         # $a0-$a7
    'NOT', 'STEP', '+', '-', '*', '/', '^', 'AND',                      # $a8-$af
    'OR', '>', '=', '<', 'SGN', 'INT', 'ABS', 'USR',                    # $b0-$b7
    'FRE', 'POS', 'SQR', 'RND', 'LOG', 'EXP', 'COS', 'SIN',           # $b8-$bf
    'TAN', 'ATN', 'PEEK', 'LEN', 'STR$', 'VAL', 'ASC', 'CHR$',        # $c0-$c7
    'LEFT$', 'RIGHT$', 'MID$', 'GO',                                    # $c8-$cb
]

# 6502 mnemonics: token $81 + index
MNEMONICS = [
    'LDA', 'STA', 'LDX', 'LDY', 'CMP', 'ADC', 'AND', 'STX',  # $81-$88
    'STY', 'INC', 'CPX', 'ASL', 'BIT', 'LSR', 'ORA', 'ROL',  # $89-$90
    'ROR', 'SBC', 'CPY', 'DEC', 'EOR', 'JMP', 'JSR', 'TXA',  # $91-$98
    'TAX', 'TYA', 'TAY', 'TSX', 'TXS', 'INY', 'PLP', 'PHA',  # $99-$a0
    'PLA', 'INX', 'DEY', 'RTS', 'NOP', 'CLC', 'SEC', 'CLI',  # $a1-$a8
    'SEI', 'CLV', 'CLD', 'SED', 'RTI', 'PHP', 'DEX', 'BRK',  # $a9-$b0
    'BPL', 'BMI', 'BVC', 'BVS', 'BCC', 'BCS', 'BNE', 'BEQ',  # $b1-$b8
]

# Directives (dot-prefixed): token $82 + index
# When a '.' precedes a token byte, the token is a directive, not a mnemonic.
DIRECTIVES = [
    'UNTIL', 'UNLESS', 'DO', 'LOOP', 'WHILE', 'CASE OF', 'OF',       # $82-$88
    'OTHERWISE', 'CASEEND', 'DURING', 'EXLOOP', 'BEGIN', 'END',       # $89-$8e
    'DEFINE', 'BASE', 'BYTE', 'WORD', 'OBJECT', 'OBJEND', 'MACRO',   # $8f-$95
    '..', '.', 'MACEND', 'COMMON', 'APPEND', 'ADL', 'CLIST',         # $96-$9c
    'ECOND', 'ALTER', 'COND', 'MACLIB', 'NAMES', 'SOURCE', 'LIST',   # $9d-$a3
    'SYMBOLS', 'SCREEN', 'REVERS', 'SPACE OF', 'REQUEST', 'CODE',    # $a4-$a9
    'SYNTAX', 'CONTROL', '=', '-', 'EXCASE', 'LAX', 'LAY', 'LXY',   # $aa-$b1
    'SAX', 'SAY',                                                      # $b2-$b3
]


def petscii_char(b):
    """Decode a single PETSCII byte to a unicode character."""
    if 0x41 <= b <= 0x5a:
        return chr(b + 0x20)  # $41-$5A -> a-z
    if 0x61 <= b <= 0x7a:
        return chr(b - 0x20)  # $61-$7A -> A-Z
    if 0xc1 <= b <= 0xda:
        return chr(b - 0x80)  # $C1-$DA -> A-Z
    return chr(b)


def decode_token(b, is_directive):
    """Decode a single token byte, returning the mnemonic or directive string."""
    if is_directive:
        idx = b - 0x82
        if 0 <= idx < len(DIRECTIVES):
            d = DIRECTIVES[idx]
            if d in ('.', '..'):
                return '.' + d  # .. becomes '..' with the leading dot, ... becomes '...'
            return d
        return f'<${b:02x}>'
    else:
        idx = b - 0x81
        if 0 <= idx < len(MNEMONICS):
            return MNEMONICS[idx]
        return f'<${b:02x}>'


def decode_bytes(data, topass=False):
    """Decode Top-Ass/Hypra-Ass PRG binary data, return list of formatted lines.

    Args:
        data: raw PRG binary bytes
        topass: if True, use Top-Ass directive names.
                if False, use Hypra-Ass directive names.
                Both modes decode BASIC tokens as 6502 mnemonics.

    Hypra-Ass output is prefixed with the BASIC line number formatted as
    'NNN -' to mirror the listing layout produced by Hypra-Ass's own LIST
    routine (and by ``tools/hypra-ass-decode.py`` which decodes raw
    Hypra-Ass .prg files directly).
    """
    pos = 0
    lines = []

    # Load address (skip)
    load_addr = data[pos] | (data[pos+1] << 8)
    pos += 2

    # First pass (Hypra-Ass only): scan max line number to size the prefix
    # column so '-' lines up across the whole listing.
    num_col = 0
    if not topass:
        scan = pos
        max_line = 0
        while scan < len(data) - 1:
            link = data[scan] | (data[scan + 1] << 8)
            scan += 2
            if link == 0:
                break
            max_line = max(max_line, data[scan] | (data[scan + 1] << 8))
            scan += 2
            while scan < len(data) and data[scan] != 0:
                scan += 1
            scan += 1
        num_col = max(3, len(str(max_line))) + 1

    while pos < len(data) - 1:
        # Link address
        link = data[pos] | (data[pos+1] << 8)
        pos += 2

        if link == 0:
            break

        # Line number
        line_num = data[pos] | (data[pos+1] << 8)
        pos += 2

        # Decode bytes until \0
        text = []
        if topass:
            # Top-Ass: decode tokens as 6502 mnemonics/directives,
            # but in comments expand as BASIC tokens
            in_comment = False
            while pos < len(data) and data[pos] != 0:
                b = data[pos]
                if b == 0x3b:  # ';' starts a comment
                    in_comment = True
                if in_comment:
                    text.append(petscii_char(b))
                elif b == 0x2e and pos + 1 < len(data) and data[pos + 1] >= 0x80:
                    # Dot + token = directive
                    pos += 1
                    d = decode_token(data[pos], is_directive=True)
                    text.append('.' + d.lower())
                    # Insert space after directive name if operand follows
                    if pos + 1 < len(data) and data[pos + 1] != 0 and data[pos + 1] != 0x3b:
                        text.append(' ')
                elif b >= 0x80:
                    text.append(decode_token(b, is_directive=False).lower())
                else:
                    text.append(petscii_char(b))
                pos += 1
        else:
            # Hypra-Ass: source text is stored as tokenized BASIC, but the
            # source code itself (after the BASIC starter line) is PETSCII
            # text typed on the C64 — so shifted-PETSCII uppercase letters
            # ($C1-$DA, also $CB) share byte values with BASIC tokens
            # (LEFT$, RIGHT$, MID$, GO). Disambiguate by treating those
            # ranges as letters, not tokens. Tokens $80-$C0 (SYS, '*' etc.)
            # remain tokenized — these legitimately appear in the BASIC
            # starter line and never collide with shifted-PETSCII letters.
            while pos < len(data) and data[pos] != 0:
                b = data[pos]
                if 0xc1 <= b <= 0xda:
                    text.append(petscii_char(b))  # shifted PETSCII A-Z
                elif 0x80 <= b <= 0xc0:
                    text.append(BASIC_TOKENS[b - 0x80])
                elif b >= 0x80:
                    text.append(petscii_char(b))
                else:
                    text.append(chr(b))
                pos += 1
        pos += 1  # skip \0

        line_text = ''.join(text)

        if topass:
            # Format: align label, mnemonic, operand, comment
            formatted = format_line(line_text)
            lines.append(formatted)
        else:
            # Hypra-Ass: text decoded from petcat-tokenized BASIC. The text
            # comes in two flavors: 'jammed' (mnemonic and operand glued
            # together, e.g. 'LDA#$0D;CR' — written in Hypra-Ass which
            # stores everything densely) and 'pre-formatted' (whitespace
            # already inserted by the author, e.g. taktzyklen.src). The
            # formatter applies column layout to the jammed case and
            # passes pre-formatted lines through almost unchanged.
            formatted = format_hypra_ass_line(line_text)
            lines.append(f"{str(line_num).ljust(num_col)}-{formatted}")

    return lines


def format_line(line_text):
    """Format an assembler line with aligned columns.

    Reproduces the original hypra-ass-decode.py indentation:
    - No label (leading space): indent 10, insert space after 3-char mnemonic
    - With label: pad label to 10 chars, insert space after 3-char mnemonic
    - Align ';' comments to column 25 (if they'd appear before that)
    - Directives and comment-only lines pass through unchanged.
    """
    if not line_text or line_text.startswith(';'):
        return line_text

    inserted_space = False

    if line_text.startswith('.'):
        # Directive: pad symbol name before '=' in .define lines
        # Find '=' that's not inside a comment
        semi = line_text.find(';')
        eq_pos = line_text.find('=')
        if eq_pos != -1 and (semi == -1 or eq_pos < semi):
            before = line_text[:eq_pos].rstrip()
            after = line_text[eq_pos:]
            line_text = before.ljust(17) + '= ' + after[1:]
        inserted_space = True
    elif line_text.startswith(' '):
        rest = line_text[1:]
        rest = rest[:3] + ' ' + rest[3:]
        line_text = ' ' * 10 + rest
        inserted_space = True
    elif line_text.find(' ') != -1:
        space_pos = line_text.find(' ')
        label = line_text[:space_pos]
        after = line_text[space_pos + 1:]
        after = after[:3] + ' ' + after[3:]
        line_text = label.ljust(10) + after
        inserted_space = True

    if inserted_space:
        # Align ; comment to column 25
        in_quotes = False
        semi_pos = -1
        for i, c in enumerate(line_text):
            if c == '"':
                in_quotes = not in_quotes
            elif c == ';' and not in_quotes:
                semi_pos = i
                break
        if semi_pos != -1 and semi_pos < 25:
            before = line_text[:semi_pos].rstrip()
            after = line_text[semi_pos:]
            line_text = before.ljust(25) + after

    return line_text.rstrip()


# --- Hypra-Ass listing formatter -------------------------------------------
#
# Used by both the live ``decode_bytes`` path (article 95, 8606) and the
# standalone ``tools/hypra-ass-decode.py`` (article 134, 8606). Keep the
# two callers in sync — both must produce the same column layout so BLOCK
# (SWAP) listings and CASS listings look consistent in the rendered articles.

_MNEMONIC_SET = set(MNEMONICS)

# Short Hypra-Ass directive forms that may appear glued to their operand
# in PETSCII source (no space inserted by the user). Mapping is identity
# for forms we keep short; '.EQ' is special-cased to expand to '.DEFINE'
# with '=' alignment, matching the BLOCK pipeline's output.
_HYPRA_SHORT_DIRECTIVES = ('.BA', '.BY', '.WO', '.TX', '.OB', '.LI', '.OP')


def _find_comment(s):
    """Return index of the first ';' that is not inside double quotes, or -1."""
    in_quotes = False
    for i, c in enumerate(s):
        if c == '"':
            in_quotes = not in_quotes
        elif c == ';' and not in_quotes:
            return i
    return -1


def _is_jammed(body):
    """Heuristic: does this line need column formatting inserted?

    'Jammed' means the author wrote it in dense Hypra-Ass style with no
    space between the mnemonic/directive and its operand (or between an
    operand and its trailing ';' comment). 'Pre-formatted' means the
    source already has columns (e.g. taktzyklen.src typed in a different
    assembler that preserves whitespace).
    """
    if not body or body[0] == ';':
        return False
    if body[0] == '.':
        # Find end of directive name (alphabetic chars after the dot).
        i = 1
        while i < len(body) and body[i].isalpha():
            i += 1
        # Jammed if there's an operand and it's glued (no space between
        # the directive name and the operand). '.OPT OO' is not jammed;
        # '.BA$15D3' is.
        return i < len(body) and body[i] != ' '
    if ' ' in body:
        first, rest = body.split(' ', 1)
        if first in _MNEMONIC_SET:
            # 'OPC OPERAND...' — already spaced.
            return False
        # First token looks like a label; recurse on the rest.
        return _is_jammed(rest.lstrip())
    # No space anywhere — definitely jammed.
    return True


def format_hypra_ass_line(line_text):
    """Format a Hypra-Ass source line with aligned columns.

    Layout (after the 'NNN -' prefix prepended by decode_bytes):
        col 0..9   label   (left-justified, 10 chars; blank when none)
        col 10..12 opcode  (3 chars)
        col 13     space
        col 14..   operand
        col 25..   comment (';...') aligned when feasible
    '.DEFINE NAME = VAL' lines are rendered without a label column,
    matching the BLOCK pipeline's output for .EQ-equivalent directives.
    """
    if not line_text:
        return line_text

    # Comment-only lines: pass through.
    if line_text.startswith(';'):
        return line_text

    # Pre-formatted line (taktzyklen.src style): preserve the source's
    # own columns but still right-trim trailing whitespace.
    if not _is_jammed(line_text):
        return line_text.rstrip()

    # --- Jammed line: rebuild from scratch. ----------------------------

    # .EQ NAME=VALUE  →  .DEFINE NAME    = VALUE  (match BLOCK output)
    if line_text.startswith('.EQ'):
        rest = line_text[3:]
        semi = _find_comment(rest)
        body = rest[:semi] if semi != -1 else rest
        comment = rest[semi:] if semi != -1 else ''
        eq = body.find('=')
        if eq != -1:
            name = body[:eq].strip()
            value = body[eq + 1:].strip()
            out = '.DEFINE ' + name.ljust(9) + '= ' + value
        else:
            out = '.DEFINE ' + body.strip()
        out = out.rstrip()
        if comment:
            out = out.ljust(25) + comment
        return out

    # Other short Hypra-Ass directives '.BA', '.BY', etc. — keep the
    # short form, just insert a space between '.XX' and the operand.
    # Require the char after the 3-letter head to be non-alpha so e.g.
    # '.OPT OO' is not mis-matched as '.OP' + 'T OO'.
    if (any(line_text.startswith(d) for d in _HYPRA_SHORT_DIRECTIVES)
            and (len(line_text) <= 3 or not line_text[3].isalpha())):
        head = line_text[:3]
        rest = line_text[3:]
        semi = _find_comment(rest)
        body = rest[:semi] if semi != -1 else rest
        comment = rest[semi:] if semi != -1 else ''
        body = body.strip()
        out = head + ' ' + body if body else head
        out = out.rstrip()
        if comment:
            out = out.ljust(25) + comment
        return out

    # Lines with a label: 'LABEL .TX"..."' or 'LABEL LDA#$00'.
    space = line_text.find(' ')
    if space != -1 and line_text[:space] not in _MNEMONIC_SET:
        label = line_text[:space]
        rest = line_text[space + 1:].lstrip()
        formatted_rest = format_hypra_ass_line(rest)
        # If rest was a directive line (.XX or .DEFINE) starting at col 0,
        # we still want the label in front and then the directive body.
        # Strip any leading spaces formatted_rest might carry and pad
        # label to col 10.
        return label.ljust(10) + formatted_rest.lstrip()

    # Plain instruction: 'LDA#$0D;CR' or 'JSRCHROUT'.
    # Split first 3 chars as opcode, rest as operand+comment.
    if len(line_text) >= 3 and line_text[:3] in _MNEMONIC_SET:
        opcode = line_text[:3]
        rest = line_text[3:]
        semi = _find_comment(rest)
        operand = (rest[:semi] if semi != -1 else rest).strip()
        comment = rest[semi:] if semi != -1 else ''
        body = opcode
        if operand:
            body += ' ' + operand
        out = ' ' * 10 + body
        out = out.rstrip()
        if comment:
            out = out.ljust(25) + comment
        return out

    # Fallback: unknown shape, leave as-is.
    return line_text.rstrip()


# --- Raw Hypra-Ass .prg decoder --------------------------------------------
#
# Raw Hypra-Ass .prg files (e.g. ``issues/8606/prg/block.prg``) store the
# source as tokenized BASIC: tokens $81-$B8 for 6502 mnemonics, '.' + token
# for assembler directives. This path bypasses petcat entirely — it decodes
# the .prg's byte stream directly and runs the result through the column
# formatter below. Output is byte-equivalent to the Hypra-Ass LIST printout
# reproduced in 64'er magazine issues.

# Hypra-Ass directives (short forms): byte $82 + index in DIRECTIVES, but
# Hypra-Ass in practice only emits these. Names match the long Top-Ass
# spellings, which is what the magazine listings print.
_RAW_PRG_DIRECTIVES = {
    0x8F: 'DEFINE',  # .EQ in Hypra-Ass short form
    0x90: 'BASE',    # .BA
    0x91: 'BYTE',    # .BY
    0x92: 'WORD',
    0x93: 'OBJECT',
    0x94: 'OBJEND',
    0x95: 'MACRO',
}


def _expand_raw_prg_tokens(text_bytes):
    """Expand BASIC tokens in a raw Hypra-Ass line to mnemonic/directive text.

    The byte preceding a token is inspected: '.' + directive byte expands to
    '.<NAME> ' (trailing space), '.' + mnemonic byte (or a bare mnemonic
    token) expands to '<MNEMONIC> ' (trailing space, so the operand is
    separated from the opcode).
    """
    out = []
    i = 0
    n = len(text_bytes)
    while i < n:
        b = text_bytes[i]
        if b == 0x2E and i + 1 < n and text_bytes[i + 1] in _RAW_PRG_DIRECTIVES:
            out.append('.' + _RAW_PRG_DIRECTIVES[text_bytes[i + 1]] + ' ')
            i += 2
        elif 0x81 <= b <= 0xB8:
            out.append(MNEMONICS[b - 0x81] + ' ')
            i += 1
        else:
            out.append(chr(b))
            i += 1
    return ''.join(out)


def _format_raw_prg_line(line_text):
    """Format a raw Hypra-Ass .prg line with aligned columns.

    Input is the output of ``_expand_raw_prg_tokens`` — each mnemonic or
    directive token already has a trailing space inserted.

    Layout (after the 'NNN -' prefix prepended by ``decode_prg_bytes``):
        col 0..9   label   (left-justified, 10 chars; empty when none)
        col 10..12 opcode  (3 chars)
        col 13     space
        col 14..   operand
        col 25..   comment (';...') aligned when feasible
    '.DEFINE NAME=VALUE' is reformatted as '.DEFINE NAME    = VALUE'.
    """
    if not line_text:
        return line_text

    # Comment-only lines: leave as-is.
    if line_text.startswith(';'):
        return line_text

    # Directive lines (start with '.'): handle .DEFINE specially.
    if line_text.startswith('.'):
        semi = _find_comment(line_text)
        body = line_text[:semi] if semi != -1 else line_text
        comment = line_text[semi:] if semi != -1 else ''

        if body.startswith('.DEFINE '):
            after_dir = body[len('.DEFINE '):]
            eq = after_dir.find('=')
            if eq != -1:
                name = after_dir[:eq].rstrip()
                value = after_dir[eq + 1:].lstrip()
                body = '.DEFINE ' + name.ljust(9) + '= ' + value
        body = body.rstrip()
        if comment:
            body = body.ljust(25) + comment
        return body

    # Instruction line: split label / opcode / operand.
    # The tokenizer emitted a single space after every mnemonic. Lines
    # without a label start with one space (the original PRG had a single
    # space before the token byte).
    if line_text.startswith(' '):
        label = ''
        body = line_text[1:]
    else:
        space = line_text.find(' ')
        if space == -1:
            return line_text.rstrip()
        label = line_text[:space]
        body = line_text[space + 1:]

    semi = _find_comment(body)
    code = body[:semi] if semi != -1 else body
    comment = body[semi:] if semi != -1 else ''
    code = code.rstrip()

    # Split opcode / operand. Opcode is the first 3 characters; if a space
    # follows it, the rest is the operand.
    if len(code) >= 4 and code[3] == ' ':
        opcode = code[:3]
        operand = code[4:]
    else:
        opcode = code
        operand = ''

    out = label.ljust(10) + opcode
    if operand:
        out += ' ' + operand
    if comment:
        out = out.ljust(25) + comment
    return out.rstrip()


def decode_prg_bytes(data):
    """Decode raw Hypra-Ass .prg bytes, returning a list of formatted lines.

    Lines are prefixed with the BASIC line number formatted as 'NNN -' to
    mirror the listing layout produced by Hypra-Ass's own LIST routine, and
    the column layout used by the magazine's printed listings.
    """
    pos = 2  # skip load address

    # Determine width for right-aligned line numbers: same width as the
    # largest line number in the file. Hypra-Ass listings in 64'er use
    # 10..900-ish numbering, i.e. 3 digits.
    max_line = 0
    scan = pos
    while scan < len(data) - 1:
        link = data[scan] | (data[scan + 1] << 8)
        scan += 2
        if link == 0:
            break
        max_line = max(max_line, data[scan] | (data[scan + 1] << 8))
        scan += 2
        while scan < len(data) and data[scan] != 0:
            scan += 1
        scan += 1
    num_col = max(3, len(str(max_line))) + 1

    lines = []
    while pos < len(data) - 1:
        link = data[pos] | (data[pos + 1] << 8)
        pos += 2
        if link == 0:
            break
        line_num = data[pos] | (data[pos + 1] << 8)
        pos += 2

        text_start = pos
        while pos < len(data) and data[pos] != 0:
            pos += 1
        raw = data[text_start:pos]
        pos += 1  # skip NUL terminator

        expanded = _expand_raw_prg_tokens(raw)
        formatted = _format_raw_prg_line(expanded)
        lines.append(f"{str(line_num).ljust(num_col)}-{formatted}")
    return lines


def decode_prg(filename, mode='hypra-raw'):
    """CLI entry point. ``mode`` is one of:
        'hypra-raw' — raw Hypra-Ass .prg (default)
        'petcat'    — petcat-tokenized .txt fed through petcat2prg
        'top-ass'   — raw Top-Ass .prg
    """
    with open(filename, 'rb') as f:
        data = f.read()
    if mode == 'hypra-raw':
        lines = decode_prg_bytes(data)
    elif mode == 'top-ass':
        lines = decode_bytes(data, topass=True)
    else:  # petcat
        lines = decode_bytes(data, topass=False)
    for line in lines:
        print(line)


if __name__ == '__main__':
    args = sys.argv[1:]
    mode = 'hypra-raw'
    if '--topass' in args:
        mode = 'top-ass'
        args.remove('--topass')
    if '--petcat' in args:
        mode = 'petcat'
        args.remove('--petcat')
    if len(args) != 1:
        print(f"Usage: {sys.argv[0]} [--topass|--petcat] <file.prg>",
              file=sys.stderr)
        sys.exit(1)
    decode_prg(args[0], mode=mode)
