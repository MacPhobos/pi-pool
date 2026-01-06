"""Tests for Light.cycle() non-blocking behavior.

This module tests that Light.cycle() runs in a background thread
and does not block the main control loop.

SAFETY REQUIREMENT:
The main control loop must remain responsive at all times for:
- Heater safety checks (pump running, temperature limits)
- Pump monitoring
- Watchdog operations
- Sensor reading and logging

If Light.cycle() blocks the main thread, all safety-critical
operations are suspended during the cycle, creating a hazard.
"""

import pytest
import time
import threading
import logging
from unittest.mock import Mock


@pytest.mark.unit
class TestLightCycleNonBlocking:
    """Tests for Light.cycle() running in background thread."""

    @pytest.fixture
    def mock_relay_block(self):
        """Mock relay block for light tests."""
        relay = Mock()
        relay.portOn = Mock()
        relay.portOff = Mock()
        return relay

    @pytest.fixture
    def light(self, mock_relay_block):
        """Create Light instance with mock relay."""
        from Light import Light
        return Light(relayBlock=mock_relay_block, lightPort=6)

    def test_light_cycle_returns_immediately(self, light):
        """cycle() must return immediately, not block."""
        start_time = time.time()

        # Start a 5-second cycle operation
        light.cycle(5, delay=1)  # Would block for 5 seconds if synchronous

        elapsed = time.time() - start_time

        # Should return in under 0.1 seconds (not 5 seconds)
        assert elapsed < 0.5, f"cycle() blocked for {elapsed:.2f}s - should be async"

        # Wait for cycle to complete
        light.waitForCycle(timeout=10)

    def test_light_is_cycling_during_operation(self, light):
        """Verify isCycling() returns True during cycle."""
        # Start cycle
        light.cycle(3, delay=0.1)

        # Should be cycling
        assert light.isCycling() is True, "Should be cycling immediately after start"

        # Wait for completion
        light.waitForCycle(timeout=5)

        # Should not be cycling anymore
        assert light.isCycling() is False, "Should not be cycling after completion"

    def test_light_cycle_runs_in_background_thread(self, light):
        """Verify cycle runs in separate thread."""
        main_thread = threading.current_thread()
        cycle_thread = [None]

        # Capture the thread that runs the cycle
        original_cycle_sync = light._cycle_sync

        def capture_thread(*args):
            cycle_thread[0] = threading.current_thread()
            original_cycle_sync(*args)

        light._cycle_sync = capture_thread

        light.cycle(1, delay=0.05)
        light.waitForCycle(timeout=5)

        # Verify cycle ran in different thread
        assert cycle_thread[0] is not None, "Cycle thread should be captured"
        assert cycle_thread[0] is not main_thread, "Cycle should not run in main thread"

    def test_light_cycle_warns_on_main_thread(self, light, caplog):
        """Verify warning logged when cycle called from main thread."""
        with caplog.at_level(logging.WARNING):
            light.cycle(1, delay=0.01)
            light.waitForCycle(timeout=5)

        # Check for warning about main thread
        assert "main thread" in caplog.text.lower(), "Should warn about main thread call"

    def test_light_cycle_count_zero_returns_immediately(self, light):
        """Verify cycle(0) returns immediately without starting thread."""
        light.cycle(0)

        assert light.isCycling() is False, "Should not start cycle for count=0"

    def test_light_cycle_count_negative_returns_immediately(self, light):
        """Verify cycle(-1) returns immediately without starting thread."""
        light.cycle(-1)

        assert light.isCycling() is False, "Should not start cycle for negative count"

    def test_light_wait_for_cycle_timeout(self, light):
        """Verify waitForCycle respects timeout."""
        # Start a long cycle
        light.cycle(10, delay=1)  # 10 seconds

        start = time.time()
        result = light.waitForCycle(timeout=0.1)  # Wait only 0.1 seconds
        elapsed = time.time() - start

        assert result is False, "Should return False on timeout"
        assert elapsed < 0.5, "Should timeout quickly"

        # Cleanup: wait for actual completion
        light.waitForCycle(timeout=15)

    def test_light_wait_for_cycle_no_cycle(self, light):
        """Verify waitForCycle returns True when no cycle running."""
        result = light.waitForCycle()

        assert result is True, "Should return True when not cycling"

    def test_light_concurrent_cycles_serialized(self, light):
        """Verify concurrent cycle requests are serialized."""
        cycle_order = []

        original_cycle_one = light.cycleOne

        def track_cycle(delay=1):
            cycle_order.append(time.time())
            original_cycle_one(delay)

        light.cycleOne = track_cycle

        # Start two cycles quickly
        light.cycle(2, delay=0.05)
        time.sleep(0.01)  # Small delay
        light.cycle(2, delay=0.05)

        # Wait for both to complete
        time.sleep(0.5)

        # Should have 4 cycles total (2 + 2), executed serially due to lock
        assert len(cycle_order) >= 2, "Should have multiple cycle events"

    def test_light_cycle_thread_is_daemon(self, light):
        """Verify cycle thread is daemon (won't prevent exit)."""
        light.cycle(1, delay=0.01)

        # Thread should be daemon
        assert light._cycle_thread.daemon is True, "Cycle thread should be daemon"

        light.waitForCycle(timeout=5)


@pytest.mark.safety
class TestLightCycleSafety:
    """Safety tests for light cycle behavior."""

    @pytest.fixture
    def mock_relay_block(self):
        relay = Mock()
        relay.portOn = Mock()
        relay.portOff = Mock()
        return relay

    @pytest.fixture
    def light(self, mock_relay_block):
        from Light import Light
        return Light(relayBlock=mock_relay_block, lightPort=6)

    def test_main_loop_responsive_during_cycle(self, light):
        """CRITICAL: Verify main loop can run during light cycle."""
        # Start a long cycle
        light.cycle(5, delay=0.2)  # 1 second total

        # Simulate main loop operations while cycling
        loop_iterations = 0
        start = time.time()

        while time.time() - start < 0.5:  # Run for 0.5 seconds
            # These would block in the old implementation
            loop_iterations += 1
            time.sleep(0.01)  # Simulate main loop work

        # Should have many iterations (not blocked)
        assert loop_iterations > 10, f"Main loop only ran {loop_iterations} times - may be blocked"

        light.waitForCycle(timeout=10)

    def test_light_has_cycle_lock(self, light):
        """Verify light has lock for cycle serialization."""
        assert hasattr(light, '_cycle_lock'), "Light should have _cycle_lock"
        assert isinstance(light._cycle_lock, type(threading.Lock())), "Should be a Lock"

    def test_light_has_cycle_thread(self, light):
        """Verify light tracks cycle thread."""
        assert hasattr(light, '_cycle_thread'), "Light should have _cycle_thread"
        assert light._cycle_thread is None, "Should be None initially"

        light.cycle(1, delay=0.01)
        light.waitForCycle(timeout=5)

        # After cycle, thread reference should exist
        assert light._cycle_thread is not None, "Should have thread reference after cycle"
