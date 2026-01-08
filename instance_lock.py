import os
import sys

from config import LOG_DIR
from log import log


def ensure_single_instance():
    os.makedirs(LOG_DIR, exist_ok=True)
    lock_path = os.path.join(LOG_DIR, "bot.lock")
    lock_file = open(lock_path, "a+", encoding="utf-8")
    try:
        lock_file.seek(0)
        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                message = f"Another instance is already running (lock: {lock_path})"
                log(message, log_level="error")
                print(message)
                lock_file.close()
                sys.exit(1)
        else:
            import fcntl

            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                message = f"Another instance is already running (lock: {lock_path})"
                log(message, log_level="error")
                print(message)
                lock_file.close()
                sys.exit(1)

        lock_file.seek(0)
        lock_file.truncate()
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        log(f"Acquired instance lock: {lock_path}", log_level="info")
        return lock_file
    except Exception:
        lock_file.close()
        raise
