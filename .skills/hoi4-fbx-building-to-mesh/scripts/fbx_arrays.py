# -*- coding: utf-8 -*-
"""Array-level FBX extractor.

The node tree in this file uses an FBX variant whose node-header layout we
could not pin down reliably, but every *array* property is self-validating:
    type:u8  count:u32  encoding:u32  complen:u32  data[complen]
and `data` is either raw or a zlib stream we can inflate and length-check.

So we scan for every zlib stream in the file, read its 13-byte header, verify
the inflated size equals count*itemsize, and label it with the nearest
preceding ASCII node name.
"""
import re
import struct
import zlib

FBX = '_tc/source/temple.fbx'
ITEMSIZE = {'d': 8, 'f': 4, 'l': 8, 'i': 4, 'b': 1}
TYPENAME = {8: 'd/double', 4: '?/int-or-float'}


def is_zlib_hdr(d, p):
    if p + 2 > len(d):
        return False
    cmf, flg = d[p], d[p + 1]
    if cmf & 0x0f != 8:
        return False
    if (cmf * 256 + flg) % 31 != 0:
        return False
    return (flg & 0x20) == 0          # no preset dictionary


def node_name_before(d, p, back=4000):
    """Find the closest plausible ASCII node name before offset p."""
    lo = max(0, p - back)
    best = (None, -1)
    for m in re.finditer(rb'[A-Za-z][A-Za-z0-9_:]{2,40}', d[lo:p]):
        nm = m.group().decode()
        if nm[0].isupper():
            best = (nm, lo + m.start())
    return best[0]


def scan():
    d = open(FBX, 'rb').read()
    out = []
    p = 0
    n = len(d)
    while True:
        p = d.find(b'\x78', p)
        if p < 0:
            break
        if is_zlib_hdr(d, p) and p >= 13:
            t = chr(d[p - 13])
            count = struct.unpack_from('<I', d, p - 12)[0]
            enc = struct.unpack_from('<I', d, p - 8)[0]
            clen = struct.unpack_from('<I', d, p - 4)[0]
            ok = (t in ITEMSIZE and enc == 1 and 0 < clen < n - p)
            if ok:
                try:
                    o = zlib.decompressobj()
                    raw = o.decompress(d[p:p + clen + 64])
                    used = len(d[p:p + clen + 64]) - len(o.unused_data)
                    if used == clen and len(raw) == count * ITEMSIZE[t]:
                        out.append(dict(off=p, type=t, count=count,
                                        complen=clen, raw=raw,
                                        name=node_name_before(d, p)))
                        p += clen
                        continue
                except zlib.error:
                    pass
        p += 1
    return out


if __name__ == '__main__':
    res = scan()
    print('found %d compressed arrays' % len(res))
    for r in res:
        kind = 'double' if r['type'] == 'd' else r['type']
        print('  @%-9d %-8s count=%-9d complen=%-9d  near=%s'
              % (r['off'], kind, r['count'], r['complen'], r['name']))