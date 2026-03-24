import pygame
import random
import config
import sys
import colorsys

# Inizializza pygame
pygame.init()

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

def generate_food(snake):
    while True:
        food = [random.randint(0, config.GRID_WIDTH - 1),
                random.randint(0, config.GRID_HEIGHT - 1)]
        if food not in snake:
            return food

def get_rainbow_color(position, total_length):
    """
    Calcola il colore del corpo dello snake basato sulla posizione nel corpo.
    Crea un gradiente arcobaleno da rosso (posizione 1) a viola (fine corpo).
    
    Args:
        position: posizione del segmento nel corpo (0 = testa, 1+ = corpo)
        total_length: lunghezza totale dello snake
    
    Returns:
        tupla RGB (r, g, b)
    """
    if position == 0:
        # La testa mantiene il suo colore
        return HEAD_COLOR
    
    # Calcola la proporzione della posizione nel corpo (0 a 1)
    # Escludiamo la testa (position 0) dal calcolo
    if total_length <= 1:
        proportion = 0
    else:
        proportion = (position - 1) / (total_length - 1)
    
    # Converte la proporzione in un valore di hue (0 = rosso, 1 = rosso di nuovo)
    # Usiamo solo 0.83 invece di 1.0 per evitare il rosso finale e fermarsi al viola
    hue = 0 + (0.83 * proportion)  # Da 0 (rosso) a 0.83 (viola)
    saturation = 0.8  # Intensità del colore
    value = 1.0  # Brightness
    
    # Converti da HSV a RGB
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    
    # Converti da float (0-1) a int (0-255)
    return (int(r * 255), int(g * 255), int(b * 255))

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
                elif event.key == pygame.K_DOWN and direction != [0, -1]:
                    direction = [0, 1]
                elif event.key == pygame.K_LEFT and direction != [1, 0]:
                    direction = [-1, 0]
                elif event.key == pygame.K_RIGHT and direction != [-1, 0]:
                    direction = [1, 0]
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
                game_over = True
            else:
                snake.insert(0, new_head)

                # Controllo se ha mangiato
                if new_head == food:
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
            color = get_rainbow_color(i, len(snake))
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
