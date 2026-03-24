"""Snake Game with Rainbow Gradient and Synthesized Audio.

Un gioco Snake classico con effetto gradiente arcobaleno dinamico e audio sintetizzato.
"""

import sys
import random
import colorsys

import pygame

import config
from audio import SoundManager

# === CONFIGURAZIONE PYGAME ===
pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
pygame.init()

# === COSTANTI DISPLAY ===
CELL_SIZE = 20
WIDTH = config.GRID_WIDTH * CELL_SIZE
HEIGHT = config.GRID_HEIGHT * CELL_SIZE
FPS = config.FPS

# === COLORI ===
BG_COLOR = config.BACKGROUND_COLOR
HEAD_COLOR = config.SNAKE_HEAD_COLOR
FOOD_COLOR = config.FOOD_COLOR
TEXT_COLOR = config.TEXT_COLOR
WRAP_FLASH_COLOR = config.COLOR_WRAP_FLASH

# === COSTANTI GAME ===
WRAP_FLASH_DURATION = 6
FOOD_SCORE = 10

# === SETUP DISPLAY ===
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Snake Game')
clock = pygame.time.Clock()

# === AUDIO ===
sound_manager = SoundManager()

# === FOOD IMAGE ===
FOOD_IMAGE = None
FOOD_IMAGE_PATH = "ecco.png"

def init_food_image():
    """Carica l'immagine del cibo se disponibile."""
    global FOOD_IMAGE
    try:
        if __import__('os').path.exists(FOOD_IMAGE_PATH):
            raw_image = pygame.image.load(FOOD_IMAGE_PATH)
            FOOD_IMAGE = pygame.transform.scale(raw_image, (50, 50))
    except:
        FOOD_IMAGE = None


def render_food(food):
    """Renderizza il cibo (PNG o rettangolo di colore)."""
    x = food[0] * CELL_SIZE + (CELL_SIZE - 50) // 2
    y = food[1] * CELL_SIZE + (CELL_SIZE - 50) // 2
    if FOOD_IMAGE:
        screen.blit(FOOD_IMAGE, (x, y))
    else:
        pygame.draw.rect(screen, FOOD_COLOR, (food[0] * CELL_SIZE, food[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))


def get_font(name="helvetica neue", size=36, bold=False):
    """Ottiene font con fallback per Helvetica Neue."""
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except:
        return pygame.font.Font(None, size)


def get_rainbow_color(position, total_length):
    """Calcola colore arcobaleno basato sulla posizione nel corpo."""
    if position == 0:
        return HEAD_COLOR
    
    if total_length <= 1:
        proportion = 0
    else:
        proportion = (position - 1) / (total_length - 1)
    
    hue = 0.83 * proportion  # 0 (rosso) → 0.83 (viola)
    saturation, value = 0.8, 1.0
    
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    return (int(r * 255), int(g * 255), int(b * 255))


def generate_food(snake):
    """Genera cibo in posizione casuale non occupata."""
    while True:
        food = [random.randint(0, config.GRID_WIDTH - 1),
                random.randint(0, config.GRID_HEIGHT - 1)]
        if food not in snake:
            return food


def handle_movement(event, direction, game_over):
    """Gestisce input da tastiera."""
    if event.type == pygame.QUIT:
        return None, direction
    
    if event.type == pygame.KEYDOWN and not game_over:
        key_map = {
            pygame.K_UP: ([0, -1], [0, 1]),
            pygame.K_DOWN: ([0, 1], [0, -1]),
            pygame.K_LEFT: ([-1, 0], [1, 0]),
            pygame.K_RIGHT: ([1, 0], [-1, 0]),
        }
        
        if event.key in key_map:
            new_dir, opposite = key_map[event.key]
            if direction != opposite:
                direction = new_dir
                sound_manager.play_sound('move')
        elif event.key == pygame.K_q:
            return None, direction
    
    elif event.type == pygame.KEYDOWN and game_over:
        return None, direction  # Esci su qualsiasi tasto
    
    return True, direction


def check_collision(new_head, snake):
    """Verifica collisioni con pareti o corpo."""
    return (new_head[0] < 0 or new_head[0] >= config.GRID_WIDTH or
            new_head[1] < 0 or new_head[1] >= config.GRID_HEIGHT or
            new_head in snake)


def handle_wrap(new_head):
    """Gestisce attraversamento muri se SHIFT è premuto."""
    mods = pygame.key.get_mods()
    if mods & pygame.KMOD_SHIFT:
        new_head[0] %= config.GRID_WIDTH
        new_head[1] %= config.GRID_HEIGHT
        return True
    return False


def render_game(snake, food, score, wrap_flash_frames):
    """Renderizza il gioco."""
    screen.fill(BG_COLOR)
    
    # Flash di wrap
    if wrap_flash_frames > 0:
        flash_alpha = int(80 * (wrap_flash_frames / WRAP_FLASH_DURATION))
        flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash_surface.fill((*WRAP_FLASH_COLOR, flash_alpha))
        screen.blit(flash_surface, (0, 0))
    
    # Cibo
    render_food(food)
    
    # Snake con gradiente arcobaleno
    for i, segment in enumerate(snake):
        color = get_rainbow_color(i, len(snake))
        pygame.draw.rect(screen, color, (segment[0] * CELL_SIZE, segment[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    # Score
    font = get_font(size=36, bold=True)
    score_text = font.render(f'Score: {score}', True, TEXT_COLOR)
    screen.blit(score_text, (10, 10))
    
    pygame.display.flip()


def render_game_over(score):
    """Renderizza schermata game over."""
    screen.fill(BG_COLOR)
    
    font_title = get_font(size=48, bold=True)
    title = font_title.render('Game Over!', True, TEXT_COLOR)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
    
    font_score = get_font(size=36, bold=True)
    score_text = font_score.render(f'Score finale: {score}', True, TEXT_COLOR)
    screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))
    
    font_small = get_font(size=24)
    exit_text = font_small.render('Premi un tasto per uscire', True, TEXT_COLOR)
    screen.blit(exit_text, exit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))
    
    pygame.display.flip()


def main():
    """Loop principale di gioco."""
    # Inizializzazione
    snake = [[config.GRID_WIDTH // 2, config.GRID_HEIGHT // 2],
             [config.GRID_WIDTH // 2 - 1, config.GRID_HEIGHT // 2],
             [config.GRID_WIDTH // 2 - 2, config.GRID_HEIGHT // 2]]
    direction = [1, 0]
    food = generate_food(snake)
    score = 0
    running, game_over, wrap_flash_frames = True, False, 0
    
    sound_manager.play_music()
    init_food_image()
    
    while running:
        # Gestione input
        for event in pygame.event.get():
            result, direction = handle_movement(event, direction, game_over)
            if result is None:
                running = False
        
        if not game_over:
            # Calcola nuova posizione testa
            new_head = [snake[0][0] + direction[0], snake[0][1] + direction[1]]
            was_wrapped = False
            
            # Controllo wrap (attraversamento muri)
            if check_collision(new_head, snake) and handle_wrap(new_head):
                wrap_flash_frames = WRAP_FLASH_DURATION
                sound_manager.play_sound('wrap')
                was_wrapped = True
            
            # Controllo collisioni
            if check_collision(new_head, snake) and not was_wrapped:
                sound_manager.stop_music()
                sound_manager.play_sound('crash')
                game_over = True
            else:
                snake.insert(0, new_head)
                
                # Controllo se ha mangiato
                if new_head == food:
                    sound_manager.play_sound('eat')
                    food = generate_food(snake)
                    score += FOOD_SCORE
                    sound_manager.update_score(score)
                else:
                    snake.pop()
            
            wrap_flash_frames = max(0, wrap_flash_frames - 1)
        
        # Rendering
        render_game(snake, food, score, wrap_flash_frames)
        
        if game_over:
            render_game_over(score)
        
        clock.tick(FPS)
    
    sound_manager.stop_music()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()

# Dimensioni celle in pixel
CELL_SIZE = 20

BG_COLOR = config.BACKGROUND_COLOR
HEAD_COLOR = config.SNAKE_HEAD_COLOR
BODY_COLOR = config.SNAKE_BODY_COLOR
FOOD_COLOR = config.FOOD_COLOR
TEXT_COLOR = config.TEXT_COLOR

# Crea finestra
WIDTH = config.GRID_WIDTH * CELL_SIZE
HEIGHT = config.GRID_HEIGHT * CELL_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Snake Game')

# Clock per controllare FPS
clock = pygame.time.Clock()

SAMPLE_RATE = 22050
MUSIC_VOLUME = 0.13
MOVE_VOLUME = 0.12
EAT_VOLUME = 0.32
CRASH_VOLUME = 0.4
WRAP_VOLUME = 0.24

MOVE_SOUND_PATH = os.path.join(os.path.dirname(__file__), "sounds", "move.wav")
EAT_SOUND_PATH = os.path.join(os.path.dirname(__file__), "sounds", "eat.wav")
CRASH_SOUND_PATH = os.path.join(os.path.dirname(__file__), "sounds", "crash.wav")
WRAP_FLASH_COLOR = config.COLOR_WRAP_FLASH
WRAP_FLASH_DURATION = 6


class SilentSound:
    def play(self):
        return None

    def set_volume(self, _volume):
        return None

    def get_length(self):
        return 0.0


def init_audio():
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        return True
    except pygame.error as error:
        print(f"Audio disabilitato: {error}")
        return False


def build_stereo_sound(samples):
    stereo = array("h")
    for sample in samples:
        stereo.extend((sample, sample))
    return pygame.mixer.Sound(buffer=stereo.tobytes())


def clamp_sample(value):
    return max(-32767, min(32767, int(value)))


def mix_voices(voices):
    mixed = 0.0
    for voice in voices:
        mixed += voice
    return mixed / max(1, len(voices))


def generate_tone_sound(duration, base_frequency, volume, sweep=0, wobble=0, overtone=0.0, warmth=0.0):
    total_samples = max(1, int(SAMPLE_RATE * duration))
    samples = []

    for index in range(total_samples):
        progress = index / total_samples
        frequency = base_frequency + (sweep * progress) + wobble * math.sin(2 * math.pi * 10 * progress)
        amplitude = volume * ((1 - progress) ** 2.1)
        fundamental = math.sin(2 * math.pi * frequency * index / SAMPLE_RATE)
        upper = overtone * math.sin(2 * math.pi * frequency * 2 * index / SAMPLE_RATE)
        lower = warmth * math.sin(2 * math.pi * (frequency * 0.5) * index / SAMPLE_RATE)
        texture = 0.04 * math.sin(2 * math.pi * (frequency * 0.25) * index / SAMPLE_RATE)
        voice = mix_voices((fundamental, upper, lower, texture))
        samples.append(clamp_sample(32767 * amplitude * voice))

    return build_stereo_sound(samples)


def generate_crash_sound(duration, volume):
    total_samples = max(1, int(SAMPLE_RATE * duration))
    samples = []

    for index in range(total_samples):
        progress = index / total_samples
        envelope = (1 - progress) ** 2.6
        noise = random.uniform(-0.6, 0.6)
        low_tone = math.sin(2 * math.pi * 65 * index / SAMPLE_RATE)
        soft_tail = math.sin(2 * math.pi * 110 * index / SAMPLE_RATE)
        voice = 0.38 * noise + 0.42 * low_tone + 0.2 * soft_tail
        samples.append(clamp_sample(32767 * volume * envelope * voice))

    return build_stereo_sound(samples)


def generate_pluck_sound(duration, base_frequency, volume, sparkle=0.0):
    total_samples = max(1, int(SAMPLE_RATE * duration))
    samples = []

    for index in range(total_samples):
        progress = index / total_samples
        current_time = index / SAMPLE_RATE
        envelope = ((1 - progress) ** 2.3) * (0.85 + 0.15 * math.sin(math.pi * progress))
        body = math.sin(2 * math.pi * base_frequency * current_time)
        octave = 0.22 * math.sin(2 * math.pi * base_frequency * 2 * current_time)
        sub = 0.18 * math.sin(2 * math.pi * (base_frequency / 2) * current_time)
        chime = sparkle * math.sin(2 * math.pi * (base_frequency * 3) * current_time)
        voice = mix_voices((body, octave, sub, chime))
        samples.append(clamp_sample(32767 * volume * envelope * voice))

    return build_stereo_sound(samples)


def generate_wrap_sound(duration, start_frequency, end_frequency, volume):
    total_samples = max(1, int(SAMPLE_RATE * duration))
    samples = []

    for index in range(total_samples):
        progress = index / total_samples
        current_time = index / SAMPLE_RATE
        frequency = start_frequency + ((end_frequency - start_frequency) * progress)
        envelope = (1 - progress) ** 1.7
        body = math.sin(2 * math.pi * frequency * current_time)
        airy = 0.22 * math.sin(2 * math.pi * (frequency * 1.5) * current_time)
        tail = 0.15 * math.sin(2 * math.pi * (frequency * 0.5) * current_time)
        voice = mix_voices((body, airy, tail))
        samples.append(clamp_sample(32767 * volume * envelope * voice))

    return build_stereo_sound(samples)


def note_frequency(note):
    notes = {
        "C": -9,
        "C#": -8,
        "D": -7,
        "D#": -6,
        "E": -5,
        "F": -4,
        "F#": -3,
        "G": -2,
        "G#": -1,
        "A": 0,
        "A#": 1,
        "B": 2,
    }
    if note == "R":
        return 0.0

    if len(note) == 2:
        name = note[0]
        octave = int(note[1])
    else:
        name = note[:2]
        octave = int(note[2])

    semitones = notes[name] + ((octave - 4) * 12)
    return 440.0 * (2 ** (semitones / 12))


def generate_music_loop():
    step_duration = 0.19
    lead_sequence = [
        "E4", "G4", "A4", "C5", "B4", "A4", "G4", "E4",
        "D4", "E4", "G4", "A4", "G4", "E4", "D4", "B3",
        "C4", "E4", "G4", "B4", "A4", "G4", "E4", "D4",
        "E4", "G4", "A4", "G4", "E4", "D4", "C4", "R",
    ]
    bass_sequence = [
        "E2", "B2", "A2", "E2", "C3", "G2", "A2", "E2",
        "D3", "A2", "G2", "D2", "C3", "G2", "A2", "B2",
    ]

    total_samples = int(len(lead_sequence) * step_duration * SAMPLE_RATE)
    samples = []

    for index in range(total_samples):
        current_time = index / SAMPLE_RATE
        lead_step = min(len(lead_sequence) - 1, int(current_time / step_duration))
        bass_step = min(len(bass_sequence) - 1, int(current_time / (step_duration * 2)))
        lead_progress = (current_time % step_duration) / step_duration
        bass_progress = (current_time % (step_duration * 2)) / (step_duration * 2)

        lead_frequency = note_frequency(lead_sequence[lead_step])
        bass_frequency = note_frequency(bass_sequence[bass_step])

        lead_voice = 0.0
        if lead_frequency:
            lead_env = 0.5 * ((1 - lead_progress) ** 1.9)
            lead_voice = lead_env * mix_voices((
                math.sin(2 * math.pi * lead_frequency * current_time),
                0.24 * math.sin(2 * math.pi * lead_frequency * 2 * current_time),
                0.12 * math.sin(2 * math.pi * lead_frequency * 3 * current_time),
                0.16 * math.sin(2 * math.pi * (lead_frequency / 2) * current_time),
            ))

        bass_voice = 0.0
        if bass_frequency:
            bass_env = 0.58 * ((1 - bass_progress) ** 1.3)
            bass_voice = bass_env * mix_voices((
                math.sin(2 * math.pi * bass_frequency * current_time),
                0.25 * math.sin(2 * math.pi * bass_frequency * 0.5 * current_time),
                0.12 * math.sin(2 * math.pi * bass_frequency * 1.5 * current_time),
            ))

        bounce = 0.018 if lead_progress < 0.08 and lead_step % 2 == 0 else 0.0
        shimmer = 0.01 * math.sin(2 * math.pi * 4 * current_time)
        voice = (0.54 * lead_voice) + (0.38 * bass_voice) + bounce + shimmer
        samples.append(clamp_sample(32767 * MUSIC_VOLUME * voice))

    return build_stereo_sound(samples)


def load_sound(path, fallback_factory, volume, prefer_file=True):
    if not AUDIO_ENABLED:
        return SilentSound()

    sound = None

    if prefer_file and os.path.exists(path):
        try:
            sound = pygame.mixer.Sound(path)
        except pygame.error as error:
            print(f"Impossibile caricare {os.path.basename(path)}: {error}")

    if sound is None:
        sound = fallback_factory()

    sound.set_volume(volume)
    return sound


def load_or_generate_sounds():
    return (
        load_sound(
            EAT_SOUND_PATH,
            lambda: generate_pluck_sound(duration=0.2, base_frequency=660, volume=0.34, sparkle=0.14),
            EAT_VOLUME,
            prefer_file=False,
        ),
        load_sound(
            CRASH_SOUND_PATH,
            lambda: generate_crash_sound(duration=0.42, volume=0.38),
            CRASH_VOLUME,
            prefer_file=False,
        ),
        load_sound(
            MOVE_SOUND_PATH,
            lambda: generate_tone_sound(duration=0.07, base_frequency=210, volume=0.17, sweep=55, wobble=8, overtone=0.08, warmth=0.16),
            MOVE_VOLUME,
            prefer_file=False,
        ),
        load_sound(
            os.path.join(os.path.dirname(__file__), "sounds", "wrap.wav"),
            lambda: generate_wrap_sound(duration=0.16, start_frequency=420, end_frequency=780, volume=0.24),
            WRAP_VOLUME,
            prefer_file=False,
        ),
    )

AUDIO_ENABLED = init_audio()

# Carica suoni
eat_sound, crash_sound, move_sound, wrap_sound = load_or_generate_sounds()
music_loop = generate_music_loop() if AUDIO_ENABLED else SilentSound()

MOVE_CHANNEL = pygame.mixer.Channel(1) if AUDIO_ENABLED else None
EAT_CHANNEL = pygame.mixer.Channel(2) if AUDIO_ENABLED else None
CRASH_CHANNEL = pygame.mixer.Channel(3) if AUDIO_ENABLED else None
MUSIC_CHANNEL = pygame.mixer.Channel(4) if AUDIO_ENABLED else None
WRAP_CHANNEL = pygame.mixer.Channel(5) if AUDIO_ENABLED else None


def play_music():
    if MUSIC_CHANNEL is not None and not MUSIC_CHANNEL.get_busy():
        MUSIC_CHANNEL.play(music_loop, loops=-1)


def stop_music():
    if MUSIC_CHANNEL is not None:
        MUSIC_CHANNEL.fadeout(350)


def play_move_sound():
    if MOVE_CHANNEL is not None:
        MOVE_CHANNEL.stop()
        MOVE_CHANNEL.play(move_sound)


def play_eat_sound():
    if EAT_CHANNEL is not None:
        EAT_CHANNEL.play(eat_sound)


def play_crash_sound():
    if CRASH_CHANNEL is not None:
        CRASH_CHANNEL.play(crash_sound)


def play_wrap_sound():
    if WRAP_CHANNEL is not None:
        WRAP_CHANNEL.play(wrap_sound)

def generate_food(snake):
    while True:
        food = [random.randint(0, config.GRID_WIDTH - 1),
                random.randint(0, config.GRID_HEIGHT - 1)]
        if food not in snake:
            return food


def shift_wrap_enabled():
    mods = pygame.key.get_mods()
    return bool(mods & pygame.KMOD_SHIFT)

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
    wrap_flash_frames = 0
    play_music()
    init_food_image()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_UP and direction != [0, 1]:
                    direction = [0, -1]
                    play_move_sound()
                elif event.key == pygame.K_DOWN and direction != [0, -1]:
                    direction = [0, 1]
                    play_move_sound()
                elif event.key == pygame.K_LEFT and direction != [1, 0]:
                    direction = [-1, 0]
                    play_move_sound()
                elif event.key == pygame.K_RIGHT and direction != [-1, 0]:
                    direction = [1, 0]
                    play_move_sound()
                elif event.key == pygame.K_q:
                    running = False

            if event.type == pygame.KEYDOWN and game_over:
                running = False

        if not game_over:
            # Calcola nuova posizione testa
            new_head = [snake[0][0] + direction[0], snake[0][1] + direction[1]]
            hit_wall = (
                new_head[0] < 0 or new_head[0] >= config.GRID_WIDTH or
                new_head[1] < 0 or new_head[1] >= config.GRID_HEIGHT
            )

            if hit_wall and shift_wrap_enabled():
                new_head[0] %= config.GRID_WIDTH
                new_head[1] %= config.GRID_HEIGHT
                wrap_flash_frames = WRAP_FLASH_DURATION
                play_wrap_sound()

            # Controllo collisioni
            if (new_head[0] < 0 or new_head[0] >= config.GRID_WIDTH or
                new_head[1] < 0 or new_head[1] >= config.GRID_HEIGHT or
                new_head in snake):
                stop_music()
                play_crash_sound()
                game_over = True
            else:
                snake.insert(0, new_head)

                # Controllo se ha mangiato
                if new_head == food:
                    play_eat_sound()
                    food = generate_food(snake)
                    score += 10
                    sound_manager.update_score(score)
                else:
                    snake.pop()

        # Disegna tutto
        screen.fill(BG_COLOR)

        if wrap_flash_frames > 0:
            flash_alpha = int(80 * (wrap_flash_frames / WRAP_FLASH_DURATION))
            flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surface.fill((*WRAP_FLASH_COLOR, flash_alpha))
            screen.blit(flash_surface, (0, 0))
            wrap_flash_frames -= 1

        # Disegna cibo
        render_food(food)

        # Disegna serpente
        for i, segment in enumerate(snake):
            color = get_rainbow_color(i, len(snake))
            pygame.draw.rect(screen, color,
                           (segment[0] * CELL_SIZE, segment[1] * CELL_SIZE,
                            CELL_SIZE, CELL_SIZE))

        # Disegna score
        font_score = get_font(size=36, bold=True)
        score_text = font_score.render(f'Score: {score}', True, TEXT_COLOR)
        screen.blit(score_text, (10, 10))

        # Messaggio game over
        if game_over:
            font = get_font(size=48, bold=True)
            text = font.render('Game Over!', True, TEXT_COLOR)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            screen.blit(text, text_rect)

            font_score_final = get_font(size=36, bold=True)
            score_final_text = font_score_final.render(f'Score finale: {score}', True, TEXT_COLOR)
            score_final_rect = score_final_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
            screen.blit(score_final_text, score_final_rect)

            font_small = get_font(size=24)
            text_small = font_small.render('Premi un tasto per uscire', True, TEXT_COLOR)
            text_rect_small = text_small.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
            screen.blit(text_small, text_rect_small)

        pygame.display.flip()
        clock.tick(config.FPS)

    stop_music()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
