"""Simulated system loader for testing without hardware."""
import logging
from typing import List
from hal.interfaces import ISystemLoader


class SimulatedSystemLoader(ISystemLoader):
    """Simulated system loader implementation for testing without hardware."""

    def __init__(self):
        """Initialize the simulated system loader."""
        self.loadedModules: List[str] = []
        logging.info("SimulatedSystemLoader: Initialized")

    def loadModules(self, modules: List[str]) -> None:
        """Simulate loading kernel modules.

        Args:
            modules: List of module names to load (e.g., ['w1-gpio', 'w1-therm'])
        """
        for module in modules:
            if module not in self.loadedModules:
                self.loadedModules.append(module)
                logging.info(f"SimulatedSystemLoader: Loaded module '{module}' (simulated)")
            else:
                logging.info(f"SimulatedSystemLoader: Module '{module}' already loaded (simulated)")

    def getLoadedModules(self) -> List[str]:
        """Get list of loaded modules (helper for testing).

        Returns:
            List of module names that have been loaded
        """
        return self.loadedModules.copy()
