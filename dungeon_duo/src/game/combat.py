"""
combat.py

Enhanced combat system for Dungeon Duo: Rough AI.
Includes weapon types, armor mechanics, critical hits, and damage types.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import random
import math
import time
from .items.weapon import Weapon, WeaponType, DamageType  # Use unified Weapon class and DamageType
from .items.item import ItemRarity

@dataclass
class Armor:
    """Represents armor with defense stats."""
    name: str
    armor_type: str  # "light", "medium", "heavy"
    physical_defense: int
    magical_defense: int
    fire_resistance: float  # 0.0 to 1.0
    ice_resistance: float
    lightning_resistance: float
    poison_resistance: float
    weight: float
    durability: int
    max_durability: int

    def __post_init__(self):
        self.durability = self.max_durability

    def use(self) -> bool:
        """Use the armor, reducing durability. Returns True if armor breaks."""
        self.durability -= 1
        return self.durability <= 0

    def repair(self, amount: int = None):
        """Repair the armor."""
        if amount is None:
            self.durability = self.max_durability
        else:
            self.durability = min(self.max_durability, self.durability + amount)

@dataclass
class CombatStats:
    """Comprehensive combat statistics."""
    # Base stats
    strength: int = 10
    dexterity: int = 10
    intelligence: int = 10
    constitution: int = 10

    # Combat modifiers
    critical_chance: float = 0.05
    critical_multiplier: float = 2.0
    dodge_chance: float = 0.05
    block_chance: float = 0.05

    # Resistances
    fire_resistance: float = 0.0
    ice_resistance: float = 0.0
    lightning_resistance: float = 0.0
    poison_resistance: float = 0.0

    # Combat history
    total_damage_dealt: int = 0
    total_damage_taken: int = 0
    critical_hits: int = 0
    dodges: int = 0
    blocks: int = 0

class CombatSystem:
    """Enhanced combat system with weapons, armor, and advanced mechanics."""

    DURABILITY_WARNING_THRESHOLD = 0.25  # Warn at 25% durability
    DURABILITY_CRITICAL_THRESHOLD = 0.1  # Critical warning at 10% durability

    def __init__(self):
        """Initialize the combat system."""
        self.combat_log: List[Dict] = []
        self.active_effects: Dict[str, List[Dict]] = {}
        self.durability_warnings: Dict[str, bool] = {}  # Track if warning was shown

        # Note: Weapon and armor creation is now handled by ItemFactory
        # Remove old templates since we use the factory pattern

    def create_weapon(self, template_name: str) -> Weapon:
        """Create a weapon from a template using the item factory."""
        # Use the item factory if available, otherwise fallback to direct instantiation
        from .inventory import ItemFactory
        factory = ItemFactory()
        weapon = factory.create_weapon(template_name)
        return weapon

    def create_armor(self, template_name: str) -> Armor:
        """Create armor from a template using the item factory."""
        from .inventory import ItemFactory
        factory = ItemFactory()
        armor = factory.create_armor(template_name)
        return armor

    def calculate_damage(self, attacker_weapon: Weapon, attacker_stats: CombatStats,
                        defender_armor: Armor, defender_stats: CombatStats) -> Dict[str, Any]:
        """Calculate damage with all modifiers applied."""
        # Base damage
        base_damage = attacker_weapon.get_damage()

        # Apply strength modifier for physical weapons
        if attacker_weapon.damage_type == DamageType.PHYSICAL:
            base_damage += attacker_stats.strength // 2

        # Apply intelligence modifier for magical weapons
        elif attacker_weapon.damage_type in [DamageType.MAGICAL, DamageType.FIRE, DamageType.ICE, DamageType.LIGHTNING]:
            base_damage += attacker_stats.intelligence // 2

        # Critical hit check
        critical_hit = False
        critical_damage = base_damage
        if random.random() < attacker_stats.critical_chance + getattr(attacker_weapon, 'critical_chance', 0.0):
            critical_hit = True
            critical_damage = int(base_damage * (attacker_stats.critical_multiplier + getattr(attacker_weapon, 'critical_multiplier', 1.0) - 1))

        # Dodge check
        if random.random() < defender_stats.dodge_chance:
            return {
                "damage": 0,
                "critical_hit": False,
                "dodged": True,
                "blocked": False,
                "damage_type": attacker_weapon.damage_type,
                "special_effects": []
            }

        # Block check
        blocked = False
        if random.random() < defender_stats.block_chance:
            blocked = True
            critical_damage = critical_damage // 2

        # Apply armor defense
        final_damage = critical_damage
        if defender_armor:
            if attacker_weapon.damage_type == DamageType.PHYSICAL:
                final_damage = max(1, final_damage - defender_armor.physical_defense)
            else:
                final_damage = max(1, final_damage - defender_armor.magical_defense)

        # Apply resistances
        resistance = 0.0
        if defender_armor:
            if attacker_weapon.damage_type == DamageType.FIRE:
                resistance = defender_armor.fire_resistance
            elif attacker_weapon.damage_type == DamageType.ICE:
                resistance = defender_armor.ice_resistance
            elif attacker_weapon.damage_type == DamageType.LIGHTNING:
                resistance = defender_armor.lightning_resistance
            elif attacker_weapon.damage_type == DamageType.POISON:
                resistance = defender_armor.poison_resistance

        final_damage = int(final_damage * (1.0 - resistance))

        # Apply special effects
        special_effects = []
        if hasattr(attacker_weapon, 'special_effects') and attacker_weapon.special_effects:
            for effect in attacker_weapon.special_effects:
                if effect == "burn" and attacker_weapon.damage_type == DamageType.FIRE:
                    special_effects.append({"type": "burn", "duration": 3, "damage_per_turn": 3})
                elif effect == "poison" and attacker_weapon.damage_type == DamageType.PHYSICAL:
                    special_effects.append({"type": "poison", "duration": 5, "damage_per_turn": 2})

        return {
            "damage": max(1, final_damage),
            "critical_hit": critical_hit,
            "dodged": False,
            "blocked": blocked,
            "damage_type": attacker_weapon.damage_type,
            "special_effects": special_effects
        }

    def process_attack(self, attacker, target, weapon=None):
        """Enhanced attack processing with durability management."""
        if not weapon:
            # Use default weapon stats from the unified Weapon class
            weapon = Weapon(
                name="Fists",
                damage=5,
                weapon_type=WeaponType.SWORD,
                damage_type=DamageType.PHYSICAL,
                durability=100,
                rarity=ItemRarity.COMMON
            )

        # Check weapon durability before attack
        if hasattr(weapon, 'get_durability_percentage'):
            durability_percent = weapon.get_durability_percentage()
            weapon_id = f"{attacker.name}_{weapon.name}"

            # Show durability warnings
            if durability_percent <= self.DURABILITY_CRITICAL_THRESHOLD * 100:
                if not self.durability_warnings.get(f"{weapon_id}_critical"):
                    print(f"CRITICAL: {weapon.name} is severely damaged! Repair immediately!")
                    self.durability_warnings[f"{weapon_id}_critical"] = True
            elif durability_percent <= self.DURABILITY_WARNING_THRESHOLD * 100:
                if not self.durability_warnings.get(f"{weapon_id}_warning"):
                    print(f"WARNING: {weapon.name} is getting worn ({durability_percent:.1f}% durability remaining)")
                    self.durability_warnings[f"{weapon_id}_warning"] = True

            # Reset warnings if weapon is repaired
            if durability_percent > self.DURABILITY_WARNING_THRESHOLD * 100:
                self.durability_warnings[f"{weapon_id}_warning"] = False
                self.durability_warnings[f"{weapon_id}_critical"] = False

        # Get combat stats
        attacker_stats = getattr(attacker, 'combat_stats', CombatStats())
        defender_stats = getattr(target, 'combat_stats', CombatStats())

        # Get armor
        defender_armor = getattr(target, 'equipped_armor', None)

        # Calculate damage
        damage_result = self.calculate_damage(weapon, attacker_stats, defender_armor, defender_stats)

        # Apply skill-based damage modifications
        damage_multiplier = 1.0

        # Check for attacker skill effects
        if hasattr(attacker, 'power_strike') and attacker.power_strike:
            damage_multiplier += 0.3

        if hasattr(attacker, 'berserker') and attacker.berserker:
            if attacker.stats.health < attacker.stats.max_health * 0.3:
                damage_multiplier += 1.0

        if hasattr(attacker, 'feral_rage') and attacker.feral_rage:
            if attacker.stats.health < attacker.stats.max_health * 0.5:
                damage_multiplier += 0.5

        # Apply damage multiplier
        base_damage = int(damage_result["damage"] * damage_multiplier)

        # Apply poison effect if attacker is venomous
        if hasattr(attacker, 'poison_damage') and hasattr(attacker, 'poison_duration'):
            if not hasattr(target, 'active_effects'):
                target.active_effects = {}
            target.active_effects['poison'] = {
                'damage': attacker.poison_damage,
                'duration': attacker.poison_duration,
                'remaining': attacker.poison_duration
            }
            print(f"{target.name} is poisoned!")

        # Apply damage
        if not damage_result["dodged"]:
            target.take_damage(base_damage)

            # Apply special effects
            for effect in damage_result["special_effects"]:
                self.apply_special_effect(target, effect)

            # Update combat stats
            attacker_stats.total_damage_dealt += base_damage
            defender_stats.total_damage_taken += base_damage

            if damage_result["critical_hit"]:
                attacker_stats.critical_hits += 1

            if damage_result["blocked"]:
                defender_stats.blocks += 1
        else:
            defender_stats.dodges += 1

        # Log combat event
        combat_event = {
            "timestamp": time.time(),
            "attacker": attacker,
            "defender": target,
            "weapon": weapon.name,
            "damage": base_damage,
            "critical_hit": damage_result["critical_hit"],
            "dodged": damage_result["dodged"],
            "blocked": damage_result["blocked"],
            "damage_type": damage_result["damage_type"].value,
            "special_effects": damage_result["special_effects"]
        }

        self.combat_log.append(combat_event)

        # Print combat message
        if damage_result["dodged"]:
            print(f"{target.name} dodged {attacker.name}'s attack!")
        elif damage_result["blocked"]:
            print(f"{target.name} blocked {attacker.name}'s attack for {base_damage} damage!")
        elif damage_result["critical_hit"]:
            print(f"{attacker.name} landed a critical hit on {target.name} for {base_damage} {damage_result['damage_type']} damage!")
        else:
            print(f"{attacker.name} hit {target.name} for {base_damage} {damage_result['damage_type']} damage!")

        # Use weapon (reduce durability) only if the attack wasn't dodged
        if not damage_result["dodged"] and hasattr(weapon, 'use'):
            if weapon.use():
                print(f"{attacker.name}'s {weapon.name} broke!")
                # Reset durability warnings for this weapon
                weapon_id = f"{attacker.name}_{weapon.name}"
                self.durability_warnings[f"{weapon_id}_warning"] = False
                self.durability_warnings[f"{weapon_id}_critical"] = False

        return damage_result

    def apply_special_effect(self, target, effect: Dict):
        """Apply a special effect to a target."""
        effect_type = effect["type"]
        duration = effect["duration"]
        damage_per_turn = effect.get("damage_per_turn", 0)

        if not hasattr(target, 'active_effects'):
            target.active_effects = {}

        target.active_effects[effect_type] = {
            "duration": duration,
            "damage_per_turn": damage_per_turn,
            "start_time": time.time()
        }

        print(f"{target.name} is affected by {effect_type} for {duration} turns!")

    def update_special_effects(self, entity):
        """Update special effects including skill-based effects."""
        if not hasattr(entity, 'active_effects'):
            return

        effects_to_remove = []

        for effect_name, effect_data in entity.active_effects.items():
            if effect_name == 'poison':
                # Apply poison damage
                entity.take_damage(effect_data['damage'])
                effect_data['remaining'] -= 1

                if effect_data['remaining'] <= 0:
                    effects_to_remove.append(effect_name)
                    print(f"{entity.name} is no longer poisoned.")

            elif effect_name == 'burn':
                # Apply burn damage
                entity.take_damage(effect_data['damage'])
                effect_data['remaining'] -= 1

                if effect_data['remaining'] <= 0:
                    effects_to_remove.append(effect_name)
                    print(f"{entity.name} is no longer burning.")

        # Remove expired effects
        for effect_name in effects_to_remove:
            del entity.active_effects[effect_name]

    def get_combat_summary(self, entity) -> Dict[str, Any]:
        """Get a summary of combat statistics for an entity."""
        if not hasattr(entity, 'combat_stats'):
            return {}

        stats = entity.combat_stats
        total_attacks = stats.critical_hits + stats.total_damage_dealt // 10  # Rough estimate

        return {
            "total_damage_dealt": stats.total_damage_dealt,
            "total_damage_taken": stats.total_damage_taken,
            "critical_hits": stats.critical_hits,
            "critical_hit_rate": stats.critical_hits / max(1, total_attacks),
            "dodges": stats.dodges,
            "blocks": stats.blocks,
            "dodge_rate": stats.dodges / max(1, total_attacks),
            "block_rate": stats.blocks / max(1, total_attacks)
        }
