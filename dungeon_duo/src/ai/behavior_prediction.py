"""
behavior_prediction.py

Naive Bayes behavior prediction system for Dungeon Duo: Rough AI.
Classifies and predicts player actions for adaptive AI.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
import time
import math

@dataclass
class PlayerAction:
    """Player action data structure."""
    action_type: str
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    health: int
    timestamp: float
    context: Dict[str, Any]  # Additional context (nearby enemies, items, etc.)

class NaiveBayesPredictor:
    """Naive Bayes classifier for predicting player behavior."""

    def __init__(self):
        """Initialize the behavior predictor."""
        # Training data
        self.action_counts: Dict[str, int] = defaultdict(int)
        self.feature_counts: Dict[str, Dict[str, Dict[Any, int]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        self.total_actions = 0

        # Feature categories
        self.feature_categories = {
            "health_level": ["low", "medium", "high"],
            "movement_speed": ["stationary", "slow", "fast"],
            "distance_to_monster": ["close", "medium", "far"],
            "monster_health": ["low", "medium", "high"],
            "recent_damage": ["none", "low", "high"],
            "position_quadrant": ["top_left", "top_right", "bottom_left", "bottom_right"]
        }

        # Prediction confidence tracking
        self.prediction_accuracy: List[float] = []
        self.confidence_scores: List[float] = []

        # Learning parameters
        self.learning_rate = 0.1
        self.min_confidence = 0.3

    def categorize_health(self, health: int, max_health: int = 100) -> str:
        """Categorize health level."""
        percentage = health / max_health
        if percentage <= 0.3:
            return "low"
        elif percentage <= 0.7:
            return "medium"
        else:
            return "high"

    def categorize_movement_speed(self, velocity: Tuple[float, float]) -> str:
        """Categorize movement speed."""
        speed = math.sqrt(velocity[0]**2 + velocity[1]**2)
        if speed < 0.1:
            return "stationary"
        elif speed < 3.0:
            return "slow"
        else:
            return "fast"

    def categorize_distance(self, distance: float) -> str:
        """Categorize distance to monster."""
        if distance < 100:
            return "close"
        elif distance < 300:
            return "medium"
        else:
            return "far"

    def categorize_position(self, position: Tuple[float, float], world_bounds: Tuple[float, float]) -> str:
        """Categorize position quadrant."""
        x, y = position
        world_width, world_height = world_bounds

        if x < world_width / 2:
            if y < world_height / 2:
                return "top_left"
            else:
                return "bottom_left"
        else:
            if y < world_height / 2:
                return "top_right"
            else:
                return "bottom_right"

    def extract_features(self, player_state: dict, monster_state: dict, world_bounds: Tuple[float, float]) -> Dict[str, str]:
        """Extract categorical features from player and monster state."""
        features = {}

        # Health level
        features["health_level"] = self.categorize_health(
            player_state.get("health", 100),
            player_state.get("max_health", 100)
        )

        # Movement speed
        velocity = player_state.get("velocity", (0, 0))
        features["movement_speed"] = self.categorize_movement_speed(velocity)

        # Distance to monster
        player_pos = player_state.get("position", (0, 0))
        monster_pos = monster_state.get("position", (0, 0))
        distance = math.sqrt((player_pos[0] - monster_pos[0])**2 + (player_pos[1] - monster_pos[1])**2)
        features["distance_to_monster"] = self.categorize_distance(distance)

        # Monster health
        features["monster_health"] = self.categorize_health(
            monster_state.get("health", 100),
            monster_state.get("max_health", 100)
        )

        # Recent damage (from combat stats)
        recent_damage = player_state.get("combat_stats", {}).get("damage_taken", 0)
        if recent_damage == 0:
            features["recent_damage"] = "none"
        elif recent_damage < 20:
            features["recent_damage"] = "low"
        else:
            features["recent_damage"] = "high"

        # Position quadrant
        features["position_quadrant"] = self.categorize_position(player_pos, world_bounds)

        return features

    def train(self, action: PlayerAction, features: Dict[str, str]):
        """Train the model with a new action and its features."""
        self.total_actions += 1
        self.action_counts[action.action_type] += 1

        # Update feature counts for this action
        for feature_name, feature_value in features.items():
            self.feature_counts[action.action_type][feature_name][feature_value] += 1

    def predict_action(self, features: Dict[str, str]) -> Tuple[str, float]:
        """Predict the most likely action given current features."""
        if self.total_actions == 0:
            return "unknown", 0.0

        action_scores = {}

        for action_type in self.action_counts:
            # Prior probability P(action)
            prior = self.action_counts[action_type] / self.total_actions

            # Likelihood P(features|action)
            likelihood = 1.0
            for feature_name, feature_value in features.items():
                if action_type in self.feature_counts and feature_name in self.feature_counts[action_type]:
                    feature_count = self.feature_counts[action_type][feature_name].get(feature_value, 0)
                    total_count = self.action_counts[action_type]

                    # Add smoothing to avoid zero probabilities
                    smoothed_prob = (feature_count + 1) / (total_count + len(self.feature_categories.get(feature_name, [])))
                    likelihood *= smoothed_prob
                else:
                    # If we haven't seen this feature for this action, use uniform probability
                    likelihood *= 1.0 / len(self.feature_categories.get(feature_name, []))

            # Posterior probability P(action|features) = P(features|action) * P(action)
            action_scores[action_type] = likelihood * prior

        if not action_scores:
            return "unknown", 0.0

        # Find action with highest probability
        best_action = max(action_scores, key=action_scores.get)
        confidence = action_scores[best_action]

        # Normalize confidence
        total_score = sum(action_scores.values())
        if total_score > 0:
            confidence /= total_score

        return best_action, confidence

    def predict_next_position(self, current_features: Dict[str, str],
                            current_position: Tuple[float, float],
                            time_horizon: float = 1.0) -> Tuple[Tuple[float, float], float]:
        """Predict player's next position based on behavior patterns."""
        predicted_action, confidence = self.predict_action(current_features)

        # Simple position prediction based on action type
        if predicted_action == "move":
            # Predict movement in the direction of current velocity
            # This would be enhanced with more sophisticated movement modeling
            return current_position, confidence
        elif predicted_action == "retreat":
            # Predict movement away from monster
            return current_position, confidence
        else:
            return current_position, confidence

    def update_accuracy(self, predicted_action: str, actual_action: str, confidence: float):
        """Update prediction accuracy tracking."""
        accuracy = 1.0 if predicted_action == actual_action else 0.0
        self.prediction_accuracy.append(accuracy)
        self.confidence_scores.append(confidence)

        # Keep only recent predictions
        if len(self.prediction_accuracy) > 1000:
            self.prediction_accuracy.pop(0)
            self.confidence_scores.pop(0)

    def get_playstyle_profile(self) -> Dict[str, float]:
        """Analyze player's playstyle based on action patterns."""
        if self.total_actions == 0:
            return {}

        profile = {}

        # Aggression level (attack frequency)
        attack_count = self.action_counts.get("attack", 0)
        profile["aggression"] = attack_count / self.total_actions

        # Mobility level (movement frequency)
        move_count = self.action_counts.get("move", 0)
        profile["mobility"] = move_count / self.total_actions

        # Defensive level (dodge frequency)
        dodge_count = self.action_counts.get("dodge", 0)
        profile["defensive"] = dodge_count / self.total_actions

        # Predictability (entropy of action distribution)
        action_probs = [count / self.total_actions for count in self.action_counts.values()]
        entropy = -sum(p * math.log2(p) for p in action_probs if p > 0)
        profile["predictability"] = 1.0 - (entropy / math.log2(len(self.action_counts)))

        return profile

    def get_performance_stats(self) -> dict:
        """Get prediction performance statistics."""
        if not self.prediction_accuracy:
            return {}

        return {
            "accuracy": sum(self.prediction_accuracy) / len(self.prediction_accuracy),
            "avg_confidence": sum(self.confidence_scores) / len(self.confidence_scores),
            "total_predictions": len(self.prediction_accuracy),
            "action_distribution": dict(self.action_counts),
            "playstyle_profile": self.get_playstyle_profile()
        }
