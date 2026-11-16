"""Sample live Ball objects (vtable 0x823CE5D4) in the running fifastreet.exe at ~100 Hz and report per-ball motion.
Usage: ball_track.py <pid> <seconds> [out.json]. Read-only (ReadProcessMemory)."""
import sys, struct, time, json
sys.path.insert(0, __import__('os').path.dirname(__file__))
import procmem as pm
pid, secs = int(sys.argv[1]), float(sys.argv[2])
h = pm.open_proc(pid)
pat = bytes.fromhex('823CE5D4')
hits = pm.scan(h, [pat])[0][pat]
addrs = [a for a in hits if a % 16 == 0]
print('ball objects:', len(addrs))
def rd(a):
    d = pm.read(h, a, 176)
    if len(d) < 176: return None
    f = lambda o, n: struct.unpack('>%df' % n, d[o:o+4*n])
    return f(32, 1)[0], f(112, 3), f(128, 4), f(144, 3), f(160, 3)
series = {a: [] for a in addrs}
t0 = time.time()
while time.time() - t0 < secs:
    t = time.time() - t0
    for a in addrs:
        r = rd(a)
        if r: series[a].append((round(t, 4),) + r[1] + r[3] + r[4])
    time.sleep(0.005)
json.dump({hex(a): s for a, s in series.items()}, open(sys.argv[3] if len(sys.argv) > 3 else 'ball_track.json', 'w'))
for a, s in series.items():
    if len(s) < 5: continue
    uniq = len({(round(x[1], 3), round(x[2], 3), round(x[3], 3)) for x in s})
    ys = [x[2] for x in s]
    sp = max((x[4]**2 + x[5]**2 + x[6]**2) ** .5 for x in s)
    print(hex(a), 'samples', len(s), 'distinct pos', uniq, 'y range %.3f..%.3f' % (min(ys), max(ys)), 'max speed %.3f' % sp,
          'x range %.2f..%.2f' % (min(x[1] for x in s), max(x[1] for x in s)))
