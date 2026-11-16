"""Neural net dumper for data/neuralnet/nnet*.dat (little-endian float32 stream; layout verified by size closure in tools/verify_all.py).
float[0]=L (layer count), float[1..L]=layer sizes (input..output); remaining = 2*(n0+nL) normalisation values + (n_i+1)*n_{i+1} weight/bias blocks.
Order of those blocks is NOT verified."""
import struct,sys
d=open(sys.argv[1],'rb').read(); f=struct.unpack('<%df'%(len(d)//4),d); L=int(f[0]); sz=[int(x) for x in f[1:1+L]]
print('layers',sz,'floats',len(f)); rest=f[1+L:]; print('remaining',len(rest),'= weights',sum((sz[i]+1)*sz[i+1] for i in range(L-1)),'+ norm',2*(sz[0]+sz[-1]))
print('min/max',min(rest),max(rest))
