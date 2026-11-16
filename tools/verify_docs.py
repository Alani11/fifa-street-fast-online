"""Check numeric claims in docs/physics_spec.md against the decoded INI files."""
import re,pathlib,sys
R=pathlib.Path(__file__).resolve().parent.parent; D=R/'unpacked_data/decoded/data0'
def ini(p):
    out={}
    for l in (D/p).read_text(errors='replace').splitlines():
        l=re.split(r'//|;',l,1)[0].strip()
        m=re.match(r'([A-Za-z_0-9]+)\s*=\s*(.+)$',l)
        if m: out.setdefault(m.group(1),[]).append(m.group(2).strip().strip('"'))
    return out
street=ini('streetdefault.ini'); hero=ini('heroperf.ini'); doc=(R/'docs/physics_spec.md').read_text(encoding='utf-8')
bad=0; n=0
def eq(a,b):
    try: return abs(float(a)-float(b))<1e-9
    except: return a==b
sec=doc.split('## 2.')[1].split('## 4.')[0]
for row in re.findall(r'^\| `([^|]+)` \| ([^|]+) \|',sec,re.M):
    key,val=row; key=key.replace('[PHYSICS] ','')
    keys=[k.strip('` ') for k in key.split(' / ')]; vals=[v.strip() for v in val.split(' / ')]
    if len(keys)==1 and key.endswith(' / LENGTH'): pass
    # forms like `AI_X_WIDTH` / `LENGTH` handled below
    m=re.match(r'(AI_\w+?)_WIDTH` / `LENGTH',key+'`') 
    if '`' in key: 
        base=re.match(r'(\w+)WIDTH',key.split('`')[0]) 
    ks=[]; 
    if ' / ' in key and 'WIDTH' in key: b=keys[0][:-5]; ks=[b+'WIDTH',b+'LENGTH']
    elif ' / ' in key and 'MIN_DIST' in key: ks=[keys[0],keys[0].replace('MIN','MAX')]
    else: ks=keys
    for k,v in zip(ks,vals):
        n+=1; got=(street.get(k) or [None])[-1]
        if got is None or not eq(got,v): bad+=1; print('MISMATCH',k,'doc',v,'file',got)
# AISHOOT table
tbl=re.findall(r'^\| (F?(?:BIG|MED|SMALL)) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \|',doc,re.M)
for name,*vs in tbl:
    for suf,v in zip(['LOW','MLO','MID','MHI','HI'],vs):
        n+=1; k=name+suf; got=(street.get(k) or [None])[-1]
        if got is None or not eq(got,v): bad+=1; print('MISMATCH',k,v,got)
for k,v in [('COMPETING_THRESHOLD','1.35'),('INITIAL_PERFORMANCE','0.2'),('NUM_PASSES_THRESHOLD','3'),('THREAT_POSSESSOR_THRESHOLD','40'),('INP_THRESHOLD_NON_POSSESSOR_NOT_DEFENDER','90'),('INP_THRESHOLD_NON_POSSESSOR_DEFENDER','60'),('OOP_THRESHOLD_TEAMMATE_IS_POSSESSOR','90'),('OOP_THRESHOLD_TEAMMATE_IS_NOT_POSSESSOR','60')]:
    n+=1; got=hero[k][0].split()[0]
    if not eq(got,v): bad+=1; print('MISMATCH hero',k,v,got)
print('checked',n,'values; mismatches',bad); sys.exit(bad>0)
