"""
damage.py

Defines damage types and related functionality.
"""

from enum import Enum

class DamageType(Enum):
    """Types of damage that can be dealt."""
    PHYSICAL = "physical"
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    POISON = "poison"
    MAGIC = "magic"

    def get_color(self) -> tuple:
        """Get the RGB color for this damage type."""
        colors = {
            DamageType.PHYSICAL: (200, 200, 200),  # Gray
            DamageType.FIRE: (255, 69, 0),         # Red-Orange
            DamageType.ICE: (135, 206, 250),       # Light Blue
            DamageType.LIGHTNING: (255, 255, 0),   # Yellow
            DamageType.POISON: (50, 205, 50),      # Lime Green
            DamageType.MAGIC: (147, 112, 219),     # Purple
        }
        return colors.get(self, (255, 255, 255))   # White as fallback
