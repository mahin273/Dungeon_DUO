import pygame
import pygame_gui
from src.game.game_engine import GameEngine, GameState
from src.game.player import Player
from src.game.monster import Monster
from src.game.combat import CombatSystem
from src.game.inventory import ItemFactory, LootTable
from src.game.quests import QuestManager, create_sample_quests, Quest
from src.ui.renderer import GameRenderer
from src.ui.hud import ModernHUDManager
from src.world.tile import TileType
import math
import json
import os

def main():
    """Main function to start the Dungeon Duo game."""
    # Initialize game engine
    engine = GameEngine()

    # Persistent adaptation level file
    adaptation_file = os.path.join(os.path.dirname(__file__), 'monster_learning.json')
    adaptation_level = 0
    # Load adaptation level if file exists
    if os.path.exists(adaptation_file):
        try:
            with open(adaptation_file, 'r') as f:
                data = json.load(f)
                adaptation_level = data.get('adaptation_level', 0)
                print(f"Loaded monster adaptation level: {adaptation_level}")
        except Exception as e:
            print(f"Failed to load adaptation level: {e}")

    # Generate the dungeon world
    print("Initializing Dungeon Duo: Rough AI...")
    spawn_position = engine.generate_world()

    # Initialize game components with proper spawn positions
    player = Player(x=spawn_position[0], y=spawn_position[1])
    print(f"Player created at position: ({player.x}, {player.y})")

    # Get monster spawn positions and create monster with better validation
    monster_spawns = engine.get_monster_spawn_positions(1)
    monster = None

    if monster_spawns:
        # Validate the spawn position is actually walkable
        spawn_x, spawn_y = monster_spawns[0]
        if engine.is_valid_position(spawn_x, spawn_y):
            monster = Monster(x=spawn_x, y=spawn_y, dungeon_map=engine.dungeon_map)
            print(f"Monster created at position: ({monster.x}, {monster.y})")
            monster.adaptation_level = adaptation_level
        else:
            print(f"Invalid monster spawn position: ({spawn_x}, {spawn_y})")

    if not monster:
        # Find a valid fallback position
        fallback_pos = engine.find_valid_monster_spawn()
        if fallback_pos:
            monster = Monster(x=fallback_pos[0], y=fallback_pos[1], dungeon_map=engine.dungeon_map)
            print(f"Monster created at fallback position: ({monster.x}, {monster.y})")
            monster.adaptation_level = adaptation_level
        else:
            # Last resort - spawn near player but not too close
            monster = Monster(x=spawn_position[0] + 15, y=spawn_position[1] + 15, dungeon_map=engine.dungeon_map)
            print(f"Monster created at emergency position: ({monster.x}, {monster.y})")
            monster.adaptation_level = adaptation_level

    # Ensure monster pathfinder is initialized
    monster.set_dungeon_map(engine.dungeon_map)
    print(f"Monster pathfinder initialized: {hasattr(monster, 'pathfinder') and monster.pathfinder is not None}")

    # Initialize enhanced combat system
    combat_system = CombatSystem()

    # Initialize item factory and loot table
    item_factory = ItemFactory()
    loot_table = LootTable(item_factory)

    # Give player initial equipment
    iron_sword = combat_system.create_weapon("iron_sword")
    leather_armor = combat_system.create_armor("leather_armor")
    if iron_sword:
        player.add_weapon_to_inventory(iron_sword)
        player.equip_weapon(iron_sword)
    if leather_armor:
        player.add_armor_to_inventory(leather_armor)
        player.equip_armor(leather_armor)

    # Give player some starting items
    health_potion = item_factory.create_consumable("health_potion")
    mana_potion = item_factory.create_consumable("mana_potion")
    if health_potion:
        player.add_item_to_inventory(health_potion)
    if mana_potion:
        player.add_item_to_inventory(mana_potion)

    # Give monster initial equipment
    fire_staff = combat_system.create_weapon("fire_staff")
    iron_armor = combat_system.create_armor("iron_armor")
    if fire_staff:
        monster.add_weapon_to_inventory(fire_staff)
        monster.equip_weapon(fire_staff)
    if iron_armor:
        monster.add_armor_to_inventory(iron_armor)
        monster.equip_armor(iron_armor)

    # Connect AI learning system to player events
    def handle_player_event(event_data):
        if monster:
            monster.update(0.0, event_data)  # Pass 0.0 as delta_time since this is event-based

    player.add_event_handler("movement", handle_player_event)
    player.add_event_handler("attack", handle_player_event)
    player.add_event_handler("dodge", handle_player_event)

    # Add player movement validation against dungeon walls
    def validate_player_movement(new_x, new_y):
        return engine.is_valid_position(new_x, new_y)

    player.set_movement_validator(validate_player_movement)

    # Store components in game engine
    engine.player = player
    engine.monster = monster
    engine.combat_system = combat_system

    # Set initial game state
    engine.current_state = GameState.PLAYING

    # Set up pygame_gui manager with theme
    pygame.init()
    window_size = (1280, 720)
    screen = pygame.display.set_mode(window_size, pygame.DOUBLEBUF)
    pygame.display.set_caption("Dungeon Duo: Rough AI")

    ui_theme = {
        "defaults": {
            "colours": {
                "normal_bg": "#45494e",
                "hovered_bg": "#35393e",
                "disabled_bg": "#25292e",
                "selected_bg": "#193754",
                "dark_bg": "#15191e",
                "normal_text": "#c5cbd8",
                "hovered_text": "#FFFFFF",
                "selected_text": "#FFFFFF",
                "disabled_text": "#6d736f",
                "link_text": "#0000EE",
                "link_hover": "#2020FF",
                "link_selected": "#551A8B",
                "text_shadow": "#777777",
                "normal_border": "#DDDDDD",
                "hovered_border": "#B0B0B0",
                "disabled_border": "#808080",
                "selected_border": "#8080B0",
                "active_border": "#8080B0",
                "filled_bar": "#f4251b",
                "unfilled_bar": "#CCCCCC"
            }
        }
    }
    manager = pygame_gui.UIManager(window_size, ui_theme)

    # Update the game engine to use the same screen surface
    engine.window_surface = screen
    engine.window_size = window_size

    # Initialize quest and achievement managers
    quest_manager = QuestManager()
    for quest in create_sample_quests():
        quest_manager.add_quest(quest)

    # Initialize renderer and HUD
    renderer = GameRenderer(screen, manager)
    hud_manager = ModernHUDManager(manager, player, quest_manager)

    # Treasure counting logic
    total_treasures = 0
    collected_treasures = 0

    # Count total treasures in the dungeon
    for y in range(len(engine.dungeon_map)):
        for x in range(len(engine.dungeon_map[0])):
            if engine.dungeon_map[y][x].tile_type == TileType.CHEST:
                total_treasures += 1

    # Override the engine's handle_events to include player input
    original_handle_events = engine.handle_events

    # Movement state for continuous movement
    movement_keys_held = {'up': False, 'down': False, 'left': False, 'right': False}
    movement_cooldown = 100  # milliseconds between moves when holding a key
    last_move_time = 0

    def enhanced_handle_events():
        nonlocal collected_treasures
        for event in pygame.event.get():
            # Reset movement keys if window focus is lost
            if event.type == pygame.ACTIVEEVENT:
                if hasattr(event, 'state') and event.state == 2 and event.gain == 0:
                    for key in movement_keys_held:
                        movement_keys_held[key] = False
            if hasattr(pygame, 'WINDOWFOCUSLOST') and event.type == pygame.WINDOWFOCUSLOST:
                for key in movement_keys_held:
                    movement_keys_held[key] = False
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_w, pygame.K_UP):
                    movement_keys_held['up'] = True
                    player.move(0, -1)  # Single-step move
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    movement_keys_held['down'] = True
                    player.move(0, 1)   # Single-step move
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    movement_keys_held['left'] = True
                    player.move(-1, 0)  # Single-step move
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    movement_keys_held['right'] = True
                    player.move(1, 0)   # Single-step move
                elif event.key == pygame.K_m:
                    renderer.toggle_minimap()
                elif event.key == pygame.K_e:
                    # Interact with objects (chests, doors, health quest)
                    px, py = int(player.x), int(player.y)
                    tile = engine.dungeon_map[py][px]
                    if tile.tile_type == TileType.CHEST:
                        result = tile.interact()
                        if result.get('type') == 'chest_opened':
                            collected_treasures += 1
                            print(f'Treasure collected! ({collected_treasures}/{total_treasures})')
                    elif tile.tile_type == TileType.HEALTH_QUEST:
                        result = tile.interact(player)
                        if result.get('type') == 'health_quest_consumed':
                            print('Health quest consumed! +10 health.')
                        elif result.get('type') == 'health_quest_full_health':
                            print('Cannot consume health quest: health is already full.')
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_w, pygame.K_UP):
                    movement_keys_held['up'] = False
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    movement_keys_held['down'] = False
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    movement_keys_held['left'] = False
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    movement_keys_held['right'] = False
            hud_manager.process_event(event)
            manager.process_events(event)
        original_handle_events()
        if engine.current_state == GameState.PLAYING:
            pass

    engine.handle_events = enhanced_handle_events

    # Add game state transitions and loot drops
    def check_game_state():
        if player.stats.health <= 0:
            engine.current_state = GameState.GAME_OVER
            print("Game Over! Player defeated.")
        elif monster.stats.health <= 0:
            print("Victory! Monster defeated.")

            # Generate loot drop
            difficulty = monster.adaptation_level + 1
            loot_items = loot_table.generate_loot(difficulty, num_items=random.randint(1, 3))
            gold_drop = loot_table.generate_gold_drop(difficulty)

            print(f"Monster dropped {gold_drop} gold!")
            player.inventory.gold += gold_drop

            for item in loot_items:
                if player.add_item_to_inventory(item):
                    print(f"Found {item.name} ({item.rarity.value})!")

            # Could restart or continue to next level
            print("Press R to regenerate dungeon with new monster!")

    # Add state checking to update loop
    original_update = engine.update

    def enhanced_update():
        original_update()
        check_game_state()

        # Continuous movement logic with cooldown
        nonlocal last_move_time
        move_x = 0
        move_y = 0
        if movement_keys_held['up']:
            move_y -= 1
        if movement_keys_held['down']:
            move_y += 1
        if movement_keys_held['left']:
            move_x -= 1
        if movement_keys_held['right']:
            move_x += 1
        if (move_x != 0 or move_y != 0):
            now = pygame.time.get_ticks()
            if now - last_move_time >= movement_cooldown:
                player.move(move_x, move_y)
                last_move_time = now

        # Check for environmental damage (e.g., traps)
        player_tile = engine.dungeon_map[int(player.y)][int(player.x)]
        env_damage = engine.environment_manager.get_environmental_damage(int(player.x), int(player.y), player_tile)
        if env_damage > 0:
            player.take_damage(env_damage, "environmental")

        # Update special effects for both player and monster
        if player:
            combat_system.update_special_effects(player)
        if monster:
            combat_system.update_special_effects(monster)

        # Update HUD manager with delta time
        hud_manager.update(engine.delta_time)

        # Update UI manager
        manager.update(engine.delta_time)

        # Monitor AI performance
        ai_metrics = engine.get_ai_performance_metrics()
        if ai_metrics and len(ai_metrics) > 0:
            # Print AI metrics every 500 frames (roughly every 8 seconds at 60 FPS)
            if hasattr(enhanced_update, 'frame_count'):
                enhanced_update.frame_count += 1
            else:
                enhanced_update.frame_count = 0

            if enhanced_update.frame_count % 500 == 0:
                print(f"AI Performance - Adaptation Level: {ai_metrics.get('adaptation_level', 0)}, "
                      f"Avg Decision Time: {ai_metrics.get('avg_decision_time', 0)*1000:.2f}ms, "
                      f"Success Rates: {ai_metrics.get('success_rates', {})}")

        # Debug: Print game state and entity positions (reduced frequency)
        if not hasattr(enhanced_update, 'debug_frame_count'):
            enhanced_update.debug_frame_count = 0
        enhanced_update.debug_frame_count += 1

        if enhanced_update.debug_frame_count % 600 == 0:  # Every 10 seconds (60 FPS * 10)
            print(f"=== GAME STATUS ===")
            print(f"Player: ({player.x:.1f}, {player.y:.1f}) HP: {player.stats.health}/{player.stats.max_health}")
            print(f"Monster: ({monster.x:.1f}, {monster.y:.1f}) HP: {monster.stats.health}/{monster.stats.max_health}")
            print(f"Distance: {math.sqrt((player.x - monster.x)**2 + (player.y - monster.y)**2):.1f}")
            print("==================")

        # Clear screen and render the frame using GameRenderer
        screen.fill((0, 0, 0))  # Clear screen
        fps = engine.clock.get_fps()
        renderer.render_frame(engine, player, monster, engine.delta_time, fps, ai_metrics,
                            treasure_info={'collected': collected_treasures, 'total': total_treasures})

        # Draw UI elements
        manager.draw_ui(screen)

        # Render HUD notifications
        hud_manager.render_notifications(screen)

        # Update display
        pygame.display.flip()

    engine.update = enhanced_update

    # Print game instructions
    print("\n=== Dungeon Duo: Rough AI ===")

    # Debug: Count and show chest locations
    chest_count = 0
    chest_locations = []
    for y in range(len(engine.dungeon_map)):
        for x in range(len(engine.dungeon_map[0])):
            if engine.dungeon_map[y][x].tile_type == TileType.CHEST:
                chest_count += 1
                chest_locations.append((x, y))
    print(f"DEBUG: Found {chest_count} chests in the dungeon at locations: {chest_locations}")

    print("Controls:")
    print("  WASD or Arrow Keys: Move player")
    print("  SPACE: Attack")
    print("  E: Interact with objects (chests, doors)")
    print("  1-9: Use items from inventory slots")
    print("  ESC: Exit game")
    print("  R: Regenerate dungeon")
    print("  T: Toggle visibility")
    print("\nGame Features:")
    print("  - Procedural dungeon generation")

    print("  - AI monster with learning capabilities")
    print("  - Adaptive AI behavior prediction")
    print("  - A* pathfinding for monster movement")
    print("  - Tactical AI decision making")

    print("\nStarting game...")

    # Save adaptation level at the end of the game
    def save_adaptation_level():
        if monster:
            try:
                with open(adaptation_file, 'w') as f:
                    json.dump({'adaptation_level': monster.adaptation_level}, f)
                print(f"Saved monster adaptation level: {monster.adaptation_level}")
            except Exception as e:
                print(f"Failed to save adaptation level: {e}")

    # Patch engine.run to save adaptation level on exit
    original_run = engine.run
    def patched_run(*args, **kwargs):
        try:
            original_run(*args, **kwargs)
        finally:
            save_adaptation_level()
    engine.run = patched_run

    # Start game loop
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
    except Exception as e:
        print(f"Game error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Game ended.")

if __name__ == "__main__":
    main()
