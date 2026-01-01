#!/usr/bin/env python3
"""
Decoder for Heimo Ponnath's assembler source files.

These files use a custom encoding:
- Bytes < 0x20 are C64 screen codes for letters (0x01='A', 0x02='B', ..., 0x1A='Z')
  Add 0x40 to convert to ASCII
- Line separator is `` (two backticks) instead of newline
- First 2 bytes are the load address (skip them)

Output format uses standard assembler column layout:
- Label:   columns 0-11  (12 chars)
- Opcode:  columns 12-15
- Operand: columns 16-31 (20 chars total with opcode)
- Comment: column 32+

Usage: python3 ponnath-asm_convert.py input.prg > output.txt
"""

import sys

OPCODES = {
    'LDA', 'LDX', 'LDY', 'STA', 'STX', 'STY', 'TAX', 'TAY', 'TXA', 'TYA',
    'PHA', 'PLA', 'PHP', 'PLP', 'AND', 'ORA', 'EOR', 'ADC', 'SBC', 'CMP',
    'CPX', 'CPY', 'INC', 'DEC', 'INX', 'INY', 'DEX', 'DEY', 'ASL', 'LSR',
    'ROL', 'ROR', 'JMP', 'JSR', 'RTS', 'RTI', 'BEQ', 'BNE', 'BCS', 'BCC',
    'BMI', 'BPL', 'BVS', 'BVC', 'SEC', 'CLC', 'SED', 'CLD', 'SEI', 'CLI',
    'CLV', 'NOP', 'BRK', 'BIT',
    '.DE', '.BA', '.BY', '.OS', '.EN', '.AS', '.TE', '.WO',
    '.IF', '.EL', '.EI', '.MA', '.ME', '.OR'
}


def decode_screen_codes(data):
    """Convert screen codes to ASCII."""
    result = []
    for b in data:
        if b < 0x20:
            result.append(b + 0x40)
        else:
            result.append(b)
    return bytes(result).decode('latin-1')


def format_line(line):
    """Format a source line with proper column alignment."""
    line = line.rstrip()

    if not line:
        return ''

    # Pure comment line
    if line.startswith(';'):
        return line

    # Split off comment
    if ';' in line:
        code_part, comment = line.split(';', 1)
        comment = ';' + comment
    else:
        code_part = line
        comment = ''

    code_part = code_part.rstrip()
    tokens = code_part.split()

    if not tokens:
        return comment if comment else ''

    label = ''
    opcode = ''
    operand = ''

    # Check if first token is opcode or label
    if tokens[0].upper() in OPCODES or tokens[0].startswith('.'):
        opcode = tokens[0]
        if len(tokens) > 1:
            operand = ' '.join(tokens[1:])
    else:
        label = tokens[0]
        if len(tokens) > 1:
            opcode = tokens[1]
        if len(tokens) > 2:
            operand = ' '.join(tokens[2:])

    # Format: Label 12 chars, Opcode+Operand 20 chars, Comment
    label_field = label.ljust(12)

    if opcode:
        opcode_operand = opcode
        if operand:
            opcode_operand += ' ' + operand
        opcode_field = opcode_operand.ljust(20)
    else:
        opcode_field = ' ' * 20

    return (label_field + opcode_field + comment).rstrip()


def convert(input_file):
    """Convert a Ponnath assembler file to readable text."""
    with open(input_file, 'rb') as f:
        data = f.read()

    # Skip 2-byte load address
    data = data[2:]

    # Decode screen codes
    text = decode_screen_codes(data)

    # Split on `` line separator
    lines = text.split('``')

    # Format and output each line
    for line in lines:
        print(format_line(line))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} input.prg", file=sys.stderr)
        sys.exit(1)

    convert(sys.argv[1])
