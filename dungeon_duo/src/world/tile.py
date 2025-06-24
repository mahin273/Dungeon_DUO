"""
tile.py

Tile definitions for Dungeon Duo: Rough AI.
Represents dungeon floor, walls, destructible terrain, and interactive elements.
"""

import pygame
from enum import Enum
from typing import Dict, Any, Optional, Tuple
import random
from ..game.inventory import ConsumableItem, ItemRarity, ItemType, Item
from ..game.combat import Weapon, Armor, WeaponType, DamageType


class TileType(Enum):
    """Enumeration of tile types in the dungeon."""
    FLOOR = "floor"
    WALL = "wall"
    DOOR = "door"
    STAIRS_UP = "stairs_up"
    STAIRS_DOWN = "stairs_down"
    WATER = "water"
    LAVA = "lava"
    TRAP = "trap"
    CHEST = "chest"
    BARRIER = "barrier"
    CORRIDOR = "corridor"
    ROOM_FLOOR = "room_floor"
    HEALTH_QUEST = "health_quest"  # New tile type


class Tile:
    """
    Represents a single tile in the dungeon.

    Attributes:
        tile_type (TileType): Type of the tile
        walkable (bool): Whether entities can walk on this tile
        transparent (bool): Whether this tile blocks line of sight
        destructible (bool): Whether this tile can be destroyed
        damage (int): Damage dealt when walking on this tile
        health (int): Current health of the tile (for destructible tiles)
        max_health (int): Maximum health of the tile
        color (Tuple[int, int, int]): RGB color for rendering
        symbol (str): ASCII symbol for text rendering
        properties (Dict[str, Any]): Additional properties
        discovered (bool): Whether the player has discovered this tile
        visible (bool): Whether this tile is currently visible
        last_triggered_time (float): Time when the trap was last triggered
    """

    def __init__(self, tile_type: TileType, walkable: bool = None, transparent: bool = None, discovered: bool = False, visible: bool = False):
        """
        Initialize a Tile.
        Args:
            tile_type (TileType): The type of the tile.
            walkable (bool): Whether this tile can be walked on.
            transparent (bool): Whether this tile blocks line of sight.
            discovered (bool): Whether the player has discovered this tile
            visible (bool): Whether this tile is currently visible
        """
        self.tile_type = tile_type
        self.walkable = walkable
        self.transparent = transparent
        self.discovered = discovered
        self.visible = visible
        self.last_triggered_time: float = 0.0

        # These attributes will be set by _set_default_properties
        self.destructible = False
        self.damage = 0
        self.health = 0
        self.max_health = 0
        self.color = (0, 0, 0) # Default to black, will be overwritten
        self.symbol = ' '
        self.properties = {}

        # Set default properties for the tile
        self._set_default_properties()

        # Override with specified values if they are not None
        if walkable is not None:
            self.walkable = walkable
        if transparent is not None:
            self.transparent = transparent


    def _set_default_properties(self):
        """Set default properties based on tile type."""
        defaults = {
            TileType.FLOOR: {
                'walkable': True,
                'transparent': True,
                'color': (150, 150, 150),
                'symbol': '.'
            },
            TileType.WALL: {
                'walkable': False,
                'transparent': False,
                'destructible': True,
                'health': 200,
                'max_health': 200,
                'color': (100, 100, 100),
                'symbol': '#'
            },
            TileType.DOOR: {
                'walkable': True,
                'transparent': False,
                'destructible': True,
                'health': 150,
                'max_health': 150,
                'color': (139, 69, 19),
                'symbol': '+'
            },
            TileType.STAIRS_UP: {
                'walkable': True,
                'transparent': True,
                'color': (255, 255, 0),
                'symbol': '<'
            },
            TileType.STAIRS_DOWN: {
                'walkable': True,
                'transparent': True,
                'color': (255, 255, 0),
                'symbol': '>'
            },
            TileType.WATER: {
                'walkable': False,
                'transparent': True,
                'damage': 5,
                'color': (0, 0, 255),
                'symbol': '~'
            },
            TileType.LAVA: {
                'walkable': False,
                'transparent': True,
                'damage': 20,
                'color': (255, 0, 0),
                'symbol': '^'
            },
            TileType.TRAP: {
                'walkable': True,
                'transparent': True,
                'damage': 15,
                'color': (220, 20, 60), # Crimson Red
                'symbol': '^'
            },
            TileType.CHEST: {
                'walkable': False,
                'transparent': False,
                'destructible': True,
                'health': 100,
                'max_health': 100,
                'color': (255, 215, 0),
                'symbol': 'C'
            },
            TileType.BARRIER: {
                'walkable': False,
                'transparent': False,
                'destructible': True,
                'health': 300,
                'max_health': 300,
                'color': (128, 128, 128),
                'symbol': '='
            },
            TileType.CORRIDOR: {
                'walkable': True,
                'transparent': True,
                'color': (120, 120, 120),
                'symbol': '.'
            },
            TileType.ROOM_FLOOR: {
                'walkable': True,
                'transparent': True,
                'color': (140, 140, 140),
                'symbol': '.'
            },
            TileType.HEALTH_QUEST: {
                'walkable': True,
                'transparent': True,
                'color': (255, 140, 0),  # Orange
                'symbol': 'H'
            }
        }

        if self.tile_type in defaults:
            for key, value in defaults[self.tile_type].items():
                setattr(self, key, value)

    def take_damage(self, damage: int) -> bool:
        """
        Apply damage to the tile.

        Args:
            damage (int): Amount of damage to apply

        Returns:
            bool: True if tile was destroyed, False otherwise
        """
        if not self.destructible:
            return False

        self.health -= damage
        if self.health <= 0:
            # Convert to floor when destroyed
            self.tile_type = TileType.FLOOR
            self.walkable = True
            self.transparent = True
            self.destructible = False
            self.damage = 0
            self.color = (100, 100, 100)
            self.symbol = '.'
            return True
        return False

    def get_display_color(self) -> Tuple[int, int, int]:
        """
        Get the color for display, considering visibility and discovery.

        Returns:
            Tuple[int, int, int]: RGB color for display
        """
        if not self.discovered:
            return (0, 0, 0)  # Black for undiscovered
        elif not self.visible:
            return tuple(max(0, c // 3) for c in self.color)  # Darkened for remembered
        else:
            return self.color

    def get_display_symbol(self) -> str:
        """
        Get the symbol for display, considering visibility and discovery.

        Returns:
            str: Symbol for display
        """
        if not self.discovered:
            return ' '
        elif not self.visible:
            return self.symbol
        else:
            return self.symbol

    def is_interactive(self) -> bool:
        """
        Check if this tile is interactive (doors, chests, stairs).

        Returns:
            bool: True if interactive
        """
        return self.tile_type in [TileType.DOOR, TileType.CHEST, TileType.STAIRS_UP, TileType.STAIRS_DOWN]

    def interact(self, player=None) -> Dict[str, Any]:
        """
        Perform interaction with the tile.

        Returns:
            Dict[str, Any]: Interaction result
        """
        if self.tile_type == TileType.DOOR:
            # Toggle door state
            if self.walkable:
                self.walkable = False
                self.transparent = False
                self.symbol = '+'
            else:
                self.walkable = True
                self.transparent = True
                self.symbol = '/'
            return {'type': 'door_toggle', 'walkable': self.walkable}

        elif self.tile_type == TileType.CHEST:
            # Open chest and convert to floor
            if not self.properties.get('opened', False):
                self.properties['opened'] = True
                loot = self._generate_loot()
                # Convert chest to a standard room floor tile after opening
                self.tile_type = TileType.ROOM_FLOOR
                self._set_default_properties() # This resets all properties to match a ROOM_FLOOR
                return {'type': 'chest_opened', 'loot': loot}
            else:
                return {'type': 'chest_already_opened'}

        elif self.tile_type == TileType.HEALTH_QUEST:
            if player is not None and hasattr(player, 'stats') and hasattr(player.stats, 'health') and hasattr(player.stats, 'max_health'):
                if player.stats.health < player.stats.max_health:
                    player.stats.health = min(player.stats.health + 10, player.stats.max_health)
                    # Remove the health quest tile
                    self.tile_type = TileType.ROOM_FLOOR
                    self._set_default_properties()
                    return {'type': 'health_quest_consumed', 'amount': 10}
                else:
                    return {'type': 'health_quest_full_health'}
            else:
                return {'type': 'health_quest_no_player'}

        elif self.tile_type in [TileType.STAIRS_UP, TileType.STAIRS_DOWN]:
            return {'type': 'stairs', 'direction': self.tile_type.value}

        return {'type': 'none'}

    def _generate_loot(self) -> Optional[Item]:
        """Generate random loot for chests."""
        loot_types = ['health_potion', 'mana_potion', 'gold', 'weapon', 'armor']
        loot_type = random.choice(loot_types)

        if loot_type == 'health_potion':
            item = ConsumableItem(
                name="Health Potion",
                effect_type="heal",
                effect_value=random.randint(10, 30)
            )
            item.rarity = ItemRarity.COMMON
            item.description = "Restores health"
            item.value = 5
            item.weight = 0.5
            return item
        elif loot_type == 'mana_potion':
            item = ConsumableItem(
                name="Mana Potion",
                effect_type="mana",
                effect_value=random.randint(10, 30)
            )
            item.rarity = ItemRarity.COMMON
            item.description = "Restores mana"
            item.value = 5
            item.weight = 0.5
            return item
        elif loot_type == 'gold':
            gold_amount = random.randint(5, 25)
            item = ConsumableItem(
                name=f"{gold_amount} Gold",
                effect_type="gold",
                effect_value=gold_amount
            )
            item.rarity = ItemRarity.COMMON
            item.description = f"Contains {gold_amount} gold pieces"
            item.value = gold_amount
            item.weight = 0.1
            return item
        elif loot_type == 'weapon':
            weapon_names = ["Rusty Sword", "Iron Dagger", "Steel Mace", "Wooden Staff"]
            weapon_name = random.choice(weapon_names)
            damage = random.randint(5, 15)
            return Weapon(
                name=weapon_name,
                weapon_type=WeaponType.SWORD,
                damage=damage,
                damage_type=DamageType.PHYSICAL,
                rarity=ItemRarity.UNCOMMON,
                description=f"A {weapon_name.lower()} that deals {damage} damage",
                value=damage * 2,
                weight=2.0
            )
        elif loot_type == 'armor':
            armor_names = ["Leather Vest", "Chain Mail", "Iron Breastplate", "Mage Robes"]
            armor_name = random.choice(armor_names)
            armor_type = random.choice(["light", "medium", "heavy"])
            physical_def = random.randint(2, 8)
            magical_def = random.randint(1, 5)
            fire_res = round(random.uniform(0.0, 0.2), 2)
            ice_res = round(random.uniform(0.0, 0.2), 2)
            lightning_res = round(random.uniform(0.0, 0.2), 2)
            poison_res = round(random.uniform(0.0, 0.2), 2)
            weight = random.uniform(2.0, 6.0)
            max_durability = random.randint(20, 40)
            return Armor(
                name=armor_name,
                armor_type=armor_type,
                physical_defense=physical_def,
                magical_defense=magical_def,
                fire_resistance=fire_res,
                ice_resistance=ice_res,
                lightning_resistance=lightning_res,
                poison_resistance=poison_res,
                weight=weight,
                durability=max_durability,
                max_durability=max_durability
            )

        return None

    def __str__(self) -> str:
        return f"Tile({self.tile_type.value}, walkable={self.walkable}, transparent={self.transparent})"

    def __repr__(self) -> str:
        return self.__str__()


class TileFactory:
    """Factory class for creating tiles with predefined configurations."""

    @staticmethod
    def create_floor() -> Tile:
        """Create a basic floor tile."""
        return Tile(TileType.FLOOR)

    @staticmethod
    def create_wall() -> Tile:
        """Create a basic wall tile."""
        return Tile(TileType.WALL)

    @staticmethod
    def create_door() -> Tile:
        """Create a door tile."""
        return Tile(TileType.DOOR)

    @staticmethod
    def create_stairs_up() -> Tile:
        """Create stairs up tile."""
        return Tile(TileType.STAIRS_UP)

    @staticmethod
    def create_stairs_down() -> Tile:
        """Create stairs down tile."""
        return Tile(TileType.STAIRS_DOWN)

    @staticmethod
    def create_water() -> Tile:
        """Create water tile."""
        return Tile(TileType.WATER)

    @staticmethod
    def create_lava() -> Tile:
        """Create lava tile."""
        return Tile(TileType.LAVA)

    @staticmethod
    def create_trap() -> Tile:
        """Create a trap tile."""
        return Tile(TileType.TRAP)

    @staticmethod
    def create_chest() -> Tile:
        """Create a chest tile."""
        return Tile(TileType.CHEST)

    @staticmethod
    def create_barrier() -> Tile:
        """Create a barrier tile."""
        return Tile(TileType.BARRIER)

    @staticmethod
    def create_corridor() -> Tile:
        """Create a corridor tile."""
        return Tile(TileType.CORRIDOR)

    @staticmethod
    def create_room_floor() -> Tile:
        """Create a room floor tile."""
        return Tile(TileType.ROOM_FLOOR)

    @staticmethod
    def create_health_quest() -> Tile:
        """Create a health quest tile."""
        return Tile(TileType.HEALTH_QUEST)
