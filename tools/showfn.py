"""Print the PowerPC comment listing of one recompiled function: showfn.py sub_XXXXXXXX [generated dir]"""
import sys,re,subprocess,pathlib
fn=sys.argv[1]; gen=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else r'C:\src\sim_recomp\generated_snapshot')
for f in gen.rglob('fifastreet_recomp.*.cpp'):
    t=f.read_text(encoding='utf-8',errors='replace')
    k=t.find('DEFINE_REX_FUNC(%s)'%fn)
    if k<0: continue
    end=t.find('DEFINE_REX_FUNC(',k+10); body=t[k:end if end>0 else len(t)]
    for l in body.splitlines():
        s=l.strip()
        if s.startswith('// ') or s.startswith('loc_') or s.startswith('DEFINE'): print(s)
    break
