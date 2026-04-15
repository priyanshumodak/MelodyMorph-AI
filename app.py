"""
MelodyMorph AI - Evolutionary Music Mashup
UPDATED VERSION with GAN integration
"""

import os
import random
import glob
from flask import Flask, render_template, jsonify, request, send_file
import numpy as np
import json
import time
import torch
from backend.ga_engine.genetic_algorithm import BollywoodGA
from backend.utils.dataset_manager import DatasetManager
from backend.utils.midi_generator import gan_to_midi

# ✅ NEW IMPORT (GAN)
from models.gan import Generator

app = Flask(__name__, 
            template_folder='frontend/templates',
            static_folder='frontend/static')

# ✅ Initialize GAN
generator = Generator()

try:
    generator.load_state_dict(torch.load("generator_wgan.pth"))
    generator.eval()
    print("✅ GAN model loaded successfully")
except:
    print("⚠️ No trained model found, using random weights")

# Initialize dataset manager
dataset_manager = DatasetManager()

if dataset_manager.get_song_count() == 0:
    print("📀 No songs found, creating sample dataset...")
    dataset_manager.add_sample_dataset()

print(f"📊 Total songs available: {dataset_manager.get_song_count()}")
print("🎵 Song names:", dataset_manager.get_song_names())
print("=" * 50)

active_runs = {}
_song_index_map = []

def _build_song_index_map():
    global _song_index_map
    count = dataset_manager.get_song_count()
    _song_index_map = list(range(count))
    random.shuffle(_song_index_map)

def _cleanup_old_midi_files(keep_last=5):
    generated_dir = os.path.join('data', 'generated')
    midi_files = sorted(
        glob.glob(os.path.join(generated_dir, '*.mid')),
        key=os.path.getmtime
    )
    for old_file in midi_files[:-keep_last] if len(midi_files) > keep_last else []:
        try:
            os.remove(old_file)
        except Exception as e:
            print(f"Warning: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'online',
        'songs_available': dataset_manager.get_song_count()
    })

@app.route('/api/songs')
def get_songs():
    _build_song_index_map()
    all_names = dataset_manager.get_song_names()
    shuffled_names = [all_names[i] for i in _song_index_map]
    return jsonify({
        'songs': shuffled_names,
        'count': len(shuffled_names)
    })

def _resolve_idx(frontend_idx):
    if _song_index_map and 0 <= frontend_idx < len(_song_index_map):
        return _song_index_map[frontend_idx]
    return frontend_idx

# 🔥 NEW ROUTE (GAN AI GENERATION)
@app.route('/generate_ai', methods=['GET'])
def generate_ai_music():
    try:
        noise = torch.randn(1, 100)
        output = generator(noise).detach().numpy()[0]

        midi_file = "gan_output.mid"
        gan_to_midi(output, midi_file)

        return jsonify({
            "success": True,
            "file": midi_file
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/gan_output.mid')
def serve_midi():
    return send_file("gan_output.mid", as_attachment=False)

# ===== EXISTING GA CODE (UNCHANGED) =====

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        song1_idx = _resolve_idx(int(data.get('song1', 0)))
        song2_idx = _resolve_idx(int(data.get('song2', 1)))
        generations = min(int(data.get('generations', 50)), 50)
        population_size = min(int(data.get('population_size', 40)), 40)

        _cleanup_old_midi_files()

        ga_input = dataset_manager.prepare_for_ga(song1_idx, song2_idx)

        ga = BollywoodGA(
            source_tracks=ga_input['source_tracks'],
            source_features=ga_input['source_features'],
            population_size=population_size,
            elite_size=population_size // 5,
            mutation_rate=0.1,
            crossover_rate=0.7
        )

        ga.initialize_population()
        results = ga.run(generations=generations)
        best = ga.get_best()

        timestamp = int(time.time())
        midi_filename = f"mashup_{timestamp}.mid"
        midi_path = os.path.join('data', 'generated', midi_filename)
        best.to_midi(midi_path)

        run_id = str(timestamp)
        active_runs[run_id] = {
            'best': best,
            'song1': ga_input['song1_name'],
            'song2': ga_input['song2_name'],
            'midi_file': midi_filename
        }

        return jsonify({
            'success': True,
            'run_id': run_id,
            'best_fitness': best.fitness,
            'midi_file': midi_filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<run_id>')
def download_midi(run_id):
    if run_id in active_runs:
        midi_file = active_runs[run_id]['midi_file']
        midi_path = os.path.join('data', 'generated', midi_file)
        if os.path.exists(midi_path):
            return send_file(midi_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

os.makedirs('data/generated', exist_ok=True)

@app.route('/api/preview/<int:song_idx>')
def preview_song(song_idx):
    """Return dummy preview notes (safe fallback)"""
    try:
        notes_json = []
        
        # Generate simple melody (so UI works)
        for i in range(20):
            notes_json.append({
                'pitch': random.randint(60, 80),
                'start': i * 0.5,
                'end': i * 0.5 + 0.3,
                'velocity': 80
            })

        return jsonify({'notes': notes_json})

    except Exception as e:
        return jsonify({'error': str(e)}), 500@app.route('/api/preview/<int:song_idx>')
def preview_song(song_idx):
    """Return dummy preview notes (safe fallback)"""
    try:
        notes_json = []
        
        # Generate simple melody (so UI works)
        for i in range(20):
            notes_json.append({
                'pitch': random.randint(60, 80),
                'start': i * 0.5,
                'end': i * 0.5 + 0.3,
                'velocity': 80
            })

        return jsonify({'notes': notes_json})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n🎵 Starting MelodyMorph AI...")
    port = int(os.environ.get('PORT', 5000))
    print(f"📍 http://127.0.0.1:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)