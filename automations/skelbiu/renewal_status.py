"""
Renewal Status Enum

Defines the possible states for item renewal operations.
"""

from enum import Enum, auto


class RenewalStatus(Enum):
    """
    Status of an item's renewal state.

    RENEWED: Item was successfully renewed in this cycle
    ALREADY_RENEWED: Item was already renewed and doesn't need renewal
    FAILED: Item renewal failed
    """

    RENEWED = auto()
    ALREADY_RENEWED = auto()
    FAILED = auto()

    def __str__(self) -> str:
        """String representation for logging"""
        return self.name.lower()
