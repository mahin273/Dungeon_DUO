"""
dungeon_generator.py

Procedural dungeon generator for Dungeon Duo: Rough AI.
Generates rooms, corridors, and strategic elements for gameplay and AI pathfinding.
"""

import random
import math
from typing import List, Tuple, Dict, Any, Optional, Set
from dataclasses import dataclass
from .tile import Tile, TileType, TileFactory


@dataclass
class Room:
    """Represents a room in the dungeon."""
    x: int
    y: int
    width: int
    height: int
    room_type: str = "normal"
    connected: bool = False

    @property
    def center(self) -> Tuple[int, int]:
        """Get the center point of the room."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def area(self) -> int:
        """Get the area of the room."""
        return self.width * self.height

    def intersects(self, other: 'Room', padding: int = 1) -> bool:
        """Check if this room intersects with another room."""
        return (self.x - padding < other.x + other.width and
                self.x + self.width + padding > other.x and
                self.y - padding < other.y + other.height and
                self.y + self.height + padding > other.y)

    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is inside this room."""
        return (self.x <= x < self.x + self.width and
                self.y <= y < self.y + self.height)


class DungeonGenerator:
    """
    Procedural dungeon generator using room-based generation.

    Attributes:
        width (int): Width of the dungeon
        height (int): Height of the dungeon
        rooms (List[Room]): List of generated rooms
        corridors (List[Tuple[int, int]]): List of corridor positions
        dungeon_map (List[List[Tile]]): 2D array of tiles
        seed (int): Random seed for generation
        stats (Dict[str, Any]): Generation statistics
    """

    def __init__(self, width: int = 100, height: int = 100, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.rooms = []
        self.corridors = set()
        self.dungeon_map = []
        self.seed = seed if seed is not None else random.randint(1, 1000000)
        self.stats = {
            'rooms_created': 0,
            'corridors_created': 0,
            'doors_placed': 0,
            'chests_placed': 0,
            'traps_placed': 0,
            'generation_time': 0
        }

        # Generation parameters
        self.min_room_size = 5
        self.max_room_size = 15
        self.max_rooms = 20
        self.corridor_width = 1
        self.door_chance = 0.3
        self.chest_chance = 0.5
        self.trap_chance = 0.05
        self.water_chance = 0.02
        self.lava_chance = 0.01

        random.seed(self.seed)

    def generate(self) -> List[List[Tile]]:
        """
        Generate a complete dungeon.

        Returns:
            List[List[Tile]]: 2D array of tiles representing the dungeon
        """
        import time
        start_time = time.time()

        # Initialize dungeon with walls
        self._initialize_dungeon()

        # Generate rooms
        self._generate_rooms()

        # Connect rooms with corridors
        self._connect_rooms()

        # Add features (doors, chests, traps, etc.)
        self._add_features()

        # Add environmental hazards
        self._add_environmental_hazards()

        # Ensure connectivity
        self._ensure_connectivity()

        # Place a health quest tile in a random room (not the spawn room)
        if len(self.rooms) > 1:
            import random
            room = random.choice(self.rooms[1:])  # Exclude spawn room
            x = random.randint(room.x + 1, room.x + room.width - 2)
            y = random.randint(room.y + 1, room.y + room.height - 2)
            if self.dungeon_map[y][x].tile_type == TileType.ROOM_FLOOR:
                self.dungeon_map[y][x] = TileFactory.create_health_quest()

        # Calculate statistics
        self.stats['generation_time'] = time.time() - start_time
        self._calculate_stats()

        # Debug print for wall and walkable tile counts
        print(f"[DEBUG] Dungeon generation: walkable_tiles={self.stats['walkable_tiles']}, wall_tiles={self.stats['wall_tiles']}, walkable_percentage={self.stats['walkable_percentage']:.1f}%")

        # After all features are added, place a chest at the player spawn
        spawn_x, spawn_y = self.get_spawn_position()
        if self.dungeon_map[spawn_y][spawn_x].tile_type in [TileType.ROOM_FLOOR, TileType.FLOOR]:
            self.dungeon_map[spawn_y][spawn_x] = TileFactory.create_chest()
            self.stats['chests_placed'] += 1
        return self.dungeon_map

    def _initialize_dungeon(self):
        """Initialize the dungeon with walls."""
        self.dungeon_map = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(TileFactory.create_wall())
            self.dungeon_map.append(row)

    def _generate_rooms(self):
        """Generate rooms using a simple algorithm."""
        attempts = 0
        max_attempts = self.max_rooms * 10

        while len(self.rooms) < self.max_rooms and attempts < max_attempts:
            # Generate random room dimensions
            room_width = random.randint(self.min_room_size, self.max_room_size)
            room_height = random.randint(self.min_room_size, self.max_room_size)

            # Generate random position
            x = random.randint(1, self.width - room_width - 1)
            y = random.randint(1, self.height - room_height - 1)

            new_room = Room(x, y, room_width, room_height)

            # Check if room overlaps with existing rooms
            failed = False
            for room in self.rooms:
                if new_room.intersects(room):
                    failed = True
                    break

            if not failed:
                self.rooms.append(new_room)
                self._carve_room(new_room)
                self.stats['rooms_created'] += 1

            attempts += 1

    def _carve_room(self, room: Room):
        """Carve out a room in the dungeon."""
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.dungeon_map[y][x] = TileFactory.create_room_floor()

    def _connect_rooms(self):
        """Connect rooms using corridors."""
        if len(self.rooms) < 2:
            return

        # Sort rooms by position to create a more natural layout
        sorted_rooms = sorted(self.rooms, key=lambda r: (r.x, r.y))

        for i in range(len(sorted_rooms) - 1):
            room1 = sorted_rooms[i]
            room2 = sorted_rooms[i + 1]

            # Connect rooms with L-shaped corridors
            self._create_corridor(room1.center, room2.center)

    def _create_corridor(self, start: Tuple[int, int], end: Tuple[int, int]):
        """Create a corridor between two points."""
        x1, y1 = start
        x2, y2 = end

        # Create L-shaped corridor
        if random.random() < 0.5:
            # Horizontal then vertical
            self._create_horizontal_corridor(x1, x2, y1)
            self._create_vertical_corridor(y1, y2, x2)
        else:
            # Vertical then horizontal
            self._create_vertical_corridor(y1, y2, x1)
            self._create_horizontal_corridor(x1, x2, y2)

    def _create_horizontal_corridor(self, x1: int, x2: int, y: int):
        """Create a horizontal corridor."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                if self.dungeon_map[y][x].tile_type == TileType.WALL:
                    self.dungeon_map[y][x] = TileFactory.create_corridor()
                    self.corridors.add((x, y))
                    self.stats['corridors_created'] += 1

    def _create_vertical_corridor(self, y1: int, y2: int, x: int):
        """Create a vertical corridor."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                if self.dungeon_map[y][x].tile_type == TileType.WALL:
                    self.dungeon_map[y][x] = TileFactory.create_corridor()
                    self.corridors.add((x, y))
                    self.stats['corridors_created'] += 1

    def _add_features(self):
        """Add doors, chests, and other features to the dungeon."""
        # Add doors between rooms and corridors
        self._add_doors()

        # Add chests in rooms
        self._add_chests()

        # Add traps
        self._add_traps()

        # Add stairs
        self._add_stairs()

    def _add_doors(self):
        """Add doors at room entrances."""
        for room in self.rooms:
            # Check each wall of the room for corridor connections
            for x in range(room.x, room.x + room.width):
                for y in range(room.y, room.y + room.height):
                    if self._is_door_candidate(x, y):
                        if random.random() < self.door_chance:
                            self.dungeon_map[y][x] = TileFactory.create_door()
                            self.stats['doors_placed'] += 1

    def _is_door_candidate(self, x: int, y: int) -> bool:
        """Check if a position is a good candidate for a door."""
        if not (0 < x < self.width - 1 and 0 < y < self.height - 1):
            return False

        # Check if this is a room floor adjacent to a corridor
        if self.dungeon_map[y][x].tile_type != TileType.ROOM_FLOOR:
            return False

        # Check if adjacent to corridor
        adjacent_corridors = 0
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.width and 0 <= ny < self.height and
                self.dungeon_map[ny][nx].tile_type == TileType.CORRIDOR):
                adjacent_corridors += 1

        return adjacent_corridors == 1

    def _add_chests(self):
        """Add chests to rooms."""
        for room in self.rooms:
            if room.area > 20:  # Only add chests to larger rooms
                chest_count = random.randint(0, 2)
                for _ in range(chest_count):
                    if random.random() < self.chest_chance:
                        x = random.randint(room.x + 1, room.x + room.width - 2)
                        y = random.randint(room.y + 1, room.y + room.height - 2)
                        if self.dungeon_map[y][x].tile_type == TileType.ROOM_FLOOR:
                            self.dungeon_map[y][x] = TileFactory.create_chest()
                            self.stats['chests_placed'] += 1

    def _add_traps(self):
        """Add traps to corridors and rooms."""
        for y in range(self.height):
            for x in range(self.width):
                if self.dungeon_map[y][x].tile_type in [TileType.CORRIDOR, TileType.ROOM_FLOOR]:
                    if random.random() < self.trap_chance:
                        self.dungeon_map[y][x] = TileFactory.create_trap()
                        self.stats['traps_placed'] += 1

    def _add_stairs(self):
        """Add stairs to the dungeon."""
        if not self.rooms:
            return

        # Add stairs up in the first room
        first_room = self.rooms[0]
        x = first_room.center[0]
        y = first_room.center[1]
        if self.dungeon_map[y][x].tile_type == TileType.ROOM_FLOOR:
            self.dungeon_map[y][x] = TileFactory.create_stairs_up()

        # Add stairs down in the last room
        last_room = self.rooms[-1]
        x = last_room.center[0]
        y = last_room.center[1]
        if self.dungeon_map[y][x].tile_type == TileType.ROOM_FLOOR:
            self.dungeon_map[y][x] = TileFactory.create_stairs_down()

    def _add_environmental_hazards(self):
        """Add environmental hazards like water and lava."""
        for y in range(self.height):
            for x in range(self.width):
                if self.dungeon_map[y][x].tile_type == TileType.ROOM_FLOOR:
                    if random.random() < self.water_chance:
                        self.dungeon_map[y][x] = TileFactory.create_water()
                    elif random.random() < self.lava_chance:
                        self.dungeon_map[y][x] = TileFactory.create_lava()

    def _ensure_connectivity(self):
        """Ensure the dungeon is fully connected."""
        # Simple flood fill to check connectivity
        start_pos = self._find_start_position()
        if start_pos:
            connected = self._flood_fill(start_pos)
            if len(connected) < len(self.corridors) + sum(room.area for room in self.rooms):
                # Add additional corridors to connect isolated areas
                self._connect_isolated_areas(connected)

    def _find_start_position(self) -> Optional[Tuple[int, int]]:
        """Find a starting position for connectivity check."""
        for y in range(self.height):
            for x in range(self.width):
                if self.dungeon_map[y][x].tile_type in [TileType.ROOM_FLOOR, TileType.CORRIDOR]:
                    return (x, y)
        return None

    def _flood_fill(self, start: Tuple[int, int]) -> Set[Tuple[int, int]]:
        """Perform flood fill to find connected areas."""
        connected = set()
        stack = [start]

        while stack:
            x, y = stack.pop()
            if (x, y) in connected:
                continue

            if not (0 <= x < self.width and 0 <= y < self.height):
                continue

            if self.dungeon_map[y][x].tile_type not in [TileType.ROOM_FLOOR, TileType.CORRIDOR]:
                continue

            connected.add((x, y))

            # Add adjacent positions
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                stack.append((x + dx, y + dy))

        return connected

    def _connect_isolated_areas(self, connected: Set[Tuple[int, int]]):
        """Connect isolated areas with additional corridors."""
        # Find isolated areas and connect them
        isolated_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if (self.dungeon_map[y][x].tile_type in [TileType.ROOM_FLOOR, TileType.CORRIDOR] and
                    (x, y) not in connected):
                    isolated_positions.append((x, y))

        # Connect isolated positions to connected areas
        for pos in isolated_positions[:5]:  # Limit connections to avoid overcrowding
            nearest = self._find_nearest_connected(pos, connected)
            if nearest:
                self._create_corridor(pos, nearest)

    def _find_nearest_connected(self, pos: Tuple[int, int], connected: Set[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Find the nearest connected position."""
        if not connected:
            return None

        min_distance = float('inf')
        nearest = None

        for connected_pos in connected:
            distance = math.sqrt((pos[0] - connected_pos[0])**2 + (pos[1] - connected_pos[1])**2)
            if distance < min_distance:
                min_distance = distance
                nearest = connected_pos

        return nearest

    def _calculate_stats(self):
        """Calculate additional generation statistics."""
        walkable_tiles = 0
        wall_tiles = 0

        for y in range(self.height):
            for x in range(self.width):
                if self.dungeon_map[y][x].walkable:
                    walkable_tiles += 1
                else:
                    wall_tiles += 1

        self.stats.update({
            'total_tiles': self.width * self.height,
            'walkable_tiles': walkable_tiles,
            'wall_tiles': wall_tiles,
            'walkable_percentage': (walkable_tiles / (self.width * self.height)) * 100,
            'average_room_size': sum(room.area for room in self.rooms) / len(self.rooms) if self.rooms else 0
        })

    def get_spawn_position(self) -> Tuple[int, int]:
        """Get a valid spawn position for the player."""
        if not self.rooms:
            return (self.width // 2, self.height // 2)

        # Return center of first room
        first_room = self.rooms[0]
        return first_room.center

    def get_monster_spawn_positions(self, count: int) -> List[Tuple[int, int]]:
        """Get valid spawn positions for monsters."""
        positions = []

        for room in self.rooms[1:]:  # Skip first room (player spawn)
            if len(positions) >= count:
                break

            # Add center of room
            if self.dungeon_map[room.center[1]][room.center[0]].walkable:
                positions.append(room.center)

            # Add random positions in room
            attempts = 0
            while len(positions) < count and attempts < 10:
                x = random.randint(room.x + 1, room.x + room.width - 2)
                y = random.randint(room.y + 1, room.y + room.height - 2)
                if self.dungeon_map[y][x].walkable:
                    positions.append((x, y))
                attempts += 1

        return positions[:count]

    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if a position is valid for movement."""
        ix, iy = int(x), int(y)
        if not (0 <= ix < self.width and 0 <= iy < self.height):
            return False
        return self.dungeon_map[iy][ix].walkable

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Get tile at position."""
        ix, iy = int(x), int(y)
        if not (0 <= ix < self.width and 0 <= iy < self.height):
            return None
        return self.dungeon_map[iy][ix]

    def set_tile(self, x: int, y: int, tile: Tile):
        """Set tile at position."""
        ix, iy = int(x), int(y)
        if 0 <= ix < self.width and 0 <= iy < self.height:
            self.dungeon_map[iy][ix] = tile

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return self.stats.copy()

    def save_dungeon(self, filename: str):
        """Save dungeon to file."""
        import json

        dungeon_data = {
            'width': self.width,
            'height': self.height,
            'seed': self.seed,
            'stats': self.stats,
            'rooms': [(r.x, r.y, r.width, r.height, r.room_type) for r in self.rooms],
            'tiles': []
        }

        for y in range(self.height):
            row = []
            for x in range(self.width):
                tile = self.dungeon_map[y][x]
                row.append({
                    'type': tile.tile_type.value,
                    'walkable': tile.walkable,
                    'transparent': tile.transparent,
                    'properties': tile.properties
                })
            dungeon_data['tiles'].append(row)

        with open(filename, 'w') as f:
            json.dump(dungeon_data, f, indent=2)

    def load_dungeon(self, filename: str):
        """Load dungeon from file."""
        import json

        with open(filename, 'r') as f:
            dungeon_data = json.load(f)

        self.width = dungeon_data['width']
        self.height = dungeon_data['height']
        self.seed = dungeon_data['seed']
        self.stats = dungeon_data['stats']

        # Reconstruct rooms
        self.rooms = []
        for room_data in dungeon_data['rooms']:
            self.rooms.append(Room(*room_data))

        # Reconstruct tiles
        self.dungeon_map = []
        for row_data in dungeon_data['tiles']:
            row = []
            for tile_data in row_data:
                tile_type = TileType(tile_data['type'])
                tile = Tile(tile_type)
                tile.walkable = tile_data['walkable']
                tile.transparent = tile_data['transparent']
                tile.properties = tile_data['properties']
                row.append(tile)
            self.dungeon_map.append(row)
