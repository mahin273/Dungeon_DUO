"""
weapon.py

Defines weapon items and their properties.
"""

from enum import Enum
from typing import Optional
from .item import Item, ItemRarity

# Define DamageType locally to avoid import issues
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

class WeaponType(Enum):
    """Types of weapons available in the game."""
    SWORD = "sword"
    STAFF = "staff"
    BOW = "bow"
    DAGGER = "dagger"
    AXE = "axe"
    SPEAR = "spear"

class Weapon(Item):
    """Base class for all weapons."""

    # Durability loss modifiers per weapon type
    DURABILITY_LOSS_MODIFIERS = {
        WeaponType.SWORD: 0.5,    # Swords are durable
        WeaponType.STAFF: 0.3,    # Staves are very durable
        WeaponType.BOW: 0.2,      # Bows lose durability slowly
        WeaponType.DAGGER: 0.7,   # Daggers lose durability faster
    }

    def __init__(self, name: str, damage: int, weapon_type: WeaponType,
                 damage_type: DamageType = DamageType.PHYSICAL,
                 durability: int = 100, rarity: ItemRarity = ItemRarity.COMMON,
                 description: str = "", value: int = 0, weight: float = 0.0):
        """Initialize a weapon."""
        super().__init__(name)
        self.rarity = rarity
        self.description = description
        self.value = value
        self.weight = weight

        self.damage = damage
        self.weapon_type = weapon_type
        self.damage_type = damage_type
        self.max_durability = durability
        self.current_durability = durability
        self.durability_loss_per_hit = self.DURABILITY_LOSS_MODIFIERS.get(weapon_type, 0.5)
        self.broken = False

    def use(self) -> bool:
        """Use the weapon, reducing its durability."""
        if self.broken:
            return False

        # Apply durability loss based on weapon type and rarity
        base_loss = self.durability_loss_per_hit

        # Rarity reduces durability loss
        rarity_modifier = {
            ItemRarity.COMMON: 1.0,
            ItemRarity.UNCOMMON: 0.8,
            ItemRarity.RARE: 0.6,
            ItemRarity.EPIC: 0.4,
            ItemRarity.LEGENDARY: 0.2
        }.get(self.rarity, 1.0)

        total_loss = base_loss * rarity_modifier

        self.current_durability -= total_loss
        if self.current_durability <= 0:
            self.broken = True
            self.current_durability = 0
            return False
        return True

    def repair(self, amount: Optional[int] = None):
        """Repair the weapon's durability."""
        if amount is None:
            self.current_durability = self.max_durability
        else:
            self.current_durability = min(self.current_durability + amount, self.max_durability)
        self.broken = False

    def get_damage(self) -> int:
        """Get the current damage value of the weapon."""
        if self.broken:
            return max(1, self.damage // 4)  # Broken weapons do 1/4 damage (minimum 1)

        # Durability affects damage when below 20%
        if self.current_durability < (self.max_durability * 0.2):
            durability_penalty = 0.5 + (self.current_durability / self.max_durability)
            return max(1, int(self.damage * durability_penalty))
        return self.damage

    def get_durability_percentage(self) -> float:
        """Get the current durability as a percentage."""
        return (self.current_durability / self.max_durability) * 100

class IronSword(Weapon):
    """Basic iron sword."""
    def __init__(self):
        super().__init__(
            name="Iron Sword",
            damage=8,
            weapon_type=WeaponType.SWORD,
            damage_type=DamageType.PHYSICAL,
            durability=150,
            rarity=ItemRarity.COMMON,
            description="A sturdy and reliable iron sword.",
            value=15,
            weight=3.0
        )

class FireStaff(Weapon):
    """Magical fire staff."""
    def __init__(self):
        super().__init__(
            name="Fire Staff",
            damage=12,
            weapon_type=WeaponType.STAFF,
            damage_type=DamageType.FIRE,
            durability=80,
            rarity=ItemRarity.UNCOMMON,
            description="A magical staff that channels the power of fire.",
            value=40,
            weight=2.0
        )
