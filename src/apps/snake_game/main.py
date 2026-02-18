import sys
import pygame
from pathlib import Path
from src.apps.snake_game.snake import Snake
from src.apps.snake_game.food import Food
from src.apps.snake_game.constants import *

def game_loop():
    score = 0  # Initialize score
    """Main game loop with event handling."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # Asset paths need to be absolute or relative to CWD. 
    # Since we run from root, we can use src/apps/snake_game/assets/...
    base_path = Path("src/apps/snake_game/assets")
    
    background = None
    eat_sound = None
    game_over_sound = None

    try:
        background = pygame.image.load(base_path / 'graphics/background.png')
        eat_sound = pygame.mixer.Sound(base_path / 'sounds/eat.wav')
        game_over_sound = pygame.mixer.Sound(base_path / 'sounds/game_over.wav')
    except Exception as e:
        print(f"Warning: Could not load assets: {e}")
        # Fallback if assets missing
        if not background:
            background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            background.fill(COLOR_BLACK)

    pygame.display.set_caption('OpenClaw Mine - Snake')
    
    font = None
    large_font = None
    try:
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(None, 36)
        large_font = pygame.font.Font(None, 74)
    except Exception as e:
        print(f"Warning: Font module error, text will be disabled: {e}")

    snake = Snake(initial_position=[(10, 10)], board_size=(20, 15))
    
    # Re-implementing food logic
    # But wait, the original main.py used a tuple for food_position.
    food_position = (5, 5) 

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if game_over_sound: game_over_sound.play()
                running = False
            # Add keyboard control
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    snake.change_direction('UP')
                elif event.key == pygame.K_DOWN:
                    snake.change_direction('DOWN')
                elif event.key == pygame.K_LEFT:
                    snake.change_direction('LEFT')
                elif event.key == pygame.K_RIGHT:
                    snake.change_direction('RIGHT')

        # Draw
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(COLOR_BLACK)

        # Move
        try:
            snake.move()
        except Exception:
            pass # Handle move errors gracefully

        # Check collisions
        if snake.check_self_collision() or snake.check_wall_collision():
            show_game_over_screen(screen, score, large_font, font)
            running = False

        # Check food
        if snake.has_eaten_food(food_position):
            score += 1
            snake.grow()
            if eat_sound: eat_sound.play()
            # Simple random food (should use Food class if available)
            import random
            food_position = (random.randint(0, 19), random.randint(0, 14))

        # Score
        if font:
            text = font.render(f'Score: {score}', True, COLOR_WHITE)
            screen.blit(text, (10, 10))

        # Update
        pygame.display.flip()
        pygame.time.Clock().tick(INITIAL_GAME_SPEED)

    pygame.quit()

def show_game_over_screen(screen, score, font_large, font_small):
    """Display the Game Over screen."""
    if font_large:
        text = font_large.render('Game Over', True, (255, 0, 0))
        screen.blit(text, (250, 250))
    
    if font_small:
        score_text = font_small.render(f'Final Score: {score}', True, (255, 255, 255))
        screen.blit(score_text, (300, 320))

        restart_text = font_small.render('Press R to Restart or Q to Quit', True, (255, 255, 255))
        screen.blit(restart_text, (200, 380))

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting = False
                    game_loop()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
