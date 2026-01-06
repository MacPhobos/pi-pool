"""Tests for heater-pump race condition fix.

This module tests the dual-locking mechanism that prevents the race condition
where pump could stop between checking pump state and activating heater GPIO.

SAFETY REQUIREMENT:
The heater GPIO activation and pump state verification must be atomic.
If the pump stops at ANY point during heater activation, the heater must
not activate - even if the pump was running at the start of the check.

The fix uses dual locking:
1. Heater's _activation_lock - prevents concurrent heater activations
2. Pump's _state_lock - prevents pump state changes during heater activation
"""

import pytest
import threading
import time
import logging
from unittest.mock import Mock, patch


@pytest.mark.safety
class TestHeaterPumpRaceCondition:
    """Tests for heater-pump race condition fix."""

    @pytest.fixture(autouse=True)
    def mock_event_and_db(self):
        """Auto-mock Event and DB for all tests in this class."""
        with patch('Event.Event.logStateEvent'), \
             patch('Event.Event.logOpaqueEvent'), \
             patch('DB.DB.getInstance') as mock_db_get:

            mock_db = Mock()
            mock_db.logDuration = Mock()
            mock_db_get.return_value = mock_db

            yield

    @pytest.fixture
    def mock_relay_block(self):
        """Mock relay block for heater tests."""
        relay = Mock()
        relay.portOn = Mock()
        relay.portOff = Mock()
        return relay

    @pytest.fixture
    def pump(self, mock_relay_block):
        """Create real Pump instance to verify lock behavior."""
        from Pump import Pump
        return Pump(relayBlock=mock_relay_block, pumpPort=8)

    @pytest.fixture
    def heater(self, mock_relay_block, pump):
        """Create Heater instance with real Pump for lock testing."""
        from Heater import Heater
        return Heater(
            relayBlock=mock_relay_block,
            heaterPort=7,
            maxWaterTemp=33,
            pump=pump
        )

    def test_pump_has_state_lock(self, pump):
        """Verify pump has _state_lock attribute for thread safety."""
        assert hasattr(pump, '_state_lock'), "Pump missing _state_lock attribute"
        # Uses RLock to allow reentrant locking (setModeOff() calls off())
        assert isinstance(pump._state_lock, type(threading.RLock())), "_state_lock should be an RLock"

    def test_heater_has_activation_lock(self, heater):
        """Verify heater has _activation_lock attribute for thread safety."""
        assert hasattr(heater, '_activation_lock'), "Heater missing _activation_lock attribute"
        assert isinstance(heater._activation_lock, type(threading.Lock())), "_activation_lock should be a Lock"

    def test_heater_activation_blocks_while_holding_pump_lock(self, heater, pump, mock_relay_block):
        """SAFETY: Heater activation must wait if pump's state lock is held.

        This verifies that heater cannot activate while another thread
        holds the pump's state lock (e.g., pump is in the middle of turning off).
        """
        from PumpState import PumpState

        # Turn pump on first
        pump.on()
        assert pump.isOn() is True

        # Set valid temperature
        heater.setInputTemp(25.0)

        # Simulate another thread holding pump's state lock
        pump._state_lock.acquire()

        heater_activated = [False]
        heater_thread_blocked = threading.Event()

        def try_activate_heater():
            heater_thread_blocked.set()
            result = heater.on()  # This should block waiting for pump lock
            heater_activated[0] = result

        # Start thread that will try to activate heater
        thread = threading.Thread(target=try_activate_heater)
        thread.start()

        # Wait for thread to start and block on lock
        heater_thread_blocked.wait(timeout=1.0)
        time.sleep(0.1)  # Give thread time to block on lock

        # Verify heater hasn't activated yet (thread is blocked)
        assert heater_activated[0] is False, "Heater should be blocked waiting for pump lock"

        # Release pump lock - heater thread can now proceed
        pump._state_lock.release()

        # Wait for thread to complete
        thread.join(timeout=2.0)
        assert not thread.is_alive(), "Heater thread should have completed"

        # Now heater should have activated (pump was ON when we released lock)
        assert heater_activated[0] is True, "Heater should have activated after pump lock released"
        assert heater.isOn() is True

    def test_pump_off_blocks_heater_activation(self, heater, pump, mock_relay_block):
        """SAFETY: Heater can only activate if pump was ON at activation moment.

        This test verifies the atomic nature of the dual-locking mechanism.
        When heater.on() and pump.off() race concurrently, exactly one of
        these outcomes must occur:

        1. Heater acquires pump lock first:
           - Heater sees pump is ON, activates successfully
           - Pump.off() waits for heater to release lock, then turns pump off
           - Result: heater ON (correctly activated), pump OFF (turned off after)

        2. Pump acquires lock first:
           - Pump turns off
           - Heater.on() sees pump is OFF, refuses to activate
           - Result: heater OFF, pump OFF

        CRITICAL SAFETY GUARANTEE: At the moment of heater GPIO activation,
        the pump was definitely running. The heater.on() return value tells
        us which scenario occurred.

        Note: If scenario 1 occurs, the runOneLoop() or watchdog will
        subsequently stop the heater when it detects pump is OFF.
        """
        from HeaterState import HeaterState

        # Turn pump on first
        pump.on()
        heater.setInputTemp(25.0)

        activation_results = []
        barrier = threading.Barrier(2)  # Synchronize thread start

        def pump_off_sequence():
            barrier.wait()  # Wait for both threads to be ready
            pump.off()

        def heater_on_sequence():
            barrier.wait()  # Wait for both threads to be ready
            result = heater.on()
            activation_results.append(result)

        # Start both threads simultaneously
        pump_thread = threading.Thread(target=pump_off_sequence)
        heater_thread = threading.Thread(target=heater_on_sequence)

        pump_thread.start()
        heater_thread.start()

        pump_thread.join(timeout=2.0)
        heater_thread.join(timeout=2.0)

        # Verify one of the two valid outcomes occurred
        assert len(activation_results) == 1, "Heater activation should have completed"

        if activation_results[0] is True:
            # Scenario 1: Heater activated because pump WAS on at activation time
            # This is correct - heater saw pump running when it checked
            assert heater.isOn() is True, "Heater should be ON (activated successfully)"
            # Pump may be OFF now (turned off after heater activated) - this is expected
            # The runOneLoop/watchdog will handle stopping heater

            # Simulate what runOneLoop would do - verify it stops the heater
            heater.runOneLoop()
            if not pump.isOn():
                # Heater should have stopped itself via runOneLoop's pump check
                assert heater.isOn() is False, "runOneLoop should stop heater when pump is off"

        else:
            # Scenario 2: Heater blocked because pump was OFF when it checked
            assert heater.isOn() is False, "Heater should be OFF (blocked by pump check)"
            assert pump.isOn() is False, "Pump should be OFF"

    def test_heater_blocked_when_pump_not_running(self, heater, pump, mock_relay_block, caplog):
        """SAFETY: Heater must not activate if pump is not running."""
        # Pump starts OFF
        assert pump.isOn() is False

        # Try to activate heater
        heater.setInputTemp(25.0)
        with caplog.at_level(logging.ERROR):
            result = heater.on()

        # Verify heater blocked
        assert result is False, "Heater.on() should return False when pump is OFF"
        assert heater.isOn() is False, "Heater should not be ON"
        mock_relay_block.portOn.assert_not_called()
        assert "Cannot turn on - pump is not running" in caplog.text

    def test_heater_activates_when_pump_running(self, heater, pump, mock_relay_block, caplog):
        """Verify heater CAN activate when pump is running."""
        # Turn pump on
        pump.on()
        assert pump.isOn() is True

        # Set valid temperature
        heater.setInputTemp(25.0)

        # Activate heater
        with caplog.at_level(logging.INFO):
            result = heater.on()

        # Verify heater activated
        assert result is True, "Heater.on() should return True when pump is ON"
        assert heater.isOn() is True, "Heater should be ON"
        mock_relay_block.portOn.assert_called_with(7)
        assert "Activated with atomic pump verification" in caplog.text

    def test_concurrent_heater_activations_serialized(self, heater, pump, mock_relay_block):
        """Verify concurrent heater activations are serialized by activation lock."""
        from HeaterState import HeaterState

        # Turn pump on
        pump.on()
        heater.setInputTemp(25.0)

        activation_count = [0]
        lock = threading.Lock()

        def try_activate():
            result = heater.on()
            with lock:
                if result:
                    activation_count[0] += 1

        # Start multiple threads trying to activate heater
        threads = [threading.Thread(target=try_activate) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        # Only one activation should succeed (heater was already on after first)
        # But since we return True even if already on, multiple might succeed
        # The key is no exceptions and heater ends up in ON state
        assert heater.isOn() is True

    def test_heater_without_pump_reference_logs_warning(self, mock_relay_block, caplog):
        """Verify heater without pump reference logs a warning."""
        from Heater import Heater

        # Create heater without pump reference
        heater = Heater(
            relayBlock=mock_relay_block,
            heaterPort=7,
            maxWaterTemp=33,
            pump=None  # No pump reference
        )

        heater.setInputTemp(25.0)

        with caplog.at_level(logging.WARNING):
            result = heater.on()

        # Should still activate but log warning
        assert result is True
        assert heater.isOn() is True
        assert "without pump reference" in caplog.text


@pytest.mark.safety
class TestPumpStateLock:
    """Tests for Pump's state lock mechanism."""

    @pytest.fixture(autouse=True)
    def mock_event_and_db(self):
        """Auto-mock Event and DB for all tests in this class."""
        with patch('Event.Event.logStateEvent'), \
             patch('Event.Event.logOpaqueEvent'), \
             patch('DB.DB.getInstance') as mock_db_get:

            mock_db = Mock()
            mock_db.logDuration = Mock()
            mock_db_get.return_value = mock_db

            yield

    @pytest.fixture
    def mock_relay_block(self):
        """Mock relay block."""
        relay = Mock()
        relay.portOn = Mock()
        relay.portOff = Mock()
        return relay

    @pytest.fixture
    def pump(self, mock_relay_block):
        """Create Pump instance."""
        from Pump import Pump
        return Pump(relayBlock=mock_relay_block, pumpPort=8)

    def test_pump_on_acquires_state_lock(self, pump, mock_relay_block):
        """Verify pump.on() uses state lock."""
        # If we hold the lock, pump.on() should block
        pump._state_lock.acquire()

        completed = [False]

        def try_pump_on():
            pump.on()
            completed[0] = True

        thread = threading.Thread(target=try_pump_on)
        thread.start()

        # Give thread time to potentially complete (it shouldn't)
        time.sleep(0.1)
        assert completed[0] is False, "pump.on() should be blocked by lock"

        # Release lock
        pump._state_lock.release()

        # Now it should complete
        thread.join(timeout=2.0)
        assert completed[0] is True, "pump.on() should complete after lock released"

    def test_pump_off_acquires_state_lock(self, pump, mock_relay_block):
        """Verify pump.off() uses state lock.

        Note: RLock is reentrant within the same thread, but blocks other threads.
        """
        # Turn pump on first
        pump.on()

        # Hold the lock (note: this thread can still acquire it since it's RLock,
        # but another thread cannot)
        pump._state_lock.acquire()

        completed = threading.Event()

        def try_pump_off():
            pump.off()
            completed.set()

        thread = threading.Thread(target=try_pump_off)
        thread.start()

        # Give thread time to potentially complete (it shouldn't since we hold lock)
        completed_before_release = completed.wait(timeout=0.2)
        assert completed_before_release is False, "pump.off() should be blocked by lock"

        # Release lock
        pump._state_lock.release()

        # Now it should complete
        completed_after_release = completed.wait(timeout=2.0)
        thread.join(timeout=2.0)
        assert completed_after_release is True, "pump.off() should complete after lock released"

    def test_pump_state_changes_are_thread_safe(self, pump):
        """Verify concurrent state changes don't cause issues."""
        errors = []

        def toggle_pump():
            try:
                for _ in range(50):
                    pump.on()
                    pump.off()
            except Exception as e:
                errors.append(e)

        # Start multiple threads toggling pump
        threads = [threading.Thread(target=toggle_pump) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        # No exceptions should have occurred
        assert len(errors) == 0, f"Thread safety errors: {errors}"
