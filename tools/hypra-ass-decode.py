#!/usr/bin/env python3
"""Decode Hypra-Ass PRG files.

Hypra-Ass stores assembler source as tokenized BASIC. Tokens $81-$B8 encode
6502 mnemonics; a token preceded by '.' ($2E) encodes an assembler directive.
This decoder reverses both mappings and reproduces the printed-listing format:

    NNN  -LABEL     OPCODE OPERAND   ;COMMENT

Line numbers are right-padded by two spaces and followed by '-' to match the
column layout produced by Hypra-Ass's own LIST routine. Bytes are kept as-is
(uppercase letters stay uppercase) so the output matches the magazine print.
"""

import sys

# 6502 mnemonics: token $81 + index
MNEMONICS = [
    'LDA', 'STA', 'LDX', 'LDY', 'CMP', 'ADC', 'AND', 'STX',  # $81-$88
    'STY', 'INC', 'CPX', 'ASL', 'BIT', 'LSR', 'ORA', 'ROL',  # $89-$90
    'ROR', 'SBC', 'CPY', 'DEC', 'EOR', 'JMP', 'JSR', 'TXA',  # $91-$98
    'TAX', 'TYA', 'TAY', 'TSX', 'TXS', 'INY', 'PLP', 'PHA',  # $99-$A0
    'PLA', 'INX', 'DEY', 'RTS', 'NOP', 'CLC', 'SEC', 'CLI',  # $A1-$A8
    'SEI', 'CLV', 'CLD', 'SED', 'RTI', 'PHP', 'DEX', 'BRK',  # $A9-$B0
    'BPL', 'BMI', 'BVC', 'BVS', 'BCC', 'BCS', 'BNE', 'BEQ',  # $B1-$B8
]

# Hypra-Ass directives (short forms): token $82 + index for Top-Ass mapping,
# but Hypra-Ass only emits BA/BY/EQ/TX in practice. We use the Top-Ass long
# names that the magazine prints in its Hypra-Ass listings.
DIRECTIVES = {
    0x8F: 'DEFINE',  # .EQ in Hypra-Ass short form
    0x90: 'BASE',    # .BA
    0x91: 'BYTE',    # .BY
    0x92: 'WORD',
    0x93: 'OBJECT',
    0x94: 'OBJEND',
    0x95: 'MACRO',
}


def decode_tokens(text_bytes):
    """Expand BASIC tokens in a line to their Hypra-Ass mnemonic/directive form.

    Returns a string with tokens replaced. The byte preceding a token is
    inspected: a '.' before a directive byte expands as '.<NAME>', other
    tokens expand as the 6502 mnemonic followed by a single space (so the
    operand that follows in the binary is separated from the opcode).
    """
    out = []
    i = 0
    n = len(text_bytes)
    while i < n:
        b = text_bytes[i]
        if b == 0x2E and i + 1 < n and text_bytes[i + 1] in DIRECTIVES:
            # Dot-prefixed directive: .DEFINE / .BASE / .BYTE / ...
            out.append('.' + DIRECTIVES[text_bytes[i + 1]] + ' ')
            i += 2
        elif 0x81 <= b <= 0xB8:
            # 6502 mnemonic
            out.append(MNEMONICS[b - 0x81] + ' ')
            i += 1
        else:
            out.append(chr(b))
            i += 1
    return ''.join(out)


def format_line(line_text):
    """Format an assembler line with aligned columns.

    Layout (zero-indexed columns of the listing body, after the 'NNN  -' prefix):
      0..9    label   (left-justified, 10 chars; empty when none)
      10..12  opcode  (3 chars)
      13      space
      14..    operand
      25..    comment (';...') aligned when feasible
    """
    if not line_text:
        return line_text

    # Comment-only lines: leave as-is.
    if line_text.startswith(';'):
        return line_text

    # Directive lines (start with '.'): handle .DEFINE specially to align '='.
    if line_text.startswith('.'):
        # Strip the trailing space the tokenizer adds after '.DEFINE '.
        rest = line_text
        # Find a ';' that's not inside quotes
        semi = _find_comment(rest)
        body = rest[:semi] if semi != -1 else rest
        comment = rest[semi:] if semi != -1 else ''

        # .DEFINE NAME=$VALUE → '.DEFINE NAME    = $VALUE'
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
    # The tokenizer emitted a single space after every mnemonic and after
    # '.DEFINE'. Lines without a label start with one space (the original
    # PRG had a single space before the token byte).
    if line_text.startswith(' '):
        label = ''
        body = line_text[1:]
    else:
        # Label is the first whitespace-delimited token.
        space = line_text.find(' ')
        if space == -1:
            return line_text.rstrip()
        label = line_text[:space]
        body = line_text[space + 1:]

    # body now starts with 'OPC OPERAND;COMMENT' (with the space the
    # tokenizer inserted between OPC and OPERAND already present).
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


def _find_comment(s):
    """Return index of the first ';' that is not inside double quotes, or -1."""
    in_quotes = False
    for i, c in enumerate(s):
        if c == '"':
            in_quotes = not in_quotes
        elif c == ';' and not in_quotes:
            return i
    return -1


def decode_prg(filename):
    with open(filename, 'rb') as f:
        data = f.read()

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
    # Line number column: left-justified, padded to one beyond the widest
    # number, then '-' immediately followed by the line body. This matches
    # Hypra-Ass's own LIST output as reproduced in the magazine's print.
    num_col = max(3, len(str(max_line))) + 1

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

        expanded = decode_tokens(raw)
        formatted = format_line(expanded)
        print(f"{str(line_num).ljust(num_col)}-{formatted}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file.prg>", file=sys.stderr)
        sys.exit(1)
    decode_prg(sys.argv[1])
