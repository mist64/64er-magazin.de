"""Score an OCR reading of 8611 p59's MSE hex listing against the VERIFIED binary.

issues/8611/prg/3d.code.prg is the hand-transcribed, checksum-satisfying program,
so it is absolute truth: every printed line "addr : b0..b7 cs" must equal the eight
bytes at that address. No judgement, no sampling -- a byte is right or it is not.
"""
import re, sys
PRG = open("/Users/mist/Documents/git/64er-magazin.de/issues/8611/prg/3d.code.prg","rb").read()
LOAD = PRG[0] | (PRG[1] << 8)

def truth(addr):
    off = addr - LOAD + 2
    return PRG[off:off+8] if 0 <= off <= len(PRG)-8 else None

LINE = re.compile(r'\b([0-9a-fA-F]{4})\s*[:;.]\s*((?:[0-9a-fA-F?£OlI]{2}[ \t]+){8}[0-9a-fA-F?£OlI]{2})')

def score(text, label):
    lines = bad_addr = ok = 0
    wrong_bytes = tot_bytes = 0
    seen = set()
    for m in LINE.finditer(text):
        a = int(m.group(1), 16)
        if a in seen: continue
        seen.add(a); lines += 1
        t = truth(a)
        if t is None: bad_addr += 1; continue
        got = m.group(2).split()[:8]
        tot_bytes += 8
        w = 0
        for i, g in enumerate(got):
            try: v = int(g, 16)
            except ValueError: w += 1; continue
            if v != t[i]: w += 1
        wrong_bytes += w
        if w == 0: ok += 1
    print(f"  {label:<22} lines parsed {lines:>3}   addr not in prg {bad_addr:>2}   "
          f"byte-perfect lines {ok:>3}/{lines-bad_addr if lines>bad_addr else 0}   "
          f"wrong bytes {wrong_bytes}/{tot_bytes}"
          + (f" = {100*wrong_bytes/tot_bytes:.2f}%" if tot_bytes else ""))
    return lines, ok, wrong_bytes, tot_bytes

if __name__ == "__main__":
    for path in sys.argv[1:]:
        score(open(path, encoding="utf-8", errors="replace").read(), path.split("/")[-1])
