# MelodyMorph AI

**Evolutionary Music Composition** · Genetic Algorithm Engine

> Create unique mashups by evolving melodies from any two songs using a genetic algorithm. Select, evolve, and download — all from the browser.

### [▶ Live Demo — melodymorph-ai.onrender.com](https://melodymorph-ai.onrender.com/)

---

## Features

| | Feature | Description |
|---|---|---|
| `GA` | **Genetic Algorithm Core** | Evolves melodies over configurable generations to find optimal combinations |
| `♫` | **Raga-Aware Fitness** | Fitness functions tuned for Indian/Bollywood music scales and patterns |
| `►` | **10-Second Preview** | Listen to any song before selecting — Web Audio synthesis, no plugins needed |
| `◈` | **Live Visualization** | Real-time fitness chart updates as the population evolves |
| `↓` | **MIDI Export** | Download the generated mashup as a standard `.mid` file |
| `◎` | **Web Interface** | Clean, responsive Flask UI — works on desktop and mobile |

---

## Tech Stack

- **Backend** — Python, Flask, NumPy
- **GA Engine** — Custom implementation with crossover, mutation, and elitism
- **Audio** — pretty_midi for MIDI generation, Web Audio API for in-browser playback
- **Frontend** — Vanilla HTML/CSS/JS, Chart.js, Lucide Icons
- **Deployment** — Render (auto-deploy from GitHub)

---

## Running Locally

```bash
# Clone
git clone https://github.com/priyanshumodak/MelodyMorph-AI
cd MelodyMorph-AI

# Virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install & run
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## Project Structure

```
MelodyMorph-AI/
├── app.py                          # Flask server & API routes
├── requirements.txt                # Python dependencies
├── render.yaml                     # Render deployment config
├── backend/
│   ├── ga_engine/
│   │   ├── genetic_algorithm.py    # GA loop: selection, crossover, mutation
│   │   ├── chromosome.py          # Chromosome representation & MIDI export
│   │   └── fitness.py             # Multi-component fitness function
│   ├── feature_extraction/
│   │   └── midi_parser.py         # MIDI file parsing & feature extraction
│   └── utils/
│       └── dataset_manager.py     # Song loading, caching, sample generation
├── frontend/
│   ├── templates/index.html       # Single-page UI
│   └── static/                    # CSS & JS assets
└── data/
    └── feature_cache.pkl          # Pre-processed song cache (50 songs)
```

---

## How It Works

```
  Song A ──┐                    ┌── Selection ── Crossover ── Mutation ──┐
            ├── Initial Pop. ──►│         Genetic Algorithm Loop         │──► Best Mashup ──► MIDI
  Song B ──┘                    └── Fitness Evaluation (raga + rhythm) ──┘
```

1. **Initialization** — Tracks from both songs are combined into an initial population of chromosomes
2. **Fitness Evaluation** — Each chromosome is scored on melodic coherence, rhythmic stability, and raga compatibility
3. **Evolution** — Top candidates are selected; crossover and mutation produce the next generation
4. **Output** — The highest-fitness chromosome is exported as a downloadable MIDI file

---

## Requirements

- Python 3.8+
- 4 GB RAM (for dataset processing)
- Modern browser (Chrome, Firefox, Edge, Safari)

---

<p align="center">
  Built with genetic algorithms and a love for music.
</p>
