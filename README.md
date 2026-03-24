# Snake Game - Rainbow Gradient Edition 🌈

Un classico gioco Snake con un effetto speciale: il corpo dello snake ha un gradiente arcobaleno che cambia colore man mano che cresce.

## Feature

- 🐍 Gioco Snake classico con controlli da tastiera (frecce)
- 🌈 **Gradiente arcobaleno dinamico**: il corpo cambia colore da rosso a viola man mano che lo snake cresce
- 📊 Score tracking in tempo reale
- ⚙️ Completamente configurabile tramite `config.py`

## Requisiti

- Python 3.7+
- pygame
- config.py (incluso)

## Installazione

```bash
pip install pygame
```

## Come giocare

```bash
python snake.py
```

### Controlli

- **Frecce**: muovi lo snake
- **Q**: esci dal gioco
- **Qualsiasi tasto**: esci dopo game over

## Come funziona il gradiente arcobaleno

Il corpo dello snake utilizza uno spazio colore HSV per creare un gradiente continuo:
- La **testa** mantiene il colore originale (bianco)
- Il **corpo** ha colori che vanno da **rosso** (primo segmento) a **viola** (ultimo segmento)
- I colori cambiano **dinamicamente** quando il corpo cresce

## Personalizzazione

Modifica `config.py` per cambiare:
- Dimensioni della griglia
- Colori di sfondo, testa e cibo
- Velocità del gioco (FPS)

## Autore

Rainbow gradient effect implementation - 2026
