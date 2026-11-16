"""Reader for hook dumps (records: u32 LE base, u32 LE size, raw bytes) written by fifastreet_app.h DumpGuestRange."""
import struct,os,sys,re
def regions(path):
    out=[]; sz=os.path.getsize(path)
    with open(path,'rb') as f:
        while f.tell()+8<=sz:
            b,s=struct.unpack('<II',f.read(8)); out.append((b,s,f.tell())); f.seek(s,1)
    return out
def find(path,needle):
    hits=[]
    with open(path,'rb') as f:
        for b,s,off in regions(path):
            f.seek(off); d=f.read(s); i=d.find(needle)
            while i!=-1: hits.append(b+i); i=d.find(needle,i+1)
    return hits
if __name__=='__main__':
    for p in sys.argv[2:]: print(p,[hex(h) for h in find(p,sys.argv[1].encode())[:10]])
