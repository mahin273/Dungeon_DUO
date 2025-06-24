"""
item.py

Base classes for game items.
"""

from enum import Enum

class ItemRarity(Enum):
    """Item rarity levels."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class Item:
    """Base class for all items."""

    def __init__(self, name: str, rarity: ItemRarity = ItemRarity.COMMON):
        """Initialize an item."""
        self.name = name
        self.rarity = rarity
        self.description = ""
        self.icon = None  # For future UI implementation

    def get_display_name(self) -> str:
        """Get the item's display name with rarity color."""
        return f"{self.name} ({self.rarity.value.capitalize()})"

    def use(self) -> bool:
        """Use the item. Returns True if successful."""
        return True

    def get_tooltip(self) -> str:
        """Get the item's tooltip text."""
        return f"{self.get_display_name()}\n{self.description}"
