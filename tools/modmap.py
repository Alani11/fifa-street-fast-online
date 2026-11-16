"""Map host addresses of a running process to loaded modules: modmap.py <pid> <hexaddr> [...]"""
import ctypes, ctypes.wintypes as wt, sys, os

ps = ctypes.WinDLL('psapi', use_last_error=True)
k = ctypes.WinDLL('kernel32', use_last_error=True)
k.OpenProcess.restype = wt.HANDLE
ps.GetModuleInformation.argtypes = [wt.HANDLE, wt.HMODULE, ctypes.c_void_p, wt.DWORD]
ps.GetModuleFileNameExW.argtypes = [wt.HANDLE, wt.HMODULE, wt.LPWSTR, wt.DWORD]
ps.EnumProcessModulesEx.argtypes = [wt.HANDLE, ctypes.c_void_p, wt.DWORD, ctypes.c_void_p, wt.DWORD]


class MI(ctypes.Structure):
    _fields_ = [('Base', ctypes.c_void_p), ('Size', wt.DWORD), ('Entry', ctypes.c_void_p)]


def modules(pid):
    h = k.OpenProcess(0x0410, False, pid)
    mods = (wt.HMODULE * 2048)()
    need = wt.DWORD()
    ps.EnumProcessModulesEx(h, mods, ctypes.sizeof(mods), ctypes.byref(need), 3)
    out = []
    for m in mods[:need.value // ctypes.sizeof(wt.HMODULE)]:
        mi = MI()
        ps.GetModuleInformation(h, m, ctypes.byref(mi), ctypes.sizeof(mi))
        nm = ctypes.create_unicode_buffer(260)
        ps.GetModuleFileNameExW(h, m, nm, 260)
        out.append((mi.Base, mi.Size, nm.value))
    return out


if __name__ == '__main__':
    mods = modules(int(sys.argv[1]))
    for a in sys.argv[2:]:
        rip = int(a, 16)
        hit = [(os.path.basename(n), hex(rip - b), hex(b)) for b, s, n in mods if b <= rip < b + s]
        print(hex(rip), hit)
