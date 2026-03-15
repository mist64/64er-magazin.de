#!/usr/bin/env python3
"""Decode Top-Ass / Hypra-Ass PRG files.

Top-Ass stores assembler source as tokenized BASIC. Tokens $81-$b8 encode
6502 mnemonics; the same tokens preceded by '.' ($2e) encode assembler
directives. This decoder reverses both mappings.

Hypra-Ass uses the same storage format but without BASIC tokens — mnemonics
are stored as plain ASCII text. Use --topass to enable Top-Ass token decoding.

The mnemonic table was extracted from the interleaved string
'LSLLCAASSICABLORRSCDEJJTTTTTTIPPPIDRNCSCSCCSRPDBBBBBBBBB
 DTDDMDNTTNPSISROOBPEOMSXAYASXNLHLNETOLELELLETHERPMVVCCNE
 AAXYPCDXYCXLTRALRCYCRPRAXAYXSYPAAXYSPCCIIVDDIPXKLICSCSEQ'
found in the ASE v2.0 binary.

The directive table was extracted from the null-terminated string table
starting at 'UNTIL' in the same binary.

Usage:
  hypra_ass_decode.py <file.prg>             # Hypra-Ass (plain ASCII, errors on tokens)
  hypra_ass_decode.py --topass <file.prg>    # Top-Ass (decodes BASIC tokens)
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
    """
    pos = 0
    lines = []

    # Load address (skip)
    load_addr = data[pos] | (data[pos+1] << 8)
    pos += 2

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
            # Hypra-Ass: pure BASIC detokenization
            while pos < len(data) and data[pos] != 0:
                b = data[pos]
                if 0x80 <= b <= 0xcb:
                    text.append(BASIC_TOKENS[b - 0x80])
                elif b >= 0x80:
                    text.append(chr(b & 0x7f))
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
            # Hypra-Ass: text is already properly spaced from BASIC detokenization
            lines.append(line_text)

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


def decode_prg(filename, topass=False):
    with open(filename, 'rb') as f:
        data = f.read()
    for line in decode_bytes(data, topass=topass):
        print(line)


if __name__ == '__main__':
    topass = '--topass' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--topass']
    if len(args) != 1:
        print(f"Usage: {sys.argv[0]} [--topass] <file.prg>", file=sys.stderr)
        sys.exit(1)
    decode_prg(args[0], topass=topass)
