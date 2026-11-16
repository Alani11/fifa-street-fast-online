"""Record/slot dump for Attrib vault data (INFERRED layout, see docs/binary_formats.md 3.3).
Record (file-absolute offset/size from ExpN): 48-byte header (u64 id, u64 shared hash, ..., u32 n at +24 and again at +32), then a 16-byte
header slot at +48 and n 16-byte slots from +64 (size = 64 + 16*n holds for most records; others are skipped and counted).
Slot = u64 key hash | u32 value | u32 flags. flags&0x4000 -> value is a big-endian float32; other flag values (0x200, 0, 0x10000, 0x14000 ...) are NOT decoded.
Names are hashed; no dictionary exists in the workspace."""
import sys,struct,csv,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent)); import attribdb_dump as a
def records(vlt):
    b=open(vlt,'rb').read(); ch,cnt,rec=a.exports(b); out=[]; skipped=0
    for ck,cl,off,sz in rec:
        if sz<64: skipped+=1; continue
        n=struct.unpack('>I',b[off+24:off+28])[0]; n2=struct.unpack('>I',b[off+32:off+36])[0]
        if sz!=64+16*n or n!=n2: skipped+=1; continue
        slots=[]
        for i in range(n):
            q=off+64+16*i; k,v,f=struct.unpack('>QII',b[q:q+16]); slots.append((k,v,f))
        out.append((ck,off,slots))
    return out,skipped,cnt
if __name__=='__main__':
    recs,skipped,cnt=records(sys.argv[1]); w=csv.writer(open(sys.argv[2],'w',newline='')); w.writerow(['collection_key','record_offset','slot_index','attr_key_hash64','flags','u32_hex','f32_if_flag_0x4000'])
    n=0
    for ck,off,slots in recs:
        for i,(k,v,f) in enumerate(slots):
            fl='%.6g'%struct.unpack('>f',struct.pack('>I',v))[0] if f&0x4000 and f==0x4000 else ''
            w.writerow(['%016x'%ck,off,i,'%016x'%k,'%08x'%f,'%08x'%v,fl]); n+=1
    print(len(recs),'records parsed,',skipped,'skipped of',cnt,'|',n,'slots')
