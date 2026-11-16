"""Structural dump of EA Attrib/Vault files (.vlt) found in data0.big.
Chunk walk: tag(4) + u32BE total size (incl. 8-byte header). Observed tags: Vers StrN DepN DatN ExpN PtrN EndC.
ExpN: tag | u32 size | u32 0 | u32 count | count*24-byte records, all big-endian:
      collectionKey u64 | classKey u64 | dataSize u32 | dataOffset u32
dataOffset is a FILE-absolute offset into the .vlt (first = DatN start+8 = 120); sorted by offset the records tile DatN with no gaps
(verified on all 3 vaults by tools/verify_all.py). Last record ends 8 bytes before DatN ends (trailing pad)."""
import struct,sys,collections,csv
def chunks(b):
    p=0;out=[]
    while p+8<=len(b):
        t=b[p:p+4]; s=struct.unpack('>I',b[p+4:p+8])[0]
        out.append((t.decode('latin1'),p,s)); p+=s
        if s<8: break
    return out
def exports(b):
    ch={t:(p,s) for t,p,s in chunks(b)}
    p,s=ch['ExpN']; cnt=struct.unpack('>I',b[p+12:p+16])[0]; rec=[]
    for i in range(cnt):
        o=p+16+i*24; ck,cl,sz,off=struct.unpack('>QQII',b[o:o+24]); rec.append((ck,cl,off,sz))
    return ch,cnt,rec
if __name__=='__main__':
    b=open(sys.argv[1],'rb').read(); ch,cnt,rec=exports(b)
    print('chunks',chunks(b)); print('exports',cnt, 'expected size',16+24*cnt,'actual',ch['ExpN'][1])
    cls=collections.Counter(r[1] for r in rec); print('classes',len(cls))
    for k,v in cls.most_common(): print(' class %016x x%d'%(k,v))
    if len(sys.argv)>2:
        w=csv.writer(open(sys.argv[2],'w',newline='')); w.writerow(['collection_key','class_key','offset','size'])
        for r in rec: w.writerow(['%016x'%r[0],'%016x'%r[1],r[2],r[3]])
