"""
inventory.py

Inventory and item system for Dungeon Duo: Rough AI.
Includes collectible items, rarity system, and equipment management.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random
import time

from .combat import Weapon, Armor, WeaponType, DamageType

class ItemRarity(Enum):
    """Item rarity levels."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class ItemType(Enum):
    """Types of items."""
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    QUEST = "quest"

@dataclass
class Item:
    """Base item class."""
    name: str
    item_type: ItemType = field(init=False, default=None)
    rarity: ItemRarity = field(init=False, default=ItemRarity.COMMON)
    description: str = field(init=False, default="")
    value: int = field(init=False, default=0)
    weight: float = field(init=False, default=0.0)
    stackable: bool = field(init=False, default=False)
    max_stack: int = field(init=False, default=1)
    quantity: int = field(init=False, default=1)

    def __post_init__(self):
        self.id = f"{self.name}_{int(time.time() * 1000)}"

    def get_rarity_color(self) -> Tuple[int, int, int]:
        """Get color associated with rarity."""
        colors = {
            ItemRarity.COMMON: (200, 200, 200),      # Gray
            ItemRarity.UNCOMMON: (0, 255, 0),        # Green
            ItemRarity.RARE: (0, 100, 255),          # Blue
            ItemRarity.EPIC: (200, 0, 255),          # Purple
            ItemRarity.LEGENDARY: (255, 165, 0)      # Orange
        }
        return colors.get(self.rarity, (255, 255, 255))

@dataclass
class ConsumableItem(Item):
    """Consumable items like potions."""
    effect_type: str  # "heal", "mana", "stamina", "buff"
    effect_value: int
    duration: float = 0.0  # Duration in seconds for buffs

    def __post_init__(self):
        super().__post_init__()
        self.item_type = ItemType.CONSUMABLE

@dataclass
class MaterialItem(Item):
    """Crafting materials."""
    material_type: str
    quality: int = 1

    def __post_init__(self):
        super().__post_init__()
        self.item_type = ItemType.MATERIAL
        self.stackable = True
        self.max_stack = 99

class Inventory:
    """Player inventory system."""

    def __init__(self, max_slots: int = 50):
        """Initialize inventory."""
        self.max_slots = max_slots
        self.items: List[Optional[Item]] = [None] * max_slots
        self.gold = 0
        self.weight_limit = 100.0
        self.current_weight = 0.0

    def add_item(self, item: Item) -> bool:
        """Add an item to inventory. Returns True if successful."""
        # Check weight limit
        if self.current_weight + item.weight > self.weight_limit:
            print(f"Inventory too heavy! Cannot carry {item.name}")
            return False

        # Try to stack with existing items
        if item.stackable:
            for i, existing_item in enumerate(self.items):
                if (existing_item and
                    existing_item.name == item.name and
                    existing_item.quantity < existing_item.max_stack):

                    space_left = existing_item.max_stack - existing_item.quantity
                    amount_to_add = min(item.quantity, space_left)

                    existing_item.quantity += amount_to_add
                    item.quantity -= amount_to_add

                    if item.quantity <= 0:
                        self.current_weight += item.weight
                        print(f"Added {amount_to_add} {item.name} to existing stack")
                        return True

        # Find empty slot
        for i in range(self.max_slots):
            if self.items[i] is None:
                self.items[i] = item
                self.current_weight += item.weight
                print(f"Added {item.name} to inventory")
                return True

        print("Inventory is full!")
        return False

    def remove_item(self, slot_index: int, quantity: int = 1) -> Optional[Item]:
        """Remove item from inventory. Returns the removed item."""
        if not (0 <= slot_index < self.max_slots):
            return None

        item = self.items[slot_index]
        if not item:
            return None

        if quantity >= item.quantity:
            # Remove entire stack
            self.items[slot_index] = None
            self.current_weight -= item.weight
            print(f"Removed {item.name} from inventory")
            return item
        else:
            # Remove partial stack
            item.quantity -= quantity
            self.current_weight -= item.weight * (quantity / item.quantity)
            print(f"Removed {quantity} {item.name} from inventory")

            # Create a copy of the item with the removed quantity
            removed_item = type(item)(
                name=item.name,
                item_type=item.item_type,
                rarity=item.rarity,
                description=item.description,
                value=item.value,
                weight=item.weight,
                stackable=item.stackable,
                max_stack=item.max_stack,
                quantity=quantity
            )
            return removed_item

    def get_item(self, slot_index: int) -> Optional[Item]:
        """Get item at slot index."""
        if 0 <= slot_index < self.max_slots:
            return self.items[slot_index]
        return None

    def find_item(self, item_name: str) -> List[int]:
        """Find slots containing items with given name."""
        slots = []
        for i, item in enumerate(self.items):
            if item and item.name == item_name:
                slots.append(i)
        return slots

    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get summary of inventory contents."""
        weapon_count = 0
        armor_count = 0
        consumable_count = 0
        material_count = 0
        total_items = 0
        used_slots = 0

        for item in self.items:
            if item:
                used_slots += 1
                total_items += item.quantity

                if item.item_type == ItemType.WEAPON:
                    weapon_count += 1
                elif item.item_type == ItemType.ARMOR:
                    armor_count += 1
                elif item.item_type == ItemType.CONSUMABLE:
                    consumable_count += 1
                elif item.item_type == ItemType.MATERIAL:
                    material_count += 1

        return {
            "total_items": total_items,
            "used_slots": used_slots,
            "max_slots": self.max_slots,
            "current_weight": self.current_weight,
            "weight_limit": self.weight_limit,
            "gold": self.gold,
            "weapons": weapon_count,
            "armor": armor_count,
            "consumables": consumable_count,
            "materials": material_count
        }

    def sort_inventory(self, sort_by: str = "type"):
        """Sort inventory by specified criteria."""
        # Remove None items
        valid_items = [item for item in self.items if item is not None]

        if sort_by == "type":
            valid_items.sort(key=lambda x: (x.item_type.value, x.rarity.value, x.name))
        elif sort_by == "rarity":
            valid_items.sort(key=lambda x: (x.rarity.value, x.item_type.value, x.name))
        elif sort_by == "name":
            valid_items.sort(key=lambda x: x.name)
        elif sort_by == "value":
            valid_items.sort(key=lambda x: x.value, reverse=True)

        # Rebuild inventory
        self.items = valid_items + [None] * (self.max_slots - len(valid_items))

class ItemFactory:
    """Factory for creating various items."""

    def __init__(self):
        """Initialize item factory with templates."""
        self.weapon_templates = {
            "steel_sword": {
                "name": "Steel Sword",
                "weapon_type": WeaponType.SWORD,
                "damage": 20,
                "damage_type": DamageType.PHYSICAL,
                "attack_speed": 1.0,
                "range": 50,
                "critical_chance": 0.12,
                "critical_multiplier": 2.2,
                "durability": 120,
                "max_durability": 120,
                "rarity": ItemRarity.UNCOMMON,
                "value": 150,
                "weight": 3.0
            },
            "ice_blade": {
                "name": "Ice Blade",
                "weapon_type": WeaponType.SWORD,
                "damage": 18,
                "damage_type": DamageType.ICE,
                "attack_speed": 1.1,
                "range": 45,
                "critical_chance": 0.15,
                "critical_multiplier": 2.5,
                "durability": 100,
                "max_durability": 100,
                "special_effects": ["freeze"],
                "rarity": ItemRarity.RARE,
                "value": 300,
                "weight": 2.5
            },
            "thunder_hammer": {
                "name": "Thunder Hammer",
                "weapon_type": WeaponType.AXE,
                "damage": 35,
                "damage_type": DamageType.LIGHTNING,
                "attack_speed": 0.6,
                "range": 40,
                "critical_chance": 0.08,
                "critical_multiplier": 3.0,
                "durability": 80,
                "max_durability": 80,
                "special_effects": ["stun"],
                "rarity": ItemRarity.EPIC,
                "value": 500,
                "weight": 8.0
            }
        }

        self.armor_templates = {
            "steel_armor": {
                "name": "Steel Armor",
                "armor_type": "heavy",
                "physical_defense": 18,
                "magical_defense": 8,
                "fire_resistance": 0.3,
                "ice_resistance": 0.2,
                "lightning_resistance": 0.1,
                "poison_resistance": 0.1,
                "weight": 12.0,
                "durability": 150,
                "max_durability": 150,
                "rarity": ItemRarity.UNCOMMON,
                "value": 200,
                "weight": 12.0
            },
            "mage_robes": {
                "name": "Mage Robes",
                "armor_type": "light",
                "physical_defense": 3,
                "magical_defense": 15,
                "fire_resistance": 0.4,
                "ice_resistance": 0.4,
                "lightning_resistance": 0.4,
                "poison_resistance": 0.2,
                "weight": 1.5,
                "durability": 60,
                "max_durability": 60,
                "rarity": ItemRarity.RARE,
                "value": 350,
                "weight": 1.5
            }
        }

        self.consumable_templates = {
            "health_potion": {
                "name": "Health Potion",
                "effect_type": "heal",
                "effect_value": 50,
                "rarity": ItemRarity.COMMON,
                "value": 25,
                "weight": 0.5,
                "description": "Restores 50 health points"
            },
            "mana_potion": {
                "name": "Mana Potion",
                "effect_type": "mana",
                "effect_value": 30,
                "rarity": ItemRarity.COMMON,
                "value": 20,
                "weight": 0.5,
                "description": "Restores 30 mana points"
            },
            "strength_potion": {
                "name": "Strength Potion",
                "effect_type": "buff",
                "effect_value": 5,
                "duration": 60.0,
                "rarity": ItemRarity.UNCOMMON,
                "value": 75,
                "weight": 0.5,
                "description": "Increases strength by 5 for 60 seconds"
            }
        }

        self.material_templates = {
            "iron_ore": {
                "name": "Iron Ore",
                "material_type": "metal",
                "quality": 1,
                "rarity": ItemRarity.COMMON,
                "value": 10,
                "weight": 2.0,
                "description": "Raw iron ore for crafting"
            },
            "magic_crystal": {
                "name": "Magic Crystal",
                "material_type": "magic",
                "quality": 3,
                "rarity": ItemRarity.RARE,
                "value": 100,
                "weight": 0.5,
                "description": "Pure magic crystal for enchanting"
            }
        }

    def create_weapon(self, template_name: str) -> Optional[Weapon]:
        """Create a weapon from template."""
        if template_name not in self.weapon_templates:
            return None

        template = self.weapon_templates[template_name]
        return Weapon(
            name=template["name"],
            weapon_type=template["weapon_type"],
            damage=template["damage"],
            damage_type=template["damage_type"],
            attack_speed=template["attack_speed"],
            range=template["range"],
            critical_chance=template["critical_chance"],
            critical_multiplier=template["critical_multiplier"],
            durability=template["durability"],
            max_durability=template["max_durability"],
            special_effects=template.get("special_effects", [])
        )

    def create_armor(self, template_name: str) -> Optional[Armor]:
        """Create armor from template."""
        if template_name not in self.armor_templates:
            return None

        template = self.armor_templates[template_name]
        return Armor(
            name=template["name"],
            armor_type=template["armor_type"],
            physical_defense=template["physical_defense"],
            magical_defense=template["magical_defense"],
            fire_resistance=template["fire_resistance"],
            ice_resistance=template["ice_resistance"],
            lightning_resistance=template["lightning_resistance"],
            poison_resistance=template["poison_resistance"],
            weight=template["weight"],
            durability=template["durability"],
            max_durability=template["max_durability"]
        )

    def create_consumable(self, template_name: str) -> Optional[ConsumableItem]:
        """Create consumable from template."""
        if template_name not in self.consumable_templates:
            return None

        template = self.consumable_templates[template_name]
        item = ConsumableItem(
            name=template["name"],
            effect_type=template["effect_type"],
            effect_value=template["effect_value"],
            duration=template.get("duration", 0.0)
        )
        item.rarity = template["rarity"]
        item.description = template["description"]
        item.value = template["value"]
        item.weight = template["weight"]
        return item

    def create_material(self, template_name: str) -> Optional[MaterialItem]:
        """Create material from template."""
        if template_name not in self.material_templates:
            return None

        template = self.material_templates[template_name]
        item = MaterialItem(
            name=template["name"],
            material_type=template["material_type"],
            quality=template["quality"]
        )
        item.rarity = template["rarity"]
        item.description = template["description"]
        item.value = template["value"]
        item.weight = template["weight"]
        return item

    def create_random_item(self, rarity_weights: Dict[ItemRarity, float] = None) -> Optional[Item]:
        """Create a random item based on rarity weights."""
        if rarity_weights is None:
            rarity_weights = {
                ItemRarity.COMMON: 0.5,
                ItemRarity.UNCOMMON: 0.3,
                ItemRarity.RARE: 0.15,
                ItemRarity.EPIC: 0.04,
                ItemRarity.LEGENDARY: 0.01
            }

        # Choose rarity
        rarity = random.choices(
            list(rarity_weights.keys()),
            weights=list(rarity_weights.values())
        )[0]

        # Choose item type
        item_types = ["weapon", "armor", "consumable", "material"]
        item_type = random.choice(item_types)

        # Create item based on type and rarity
        if item_type == "weapon":
            available_weapons = [name for name, template in self.weapon_templates.items()
                               if template["rarity"] == rarity]
            if available_weapons:
                weapon_name = random.choice(available_weapons)
                return self.create_weapon(weapon_name)

        elif item_type == "armor":
            available_armor = [name for name, template in self.armor_templates.items()
                              if template["rarity"] == rarity]
            if available_armor:
                armor_name = random.choice(available_armor)
                return self.create_armor(armor_name)

        elif item_type == "consumable":
            available_consumables = [name for name, template in self.consumable_templates.items()
                                   if template["rarity"] == rarity]
            if available_consumables:
                consumable_name = random.choice(available_consumables)
                return self.create_consumable(consumable_name)

        elif item_type == "material":
            available_materials = [name for name, template in self.material_templates.items()
                                 if template["rarity"] == rarity]
            if available_materials:
                material_name = random.choice(available_materials)
                return self.create_material(material_name)

        # Fallback to common health potion
        return self.create_consumable("health_potion")

class LootTable:
    """Loot table for generating drops from enemies and containers."""

    def __init__(self, item_factory: ItemFactory):
        """Initialize loot table."""
        self.item_factory = item_factory

    def generate_loot(self, difficulty: float, num_items: int = 1) -> List[Item]:
        """Generate loot based on difficulty."""
        items = []

        # Adjust rarity weights based on difficulty
        base_weights = {
            ItemRarity.COMMON: 0.5,
            ItemRarity.UNCOMMON: 0.3,
            ItemRarity.RARE: 0.15,
            ItemRarity.EPIC: 0.04,
            ItemRarity.LEGENDARY: 0.01
        }

        # Boost higher rarities for higher difficulty
        difficulty_multiplier = min(difficulty / 10.0, 2.0)
        adjusted_weights = {
            ItemRarity.COMMON: base_weights[ItemRarity.COMMON] / difficulty_multiplier,
            ItemRarity.UNCOMMON: base_weights[ItemRarity.UNCOMMON],
            ItemRarity.RARE: base_weights[ItemRarity.RARE] * difficulty_multiplier,
            ItemRarity.EPIC: base_weights[ItemRarity.EPIC] * difficulty_multiplier,
            ItemRarity.LEGENDARY: base_weights[ItemRarity.LEGENDARY] * difficulty_multiplier
        }

        for _ in range(num_items):
            item = self.item_factory.create_random_item(adjusted_weights)
            if item:
                items.append(item)

        return items

    def generate_gold_drop(self, difficulty: float) -> int:
        """Generate gold drop based on difficulty."""
        base_gold = 10
        gold_range = int(base_gold * difficulty)
        return random.randint(base_gold, base_gold + gold_range)
