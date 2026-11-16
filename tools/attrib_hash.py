"""Attrib name hash recovered from the lifted code: sub_8269C930(str) -> sub_8269C508(str, len, 0xABCDEF0011223344)
sub_8269C508 = Bob Jenkins lookup8 (a=b=level, c=0x9E3779B97F4A7C13, 24-byte LE blocks, c += len, tail bytes 16.. shifted <<8)."""
M=(1<<64)-1
SEED=0xABCDEF0011223344
def _mix(a,b,c):
    a=(a-b-c)&M; a^=c>>43; b=(b-c-a)&M; b^=(a<<9)&M; c=(c-a-b)&M; c^=b>>8
    a=(a-b-c)&M; a^=c>>38; b=(b-c-a)&M; b^=(a<<23)&M; c=(c-a-b)&M; c^=b>>5
    a=(a-b-c)&M; a^=c>>35; b=(b-c-a)&M; b^=(a<<49)&M; c=(c-a-b)&M; c^=b>>11
    a=(a-b-c)&M; a^=c>>12; b=(b-c-a)&M; b^=(a<<18)&M; c=(c-a-b)&M; c^=b>>22
    return a,b,c
def lookup8(k,level=SEED):
    if isinstance(k,str): k=k.encode('latin1')
    L=len(k); a=b=level; c=0x9e3779b97f4a7c13; p=0
    while L-p>=24:
        a=(a+int.from_bytes(k[p:p+8],'little'))&M; b=(b+int.from_bytes(k[p+8:p+16],'little'))&M; c=(c+int.from_bytes(k[p+16:p+24],'little'))&M
        a,b,c=_mix(a,b,c); p+=24
    c=(c+L)&M; r=k[p:]+b'\0'*24
    a=(a+int.from_bytes(r[0:8],'little'))&M; b=(b+int.from_bytes(r[8:16],'little'))&M
    c=(c+(int.from_bytes(r[16:23],'little')<<8))&M
    a,b,c=_mix(a,b,c); return c
def name_hash(s): return lookup8(s,SEED)
