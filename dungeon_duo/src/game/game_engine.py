"""
game_engine.py

Main game loop and state management for Dungeon Duo: Rough AI.
Handles game states, event processing, and integration with AI systems.
"""

import pygame
import pygame_gui
from enum import Enum
import time
from typing import Optional, List, Tuple, Dict, Any
import math
import random

# Import world generation systems
from ..world.dungeon_generator import DungeonGenerator
from ..world.environment import EnvironmentManager
from ..world.tile import Tile, TileType, TileFactory
from ..game.player import Player
from ..game.monster import Monster
from ..game.combat_system import CombatSystem

class GameState(Enum):
    """Game state enumeration."""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"

class GameEngine:
    """Main game engine class for Dungeon Duo."""

    def __init__(self, window_width: int = 1280, window_height: int = 720):
        """Initialize the game engine."""
        pygame.init()
        pygame.display.set_caption("Dungeon Duo: Rough AI")

        # Display setup
        self.window_size = (window_width, window_height)
        self.window_surface = pygame.display.set_mode(self.window_size)
        self.clock = pygame.time.Clock()

        # UI Manager setup
        self.ui_manager = pygame_gui.UIManager(self.window_size)

        # Game state
        self.current_state = GameState.MENU
        self.running = True
        # Target FPS for smooth gameplay
        self.target_fps = 60  # Always run at 60 FPS
        self.delta_time = 0

        # Performance monitoring
        self.frame_times = []
        self.ai_calculation_times = []

        # World generation systems
        self.dungeon_width = 100
        self.dungeon_height = 100
        self.dungeon_generator = DungeonGenerator(self.dungeon_width, self.dungeon_height)
        self.environment_manager = EnvironmentManager(self.dungeon_width, self.dungeon_height)
        self.dungeon_map = []

        # Camera/viewport settings
        self.camera_x = 0
        self.camera_y = 0
        self.tile_size = 32  # Match renderer's tile size
        self.viewport_width = window_width // self.tile_size
        self.viewport_height = window_height // self.tile_size

        # Smooth camera movement
        self.target_camera_x = 0
        self.target_camera_y = 0
        self.camera_speed = 0.1  # Reduced for smoother movement

        # Game components
        self.player = None
        self.monster = None
        self.world = None
        self.combat_system = CombatSystem()  # Initialize combat system

        # World generation statistics
        self.generation_stats = {}

    def generate_world(self, seed: Optional[int] = None):
        """Generate a new dungeon world."""
        print("Generating dungeon world...")

        # Generate dungeon
        self.dungeon_map = self.dungeon_generator.generate()
        self.generation_stats = self.dungeon_generator.get_generation_stats()

        # Initialize environment manager
        self.environment_manager = EnvironmentManager(self.dungeon_width, self.dungeon_height)

        # Add light sources (player will be one)
        spawn_pos = self.dungeon_generator.get_spawn_position()
        self.environment_manager.add_light_source(spawn_pos[0], spawn_pos[1], 1.0)

        print(f"Dungeon generated successfully!")
        print(f"Stats: {self.generation_stats}")

        return spawn_pos

    def handle_events(self):
        """Process all game events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.current_state == GameState.PLAYING:
                        self.current_state = GameState.PAUSED
                    elif self.current_state == GameState.PAUSED:
                        self.current_state = GameState.PLAYING

                # Debug keys for world generation
                if event.key == pygame.K_r and self.current_state == GameState.PLAYING:
                    # Regenerate world
                    spawn_pos = self.generate_world()
                    if self.player:
                        self.player.x, self.player.y = spawn_pos

                if event.key == pygame.K_t and self.current_state == GameState.PLAYING:
                    # Toggle tile visibility
                    self.environment_manager.visibility_system.visibility_radius = (
                        0 if self.environment_manager.visibility_system.visibility_radius > 0 else 8
                    )

                if event.key == pygame.K_a and self.current_state == GameState.PLAYING:
                    # Force monster adaptation
                    if self.monster:
                        self.monster._adapt_behavior()

                if event.key == pygame.K_p and self.current_state == GameState.PLAYING:
                    # Print AI performance metrics
                    ai_metrics = self.get_ai_performance_metrics()
                    print(f"Current AI Metrics: {ai_metrics}")

                if event.key == pygame.K_m and self.current_state == GameState.PLAYING:
                    # Toggle monster AI debug info
                    if hasattr(self, 'show_monster_debug'):
                        self.show_monster_debug = not self.show_monster_debug
                    else:
                        self.show_monster_debug = True

            # Let the UI manager handle events
            self.ui_manager.process_events(event)

    def update(self):
        """Update game state."""
        # Note: UI manager update is now handled in main.py to prevent conflicts
        # self.ui_manager.update(self.delta_time)

        if self.current_state == GameState.PLAYING:
            # Start AI calculation timing
            ai_start_time = time.time()

            # Update game components
            if self.player:
                self.player.update(self.delta_time)

                # Update target camera position to follow player
                self.target_camera_x = self.player.x - self.viewport_width // 2
                self.target_camera_y = self.player.y - self.viewport_height // 2

                # Smooth camera movement
                self.update_camera(self.player.x, self.player.y)

                # Update environment systems
                self.environment_manager.update(self.player.x, self.player.y, self.dungeon_map)

                # Apply environmental effects to player
                tile = self.get_tile_at(int(self.player.x), int(self.player.y))
                if tile:
                    environmental_damage = self.environment_manager.get_environmental_damage(
                        int(self.player.x), int(self.player.y), tile
                    )
                    if environmental_damage > 0:
                        self.player.take_damage(environmental_damage, damage_type="environmental")

            if self.monster:
                # Update monster with player state and dungeon map
                if not hasattr(self.monster, 'dungeon_map') or self.monster.dungeon_map is None:
                    self.monster.set_dungeon_map(self.dungeon_map)

                # Get player state for monster AI
                if self.player:
                    player_state = self.player.get_state()
                    self.monster.update(self.delta_time, player_state)

                    # Check for monster-player interaction
                    self._check_monster_player_interaction()

            if self.world:
                self.world.update(self.delta_time)

            # Record AI calculation time
            ai_end_time = time.time()
            self.ai_calculation_times.append(ai_end_time - ai_start_time)

            # Keep only last 100 calculations for monitoring
            if len(self.ai_calculation_times) > 100:
                self.ai_calculation_times.pop(0)

    def render(self):
        """Render the game state."""
        self.window_surface.fill((0, 0, 0))  # Clear screen

        if self.current_state == GameState.PLAYING:
            self._render_dungeon()
            self._render_entities()
        elif self.current_state == GameState.MENU:
            self._render_menu()
        elif self.current_state == GameState.PAUSED:
            self._render_dungeon()
            self._render_pause_overlay()
        elif self.current_state == GameState.GAME_OVER:
            self._render_game_over()

        # Draw UI elements
        self.ui_manager.draw_ui(self.window_surface)

        # Update display
        pygame.display.flip()

    def _render_dungeon(self):
        """Render the dungeon tiles."""
        # Calculate visible area
        start_x = max(0, int(self.camera_x))
        start_y = max(0, int(self.camera_y))
        end_x = min(self.dungeon_width, int(self.camera_x + self.viewport_width + 1))
        end_y = min(self.dungeon_height, int(self.camera_y + self.viewport_height + 1))

        # Draw visible tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.dungeon_map[y][x]
                if tile:
                    # Calculate screen position
                    screen_x = (x - self.camera_x) * self.tile_size
                    screen_y = (y - self.camera_y) * self.tile_size

                    # Draw tile
                    if tile.tile_type == TileType.WALL:
                        pygame.draw.rect(self.window_surface, (64, 64, 64),
                                      (screen_x, screen_y, self.tile_size, self.tile_size))
                    elif tile.tile_type == TileType.FLOOR:
                        pygame.draw.rect(self.window_surface, (32, 32, 32),
                                      (screen_x, screen_y, self.tile_size, self.tile_size))
                    elif tile.tile_type == TileType.DOOR:
                        pygame.draw.rect(self.window_surface, (139, 69, 19),
                                      (screen_x, screen_y, self.tile_size, self.tile_size))
                    elif tile.tile_type == TileType.TRAP:
                        pygame.draw.rect(self.window_surface, (128, 0, 0),  # Dark red for traps
                                      (screen_x, screen_y, self.tile_size, self.tile_size))
                    elif tile.tile_type == TileType.CHEST:
                        pygame.draw.rect(self.window_surface, (255, 215, 0),
                                      (screen_x, screen_y, self.tile_size, self.tile_size))

    def _render_entities(self):
        """Render game entities."""
        if self.player:
            # Draw player (green square)
            screen_x = (self.player.x - self.camera_x) * self.tile_size
            screen_y = (self.player.y - self.camera_y) * self.tile_size
            pygame.draw.rect(self.window_surface, (0, 255, 0),
                          (screen_x, screen_y, self.tile_size, self.tile_size))

            # Add "P" label to player
            font = pygame.font.Font(None, 24)
            text = font.render('P', True, (0, 0, 0))
            text_rect = text.get_rect(center=(screen_x + self.tile_size//2, screen_y + self.tile_size//2))
            self.window_surface.blit(text, text_rect)

        if self.monster:
            # Draw monster (purple circle to distinguish from red traps)
            screen_x = (self.monster.x - self.camera_x) * self.tile_size
            screen_y = (self.monster.y - self.camera_y) * self.tile_size
            center_x = screen_x + self.tile_size // 2
            center_y = screen_y + self.tile_size // 2
            radius = self.tile_size // 2 - 2

            # Draw purple circle for monster
            pygame.draw.circle(self.window_surface, (128, 0, 128), (center_x, center_y), radius)

            # Add "M" label to monster
            font = pygame.font.Font(None, 24)
            text = font.render('M', True, (255, 255, 255))
            text_rect = text.get_rect(center=(center_x, center_y))
            self.window_surface.blit(text, text_rect)

        # Draw legend in top-left corner
        self._draw_legend()

    def _draw_legend(self):
        """Draw a legend showing what each color represents."""
        font = pygame.font.Font(None, 20)
        y_offset = 10

        # Legend background
        legend_surface = pygame.Surface((200, 120))
        legend_surface.set_alpha(180)
        legend_surface.fill((0, 0, 0))
        self.window_surface.blit(legend_surface, (10, 10))

        # Legend items
        legend_items = [
            ("Green Square + P", (0, 255, 0), "Player"),
            ("Purple Circle + M", (128, 0, 128), "Monster"),
            ("Dark Red Square", (128, 0, 0), "Trap"),
            ("Gold Square", (255, 215, 0), "Chest"),
            ("Brown Square", (139, 69, 19), "Door"),
            ("Gray Square", (64, 64, 64), "Wall")
        ]

        for i, (label, color, description) in enumerate(legend_items):
            y_pos = 15 + i * 18

            # Draw color indicator
            if "Circle" in label:
                pygame.draw.circle(self.window_surface, color, (25, y_pos + 8), 6)
            else:
                pygame.draw.rect(self.window_surface, color, (20, y_pos, 12, 12))

            # Draw text
            text = font.render(f"{label}: {description}", True, (255, 255, 255))
            self.window_surface.blit(text, (40, y_pos))

    def _render_menu(self):
        """Render the main menu."""
        font = pygame.font.Font(None, 74)
        text = font.render('Dungeon Duo: Rough AI', True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.window_size[0]/2, self.window_size[1]/2))
        self.window_surface.blit(text, text_rect)

        font = pygame.font.Font(None, 36)
        text = font.render('Press SPACE to start', True, (200, 200, 200))
        text_rect = text.get_rect(center=(self.window_size[0]/2, self.window_size[1]/2 + 100))
        self.window_surface.blit(text, text_rect)

    def _render_pause_overlay(self):
        """Render pause screen overlay."""
        # Semi-transparent overlay
        overlay = pygame.Surface(self.window_size)
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.window_surface.blit(overlay, (0, 0))

        font = pygame.font.Font(None, 74)
        text = font.render('PAUSED', True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.window_size[0]/2, self.window_size[1]/2))
        self.window_surface.blit(text, text_rect)

    def _render_game_over(self):
        """Render game over screen."""
        font = pygame.font.Font(None, 74)
        text = font.render('GAME OVER', True, (255, 0, 0))
        text_rect = text.get_rect(center=(self.window_size[0]/2, self.window_size[1]/2))
        self.window_surface.blit(text, text_rect)

    def get_tile_at(self, x: int, y: int) -> Optional[Tile]:
        """Get tile at world coordinates."""
        ix, iy = int(x), int(y)
        if 0 <= ix < self.dungeon_width and 0 <= iy < self.dungeon_height:
            return self.dungeon_map[iy][ix]
        return None

    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if a position is valid (within bounds and not a wall)."""
        if x < 0 or y < 0 or x >= self.dungeon_width or y >= self.dungeon_height:
            return False
        return not self.dungeon_map[int(y)][int(x)].tile_type == TileType.WALL

    def get_spawn_position(self) -> Tuple[int, int]:
        """Get a valid spawn position."""
        return self.dungeon_generator.get_spawn_position()

    def get_monster_spawn_positions(self, count: int) -> List[Tuple[int, int]]:
        """Get valid spawn positions for monsters."""
        return self.dungeon_generator.get_monster_spawn_positions(count)

    def find_valid_monster_spawn(self) -> Optional[Tuple[int, int]]:
        """Find a valid spawn position for a monster."""
        # Try to find a position in a different room than the player
        player_room = None
        for room in self.dungeon_generator.rooms:
            if room.contains_point(int(self.player.x), int(self.player.y)):
                player_room = room
                break

        # Look for positions in other rooms
        for room in self.dungeon_generator.rooms:
            if room != player_room:
                # Try center of room
                if self.is_valid_position(room.center[0], room.center[1]):
                    return room.center

                # Try random positions in room
                for _ in range(10):
                    x = random.randint(room.x + 1, room.x + room.width - 2)
                    y = random.randint(room.y + 1, room.y + room.height - 2)
                    if self.is_valid_position(x, y):
                        return (x, y)

        # Fallback: find any walkable position
        for y in range(self.dungeon_height):
            for x in range(self.dungeon_width):
                if self.is_valid_position(x, y):
                    # Make sure it's not too close to player
                    distance = math.sqrt((x - self.player.x)**2 + (y - self.player.y)**2)
                    if distance > 10:
                        return (x, y)

        return None

    def _check_monster_player_interaction(self):
        """Check for interactions between monster and player."""
        print(f"[DEBUG] _check_monster_player_interaction: player.is_attacking={getattr(self.player, 'is_attacking', None)}, monster.is_attacking={getattr(self.monster, 'is_attacking', None)}")
        if not self.player or not self.monster:
            return

        # Calculate distance between monster and player
        dx = self.player.x - self.monster.x
        dy = self.player.y - self.monster.y
        distance = math.sqrt(dx * dx + dy * dy)

        # Check if monster is attacking player
        if self.monster.is_attacking and distance <= self.monster.stats.attack_range:
            self.combat_system.process_attack(self.monster, self.player, self.monster.equipped_weapon)

        # Check if player is attacking monster
        if hasattr(self.player, 'is_attacking') and self.player.is_attacking:
            if distance <= 50:  # Player attack range
                self.combat_system.process_attack(self.player, self.monster, self.player.equipped_weapon)

    def get_ai_performance_metrics(self) -> dict:
        """Get AI performance metrics for monitoring."""
        if self.monster:
            return self.monster.get_performance_metrics()
        return {}

    def update_camera(self, target_x: float, target_y: float):
        """Update camera position smoothly."""
        # Calculate target camera position (centered on target)
        self.target_camera_x = target_x - self.viewport_width // 2
        self.target_camera_y = target_y - self.viewport_height // 2

        # Smoothly move camera towards target
        self.camera_x += (self.target_camera_x - self.camera_x) * self.camera_speed
        self.camera_y += (self.target_camera_y - self.camera_y) * self.camera_speed

        # Ensure camera doesn't go out of bounds
        self.camera_x = max(0, min(self.camera_x, self.dungeon_width - self.viewport_width))
        self.camera_y = max(0, min(self.camera_y, self.dungeon_height - self.viewport_height))

    def run(self):
        """Run the main game loop."""
        self.running = True
        last_time = time.time()

        while self.running:
            # Calculate delta time
            current_time = time.time()
            self.delta_time = current_time - last_time
            last_time = current_time

            # Cap delta time to prevent large jumps
            self.delta_time = min(self.delta_time, 0.1)

            # Process events
            self.handle_events()

            # Update game state - this will call the enhanced_update function
            self.update()

            # Note: UI manager update and rendering are now handled in main.py to prevent conflicts
            # The built-in rendering methods are disabled to prevent conflicts

            # Cap framerate
            self.clock.tick(self.target_fps)

        # Cleanup
        pygame.quit()
