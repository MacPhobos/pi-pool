"""System loader interface for hardware abstraction."""
from abc import ABC, abstractmethod
from typing import List


class ISystemLoader(ABC):
    """Interface for loading system kernel modules."""

    @abstractmethod
    def loadModules(self, modules: List[str]) -> None:
        """Load kernel modules.

        Args:
            modules: List of module names to load (e.g., ['w1-gpio', 'w1-therm'])
        """
        pass
