"""Read-only scanner for the running fifastreet.exe (the user's own process): enumerates committed readable regions with
VirtualQueryEx and searches them with ReadProcessMemory. Guest memory is stored big-endian in the host process.
Usage: procmem.py <pid> hex:<hexbytes> [hex:<hexbytes> ...]"""
import ctypes, ctypes.wintypes as wt, sys

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
PAGE_NOACCESS = 0x01
PAGE_GUARD = 0x100


class MBI(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_void_p), ('AllocationBase', ctypes.c_void_p), ('AllocationProtect', wt.DWORD),
                ('PartitionId', wt.WORD), ('RegionSize', ctypes.c_size_t), ('State', wt.DWORD), ('Protect', wt.DWORD),
                ('Type', wt.DWORD)]


k32.OpenProcess.restype = wt.HANDLE
k32.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
k32.VirtualQueryEx.restype = ctypes.c_size_t
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


def open_proc(pid):
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        raise OSError('OpenProcess failed: %d' % ctypes.get_last_error())
    return h


def regions(h):
    addr = 0
    mbi = MBI()
    while addr < 0x7FFFFFFFFFFF:
        if not k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        base = mbi.BaseAddress or 0
        if mbi.State == MEM_COMMIT and not (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) and mbi.Protect:
            yield base, mbi.RegionSize
        addr = base + mbi.RegionSize


def read(h, addr, n):
    buf = ctypes.create_string_buffer(n)
    got = ctypes.c_size_t(0)
    if not k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)):
        return buf.raw[:got.value]
    return buf.raw[:got.value]


def scan(h, pats, chunk=64 << 20):
    hits = {p: [] for p in pats}
    total = 0
    for base, size in regions(h):
        off = 0
        while off < size:
            n = min(chunk, size - off)
            d = read(h, base + off, n)
            total += len(d)
            for p in pats:
                i = d.find(p)
                while i != -1:
                    hits[p].append(base + off + i)
                    i = d.find(p, i + 1)
            off += n - 64 if n == chunk and off + n < size else n
    return hits, total


if __name__ == '__main__':
    pid = int(sys.argv[1])
    pats = [bytes.fromhex(a[4:]) for a in sys.argv[2:]]
    h = open_proc(pid)
    hits, total = scan(h, pats)
    print('scanned %.1f MB' % (total / 1e6))
    for p, v in hits.items():
        print(p.hex(), len(v), [hex(x) for x in v[:8]])
