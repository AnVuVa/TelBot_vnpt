import threading
import time
from collections import deque


class RateLimiter:
    def __init__(self, rate_per_second: int):
        self.rate_per_second = max(1, rate_per_second)
        self.lock = threading.Lock()
        self.timestamps = deque()

    def wait_for_slot(self):
        while True:
            with self.lock:
                now = time.monotonic()
                while self.timestamps and now - self.timestamps[0] >= 1:
                    self.timestamps.popleft()
                if len(self.timestamps) < self.rate_per_second:
                    self.timestamps.append(now)
                    return
                sleep_for = 1 - (now - self.timestamps[0])
            time.sleep(max(sleep_for, 0.01))
