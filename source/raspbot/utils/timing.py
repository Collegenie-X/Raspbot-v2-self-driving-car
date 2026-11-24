"""루프 주기 측정 유틸리티."""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Optional


class FpsTimer:
    def __init__(self, window: int = 10) -> None:
        self.window = window
        self._timestamps: Deque[float] = deque(maxlen=window)

    def lap(self) -> Optional[float]:
        now = time.perf_counter()
        self._timestamps.append(now)
        if len(self._timestamps) < 2:
            return None
        if len(self._timestamps) < self.window:
            start = self._timestamps[0]
            elapsed = now - start
            return (len(self._timestamps) - 1) / elapsed if elapsed > 0 else None
        start = self._timestamps[0]
        elapsed = now - start
        return (self.window - 1) / elapsed if elapsed > 0 else None
