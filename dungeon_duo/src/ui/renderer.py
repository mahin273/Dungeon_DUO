"""
renderer.py

Rendering logic for Dungeon Duo: Rough AI.
Handles drawing of game world, entities, and UI overlays.
"""

import pygame
import pygame_gui
import math
from typing import Dict, Any, Optional, Tuple
from ..game.game_engine import GameEngine
from ..game.player import Player
from ..game.monster import Monster
from ..world.tile import TileType

class GameRenderer:
    """Handles all rendering for the game."""

    def __init__(self, screen: pygame.Surface, ui_manager: pygame_gui.UIManager):
        self.screen = screen
        self.ui_manager = ui_manager

        # Enhanced fonts with better sizing
        self.title_font = pygame.font.Font(None, 36)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.tiny_font = pygame.font.Font(None, 14)

        # Modern color palette with gradients
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.DARK_GRAY = (32, 32, 32)
        self.GRAY = (64, 64, 64)
        self.LIGHT_GRAY = (128, 128, 128)

        # Primary colors
        self.RED = (255, 50, 50)
        self.GREEN = (50, 255, 50)
        self.BLUE = (50, 150, 255)
        self.YELLOW = (255, 255, 50)
        self.PURPLE = (150, 50, 255)
        self.ORANGE = (255, 150, 50)
        self.CYAN = (50, 255, 255)

        # UI Colors
        self.UI_BG = (20, 20, 30)
        self.UI_PANEL = (40, 40, 60)
        self.UI_BORDER = (80, 80, 120)
        self.UI_HIGHLIGHT = (100, 100, 150)
        self.UI_TEXT = (220, 220, 240)
        self.UI_TEXT_DIM = (150, 150, 170)

        # Nord color palette
        # https://www.nordtheme.com/docs/colors-and-palettes
        self.WALL_COLOR = (32, 36, 44)      # Very dark Nord wall
        self.WALL_HIGHLIGHT = (67, 76, 94)       # nord4
        self.FLOOR_COLOR = (67, 76, 94)    # Nord4
        self.FLOOR_HIGHLIGHT = (229, 233, 240)   # nord5
        self.DOOR_COLOR = (94, 129, 172)         # nord9
        self.DOOR_HIGHLIGHT = (136, 192, 208)    # nord8
        self.TRAP_COLOR = (10, 10, 80)        # Dark blue
        self.TRAP_HIGHLIGHT = (30, 30, 120)   # Slightly lighter blue
        self.CHEST_COLOR = (255, 255, 0)      # Yellow
        self.CHEST_HIGHLIGHT = (255, 255, 128)# Light yellow
        self.TILE_BORDER_COLOR = (40, 40, 40) # Neutral border

        # Entity colors with Nord harmony
        self.PLAYER_COLOR = (0, 255, 0)       # Green
        self.PLAYER_GLOW = (0, 255, 128)      # Light green glow
        self.MONSTER_COLOR = (255, 0, 0)      # Red
        self.MONSTER_GLOW = (255, 128, 128)   # Light red glow

        # Health bar colors
        self.HEALTH_BAR_BG = (60, 20, 20)
        self.HEALTH_BAR_FG = (40, 200, 40)
        self.HEALTH_BAR_BORDER = (100, 100, 100)
        self.HEALTH_BAR_LOW = (200, 40, 40)

        # Rendering settings
        self.tile_size = 32
        self.player_size = 24
        self.monster_size = 24
        self.view_padding = 5

        # Animation variables
        self.animation_time = 0
        self.pulse_animation = 0

        # Particle effects
        self.particles = []

        # UI state
        self.show_minimap = True
        self.show_debug_info = False

        # Add attributes to track game over and victory state
        self.game_over = False
        self.victory = False

    def render_frame(self, engine: GameEngine, player: Player, monster: Optional[Monster], delta_time: float, fps: float, ai_metrics: Dict = None, treasure_info: Dict = None):
        """Render a complete frame with enhanced visuals."""
        # Update animation time
        self.animation_time += delta_time
        self.pulse_animation = math.sin(self.animation_time * 3) * 0.5 + 0.5

        # Update particles
        self._update_particles(delta_time)

        # Fill background with pure black for outside/void
        self.screen.fill((0, 0, 0))  # Pure black

        # Use engine's camera position
        camera_x = int(engine.camera_x)
        camera_y = int(engine.camera_y)

        # Calculate view bounds
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        view_width = screen_width // self.tile_size
        view_height = screen_height // self.tile_size

        # Render world with enhanced visuals
        self._render_world(engine, camera_x, camera_y, view_width, view_height)

        # Render entities with effects
        self._render_entities(player, monster, camera_x, camera_y)

        # Render particles
        self._render_particles()

        # Render UI overlays
        self._render_ui_overlays(player, monster, fps, ai_metrics, treasure_info)

        # Render minimap
        if self.show_minimap:
            self._render_minimap(engine, player, monster)

        # Render debug info
        if self.show_debug_info:
            self._render_debug_info(engine, player, monster, fps, ai_metrics)

        # Render end screen if game over or victory
        if self.game_over or self.victory:
            self._render_end_screen()

    def _draw_background_gradient(self):
        """Draw a subtle gradient background."""
        height = self.screen.get_height()
        for y in range(height):
            # Create a subtle dark gradient from top to bottom
            intensity = int(20 + (y / height) * 10)
            color = (intensity, intensity, intensity + 10)
            pygame.draw.line(self.screen, color, (0, y), (self.screen.get_width(), y))

    def _render_world(self, engine: GameEngine, camera_x: int, camera_y: int, view_width: int, view_height: int):
        """Render walls and floors with dark Nord colors, then traps and treasures on top."""
        for y in range(max(0, camera_y), min(len(engine.dungeon_map), camera_y + view_height + 1)):
            for x in range(max(0, camera_x), min(len(engine.dungeon_map[0]), camera_x + view_width + 1)):
                tile = engine.dungeon_map[y][x]
                screen_x = (x - camera_x) * self.tile_size
                screen_y = (y - camera_y) * self.tile_size
                # Draw wall or floor
                if tile.tile_type == TileType.WALL:
                    pygame.draw.rect(self.screen, self.WALL_COLOR, (screen_x, screen_y, self.tile_size, self.tile_size))
                else:
                    pygame.draw.rect(self.screen, self.FLOOR_COLOR, (screen_x, screen_y, self.tile_size, self.tile_size))
                # Draw trap, treasure, or health quest on top
                if tile.tile_type == TileType.TRAP:
                    pygame.draw.rect(self.screen, self.TRAP_COLOR, (screen_x, screen_y, self.tile_size, self.tile_size))
                elif tile.tile_type == TileType.CHEST:
                    pygame.draw.rect(self.screen, self.CHEST_COLOR, (screen_x, screen_y, self.tile_size, self.tile_size))
                elif tile.tile_type == TileType.HEALTH_QUEST:
                    pygame.draw.rect(self.screen, (255, 140, 0), (screen_x, screen_y, self.tile_size, self.tile_size))
                    h_surface = self.tiny_font.render("H", True, (255, 255, 255))
                    h_rect = h_surface.get_rect(center=(screen_x + self.tile_size // 2, screen_y + self.tile_size // 2))
                    self.screen.blit(h_surface, h_rect)

    def _render_entities(self, player: Player, monster: Optional[Monster], camera_x: int, camera_y: int):
        """Render only player (green circle) and monster (red circle)."""
        # Player
        player_screen_x = (player.x - camera_x) * self.tile_size + self.tile_size // 2
        player_screen_y = (player.y - camera_y) * self.tile_size + self.tile_size // 2
        pygame.draw.circle(self.screen, self.PLAYER_COLOR, (player_screen_x, player_screen_y), self.player_size // 2)
        # Monster
        if monster:
            monster_screen_x = (monster.x - camera_x) * self.tile_size + self.tile_size // 2
            monster_screen_y = (monster.y - camera_y) * self.tile_size + self.tile_size // 2
            pygame.draw.circle(self.screen, self.MONSTER_COLOR, (monster_screen_x, monster_screen_y), self.monster_size // 2)

    def _render_health_bar(self, x: int, y: int, current_health: float, max_health: float, label: str):
        """Render a health bar with enhanced visuals."""
        bar_width = 32
        bar_height = 4

        # Background
        pygame.draw.rect(self.screen, self.HEALTH_BAR_BG, (x, y, bar_width, bar_height))

        # Health fill
        health_ratio = max(0, min(1, current_health / max_health))
        fill_width = int(bar_width * health_ratio)

        if health_ratio > 0.5:
            fill_color = self.HEALTH_BAR_FG
        else:
            fill_color = self.HEALTH_BAR_LOW

        if fill_width > 0:
            pygame.draw.rect(self.screen, fill_color, (x, y, fill_width, bar_height))

        # Border
        pygame.draw.rect(self.screen, self.HEALTH_BAR_BORDER, (x, y, bar_width, bar_height), 1)

        # Health text
        health_text = f"{int(current_health)}/{int(max_health)}"
        text_surface = self.tiny_font.render(health_text, True, self.WHITE)
        text_rect = text_surface.get_rect(center=(x + bar_width // 2, y + bar_height + 8))
        self.screen.blit(text_surface, text_rect)

    def _render_ui_overlays(self, player: Player, monster: Optional[Monster], fps: float, ai_metrics: Dict = None, treasure_info: Dict = None):
        """Render UI overlays with modern design."""
        # Player stats panel
        self._render_player_stats_panel(player, treasure_info)

        # Combat info panel
        if monster:
            self._render_combat_panel(player, monster)

        # FPS counter
        self._render_fps_counter(fps)

        # AI metrics panel
        if ai_metrics:
            self._render_ai_metrics_panel(ai_metrics)

    def _render_player_stats_panel(self, player: Player, treasure_info: Dict = None):
        """Render player stats in a modern panel."""
        panel_x = 10
        panel_y = 10
        panel_width = 200
        panel_height = 140  # Increased height to accommodate treasure counter

        # Panel background with transparency effect
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill(self.UI_PANEL)
        self.screen.blit(panel_surface, (panel_x, panel_y))

        # Panel border
        pygame.draw.rect(self.screen, self.UI_BORDER, (panel_x, panel_y, panel_width, panel_height), 2)

        # Title
        title_text = self.font.render("Player Stats", True, self.UI_TEXT)
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))

        # Stats
        stats_y = panel_y + 40
        stats = [
            f"Health: {int(player.stats.health)}/{int(player.stats.max_health)}",
            f"Attack: {player.stats.attack}",
            f"Defense: {player.stats.defense}",
            f"Speed: {player.stats.speed}"
        ]

        for i, stat in enumerate(stats):
            stat_text = self.small_font.render(stat, True, self.UI_TEXT)
            self.screen.blit(stat_text, (panel_x + 10, stats_y + i * 18))

        # Treasure counter with background highlight
        if treasure_info:
            treasure_text = f"Treasure: {treasure_info['collected']}/{treasure_info['total']}"
            treasure_surface = self.small_font.render(treasure_text, True, self.YELLOW)

            # Add a semi-transparent background for the treasure counter
            text_rect = treasure_surface.get_rect()
            text_rect.topleft = (panel_x + 10, panel_y + panel_height - 30)

            # Background rectangle for treasure counter
            bg_rect = pygame.Rect(panel_x + 8, panel_y + panel_height - 32, text_rect.width + 4, text_rect.height + 4)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.set_alpha(150)
            bg_surface.fill((20, 20, 20))  # Dark background
            self.screen.blit(bg_surface, bg_rect)

            # Draw treasure counter text
            self.screen.blit(treasure_surface, text_rect)

    def _render_combat_panel(self, player: Player, monster: Monster):
        """Render combat information panel."""
        panel_x = self.screen.get_width() - 210
        panel_y = 10
        panel_width = 200
        panel_height = 100

        # Panel background
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill(self.UI_PANEL)
        self.screen.blit(panel_surface, (panel_x, panel_y))

        # Panel border
        pygame.draw.rect(self.screen, self.UI_BORDER, (panel_x, panel_y, panel_width, panel_height), 2)

        # Title
        title_text = self.font.render("Combat", True, self.UI_TEXT)
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))

        # Distance to monster
        distance = math.sqrt((player.x - monster.x)**2 + (player.y - monster.y)**2)
        distance_text = self.small_font.render(f"Distance: {distance:.1f}", True, self.UI_TEXT)
        self.screen.blit(distance_text, (panel_x + 10, panel_y + 35))

        # Monster health
        monster_health_text = self.small_font.render(f"Monster HP: {int(monster.stats.health)}", True, self.UI_TEXT)
        self.screen.blit(monster_health_text, (panel_x + 10, panel_y + 55))

    def _render_fps_counter(self, fps: float):
        """Render FPS counter."""
        fps_text = self.small_font.render(f"FPS: {fps:.1f}", True, self.UI_TEXT_DIM)
        self.screen.blit(fps_text, (self.screen.get_width() - 80, self.screen.get_height() - 25))

    def _render_ai_metrics_panel(self, ai_metrics: Dict):
        """Render AI performance metrics."""
        panel_x = 10
        panel_y = self.screen.get_height() - 150
        panel_width = 250
        panel_height = 140

        # Panel background
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill(self.UI_PANEL)
        self.screen.blit(panel_surface, (panel_x, panel_y))

        # Panel border
        pygame.draw.rect(self.screen, self.UI_BORDER, (panel_x, panel_y, panel_width, panel_height), 2)

        # Title
        title_text = self.font.render("AI Performance", True, self.UI_TEXT)
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))

        # Metrics
        metrics_y = panel_y + 35
        adaptation = ai_metrics.get('adaptation_level', 0)
        decision_time = ai_metrics.get('avg_decision_time', 0) * 1000

        adaptation_text = self.small_font.render(f"Adaptation: {adaptation:.1f}", True, self.UI_TEXT)
        self.screen.blit(adaptation_text, (panel_x + 10, metrics_y))

        decision_text = self.small_font.render(f"Decision Time: {decision_time:.2f}ms", True, self.UI_TEXT)
        self.screen.blit(decision_text, (panel_x + 10, metrics_y + 20))

    def _render_minimap(self, engine: GameEngine, player: Player, monster: Optional[Monster]):
        """Render a minimap in the corner."""
        minimap_size = 150
        minimap_x = self.screen.get_width() - minimap_size - 10
        minimap_y = self.screen.get_height() - minimap_size - 10

        # Minimap background
        pygame.draw.rect(self.screen, self.UI_PANEL, (minimap_x, minimap_y, minimap_size, minimap_size))
        pygame.draw.rect(self.screen, self.UI_BORDER, (minimap_x, minimap_y, minimap_size, minimap_size), 2)

        # Calculate minimap scale
        map_width = len(engine.dungeon_map[0])
        map_height = len(engine.dungeon_map)
        scale_x = minimap_size / map_width
        scale_y = minimap_size / map_height
        scale = min(scale_x, scale_y)

        # Draw dungeon tiles
        for y in range(map_height):
            for x in range(map_width):
                tile = engine.dungeon_map[y][x]
                if tile.tile_type == TileType.WALL:
                    color = self.WALL_COLOR
                elif tile.tile_type == TileType.HEALTH_QUEST:
                    color = (255, 140, 0)
                else:
                    color = self.FLOOR_COLOR

                pixel_x = minimap_x + x * scale
                pixel_y = minimap_y + y * scale
                pixel_size = max(1, int(scale))

                pygame.draw.rect(self.screen, color, (pixel_x, pixel_y, pixel_size, pixel_size))

        # Draw player
        player_pixel_x = minimap_x + player.x * scale
        player_pixel_y = minimap_y + player.y * scale
        pygame.draw.circle(self.screen, self.PLAYER_COLOR, (int(player_pixel_x), int(player_pixel_y)), 2)

        # Draw monster
        if monster:
            monster_pixel_x = minimap_x + monster.x * scale
            monster_pixel_y = minimap_y + monster.y * scale
            pygame.draw.circle(self.screen, self.MONSTER_COLOR, (int(monster_pixel_x), int(monster_pixel_y)), 2)

    def _render_debug_info(self, engine: GameEngine, player: Player, monster: Optional[Monster], fps: float, ai_metrics: Dict = None):
        """Render debug information."""
        debug_y = 140
        debug_info = [
            f"Player: ({player.x:.1f}, {player.y:.1f})",
            f"Camera: ({engine.camera_x:.1f}, {engine.camera_y:.1f})",
            f"FPS: {fps:.1f}",
            f"Screen: {self.screen.get_width()}x{self.screen.get_height()}"
        ]

        if monster:
            debug_info.append(f"Monster: ({monster.x:.1f}, {monster.y:.1f})")

        for i, info in enumerate(debug_info):
            debug_text = self.tiny_font.render(info, True, self.UI_TEXT_DIM)
            self.screen.blit(debug_text, (10, debug_y + i * 15))

    def _update_particles(self, delta_time: float):
        """Update particle effects."""
        # Remove expired particles
        self.particles = [p for p in self.particles if p['life'] > 0]

        # Update remaining particles
        for particle in self.particles:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['life'] -= delta_time

    def _render_particles(self):
        """Render particle effects."""
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            rgb_color = particle['color'][:3]  # Only use RGB for fill

            # Create a larger surface for the particle with alpha
            particle_size = 6  # Increased from 4 to 6 pixels
            particle_surface = pygame.Surface((particle_size, particle_size), pygame.SRCALPHA)
            particle_surface.set_alpha(alpha)
            particle_surface.fill(rgb_color)
            self.screen.blit(particle_surface, (particle['x'] - particle_size//2, particle['y'] - particle_size//2))

    def add_particle_effect(self, x: float, y: float, color: Tuple[int, int, int], velocity: Tuple[float, float], life: float = 1.0):
        """Add a particle effect."""
        # Debug print to confirm particles are being created
        print(f"DEBUG: Creating particle at ({x}, {y}) with color {color}, velocity {velocity}, life {life}")
        self.particles.append({
            'x': x,
            'y': y,
            'vx': velocity[0],
            'vy': velocity[1],
            'color': color,
            'life': life,
            'max_life': life
        })

    def toggle_minimap(self):
        """Toggle minimap visibility."""
        self.show_minimap = not self.show_minimap

    def toggle_debug_info(self):
        """Toggle debug information visibility."""
        self.show_debug_info = not self.show_debug_info

    def _draw_tile_label(self, x: int, y: int, tile_type: TileType):
        """Draw a letter label on important tiles for easy identification."""
        # Define labels for important tiles only (no walls or floors)
        labels = {
            TileType.CHEST: "C",
            TileType.TRAP: "T",
            TileType.DOOR: "D",
            TileType.STAIRS_UP: "↑",
            TileType.STAIRS_DOWN: "↓"
        }

        if tile_type in labels:
            label_surface = self.tiny_font.render(labels[tile_type], True, (255, 255, 255))  # White text
            label_rect = label_surface.get_rect(center=(x + self.tile_size // 2, y + self.tile_size // 2))
            self.screen.blit(label_surface, label_rect)

    def show_game_over(self):
        """Set game over state."""
        self.game_over = True

    def show_victory(self):
        """Set victory state."""
        self.victory = True

    def _render_end_screen(self):
        """Render end screen."""
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((20, 20, 40, 200))  # Semi-transparent dark overlay
        self.screen.blit(overlay, (0, 0))

        if self.victory:
            text = "Victory! You collected all treasures!"
            color = (255, 215, 0)
        elif self.game_over:
            text = "Game Over! You died."
            color = (255, 80, 80)
        else:
            return

        font = pygame.font.Font(None, 80)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        self.screen.blit(text_surface, text_rect)
