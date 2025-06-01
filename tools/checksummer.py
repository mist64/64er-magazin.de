import string
import sys
import re
import itertools
from typing import Optional, Tuple


# approximating the overline / underline notation in the magazine
# uses overline/underline style decorators plus a PUA character
# for later translation into HTML entities.
def to_cbm(c: str) -> str:
    return "\u0346" + c + "\ue000"


def to_shift(c: str) -> str:
    return "\u033a" + c + "\ue000"


# With help from https://style64.org/petscii/
# and https://rvbelzen.tripod.com/spielekurs/eingabe.htm
encoding_64er = [
    # fmt:off
    "{NULL}", "{CTRL-A}", "{CTRL-B}", "{CTRL-C}", "{CTRL-D}", "{WHITE}", "{CTRL-F}", "{CTRL-G}",
    "{CTRL-H}", "{CTRL-I}", "{CTRL-J}", "{CTRL-K}", "{CTRL-L}", "{RETURN}", "{CTRL-N}", "{CTRL-O}",
    "{CTRL-P}", "{DOWN}", "{RVSON}", "{HOME}", "{DEL}", "{CTRL-U}", "{CTRL-V}", "{CTRL-W}",
    "{CTRL-X}", "{CTRL-Y}", "{CTRL-Z}", "{CTRL-}", "{RED}", "{RIGHT}", "{GREEN}", "{BLUE}",
    " ", "!", '"', "#", "$", "%", "&", "'",
    "(", ")", "*", "+", ",", "-", ".", "/",
    "0", "1", "2", "3", "4", "5", "6", "7",
    "8", "9", ":", ";", "<", "=", ">", "?",
    "@", "A", "B", "C", "D", "E", "F", "G",
    "H", "I", "J", "K", "L", "M", "N", "O",
    "P", "Q", "R", "S", "T", "U", "V", "W",
    "X", "Y", "Z", "[", "£", "]", "↑", "←",
    "━", "{$61}", "{$62}", "{$63}", "{$64}", "{$65}", "{$66}", "{$67}",
    "{$68}", "{$69}", "{$6a}", "{$6b}", "{$6c}", "{$6d}", "{$6e}", "{$6f}",
    "{$70}", "{$71}", "{$72}", "{$73}", "{$74}", "{$75}", "{$76}", "{$77}",
    "{$78}", "{$79}", "{$7a}", "╋", "🮌", "│", "π", "◥",
    "{$80}", "{ORANGE}", "{$82}", "{$83}", "{$84}", "{F1}", "{F3}", "{F5}",
    "{F7}", "{F2}", "{F4}", "{F6}", "{F8}", "{$8d}", "{$8e}", "{$8f}",
    "{BLACK}", "{UP}", "{RVOFF}", "{CLR}", "{INST}", "{BROWN}", "{LIG.RED}", "{GREY1}",
    "{GREY2}", "{LIG.GREEN}", "{LIG.BLUE}", "{GREY3}", "{PURPLE}", "{LEFT}", "{YELLOW}", "{CYAN}",
    "{SHIFT-SPACE}", to_cbm("K"), to_cbm("I"), to_cbm("T"), to_cbm("@"), to_cbm("G"), to_cbm("+"), to_cbm("M"),
    to_cbm("£"), to_shift("£"), to_cbm("N"), to_cbm("Q"), to_cbm("D"), to_cbm("Z"), to_cbm("S"), to_cbm("P"),
    to_cbm("A"), to_cbm("E"), to_cbm("R"), to_cbm("W"), to_cbm("H"), to_cbm("J"), to_cbm("L"), to_cbm("Y"),
    to_cbm("U"), to_cbm("O"), to_shift("@"), to_cbm("F"), to_cbm("C"), to_cbm("X"), to_cbm("V"), to_cbm("B"),
    to_shift("*"), to_shift("A"), to_shift("B"), to_shift("C"), to_shift("D"), to_shift("E"), to_shift("F"), to_shift("G"),
    to_shift("H"), to_shift("I"), to_shift("J"), to_shift("K"), to_shift("L"), to_shift("M"), to_shift("N"), to_shift("O"),
    to_shift("P"), to_shift("Q"), to_shift("R"), to_shift("S"), to_shift("T"), to_shift("U"), to_shift("V"), to_shift("W"),
    to_shift("X"), to_shift("Y"), to_shift("Z"), to_shift("+"), to_cbm("-"), to_shift("-"), "{$DE}", to_cbm("*"),
    "{$e0}", "{$e1}", "{$e2}", "{$e3}", "{$e4}", "{$e5}", "{$e6}", "{$e7}",
    "{$e8}", "{$e9}", "{$ea}", "{$eb}", "{$ec}", "{$ed}", "{$ee}", "{$ef}",
    "{$f0}", "{$f1}", "{$f2}", "{$f3}", "{$f4}", "{$f5}", "{$f6}", "{$f7}",
    "{$f8}", "{$f9}", "{$fa}", "{$fb}", "{$fc}", "{$fd}", "{$fe}", to_shift("↑"),
    # fmt:on
]

assert len(encoding_64er) == 256

tokens = {
    # BASIC 1.0 like on PET
    "1p": {
        "segments": [
            {
                "start": 0x80,
                "end": 0xCA,
                # fmt:off
                "tokens": [  # 0x80
                    "END", "FOR", "NEXT", "DATA", "INPUT#", "INPUT", "DIM", "READ",
                    "LET", "GOTO", "RUN", "IF", "RESTORE", "GOSUB", "RETURN", "REM",
                    # 0x90
                    "STOP", "ON", "WAIT", "LOAD", "SAVE", "VERIFY", "DEF", "POKE",
                    "PRINT#", "PRINT", "CONT", "LIST", "CLR", "CMD", "SYS", "OPEN",
                    # 0xa0
                    "CLOSE", "GET", "NEW", "TAB(", "TO", "FN", "SPC(", "THEN",
                    "NOT", "STEP", "+", "-", "*", "/", "^", "AND",
                    # 0xb0
                    "OR", ">", "=", "<", "SGN", "INT", "ABS", "USR",
                    "FRE", "POS", "SQR", "RND", "LOG", "EXP", "COS", "SIN",
                    # 0xc0
                    "TAN", "ATN", "PEEK", "LEN", "STR$", "VAL", "ASC", "CHR$",
                    "LEFT$", "RIGHT$", "MID$",
                ],
                # fmt:on
            }
        ]
    },
    "2": {
        "parent": "1p",
        "segments": [
            {
                "start": 0xCB,
                "end": 0xCB,
                "tokens": [
                    "GO",
                ],
            },
            {
                "start": 0xFF,
                "end": 0xFF,
                "tokens": [
                    "π",
                ],
            },
        ],
    },
    # BASIC 3.5
    "3": {
        "parent": "2",
        "segments": [
            {
                "start": 0xCC,
                "end": 0xFD,
                # fmt:off
                "tokens": [
                    # 0xcc
                    "RGR", "RCLR", "RLUM", "JOY",
                    # 0xd0
                    "RDOT", "DEC", "HEX$", "ERR$", "INSTR", "ELSE", "RESUME", "TRAP",
                    "TRON", "TROFF", "SOUND", "VOL", "AUTO", "PUDEF", "GRAPHIC", "PAINT",
                    # 0xe0
                    "CHAR", "BOX", "CIRCLE", "GSHAPE", "SSHAPE", "DRAW", "LOCATE", "COLOR",
                    "SCNCLR", "SCALE", "HELP", "DO", "LOOP", "EXIT", "DIRECTORY", "DSAVE",
                    # 0xf0
                    "DLOAD", "HEADER", "SCRATCH", "COLLECT", "COPY", "RENAME", "BACKUP", "DELETE",
                    "RENUMBER", "KEY", "MONITOR", "USING", "UNTIL", "WHILE",
                ],
                # fmt:on
            },
            {
                "start": 0xFF,
                "end": 0xFF,
                "tokens": [
                    None,  # no pi
                ],
            },
        ],
    },
    "7": {
        "parent": "3",
        "segments": [
            {
                "longtoken": 0xCE,
                "start": 0x02,
                "end": 0x0A,
                # fmt:off
                "tokens": [
                    # 0x02
	                "POT", "BUMP", "PEN", "RSPPOS", "RSPRITE", "RSPCOLOR",
	                "XOR", "RWINDOW", "POINTER",
                ],
                # fmt:on
            },
            {
                "longtoken": 0xFE,
                "start": 0x02,
                "end": 0x1F,
                # fmt:off
                "tokens": [
                    # 0x02
	               "BANK", "FILTER", "PLAY", "TEMPO", "MOVSPR", "SPRITE",
                   "SPRCOLOR", "RREG", "ENVELOPE", "SLEEP", "CATALOG", "DOPEN", "APPEND", "DCLOSE",
                   # 0x10
	               "BSAVE", "BLOAD", "RECORD", "CONCAT", "DVERIFY", "DCLEAR", "SPRSAV", "COLLISION",
                   "BEGIN", "BEND", "WINDOW", "BOOT", "WIDTH", "SPRDEF", "QUIT", "STASH",
                ],
                # fmt:on
            },
            {
                "longtoken": 0xFE,
                "start": 0x21,
                "end": 0x21,
                "tokens": [
                    "FETCH",
                ],
            },
            {
                "longtoken": 0xFE,
                "start": 0x23,
                "end": 0x26,
                # fmt:off
                "tokens": [
	                "SWAP", "OFF", "FAST", "SLOW",
                ],
                # fmt:on
            },
            {
                "start": 0xFF,
                "end": 0xFF,
                "tokens": [
                    "π",
                ],
            },
        ],
    },
    "simon": {
        "parent": "2",
        "segments": [
            {
                "longtoken": 0x64,
                "start": 0x01,
                "end": 0x21,
                # fmt:off
                "tokens": [
	                # 0x01
                    "HIRES", "PLOT", "LINE", "BLOCK", "FCHR", "FCOL", "FILL",
	                "REC", "ROT", "DRAW", "CHAR", "HI COL", "INV", "FRAC", "MOVE",
                    # 0x10
	                "PLACE", "UPB", "UPW", "LEFTW", "LEFTB", "DOWNB", "DOWNW", "RIGHTB",
	                "RIGHTW", "MULTI", "COLOUR", "MMOB", "BFLASH", "MOB SET", "MUSIC", "FLASH",
                    # 0x20
	                "REPEAT", "PLAY",
                ],
                # fmt:on
            },
            {
                "longtoken": 0x64,
                "start": 0x23,
                "end": 0x29,
                # fmt:off
                "tokens": [
	                "CENTRE", "ENVELOPE", "CGOTO", "WAVE", "FETCH",
	                "AT(", "UNTIL",
                ],
                # fmt:on
            },
            {
                "longtoken": 0x64,
                "start": 0x2C,
                "end": 0x2C,
                "tokens": [
                    "USE",
                ],
            },
            {
                "longtoken": 0x64,
                "start": 0x2E,
                "end": 0x2E,
                # fmt:off
                "tokens": [
                    "GLOBAL",
                ],
                # fmt:on
            },
            {
                "longtoken": 0x64,
                "start": 0x30,
                "end": 0x3B,
                # fmt:off
                "tokens": [
	                # 0x30
	                "RESET", "PROC", "CALL", "EXEC", "END PROC", "EXIT", "END LOOP", "ON KEY",
	                "DISABLE", "RESUME", "LOOP", "DELAY",
                ],
                # fmt:on
            },
            {
                "longtoken": 0x64,
                "start": 0x40,
                "end": 0x53,
                # fmt:off
                "tokens": [
	                # 0x40
	                "SECURE", "DISAPA", "CIRCLE", "ON ERROR", "NO ERROR", "LOCAL", "RCOMP", "ELSE",
	                "RETRACE", "TRACE", "DIR", "PAGE", "DUMP", "FIND", "OPTION", "AUTO",
                    # 0x50
	                "OLD", "JOY", "MOD", "DIV",
                ],
                # fmt:on
            },
            {
                "longtoken": 0x64,
                "start": 0x55,
                "end": 0x5D,
                # fmt:off
                "tokens": [
	                "DUP", "INKEY", "INST",
	                "TEST", "LIN", "EXOR", "INSERT", "POT", "PENX",
                ],
                # fmt:on
            },
            {
                "longtoken": 0x64,
                "start": 0x5F,
                "end": 0x7F,
                # fmt:off
                "tokens": [
                    "PENY",
	                # 0x60
	                "SOUND", "GRAPHICS", "DESIGN", "RLOCMOB", "CMOB", "BCKGNDS", "PAUSE", "NRM",
                    "MOB", "OFF", "ANGL", "ARC", "COLD", "SCRSV", "SCRLD", "TEXT",
                    # 0x70
	                "CSET", "VOL", "DISK", "HRDCPY", "KEY", "PAINT", "LOW COL", "COPY",
	                "MERGE", "RENUMBER", "MEM", "DETECT", "CHECK", "DISPLAY", "ERR", "OUT"
                ],
                # fmt:on
            },
        ],
    },
}


def detokenize(basicver: str, token: int, extratoken: int) -> (str, bool):
    langver = tokens[basicver]
    tblit = iter(langver["segments"])
    tbl = tblit.__next__()

    while True:
        islong = None
        if token == tbl.get("longtoken"):
            islong = token
            token = extratoken
        if islong == tbl.get("longtoken") and token >= tbl["start"] and token <= tbl["end"]:
            return tbl["tokens"][token - tbl["start"]], islong is not None
        try:
            tbl = tblit.__next__()
        except StopIteration:
            if "parent" not in langver:
                return chr(token), False
            langver = tokens[langver["parent"]]
            tblit = iter(langver["segments"])
            tbl = tblit.__next__()


def process_line(line: str) -> str:
    line = line.strip()

    # Handle spaces before control codes
    b = line
    c = ""
    while c != b:
        c = b
        b = b.replace("} ", "}{SPACE}").replace(" {", "{SPACE}{")
    nline = c

    # Make adjacent control codes more compact
    nline = nline.replace("}{", ",")

    # Handle duplicate control codes
    sequences = re.findall("{(.*?,.*?)}", nline)
    for s in sequences:
        uniq = [list(map(str, v)) for k, v in itertools.groupby(s.split(","))]
        short = ",".join(map(lambda i: f"{len(i)}{i[0]}" if len(i) > 1 else i[0], uniq))
        if short == s:
            continue
        nline = nline.replace(s, short, 1)

    return nline


def parse(
    prg: bytes, chksumver: int = 3, basicver: str = "2"
) -> list[tuple[int, str, int]]:
    base = 0
    data = prg
    res = []

    def read8(addr: int) -> int:
        return data[addr - base]

    def read16le(addr: int) -> int:
        return data[addr - base] + data[addr - base + 1] * 256

    def chksumv1v2(val: int, shift: int, b: int) -> Tuple[int, int]:
        if b == 0x20:
            return val, shift
        return val + b, shift

    def chksumv3(val: int, shift: int, b: int) -> Tuple[int, int]:
        if b == 0x20:
            return val, shift
        shift &= 7
        tmp = b << shift
        tmp |= b >> (8 - shift)
        return val + tmp, shift + 1

    if chksumver < 3:
        checksummer = chksumv1v2
    else:
        checksummer = chksumv3

    base = read16le(0)

    data = prg[2:]
    p = base
    while read16le(p) != 0:
        nextp = read16le(p)
        p += 2

        val = 0
        shift = 0
        lineno = read16le(p)
        # Not part of the loop because they're allowed to contain 0s
        val, shift = checksummer(val, shift, read8(p))
        val, shift = checksummer(val, shift, read8(p + 1))
        p += 2

        line = ""
        quoted = False

        while read8(p) != 0:
            b = read8(p)

            val, shift = checksummer(val, shift, b)
            if b == ord('"'):
                quoted = not quoted
                line += '"'
            elif quoted:
                if b == ord(' '):
                    if line[-1] == ' ':
                        line = line[:-1]+'{SPACE}{SPACE}'
                    elif line[-1] == '}':
                        line += '{SPACE}'
                    else:
                        line += " "
                else:
                    line += encoding_64er[b]
            else:
                token, skip = detokenize(basicver, b, read8(p + 1))
                if skip:
                    p += 1
                if token in ["TO", "THEN"]:
                    if line[-1] != 0x20:
                        line += " "
                elif len(token) > 1 and token[:5] not in ["INPUT", "PRINT"]:
                    if read8(p + 1) != 0x20:
                        token += " "
                line += token

            p += 1

        line = process_line(line)
        res.append((lineno, line, val & 0xFF))
        p = nextp
    return res


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} prg-file [checksummer version] [basicver]")
        sys.exit(1)

    prgfn = sys.argv[1]

    chksumver = 3
    if len(sys.argv) > 2:
        chksumver = int(sys.argv[2])

    basicver = "2"
    if len(sys.argv) > 3:
        basicver = sys.argv[3]

    with open(prgfn, "rb") as f:
        prg = f.read()

    listing = parse(prg, chksumver, basicver)

    for lineno, content, checksum in listing:
        print(f"{lineno} {content} <{checksum:03d}>")
