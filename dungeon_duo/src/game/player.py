"""
player.py

Enhanced Player class for Dungeon Duo: Rough AI.
Integrates with the new combat system including weapons, armor, and combat stats.
"""

import pygame
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time
import math
import random

from .combat import CombatStats, Weapon, Armor
from .inventory import Inventory, ItemFactory, ConsumableItem, ItemType, Item, ItemRarity
from .skills import SkillTree, get_default_player_skills
from .items.weapon import Weapon, WeaponType, DamageType

class PlayerAction(Enum):
    """Enumeration of trackable player actions."""
    MOVE = "move"
    ATTACK = "attack"
    USE_ITEM = "use_item"
    DODGE = "dodge"
    EXPLORE = "explore"

@dataclass
class PlayerStats:
    """Player statistics and attributes."""
    health: int = 100
    max_health: int = 100
    mana: int = 50
    max_mana: int = 50
    stamina: int = 100
    max_stamina: int = 100
    speed: float = 5.0
    # Combat attributes
    attack: int = 10
    defense: int = 5  # Added defense attribute
    crit_chance: float = 0.05
    crit_multiplier: float = 2.0
    # RPG progression attributes
    level: int = 1
    experience: int = 0
    experience_to_next: int = 100

class Player:
    """Enhanced player class with combat system integration and skill tree."""

    def __init__(self, x: float, y: float):
        """Initialize the player with position and enhanced systems."""
        # Position and movement
        self.x = x
        self.y = y
        self.velocity_x = 0
        self.velocity_y = 0
        self.name = "Player"

        # Core stats
        self.stats = PlayerStats()

        # Combat system integration
        self.combat_stats = CombatStats()
        self.equipped_weapon: Optional[Weapon] = None
        self.equipped_armor: Optional[Armor] = None

        # Enhanced inventory system
        self.inventory = Inventory(max_slots=50)
        self.item_factory = ItemFactory()

        # Combat state
        self.is_attacking = False
        self.last_attack_time = 0
        self.attack_cooldown = 1.0

        # Movement validation
        self.movement_validator = None
        self.event_handlers: Dict[str, List[callable]] = {
            "movement": [],
            "attack": [],
            "dodge": [],
            "level_up": [],
            "item_pickup": [],
            "item_use": []
        }

        # Active effects
        self.active_effects = {}

        # Combat history
        self.combat_history: List[Dict] = []

        # Skill tree system
        self.skill_tree = SkillTree()
        for skill in get_default_player_skills():
            self.skill_tree.add_skill(skill)
        self.skill_tree.skill_points = 0

    def update(self, delta_time: float):
        """Update player state."""
        # Update special effects
        self._update_special_effects()

        # Regenerate resources
        self._regenerate_resources(delta_time)

        # Update attack cooldown
        if self.is_attacking:
            current_time = time.time()
            if current_time - self.last_attack_time >= self.attack_cooldown:
                self.is_attacking = False

    def move(self, dx: float, dy: float):
        """Enhanced movement with skill effects."""
        # Apply speed modifications from skills
        if hasattr(self, 'speed_multiplier'):
            dx *= self.speed_multiplier
            dy *= self.speed_multiplier

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.7071  # 1/sqrt(2)
            dy *= 0.7071

        # Calculate new position
        new_x = self.x + dx * self.stats.speed * 0.1  # Reduced speed multiplier for smoother movement
        new_y = self.y + dy * self.stats.speed * 0.1

        # Validate movement
        if self.movement_validator:
            # Check with rounded coordinates for collision
            if not self.movement_validator(int(new_x), int(new_y)):
                return

        # Apply movement
        self.x = new_x
        self.y = new_y
        self.velocity_x = dx * self.stats.speed
        self.velocity_y = dy * self.stats.speed

        # Emit movement event
        self._emit_event("movement", {
            "position": (self.x, self.y),
            "velocity": (self.velocity_x, self.velocity_y)
        })

    def attack(self, target) -> bool:
        """Attack a target."""
        if not self.equipped_weapon:
            # Unarmed attack
            damage = max(1, self.stats.attack // 2)
            damage_type = DamageType.PHYSICAL
        else:
            # Use weapon and check if it's broken
            if not self.equipped_weapon.use():
                # Weapon is broken but still usable at reduced damage
                damage = self.equipped_weapon.get_damage()
                print(f"{self.equipped_weapon.name} is broken! Dealing reduced damage.")
            else:
                damage = self.equipped_weapon.get_damage()
            damage_type = self.equipped_weapon.damage_type

        # Apply critical hit chance
        is_critical = random.random() < self.stats.crit_chance
        if is_critical:
            damage *= self.stats.crit_multiplier

        # Let target handle the damage
        damage_dealt = target.take_damage(damage)

        # Print combat message
        if damage_dealt > 0:
            if is_critical:
                print(f"{self.name} landed a critical hit on {target.name} for {damage_dealt} {damage_type.value} damage!")
            else:
                print(f"{self.name} hit {target.name} for {damage_dealt} {damage_type.value} damage!")
        elif damage_dealt == 0:
            print(f"{target.name} blocked {self.name}'s attack!")
        else:  # damage_dealt < 0 indicates dodge
            print(f"{target.name} dodged {self.name}'s attack!")

        return damage_dealt > 0

    def take_damage(self, amount: int, damage_type: str = "physical"):
        """Enhanced damage handling with skill effects and damage types."""

        # Environmental damage should not be reduced by armor or skills
        if damage_type == "environmental":
            self.stats.health = max(0, self.stats.health - amount)
            self.combat_stats.total_damage_taken += amount
            print(f"DEBUG: Player took {amount} environmental damage.")
            if self.stats.health <= 0:
                print(f"{self.name} has been defeated by the environment!")
            return

        # --- Combat Damage Calculation ---
        original_amount = amount

        # Apply armor defense if equipped
        if self.equipped_armor:
            if damage_type == "physical":
                amount = max(1, amount - self.equipped_armor.physical_defense)
            elif damage_type == "magical":
                amount = max(1, amount - self.equipped_armor.magical_defense)

        # Iron Wall: Reduce damage when health is high
        if hasattr(self, 'iron_wall') and self.iron_wall:
            if self.stats.health > self.stats.max_health * 0.7:
                amount = int(amount * 0.5)
                print(f"{self.name}'s Iron Wall reduces damage!")

        # Tough Skin: Always reduce damage
        if hasattr(self, 'tough_skin') and self.tough_skin:
            amount = max(1, amount - 2)

        # Record damage time for Adrenaline Rush
        self.last_damage_time = time.time()

        self.stats.health = max(0, self.stats.health - amount)
        self.combat_stats.total_damage_taken += amount

        # Record combat event
        self.combat_history.append({
            "type": "damage_taken",
            "amount": amount,
            "original_amount": original_amount,
            "damage_type": damage_type,
            "current_health": self.stats.health,
            "timestamp": time.time()
        })

        if self.stats.health <= 0:
            print(f"{self.name} has been defeated!")

    def heal(self, amount: int):
        """Heal the player."""
        old_health = self.stats.health
        self.stats.health = min(self.stats.max_health, self.stats.health + amount)
        healed_amount = self.stats.health - old_health

        if healed_amount > 0:
            print(f"{self.name} healed for {healed_amount} health!")

    def equip_weapon(self, weapon: Weapon):
        """Equip a weapon from inventory."""
        # Find weapon in inventory
        weapon_slots = self.inventory.find_item(weapon.name)
        if weapon_slots:
            self.equipped_weapon = weapon
            self.attack_cooldown = 1.0 / weapon.attack_speed
            print(f"{self.name} equipped {weapon.name}!")
        else:
            print("Weapon not in inventory!")

    def equip_armor(self, armor: Armor):
        """Equip armor from inventory."""
        # Find armor in inventory
        armor_slots = self.inventory.find_item(armor.name)
        if armor_slots:
            self.equipped_armor = armor
            print(f"{self.name} equipped {armor.name}!")
        else:
            print("Armor not in inventory!")

    def add_item_to_inventory(self, item):
        """Add an item to inventory."""
        if self.inventory.add_item(item):
            # Emit item pickup event
            self._emit_event("item_pickup", {
                "item_type": item.item_type.value,
                "item_name": item.name,
                "rarity": item.rarity.value,
                "timestamp": time.time()
            })

    def use_item(self, slot_index: int):
        """Use an item from inventory."""
        item = self.inventory.get_item(slot_index)
        if not item:
            print("No item in that slot!")
            return False

        if item.item_type == ItemType.CONSUMABLE:
            return self._use_consumable(item, slot_index)
        elif item.item_type == ItemType.WEAPON:
            return self._equip_weapon_from_slot(slot_index)
        elif item.item_type == ItemType.ARMOR:
            return self._equip_armor_from_slot(slot_index)
        else:
            print(f"Cannot use {item.name}!")
            return False

    def _use_consumable(self, item: ConsumableItem, slot_index: int):
        """Use a consumable item."""
        if item.effect_type == "heal":
            self.heal(item.effect_value)
        elif item.effect_type == "mana":
            self.stats.mana = min(self.stats.max_mana, self.stats.mana + item.effect_value)
            print(f"{self.name} restored {item.effect_value} mana!")
        elif item.effect_type == "stamina":
            self.stats.stamina = min(self.stats.max_stamina, self.stats.stamina + item.effect_value)
            print(f"{self.name} restored {item.effect_value} stamina!")
        elif item.effect_type == "buff":
            # Apply buff effect
            self._apply_buff(item)
        else:
            print(f"Unknown effect type: {item.effect_type}")
            return False

        # Remove item from inventory
        self.inventory.remove_item(slot_index, 1)

        # Emit item use event
        self._emit_event("item_use", {
            "item_name": item.name,
            "effect_type": item.effect_type,
            "timestamp": time.time()
        })

        return True

    def _apply_buff(self, item: ConsumableItem):
        """Apply a buff effect to the player."""
        if item.effect_type == "buff":
            # Apply strength buff
            self.combat_stats.strength += item.effect_value
            print(f"{self.name} gained +{item.effect_value} strength for {item.duration} seconds!")

            # Schedule buff removal
            def remove_buff():
                self.combat_stats.strength -= item.effect_value
                print(f"{self.name}'s strength buff expired!")

            # In a real implementation, you'd use a timer system
            # For now, we'll just apply the buff immediately

    def _equip_weapon_from_slot(self, slot_index: int):
        """Equip a weapon from inventory slot."""
        item = self.inventory.get_item(slot_index)
        if item and item.item_type == ItemType.WEAPON:
            # Create weapon from item data
            weapon = self.item_factory.create_weapon(item.name.lower().replace(" ", "_"))
            if weapon:
                self.equip_weapon(weapon)
                return True
        return False

    def _equip_armor_from_slot(self, slot_index: int):
        """Equip armor from inventory slot."""
        item = self.inventory.get_item(slot_index)
        if item and item.item_type == ItemType.ARMOR:
            # Create armor from item data
            armor = self.item_factory.create_armor(item.name.lower().replace(" ", "_"))
            if armor:
                self.equip_armor(armor)
                return True
        return False

    def add_weapon_to_inventory(self, weapon: Weapon):
        """Add a weapon to inventory (legacy method)."""
        # Convert weapon to item and add to inventory
        item = Item(name=weapon.name)
        item.item_type = ItemType.WEAPON
        item.rarity = ItemRarity.UNCOMMON  # Default rarity
        item.description = f"A {weapon.weapon_type.value} weapon"
        item.value = weapon.damage * 10
        item.weight = weapon.range / 10
        self.add_item_to_inventory(item)

    def add_armor_to_inventory(self, armor: Armor):
        """Add armor to inventory (legacy method)."""
        # Convert armor to item and add to inventory
        item = Item(name=armor.name)
        item.item_type = ItemType.ARMOR
        item.rarity = ItemRarity.UNCOMMON  # Default rarity
        item.description = f"{armor.armor_type} armor"
        item.value = armor.physical_defense * 15
        item.weight = armor.weight
        self.add_item_to_inventory(item)

    def set_movement_validator(self, validator):
        """Set the movement validation function."""
        self.movement_validator = validator

    def add_event_handler(self, event_type: str, handler: callable):
        """Add an event handler."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)

    def _emit_event(self, event_type: str, event_data: Dict):
        """Emit an event to all handlers."""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                handler(event_data)

    def _update_special_effects(self):
        """Update special effects on the player."""
        current_time = time.time()
        expired_effects = []

        for effect_type, effect_data in self.active_effects.items():
            # Apply damage per turn
            if effect_data["damage_per_turn"] > 0:
                self.take_damage(effect_data["damage_per_turn"])
                print(f"{self.name} takes {effect_data['damage_per_turn']} {effect_type} damage!")

            # Reduce duration
            effect_data["duration"] -= 1

            # Check if effect expired
            if effect_data["duration"] <= 0:
                expired_effects.append(effect_type)
                print(f"{self.name} is no longer affected by {effect_type}!")

        # Remove expired effects
        for effect_type in expired_effects:
            del self.active_effects[effect_type]

    def _regenerate_resources(self, delta_time: float):
        """Regenerate health, mana, and stamina over time."""
        # Health regeneration (slower)
        if self.stats.health < self.stats.max_health:
            self.stats.health = min(self.stats.max_health,
                                  self.stats.health + int(2 * delta_time))

        # Mana regeneration
        if self.stats.mana < self.stats.max_mana:
            self.stats.mana = min(self.stats.max_mana,
                                self.stats.mana + int(5 * delta_time))

        # Stamina regeneration
        if self.stats.stamina < self.stats.max_stamina:
            self.stats.stamina = min(self.stats.max_stamina,
                                   self.stats.stamina + int(10 * delta_time))

    def _distance_to(self, pos: Tuple[float, float]) -> float:
        """Calculate distance to a position."""
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return math.sqrt(dx*dx + dy*dy)

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the player."""
        inventory_summary = self.inventory.get_inventory_summary()

        return {
            "position": (self.x, self.y),
            "health": self.stats.health,
            "max_health": self.stats.max_health,
            "mana": self.stats.mana,
            "max_mana": self.stats.max_mana,
            "stamina": self.stats.stamina,
            "max_stamina": self.stats.max_stamina,
            "level": self.stats.level,
            "experience": self.stats.experience,
            "experience_to_next": self.stats.experience_to_next,
            "is_attacking": self.is_attacking,
            "equipped_weapon": self.equipped_weapon.name if self.equipped_weapon else None,
            "equipped_armor": self.equipped_armor.name if self.equipped_armor else None,
            "inventory": inventory_summary,
            "gold": self.inventory.gold,
            "velocity": (self.velocity_x, self.velocity_y),
            "active_effects": list(self.active_effects.keys()),
            "skill_tree": self.get_skill_tree_state()
        }

    def get_combat_summary(self) -> Dict[str, Any]:
        """Get combat statistics summary."""
        return {
            "level": self.stats.level,
            "total_damage_dealt": self.combat_stats.total_damage_dealt,
            "total_damage_taken": self.combat_stats.total_damage_taken,
            "critical_hits": self.combat_stats.critical_hits,
            "dodges": self.combat_stats.dodges,
            "blocks": self.combat_stats.blocks,
            "combat_history_length": len(self.combat_history)
        }

    def unlock_skill(self, skill_id: str):
        """Unlock a skill by ID if possible."""
        if self.skill_tree.unlock_skill(skill_id):
            print(f"{self.name} unlocked skill: {self.skill_tree.skills[skill_id].name}")
            # Apply skill effect (stat boost, etc.)
            self._apply_skill_effect(skill_id)
            return True
        print(f"Cannot unlock skill: {skill_id}")
        return False

    def _apply_skill_effect(self, skill_id: str):
        """Apply the effect of a skill to the player."""
        skill = self.skill_tree.skills.get(skill_id)
        if not skill:
            return
        # Example effects for default skills
        if skill_id == "power_strike":
            self.combat_stats.strength += 5
            print(f"{self.name}'s strength increased by 5!")
        elif skill_id == "tough_skin":
            self.combat_stats.constitution += 3
            print(f"{self.name}'s defense increased by 3!")
        elif skill_id == "quick_learner":
            # Could add a flag for bonus XP
            self.bonus_xp = 0.1
            print(f"{self.name} now gains 10% more experience!")
        elif skill_id == "adrenaline_rush":
            # Could add a flag for speed boost after damage
            self.adrenaline_rush = True
            print(f"{self.name} can now trigger Adrenaline Rush!")
        elif skill_id == "berserker":
            self.berserker = True
            print(f"{self.name} can now trigger Berserker mode!")
        elif skill_id == "iron_wall":
            self.iron_wall = True
            print(f"{self.name} can now trigger Iron Wall!")

    def get_skill_tree_state(self):
        """Return a summary of the player's skill tree."""
        return {
            "skill_points": self.skill_tree.skill_points,
            "unlocked_skills": [s.name for s in self.skill_tree.get_unlocked_skills()],
            "unlockable_skills": [s.name for s in self.skill_tree.get_unlockable_skills()],
        }
