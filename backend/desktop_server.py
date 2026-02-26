import os

import uvicorn

from main import app


def _resolve_host() -> str:
    return os.getenv("POMODORO_HOST", "127.0.0.1")


def _resolve_port() -> int:
    value = os.getenv("POMODORO_PORT", "8000")
    try:
        return int(value)
    except ValueError:
        return 8000


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=_resolve_host(),
        port=_resolve_port(),
        log_level=os.getenv("POMODORO_LOG_LEVEL", "info"),
    )
