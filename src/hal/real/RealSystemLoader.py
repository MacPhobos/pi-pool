"""Real system loader using modprobe for kernel modules."""
import logging
import os
from typing import List
from hal.interfaces import ISystemLoader


class RealSystemLoader(ISystemLoader):
    """Real system loader implementation using modprobe."""

    def __init__(self):
        """Initialize the real system loader."""
        logging.info("RealSystemLoader: Initialized")

    def loadModules(self, modules: List[str]) -> None:
        """Load kernel modules using modprobe.

        Args:
            modules: List of module names to load (e.g., ['w1-gpio', 'w1-therm'])
        """
        for module in modules:
            try:
                result = os.system(f'modprobe {module}')
                if result == 0:
                    logging.info(f"RealSystemLoader: Loaded module '{module}'")
                else:
                    logging.error(f"RealSystemLoader: Failed to load module '{module}' (exit code: {result})")
            except Exception as e:
                logging.error(f"RealSystemLoader: Error loading module '{module}': {e}")
