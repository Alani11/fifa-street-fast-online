"""Find reads/writes of given guest data addresses in the recompiled code: lis rX,hi followed (within 60 lines of the same function)
by an lfs/lfd/lwz/stw/stfs/... d(rX) or addi that lands on the address. Linear scan; a register overwrite drops tracking.
Usage: dataxref.py 0x83E2BF10 [0x...]  (prints function, line index, instruction)"""
import sys,re,pathlib
gen=pathlib.Path(r'C:\src\sim_recomp\generated_snapshot'); targets={int(a,16) for a in sys.argv[1:]}
fre=re.compile(r'DEFINE_REX_FUNC\((sub_[0-9A-F]+)\)'); lis=re.compile(r'// lis r(\d+),(-?\d+)$')
memop=re.compile(r'// (lfs|lfd|lwz|lbz|lhz|stw|stb|sth|stfs|stfd|addi|lwzx) ([a-z0-9]+),(-?\d+)\(?r?(\d+)?\)?$')
res=[]
for f in sorted(gen.rglob('fifastreet_recomp.*.cpp')):
    fn=None; hi={}; n=0
    for line in open(f,encoding='utf-8',errors='replace'):
        m=fre.search(line)
        if m: fn=m.group(1); hi={}; n=0; continue
        s=line.strip()
        if not s.startswith('// '): continue
        n+=1
        m=lis.match(s)
        if m: hi[m.group(1)]=((int(m.group(2))&0xffff)<<16,n); continue
        m=re.match(r'// (lfs|lfd|lwz|lbz|lhz|stw|stb|sth|stfs|stfd) (\w+),(-?\d+)\(r(\d+)\)$',s)
        if m and m.group(4) in hi and n-hi[m.group(4)][1]<80:
            a=(hi[m.group(4)][0]+int(m.group(3)))&0xffffffff
            if a in targets: res.append((a,fn,s))
        m=re.match(r'// addi r(\d+),r(\d+),(-?\d+)$',s)
        if m and m.group(2) in hi and n-hi[m.group(2)][1]<80:
            a=(hi[m.group(2)][0]+int(m.group(3)))&0xffffffff
            if a in targets: res.append((a,fn,s))
for a,fn,s in sorted(res): print('0x%08X'%a,fn,s)
