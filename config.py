# Configurazione per il gioco Snake

# Dimensioni della griglia (numero di celle)
# In terminale, meglio stare in range piccoli se possibile, ma usiamo gli stessi valori
GRID_WIDTH = 40
GRID_HEIGHT = 20

# Caratteri per il serpente e cibo
CHAR_SNAKE_HEAD = '@'
CHAR_SNAKE_BODY = 'o'
CHAR_FOOD = '*'
CHAR_EMPTY = ' '

# Colori per curses (nomi dei colori)
COLOR_BACKGROUND = 'GREEN'
COLOR_SNAKE_HEAD = 'WHITE'
COLOR_SNAKE_BODY = 'MAGENTA' # Curses non ha il rosa standard, usiamo magenta
COLOR_FOOD = 'RED'

# Velocità del gioco (frame per secondo)
# Per curses, il tempo è espresso in millisecondi di delay (1000/FPS)
FPS = 10
DELAY = int(1000 / FPS)
