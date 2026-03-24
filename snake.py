import math
import os
import random
import sys
from array import array

import pygame

import config

# Inizializza pygame con impostazioni audio prevedibili
pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
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

SAMPLE_RATE = 22050
MUSIC_VOLUME = 0.16
MOVE_VOLUME = 0.16
EAT_VOLUME = 0.42
CRASH_VOLUME = 0.6

MOVE_SOUND_PATH = os.path.join(os.path.dirname(__file__), "sounds", "move.wav")
EAT_SOUND_PATH = os.path.join(os.path.dirname(__file__), "sounds", "eat.wav")
CRASH_SOUND_PATH = os.path.join(os.path.dirname(__file__), "sounds", "crash.wav")


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


def generate_tone_sound(duration, base_frequency, volume, sweep=0, wobble=0, overtone=0.0):
    total_samples = max(1, int(SAMPLE_RATE * duration))
    samples = []

    for index in range(total_samples):
        progress = index / total_samples
        frequency = base_frequency + (sweep * progress) + wobble * math.sin(2 * math.pi * 10 * progress)
        amplitude = volume * ((1 - progress) ** 1.4)
        fundamental = math.sin(2 * math.pi * frequency * index / SAMPLE_RATE)
        upper = overtone * math.sin(2 * math.pi * frequency * 2 * index / SAMPLE_RATE)
        texture = 0.08 * math.sin(2 * math.pi * (frequency * 0.5) * index / SAMPLE_RATE)
        voice = mix_voices((fundamental, upper, texture))
        samples.append(clamp_sample(32767 * amplitude * voice))

    return build_stereo_sound(samples)


def generate_crash_sound(duration, volume):
    total_samples = max(1, int(SAMPLE_RATE * duration))
    samples = []

    for index in range(total_samples):
        progress = index / total_samples
        envelope = (1 - progress) ** 2
        noise = random.uniform(-1.0, 1.0)
        low_tone = math.sin(2 * math.pi * 70 * index / SAMPLE_RATE)
        metallic = math.sin(2 * math.pi * 180 * index / SAMPLE_RATE)
        voice = 0.6 * noise + 0.25 * low_tone + 0.15 * metallic
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
    step_duration = 0.18
    lead_sequence = [
        "E4", "G4", "A4", "B4", "A4", "G4", "E4", "D4",
        "C4", "E4", "G4", "A4", "G4", "E4", "D4", "B3",
        "E4", "G4", "A4", "B4", "D5", "B4", "A4", "G4",
        "E4", "D4", "C4", "D4", "E4", "G4", "D4", "R",
    ]
    bass_sequence = [
        "E2", "E2", "A2", "A2", "C3", "C3", "B2", "B2",
        "C3", "C3", "G2", "G2", "A2", "A2", "B2", "B2",
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
            lead_env = 0.65 * ((1 - lead_progress) ** 1.8)
            lead_voice = lead_env * mix_voices((
                math.sin(2 * math.pi * lead_frequency * current_time),
                0.35 * math.sin(2 * math.pi * lead_frequency * 2 * current_time),
                0.15 * math.sin(2 * math.pi * (lead_frequency / 2) * current_time),
            ))

        bass_voice = 0.0
        if bass_frequency:
            bass_env = 0.8 * ((1 - bass_progress) ** 1.2)
            bass_voice = bass_env * mix_voices((
                math.sin(2 * math.pi * bass_frequency * current_time),
                0.25 * math.sin(2 * math.pi * bass_frequency * 0.5 * current_time),
            ))

        pulse = 0.06 if (lead_step % 4 == 0 and lead_progress < 0.12) else 0.0
        voice = (0.52 * lead_voice) + (0.45 * bass_voice) + pulse
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
            lambda: generate_tone_sound(duration=0.18, base_frequency=740, volume=0.46, sweep=420, wobble=35, overtone=0.22),
            EAT_VOLUME,
            prefer_file=False,
        ),
        load_sound(
            CRASH_SOUND_PATH,
            lambda: generate_crash_sound(duration=0.48, volume=0.52),
            CRASH_VOLUME,
            prefer_file=False,
        ),
        load_sound(
            MOVE_SOUND_PATH,
            lambda: generate_tone_sound(duration=0.06, base_frequency=220, volume=0.22, sweep=85, overtone=0.18),
            MOVE_VOLUME,
            prefer_file=False,
        ),
    )

AUDIO_ENABLED = init_audio()

# Carica suoni
eat_sound, crash_sound, move_sound = load_or_generate_sounds()
music_loop = generate_music_loop() if AUDIO_ENABLED else SilentSound()

MOVE_CHANNEL = pygame.mixer.Channel(1) if AUDIO_ENABLED else None
EAT_CHANNEL = pygame.mixer.Channel(2) if AUDIO_ENABLED else None
CRASH_CHANNEL = pygame.mixer.Channel(3) if AUDIO_ENABLED else None
MUSIC_CHANNEL = pygame.mixer.Channel(4) if AUDIO_ENABLED else None


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
    play_music()

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

    stop_music()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
