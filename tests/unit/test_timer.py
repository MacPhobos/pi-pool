"""Unit tests for Timer class.

Tests the Timer class that tracks elapsed time for pool devices.
"""

import pytest
import time
from Timer import Timer


@pytest.mark.unit
class TestTimer:
    """Unit tests for Timer class timing functionality."""

    def test_timer_initial_state(self):
        """Timer should start in stopped state with no elapsed time."""
        timer = Timer()

        assert timer.isRunning is False
        assert timer._start_time is None
        assert timer._wall_start_time is None
        assert timer.elapsedSeconds() == 0

    def test_timer_start_records_time(self):
        """Starting timer should set running state and record start time."""
        timer = Timer()

        timer.start()

        assert timer.isRunning is True
        assert timer._start_time is not None
        assert timer._wall_start_time is not None

    def test_timer_stop_returns_elapsed(self):
        """Stopping timer should return wall time and elapsed seconds."""
        timer = Timer()

        timer.start()
        time.sleep(0.1)  # Sleep for 100ms
        wall_time, elapsed = timer.stop()

        assert timer.isRunning is False
        assert timer._start_time is None
        assert wall_time is not None
        assert elapsed >= 0.1  # At least 100ms elapsed
        assert elapsed < 0.5   # Should not be too long

    def test_timer_elapsed_while_running(self):
        """Timer should report elapsed time while running."""
        timer = Timer()

        timer.start()
        time.sleep(0.1)
        elapsed = timer.elapsedSeconds()

        assert elapsed >= 0.1  # At least 100ms elapsed
        assert timer.isRunning is True  # Still running

    def test_timer_reset(self):
        """Stopping timer should reset state for reuse."""
        timer = Timer()

        # First run
        timer.start()
        time.sleep(0.05)
        wall_time1, elapsed1 = timer.stop()

        assert elapsed1 >= 0.05
        assert timer.isRunning is False

        # Second run after reset
        timer.start()
        time.sleep(0.05)
        wall_time2, elapsed2 = timer.stop()

        assert elapsed2 >= 0.05
        assert wall_time2 > wall_time1  # Later wall time
        assert timer.isRunning is False

    def test_timer_multiple_start_stop_cycles(self):
        """Timer should handle multiple start/stop cycles correctly."""
        timer = Timer()

        # Cycle 1
        timer.start()
        time.sleep(0.02)
        _, elapsed1 = timer.stop()
        assert elapsed1 >= 0.02

        # Cycle 2
        timer.start()
        time.sleep(0.02)
        _, elapsed2 = timer.stop()
        assert elapsed2 >= 0.02

        # Cycle 3
        timer.start()
        time.sleep(0.02)
        _, elapsed3 = timer.stop()
        assert elapsed3 >= 0.02

        # All cycles should be independent
        assert timer.isRunning is False

    def test_timer_stop_when_not_started(self):
        """Stopping timer that was never started should return zeros."""
        timer = Timer()

        wall_time, elapsed = timer.stop()

        # Returns current time and 0 elapsed when not started
        assert elapsed == 0
        assert wall_time is not None

    def test_timer_double_start_idempotent(self):
        """Starting timer twice should be idempotent (no effect on second call)."""
        timer = Timer()

        timer.start()
        start_time_1 = timer._start_time
        time.sleep(0.01)

        timer.start()  # Second start should have no effect
        start_time_2 = timer._start_time

        # Start time should not change
        assert start_time_1 == start_time_2
        assert timer.isRunning is True

    def test_timer_elapsed_seconds_when_stopped(self):
        """Elapsed seconds should return 0 when timer is stopped."""
        timer = Timer()

        assert timer.elapsedSeconds() == 0

        timer.start()
        timer.stop()

        assert timer.elapsedSeconds() == 0
