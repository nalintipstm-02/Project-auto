import threading
from core.build_runtime_memory import build_runtime_memory

_runtime_state = None
_runtime_lock = threading.Lock()


def load_runtime_state():
    global _runtime_state
    print("?? Loading runtime state into memory...")

    with _runtime_lock:
        _runtime_state = build_runtime_memory()

    print("? Runtime state loaded")


def get_runtime_state():
    with _runtime_lock:
        return _runtime_state


def reload_runtime_state():
    global _runtime_state
    print("?? Reloading runtime state...")

    with _runtime_lock:
        _runtime_state = build_runtime_memory()

    print("? Runtime state reloaded")
