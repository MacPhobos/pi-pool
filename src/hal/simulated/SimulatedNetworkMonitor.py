"""Simulated network monitor for testing without hardware."""
import logging
from hal.interfaces import INetworkMonitor


class SimulatedNetworkMonitor(INetworkMonitor):
    """Simulated network monitor implementation for testing without hardware."""

    def __init__(self, defaultConnected: bool = True):
        """Initialize the simulated network monitor.

        Args:
            defaultConnected: Default connection state (True = always connected)
        """
        self.connected = defaultConnected
        logging.info(f"SimulatedNetworkMonitor: Initialized (default connected: {defaultConnected})")

    def ping(self, target: str, count: int = 10, interval: int = 1) -> bool:
        """Simulate ping to a target host.

        Args:
            target: Host to ping (IP address or hostname)
            count: Number of ping attempts (ignored in simulation)
            interval: Interval between pings in seconds (ignored in simulation)

        Returns:
            Current connection state
        """
        if self.connected:
            logging.info(f"SimulatedNetworkMonitor: Ping to {target} succeeded (simulated)")
        else:
            logging.warning(f"SimulatedNetworkMonitor: Ping to {target} failed (simulated)")

        return self.connected

    def setConnectionState(self, connected: bool) -> None:
        """Set the simulated connection state (helper for testing).

        Args:
            connected: New connection state (True = connected, False = disconnected)
        """
        self.connected = connected
        logging.info(f"SimulatedNetworkMonitor: Connection state set to {connected}")
