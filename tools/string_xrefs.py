"""Index guest-string references in the recompiled C++: for each function, find lis rX,hi + addi/ori rY,rX,lo address pairs
(taken from the PowerPC instruction comments the generator emits) that land on a NUL-terminated ASCII string in the dumped guest image.
Usage: string_xrefs.py <generated dir> <dump .bin> <out tsv>"""
import re,sys,struct,pathlib,collections
sys.path.insert(0,str(pathlib.Path(__file__).parent)); import gdump
gen=pathlib.Path(sys.argv[1]); dump=sys.argv[2]; out=sys.argv[3]
mem=[]
with open(dump,'rb') as f:
    for b,s,off in gdump.regions(dump):
        f.seek(off); mem.append((b,f.read(s)))
def string_at(a):
    for b,d in mem:
        if b<=a<b+len(d):
            i=a-b; j=d.find(b'\0',i,i+160)
            if j-i>=3:
                s=d[i:j]
                if all(32<=c<127 for c in s): return s.decode()
            return None
    return None
fre=re.compile(r'DEFINE_REX_FUNC\((sub_[0-9A-F]+)\)')
lis=re.compile(r'// lis r(\d+),(-?\d+)$'); add=re.compile(r'// addi r(\d+),r(\d+),(-?\d+)$'); ori=re.compile(r'// ori r(\d+),r(\d+),(\d+)$')
rows=[]; cache={}
for f in sorted(gen.rglob('fifastreet_recomp.*.cpp')):
    fn=None; hi={}
    for line in open(f,encoding='utf-8',errors='replace'):
        m=fre.search(line)
        if m: fn=m.group(1); hi={}; continue
        s=line.strip()
        if not s.startswith('// '): continue
        m=lis.match(s)
        if m: hi[m.group(1)]=(int(m.group(2))&0xffff)<<16; continue
        m=add.match(s)
        if m and m.group(2) in hi:
            a=(hi[m.group(2)]+int(m.group(3)))&0xffffffff
            if 0x82000000<=a<0x84000000:
                if a not in cache: cache[a]=string_at(a)
                if cache[a]: rows.append((fn,hex(a),cache[a],f.parent.name))
            hi.pop(m.group(1),None) if m.group(1)!=m.group(2) else None
            continue
        m=ori.match(s)
        if m and m.group(2) in hi:
            a=hi[m.group(2)]|int(m.group(3))
            if 0x82000000<=a<0x84000000:
                if a not in cache: cache[a]=string_at(a)
                if cache[a]: rows.append((fn,hex(a),cache[a],f.parent.name))
with open(out,'w',encoding='utf-8') as o:
    o.write('function\taddress\tstring\tmodule\n')
    for r in rows: o.write('\t'.join(r)+'\n')
print(len(rows),'string refs;',len({r[0] for r in rows}),'functions;',len({r[2] for r in rows}),'distinct strings')
