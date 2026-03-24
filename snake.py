import pygame
import random
import config
import sys

# Inizializza pygame
pygame.init()
pygame.mixer.init()

# Dimensioni celle in pixel
CELL_SIZE = 20

# Colori (RGB)
color_map = {
    'BLACK': (0, 0, 0),
    'BLUE': (0, 0, 255),
    'CYAN': (0, 255, 255),
    'GREEN': (0, 255, 0),
    'MAGENTA': (255, 0, 255),
    'RED': (255, 0, 0),
    'WHITE': (255, 255, 255),
    'YELLOW': (255, 255, 0),
    'PINK': (255, 105, 180)
}

# Configura colori dal config
BG_COLOR = color_map.get(config.COLOR_BACKGROUND, (0, 0, 0))
HEAD_COLOR = color_map.get(config.COLOR_SNAKE_HEAD, (255, 255, 255))
BODY_COLOR = color_map.get(config.COLOR_SNAKE_BODY, (255, 0, 255))
FOOD_COLOR = color_map.get(config.COLOR_FOOD, (255, 0, 0))

# Crea finestra
WIDTH = config.GRID_WIDTH * CELL_SIZE
HEIGHT = config.GRID_HEIGHT * CELL_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Snake Game')

# Clock per controllare FPS
clock = pygame.time.Clock()

# Carica suoni da file, con fallback a suoni generati
import os
import numpy as np

def load_or_generate_sounds():
    sounds_dir = os.path.join(os.path.dirname(__file__), 'sounds')

    # Prova a caricare da file
    eat_sound = None
    crash_sound = None
    move_sound = None

    if os.path.exists(sounds_dir):
        try:
            eat_path = os.path.join(sounds_dir, 'eat.wav')
            crash_path = os.path.join(sounds_dir, 'crash.wav')
            move_path = os.path.join(sounds_dir, 'move.wav')

            if os.path.exists(eat_path):
                eat_sound = pygame.mixer.Sound(eat_path)
            if os.path.exists(crash_path):
                crash_sound = pygame.mixer.Sound(crash_path)
            if os.path.exists(move_path):
                move_sound = pygame.mixer.Sound(move_path)
        except Exception as e:
            print(f"Errore nel caricamento dei suoni: {e}")

    # Genera suoni mancanti
    if eat_sound is None:
        sample_rate = 22050
        duration = 0.15
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Suono tipo "bleep" per mangiata
        freq = 800 + 400 * np.sin(2 * np.pi * 10 * t)
        wave = np.sin(2 * np.pi * freq * t) * 0.3 * (1 - t / duration)
        wave = (wave * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        eat_sound = pygame.sndarray.make_sound(stereo_wave)

    if crash_sound is None:
        sample_rate = 22050
        duration = 0.4
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Rumore con frequenze basse per crash
        wave = np.random.uniform(-0.6, 0.6, len(t)) * np.exp(-8 * t)
        wave = (wave * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        crash_sound = pygame.sndarray.make_sound(stereo_wave)

    if move_sound is None:
        sample_rate = 22050
        duration = 0.03
        frequency = 150
        t = np.linspace(0, duration, int(sample_rate * duration))
        wave = np.sin(2 * np.pi * frequency * t) * 0.15 * (1 - t / duration)
        wave = (wave * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        move_sound = pygame.sndarray.make_sound(stereo_wave)

    return eat_sound, crash_sound, move_sound

# Carica suoni
eat_sound, crash_sound, move_sound = load_or_generate_sounds()

def generate_food(snake):
    while True:
        food = [random.randint(0, config.GRID_WIDTH - 1),
                random.randint(0, config.GRID_HEIGHT - 1)]
        if food not in snake:
            return food

def main():
    # Stato iniziale del serpente (x, y)
    snake = [
        [config.GRID_WIDTH // 2, config.GRID_HEIGHT // 2],
        [config.GRID_WIDTH // 2 - 1, config.GRID_HEIGHT // 2],
        [config.GRID_WIDTH // 2 - 2, config.GRID_HEIGHT // 2]
    ]
    direction = [1, 0]  # Muove a destra

    food = generate_food(snake)
    score = 0

    running = True
    game_over = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_UP and direction != [0, 1]:
                    direction = [0, -1]
                    move_sound.play()
                elif event.key == pygame.K_DOWN and direction != [0, -1]:
                    direction = [0, 1]
                    move_sound.play()
                elif event.key == pygame.K_LEFT and direction != [1, 0]:
                    direction = [-1, 0]
                    move_sound.play()
                elif event.key == pygame.K_RIGHT and direction != [-1, 0]:
                    direction = [1, 0]
                    move_sound.play()
                elif event.key == pygame.K_q:
                    running = False

            if event.type == pygame.KEYDOWN and game_over:
                running = False

        if not game_over:
            # Calcola nuova posizione testa
            new_head = [snake[0][0] + direction[0], snake[0][1] + direction[1]]

            # Controllo collisioni
            if (new_head[0] < 0 or new_head[0] >= config.GRID_WIDTH or
                new_head[1] < 0 or new_head[1] >= config.GRID_HEIGHT or
                new_head in snake):
                crash_sound.play()
                game_over = True
            else:
                snake.insert(0, new_head)

                # Controllo se ha mangiato
                if new_head == food:
                    eat_sound.play()
                    food = generate_food(snake)
                    score += 10
                else:
                    snake.pop()

        # Disegna tutto
        screen.fill(BG_COLOR)

        # Disegna cibo
        pygame.draw.rect(screen, FOOD_COLOR,
                        (food[0] * CELL_SIZE, food[1] * CELL_SIZE,
                         CELL_SIZE, CELL_SIZE))

        # Disegna serpente
        for i, segment in enumerate(snake):
            color = HEAD_COLOR if i == 0 else BODY_COLOR
            pygame.draw.rect(screen, color,
                           (segment[0] * CELL_SIZE, segment[1] * CELL_SIZE,
                            CELL_SIZE, CELL_SIZE))

        # Disegna score
        font_score = pygame.font.Font(None, 36)
        score_text = font_score.render(f'Score: {score}', True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        # Messaggio game over
        if game_over:
            font = pygame.font.Font(None, 48)
            text = font.render('Game Over!', True, (255, 255, 255))
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            screen.blit(text, text_rect)

            font_score_final = pygame.font.Font(None, 36)
            score_final_text = font_score_final.render(f'Score finale: {score}', True, (255, 255, 255))
            score_final_rect = score_final_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
            screen.blit(score_final_text, score_final_rect)

            font_small = pygame.font.Font(None, 24)
            text_small = font_small.render('Premi un tasto per uscire', True, (255, 255, 255))
            text_rect_small = text_small.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
            screen.blit(text_small, text_rect_small)

        pygame.display.flip()
        clock.tick(config.FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
