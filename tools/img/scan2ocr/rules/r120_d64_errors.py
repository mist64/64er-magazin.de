#!/usr/bin/env python3
"""Report a .D64's read errors, and whether they touch anything.

WHY THIS EXISTS: `c1541 <img> -extract` says NOTHING about read errors.  On
SH8604's SH04C -- a disk with two bad sectors -- it printed four informational
lines, exited 0, and extracted the files.  `tools/prg_links.sh` additionally
sent its output to /dev/null, so even those four lines were discarded, and the
build learned about the damage from somewhere else entirely.

Nor can the extracted file COUNT stand in for the check: `c1541 -list | grep
-c '"'` reads 48 on the healthy SH03A against 27 files extracted, because the
listing counts the disk-name line and entry types -extract does not write.  A
count comparison flags a good disk.

THE SIGNAL IS IN THE IMAGE.  A 35-track D64 is 683 sectors x 256 = 174848
bytes.  An image written by a tool that recorded read errors carries one extra
STATUS BYTE PER SECTOR appended, so 174848 + 683 = 175531; 1 means OK, 0 means
no status recorded, and anything else is that sector's 1541 error code.
Measured over the Sonderheft disks on hand: six are 174848 and carry no error
info at all, and SH04C is 175531 with exactly 2 sectors at code 5.

A bad sector only matters if something USES it, so this also reads the BAM and
says whether each one is allocated.  SH04C's two are both free, which is why
nothing was lost -- but that is a conclusion somebody has to be handed, not
one to assume from a silent extract.

Usage:
    r120_d64_errors.py <image.d64> [<image.d64> ...]

Exit 1 if any image has a bad sector that is ALLOCATED, 0 otherwise.
"""

import os
import sys

# sectors per track, 1-based: 1-17 -> 21, 18-24 -> 19, 25-30 -> 18, 31-40 -> 17
def sectors_per_track(t):
    if t <= 17:
        return 21
    if t <= 24:
        return 19
    if t <= 30:
        return 18
    return 17


def layout(tracks):
    """[(track, sector)] in image order."""
    return [(t, s) for t in range(1, tracks + 1)
            for s in range(sectors_per_track(t))]


# 1541 error codes as c1541 and the drive ROM use them.  2-11 are the drive's
# own numbering; the ones this corpus has actually met are named.
ERRORS = {
    1:  'OK',
    2:  '20 header block not found',
    3:  '21 no sync character',
    4:  '22 data block not present',
    5:  '23 checksum error in data block',
    6:  '24 write verify error',
    7:  '25 write verify error',
    8:  '26 write protect on',
    9:  '27 checksum error in header block',
    10: '28 write error',
    11: '29 disk ID mismatch',
    15: '74 drive not ready',
}


def bam_free(data, track, sector, bam_off):
    """True when the BAM marks this sector FREE."""
    # BAM: track 18 sector 0, 4 bytes per track from offset 4
    #      byte 0 = free count, bytes 1-3 = bitmap, bit set == free
    e = bam_off + 4 + (track - 1) * 4
    if e + 4 > len(data):
        return None
    bits = data[e + 1:e + 4]
    return bool(bits[sector // 8] & (1 << (sector % 8)))


def report(path):
    data = open(path, 'rb').read()
    n = len(data)
    name = os.path.basename(path)
    for tracks in (35, 40):
        plain = len(layout(tracks)) * 256
        if n == plain:
            print('  %-14s %7d bytes, %d tracks, NO error info recorded'
                  % (name, n, tracks))
            return 0
        if n == plain + len(layout(tracks)):
            break
    else:
        print('  %-14s %7d bytes -- not a size this knows; check the image'
              % (name, n))
        return 0

    secs = layout(tracks)
    status = data[plain:]
    # the BAM lives at track 18 sector 0
    bam_off = 256 * secs.index((18, 0))
    bad = [(secs[i], st) for i, st in enumerate(status) if st not in (0, 1)]
    if not bad:
        print('  %-14s %7d bytes, %d tracks, error info present, 0 bad sectors'
              % (name, n, tracks))
        return 0

    allocated = 0
    print('  %-14s %7d bytes, %d tracks, %d BAD SECTOR(S):'
          % (name, n, tracks, len(bad)))
    for (t, s), st in bad:
        free = bam_free(data, t, s, bam_off)
        where = 'free' if free else ('ALLOCATED' if free is False else '?')
        if free is False:
            allocated += 1
        print('      track %2d sector %2d  code %-2d %-34s %s'
              % (t, s, st, ERRORS.get(st, 'unknown code'), where))
    if allocated:
        print('      -> %d of them hold data: something IS damaged, and the'
              % allocated)
        print('         extracted .prg files need checking against the print.')
    else:
        print('      -> all in free blocks: nothing extracted is affected.')
        print('         Say so in LOG.md; do not leave it unmentioned.')
    return 1 if allocated else 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__.strip().splitlines()[-3], file=sys.stderr)
        sys.exit(2)
    rc = 0
    for p in sys.argv[1:]:
        rc |= report(p)
    sys.exit(rc)
