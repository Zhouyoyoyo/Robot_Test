"""PingID global lock module.

Provide cross-process file lock for PingID operations.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path


def _default_lock_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / "pingid.lock"


@contextmanager
def pingid_global_lock():
    lockfile = os.environ.get("PW_PINGID_LOCKFILE")
    lock_path = Path(lockfile) if lockfile else _default_lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    fh = lock_path.open("a+")
    try:
        if os.name == "nt":
            import msvcrt

            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            if os.name == "nt":
                import msvcrt

                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()
