"""
optimization.py

Simulated Annealing optimization system for Dungeon Duo: Rough AI.
Optimizes monster abilities, stats, and dungeon elements.
"""

import random
import math
import time
from typing import Dict, List, Tuple, Any, Callable, Optional
from dataclasses import dataclass
import copy

@dataclass
class MonsterLoadout:
    """Monster ability and stat configuration."""
    attack_power: int
    defense: int
    speed: float
    health: int
    abilities: List[str]
    aggression_level: float  # 0.0 to 1.0
    tactical_preference: str  # "aggressive", "defensive", "ambush", "hit_and_run"

class SimulatedAnnealingOptimizer:
    """Simulated Annealing optimizer for monster adaptation."""

    def __init__(self, initial_temp: float = 100.0, cooling_rate: float = 0.95):
        """Initialize the optimizer."""
        self.initial_temp = initial_temp
        self.current_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.min_temp = 0.1

        # Optimization history
        self.best_solution = None
        self.best_score = float('-inf')
        self.optimization_history: List[Tuple[float, float]] = []  # (temperature, score)

        # Performance tracking
        self.iterations = 0
        self.accepted_moves = 0
        self.rejected_moves = 0

        # Available abilities for optimization
        self.available_abilities = [
            "charge_attack", "ranged_attack", "defensive_stance",
            "heal", "speed_boost", "damage_boost", "stealth"
        ]

    def evaluate_loadout(self, loadout: MonsterLoadout, player_data: dict) -> float:
        """Evaluate the fitness of a monster loadout against player data."""
        score = 0.0

        # Analyze player weaknesses and strengths
        player_health = player_data.get("health", 100)
        player_defense = player_data.get("defense", 5)
        player_speed = player_data.get("speed", 5.0)
        player_aggression = player_data.get("playstyle", {}).get("aggression", 0.5)

        # Score based on countering player strengths
        if player_defense > 10:
            # Player has high defense, prioritize high attack power
            score += loadout.attack_power * 2
        else:
            score += loadout.attack_power

        if player_speed > 6.0:
            # Player is fast, need speed to keep up
            score += loadout.speed * 3
        else:
            score += loadout.speed

        # Score based on player health
        if player_health < 50:
            # Player is weak, aggressive approach
            if loadout.aggression_level > 0.7:
                score += 50
        else:
            # Player is healthy, defensive approach
            if loadout.aggression_level < 0.3:
                score += 30

        # Score based on tactical preference vs player playstyle
        if player_aggression > 0.7 and loadout.tactical_preference == "defensive":
            score += 40  # Good counter
        elif player_aggression < 0.3 and loadout.tactical_preference == "aggressive":
            score += 40  # Good counter

        # Score based on ability synergy
        ability_score = self._evaluate_ability_synergy(loadout.abilities)
        score += ability_score

        # Balance score (avoid extreme values)
        balance_penalty = self._calculate_balance_penalty(loadout)
        score -= balance_penalty

        return score

    def _evaluate_ability_synergy(self, abilities: List[str]) -> float:
        """Evaluate how well abilities work together."""
        score = 0.0

        # Check for complementary abilities
        if "charge_attack" in abilities and "speed_boost" in abilities:
            score += 20  # Good synergy

        if "defensive_stance" in abilities and "heal" in abilities:
            score += 15  # Good synergy

        if "stealth" in abilities and "ambush" in abilities:
            score += 25  # Good synergy

        # Penalty for too many abilities (dilution)
        if len(abilities) > 4:
            score -= (len(abilities) - 4) * 10

        return score

    def _calculate_balance_penalty(self, loadout: MonsterLoadout) -> float:
        """Calculate penalty for unbalanced stats."""
        penalty = 0.0

        # Check for extreme values
        if loadout.attack_power > 30:
            penalty += (loadout.attack_power - 30) * 2

        if loadout.defense > 20:
            penalty += (loadout.defense - 20) * 2

        if loadout.speed > 8.0:
            penalty += (loadout.speed - 8.0) * 5

        if loadout.health > 200:
            penalty += (loadout.health - 200) * 0.5

        return penalty

    def generate_neighbor(self, current_loadout: MonsterLoadout) -> MonsterLoadout:
        """Generate a neighboring solution by making small changes."""
        neighbor = copy.deepcopy(current_loadout)

        # Randomly choose what to modify
        modification = random.choice([
            "attack_power", "defense", "speed", "health",
            "abilities", "aggression", "tactical"
        ])

        if modification == "attack_power":
            neighbor.attack_power += random.randint(-3, 3)
            neighbor.attack_power = max(5, min(40, neighbor.attack_power))

        elif modification == "defense":
            neighbor.defense += random.randint(-2, 2)
            neighbor.defense = max(3, min(25, neighbor.defense))

        elif modification == "speed":
            neighbor.speed += random.uniform(-0.5, 0.5)
            neighbor.speed = max(2.0, min(10.0, neighbor.speed))

        elif modification == "health":
            neighbor.health += random.randint(-20, 20)
            neighbor.health = max(100, min(300, neighbor.health))

        elif modification == "abilities":
            if random.random() < 0.5 and len(neighbor.abilities) < 5:
                # Add ability
                new_ability = random.choice(self.available_abilities)
                if new_ability not in neighbor.abilities:
                    neighbor.abilities.append(new_ability)
            elif neighbor.abilities:
                # Remove ability
                neighbor.abilities.pop(random.randrange(len(neighbor.abilities)))

        elif modification == "aggression":
            neighbor.aggression_level += random.uniform(-0.1, 0.1)
            neighbor.aggression_level = max(0.0, min(1.0, neighbor.aggression_level))

        elif modification == "tactical":
            tactical_options = ["aggressive", "defensive", "ambush", "hit_and_run"]
            neighbor.tactical_preference = random.choice(tactical_options)

        return neighbor

    def optimize(self, initial_loadout: MonsterLoadout,
                player_data: dict,
                max_iterations: int = 1000) -> MonsterLoadout:
        """Run simulated annealing optimization."""
        self.current_temp = self.initial_temp
        current_loadout = copy.deepcopy(initial_loadout)
        current_score = self.evaluate_loadout(current_loadout, player_data)

        self.best_solution = copy.deepcopy(current_loadout)
        self.best_score = current_score

        for iteration in range(max_iterations):
            # Generate neighbor
            neighbor_loadout = self.generate_neighbor(current_loadout)
            neighbor_score = self.evaluate_loadout(neighbor_loadout, player_data)

            # Calculate score difference
            score_diff = neighbor_score - current_score

            # Accept or reject based on temperature and score
            if score_diff > 0 or random.random() < math.exp(score_diff / self.current_temp):
                # Accept move
                current_loadout = neighbor_loadout
                current_score = neighbor_score
                self.accepted_moves += 1

                # Update best solution
                if current_score > self.best_score:
                    self.best_solution = copy.deepcopy(current_loadout)
                    self.best_score = current_score
            else:
                self.rejected_moves += 1

            # Record optimization progress
            self.optimization_history.append((self.current_temp, current_score))

            # Cool down
            self.current_temp *= self.cooling_rate
            if self.current_temp < self.min_temp:
                break

            self.iterations += 1

        return self.best_solution

    def optimize_dungeon_elements(self, dungeon_layout: dict, player_data: dict) -> dict:
        """Optimize dungeon trap and item placement."""
        # This would optimize trap placement, item locations, etc.
        # For now, return the original layout
        return dungeon_layout

    def get_optimization_stats(self) -> dict:
        """Get optimization performance statistics."""
        return {
            "iterations": self.iterations,
            "accepted_moves": self.accepted_moves,
            "rejected_moves": self.rejected_moves,
            "acceptance_rate": self.accepted_moves / (self.accepted_moves + self.rejected_moves) if (self.accepted_moves + self.rejected_moves) > 0 else 0,
            "best_score": self.best_score,
            "final_temperature": self.current_temp,
            "optimization_history_length": len(self.optimization_history)
        }

    def reset(self):
        """Reset the optimizer for a new optimization run."""
        self.current_temp = self.initial_temp
        self.best_solution = None
        self.best_score = float('-inf')
        self.optimization_history.clear()
        self.iterations = 0
        self.accepted_moves = 0
        self.rejected_moves = 0
