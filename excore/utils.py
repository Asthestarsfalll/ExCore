import functools
import threading
import time


class CacheOut:
    def __call__(self, func):
        @functools.wraps(func)
        def _cache(self):
            if not hasattr(self, "cached_elem"):
                setattr(self, "cached_elem", func(self))
            return getattr(self, "cached_elem")

        return _cache


class FileLock:
    def __init__(self, file_path, timeout=15):
        self.file_path = file_path
        self.timeout = timeout
        self.lock = threading.Lock()

    def __enter__(self):
        start_time = time.time()
        while not self.lock.acquire(False):
            if time.time() - start_time >= self.timeout:
                raise TimeoutError("Failed to acquire lock on file")
            time.sleep(0.1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release()
