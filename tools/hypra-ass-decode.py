#!/usr/bin/env python3
"""Decode Hypra-Ass PRG files (MS BASIC format, no tokens)."""

import sys

def decode_prg(filename):
    with open(filename, 'rb') as f:
        data = f.read()

    pos = 0

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

        # ASCII text until \0
        text = []
        while pos < len(data) and data[pos] != 0:
            text.append(chr(data[pos]))
            pos += 1
        pos += 1  # skip \0

        line_text = ''.join(text)
        inserted_space = False
        if line_text.startswith(' '):
            rest = line_text[1:]
            rest = rest[:3] + ' ' + rest[3:]
            line_text = ' ' * 10 + rest
            inserted_space = True
        elif not line_text.startswith('.') and not line_text.startswith(';'):
            space_pos = line_text.find(' ')
            if space_pos != -1:
                label = line_text[:space_pos]
                after = line_text[space_pos+1:]
                after = after[:3] + ' ' + after[3:]
                line_text = label.ljust(10) + after
                inserted_space = True

        if inserted_space:
            # Find ; outside quotes
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

        print(f"{line_num}  -{line_text}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file.prg>", file=sys.stderr)
        sys.exit(1)
    decode_prg(sys.argv[1])
