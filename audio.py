"""Audio synthesis system for Snake Game.

Questo modulo gestisce la generazione di suoni sintetizzati e il sistema audio.
"""

import math
import os
import random
from array import array

import pygame

SAMPLE_RATE = 22050
MAX_SAMPLE_VALUE = 32767

# Audio parameters
MUSIC_VOLUME = 0.13
MOVE_VOLUME = 0.12
EAT_VOLUME = 0.32
CRASH_VOLUME = 0.4
WRAP_VOLUME = 0.24

# Sound generation parameters
SOUND_PARAMS = {
    'eat': {'duration': 0.2, 'base_frequency': 660, 'volume': 0.34, 'sparkle': 0.14},
    'crash': {'duration': 0.42, 'volume': 0.38},
    'move': {'duration': 0.07, 'base_frequency': 210, 'volume': 0.17, 'sweep': 55, 'wobble': 8, 'overtone': 0.08, 'warmth': 0.16},
    'wrap': {'duration': 0.16, 'start_frequency': 420, 'end_frequency': 780, 'volume': 0.24},
}

SOUND_CHANNEL_IDS = {'move': 1, 'eat': 2, 'crash': 3, 'music': 4, 'wrap': 5}


class SilentSound:
    """Placeholder quando audio è disabilitato."""
    def play(self):
        return None
    def set_volume(self, _volume):
        return None
    def get_length(self):
        return 0.0


def init_audio():
    """Inizializza il sistema audio di pygame."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        return True
    except pygame.error as error:
        print(f"Audio disabilitato: {error}")
        return False


def clamp_sample(value):
    """Limita il valore del campione tra -MAX_SAMPLE e MAX_SAMPLE."""
    return max(-MAX_SAMPLE_VALUE, min(MAX_SAMPLE_VALUE, int(value)))


def build_stereo_sound(samples):
    """Converte lista di campioni mono in suono stereo."""
    stereo = array("h")
    for sample in samples:
        stereo.extend((sample, sample))
    return pygame.mixer.Sound(buffer=stereo.tobytes())


def mix_voices(voices):
    """Mescola più voci audio calcolando la media."""
    return sum(voices) / max(1, len(voices))


def generate_sine_wave(frequency, duration, sample_rate=SAMPLE_RATE):
    """Genera un'onda sinusoidale pura."""
    total_samples = int(duration * sample_rate)
    return [math.sin(2 * math.pi * frequency * i / sample_rate) for i in range(total_samples)]


def generate_tone_sound(base_frequency, duration, volume, sweep=0, wobble=0, overtone=0.0, warmth=0.0):
    """Genera suono tonale con modulazioni."""
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
        samples.append(clamp_sample(MAX_SAMPLE_VALUE * amplitude * voice))

    return build_stereo_sound(samples)


def generate_crash_sound(duration, volume):
    """Genera suono di crash (scontro)."""
    total_samples = max(1, int(SAMPLE_RATE * duration))
    samples = []

    for index in range(total_samples):
        progress = index / total_samples
        envelope = (1 - progress) ** 2.6
        noise = random.uniform(-0.6, 0.6)
        low_tone = math.sin(2 * math.pi * 65 * index / SAMPLE_RATE)
        soft_tail = math.sin(2 * math.pi * 110 * index / SAMPLE_RATE)
        voice = 0.38 * noise + 0.42 * low_tone + 0.2 * soft_tail
        
        samples.append(clamp_sample(MAX_SAMPLE_VALUE * volume * envelope * voice))

    return build_stereo_sound(samples)


def generate_pluck_sound(base_frequency, duration, volume, sparkle=0.0):
    """Genera suono di plettro (pizzicato)."""
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
        samples.append(clamp_sample(MAX_SAMPLE_VALUE * volume * envelope * voice))

    return build_stereo_sound(samples)


def generate_wrap_sound(start_freq, end_freq, duration, volume):
    """Genera suono di wrap (attraversamento muri)."""
    total_samples = max(1, int(SAMPLE_RATE * duration))
    samples = []

    for index in range(total_samples):
        progress = index / total_samples
        current_time = index / SAMPLE_RATE
        frequency = start_freq + ((end_freq - start_freq) * progress)
        envelope = (1 - progress) ** 1.7
        
        body = math.sin(2 * math.pi * frequency * current_time)
        airy = 0.22 * math.sin(2 * math.pi * (frequency * 1.5) * current_time)
        tail = 0.15 * math.sin(2 * math.pi * (frequency * 0.5) * current_time)
        
        voice = mix_voices((body, airy, tail))
        samples.append(clamp_sample(MAX_SAMPLE_VALUE * volume * envelope * voice))

    return build_stereo_sound(samples)


NOTE_FREQUENCIES = {
    "C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3,
    "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2,
}


def note_frequency(note):
    """Converte nota musicale (es. 'E4') in frequenza Hz."""
    if note == "R":
        return 0.0

    name = note[0] if len(note) == 2 else note[:2]
    octave = int(note[1] if len(note) == 2 else note[2])

    if name not in NOTE_FREQUENCIES:
        return 0.0

    semitones = NOTE_FREQUENCIES[name] + ((octave - 4) * 12)
    return 440.0 * (2 ** (semitones / 12))


def generate_music_loop():
    """Genera il loop musicale principale."""
    step_duration = 0.19
    lead_notes = ["E4", "G4", "A4", "C5", "B4", "A4", "G4", "E4",
                  "D4", "E4", "G4", "A4", "G4", "E4", "D4", "B3",
                  "C4", "E4", "G4", "B4", "A4", "G4", "E4", "D4",
                  "E4", "G4", "A4", "G4", "E4", "D4", "C4", "R"]
    bass_notes = ["E2", "B2", "A2", "E2", "C3", "G2", "A2", "E2",
                  "D3", "A2", "G2", "D2", "C3", "G2", "A2", "B2"]

    total_samples = int(len(lead_notes) * step_duration * SAMPLE_RATE)
    samples = []

    for index in range(total_samples):
        current_time = index / SAMPLE_RATE
        lead_step = min(len(lead_notes) - 1, int(current_time / step_duration))
        bass_step = min(len(bass_notes) - 1, int(current_time / (step_duration * 2)))
        lead_progress = (current_time % step_duration) / step_duration
        bass_progress = (current_time % (step_duration * 2)) / (step_duration * 2)

        lead_freq = note_frequency(lead_notes[lead_step])
        bass_freq = note_frequency(bass_notes[bass_step])

        lead_voice = 0.0
        if lead_freq:
            lead_env = 0.5 * ((1 - lead_progress) ** 1.9)
            lead_voice = lead_env * mix_voices((
                math.sin(2 * math.pi * lead_freq * current_time),
                0.24 * math.sin(2 * math.pi * lead_freq * 2 * current_time),
                0.12 * math.sin(2 * math.pi * lead_freq * 3 * current_time),
                0.16 * math.sin(2 * math.pi * (lead_freq / 2) * current_time),
            ))

        bass_voice = 0.0
        if bass_freq:
            bass_env = 0.58 * ((1 - bass_progress) ** 1.3)
            bass_voice = bass_env * mix_voices((
                math.sin(2 * math.pi * bass_freq * current_time),
                0.25 * math.sin(2 * math.pi * bass_freq * 0.5 * current_time),
                0.12 * math.sin(2 * math.pi * bass_freq * 1.5 * current_time),
            ))

        bounce = 0.018 if lead_progress < 0.08 and lead_step % 2 == 0 else 0.0
        shimmer = 0.01 * math.sin(2 * math.pi * 4 * current_time)
        voice = (0.54 * lead_voice) + (0.38 * bass_voice) + bounce + shimmer
        samples.append(clamp_sample(MAX_SAMPLE_VALUE * MUSIC_VOLUME * voice))

    return build_stereo_sound(samples)


def load_sound(path, factory_func, volume, prefer_file=True):
    """Carica o genera un suono."""
    def fallback():
        return factory_func()

    if not AUDIO_ENABLED:
        return SilentSound()

    sound = None
    if prefer_file and os.path.exists(path):
        try:
            sound = pygame.mixer.Sound(path)
        except pygame.error as error:
            print(f"Impossibile caricare {os.path.basename(path)}: {error}")

    sound = sound or fallback()
    sound.set_volume(volume)
    return sound


class SoundManager:
    """Gestisce tutti i suoni e i canali audio."""
    
    def __init__(self, sounds_dir=None):
        self.enabled = init_audio()
        self.sounds_dir = sounds_dir or os.path.dirname(__file__)
        self.channels = {}
        self.sounds = {}
        self._init_sounds()
        self._init_channels()
    
    def _init_sounds(self):
        """Inizializza tutti i suoni."""
        eat_params = SOUND_PARAMS['eat']
        self.sounds['eat'] = load_sound(
            os.path.join(self.sounds_dir, "sounds", "eat.wav"),
            lambda: generate_pluck_sound(**eat_params),
            EAT_VOLUME
        )
        
        crash_params = SOUND_PARAMS['crash']
        self.sounds['crash'] = load_sound(
            os.path.join(self.sounds_dir, "sounds", "crash.wav"),
            lambda: generate_crash_sound(**crash_params),
            CRASH_VOLUME
        )
        
        move_params = SOUND_PARAMS['move']
        self.sounds['move'] = load_sound(
            os.path.join(self.sounds_dir, "sounds", "move.wav"),
            lambda: generate_tone_sound(**move_params),
            MOVE_VOLUME
        )
        
        wrap_params = SOUND_PARAMS['wrap']
        self.sounds['wrap'] = load_sound(
            os.path.join(self.sounds_dir, "sounds", "wrap.wav"),
            lambda: generate_wrap_sound(wrap_params['start_frequency'], wrap_params['end_frequency'], wrap_params['duration'], wrap_params['volume']),
            WRAP_VOLUME
        )
        
        self.sounds['music'] = generate_music_loop() if self.enabled else SilentSound()
    
    def _init_channels(self):
        """Inizializza i canali audio."""
        if self.enabled:
            for name, channel_id in SOUND_CHANNEL_IDS.items():
                self.channels[name] = pygame.mixer.Channel(channel_id)
    
    def play_music(self):
        """Avvia la musica di sfondo."""
        if self.channels.get('music') and not self.channels['music'].get_busy():
            self.channels['music'].play(self.sounds['music'], loops=-1)
    
    def stop_music(self):
        """Ferma la musica con fade out."""
        if self.channels.get('music'):
            self.channels['music'].fadeout(350)
    
    def play_sound(self, sound_name):
        """Gioca un suono."""
        channel = self.channels.get(sound_name)
        if channel and sound_name in self.sounds:
            if sound_name == 'move':
                channel.stop()
            channel.play(self.sounds[sound_name])


AUDIO_ENABLED = init_audio()
