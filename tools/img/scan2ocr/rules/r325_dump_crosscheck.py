import re,io,glob,os,sys
# 6502 opcode table: opcode -> (mnemonic, operand-bytes, format)
OPS={}
def add(o,m,n,f): OPS[o]=(m,n,f)
rows="""69 adc 1 imm|65 adc 1 zp|75 adc 1 zpx|6d adc 2 abs|7d adc 2 absx|79 adc 2 absy|61 adc 1 indx|71 adc 1 indy
29 and 1 imm|25 and 1 zp|35 and 1 zpx|2d and 2 abs|3d and 2 absx|39 and 2 absy|21 and 1 indx|31 and 1 indy
0a asl 0 acc|06 asl 1 zp|16 asl 1 zpx|0e asl 2 abs|1e asl 2 absx
90 bcc 1 rel|b0 bcs 1 rel|f0 beq 1 rel|30 bmi 1 rel|d0 bne 1 rel|10 bpl 1 rel|50 bvc 1 rel|70 bvs 1 rel
24 bit 1 zp|2c bit 2 abs|00 brk 0 imp|18 clc 0 imp|d8 cld 0 imp|58 cli 0 imp|b8 clv 0 imp
c9 cmp 1 imm|c5 cmp 1 zp|d5 cmp 1 zpx|cd cmp 2 abs|dd cmp 2 absx|d9 cmp 2 absy|c1 cmp 1 indx|d1 cmp 1 indy
e0 cpx 1 imm|e4 cpx 1 zp|ec cpx 2 abs|c0 cpy 1 imm|c4 cpy 1 zp|cc cpy 2 abs
c6 dec 1 zp|d6 dec 1 zpx|ce dec 2 abs|de dec 2 absx|ca dex 0 imp|88 dey 0 imp
49 eor 1 imm|45 eor 1 zp|55 eor 1 zpx|4d eor 2 abs|5d eor 2 absx|59 eor 2 absy|41 eor 1 indx|51 eor 1 indy
e6 inc 1 zp|f6 inc 1 zpx|ee inc 2 abs|fe inc 2 absx|e8 inx 0 imp|c8 iny 0 imp
4c jmp 2 abs|6c jmp 2 ind|20 jsr 2 abs
a9 lda 1 imm|a5 lda 1 zp|b5 lda 1 zpx|ad lda 2 abs|bd lda 2 absx|b9 lda 2 absy|a1 lda 1 indx|b1 lda 1 indy
a2 ldx 1 imm|a6 ldx 1 zp|b6 ldx 1 zpy|ae ldx 2 abs|be ldx 2 absy
a0 ldy 1 imm|a4 ldy 1 zp|b4 ldy 1 zpx|ac ldy 2 abs|bc ldy 2 absx
4a lsr 0 acc|46 lsr 1 zp|56 lsr 1 zpx|4e lsr 2 abs|5e lsr 2 absx|ea nop 0 imp
09 ora 1 imm|05 ora 1 zp|15 ora 1 zpx|0d ora 2 abs|1d ora 2 absx|19 ora 2 absy|01 ora 1 indx|11 ora 1 indy
48 pha 0 imp|08 php 0 imp|68 pla 0 imp|28 plp 0 imp
2a rol 0 acc|26 rol 1 zp|36 rol 1 zpx|2e rol 2 abs|3e rol 2 absx
6a ror 0 acc|66 ror 1 zp|76 ror 1 zpx|6e ror 2 abs|7e ror 2 absx
40 rti 0 imp|60 rts 0 imp
e9 sbc 1 imm|e5 sbc 1 zp|f5 sbc 1 zpx|ed sbc 2 abs|fd sbc 2 absx|f9 sbc 2 absy|e1 sbc 1 indx|f1 sbc 1 indy
38 sec 0 imp|f8 sed 0 imp|78 sei 0 imp
85 sta 1 zp|95 sta 1 zpx|8d sta 2 abs|9d sta 2 absx|99 sta 2 absy|81 sta 1 indx|91 sta 1 indy
86 stx 1 zp|96 stx 1 zpy|8e stx 2 abs|84 sty 1 zp|94 sty 1 zpx|8c sty 2 abs
aa tax 0 imp|a8 tay 0 imp|ba tsx 0 imp|8a txa 0 imp|9a txs 0 imp|98 tya 0 imp"""
for part in rows.replace('\n','|').split('|'):
    p=part.split()
    if len(p)==4: add(p[0],p[1],int(p[2]),p[3])

def fmt(m,f,ops,pc):
    if f=='imp': return m
    if f=='acc': return m
    if f=='imm': return f"{m} #${ops[0]:02x}"
    if f=='zp':  return f"{m} ${ops[0]:02x}"
    if f=='zpx': return f"{m} ${ops[0]:02x},x"
    if f=='zpy': return f"{m} ${ops[0]:02x},y"
    if f=='rel': 
        d=ops[0]-256 if ops[0]>127 else ops[0]
        return f"{m} ${(pc+2+d)&0xffff:04x}"
    a=ops[0]|(ops[1]<<8)
    return {'abs':f"{m} ${a:04x}",'absx':f"{m} ${a:04x},x",'absy':f"{m} ${a:04x},y",'ind':f"{m} (${a:04x})"}[f]

# Mnemonic is deliberately PERMISSIVE: the whole point is to catch `1da` for
# `lda` and `bp1` for `bpl`, so a strict [a-zA-Z] pattern would skip exactly the
# damaged lines.  Byte tokens tolerate a trailing stray period/comma.
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
                if re.match(r'^[a.]?\s*[0-9a-fA-FlO]{4,5}\s', t) and not re.match(r'^\d{3,5}\s+[A-Z"]', t):
                    skipped.append((path,t,"UNPARSEABLE — read this line on the page"))
                continue
            addr,byts,mn,rest=m.groups()
            try: a=int(norm(addr),16)
            except: continue
            bs=[b for b in byts.split()]
            try: bb=[int(norm(b),16) for b in bs]
            except: continue
            if not re.search(r'[a-zA-Z]', mn): continue   # pure-digit run, not a mnemonic
            op=OPS.get(f"{bb[0]:02x}")
            printed=(mn+rest).strip().lower()
            printed=re.sub(r'\s+',' ',printed)
            if op is None:
                out.append((path,raw.strip(),"opcode %02x unknown"%bb[0])); continue
            m2,n,f=op
            if len(bb)!=n+1:
                out.append((path,raw.strip(),f"{bb[0]:02x} ({m2}) takes {n} operand byte(s), {len(bb)-1} printed")); continue
            try: exp=fmt(m2,f,bb[1:],a)
            except Exception: continue
            pn=printed.replace(' ','').replace('$','$')
            en=exp.replace(' ','')
            if pn!=en:
                out.append((path,raw.strip(),f"bytes say  {exp}"))
            if prev is not None and a!=prev:
                out.append((path,raw.strip(),f"address gap: expected {prev:05x}"))
            prev=a+n+1
    return out+skipped
tot=[]
for f in sorted(glob.glob('/Users/mist/Documents/git/64er-magazin.de/issues/SH8601/*.html')):
    tot+=check(f)
print(f"cross-check findings: {len(tot)}\n")
cur=None
for p,line,why in tot:
    b=os.path.basename(p)
    if b!=cur: print(f"--- {b}"); cur=b
    print(f"  {line[:52]:54} {why}")
