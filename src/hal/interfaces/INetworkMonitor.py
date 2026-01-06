"""Network monitor interface for hardware abstraction."""
from abc import ABC, abstractmethod


class INetworkMonitor(ABC):
    """Interface for network connectivity monitoring."""

    @abstractmethod
    def ping(self, target: str, count: int = 10, interval: int = 1) -> bool:
        """Ping a target host to check connectivity.

        Args:
            target: Host to ping (IP address or hostname)
            count: Number of ping attempts
            interval: Interval between pings in seconds

        Returns:
            True if at least one ping succeeded, False otherwise
        """
        pass
