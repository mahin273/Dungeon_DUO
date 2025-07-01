"""
combat_system.py

Handles combat mechanics and effects for Dungeon Duo.
"""

from .combat import Weapon, Armor, DamageType
import random

class CombatSystem:
    """Manages combat mechanics and effects."""

    def __init__(self):
        """Initialize the combat system."""
        self.active_effects = {}
        self.attack_cooldowns = {}

    def update(self, delta_time: float):
        """Update combat system state."""
        # Update active effects
        for entity in list(self.active_effects.keys()):
            effects_to_remove = []
            for effect in self.active_effects[entity]:
                effect.duration -= delta_time
                if effect.duration <= 0:
                    effects_to_remove.append(effect)
                else:
                    effect.apply(entity, delta_time)

            # Remove expired effects
            for effect in effects_to_remove:
                self.active_effects[entity].remove(effect)

        # Update cooldowns
        for entity in list(self.attack_cooldowns.keys()):
            if self.attack_cooldowns[entity] > 0:
                self.attack_cooldowns[entity] -= delta_time

    def process_attack(self, attacker, defender, weapon: Weapon = None):
        """Processes an attack from an attacker on a defender."""
        print(f"[DEBUG] process_attack called: attacker={getattr(attacker, 'name', attacker)}, defender={getattr(defender, 'name', defender)}, weapon={getattr(weapon, 'name', weapon) if weapon else None}")
        if not attacker or not defender:
            return

        # Determine damage and damage type
        if weapon:
            damage = weapon.get_damage()
            damage_type = weapon.damage_type.value
        else:
            # Unarmed attack
            damage = attacker.stats.attack if hasattr(attacker, 'stats') else 5
            damage_type = "physical"

        # Apply critical hit chance
        crit_chance = attacker.stats.crit_chance if hasattr(attacker, 'stats') else 0.05
        if random.random() < crit_chance:
            crit_multiplier = attacker.stats.crit_multiplier if hasattr(attacker, 'stats') else 1.5
            damage = int(damage * crit_multiplier)
            print(f"CRITICAL HIT! {attacker.name} strikes {defender.name} for {damage} {damage_type} damage.")
        else:
            print(f"{attacker.name} attacks {defender.name} for {damage} {damage_type} damage.")

        # Defender takes damage
        defender.take_damage(damage, damage_type=damage_type)

    def apply_special_effect(self, target, effect_type: str, duration: int, damage_per_turn: int = 0):
        """Applies a special effect to a target."""
        if not hasattr(target, 'active_effects'):
            target.active_effects = {}

        print(f"Applying {effect_type} to {target.name} for {duration} turns.")
        target.active_effects[effect_type] = {
            "duration": duration,
            "damage_per_turn": damage_per_turn
        }

    def update_special_effects(self, entity):
        """Updates special effects for a single entity."""
        if not hasattr(entity, 'active_effects') or not entity.active_effects:
            return

        expired_effects = []
        for effect, data in entity.active_effects.items():
            data["duration"] -= 1
            if data["damage_per_turn"] > 0:
                print(f"{entity.name} takes {data['damage_per_turn']} damage from {effect}.")
                entity.take_damage(data['damage_per_turn'], damage_type="environmental") # Effects bypass armor

            if data["duration"] <= 0:
                expired_effects.append(effect)

        for effect in expired_effects:
            print(f"{effect} has worn off for {entity.name}.")
            del entity.active_effects[effect]

    def create_weapon(self, weapon_id: str) -> Weapon:
        """Creates a weapon from an ID."""
        if weapon_id == "iron_sword":
            return Weapon(name="Iron Sword", damage=10, weapon_type="sword", damage_type=DamageType.PHYSICAL)
        elif weapon_id == "fire_staff":
            return Weapon(name="Fire Staff", damage=15, weapon_type="staff", damage_type=DamageType.FIRE)
        return None

    def create_armor(self, armor_id: str) -> Armor:
        """Creates an armor from an ID."""
        if armor_id == "leather_armor":
            return Armor(name="Leather Armor", armor_type="light", physical_defense=5, magical_defense=2)
        elif armor_id == "iron_armor":
            return Armor(name="Iron Armor", armor_type="heavy", physical_defense=10, magical_defense=5)
        return None
