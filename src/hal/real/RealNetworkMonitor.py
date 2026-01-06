"""Real network monitor using pythonping library."""
import logging
from hal.interfaces import INetworkMonitor


class RealNetworkMonitor(INetworkMonitor):
    """Real network monitor implementation using pythonping."""

    def __init__(self):
        """Initialize the real network monitor."""
        try:
            from pythonping import ping
            from pythonping.executor import SuccessOn
            self._ping = ping
            self._SuccessOn = SuccessOn
            logging.info("RealNetworkMonitor: Initialized with pythonping")
        except ImportError as e:
            logging.error(f"RealNetworkMonitor: Failed to import pythonping: {e}")
            raise RuntimeError("pythonping not available - cannot use RealNetworkMonitor") from e

    def ping(self, target: str, count: int = 10, interval: int = 1) -> bool:
        """Ping a target host to check connectivity.

        Args:
            target: Host to ping (IP address or hostname)
            count: Number of ping attempts
            interval: Interval between pings in seconds

        Returns:
            True if at least one ping succeeded, False otherwise
        """
        try:
            # Use SuccessOn.One to return success if at least one ping succeeds
            result = self._ping(target, count=count, interval=interval, verbose=False,
                               success_on=self._SuccessOn.One)

            success = result.success()
            if success:
                logging.info(f"RealNetworkMonitor: Ping to {target} succeeded")
            else:
                logging.warning(f"RealNetworkMonitor: Ping to {target} failed")

            return success
        except Exception as e:
            logging.error(f"RealNetworkMonitor: Error pinging {target}: {e}")
            return False
