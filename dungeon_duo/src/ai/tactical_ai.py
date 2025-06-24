"""
tactical_ai.py

Min-Max tactical AI system for Dungeon Duo: Rough AI.
Handles combat decision-making and action selection.
"""

import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time

class ActionType(Enum):
    """Types of actions the monster can take."""
    MOVE = "move"
    ATTACK = "attack"
    USE_ABILITY = "use_ability"
    RETREAT = "retreat"
    DEFEND = "defend"

@dataclass
class GameState:
    """Represents a game state for tactical analysis."""
    monster_pos: Tuple[float, float]
    monster_health: int
    monster_abilities: List[str]
    player_pos: Tuple[float, float]
    player_health: int
    player_state: str  # "attacking", "defending", "moving", etc.
    distance: float
    turn: int = 0

@dataclass
class Action:
    """Represents a possible action."""
    action_type: ActionType
    target_pos: Optional[Tuple[float, float]] = None
    ability_name: Optional[str] = None
    value: float = 0.0

class MinMaxTacticalAI:
    """Min-Max tactical AI with alpha-beta pruning."""

    def __init__(self, max_depth: int = 3):
        """Initialize the tactical AI."""
        self.max_depth = max_depth
        self.evaluation_cache: Dict[str, float] = {}
        self.nodes_evaluated = 0
        self.pruning_count = 0

        # Performance tracking
        self.decision_times: List[float] = []
        self.action_history: List[Action] = []

        # Tactical weights
        self.weights = {
            "health_advantage": 10.0,
            "position_advantage": 5.0,
            "ability_advantage": 3.0,
            "distance_control": 2.0,
            "action_efficiency": 1.0
        }

    def get_available_actions(self, state: GameState) -> List[Action]:
        """Get all available actions for the current state."""
        actions = []

        # Movement actions
        movement_range = 50.0  # Maximum movement distance
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx == 0 and dy == 0:
                    continue
                new_x = state.monster_pos[0] + dx * 20
                new_y = state.monster_pos[1] + dy * 20
                distance = math.sqrt(dx*dx + dy*dy) * 20
                if distance <= movement_range:
                    actions.append(Action(
                        action_type=ActionType.MOVE,
                        target_pos=(new_x, new_y)
                    ))

        # Attack action
        if state.distance <= 60:  # Attack range
            actions.append(Action(action_type=ActionType.ATTACK))

        # Ability actions
        for ability in state.monster_abilities:
            actions.append(Action(
                action_type=ActionType.USE_ABILITY,
                ability_name=ability
            ))

        # Defend action
        actions.append(Action(action_type=ActionType.DEFEND))

        # Retreat action (if health is low)
        if state.monster_health < 50:
            actions.append(Action(action_type=ActionType.RETREAT))

        return actions

    def evaluate_state(self, state: GameState) -> float:
        """Evaluate the current game state from monster's perspective."""
        # Create cache key
        cache_key = f"{state.monster_pos}_{state.monster_health}_{state.player_pos}_{state.player_health}_{state.distance}"

        if cache_key in self.evaluation_cache:
            return self.evaluation_cache[cache_key]

        score = 0.0

        # Health advantage (positive for monster advantage)
        health_diff = state.monster_health - state.player_health
        score += health_diff * self.weights["health_advantage"]

        # Position advantage
        position_score = self._evaluate_position_advantage(state)
        score += position_score * self.weights["position_advantage"]

        # Ability advantage
        ability_score = self._evaluate_ability_advantage(state)
        score += ability_score * self.weights["ability_advantage"]

        # Distance control
        distance_score = self._evaluate_distance_control(state)
        score += distance_score * self.weights["distance_control"]

        # Action efficiency (bonus for having more options)
        efficiency_score = len(self.get_available_actions(state))
        score += efficiency_score * self.weights["action_efficiency"]

        # Cache the result
        self.evaluation_cache[cache_key] = score
        self.nodes_evaluated += 1

        return score

    def _evaluate_position_advantage(self, state: GameState) -> float:
        """Evaluate positional advantage."""
        score = 0.0

        # Prefer positions that allow attack but maintain safety
        if state.distance <= 60:  # Can attack
            score += 10
        elif state.distance <= 100:  # Close enough to engage
            score += 5
        elif state.distance > 200:  # Too far, penalty
            score -= 10

        # Prefer positions with escape routes
        # This would be enhanced with actual pathfinding analysis
        score += 2

        return score

    def _evaluate_ability_advantage(self, state: GameState) -> float:
        """Evaluate ability advantage."""
        score = 0.0

        # Score based on available abilities
        for ability in state.monster_abilities:
            if ability == "heal" and state.monster_health < 70:
                score += 15
            elif ability == "charge_attack" and state.distance <= 80:
                score += 10
            elif ability == "defensive_stance" and state.player_state == "attacking":
                score += 8
            elif ability == "stealth" and state.distance > 100:
                score += 5

        return score

    def _evaluate_distance_control(self, state: GameState) -> float:
        """Evaluate distance control."""
        # Prefer optimal engagement distance
        optimal_distance = 50.0
        distance_diff = abs(state.distance - optimal_distance)

        if distance_diff < 20:
            return 10  # Optimal distance
        elif distance_diff < 50:
            return 5   # Good distance
        else:
            return -5  # Poor distance

    def minmax(self, state: GameState, depth: int, alpha: float, beta: float, is_maximizing: bool) -> Tuple[float, Optional[Action]]:
        """Min-Max algorithm with alpha-beta pruning."""
        # Terminal conditions
        if depth == 0 or state.monster_health <= 0 or state.player_health <= 0:
            return self.evaluate_state(state), None

        if is_maximizing:
            # Monster's turn (maximizing)
            best_value = float('-inf')
            best_action = None

            for action in self.get_available_actions(state):
                # Simulate action
                new_state = self._simulate_action(state, action, is_maximizing=True)
                value, _ = self.minmax(new_state, depth - 1, alpha, beta, False)

                if value > best_value:
                    best_value = value
                    best_action = action

                # Alpha-beta pruning
                alpha = max(alpha, best_value)
                if beta <= alpha:
                    self.pruning_count += 1
                    break

            return best_value, best_action
        else:
            # Player's turn (minimizing)
            best_value = float('inf')
            best_action = None

            for action in self.get_available_actions(state):
                # Simulate action
                new_state = self._simulate_action(state, action, is_maximizing=False)
                value, _ = self.minmax(new_state, depth - 1, alpha, beta, True)

                if value < best_value:
                    best_value = value
                    best_action = action

                # Alpha-beta pruning
                beta = min(beta, best_value)
                if beta <= alpha:
                    self.pruning_count += 1
                    break

            return best_value, best_action

    def _simulate_action(self, state: GameState, action: Action, is_maximizing: bool) -> GameState:
        """Simulate the result of an action."""
        new_state = GameState(
            monster_pos=state.monster_pos,
            monster_health=state.monster_health,
            monster_abilities=state.monster_abilities.copy(),
            player_pos=state.player_pos,
            player_health=state.player_health,
            player_state=state.player_state,
            distance=state.distance,
            turn=state.turn + 1
        )

        if is_maximizing:
            # Monster's action
            if action.action_type == ActionType.MOVE and action.target_pos:
                new_state.monster_pos = action.target_pos
                new_state.distance = math.sqrt(
                    (new_state.monster_pos[0] - new_state.player_pos[0])**2 +
                    (new_state.monster_pos[1] - new_state.player_pos[1])**2
                )

            elif action.action_type == ActionType.ATTACK:
                if new_state.distance <= 60:
                    damage = 15  # Base attack damage
                    new_state.player_health = max(0, new_state.player_health - damage)

            elif action.action_type == ActionType.USE_ABILITY:
                if action.ability_name == "heal":
                    new_state.monster_health = min(150, new_state.monster_health + 30)
                elif action.ability_name == "charge_attack":
                    if new_state.distance <= 80:
                        new_state.player_health = max(0, new_state.player_health - 25)
        else:
            # Player's action (simplified)
            if new_state.distance <= 60:
                damage = 10  # Player attack damage
                new_state.monster_health = max(0, new_state.monster_health - damage)

        return new_state

    def get_best_action(self, current_state: GameState) -> Action:
        """Get the best action for the current state."""
        start_time = time.time()

        # Run Min-Max search
        _, best_action = self.minmax(current_state, self.max_depth, float('-inf'), float('inf'), True)

        # Record decision time
        decision_time = time.time() - start_time
        self.decision_times.append(decision_time)
        if len(self.decision_times) > 100:
            self.decision_times.pop(0)

        # Record action
        if best_action:
            self.action_history.append(best_action)
            if len(self.action_history) > 1000:
                self.action_history.pop(0)

        return best_action or Action(action_type=ActionType.DEFEND)

    def get_performance_stats(self) -> dict:
        """Get tactical AI performance statistics."""
        return {
            "avg_decision_time": sum(self.decision_times) / len(self.decision_times) if self.decision_times else 0,
            "nodes_evaluated": self.nodes_evaluated,
            "pruning_count": self.pruning_count,
            "pruning_efficiency": self.pruning_count / (self.nodes_evaluated + self.pruning_count) if (self.nodes_evaluated + self.pruning_count) > 0 else 0,
            "cache_size": len(self.evaluation_cache),
            "total_decisions": len(self.decision_times)
        }

    def clear_cache(self):
        """Clear the evaluation cache."""
        self.evaluation_cache.clear()
        self.nodes_evaluated = 0
        self.pruning_count = 0
