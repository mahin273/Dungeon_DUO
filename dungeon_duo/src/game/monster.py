"""
monster.py

Enhanced AI Monster class for Dungeon Duo: Rough AI.
Integrates pathfinding, behavior prediction, optimization, tactical AI systems, and enhanced combat.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import time
import math
import random

# Import AI systems
from ..ai.pathfinding import AStarPathfinder
from ..ai.behavior_prediction import NaiveBayesPredictor, PlayerAction
from ..ai.optimization import SimulatedAnnealingOptimizer, MonsterLoadout
from ..ai.tactical_ai import MinMaxTacticalAI, GameState as TacticalGameState, ActionType

# Import combat system
from .combat import CombatStats, Weapon, Armor, WeaponType, DamageType

# Import skill tree system
from .skills import SkillTree, get_default_monster_skills

# Import weapon system
from .items.weapon import Weapon, WeaponType

@dataclass
class MonsterStats:
    """Monster statistics and attributes."""
    health: int = 100
    max_health: int = 100
    speed: float = 4.0
    attack_power: int = 15
    defense: int = 8
    sight_range: float = 200.0
    attack_range: float = 50.0
    # AI-specific stats
    learning_rate: float = 0.1
    adaptation_threshold: int = 10
    tactical_memory: int = 50

class Monster:
    """Enhanced adaptive AI monster class with integrated AI systems and combat."""

    def __init__(self, x: float, y: float, dungeon_map=None):
        """Initialize the monster with position and AI systems."""
        # Position and movement
        self.x = x
        self.y = y
        self.velocity_x = 0
        self.velocity_y = 0
        self.name = "Monster"

        # Stats and state
        self.stats = MonsterStats()

        # Enhanced combat system integration
        self.combat_stats = CombatStats()
        self.equipped_weapon: Optional[Weapon] = None
        self.equipped_armor: Optional[Armor] = None
        self.weapon_inventory: List[Weapon] = []
        self.armor_inventory: List[Armor] = []

        # Combat state
        self.is_attacking = False
        self.target: Optional[Tuple[float, float]] = None
        self.current_path: List[Tuple[float, float]] = []
        self.dungeon_map = dungeon_map
        self.last_attack_time = 0
        self.attack_cooldown = 1.0

        # AI Systems
        self.pathfinder = None  # Will be initialized when dungeon map is set
        self.behavior_predictor = NaiveBayesPredictor()
        self.optimizer = SimulatedAnnealingOptimizer()
        self.tactical_ai = MinMaxTacticalAI()

        # AI learning state
        self.observed_player_actions: List[dict] = []
        self.combat_history: List[dict] = []
        self.adaptation_level = 0  # Increases as monster learns
        self.last_adaptation_time = time.time()
        self.adaptation_cooldown = 30.0  # Increased from 5.0 to 30.0 seconds between adaptations

        # Performance tracking
        self.decision_times: List[float] = []
        self.success_rate: Dict[str, float] = {
            "attacks": 0.0,
            "predictions": 0.0,
            "pathfinding": 0.0,
            "tactical_decisions": 0.0
        }

        # AI state tracking
        self.current_strategy = "patrol"
        self.last_player_position = None
        self.patrol_points = []
        self.current_patrol_index = 0

        # Combat state
        self.is_in_combat = False
        self.combat_start_time = 0

        # Active effects
        self.active_effects = {}

        # Skill tree system
        self.skill_tree = SkillTree()
        for skill in get_default_monster_skills():
            self.skill_tree.add_skill(skill)
        self.skill_tree.skill_points = 0

    def update(self, delta_time: float, player_state: dict = None):
        """Update monster behavior based on player state and AI learning."""
        start_time = time.time()

        # Update special effects
        self._update_special_effects()

        # Process player state for learning
        if player_state:
            self._observe_player(player_state)

        # Update AI systems
        self._update_ai_systems()

        # Make tactical decisions
        self._make_tactical_decisions(player_state)

        # Update movement and behavior
        self._update_movement(delta_time)

        # Check for adaptation opportunities
        self._check_adaptation()

        # Update attack cooldown
        if self.is_attacking:
            current_time = time.time()
            if current_time - self.last_attack_time >= self.attack_cooldown:
                self.is_attacking = False

        # Apply skill-based behavior modifications
        self._apply_skill_behavior_modifications(player_state, delta_time)

        # Record decision time
        decision_time = time.time() - start_time
        self.decision_times.append(decision_time)
        if len(self.decision_times) > 100:
            self.decision_times.pop(0)

        # Debug: Print monster state every 300 frames (5 seconds at 60 FPS)
        if not hasattr(self, '_debug_frame_count'):
            self._debug_frame_count = 0
        self._debug_frame_count += 1

        if self._debug_frame_count % 300 == 0 and player_state:
            player_pos = player_state.get('position', (0, 0))
            distance = self._distance_to(player_pos)
            can_see = distance <= self.stats.sight_range
            print(f"Monster Decision - Distance: {distance:.1f}, Attack range: {self.stats.attack_range}, Sight range: {self.stats.sight_range}")
            print(f"Monster Decision - Current strategy: {self.current_strategy}")

    def _observe_player(self, player_state: dict):
        """Process and learn from player state."""
        current_time = time.time()

        # Update last known player position
        if 'position' in player_state:
            self.last_player_position = player_state['position']

        # Record observation
        observation = {
            "state": player_state,
            "timestamp": current_time,
            "monster_position": (self.x, self.y),
            "distance_to_player": self._distance_to(self.last_player_position) if self.last_player_position else float('inf')
        }

        self.observed_player_actions.append(observation)

        # Keep observation history manageable
        if len(self.observed_player_actions) > 1000:
            self.observed_player_actions.pop(0)

    def _update_ai_systems(self):
        """Update all AI systems with new data."""
        # Update behavior prediction
        if len(self.observed_player_actions) >= 5:
            # Create PlayerAction objects for training
            for action_data in self.observed_player_actions[-5:]:
                player_state = action_data['state']
                action = PlayerAction(
                    action_type=player_state.get('last_action', 'move'),
                    position=player_state.get('position', (0, 0)),
                    velocity=player_state.get('velocity', (0, 0)),
                    health=player_state.get('health', 100),
                    timestamp=action_data['timestamp'],
                    context={'distance_to_monster': action_data['distance_to_player']}
                )

                # Extract features and train
                features = self._extract_player_features(player_state)
                self.behavior_predictor.train(action, features)

    def _extract_player_features(self, player_state: dict) -> Dict[str, str]:
        """Extract features from player state for behavior prediction."""
        features = {}

        # Health level
        health = player_state.get('health', 100)
        if health <= 30:
            features['health_level'] = 'low'
        elif health <= 70:
            features['health_level'] = 'medium'
        else:
            features['health_level'] = 'high'

        # Movement speed
        velocity = player_state.get('velocity', (0, 0))
        speed = math.sqrt(velocity[0]**2 + velocity[1]**2)
        if speed < 0.1:
            features['movement_speed'] = 'stationary'
        elif speed < 3.0:
            features['movement_speed'] = 'slow'
        else:
            features['movement_speed'] = 'fast'

        # Distance to monster
        if self.last_player_position:
            distance = self._distance_to(self.last_player_position)
            if distance < 100:
                features['distance_to_monster'] = 'close'
            elif distance < 300:
                features['distance_to_monster'] = 'medium'
            else:
                features['distance_to_monster'] = 'far'
        else:
            features['distance_to_monster'] = 'far'

        # Monster health
        if self.stats.health <= 50:
            features['monster_health'] = 'low'
        elif self.stats.health <= 100:
            features['monster_health'] = 'medium'
        else:
            features['monster_health'] = 'high'

        # Recent damage
        recent_damage = player_state.get('combat_stats', {}).get('damage_taken', 0)
        if recent_damage == 0:
            features['recent_damage'] = 'none'
        elif recent_damage < 20:
            features['recent_damage'] = 'low'
        else:
            features['recent_damage'] = 'high'

        # Position quadrant (simplified)
        features['position_quadrant'] = 'top_left'  # Default, could be enhanced

        return features

    def _make_tactical_decisions(self, player_state: dict):
        """Make tactical decisions using the tactical AI system."""
        if not player_state or not self.last_player_position:
            return

        # Calculate distance to player
        distance_to_player = self._distance_to(self.last_player_position)

        # Debug: Print decision making
        if not hasattr(self, '_debug_decision_count'):
            self._debug_decision_count = 0
        self._debug_decision_count += 1

        if self._debug_decision_count % 60 == 0:
            print(f"Monster Decision - Distance: {distance_to_player:.1f}, Attack range: {self.stats.attack_range}, Sight range: {self.stats.sight_range}")
            print(f"Monster Decision - Current strategy: {self.current_strategy}")

        # Determine current situation
        if distance_to_player <= self.stats.attack_range:
            self.is_in_combat = True
            self.current_strategy = "combat"
            if not self.combat_start_time:
                self.combat_start_time = time.time()

            # Make combat decision
            self._make_combat_decision(player_state)

        elif distance_to_player <= self.stats.sight_range:
            # Player is visible but not in attack range
            self.is_in_combat = False
            self.combat_start_time = 0
            self.current_strategy = "chase"
            self._make_chase_decision(player_state)

        else:
            # Player not visible
            self.is_in_combat = False
            self.combat_start_time = 0
            self.current_strategy = "patrol"
            self._make_patrol_decision()

    def _make_combat_decision(self, player_state: dict):
        """Make decisions during combat."""
        current_time = time.time()

        # Debug: Print combat decision
        if not hasattr(self, '_debug_combat_count'):
            self._debug_combat_count = 0
        self._debug_combat_count += 1

        if self._debug_combat_count % 60 == 0:
            print(f"Monster Combat - Can attack: {current_time - self.last_attack_time >= self.attack_cooldown}")
            print(f"Monster Combat - Distance to player: {self._distance_to(self.last_player_position):.1f}")

        # Check if we can attack
        if current_time - self.last_attack_time >= self.attack_cooldown:
            # Create game state for tactical AI
            game_state = TacticalGameState(
                monster_pos=(self.x, self.y),
                monster_health=self.stats.health,
                monster_abilities=['basic_attack', 'dodge', 'retreat'],
                player_pos=self.last_player_position,
                player_health=player_state.get('health', 100),
                player_state='attacking' if player_state.get('is_attacking', False) else 'moving',
                distance=self._distance_to(self.last_player_position)
            )

            # Get best action from tactical AI
            best_action = self.tactical_ai.get_best_action(game_state)

            if self._debug_combat_count % 60 == 0:
                print(f"Monster Combat - Best action: {best_action}")

            if best_action:
                if best_action.action_type == ActionType.ATTACK:
                    self.attack(self.last_player_position)
                    self.last_attack_time = current_time
                    if self._debug_combat_count % 60 == 0:
                        print(f"Monster Combat - Attacking player!")
                elif best_action.action_type == ActionType.RETREAT:
                    # Find retreat position
                    retreat_pos = self._find_retreat_position()
                    if retreat_pos:
                        self.set_target(retreat_pos[0], retreat_pos[1])
                        if self._debug_combat_count % 60 == 0:
                            print(f"Monster Combat - Retreating to {retreat_pos}")
                elif best_action.action_type == ActionType.MOVE and best_action.target_pos:
                    # Move to tactical position
                    self.set_target(best_action.target_pos[0], best_action.target_pos[1])
                    if self._debug_combat_count % 60 == 0:
                        print(f"Monster Combat - Moving to tactical position {best_action.target_pos}")
                elif best_action.action_type == ActionType.DEFEND:
                    # Implement defensive stance
                    self._perform_dodge()
                    if self._debug_combat_count % 60 == 0:
                        print(f"Monster Combat - Dodging!")
            else:
                # Fallback: attack directly if no tactical decision
                self.attack(self.last_player_position)
                self.last_attack_time = current_time
                if self._debug_combat_count % 60 == 0:
                    print(f"Monster Combat - Fallback attack!")
        else:
            # If attack is on cooldown, move towards the player
            self._make_chase_decision(player_state)

    def _make_chase_decision(self, player_state: dict):
        """Make chase decision using pathfinding."""
        if not player_state or 'position' not in player_state:
            return

        player_pos = player_state['position']
        distance = self._distance_to(player_pos)

        # Set target to player position
        self.set_target(player_pos[0], player_pos[1])

        # Use pathfinding to find path to player
        if self.pathfinder:
            path = self.pathfinder.find_path((self.x, self.y), player_pos)

            if path and len(path) > 1:
                self.current_path = path
                print(f"Monster Chase - Path found with {len(path)} waypoints")
            else:
                print(f"Monster Chase - No pathfinding, direct target: {player_pos}")
                self.current_path = []
                # Fallback: try to move directly towards player with collision detection
                self._fallback_movement_towards_player(player_pos)

        # Update strategy
        self.current_strategy = "chase"

    def _fallback_movement_towards_player(self, player_pos: Tuple[float, float]):
        """Fallback movement when pathfinding fails."""
        if not self.dungeon_map:
            return

        # Calculate direction to player
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance > 0:
            # Normalize direction
            dx = dx / distance
            dy = dy / distance

            # Try to move in the direction of the player
            new_x = self.x + dx * self.stats.speed * 0.016  # Assuming 60 FPS
            new_y = self.y + dy * self.stats.speed * 0.016

            # Check if new position is valid
            if self._is_valid_position(new_x, new_y):
                self.x = new_x
                self.y = new_y
                self.velocity_x = dx * self.stats.speed
                self.velocity_y = dy * self.stats.speed
            else:
                # Try alternative directions (perpendicular)
                alt_dx = -dy
                alt_dy = dx
                new_x = self.x + alt_dx * self.stats.speed * 0.016
                new_y = self.y + alt_dy * self.stats.speed * 0.016

                if self._is_valid_position(new_x, new_y):
                    self.x = new_x
                    self.y = new_y
                    self.velocity_x = alt_dx * self.stats.speed
                    self.velocity_y = alt_dy * self.stats.speed
                else:
                    # Try opposite direction
                    new_x = self.x - alt_dx * self.stats.speed * 0.016
                    new_y = self.y - alt_dy * self.stats.speed * 0.016

                    if self._is_valid_position(new_x, new_y):
                        self.x = new_x
                        self.y = new_y
                        self.velocity_x = -alt_dx * self.stats.speed
                        self.velocity_y = -alt_dy * self.stats.speed
                    else:
                        # Stop moving if all directions are blocked
                        self.velocity_x = 0
                        self.velocity_y = 0

    def _make_patrol_decision(self):
        """Make decisions when patrolling."""
        if not self.patrol_points:
            self._generate_patrol_points()

        if self.patrol_points:
            # Move to next patrol point
            target_point = self.patrol_points[self.current_patrol_index]
            self.set_target(target_point[0], target_point[1])

            # Check if reached patrol point
            if self._distance_to(target_point) < 10:
                self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)

    def _generate_patrol_points(self):
        """Generate patrol points around the monster's current area."""
        if not self.dungeon_map:
            return

        self.patrol_points = []
        center_x, center_y = int(self.x), int(self.y)
        patrol_radius = 50

        for i in range(4):
            angle = (i * 90) * (math.pi / 180)
            px = center_x + int(patrol_radius * math.cos(angle))
            py = center_y + int(patrol_radius * math.sin(angle))

            # Check if position is valid
            ix, iy = int(px), int(py)
            if (0 <= ix < len(self.dungeon_map[0]) and
                0 <= iy < len(self.dungeon_map) and
                self.dungeon_map[iy][ix].walkable):
                self.patrol_points.append((px, py))

        if not self.patrol_points:
            # Fallback to current position
            self.patrol_points = [(self.x, self.y)]

    def _find_retreat_position(self) -> Optional[Tuple[float, float]]:
        """Find a safe retreat position."""
        if not self.dungeon_map or not self.last_player_position:
            return None

        # Find position away from player
        player_x, player_y = self.last_player_position
        retreat_distance = 100

        for angle in range(0, 360, 45):
            rad_angle = angle * (math.pi / 180)
            px = self.x + int(retreat_distance * math.cos(rad_angle))
            py = self.y + int(retreat_distance * math.sin(rad_angle))

            # Check if position is valid
            ix, iy = int(px), int(py)
            if (0 <= ix < len(self.dungeon_map[0]) and
                0 <= iy < len(self.dungeon_map) and
                self.dungeon_map[iy][ix].walkable):
                return (px, py)

        return None

    def _perform_dodge(self):
        """Perform a dodge movement."""
        # Simple dodge: move perpendicular to player direction
        if self.last_player_position:
            dx = self.x - self.last_player_position[0]
            dy = self.y - self.last_player_position[1]

            # Normalize and rotate 90 degrees
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                dodge_x = -dy / length * 10
                dodge_y = dx / length * 10

                new_x = self.x + dodge_x
                new_y = self.y + dodge_y
                ix, iy = int(new_x), int(new_y)
                # Check if dodge position is valid
                if (self.dungeon_map and
                    0 <= ix < len(self.dungeon_map[0]) and
                    0 <= iy < len(self.dungeon_map) and
                    self.dungeon_map[iy][ix].walkable):
                    self.set_target(new_x, new_y)

    def _update_movement(self, delta_time: float):
        """Update monster movement based on current strategy and pathfinding."""
        if not self.target:
            return

        # Calculate distance to target
        target_distance = self._distance_to(self.target)

        # If we're close enough to target, move to next waypoint or stop if at final destination
        if target_distance < 1.0:
            if self.current_path and len(self.current_path) > 2:
                # Remove the current waypoint and move to the next one
                self.current_path.pop(0)  # Remove current waypoint
                next_waypoint = self.current_path[1]  # Get next waypoint
                self.target = next_waypoint
            else:
                # Reached final destination, stop moving
                self.velocity_x = 0
                self.velocity_y = 0
                return

        # Use pathfinding if available
        if self.pathfinder and self.current_path:
            if len(self.current_path) > 1:
                next_waypoint = self.current_path[1]  # Skip current position
                dx = next_waypoint[0] - self.x
                dy = next_waypoint[1] - self.y

                # Normalize direction
                distance = math.sqrt(dx*dx + dy*dy)
                if distance > 0:
                    dx = dx / distance
                    dy = dy / distance

                    # Apply movement with validation
                    new_x = self.x + dx * self.stats.speed * delta_time
                    new_y = self.y + dy * self.stats.speed * delta_time

                    if self._is_valid_position(new_x, new_y):
                        self.x = new_x
                        self.y = new_y
                        self.velocity_x = dx * self.stats.speed
                        self.velocity_y = dy * self.stats.speed
                    else:
                        # Hit a wall, try to find a new path
                        self._recalculate_path()
            else:
                # Reached the end of path, recalculate
                self._recalculate_path()
        else:
            # Direct movement to target (fallback)
            dx = self.target[0] - self.x
            dy = self.target[1] - self.y

            # Normalize direction
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                dx = dx / distance
                dy = dy / distance

                # Apply movement with validation
                new_x = self.x + dx * self.stats.speed * delta_time
                new_y = self.y + dy * self.stats.speed * delta_time

                if self._is_valid_position(new_x, new_y):
                    self.x = new_x
                    self.y = new_y
                    self.velocity_x = dx * self.stats.speed
                    self.velocity_y = dy * self.stats.speed
                else:
                    # Hit a wall, try fallback movement
                    self._fallback_movement_towards_player(self.target)
                    # Only print wall hits occasionally to reduce spam
                    if not hasattr(self, '_wall_hit_count'):
                        self._wall_hit_count = 0
                    self._wall_hit_count += 1
                    if self._wall_hit_count % 60 == 0:  # Print every 60 wall hits
                        print(f"Monster hit wall at ({int(new_x)}, {int(new_y)}), staying at ({self.x:.1f}, {self.y:.1f})")

    def _recalculate_path(self):
        """Recalculate path to current target."""
        if not self.pathfinder or not self.target:
            return

        new_path = self.pathfinder.find_path((self.x, self.y), self.target)
        if new_path and len(new_path) > 1:
            self.current_path = new_path
            print(f"Monster path recalculated with {len(new_path)} waypoints")
        else:
            # Only print pathfinding failures occasionally
            if not hasattr(self, '_path_fail_count'):
                self._path_fail_count = 0
            self._path_fail_count += 1
            if self._path_fail_count % 30 == 0:  # Print every 30 failures
                print(f"Monster cannot find path to {self.target}, using fallback movement")
            self.current_path = []

    def _check_adaptation(self):
        """Check if monster should adapt its behavior."""
        current_time = time.time()

        # Check adaptation cooldown
        if current_time - self.last_adaptation_time < self.adaptation_cooldown:
            return

        # Check if enough data for adaptation
        if len(self.observed_player_actions) < self.stats.adaptation_threshold:
            return

        # Perform adaptation
        self._adapt_behavior()
        self.last_adaptation_time = current_time

    def _adapt_behavior(self):
        """Adapt monster behavior based on learned patterns."""
        # Create current loadout from stats
        current_loadout = MonsterLoadout(
            attack_power=self.stats.attack_power,
            defense=self.stats.defense,
            speed=self.stats.speed,
            health=self.stats.health,
            abilities=['basic_attack'],  # Default ability
            aggression_level=0.5,  # Default aggression
            tactical_preference='aggressive'  # Default preference
        )

        # Create player data from recent observations
        player_data = {}
        if self.observed_player_actions:
            latest_observation = self.observed_player_actions[-1]
            player_state = latest_observation['state']
            player_data = {
                'health': player_state.get('health', 100),
                'speed': 5.0,  # Default player speed
                'playstyle': {
                    'aggression': 0.5  # Default aggression
                }
            }

        # Optimize stats
        optimized_loadout = self.optimizer.optimize(
            current_loadout,
            player_data,
            max_iterations=50
        )

        # Apply optimized stats
        self.stats.speed = optimized_loadout.speed
        self.stats.attack_power = optimized_loadout.attack_power
        self.stats.defense = optimized_loadout.defense
        self.stats.health = optimized_loadout.health

        # Increase adaptation level
        self.adaptation_level += 1

        print(f"Monster adapted! Level: {self.adaptation_level}, New stats: Speed={self.stats.speed}, Attack={self.stats.attack_power}, Defense={self.stats.defense}")

    def set_target(self, x: float, y: float):
        """Set a new movement target."""
        self.target = (x, y)

        # Use pathfinding if dungeon map is available
        if self.dungeon_map and self.pathfinder:
            path = self.pathfinder.find_path(
                (self.x, self.y),  # Use world coordinates
                (x, y)  # Use world coordinates
            )
            if path:
                self.current_path = path
                # Set target to first waypoint in path (not the final destination)
                if len(path) > 1:
                    self.target = path[1]  # Move to next waypoint
                else:
                    self.target = path[0]  # Final destination
            else:
                self.current_path = [(x, y)]
                self.target = (x, y)
        else:
            self.current_path = [(x, y)]
            self.target = (x, y)

    def attack(self, target_pos: Tuple[float, float]):
        """Enhanced attack with skill effects."""
        if self._distance_to(target_pos) <= self.stats.attack_range:
            self.is_attacking = True

            # Reset attack cooldown
            self.last_attack_time = time.time()

            # Record attack
            attack_data = {
                "type": "attack",
                "position": (self.x, self.y),
                "target": target_pos,
                "timestamp": time.time(),
                "damage": self.stats.attack_power,
                "weapon": self.equipped_weapon.name if self.equipped_weapon else "Claws"
            }

            self.combat_history.append(attack_data)

            # Update success rate
            self._update_success_rate("attacks", True)

            # Reset attack state after delay
            self.is_attacking = False

            # Apply skill-based attack modifications
            if hasattr(self, 'feral_rage') and self.feral_rage:
                # Feral Rage: Increased damage when health is low
                if self.stats.health < self.stats.max_health * 0.5:
                    damage_multiplier = 1.5
                    print(f"{self.name} enters Feral Rage!")
                else:
                    damage_multiplier = 1.0
            else:
                damage_multiplier = 1.0

            # Apply poison damage if venomous
            if hasattr(self, 'poison_damage') and hasattr(self, 'poison_duration'):
                # This would be applied to the target in combat system
                pass

    def take_damage(self, amount: int):
        print(f"[DEBUG] Monster.take_damage called: amount={amount}, health_before={self.stats.health}")
        # Apply armor defense if equipped
        if self.equipped_armor:
            # Reduce damage based on armor type
            if hasattr(self, 'last_damage_type') and self.last_damage_type == "physical":
                amount = max(1, amount - self.equipped_armor.physical_defense)
            else:
                amount = max(1, amount - self.equipped_armor.magical_defense)

        actual_damage = max(0, amount - self.stats.defense)
        self.stats.health = max(0, self.stats.health - actual_damage)

        # Update combat stats
        self.combat_stats.total_damage_taken += actual_damage

        self.combat_history.append({
            "type": "damage_taken",
            "amount": actual_damage,
            "current_health": self.stats.health,
            "timestamp": time.time()
        })

        # Return the actual damage dealt
        return actual_damage

    def equip_weapon(self, weapon: Weapon):
        """Equip a weapon."""
        if weapon in self.weapon_inventory:
            self.equipped_weapon = weapon
            self.attack_cooldown = 1.0 / weapon.attack_speed
            print(f"{self.name} equipped {weapon.name}!")
        else:
            print("Weapon not in inventory!")

    def equip_armor(self, armor: Armor):
        """Equip armor."""
        if armor in self.armor_inventory:
            self.equipped_armor = armor
            print(f"{self.name} equipped {armor.name}!")
        else:
            print("Armor not in inventory!")

    def add_weapon_to_inventory(self, weapon: Weapon):
        """Add a weapon to inventory."""
        self.weapon_inventory.append(weapon)
        print(f"{self.name} picked up {weapon.name}!")

    def add_armor_to_inventory(self, armor: Armor):
        """Add armor to inventory."""
        self.armor_inventory.append(armor)
        print(f"{self.name} picked up {armor.name}!")

    def _update_special_effects(self):
        """Update special effects on the monster."""
        current_time = time.time()
        expired_effects = []

        for effect_type, effect_data in self.active_effects.items():
            # Remove or comment out poison/environmental/special effect damage to monster
            # if effect_data["damage_per_turn"] > 0:
            #     self.take_damage(effect_data["damage_per_turn"])
            #     print(f"{self.name} takes {effect_data['damage_per_turn']} {effect_type} damage!")

            # Reduce duration
            effect_data["duration"] -= 1

            # Check if effect expired
            if effect_data["duration"] <= 0:
                expired_effects.append(effect_type)
                print(f"{self.name} is no longer affected by {effect_type}!")

        # Remove expired effects
        for effect_type in expired_effects:
            del self.active_effects[effect_type]

    def _distance_to(self, pos: Tuple[float, float]) -> float:
        """Calculate distance to a position."""
        if not pos:
            return float('inf')
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return math.sqrt(dx*dx + dy*dy)

    def _update_success_rate(self, metric: str, success: bool):
        """Update success rate for a metric."""
        if metric in self.success_rate:
            current_rate = self.success_rate[metric]
            # Simple moving average
            self.success_rate[metric] = current_rate * 0.9 + (1.0 if success else 0.0) * 0.1

    def get_state(self) -> dict:
        """Get the current state of the monster."""
        return {
            "position": (self.x, self.y),
            "health": self.stats.health,
            "is_attacking": self.is_attacking,
            "target": self.target,
            "adaptation_level": self.adaptation_level,
            "velocity": (self.velocity_x, self.velocity_y),
            "strategy": self.current_strategy,
            "is_in_combat": self.is_in_combat,
            "equipped_weapon": self.equipped_weapon.name if self.equipped_weapon else None,
            "equipped_armor": self.equipped_armor.name if self.equipped_armor else None,
            "active_effects": list(self.active_effects.keys())
        }

    def get_performance_metrics(self) -> dict:
        """Get AI performance metrics."""
        return {
            "avg_decision_time": sum(self.decision_times) / len(self.decision_times) if self.decision_times else 0,
            "success_rates": self.success_rate,
            "adaptation_level": self.adaptation_level,
            "combat_history_length": len(self.combat_history),
            "observations_count": len(self.observed_player_actions)
        }

    def set_dungeon_map(self, dungeon_map):
        """Set the dungeon map and initialize the pathfinder."""
        self.dungeon_map = dungeon_map
        if dungeon_map:
            self.pathfinder = AStarPathfinder(
                grid_width=len(dungeon_map[0]),
                grid_height=len(dungeon_map),
                dungeon_map=dungeon_map
            )
            print(f"[DEBUG] Monster pathfinder initialized: {self.pathfinder is not None}")

    def adapt(self):
        """Monster adapts and may gain a skill point and unlock a skill."""
        self.skill_tree.skill_points += 1
        unlockable = self.skill_tree.get_unlockable_skills()
        if unlockable:
            skill = unlockable[0]  # For now, just pick the first unlockable skill
            if self.skill_tree.unlock_skill(skill.id):
                self._apply_skill_effect(skill.id)

    def _apply_skill_effect(self, skill_id: str):
        """Apply the effect of a skill to the monster."""
        skill = self.skill_tree.skills.get(skill_id)
        if not skill:
            return
        # Example effects for default monster skills
        if skill_id == "feral_rage":
            self.combat_stats.strength += 4
        elif skill_id == "thick_hide":
            self.combat_stats.constitution += 2
        elif skill_id == "shadow_step":
            self.shadow_step = True
        elif skill_id == "venomous":
            self.venomous = True
        elif skill_id == "alpha_predator":
            self.alpha_predator = True

    def get_skill_tree_state(self):
        """Return a summary of the monster's skill tree."""
        return {
            "skill_points": self.skill_tree.skill_points,
            "unlocked_skills": [s.name for s in self.skill_tree.get_unlocked_skills()],
            "unlockable_skills": [s.name for s in self.skill_tree.get_unlockable_skills()],
        }

    def _apply_skill_behavior_modifications(self, player_state: dict = None, delta_time: float = 0.0):
        """Apply skill-based modifications to monster behavior."""
        if not player_state:
            return

        # Shadow Step: Teleport behind player when health is low
        if hasattr(self, 'shadow_step') and self.shadow_step and self.stats.health < self.stats.max_health * 0.3:
            if player_state.get('position'):
                player_x, player_y = player_state['position']
                # Calculate position behind player
                dx = self.x - player_x
                dy = self.y - player_y
                distance = (dx**2 + dy**2)**0.5
                if distance > 0:
                    # Teleport to position behind player
                    teleport_x = player_x - (dx / distance) * 30
                    teleport_y = player_y - (dy / distance) * 30
                    if self._is_valid_position(teleport_x, teleport_y):
                        self.x = teleport_x
                        self.y = teleport_y
                        print(f"{self.name} used Shadow Step!")

        # Alpha Predator: More aggressive when player is weakened
        if hasattr(self, 'alpha_predator') and self.alpha_predator:
            if player_state.get('health', 100) < 50:
                # Increase aggression and damage
                self.aggression_multiplier = 2.0
                self.combat_stats.strength += 10
            else:
                self.aggression_multiplier = 1.0

        # Venomous: Apply poison effect on attacks
        if hasattr(self, 'venomous') and self.venomous:
            self.poison_damage = 5
            self.poison_duration = 3

    def _is_valid_position(self, x: float, y: float) -> bool:
        """Check if a position is valid (within bounds and walkable)."""
        if not self.dungeon_map:
            return True

        grid_x, grid_y = int(x), int(y)
        if not (0 <= grid_x < len(self.dungeon_map[0]) and 0 <= grid_y < len(self.dungeon_map)):
            return False

        return self.dungeon_map[grid_y][grid_x].walkable
