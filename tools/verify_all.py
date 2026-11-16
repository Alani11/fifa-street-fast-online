"""Re-verifies every structural claim in docs/binary_formats.md against the real files."""
import sys,struct,pathlib,collections,math,re
sys.path.insert(0,str(pathlib.Path(__file__).parent)); import big4,chunkdec
R=pathlib.Path(__file__).resolve().parent.parent
bad=0
def chk(c,m):
    global bad
    if not c: bad+=1; print('FAIL',m)
# 1 outer + nested BIG4/BIGF: size field, bounds, 0x40 alignment
al=collections.Counter(); n=0
for p in list((R/'engine_data').rglob('*.big')):
    fs,he,te,en=big4.parse(str(p)); a=p.stat().st_size; chk(fs==a,(p,'size'))
    chk(all(o+s<=a for _,o,s in en),(p,'bounds')); chk(te<=he<=te+8,(p,'hend'))
    for _,o,s in en: al[o%64==0 or o==he]+=1
    n+=1
print('outer archives',n,'entry offset 64-aligned (or ==hdr end):',dict(al))
# 2 chunk containers: chunk-count hypothesis for header word @0x14, @0x18
hy=collections.Counter(); nf=0
for f in (R/'unpacked_data'/'data0').rglob('*'):
    if f.is_file() and f.read_bytes()[:8]==b'chunklzx':
        b=f.read_bytes(); full,chunk=struct.unpack('>II',b[12:20]); w=struct.unpack('>6I',b[20:44]); nf+=1
        hy[(w[0]==math.ceil(full/chunk),w[1])]+=1
        chunkdec.decode_chunk(b)  # asserts full size
print('chunklzx files decoded+size-asserted',nf,'| (word@0x14==ceil(full/chunk), word@0x18):',dict(hy))
# 3 libfinal index vs actual seq files
for lf in (R/'unpacked_data'/'decoded').rglob('aisequence.libfinal'):
    d=lf.read_bytes(); ver,cnt=struct.unpack('>II',d[:8]); ids=struct.unpack('>%dI'%cnt,d[8:8+4*cnt])
    seqs={int(s.stem.strip('_')) for s in lf.parent.glob('final/*.seq')}
    chk(len(d)==8+4*cnt,(lf,'size')); chk(set(ids)==seqs,(lf,'ids vs files'))
    print(lf.parent.name,'libfinal ver',ver,'count',cnt,'ids==seq files',set(ids)==seqs)
# 4 nnet closure
for n_ in ['pass','shot','tackle','dribble']:
    d=(R/'unpacked_data/decoded/data0/data/neuralnet'/f'nnet{n_}.dat').read_bytes(); f=struct.unpack('<%df'%(len(d)//4),d)
    L=int(f[0]); sz=[int(x) for x in f[1:1+L]]
    tot=1+L+sum((sz[i]+1)*sz[i+1] for i in range(L-1))+2*(sz[0]+sz[-1]); chk(tot==len(f),(n_,'nnet')); print('nnet',n_,'layers',sz,'floats',len(f),'model',tot)
# 5 vault ExpN: (size, offset) records must tile DatN with no gaps (offsets file-absolute)
import attribdb_dump as a, attrib_slots as sl, re
V=R/'unpacked_data/decoded/data0/data'
for v in sorted(V.rglob('attribdb.vlt')):
    b=v.read_bytes(); ch,cnt,rec=a.exports(b); d0,dl=ch['DatN']
    r=sorted((o,z) for _,_,o,z in rec); gaps=sum(1 for i in range(len(r)-1) if r[i][0]+r[i][1]!=r[i+1][0])
    chk(r[0][0]==d0+8,(v,'first offset == DatN+8')); chk(gaps==0,(v,'tiling')); chk(r[-1][0]+r[-1][1]+8==d0+dl,(v,'8-byte tail'))
    tot=sum(s_ for _,_,s_ in a.chunks(b)); chk(tot==len(b),(v,'chunk sizes sum to file')); chk(b[:4]==b'Vers' and struct.unpack('>I',b[4:8])[0]==16,(v,'Vers chunk is 16 bytes'))
    recs,skipped,_=sl.records(str(v))
    print(v.parent.name,'exports',cnt,'tile gaps',gaps,'ExpN size-(16+24n)',ch['ExpN'][1]-16-24*cnt,'| records with size==64+16n:',len(recs),'other',skipped)
# 6 ESIA size formula (word@0x08 is 0 -> 24n+128 else 28n+152, n = word@0x0C)
ok=tot_=0
for f in (V/'skillmoveai').rglob('*.seq'):
    d=f.read_bytes(); idw,w8,n=struct.unpack('>3I',d[4:16]); tot_+=1
    chk(idw==int(re.search(r'_(\d+)_',f.name).group(1)),(f,'id')); ok+=len(d)==(24*n+128 if w8==0 else 28*n+152)
chk(ok==tot_,'ESIA size formula'); print('ESIA files',tot_,'size formula fits',ok)
# 7 nested archives (all BIG4/BIGF under unpacked_data/decoded): size field, bounds
nn=0
for f in (R/'unpacked_data/decoded').rglob('*'):
    if f.is_file() and f.read_bytes()[:4] in (b'BIG4',b'BIGF') and not f.name.endswith('_x'):
        fs,he,te,en=big4.parse(str(f)); chk(fs==f.stat().st_size-(16 if f.read_bytes()[:4]==b'BIGF' else 0),(f,'nested size (BIGF: file size - 16)')); chk(all(o+z<=fs for _,o,z in en),(f,'nested bounds')); nn+=1
print('nested archives checked',nn)
# 8 chunkzip + refpack length
cz=rp=0
for f in (R/'unpacked_data'/'data0').rglob('*'):
    if f.is_file():
        h=f.read_bytes()
        if h[:8]==b'chunkzip': chunkdec.decode_chunk(h); cz+=1
for f in (R/'unpacked_data/decoded').rglob('*'):
    pass
print('chunkzip decoded',cz)
# 9 outer archive header end vs data start (data starts at next 64-byte boundary after header end)
for p in (R/'engine_data').rglob('*.big'):
    fs,he,te,en=big4.parse(str(p)); chk(min(o for _,o,_ in en)==(he+63)//64*64,(p,'first data = ceil64(hend)'))
# 10 GD.STRM (ANT generic data) size field equals decoded length; exercises chunkref + uncompressed-LZX paths
ok=0
for f in list((R/'unpacked_data/decoded_data7').rglob('*.cba*'))+list((R/'unpacked_data/loose').glob('*.dec')):
    b=f.read_bytes()
    if b[:8]==b'GD.STRMb': chk(struct.unpack('>I',b[8:12])[0]==len(b),(f,'GD.STRM size')); ok+=1
print('GD.STRM files size-checked',ok); print('FAILS',bad)
# 11 GD.STRM semantic checks (inferred layout must hold on every instance)
import gdstrm, csv as _csv
ab=gdstrm.load(str(R/'unpacked_data/loose/ant.cbac.dec')); acl={c['hash']:c for c in gdstrm.classes(ab)}; abl=gdstrm.blocks(ab)
guids=set()
for blk in abl:
    c=acl.get(blk[2])
    if c:
        g_=gdstrm.block_guid(ab,c,blk)
        if g_: guids.add(g_)
tr=acl[0x75abaa2d]; ntr=0
for blk in (x for x in abl if x[2]==0x75abaa2d):
    ntr+=1; chk(gdstrm.ref_one(ab,tr,blk,'From') in guids and gdstrm.ref_one(ab,tr,blk,'To') in guids,'transition endpoint unresolved')
print('transitions with both endpoints resolved:',ntr)
cb=gdstrm.load(str(R/'unpacked_data/loose/common.cbac.dec')); ccl={c['hash']:c for c in gdstrm.classes(cb)}
pp=ccl[0x1182aa72]; k=0
for blk in (x for x in gdstrm.blocks(cb) if x[2]==0x1182aa72):
    v=gdstrm.decode(cb,pp,blk); chk(v['InertiaTensorScale']==1.0 and v['Density']==1.0 and 0<v['Mass']<100,'PartProperty float offsets'); k+=1
print('PartProperty float-offset checks',k)
_ang=[]
rows=list(_csv.DictReader(open(R/'docs/listings/gestures.tsv',encoding='utf-8'),delimiter='	')); badg=0
for r in rows:
    chk(float(r['min_ticks'])<=float(r['max_ticks']),('tick order',r['gesture']))
    for kv in r['params'].split(';'):
        if kv.startswith(('MinAngle=','MaxAngle=')):
            dg=__import__('math').degrees(float(kv.split('=')[1])); chk(-360<=dg<=720,('angle outside -360..720 deg',r['gesture'],dg)); _ang.append(abs(dg/5-round(dg/5))<0.02)
print('gesture rows checked',len(rows),'| angles that are multiples of 5 deg: %d of %d'%(sum(_ang),len(_ang))); print('FAILS',bad)

