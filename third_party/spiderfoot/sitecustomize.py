import multiprocessing.synchronize as s

s.SemLock.__init__.__globals__["register"] = lambda *a, **k: None
s.SemLock.__init__.__globals__["unregister"] = lambda *a, **k: None
