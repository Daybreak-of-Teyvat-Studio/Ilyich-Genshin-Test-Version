# -*- coding: utf-8 -*-
"""用 Restart Manager API 查出到底哪个进程锁住了文件。"""
import os, ctypes
import ctypes.wintypes as wt

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
H = os.path.join(G, ".workbuddy")

TARGETS = [
    os.path.join(G, "map", "heightmap.bmp"),
    os.path.join(H, "heightmap_soft", "preview_full.png"),
    os.path.join(H, "heightmap_soft", "report.txt"),
    os.path.join(H, "heightmap_soft", "verify.txt"),
    os.path.join(H, "heightmap_soft", "compare_full.png"),
    os.path.join(H, "heightmap.bmp"),
    os.path.join(H, "DOT MAP 3.0.bmp"),
]


class RM_UNIQUE_PROCESS(ctypes.Structure):
    _fields_ = [("dwProcessId", wt.DWORD), ("ProcessStartTime", wt.FILETIME)]


class RM_PROCESS_INFO(ctypes.Structure):
    _fields_ = [("Process", RM_UNIQUE_PROCESS),
                ("strAppName", ctypes.c_wchar * 256),
                ("strServiceShortName", ctypes.c_wchar * 64),
                ("ApplicationType", ctypes.c_uint),
                ("AppStatus", ctypes.c_uint),
                ("TSSessionId", wt.DWORD),
                ("bRestartable", wt.BOOL)]


def who_locks(path):
    rm = ctypes.WinDLL("rstrtmgr")
    session = wt.DWORD()
    key = ctypes.create_unicode_buffer(512)
    rc = rm.RmStartSession(ctypes.byref(session), None, key)
    if rc != 0:
        return ["RmStartSession rc=%d" % rc]
    try:
        files = (ctypes.c_wchar_p * 1)(path)
        rc = rm.RmRegisterResources(session, 1, files, 0, None, 0, None)
        if rc != 0:
            return ["RmRegisterResources rc=%d" % rc]
        need = wt.DWORD(0); reasons = wt.DWORD(0)
        rc = rm.RmGetList(session, ctypes.byref(need), None, None, ctypes.byref(reasons))
        if rc not in (0, 234):
            return ["RmGetList probe rc=%d" % rc]
        n = need.value
        if n == 0:
            return []
        cnt = wt.DWORD(n)
        arr = (RM_PROCESS_INFO * n)()
        rc = rm.RmGetList(session, ctypes.byref(need), ctypes.byref(cnt), arr, ctypes.byref(reasons))
        if rc != 0:
            return ["RmGetList rc=%d" % rc]
        return [("%s (pid %d)" % (arr[i].strAppName, arr[i].Process.dwProcessId))
                for i in range(cnt.value)]
    finally:
        rm.RmEndSession(session)


def writable(path):
    try:
        open(path, "r+b").close()
        return True
    except Exception:
        return False


for p in TARGETS:
    ex = os.path.isfile(p)
    w = writable(p) if ex else None
    lock = who_locks(p) if ex else []
    print("%-46s exists=%-5s writable=%-5s locks=%s"
          % (os.path.basename(p), ex, w, lock if lock else "无"))
