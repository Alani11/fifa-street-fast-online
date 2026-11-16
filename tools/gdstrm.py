"""GD.STRM reader (ANT generic data). INFERRED layout, partly verified against the files:
 GD.STRMb | u32 BE total length | u32 | GD.REFLb (class schema) | many GD.DATAb instance blocks.
REFL class record = [marker FF FF FF FD | u32 idx | u32 | u32 | u32 | u32 | u32 1 | u32 classHash | n * 32-byte field entries] [NUL-separated names: class, __name, __guid, __base, fields...]
 field entry (8 x u32 BE): kind, size, payload_offset, name_pool_offset, flagsA, flagsB, 0, typeRef.  name_pool_offset indexes the class's name pool (1-based cumulative).
DATA block = 'GD.DATAb' | u32 total | u32 payload | ... ; classHash at block+36; field payload_offset is relative to block+48 (verified for float fields)."""
import re,struct,sys,collections
def load(path):
    return open(path,'rb').read()
def classes(b):
    refl_end=b.find(b'GD.DATAb'); out=[]; pos=0
    for m in re.finditer(rb'\xff\xff\xff\xfd',b[:refl_end]):
        s=m.start(); h=struct.unpack('>I',b[s+28:s+32])[0]; p=s+32; ents=[]
        while p+32<=refl_end:
            w=struct.unpack('>8I',b[p:p+32])
            if w[0] in (0,) or w[0]>0x40 or w[1]>0x400 or w[3]>0x2000 or w[6]!=0 or w[7]>refl_end: break
            ents.append(w); p+=32
        # names pool: NUL separated printable run(s) after entries
        q=p
        while q<refl_end and b[q]==0: q+=1
        names=[]; 
        while q<refl_end:
            e=b.find(b'\0',q)
            if e==q or e<0: break
            t=b[q:e]
            if not re.fullmatch(rb'[\x20-\x7e]+',t): break
            names.append(t.decode()); q=e+1
        out.append(dict(hash=h,entries=ents,names=names,at=s))
    return out
def name_at(names,off):
    pos=1
    for n in names:
        if pos==off: return n
        pos+=len(n)+1
    return '?%d'%off
def blocks(b):
    offs=[m.start() for m in re.finditer(rb'GD\.DATAb',b)]+[len(b)]
    return [(offs[i],offs[i+1]-offs[i],struct.unpack('>I',b[offs[i]+36:offs[i]+40])[0]) for i in range(len(offs)-1)]
if __name__=='__main__':
    b=load(sys.argv[1]); cl=classes(b); bl=collections.Counter(h for _,_,h in blocks(b))
    print(len(cl),'classes parsed')
    for c in cl:
        print('%08x'%c['hash'],'instances',bl.get(c['hash'],0),c['names'][:1],'fields',len(c['entries']))

def f32(b,o): return struct.unpack('>f',b[o:o+4])[0]
def decode(b,cls,blk):
    """Decode float32 (kind 0xA), vec4 (kind 0xC), bool/byte (kind 1) and uint (kind 6) fields of one block, plus its tail strings."""
    o,n,h=blk; d=b[o:o+n]; out={}
    for e in cls['entries']:
        kind,size,off=e[0],e[1],e[2]; nm=name_at(cls['names'],e[3]); p=48+off
        if p+size>n: continue
        if kind==0xa: out[nm]=struct.unpack('>f',d[p:p+4])[0]
        elif kind==0xc: out[nm]=struct.unpack('>4f',d[p:p+16])
        elif kind==1: out[nm]=d[p]
        elif kind==6: out[nm]=struct.unpack('>I',d[p:p+4])[0]
        elif kind==7: out[nm]=struct.unpack('>I',d[p:p+4])[0]; out[nm+'_f32']=struct.unpack('>f',d[p:p+4])[0]
    out['_strings']=[s.decode() for s in re.findall(rb'[A-Za-z_][\x20-\x7e]{2,}',d[48:]) ]
    return out

def _field(cls,name):
    for e in cls['entries']:
        if name_at(cls['names'],e[3])==name: return e
def block_name(b,cls,blk):
    """__name: kind 0x11 handle (u32 len, u32 cap, u32 0, u32 off) -> text at block+16+off (checked on StateFlow nodes and PartProperty blocks)."""
    e=_field(cls,'__name'); o,n,h=blk
    if not e: return None
    p=o+48+e[2]; ln,cap,z,off=struct.unpack('>4I',b[p:p+16])
    q=o+16+off
    if 0<ln<200 and q+ln<=o+n:
        t=b[q:q+ln-1] if b[q+ln-1:q+ln]==b'\0' else b[q:q+ln]
        if re.fullmatch(rb'[\x20-\x7e]*',t): return t.decode()
    return None
def block_guid(b,cls,blk):
    e=_field(cls,'__guid'); o,n,h=blk
    return b[o+48+e[2]:o+48+e[2]+16] if e else None

def ref_list(b,cls,blk,field):
    """List field (kind 0x10, 16 bytes): handle (count, count, 0, off); items are 16-byte GUIDs at block+16+off. Inferred from GestureAsset/GestureStepAsset blocks."""
    e=_field(cls,field)
    if not e: return []
    o,n,h=blk; p=o+48+e[2]; cnt,_,_,off=struct.unpack('>4I',b[p:p+16])
    if cnt>200 or o+16+off+16*cnt>o+n: return []
    return [b[o+16+off+16*i:o+32+off+16*i] for i in range(cnt)]
def ref_one(b,cls,blk,field):
    e=_field(cls,field); o=blk[0]
    return b[o+48+e[2]:o+48+e[2]+16] if e else None
