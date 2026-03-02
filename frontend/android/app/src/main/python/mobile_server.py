import os
import threading
import sys

import uvicorn

from main import app

_started = False
_lock = threading.Lock()


def start_server(files_dir: str) -> bool:
    global _started

    with _lock:
        if _started:
            return True

        db_path = os.path.join(files_dir, "pomodoro.db")
        os.environ.setdefault("POMODORO_DB_PATH", db_path)
        os.environ.setdefault("POMODORO_HOST", "127.0.0.1")
        os.environ.setdefault("POMODORO_PORT", "8000")
        os.environ.setdefault("POMODORO_LOG_LEVEL", "warning")

        vendor_dir = os.path.join(os.path.dirname(__file__), "vendor")
        if os.path.isdir(vendor_dir) and vendor_dir not in sys.path:
            sys.path.insert(0, vendor_dir)
        _started = True

    uvicorn.run(
        app,
        host=os.environ["POMODORO_HOST"],
        port=int(os.environ["POMODORO_PORT"]),
        log_level=os.environ["POMODORO_LOG_LEVEL"],
    )
    return True
