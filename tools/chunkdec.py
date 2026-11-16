"""Decoder for EA 'chunklzx'/'chunkzip' containers (+RefPack). Format taken from
port_code/Tools/ReStreetAssetScan/Program.cs DecodeChunk and LzxDecoder.cs (libmspack port).
Header: 'chunklzx' | u32BE ver=2 | u32BE full | u32BE chunk | pad to 0x28; then per chunk:
 align16 +8 -> u32BE n, u32BE kind(1 deflate,3 xbox-lzx,4 raw) + n bytes."""
import struct, zlib, sys
NUM_CHARS=256; MIN_MATCH=2; NPL=7; NSL=249
EXTRA=[0]*52; POSB=[0]*51
j=0
for i in range(0,51,2):
    EXTRA[i]=EXTRA[i+1]=j
    if i!=0 and j<17: j+=1
j=0
for i in range(51): POSB[i]=j; j+=1<<EXTRA[i]
class Bits:
    def __init__(s,b): s.b=b; s.p=0; s.buf=0; s.n=0
    def ensure(s,k):
        while s.n<k:
            lo=s.b[s.p] if s.p<len(s.b) else 0; hi=s.b[s.p+1] if s.p+1<len(s.b) else 0; s.p+=2
            s.buf|=((hi<<8)|lo)<<(16-s.n) if False else 0
            s.buf=(s.buf<<16)|((hi<<8)|lo); s.n+=16
    def peek(s,k): s.ensure(k); return (s.buf>>(s.n-k))&((1<<k)-1)
    def read(s,k):
        if k==0: return 0
        v=s.peek(k); s.n-=k; s.buf&=(1<<s.n)-1; return v
def mk(lens):
    codes={}; code=0
    for l in range(1,17):
        for sym,x in enumerate(lens):
            if x==l: codes[(l,code)]=sym; code+=1
        code<<=1
    return codes
def sym(bits,codes):
    c=0
    for l in range(1,17):
        c=(c<<1)|bits.read(1)
        r=codes.get((l,c))
        if r is not None: return r
    raise ValueError('bad huff')
class Lzx:
    def __init__(s,wb=17):
        s.ws=1<<wb; s.win=bytearray(b'\xdc'*s.ws); s.wp=0; s.R=[1,1,1]
        ps=wb*2 if wb<20 else (42 if wb==20 else 50); s.main_el=NUM_CHARS+ps*8
        s.hdr=False; s.rem=0; s.bt=0; s.blen=0; s.main=[0]*656; s.len=[0]*250; s.al=[0]*8
    def rl(s,b,lens,first,last):
        pt=mk([b.read(4) for _ in range(20)]); x=first
        while x<last:
            z=sym(b,pt)
            if z==17:
                y=b.read(4)+4
                for _ in range(y): lens[x]=0; x+=1
            elif z==18:
                y=b.read(5)+20
                for _ in range(y): lens[x]=0; x+=1
            elif z==19:
                y=b.read(1)+4; z=sym(b,pt); z=lens[x]-z
                if z<0: z+=17
                for _ in range(y): lens[x]=z; x+=1
            else:
                z=lens[x]-z
                if z<0: z+=17
                lens[x]=z; x+=1
    def frame(s,data,outlen):
        b=Bits(data); togo=outlen; win=s.win; wp=s.wp; R=s.R
        if not s.hdr:
            if b.read(1): b.read(16); b.read(16)
            s.hdr=True
        while togo>0:
            if s.rem==0:
                if s.bt==3:
                    if s.blen&1: b.p+=1
                    b.n=0; b.buf=0
                s.bt=b.read(3); s.rem=(b.read(16)<<8)|b.read(8); s.blen=s.rem
                if s.bt==2:
                    s.al=[b.read(3) for _ in range(8)]; s.alc=mk(s.al)
                if s.bt in(1,2):
                    self_main=s.main
                    s.rl(b,s.main,0,256); s.rl(b,s.main,256,s.main_el); s.mc=mk(s.main)
                    s.rl(b,s.len,0,NSL); s.lc=mk(s.len)
                elif s.bt==3:
                    b.ensure(16)
                    if b.n>16: b.p-=2
                    b.n=0; b.buf=0
                    for i in range(3): R[i]=struct.unpack('<I',b.b[b.p:b.p+4])[0]; b.p+=4
                else: raise ValueError('block type %d'%s.bt)
            while s.rem>0 and togo>0:
                run=min(s.rem,togo); togo-=run; s.rem-=run; wp&=s.ws-1
                if s.bt==3:
                    win[wp:wp+run]=b.b[b.p:b.p+run]; b.p+=run; wp+=run; continue
                while run>0:
                    m=sym(b,s.mc)
                    if m<256: win[wp]=m; wp+=1; run-=1; continue
                    m-=256; ml=m&7
                    if ml==7: ml+=sym(b,s.lc)
                    ml+=MIN_MATCH; mo=m>>3
                    if mo>2:
                        if s.bt==1:
                            if mo!=3: mo=POSB[mo]-2+b.read(EXTRA[mo])
                            else: mo=1
                        else:
                            ex=EXTRA[mo]; mo=POSB[mo]-2
                            if ex>3: mo+=b.read(ex-3)<<3; mo+=sym(b,s.alc)
                            elif ex==3: mo+=sym(b,s.alc)
                            elif ex>0: mo+=b.read(ex)
                            else: mo=1
                        R[2]=R[1]; R[1]=R[0]; R[0]=mo
                    elif mo==0: mo=R[0]
                    elif mo==1: mo=R[1]; R[1]=R[0]; R[0]=mo
                    else: mo=R[2]; R[2]=R[0]; R[0]=mo
                    run-=ml
                    for _ in range(ml):
                        win[wp]=win[(wp-mo)%s.ws]; wp+=1
        st=wp if wp else s.ws; st-=outlen; s.wp=wp
        return bytes(win[st:st+outlen])
def decode_chunk(b):
    assert b[:8] in(b'chunklzx',b'chunkzip',b'chunkref')
    full,chunk=struct.unpack('>II',b[12:20]); p=40; out=bytearray()
    while len(out)<full:
        p=(p+7)//16*16+8; n,kind=struct.unpack('>II',b[p:p+8]); p+=8
        target=min(chunk,full-len(out)); end=p+n
        if kind==4: out+=b[p:end]
        elif kind==1: out+=zlib.decompress(b[p:end],-15)
        elif kind==2:
            r=refpack(b[p:end]); assert len(r)==target,(len(r),target); out+=r
        elif kind==3:
            d=Lzx(17); produced=0
            while p<end and produced<target:
                osz=32768
                if b[p]==255: osz=(b[p+1]<<8)|b[p+2]; isz=(b[p+3]<<8)|b[p+4]; p+=5
                else: isz=(b[p]<<8)|b[p+1]; p+=2
                out+=d.frame(b[p:p+isz],osz); p+=isz; produced+=osz
        else: raise ValueError('kind %d'%kind)
        assert len(out)<=full and p<=len(b)
        p=end
    assert len(out)==full,(len(out),full)
    return bytes(out)
def refpack(b):
    if len(b)<5 or b[0]!=0x10 or b[1]!=0xfb: return b
    L=(b[2]<<16)|(b[3]<<8)|b[4]; p=5; r=bytearray()
    while len(r)<L and p<len(b):
        c=b[p]; p+=1; cp=0; d=0
        if c<0x80: x=b[p]; p+=1; lit=c&3; cp=((c&0x1c)>>2)+3; d=((c&0x60)<<3)+x+1
        elif c<0xc0: x=b[p]; y=b[p+1]; p+=2; lit=x>>6; cp=(c&0x3f)+4; d=((x&0x3f)<<8)+y+1
        elif c<0xe0: x,y,z=b[p],b[p+1],b[p+2]; p+=3; lit=c&3; cp=((c&0x0c)<<6)+z+5; d=((c&0x10)<<12)+(x<<8)+y+1
        elif c<0xfc: lit=((c&0x1f)<<2)+4
        else: lit=c&3
        r+=b[p:p+lit]; p+=lit
        for _ in range(cp): r.append(r[-d])
        if c>=0xfc: break
    return bytes(r)
def decode(b):
    if b[:8] in(b'chunklzx',b'chunkzip',b'chunkref'): b=decode_chunk(b)
    return refpack(b)
if __name__=='__main__':
    for f in sys.argv[1:]:
        o=decode(open(f,'rb').read()); open(f+'.dec','wb').write(o); print(f,len(o),o[:16])
