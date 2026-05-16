#!/usr/bin/env python3
"""Decode raw Hypra-Ass PRG files (thin CLI wrapper).

The decoder logic lives in ``assembler_decode.decode_prg_bytes`` — this
script is kept for backwards compatibility with offline use; new callers
should import ``assembler_decode`` directly.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from assembler_decode import decode_prg_bytes


def decode_prg(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    for line in decode_prg_bytes(data):
        print(line)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file.prg>", file=sys.stderr)
        sys.exit(1)
    decode_prg(sys.argv[1])
