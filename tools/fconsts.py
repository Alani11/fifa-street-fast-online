"""Resolve data references (lis + lfs/lfd/lwz/stw/stfs d(rX)) inside one recompiled function and read the value from a guest dump.
Register tracker is cleared at loc_ labels and when a tracked register is overwritten (approximation: linear scan, so values after
back-edges may be missed). Output: instruction, address, float32/uint32 value at that address in the dump.
Usage: fconsts.py sub_XXXXXXXX <dump.bin> [generated dir]"""
import sys,re,struct,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent)); import gdump
fn=sys.argv[1]; dump=sys.argv[2]; gen=pathlib.Path(sys.argv[3] if len(sys.argv)>3 else r'C:\src\sim_recomp\generated_snapshot')
mem=[]
with open(dump,'rb') as f:
    for b,s,off in gdump.regions(dump): f.seek(off); mem.append((b,f.read(s)))
def rd(a,n=4):
    for b,d in mem:
        if b<=a<=b+len(d)-n: return d[a-b:a-b+n]
def body(fn):
    for f in gen.rglob('fifastreet_recomp.*.cpp'):
        t=f.read_text(encoding='utf-8',errors='replace'); k=t.find('DEFINE_REX_FUNC(%s)'%fn)
        if k>=0:
            e=t.find('DEFINE_REX_FUNC(',k+10); return t[k:e if e>0 else len(t)]
lisr=re.compile(r'// lis r(\d+),(-?\d+)$'); mem_ops=('lfs','lfd','lwz','stw','stfs','stfd','lbz','stb','lhz','sth','lwzx')
opre=re.compile(r'// (\w+)\.? ?(.*)$')
hi={}; out=[]
for line in body(fn).splitlines():
    s=line.strip()
    if s.startswith('loc_'): hi.clear(); continue
    if not s.startswith('// '): continue
    m=lisr.match(s)
    if m: hi[m.group(1)]=(int(m.group(2))&0xffff)<<16; continue
    m=opre.match(s)
    if not m: continue
    op,args=m.groups(); a=args.split(',')
    mm=re.match(r'(-?\d+)\(r(\d+)\)$',a[-1].strip()) if a else None
    if op in mem_ops and mm and mm.group(2) in hi:
        addr=(hi[mm.group(2)]+int(mm.group(1)))&0xffffffff; raw=rd(addr)
        v=None
        if raw:
            v='f32=%g u32=0x%08x'%(struct.unpack('>f',raw)[0],struct.unpack('>I',raw)[0])
        out.append('%-6s %-14s @0x%08X  %s'%(op,a[0],addr,v)); 
    elif op in ('lvlx128','lvx128','lvx','lvlx') and len(a)==3:
        ra=a[1].strip(); rb=a[2].strip()
        va=0 if ra=='r0' else hi.get(ra[1:]); vb=0 if rb=='r0' else hi.get(rb[1:])
        if va is not None and vb is not None:
            addr=(va+vb)&0xffffffff; raw=rd(addr,16)
            v=('f32x4=%s'%[round(x,6) for x in struct.unpack('>4f',raw)]) if raw else None
            out.append('%-8s %-6s @0x%08X  %s'%(op,a[0],addr,v))
    elif op=='addi' and len(a)==3 and a[1].strip() in [('r'+k) for k in hi]:
        addr=(hi[a[1].strip()[1:]]+int(a[2]))&0xffffffff; hi[a[0].strip()[1:]]=addr
    else:
        d=a[0].strip() if a else ''
        if d.startswith('r') and d[1:] in hi and op!='lis': hi.pop(d[1:],None)
print('\n'.join(out))
