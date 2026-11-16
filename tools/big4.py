import struct,sys,os,pathlib
def parse(path):
    d=open(path,'rb')
    h=d.read(16)
    assert h[:4] in (b'BIG4',b'BIGF')
    fsize=struct.unpack('<I',h[4:8])[0]; cnt,hend=struct.unpack('>II',h[8:16])
    toc=d.read(hend-16); p=0; ents=[]
    for _ in range(cnt):
        off,size=struct.unpack('>II',toc[p:p+8]); p+=8
        e=toc.index(b'\0',p); ents.append((toc[p:e].decode('latin1'),off,size)); p=e+1
    return fsize,hend,p+16,ents
def extract(path,out,filt=None):
    fsize,hend,tocend,ents=parse(path); f=open(path,'rb'); n=0
    for name,off,size in ents:
        if filt and not filt(name): continue
        f.seek(off); b=f.read(size); t=pathlib.Path(out)/name.replace(':','_')
        t.parent.mkdir(parents=True,exist_ok=True); t.write_bytes(b); n+=1
    return n
if __name__=='__main__':
    for p in sys.argv[1:]:
        fs,he,te,en=parse(p); print(p,'filesize',fs,'actual',os.path.getsize(p),'hend',hex(he),'tocend',hex(te),'n',len(en))
        for e in en: print('  ',e[0],hex(e[1]),e[2])
