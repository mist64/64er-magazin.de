import re,io,glob,os,sys
# 6502 opcode table: opcode -> (mnemonic, operand-bytes, format)
import subprocess, tempfile

# DISASSEMBLY IS DELEGATED TO da65 (cc65).  A hand-rolled opcode table is one
# more thing that can be wrong -- and mine WAS: it had no indirect-addressing
# case, which produced 12 phantom findings on SH8601 before anyone noticed.
# da65 is the reference implementation; if it disagrees with the page, the page
# is what needs looking at.
DA65 = "da65"

def disasm(addr, byts):
    """One instruction at `addr` from `byts` -> normalised text, or None."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as fh:
        fh.write(bytes(byts)); path = fh.name
    try:
        out = subprocess.run([DA65, "--start-addr", hex(addr), path],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return None
    finally:
        os.unlink(path)
    for ln in out.splitlines():
        ln = ln.strip()
        # da65 emits `L795C := $795C` for targets outside the loaded bytes --
        # a symbol definition, not an instruction.  Skipping these was NOT
        # optional: without it every jsr/branch reported a phantom mismatch.
        if not ln or ln.startswith(";") or ln.startswith(".") or ":=" in ln: continue
        ln = re.sub(r"^L[0-9A-Fa-f]{4}:\s*", "", ln)      # drop a leading label
        if not ln: continue
        ln = re.sub(r"\bL([0-9A-Fa-f]{4})\b", r"$\1", ln)  # branch target -> $addr
        return re.sub(r"\s+", " ", ln).lower().replace(" ", "")
    return None

LINE=re.compile(r'^\s*[a.]?\s*([0-9a-fA-FlO]{4,5})\s+((?:[0-9a-fA-FlOSB][0-9a-fA-FlOSB][.,]?\s+){1,3})([a-zA-Z0-9]{3})\b(.*)$')
def norm(h): return h.lower().rstrip('.,').replace('l','1').replace('o','0').replace('s','5').replace('b','b')

def check(path):
    s=io.open(path,encoding='utf-8').read()
    out=[]; skipped=[]
    for pm in re.finditer(r'<pre(?![^>]*data-filename)[^>]*>(.*?)</pre>', s, re.S):
        blk=re.sub(r'<[^>]+>','',pm.group(1))
        prev=None
        for raw in blk.split('\n'):
            m=LINE.match(raw)
            if not m:
                t=raw.strip()
                # A line that LOOKS like a dump but will not parse is itself a
                # finding: silence is this checker's only real failure mode.
                # Guard against VALUE TABLES, which look like dumps but are not:
                # `4098 $1002 8D 80 00 00 00` is a decimal/hex row, and its
                # second column starting with `$` is the tell.  Without this the
                # table rows are reported as unreadable dump lines.
                # An ASSEMBLER SOURCE listing numbers its lines like BASIC and
                # comments them with ';' (`1003 ; -- KOPIEREN --`). That is a
                # comment line, not an unreadable dump line.
                if re.match(r'^[a.]?\s*[0-9a-fA-FlO]{4,5}\s*;', t): continue
                # An address followed by NO hex bytes is an annotation line in
                # the dump's comment column (`0c042   rechte Grenze low-Byte`),
                # not an unreadable instruction. Require at least one byte-shaped
                # token before calling a line unparseable.
                tail = re.sub(r'^[a.]?\s*[0-9a-fA-FlO]{4,5}\s*', '', t)
                if not re.match(r'(?:[0-9a-fA-FlOSB]{2}[.,]?\s+){1,}', tail + ' '): continue
                if re.match(r'^[a.]?\s*[0-9a-fA-FlO]{4,5}\s', t) and not re.match(r'^\d{3,5}\s+[A-Z"$]', t):
                    skipped.append((path,t,"UNPARSEABLE — read this line on the page"))
                continue
            addr,byts,mn,rest=m.groups()
            try: a=int(norm(addr),16)
            except: continue
            bs=[b for b in byts.split()]
            try: bb=[int(norm(b),16) for b in bs]
            except: continue
            if not re.search(r'[a-zA-Z]', mn): continue   # pure-digit run, not a mnemonic
            exp = disasm(a, bb)
            if exp is None:
                out.append((path,raw.strip(),"da65 could not disassemble these bytes")); continue
            # CUT THE COMMENT COLUMN. Many printed dumps annotate each line
            # (`20 fd ae jsr $aefd  Test auf Komma`), and the comment is not part
            # of the instruction. An operand never contains two spaces in a row,
            # so the column gap is the boundary; `;` also starts one. Without
            # this, every annotated line is a phantom finding: 203 of 8611's 205.
            # A 6502 OPERAND NEVER CONTAINS A SPACE, and always opens with $, #
            # or '(' in these dumps ('a' for accumulator mode). Anything else in
            # that position is the comment column, which matters most for the
            # instructions that take NO operand: in `lsr     Maus nach oben ?`
            # a naive split makes "Maus nach oben ?" the operand.
            first = (rest.strip().split() or [''])[0]
            operand = first if re.match(r'^[#$(]|^[aA]$', first) else ''
            printed = re.sub(r'\s+','', (mn+operand).strip().lower())
            # da65 writes ABSOLUTE operands in assembler shorthand and drops a
            # zero high byte: `99 fb 00` (STA abs,y -- there IS no zp,y form for
            # $99) renders as `sta $fb,y`, where the C128 monitor prints all
            # four digits, `sta $00fb,y`.  Same instruction, different syntax.
            # Pad da65's operand back to four digits for 3-byte encodings before
            # comparing, or every such line is a phantom finding.
            if len(bb) == 3:
                exp = re.sub(r'\$([0-9a-f]{2})\b', lambda m: '$00'+m.group(1), exp)
            # ACCUMULATOR ADDRESSING: da65 writes `lsr a`, the printed dumps
            # write a bare `lsr`. Same instruction, different syntax, like the
            # $00fb case above.
            if exp == printed + 'a' and mn.lower() in ('asl','lsr','rol','ror'):
                exp = printed
            if printed != exp:
                out.append((path,raw.strip(),f"bytes say  {exp}"))
            if prev is not None and a!=prev:
                out.append((path,raw.strip(),f"address gap: expected {prev:05x}"))
            prev = a + len(bb)
    return out+skipped
# THE ISSUE DIRECTORY COMES FROM argv, like every other tool in the chain.
# This was hardcoded to SH8601 and ignored its argument, so running it on any
# other issue silently cross-checked SH8601 and printed ITS findings as though
# they were yours. Same class as r280's hardcoded canary.
import r000_issue
from r000_issue import ISSUE
ISSUE_DIR = sys.argv[1] if len(sys.argv) > 1 else r000_issue.load(ISSUE).issue_dir
tot=[]
for f in sorted(glob.glob(os.path.join(ISSUE_DIR, '*.html'))):
    tot+=check(f)
print(f"issue dir: {ISSUE_DIR}")
print(f"cross-check findings: {len(tot)}\n")
cur=None
for p,line,why in tot:
    b=os.path.basename(p)
    if b!=cur: print(f"--- {b}"); cur=b
    print(f"  {line[:52]:54} {why}")
