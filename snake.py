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
        score_text = font_score.render(f'Score: {score}', True, TEXT_COLOR)
        screen.blit(score_text, (10, 10))

        # Messaggio game over
        if game_over:
            font = pygame.font.Font(None, 48)
            text = font.render('Game Over!', True, TEXT_COLOR)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            screen.blit(text, text_rect)

            font_score_final = pygame.font.Font(None, 36)
            score_final_text = font_score_final.render(f'Score finale: {score}', True, TEXT_COLOR)
            score_final_rect = score_final_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
            screen.blit(score_final_text, score_final_rect)

            font_small = pygame.font.Font(None, 24)
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
