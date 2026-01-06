import time
from datetime import datetime


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


class Timer:
    def __init__(self):
        self._start_time = None
        self._wall_start_time = None
        self.isRunning = False

    def start(self):
        """Start a new timer"""
        if self._start_time is not None:
            return

        self._wall_start_time = datetime.now()
        self._start_time = time.perf_counter()
        self.isRunning = True

    def stop(self):
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            return time.time(), 0

        elapsedTime = time.perf_counter() - self._start_time
        self._start_time = None
        self.isRunning = False
        return self._wall_start_time, elapsedTime

    def elapsedSeconds(self):
        if self._start_time is None:
            return 0

        elapsedTime = time.perf_counter() - self._start_time

        return elapsedTime
