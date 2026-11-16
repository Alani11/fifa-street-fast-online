"""For every INI key of streetdefault.ini/heroperf.ini that has a string xref, locate the config-read call in the lifted code:
key address -> `addi r3,rX,lo` ; next `bl` target (getter) ; default = last float loaded into f1 (directly or via fmr f1,fN) before the call
; destination = first stf*/stw with a lis-based address after the call. HEURISTIC; output is a lead list, not proof."""
import sys,re,struct,csv,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent)); import gdump
dump=r'C:\src\sim_recomp\dump\pass0_modules.bin'; gen=pathlib.Path(r'C:\src\sim_recomp\generated_snapshot')
mem=[]
with open(dump,'rb') as f:
    for b,s,off in gdump.regions(dump): f.seek(off); mem.append((b,f.read(s)))
def rd(a,n=4):
    for b,d in mem:
        if b<=a<=b+len(d)-n: return d[a-b:a-b+n]
def ini_keys():
    ks={}
    for p in ['streetdefault.ini','heroperf.ini']:
        for l in open(rf'unpacked_data\decoded\data0\{p}',errors='replace'):
            l=re.split(r'//|;',l)[0].strip(); m=re.match(r'([A-Za-z_0-9]+)\s*=\s*(.+)$',l)
            if m: ks.setdefault(m.group(1),m.group(2).strip())
    return ks
ini=ini_keys()
rows=list(csv.DictReader(open('docs/listings/string_xrefs.tsv',encoding='utf-8'),delimiter='\t'))
byfn={}
for r in rows:
    k=r['string'].split('/')[-1]
    if k in ini or r['string'] in ini: byfn.setdefault(r['function'],[]).append((k,int(r['address'],16)))
cache={}
def lines(fn):
    if fn in cache: return cache[fn]
    for f in gen.rglob('fifastreet_recomp.*.cpp'):
        t=f.read_text(encoding='utf-8',errors='replace'); k=t.find('DEFINE_REX_FUNC(%s)'%fn)
        if k>=0:
            e=t.find('DEFINE_REX_FUNC(',k+10); cache[fn]=[l.strip() for l in t[k:e if e>0 else len(t)].splitlines() if l.strip().startswith(('// ','loc_'))]; return cache[fn]
def hi_of(t,i):  # resolve lis for a register used at line i by scanning back for 'lis rX'
    pass
out=[]
def snaps(L):
    hi={}; S=[]
    for l in L:
        S.append(dict(hi))
        m=re.match(r'// lis r(\d+),(-?\d+)$',l)
        if m: hi[m.group(1)]=(int(m.group(2))&0xffff)<<16
    return S
def fval(L,S,reg,j):
    """value loaded into float reg before line j: follow fmr chain back to the nearest lfs with a resolvable address."""
    for k in range(j-1,max(0,j-80),-1):
        x=L[k]
        m=re.match(r'// lfs f(\d+),(-?\d+)\(r(\d+)\)$',x)
        if m and m.group(1)==reg:
            if m.group(3) in S[k]:
                raw=rd((S[k][m.group(3)]+int(m.group(2)))&0xffffffff)
                return struct.unpack('>f',raw)[0] if raw else None
            return None
        m=re.match(r'// fmr f(\d+),f(\d+)$',x)
        if m and m.group(1)==reg: reg=m.group(2); continue
        m=re.match(r'// (?:fadds|fsubs|fmuls|fdivs|fneg|fabs|fsel|fmadds|lfd|fcfid|frsp)\w* f(\d+),',x)
        if m and m.group(1)==reg: return None
    return None
for fn,keys in byfn.items():
    L=lines(fn)
    if not L: continue
    S=snaps(L)
    for key,addr in keys:
        lo=addr&0xffff; lo_s=lo if lo<0x8000 else lo-0x10000
        for i,l in enumerate(L):
            if l.startswith('// addi r3,') and l.endswith(','+str(lo_s)):
                src=l.split(',')[1]
                if not (src[1:] in S[i] and S[i][src[1:]]+lo_s==addr): continue
                bj=next((j for j in range(i,min(len(L),i+12)) if L[j].startswith('// bl ')),None)
                if bj is None: continue
                getter=L[bj].split()[-1]
                dfl=fval(L,S,'1',bj)
                if dfl is None:
                    m=None
                    for k in range(bj-1,max(0,bj-30),-1):
                        m=re.match(r'// fmr f1,f(\d+)$',L[k])
                        if m: dfl=fval(L,S,m.group(1),k); break
                dest=None
                for j in range(bj,min(len(L),bj+30)):
                    m=re.match(r'// (stfs|stw|stb|stfd) \w+,(-?\d+)\(r(\d+)\)$',L[j])
                    if m and m.group(3) in S[j]: dest='0x%08X'%((S[j][m.group(3)]+int(m.group(2)))&0xffffffff); break
                out.append((key,ini.get(key),fn,hex(addr),getter,'%g'%dfl if dfl is not None else '',dest or ''))
                break
with open('docs/listings/config_keys.tsv','w') as f:
    f.write('key\tini_value\tfunction\tstring_addr\tgetter_call\tdefault_guess\tdest_global_guess\n')
    for r in sorted(out): f.write('\t'.join(str(x) for x in r)+'\n')
print(len(out),'keys located;',len({o[2] for o in out}),'functions; getters:',__import__('collections').Counter(o[4] for o in out).most_common(6))
