"""Hardware watchpoint tracer for the user's own running fifastreet.exe (research aid).
Sets x86-64 debug registers DR0-DR3 (read/write, 4 bytes) on the host addresses of live attribute values in every thread,
logs the instruction pointer of each access, then resolves RIPs to recompiled guest functions via the (guest, host) function
table of fifastreet_init.cpp that is resident in the process. Usage: watch_reads.py <pid> <seconds> name=hostaddr [...]"""
import ctypes, ctypes.wintypes as wt, sys, time, struct, collections, json

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_DEBUG_EVENT, CREATE_THREAD_DEBUG_EVENT, CREATE_PROCESS_DEBUG_EVENT, EXIT_THREAD_DEBUG_EVENT = 1, 2, 3, 4
EXIT_PROCESS_DEBUG_EVENT, LOAD_DLL_DEBUG_EVENT = 5, 6
EXCEPTION_SINGLE_STEP = 0x80000004
CONTEXT_AMD64 = 0x100000
CONTEXT_DEBUG_REGISTERS = CONTEXT_AMD64 | 0x10
CONTEXT_CONTROL = CONTEXT_AMD64 | 0x1
THREAD_ALL = 0x1FFFFF


class M128(ctypes.Structure):
    _fields_ = [('Low', ctypes.c_ulonglong), ('High', ctypes.c_longlong)]


class CONTEXT(ctypes.Structure):
    _fields_ = [('P1Home', ctypes.c_ulonglong), ('P2Home', ctypes.c_ulonglong), ('P3Home', ctypes.c_ulonglong),
                ('P4Home', ctypes.c_ulonglong), ('P5Home', ctypes.c_ulonglong), ('P6Home', ctypes.c_ulonglong),
                ('ContextFlags', wt.DWORD), ('MxCsr', wt.DWORD),
                ('SegCs', wt.WORD), ('SegDs', wt.WORD), ('SegEs', wt.WORD), ('SegFs', wt.WORD), ('SegGs', wt.WORD), ('SegSs', wt.WORD),
                ('EFlags', wt.DWORD),
                ('Dr0', ctypes.c_ulonglong), ('Dr1', ctypes.c_ulonglong), ('Dr2', ctypes.c_ulonglong), ('Dr3', ctypes.c_ulonglong),
                ('Dr6', ctypes.c_ulonglong), ('Dr7', ctypes.c_ulonglong),
                ('Rax', ctypes.c_ulonglong), ('Rcx', ctypes.c_ulonglong), ('Rdx', ctypes.c_ulonglong), ('Rbx', ctypes.c_ulonglong),
                ('Rsp', ctypes.c_ulonglong), ('Rbp', ctypes.c_ulonglong), ('Rsi', ctypes.c_ulonglong), ('Rdi', ctypes.c_ulonglong),
                ('R8', ctypes.c_ulonglong), ('R9', ctypes.c_ulonglong), ('R10', ctypes.c_ulonglong), ('R11', ctypes.c_ulonglong),
                ('R12', ctypes.c_ulonglong), ('R13', ctypes.c_ulonglong), ('R14', ctypes.c_ulonglong), ('R15', ctypes.c_ulonglong),
                ('Rip', ctypes.c_ulonglong), ('Flt', ctypes.c_ubyte * 512), ('Vec', M128 * 26), ('VCtl', ctypes.c_ulonglong),
                ('DbgCtl', ctypes.c_ulonglong), ('LBTR', ctypes.c_ulonglong), ('LBFR', ctypes.c_ulonglong),
                ('LETR', ctypes.c_ulonglong), ('LEFR', ctypes.c_ulonglong)]


class EXCEPTION_RECORD(ctypes.Structure):
    pass


EXCEPTION_RECORD._fields_ = [('ExceptionCode', wt.DWORD), ('ExceptionFlags', wt.DWORD), ('ExceptionRecord', ctypes.c_void_p),
                             ('ExceptionAddress', ctypes.c_void_p), ('NumberParameters', wt.DWORD), ('Pad', wt.DWORD),
                             ('ExceptionInformation', ctypes.c_ulonglong * 15)]


class DBG_EVENT(ctypes.Structure):
    _fields_ = [('dwDebugEventCode', wt.DWORD), ('dwProcessId', wt.DWORD), ('dwThreadId', wt.DWORD), ('Pad', wt.DWORD),
                ('u', ctypes.c_byte * 160)]


k32.OpenThread.restype = wt.HANDLE
k32.GetThreadContext.argtypes = [wt.HANDLE, ctypes.POINTER(CONTEXT)]
k32.SetThreadContext.argtypes = [wt.HANDLE, ctypes.POINTER(CONTEXT)]
k32.WaitForDebugEvent.argtypes = [ctypes.POINTER(DBG_EVENT), wt.DWORD]
k32.ContinueDebugEvent.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD]


def set_drs(tid, addrs):
    h = k32.OpenThread(THREAD_ALL, False, tid)
    if not h:
        return False
    k32.SuspendThread(h)
    ctx = CONTEXT()
    ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS
    if k32.GetThreadContext(h, ctypes.byref(ctx)):
        regs = ['Dr0', 'Dr1', 'Dr2', 'Dr3']
        dr7 = 0
        for i, a in enumerate(addrs[:4]):
            setattr(ctx, regs[i], a)
            dr7 |= (1 << (i * 2)) | (3 << (16 + i * 4)) | (3 << (18 + i * 4))  # local enable, RW=3 (read/write), LEN=3 (4 bytes)
        ctx.Dr7 = dr7
        ctx.Dr6 = 0
        k32.SetThreadContext(h, ctypes.byref(ctx))
    k32.ResumeThread(h)
    k32.CloseHandle(h)
    return True


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [('cb', wt.DWORD), ('lpReserved', wt.LPWSTR), ('lpDesktop', wt.LPWSTR), ('lpTitle', wt.LPWSTR),
                ('dwX', wt.DWORD), ('dwY', wt.DWORD), ('dwXSize', wt.DWORD), ('dwYSize', wt.DWORD),
                ('dwXCountChars', wt.DWORD), ('dwYCountChars', wt.DWORD), ('dwFillAttribute', wt.DWORD),
                ('dwFlags', wt.DWORD), ('wShowWindow', wt.WORD), ('cbReserved2', wt.WORD), ('lpReserved2', ctypes.c_void_p),
                ('hStdInput', wt.HANDLE), ('hStdOutput', wt.HANDLE), ('hStdError', wt.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [('hProcess', wt.HANDLE), ('hThread', wt.HANDLE), ('dwProcessId', wt.DWORD), ('dwThreadId', wt.DWORD)]


def launch_debugged(exe, cmdline, cwd):
    """CreateProcess with DEBUG_ONLY_THIS_PROCESS: the debugger sees the very first thread before any game code runs."""
    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()
    ok = k32.CreateProcessW(exe, cmdline, None, None, False, 0x2, None, cwd, ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        raise OSError('CreateProcess failed %d' % ctypes.get_last_error())
    return pi.dwProcessId


def main():
    launch = sys.argv[1] == 'launch'
    if launch:
        # watch_reads.py launch <exe> <cwd> <seconds> name=hostaddr ...   (REX_* environment is inherited)
        exe, cwd, secs, rest = sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5:]
        pid = launch_debugged(exe, '"%s" --game_data_root=%s' % (exe, __import__('os').environ.get('REX_GAME_DATA_ROOT', '')), cwd)
        sys.argv = [sys.argv[0], str(pid), str(secs)] + rest
    pid = int(sys.argv[1])
    secs = float(sys.argv[2])
    targets = {}
    for a in sys.argv[3:]:
        n, v = a.split('=')
        targets[int(v, 16)] = n
    addrs = list(targets)
    if not launch:
        if not k32.DebugActiveProcess(pid):
            raise OSError('DebugActiveProcess failed %d' % ctypes.get_last_error())
    k32.DebugSetProcessKillOnExit(False)
    hits = collections.Counter()
    threads = set()
    t0 = time.time()
    ev = DBG_EVENT()
    n_ev = 0
    while time.time() - t0 < secs:
        if not k32.WaitForDebugEvent(ctypes.byref(ev), 200):
            continue
        n_ev += 1
        cont = DBG_CONTINUE
        code = ev.dwDebugEventCode
        tid = ev.dwThreadId
        if code in (CREATE_PROCESS_DEBUG_EVENT, CREATE_THREAD_DEBUG_EVENT):
            if tid not in threads:
                threads.add(tid)
                set_drs(tid, addrs)
        elif code == EXCEPTION_DEBUG_EVENT:
            rec = EXCEPTION_RECORD.from_buffer_copy(ctypes.string_at(ctypes.addressof(ev.u), ctypes.sizeof(EXCEPTION_RECORD)))
            if rec.ExceptionCode == EXCEPTION_SINGLE_STEP:
                h = k32.OpenThread(THREAD_ALL, False, tid)
                ctx = CONTEXT()
                ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS | CONTEXT_CONTROL
                if k32.GetThreadContext(h, ctypes.byref(ctx)):
                    which = [i for i in range(4) if ctx.Dr6 & (1 << i)]
                    for i in which:
                        hits[(targets[addrs[i]], ctx.Rip)] += 1
                    ctx.Dr6 = 0
                    k32.SetThreadContext(h, ctypes.byref(ctx))
                k32.CloseHandle(h)
            else:
                cont = DBG_EXCEPTION_NOT_HANDLED
        elif code == EXIT_PROCESS_DEBUG_EVENT:
            k32.ContinueDebugEvent(ev.dwProcessId, tid, DBG_CONTINUE)
            break
        k32.ContinueDebugEvent(ev.dwProcessId, tid, cont)
        # threads that existed before attach: set once on first sight
        if tid not in threads and code == EXCEPTION_DEBUG_EVENT:
            threads.add(tid)
            set_drs(tid, addrs)
    k32.DebugActiveProcessStop(pid)
    out = [{'name': n, 'rip': hex(r), 'count': c} for (n, r), c in hits.most_common()]
    json.dump(out, open(sys.argv[0] + '.hits.json', 'w'))
    print('events', n_ev, 'distinct (value,rip) hits', len(out))
    for o in out[:40]:
        print(o)


if __name__ == '__main__':
    main()
