#!/bin/bash
# Disassemble C64 PRG file in SMON style using cpu_6502.txt
# Usage: disasm_prg.sh file.prg [cpu_6502.txt]

PRG="$1"
if [ -z "$PRG" ]; then echo "Usage: $0 file.prg [cpu_6502.txt]"; exit 1; fi

# Find cpu_6502.txt
CPU_FILE="${2:-}"
if [ -z "$CPU_FILE" ]; then
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    for p in "$SCRIPT_DIR/../issues/SH8508/prg/cpu_6502.txt" \
             "$SCRIPT_DIR/cpu_6502.txt" \
             "cpu_6502.txt"; do
        [ -f "$p" ] && { CPU_FILE="$p"; break; }
    done
fi
[ ! -f "$CPU_FILE" ] && { echo "Error: cpu_6502.txt not found" >&2; exit 1; }

# Convert PRG to hex stream
HEX=$(xxd -p "$PRG" | tr -d '\n' | tr 'a-f' 'A-F')

# Extract load address (little-endian) and code
LO=${HEX:0:2}; HI=${HEX:2:2}
LOAD_ADDR=$((16#$HI$LO))
CODE=${HEX:4}

awk -v load_addr="$LOAD_ADDR" -v code="$CODE" '
BEGIN {
    # Addressing mode -> instruction size
    sz["-"]=1; sz["A"]=1; sz["#d8"]=2; sz["a8"]=2; sz["a8,X"]=2; sz["a8,Y"]=2
    sz["(a8,X)"]=2; sz["(a8),Y"]=2; sz["a16"]=3; sz["a16,X"]=3; sz["a16,Y"]=3
    sz["(a16)"]=3; sz["r8"]=2
    in_opc = 0
}

/^\[opcodes\]/ { in_opc = 1; next }
/^\[/ && in_opc { in_opc = 0 }

in_opc && /^[0-9A-Fa-f][0-9A-Fa-f]/ {
    opc = toupper($1)
    mn = $2; md = $3
    # Strip * from illegal opcodes
    if (substr(mn,1,1) == "*") mn = substr(mn,2)
    if (md == "") md = "-"
    mnemonic[opc] = mn
    mode[opc] = md
}

END {
    pos = 0; len = length(code)
    while (pos < len) {
        pc = load_addr + int(pos/2)
        op = substr(code, pos+1, 2)

        if (!(op in mnemonic)) {
            # Unknown opcode - output as .BYTE
            printf ",%04X  %s        .BYTE %s\n", pc, op, op
            pos += 2; continue
        }

        mn = mnemonic[op]; md = mode[op]; size = sz[md]

        # Check we have enough bytes
        if (pos + size*2 > len) {
            printf ",%04X  %s        .BYTE %s\n", pc, op, op
            pos += 2; continue
        }

        # Build hex bytes string
        if (size == 1) {
            hx = op; b1 = ""; b2 = ""
        } else if (size == 2) {
            b1 = substr(code, pos+3, 2)
            hx = op " " b1
        } else {
            b1 = substr(code, pos+3, 2)
            b2 = substr(code, pos+5, 2)
            hx = op " " b1 " " b2
        }

        # Format operand based on addressing mode
        if (md == "-" || md == "A") {
            operand = ""
        } else if (md == "#d8") {
            operand = "#" b1
        } else if (md == "a8") {
            operand = "   " b1
        } else if (md == "a8,X") {
            operand = "   " b1 ",X"
        } else if (md == "a8,Y") {
            operand = "   " b1 ",Y"
        } else if (md == "(a8,X)") {
            operand = "(" b1 ",X)"
        } else if (md == "(a8),Y") {
            operand = "(" b1 "),Y"
        } else if (md == "a16") {
            operand = b2 b1
        } else if (md == "a16,X") {
            operand = b2 b1 ",X"
        } else if (md == "a16,Y") {
            operand = b2 b1 ",Y"
        } else if (md == "(a16)") {
            operand = "(" b2 b1 ")"
        } else if (md == "r8") {
            # Relative branch: signed offset from PC+2
            off = 0
            c1 = substr(b1,1,1); c2 = substr(b1,2,1)
            for (i=1; i<=2; i++) {
                c = (i==1) ? c1 : c2
                if (c ~ /[0-9]/) v = c+0
                else if (c == "A") v = 10
                else if (c == "B") v = 11
                else if (c == "C") v = 12
                else if (c == "D") v = 13
                else if (c == "E") v = 14
                else if (c == "F") v = 15
                off = off * 16 + v
            }
            if (off >= 128) off = off - 256
            target = pc + 2 + off
            operand = sprintf("%04X", target)
        }

        # Build instruction string
        instr = mn
        if (operand != "") instr = instr " " operand

        printf ",%04X  %-8s  %s\n", pc, hx, instr
        pos += size * 2
    }
}
' "$CPU_FILE"
