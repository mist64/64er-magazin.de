import string
import sys
import re
import itertools
from typing import Optional, Tuple


# approximating the overline / underline notation in the magazine
def to_cbm(c: str) -> str:
    return "\u0346" + c


def to_shift(c: str) -> str:
    return "\u033a" + c


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
    "@", "a", "b", "c", "d", "e", "f", "g",
    "h", "i", "j", "k", "l", "m", "n", "o",
    "p", "q", "r", "s", "t", "u", "v", "w",
    "x", "y", "z", "[", "£", "]", "↑", "←",
    "━", "{$61}", "{$62}", "{$63}", "{$64}", "{$65}", "{$66}", "{$67}",
    "{$68}", "{$69}", "{$6a}", "{$6b}", "{$6c}", "{$6d}", "{$6e}", "{$6f}",
    "{$70}", "{$71}", "{$72}", "{$73}", "{$74}", "{$75}", "{$76}", "{$77}",
    "{$78}", "{$79}", "{$7a}", "╋", "🮌", "│", "π", "◥",
    "{$80}", "{ORANGE}", "{$82}", "{$83}", "{$84}", "{F1}", "{F3}", "{F5}",
    "{F7}", "{F2}", "{F4}", "{F6}", "{F8}", "{$8d}", "{$8e}", "{$8f}",
    "{BLACK}", "{UP}", "{RVOFF}", "{CLR}", "{INST}", "{BROWN}", "{LIG.RED}", "{GREY1}",
    "{GREY2}", "{LIG.GREEN}", "{LIG.BLUE}", "{GREY3}", "{PURPLE}", "{LEFT}", "{YELLOW}", "{CYAN}",
    "{SHIFT-SPACE}", to_cbm("k"), to_cbm("i"), to_cbm("t"), to_cbm("@"), to_cbm("g"), to_cbm("+"), to_cbm("m"),
    to_cbm("£"), to_shift("£"), to_cbm("n"), to_cbm("q"), to_cbm("d"), to_cbm("z"), to_cbm("s"), to_cbm("p"),
    to_cbm("a"), to_cbm("e"), to_cbm("r"), to_cbm("w"), to_cbm("h"), to_cbm("j"), to_cbm("l"), to_cbm("y"),
    to_cbm("u"), to_cbm("o"), to_shift("@"), to_cbm("f"), to_cbm("c"), to_cbm("x"), to_cbm("v"), to_cbm("b"),
    to_shift("*"), to_shift("a"), to_shift("b"), to_shift("c"), to_shift("d"), to_shift("e"), to_shift("f"), to_shift("g"),
    to_shift("h"), to_shift("i"), to_shift("j"), to_shift("k"), to_shift("l"), to_shift("m"), to_shift("n"), to_shift("o"),
    to_shift("p"), to_shift("q"), to_shift("r"), to_shift("s"), to_shift("t"), to_shift("u"), to_shift("v"), to_shift("w"),
    to_shift("x"), to_shift("y"), to_shift("z"), to_shift("+"), to_cbm("-"), to_shift("-"), "{$de}", to_cbm("*"),
    "{$e0}", "{$e1}", "{$e2}", "{$e3}", "{$e4}", "{$e5}", "{$e6}", "{$e7}",
    "{$e8}", "{$e9}", "{$ea}", "{$eb}", "{$ec}", "{$ed}", "{$ee}", "{$ef}",
    "{$f0}", "{$f1}", "{$f2}", "{$f3}", "{$f4}", "{$f5}", "{$f6}", "{$f7}",
    "{$f8}", "{$f9}", "{$fa}", "{$fb}", "{$fc}", "{$fd}", "{$fe}", to_shift("↑"),
    # fmt:on
]

assert len(encoding_64er) == 256

encoding_petcat = [
    # fmt:off
    "{null}", "{CTRL-A}", "{CTRL-B}", "{stop}", "{CTRL-D}", "{wht}", "{CTRL-F}", "{CTRL-G}",
    "{dish}", "{ensh}", "{$0a}", "{CTRL-K}", "{\\f}", "{\\n}", "{swlc}", "{CTRL-O}",
    "{CTRL-P}", "{down}", "{rvon}", "{home}", "{del}", "{CTRL-U}", "{CTRL-V}", "{CTRL-W}",
    "{CTRL-X}", "{CTRL-Y}", "{CTRL-Z}", "{esc}", "{red}", "{rght}", "{grn}", "{blu}",
    " ", "!", '"', "#", "$", "%", "&", "'",
    "(", ")", "*", "+", ",", "-", ".", "/",
    "0", "1", "2", "3", "4", "5", "6", "7",
    "8", "9", ":", ";", "<", "=", ">", "?",
    "@", "a", "b", "c", "d", "e", "f", "g",
    "h", "i", "j", "k", "l", "m", "n", "o",
    "p", "q", "r", "s", "t", "u", "v", "w",
    "x", "y", "z", "[", "{pound}", "]", "^", "_",
    "{$60}", "{$61}", "{$62}", "{$63}", "{$64}", "{$65}", "{$66}", "{$67}",
    "{$68}", "{$69}", "{$6a}", "{$6b}", "{$6c}", "{$6d}", "{$6e}", "{$6f}",
    "{$70}", "{$71}", "{$72}", "{$73}", "{$74}", "{$75}", "{$76}", "{$77}",
    "{$78}", "{$79}", "{$7a}", "{$7b}", "{$7c}", "{$7d}", "{$7e}", "{$7f}",
    "{$80}", "{orng}", "{$82}", "{$83}", "{$84}", "{f1}", "{f3}", "{f5}",
    "{f7}", "{f2}", "{f4}", "{f6}", "{f8}", "{stret}", "{swuc}", "{$8f}",
    "{blk}", "{up}", "{rvof}", "{clr}", "{inst}", "{brn}", "{lred}", "{gry1}",
    "{gry2}", "{lgrn}", "{lblu}", "{gry3}", "{pur}", "{left}", "{yel}", "{cyn}",
    "{$a0}", "{CBM-K}", "{CBM-I}", "{CBM-T}", "{CBM-@}", "{CBM-G}", "{CBM-+}", "{CBM-M}",
    "{CBM-POUND}", "{SHIFT-POUND}", "{CBM-N}", "{CBM-Q}", "{CBM-D}", "{CBM-Z}", "{CBM-S}", "{CBM-P}",
    "{CBM-A}", "{CBM-E}", "{CBM-R}", "{CBM-W}", "{CBM-H}", "{CBM-J}", "{CBM-L}", "{CBM-Y}",
    "{CBM-U}", "{CBM-O}", "{SHIFT-@}", "{CBM-F}", "{CBM-C}", "{CBM-X}", "{CBM-V}", "{CBM-B}",
    "{SHIFT-*}", "A", "B", "C", "D", "E", "F", "G",
    "H", "I", "J", "K", "L", "M", "N", "O",
    "P", "Q", "R", "S", "T", "U", "V", "W",
    "X", "Y", "Z", "{SHIFT-+}", "{CBM--}", "{SHIFT--}", "{$de}", "{CBM-*}",
    "{$e0}", "{$e1}", "{$e2}", "{$e3}", "{$e4}", "{$e5}", "{$e6}", "{$e7}",
    "{$e8}", "{$e9}", "{$ea}", "{$eb}", "{$ec}", "{$ed}", "{$ee}", "{$ef}",
    "{$f0}", "{$f1}", "{$f2}", "{$f3}", "{$f4}", "{$f5}", "{$f6}", "{$f7}",
    "{$f8}", "{$f9}", "{$fa}", "{$fb}", "{$fc}", "{$fd}", "{$fe}", "~",
    # fmt:on
]
assert len(encoding_petcat) == 256

map_petcat_64er = dict(zip(encoding_petcat, encoding_64er))

map_petcat_64er_singles = dict(
    map(
        lambda k: (k, map_petcat_64er[k]),
        filter(lambda x: len(x) == 1 and (x < "A" or x > "Z") and map_petcat_64er[x] != x, encoding_petcat),
    )
)

def map_shift(s: str) -> str:
    for c in string.ascii_uppercase:
        s = s.replace(c, to_shift(c))
    return s


def calculate_checksums(prg: bytes, version: int) -> dict[int, int]:
    base = 0
    data = prg
    res = {}

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

    if version < 3:
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
        while read8(p) != 0:
            val, shift = checksummer(val, shift, read8(p))
            p += 1
        res[lineno] = val & 0xFF
        p = nextp
    return res


def process_line(line: str) -> tuple[int, str] | tuple[None, None]:
    line = line.strip()

    # 64er doesn't have petcat comments, also skip empty lines
    if len(line) == 0 or line[0] == ";":
        return None, None

    # Replace the single character differences that can appear outside strings
    for k in map_petcat_64er_singles:
        line = line.replace(k, map_petcat_64er_singles[k])

    _lineno, *_content = line.strip().split(" ")
    lineno = int(_lineno)
    line = " ".join(_content)

    # no strings? no pain.
    if not '"' in line:
        return lineno, line.upper()

    parts = line.split('"')
    newparts = []
    quotes = False
    for part in parts:
        if quotes:
            special = part.split("{")
            if len(special) > 1:
                tmp = map_shift(special[0])
                for seg in special[1:]:
                    seg = "{" + seg
                    lenspecial = seg.find("}")
                    tmp += map_petcat_64er[seg[: lenspecial + 1]]
                    tmp += map_shift(seg[lenspecial + 1 :])
                part = tmp

        newparts += [part]
        quotes = not quotes
    nline = '"'.join(newparts)
    nline = nline.upper()

    # Handle spaces adjacent to control codes
    nline = nline.replace("} ", "}{SPACE}")
    b = nline
    c = ""
    while c != b:
        c = b
        b = b.replace("} ", "}{SPACE}").replace(" {", "{SPACE}{")
    nline = c

    # Make adjacent control codes more compact
    nline = nline.replace("}{", ",")

    # Handle duplicate control codes
    sequences = set(re.findall("{(.*?,.*?)}", nline))
    for s in sequences:
        uniq = [list(map(str, v)) for k, v in itertools.groupby(s.split(","))]
        short = ",".join(map(lambda i: f"{len(i)}{i[0]}" if len(i) > 1 else i[0], uniq))
        nline = nline.replace(s, short)

    return lineno, nline


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} petcat-source prg-file [checksummer version]")
        sys.exit(1)

    srcfn, prgfn = sys.argv[1], sys.argv[2]

    chksumver = 3
    if len(sys.argv) > 4:
        checksumver = int(sys.argv[3])

    with open(prgfn, "rb") as f:
        prg = f.read()

    checksums = calculate_checksums(prg, chksumver)

    for line in open(srcfn).readlines():
        lineno, content = process_line(line)
        if lineno is not None:
            checksum = checksums[lineno]
            print(f"{lineno} {content} <{checksum:03d}>")
