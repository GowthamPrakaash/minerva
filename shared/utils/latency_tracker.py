"""
shared/utils/latency_tracker.py — Pipeline latency instrumentation.

Purpose:
    Measures wall-clock duration for each pipeline stage. Used for
    performance monitoring and usage_records cost estimation.

Usage:
    tracker = LatencyTracker()
    with tracker.measure("STT"):
        result = stt_provider.transcribe(...)
    print(tracker.all())  # {"STT": 0.842, ...}

Methods:
    measure(label) — context manager that times a block
    get(label) → float
    all() → dict[str, float]
    total() → float
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator


class LatencyTracker:
    """Thread-safe wall-clock latency tracker for named pipeline stages."""

    def __init__(self) -> None:
        self._timings: dict[str, float] = {}

    @contextmanager
    def measure(self, label: str) -> Generator[None, None, None]:
        """
        Context manager that records the wall-clock duration of a block.

        Args:
            label: Human-readable stage name (e.g. 'STT', 'LLM', 'TTS').

        Usage:
            with tracker.measure("LLM"):
                response = await llm.chat_completion(...)
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self._timings[label] = elapsed

    def get(self, label: str) -> float:
        """Return the recorded duration for a label, or 0.0 if not measured."""
        return self._timings.get(label, 0.0)

    def all(self) -> dict[str, float]:
        """Return a copy of all recorded timings as {label: seconds}."""
        return dict(self._timings)

    def total(self) -> float:
        """Return the sum of all recorded durations."""
        return sum(self._timings.values())

    def __repr__(self) -> str:
        pairs = ", ".join(f"{k}={v:.3f}s" for k, v in self._timings.items())
        return f"LatencyTracker({pairs})"
