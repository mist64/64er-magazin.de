# Converter of PRG files into 64'er MSE (Maschinenspracheditor) formats.
# Based on
# https://codeberg.org/pgeorgi/render64prg/src/branch/main/src/64ermag-mse.ts
# by Patrick Georgi (ISC License)

import sys

class Memory:
    def __init__(self, data):
        self.data = data
    def byteAt(self, i):
        return self.data[i]

def intHex(v, width):
    return f"{v:0{width}X}"

def pad(s, length, ch='0'):
    return s.rjust(length, ch)

def splitString(s, length):
    return [s[i:i+length] for i in range(0, len(s), length)]

def rol8(b):
    b &= 0xff
    b = (b << 1) | (b >> 7)
    return b & 0xff

def mapToMSE2(bytes_):
    bitstr = "".join([pad(bin(b)[2:],8) for b in bytes_])
    chunks = splitString(bitstr,5)
    vals = [int(c,2) for c in chunks]
    charset = "7abcdefghijklmnopqrstuvwxyz23456"
    return "".join(charset[v] for v in vals)

def mapToMSEchksum(b):
    bin_ = pad(bin(b)[2:],8)
    upper = bin_[:5]
    lower = bin_[5:][::-1]
    bitstring = pad(lower,5) + upper + "000000"
    arr = [int(bitstring[i:i+8],2) for i in range(0,len(bitstring),8)]
    return mapToMSE2(arr)[:2]

def dumpDataLine(data, start, end, cur, dump, checksum):
    return [intHex(cur,4), dump(data), checksum(data, start, end, cur)]

def dumpFile(data, start, end, stride, fill, dump, checksum):
    result = []
    for cur in range(start, end, stride):
        buf_len = min(stride, end - cur)
        buf = [data.byteAt((cur - start) + i) for i in range(buf_len)]
        if not fill:
            buf = buf[:buf_len]
        result.append(dumpDataLine(buf, start, end, cur, dump, checksum))
    return result

def dumpMSE1(data, start, end):
    def dmp(d): return " ".join(intHex(b,2) for b in d)
    def chk(d, s, e, c):
        chksum = c & 0xff
        for i,b in enumerate(d):
            if c+i<e:
                chksum=(chksum+b)<<1
        chksum=((chksum>>8)+(chksum&0xff)+1)&0xff
        return intHex(chksum,2)
    return dumpFile(data, start, end, 8, False, dmp, chk)

def dumpMSE2(data, start, end):
    def dmp(d): return " ".join(splitString(mapToMSE2(d),4))
    def chk(d, s, e, c):
        val = (c & 0xff) ^ (0x1c + (c>>8) - (s>>8))
        for b in reversed(d):
            val = rol8(val+b)
        return mapToMSEchksum(val)
    return dumpFile(data, start, end, 15, True, dmp, chk)

def dumpMSE2_1(data, start, end):
    def dmp(d): return " ".join(splitString(mapToMSE2(d),4))
    def chk(d, s, e, c):
        val = (c & 0xff)
        for b in d:
            val = rol8(val+b)
        return mapToMSEchksum(val)
    return dumpFile(data, start, end, 15, True, dmp, chk)

def printHeader(filename, start, end, width):
    filename = filename.upper().removesuffix(".PRG")
    return [f"{filename.ljust(width-10)} {intHex(start,4)} {intHex(end,4)}",
            "-"*width]

def MSE1(filename, start, end, data):
    out = printHeader("PROGRAMM : "+filename, start, end, 35)
    for addr,dt,ch in dumpMSE1(data,start,end):
        line = (addr+" : "+dt).ljust(6+8*3+2)+" "+ch
        out.append(line)
    return out

def MSE2(filename, start, end, data):
    out = printHeader("PROGRAMM : "+filename, start, end, 38)
    for addr,dt,ch in dumpMSE2(data,start,end):
        out.append(f"{addr}: {dt} {ch}")
    return out

def MSE2_1(filename, start, end, data):
    out = printHeader("PROGRAMM : "+filename, start, end, 38)
    for addr,dt,ch in dumpMSE2_1(data,start,end):
        out.append(f"{addr}: {dt} {ch}")
    return out

MSEversions = {
    "mse1": MSE1,
    "mse2.0": MSE2,
    "mse2.1": MSE2_1
}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} FILE VERSION (one of: {', '.join(MSEversions.keys())})")
        sys.exit(1)

    fn, ver = sys.argv[1], sys.argv[2]
    with open(fn,"rb") as f:
        data = f.read()
    start = data[0] | (data[1] << 8)
    end = start + (len(data) - 2)
    mem = Memory(data[2:])
    lines = MSEversions[ver](fn, start, end, mem)
    for l in lines:
        print(l)
