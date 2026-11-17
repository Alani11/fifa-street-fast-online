"""Extract an Xbox 360 XISO (raw GDF, volume descriptor at 0x10000) to a folder. Usage: xiso_extract.py game.iso out_dir [part_offset]
Use only with a disc image of a game you own."""
import struct, sys, os
iso, out = sys.argv[1], sys.argv[2]
base = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0
f = open(iso, 'rb')
f.seek(base + 0x10000)
vd = f.read(0x800)
assert vd[:20] == b'MICROSOFT*XBOX*MEDIA', 'not an XISO at this offset'
root_sec, root_size = struct.unpack('<II', vd[0x14:0x1C])
total = 0
def walk(sector, size, path):
    global total
    f.seek(base + sector * 0x800)
    d = f.read(size)
    seen = set()
    def entry(off):
        global total
        if off in seen or off * 4 + 14 > len(d): return
        seen.add(off)
        o = off * 4
        l, r, sec, sz, attr, nl = struct.unpack('<HHIIBB', d[o:o + 14])
        if l == 0xFFFF and r == 0xFFFF and sec == 0xFFFFFFFF: return
        name = d[o + 14:o + 14 + nl].decode('latin-1')
        if l: entry(l)
        p = os.path.join(path, name)
        if attr & 0x10:
            os.makedirs(p, exist_ok=True)
            if sz: walk(sec, sz, p)
        else:
            os.makedirs(path, exist_ok=True)
            with open(p, 'wb') as w:
                f.seek(base + sec * 0x800); left = sz
                while left:
                    n = min(left, 1 << 24); w.write(f.read(n)); left -= n
            total += sz
        if r: entry(r)
    entry(0)
walk(root_sec, root_size, out)
print('extracted %.1f MB to %s' % (total / 1e6, out))
