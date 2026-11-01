"""Permission hardening only: not encryption or a same-UID security boundary.

Never parse/rewrite CLI-owned canonical bytes. The official CLI alone owns refresh.
Root lifecycle chmod can still race the app; exclude credentials from that lifecycle
before claiming continuous protection. Child umask is explicit, not thread preexec_fn.
"""
import os
from pathlib import Path
import stat


def _mode(path, mode, is_dir=False):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    if is_dir:
        flags |= os.O_DIRECTORY
    try:
        fd = os.open(path, flags)
        try:
            info = os.fstat(fd)
            if not (stat.S_ISDIR(info.st_mode) if is_dir else stat.S_ISREG(info.st_mode)):
                raise ValueError()
            os.fchmod(fd, mode)
        finally:
            os.close(fd)
    except (OSError, ValueError):
        raise ValueError("Private storage unavailable.") from None


def directory(path):
    path = Path(path)
    try:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError:
        raise ValueError("Private storage unavailable.") from None
    _mode(path, 0o700, is_dir=True)
    return path


def harden_login(path):
    root = directory(path)
    for name in (".credentials.json", ".claude.json"):
        item = root / name
        if item.exists() or item.is_symlink():
            _mode(item, 0o600)
