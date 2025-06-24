"""
environment.py

Environment logic for Dungeon Duo: Rough AI.
Handles environmental interactions, lighting, and visibility systems.
"""

import math
import time
from typing import List, Tuple, Dict, Any, Optional, Set
from .tile import Tile, TileType


class LightingSystem:
    """
    Handles lighting and visibility calculations for the dungeon.

    Attributes:
        light_sources (List[Tuple[int, int, float]]): List of (x, y, intensity) light sources
        ambient_light (float): Ambient light level (0.0 to 1.0)
        max_light_distance (int): Maximum distance light can travel
        fog_of_war (bool): Whether fog of war is enabled
        visibility_cache (Dict[Tuple[int, int], float]): Cache for visibility calculations
    """

    def __init__(self, ambient_light: float = 0.1, max_light_distance: int = 8):
        self.light_sources = []
        self.ambient_light = ambient_light
        self.max_light_distance = max_light_distance
        self.fog_of_war = True
        self.visibility_cache = {}
        self.light_map = []
        self.width = 0
        self.height = 0

    def add_light_source(self, x: int, y: int, intensity: float):
        """Add a light source at the specified position."""
        self.light_sources.append((x, y, intensity))

    def remove_light_source(self, x: int, y: int):
        """Remove a light source at the specified position."""
        self.light_sources = [(lx, ly, intensity) for lx, ly, intensity in self.light_sources
                             if not (lx == x and ly == y)]

    def update_lighting(self, dungeon_map: List[List[Tile]]):
        """Update the lighting map for the entire dungeon."""
        if not dungeon_map:
            return

        self.height = len(dungeon_map)
        self.width = len(dungeon_map[0]) if dungeon_map else 0

        # Initialize light map
        self.light_map = [[self.ambient_light for _ in range(self.width)] for _ in range(self.height)]

        # Calculate light from each source
        for x, y, intensity in self.light_sources:
            self._cast_light(x, y, intensity, dungeon_map)

    def _cast_light(self, source_x: int, source_y: int, intensity: float, dungeon_map: List[List[Tile]]):
        """Cast light from a source using ray casting."""
        for y in range(max(0, source_y - self.max_light_distance),
                      min(self.height, source_y + self.max_light_distance + 1)):
            for x in range(max(0, source_x - self.max_light_distance),
                          min(self.width, source_x + self.max_light_distance + 1)):

                distance = math.sqrt((x - source_x) ** 2 + (y - source_y) ** 2)
                if distance <= self.max_light_distance:
                    # Check line of sight
                    if self._has_line_of_sight(source_x, source_y, x, y, dungeon_map):
                        # Calculate light intensity based on distance
                        light_intensity = intensity * (1.0 - distance / self.max_light_distance)
                        self.light_map[y][x] = max(self.light_map[y][x], light_intensity)

    def _has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int, dungeon_map: List[List[Tile]]) -> bool:
        """Check if there's a clear line of sight between two points."""
        # Use Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        n = 1 + dx + dy
        x_inc = 1 if x2 > x1 else -1
        y_inc = 1 if y2 > y1 else -1
        error = dx - dy
        dx *= 2
        dy *= 2

        for _ in range(n):
            # Check if current position blocks light
            if 0 <= x < self.width and 0 <= y < self.height:
                if not dungeon_map[y][x].transparent:
                    return False

            if x == x2 and y == y2:
                break

            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx

        return True

    def get_light_level(self, x: int, y: int) -> float:
        """Get the light level at a specific position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.light_map[y][x]
        return self.ambient_light

    def is_visible(self, x: int, y: int) -> bool:
        """Check if a position is visible (has sufficient light)."""
        return self.get_light_level(x, y) > 0.1


class VisibilitySystem:
    """
    Handles visibility and fog of war for the player.

    Attributes:
        player_position (Tuple[int, int]): Current player position
        visibility_radius (int): Radius of player visibility
        discovered_tiles (Set[Tuple[int, int]]): Set of discovered tile positions
        visible_tiles (Set[Tuple[int, int]]): Set of currently visible tile positions
    """

    def __init__(self, visibility_radius: int = 8):
        self.player_position = (0, 0)
        self.visibility_radius = visibility_radius
        self.discovered_tiles = set()
        self.visible_tiles = set()

    def update_visibility(self, player_x: int, player_y: int, dungeon_map: List[List[Tile]]):
        """Update visibility based on player position."""
        ix, iy = int(player_x), int(player_y)
        self.player_position = (ix, iy)
        self.visible_tiles.clear()

        if not dungeon_map:
            return

        height = len(dungeon_map)
        width = len(dungeon_map[0]) if dungeon_map else 0

        # Check visibility in a square around the player
        for y in range(max(0, iy - self.visibility_radius),
                      min(height, iy + self.visibility_radius + 1)):
            for x in range(max(0, ix - self.visibility_radius),
                          min(width, ix + self.visibility_radius + 1)):

                distance = max(abs(x - ix), abs(y - iy))
                if distance <= self.visibility_radius:
                    if self._has_line_of_sight(ix, iy, x, y, dungeon_map):
                        self.visible_tiles.add((x, y))
                        self.discovered_tiles.add((x, y))

        # Update tile visibility states
        for y in range(height):
            for x in range(width):
                tile = dungeon_map[y][x]
                tile.discovered = (x, y) in self.discovered_tiles
                tile.visible = (x, y) in self.visible_tiles

    def _has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int, dungeon_map: List[List[Tile]]) -> bool:
        """Check if there's a clear line of sight between two points."""
        # Use Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        n = 1 + dx + dy
        x_inc = 1 if x2 > x1 else -1
        y_inc = 1 if y2 > y1 else -1
        error = dx - dy
        dx *= 2
        dy *= 2

        for _ in range(n):
            # Check if current position blocks vision
            if 0 <= x < len(dungeon_map[0]) and 0 <= y < len(dungeon_map):
                if not dungeon_map[y][x].transparent:
                    return False

            if x == x2 and y == y2:
                break

            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx

        return True

    def is_tile_visible(self, x: int, y: int) -> bool:
        """Check if a tile is currently visible."""
        return (x, y) in self.visible_tiles

    def is_tile_discovered(self, x: int, y: int) -> bool:
        """Check if a tile has been discovered."""
        return (x, y) in self.discovered_tiles


class EnvironmentalEffects:
    """
    Handles environmental effects and interactions.

    Attributes:
        effects (Dict[Tuple[int, int], Dict[str, Any]]): Active effects by position
        effect_duration (Dict[str, int]): Duration of different effect types
    """

    def __init__(self):
        self.effects = {}
        self.effect_duration = {
            'poison': 5,
            'burn': 3,
            'freeze': 4,
            'heal': 1
        }

    def add_effect(self, x: int, y: int, effect_type: str, intensity: float = 1.0):
        """Add an environmental effect at a position."""
        if (x, y) not in self.effects:
            self.effects[(x, y)] = {}

        self.effects[(x, y)][effect_type] = {
            'intensity': intensity,
            'duration': self.effect_duration.get(effect_type, 1),
            'remaining': self.effect_duration.get(effect_type, 1)
        }

    def update_effects(self):
        """Update all environmental effects (decrease duration)."""
        positions_to_remove = []

        for pos, effects in self.effects.items():
            effects_to_remove = []
            for effect_type, effect_data in effects.items():
                effect_data['remaining'] -= 1
                if effect_data['remaining'] <= 0:
                    effects_to_remove.append(effect_type)

            for effect_type in effects_to_remove:
                del effects[pos][effect_type]

            if not effects[pos]:
                positions_to_remove.append(pos)

        for pos in positions_to_remove:
            del self.effects[pos]

    def get_effects_at(self, x: int, y: int) -> Dict[str, Any]:
        """Get all effects at a specific position."""
        return self.effects.get((x, y), {})

    def apply_effects_to_entity(self, x: int, y: int, entity) -> Dict[str, float]:
        """Apply environmental effects to an entity at a position."""
        effects = self.get_effects_at(x, y)
        damage_dealt = {}

        for effect_type, effect_data in effects.items():
            intensity = effect_data['intensity']

            if effect_type == 'poison':
                damage = int(5 * intensity)
                entity.take_damage(damage)
                damage_dealt['poison'] = damage

            elif effect_type == 'burn':
                damage = int(8 * intensity)
                entity.take_damage(damage)
                damage_dealt['burn'] = damage

            elif effect_type == 'freeze':
                # Slow movement
                if hasattr(entity, 'movement_speed'):
                    entity.movement_speed *= (1.0 - 0.3 * intensity)
                damage_dealt['freeze'] = 0

            elif effect_type == 'heal':
                healing = int(10 * intensity)
                if hasattr(entity, 'heal'):
                    entity.heal(healing)
                damage_dealt['heal'] = -healing  # Negative for healing

        return damage_dealt


class EnvironmentManager:
    """
    Main environment manager that coordinates lighting, visibility, and effects.

    Attributes:
        lighting_system (LightingSystem): Lighting system instance
        visibility_system (VisibilitySystem): Visibility system instance
        effects_system (EnvironmentalEffects): Environmental effects system
        weather_effects (Dict[str, Any]): Current weather effects
    """

    def __init__(self, dungeon_width: int = 100, dungeon_height: int = 100):
        self.lighting_system = LightingSystem()
        self.visibility_system = VisibilitySystem()
        self.effects_system = EnvironmentalEffects()
        self.weather_effects = {}
        self.dungeon_width = dungeon_width
        self.dungeon_height = dungeon_height

    def update(self, player_x: int, player_y: int, dungeon_map: List[List[Tile]]):
        """Update all environment systems."""
        # Update lighting
        self.lighting_system.update_lighting(dungeon_map)

        # Update visibility
        self.visibility_system.update_visibility(player_x, player_y, dungeon_map)

        # Update environmental effects
        self.effects_system.update_effects()

        # Update weather effects
        self._update_weather()

    def _update_weather(self):
        """Update weather effects."""
        # Simple weather system - could be expanded
        pass

    def add_light_source(self, x: int, y: int, intensity: float):
        """Add a light source."""
        self.lighting_system.add_light_source(x, y, intensity)

    def remove_light_source(self, x: int, y: int):
        """Remove a light source."""
        self.lighting_system.remove_light_source(x, y)

    def get_light_level(self, x: int, y: int) -> float:
        """Get light level at position."""
        return self.lighting_system.get_light_level(x, y)

    def is_visible(self, x: int, y: int) -> bool:
        """Check if position is visible."""
        return self.visibility_system.is_tile_visible(x, y)

    def is_discovered(self, x: int, y: int) -> bool:
        """Check if position has been discovered."""
        return self.visibility_system.is_tile_discovered(x, y)

    def add_environmental_effect(self, x: int, y: int, effect_type: str, intensity: float = 1.0):
        """Add an environmental effect."""
        self.effects_system.add_effect(x, y, effect_type, intensity)

    def get_effects_at(self, x: int, y: int) -> Dict[str, Any]:
        """Get effects at position."""
        return self.effects_system.get_effects_at(x, y)

    def apply_effects_to_entity(self, x: int, y: int, entity) -> Dict[str, float]:
        """Apply environmental effects to entity."""
        return self.effects_system.apply_effects_to_entity(x, y, entity)

    def get_environmental_damage(self, x: int, y: int, tile: Tile) -> int:
        """Calculate environmental damage at a given position."""
        damage = 0
        current_time = time.time()
        # Check if it's a trap and if it's active
        if tile.tile_type == TileType.TRAP and (current_time - tile.last_triggered_time > 2.0):
            # For simplicity, let's say traps always deal 10 damage when stepped on.
            damage = 10
            tile.last_triggered_time = current_time
            print(f"DEBUG: Player stepped on a trap at ({x}, {y}) dealing {damage} damage.")
        return damage

    def create_environmental_hazard(self, x: int, y: int, hazard_type: str, duration: int = 10):
        """Create an environmental hazard."""
        if hazard_type == 'poison_pool':
            self.add_environmental_effect(x, y, 'poison', 1.5)
        elif hazard_type == 'fire':
            self.add_environmental_effect(x, y, 'burn', 2.0)
        elif hazard_type == 'ice':
            self.add_environmental_effect(x, y, 'freeze', 1.0)
        elif hazard_type == 'healing_fountain':
            self.add_environmental_effect(x, y, 'heal', 1.0)

    def get_environmental_info(self, x: int, y: int) -> Dict[str, Any]:
        """Get comprehensive environmental information for a position."""
        return {
            'light_level': self.get_light_level(x, y),
            'visible': self.is_visible(x, y),
            'discovered': self.is_discovered(x, y),
            'effects': self.get_effects_at(x, y),
            'hazardous': self.get_environmental_damage(x, y, None) > 0
        }

    def reset(self):
        """Reset all environment systems."""
        self.lighting_system.light_sources.clear()
        self.lighting_system.light_map.clear()
        self.visibility_system.discovered_tiles.clear()
        self.visibility_system.visible_tiles.clear()
        self.effects_system.effects.clear()
        self.weather_effects.clear()
