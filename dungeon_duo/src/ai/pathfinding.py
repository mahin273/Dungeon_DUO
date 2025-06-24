"""
pathfinding.py

A* pathfinding implementation for Dungeon Duo: Rough AI.
Supports dynamic obstacles, multiple heuristics, and path optimization.
"""

import heapq
from typing import List, Tuple, Dict, Set, Optional, Callable, Any
from dataclasses import dataclass
import math
import time

@dataclass
class Node:
    """Node for A* pathfinding."""
    x: int
    y: int
    g_cost: float = float('inf')  # Cost from start to this node
    h_cost: float = 0  # Heuristic cost from this node to goal
    parent: Optional['Node'] = None

    @property
    def f_cost(self) -> float:
        """Total cost (g + h)."""
        return self.g_cost + self.h_cost

    def __lt__(self, other):
        """Comparison for priority queue."""
        return self.f_cost < other.f_cost

    def __eq__(self, other):
        """Equality comparison."""
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        """Hash for set operations."""
        return hash((self.x, self.y))

class AStarPathfinder:
    """A* pathfinding implementation with multiple heuristics and optimizations."""

    def __init__(self, grid_width: int, grid_height: int, tile_size: int = 32, dungeon_map: Optional[List[List[Any]]] = None):
        """Initialize the pathfinder with grid dimensions."""
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.tile_size = tile_size
        self.obstacles: Set[Tuple[int, int]] = set()
        self.dynamic_obstacles: Dict[Tuple[int, int], float] = {}  # Position -> expiration time
        self.dungeon_map = dungeon_map  # Store reference to dungeon map

        # Path caching
        self.path_cache: Dict[Tuple[Tuple[int, int], Tuple[int, int]], List[Tuple[int, int]]] = {}
        self.cache_size_limit = 1000

        # Performance tracking
        self.pathfinding_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0

        if dungeon_map:
            self.set_dungeon_map(dungeon_map)

    def world_to_grid(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to grid coordinates."""
        # Since the game uses 1:1 world to grid mapping, just convert to integers
        return (int(world_x), int(world_y))

    def grid_to_world(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """Convert grid coordinates to world coordinates."""
        # Since the game uses 1:1 world to grid mapping, just convert to floats
        return (float(grid_x), float(grid_y))

    def add_obstacle(self, x: int, y: int):
        """Add a static obstacle."""
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            self.obstacles.add((x, y))
            self._clear_cache()  # Clear cache when obstacles change

    def add_dynamic_obstacle(self, x: int, y: int, duration: float):
        """Add a temporary obstacle that expires after duration seconds."""
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            self.dynamic_obstacles[(x, y)] = time.time() + duration

    def remove_obstacle(self, x: int, y: int):
        """Remove a static obstacle."""
        self.obstacles.discard((x, y))
        self._clear_cache()

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a grid position is walkable."""
        if not (0 <= x < self.grid_width and 0 <= y < self.grid_height):
            return False

        # Check static obstacles
        if (x, y) in self.obstacles:
            return False

        # Check dynamic obstacles
        if (x, y) in self.dynamic_obstacles:
            if time.time() > self.dynamic_obstacles[(x, y)]:
                del self.dynamic_obstacles[(x, y)]
            else:
                return False

        # Check dungeon map tiles if available
        if self.dungeon_map:
            return self.dungeon_map[y][x].walkable

        return True

    def get_neighbors(self, node: Node) -> List[Node]:
        """Get walkable neighbors of a node."""
        neighbors = []
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  # Cardinal directions
            (-1, -1), (-1, 1), (1, -1), (1, 1)  # Diagonal directions
        ]

        for dx, dy in directions:
            new_x, new_y = node.x + dx, node.y + dy

            if self.is_walkable(new_x, new_y):
                # Check diagonal movement (ensure both adjacent tiles are walkable)
                if abs(dx) == 1 and abs(dy) == 1:
                    if not (self.is_walkable(node.x + dx, node.y) and
                           self.is_walkable(node.x, node.y + dy)):
                        continue

                neighbors.append(Node(new_x, new_y))

        return neighbors

    def calculate_cost(self, from_node: Node, to_node: Node) -> float:
        """Calculate movement cost between two adjacent nodes."""
        dx = abs(to_node.x - from_node.x)
        dy = abs(to_node.y - from_node.y)

        # Diagonal movement costs more
        if dx == 1 and dy == 1:
            return 1.4  # sqrt(2)
        else:
            return 1.0

    def manhattan_heuristic(self, node: Node, goal: Node) -> float:
        """Manhattan distance heuristic."""
        return abs(node.x - goal.x) + abs(node.y - goal.y)

    def euclidean_heuristic(self, node: Node, goal: Node) -> float:
        """Euclidean distance heuristic."""
        dx = node.x - goal.x
        dy = node.y - goal.y
        return math.sqrt(dx*dx + dy*dy)

    def octile_heuristic(self, node: Node, goal: Node) -> float:
        """Octile distance heuristic (better for diagonal movement)."""
        dx = abs(node.x - goal.x)
        dy = abs(node.y - goal.y)
        return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)

    def find_path(self, start_world: Tuple[float, float],
                  goal_world: Tuple[float, float],
                  heuristic: str = "octile") -> Optional[List[Tuple[float, float]]]:
        """Find path from start to goal using A* algorithm."""
        start_time = time.time()

        # Convert world coordinates to grid coordinates
        start_grid = self.world_to_grid(start_world[0], start_world[1])
        goal_grid = self.world_to_grid(goal_world[0], goal_world[1])

        # Check cache first
        cache_key = (start_grid, goal_grid)
        if cache_key in self.path_cache:
            self.cache_hits += 1
            return [self.grid_to_world(x, y) for x, y in self.path_cache[cache_key]]

        self.cache_misses += 1

        # Validate start and goal positions
        if not self.is_walkable(start_grid[0], start_grid[1]):
            return None
        if not self.is_walkable(goal_grid[0], goal_grid[1]):
            return None

        # Initialize nodes
        start_node = Node(start_grid[0], start_grid[1], g_cost=0)
        goal_node = Node(goal_grid[0], goal_grid[1])

        # Select heuristic function
        heuristic_func = {
            "manhattan": self.manhattan_heuristic,
            "euclidean": self.euclidean_heuristic,
            "octile": self.octile_heuristic
        }.get(heuristic, self.octile_heuristic)

        start_node.h_cost = heuristic_func(start_node, goal_node)

        # Initialize open and closed sets
        open_set = [start_node]
        closed_set = set()
        node_dict = {start_grid: start_node}

        iterations = 0
        max_iterations = 1000  # Prevent infinite loops

        while open_set and iterations < max_iterations:
            iterations += 1
            current = heapq.heappop(open_set)

            if current.x == goal_node.x and current.y == goal_node.y:
                # Path found, reconstruct and cache it
                path = self._reconstruct_path(current)
                grid_path = [(node.x, node.y) for node in path]
                self.path_cache[cache_key] = grid_path
                self._manage_cache_size()

                # Convert to world coordinates
                world_path = [self.grid_to_world(x, y) for x, y in grid_path]

                # Record performance
                pathfinding_time = time.time() - start_time
                self.pathfinding_times.append(pathfinding_time)
                if len(self.pathfinding_times) > 100:
                    self.pathfinding_times.pop(0)

                return world_path

            closed_set.add((current.x, current.y))

            for neighbor in self.get_neighbors(current):
                if (neighbor.x, neighbor.y) in closed_set:
                    continue

                tentative_g_cost = current.g_cost + self.calculate_cost(current, neighbor)

                if (neighbor.x, neighbor.y) not in node_dict:
                    neighbor.g_cost = tentative_g_cost
                    neighbor.h_cost = heuristic_func(neighbor, goal_node)
                    neighbor.parent = current
                    node_dict[(neighbor.x, neighbor.y)] = neighbor
                    heapq.heappush(open_set, neighbor)
                elif tentative_g_cost < node_dict[(neighbor.x, neighbor.y)].g_cost:
                    # Update existing node
                    node_dict[(neighbor.x, neighbor.y)].g_cost = tentative_g_cost
                    node_dict[(neighbor.x, neighbor.y)].parent = current
                    # Re-heapify (inefficient but simple)
                    open_set = [n for n in open_set if n != node_dict[(neighbor.x, neighbor.y)]]
                    heapq.heapify(open_set)
                    heapq.heappush(open_set, node_dict[(neighbor.x, neighbor.y)])

        # No path found
        return None

    def _reconstruct_path(self, goal_node: Node) -> List[Node]:
        """Reconstruct path from goal node to start node."""
        path = []
        current = goal_node
        while current is not None:
            path.append(current)
            current = current.parent
        return list(reversed(path))

    def _clear_cache(self):
        """Clear the path cache."""
        self.path_cache.clear()

    def _manage_cache_size(self):
        """Manage cache size to prevent memory issues."""
        if len(self.path_cache) > self.cache_size_limit:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self.path_cache.keys())[:len(self.path_cache) // 2]
            for key in keys_to_remove:
                del self.path_cache[key]

    def get_performance_stats(self) -> dict:
        """Get pathfinding performance statistics."""
        return {
            "avg_pathfinding_time": sum(self.pathfinding_times) / len(self.pathfinding_times) if self.pathfinding_times else 0,
            "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            "cache_size": len(self.path_cache),
            "total_paths_found": len(self.pathfinding_times)
        }

    def set_dungeon_map(self, dungeon_map: List[List[Any]]):
        """Set the dungeon map and populate obstacles."""
        self.dungeon_map = dungeon_map  # Store the dungeon map reference
        self.grid_width = len(dungeon_map[0])
        self.grid_height = len(dungeon_map)
        self.obstacles.clear()

        # Populate obstacles from non-walkable tiles
        for y, row in enumerate(dungeon_map):
            for x, tile in enumerate(row):
                if not tile.walkable:
                    self.obstacles.add((x, y))

        self._clear_cache()
