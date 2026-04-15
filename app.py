"""
MelodyMorph AI - Evolutionary Music Mashup
Main application file - FIXED VERSION
"""

import os
import random
import glob
from flask import Flask, render_template, jsonify, request, send_file
import numpy as np
import json
import time
from backend.ga_engine.genetic_algorithm import BollywoodGA
from backend.utils.dataset_manager import DatasetManager

app = Flask(__name__, 
            template_folder='frontend/templates',
            static_folder='frontend/static')

# Initialize dataset manager
dataset_manager = DatasetManager()

# Check if we have songs (loaded automatically in __init__)
if dataset_manager.get_song_count() == 0:
    print("📀 No songs found, creating sample dataset...")
    dataset_manager.add_sample_dataset()

print(f"📊 Total songs available: {dataset_manager.get_song_count()}")
print("=" * 50)

# Store active GA runs
active_runs = {}

# Shuffled index map: frontend_index -> dataset_index
# Re-shuffled on each /api/songs call for variety
_song_index_map = []

def _build_song_index_map():
    """Build a freshly shuffled index map from dataset"""
    global _song_index_map
    count = dataset_manager.get_song_count()
    _song_index_map = list(range(count))
    random.shuffle(_song_index_map)

def _cleanup_old_midi_files(keep_last=5):
    """Delete old generated MIDI files, keeping only the most recent N"""
    generated_dir = os.path.join('data', 'generated')
    midi_files = sorted(
        glob.glob(os.path.join(generated_dir, '*.mid')),
        key=os.path.getmtime
    )
    # Remove all but the last `keep_last` files
    for old_file in midi_files[:-keep_last] if len(midi_files) > keep_last else []:
        try:
            os.remove(old_file)
            print(f"🗑️  Cleaned up old file: {os.path.basename(old_file)}")
        except Exception as e:
            print(f"Warning: could not delete {old_file}: {e}")

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """API endpoint to check if server is running"""
    return jsonify({
        'status': 'online',
        'message': 'MelodyMorph AI is ready!',
        'version': '1.0.0',
        'songs_available': dataset_manager.get_song_count()
    })

@app.route('/api/songs')
def get_songs():
    """Get list of available songs - reshuffled each call for variety"""
    _build_song_index_map()
    all_names = dataset_manager.get_song_names()
    # Return names in shuffled order
    shuffled_names = [all_names[i] for i in _song_index_map]
    return jsonify({
        'songs': shuffled_names,
        'count': len(shuffled_names)
    })

def _resolve_idx(frontend_idx):
    """Translate frontend (shuffled) index to actual dataset index"""
    if _song_index_map and 0 <= frontend_idx < len(_song_index_map):
        return _song_index_map[frontend_idx]
    return frontend_idx  # fallback

@app.route('/api/preview/<int:song_idx>')
def preview_song(song_idx):
    """Generate and return a 10-second MIDI preview of a song"""
    try:
        song = dataset_manager.get_song(_resolve_idx(song_idx))
        if not song:
            return jsonify({'error': 'Song not found'}), 404
        
        import pretty_midi
        
        # Create a short MIDI from the song's tracks
        midi = pretty_midi.PrettyMIDI(initial_tempo=song.get('tempo', 120))
        
        # Use melody track (index 2) or fallback to any available track
        tracks = song.get('tracks', [])
        track_to_use = None
        for idx in [2, 1, 0]:  # Prefer melody, then bass, then drums
            if idx < len(tracks) and tracks[idx]:
                track_to_use = tracks[idx]
                break
        
        if not track_to_use:
            return jsonify({'error': 'No playable track found'}), 404
        
        # Find the starting time (first note)
        first_note_start = float('inf')
        for note in track_to_use:
            if note['start'] < first_note_start:
                first_note_start = note['start']
                
        if first_note_start == float('inf'):
            return jsonify({'error': 'Track is empty'}), 404
            
        # Filter notes to first 10 seconds after the first note
        notes_json = []
        for note in track_to_use:
            if note['start'] >= first_note_start and note['start'] < first_note_start + 10.0:
                end = min(note['end'], first_note_start + 10.0)
                notes_json.append({
                    'velocity': min(120, max(40, note.get('velocity', 90))),
                    'pitch': max(21, min(108, int(note['pitch']))),
                    'start': note['start'] - first_note_start,
                    'end': end - first_note_start
                })
                
        if not notes_json:
            return jsonify({'error': 'No notes in preview range'}), 404
        
        return jsonify({'notes': notes_json})
    except Exception as e:
        print(f"Preview error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mashup_preview/<run_id>')
def preview_mashup(run_id):
    """Generate and return a preview of the generated mashup"""
    try:
        if run_id not in active_runs:
            return jsonify({'error': 'Run not found'}), 404
            
        midi_file = active_runs[run_id]['midi_file']
        midi_path = os.path.join('data', 'generated', midi_file)
        
        if not os.path.exists(midi_path):
            return jsonify({'error': 'MIDI file not found'}), 404
            
        import pretty_midi
        pm = pretty_midi.PrettyMIDI(midi_path)
        
        all_notes = []
        for instrument in pm.instruments:
            if not instrument.is_drum:
                for note in instrument.notes:
                    all_notes.append({
                        'pitch': note.pitch,
                        'start': note.start,
                        'end': note.end,
                        'velocity': note.velocity
                    })
        
        if not all_notes:
            return jsonify({'error': 'No notes found in mashup'}), 404
            
        # Sort by start time
        all_notes.sort(key=lambda x: x['start'])
        
        # Take first 30 seconds for mashup preview
        first_note_start = all_notes[0]['start']
        notes_json = []
        for note in all_notes:
            if note['start'] < first_note_start + 30.0:
                end = min(note['end'], first_note_start + 30.0)
                notes_json.append({
                    'pitch': int(note['pitch']),
                    'start': note['start'] - first_note_start,
                    'end': end - first_note_start,
                    'velocity': int(note['velocity'])
                })
                
        return jsonify({'notes': notes_json})
    except Exception as e:
        print(f"Mashup preview error: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    error_details = {
        "error": str(e),
        "type": type(e).__name__,
        "traceback": traceback.format_exc()
    }
    print(f"❌ SERVER ERROR: {error_details['error']}")
    print(error_details['traceback'])
    return jsonify(error_details), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate mashup using GA"""
    try:
        data = request.json
        song1_idx = _resolve_idx(int(data.get('song1', 0)))
        song2_idx = _resolve_idx(int(data.get('song2', 1)))
        generations = min(int(data.get('generations', 50)), 50)      # cap: Render timeout safety
        population_size = min(int(data.get('population_size', 40)), 40)  # cap: memory safety
        
        # Clean up old generated files before creating a new one
        _cleanup_old_midi_files(keep_last=5)
        
        print(f"\n🎮 Generating mashup:")
        print(f"   Song 1: {dataset_manager.get_song_names()[song1_idx]}")
        print(f"   Song 2: {dataset_manager.get_song_names()[song2_idx]}")
        print(f"   Generations: {generations}")
        print(f"   Population: {population_size}")
        
        # Prepare data for GA
        ga_input = dataset_manager.prepare_for_ga(song1_idx, song2_idx)
        
        # Create and run GA
        ga = BollywoodGA(
            source_tracks=ga_input['source_tracks'],
            source_features=ga_input['source_features'],
            population_size=population_size,
            elite_size=population_size // 5,
            mutation_rate=0.1,
            crossover_rate=0.7
        )
        
        # Initialize population
        ga.initialize_population()
        
        # Run evolution
        results = ga.run(generations=generations)
        
        # Get best chromosome
        best = ga.get_best()
        
        # Generate MIDI file
        timestamp = int(time.time())
        midi_filename = f"mashup_{timestamp}.mid"
        midi_path = os.path.join('data', 'generated', midi_filename)
        best.to_midi(midi_path)
        
        # Store run info (cap at 5 to prevent memory growth on Render)
        run_id = str(timestamp)
        active_runs[run_id] = {
            'ga': ga,
            'best': best,
            'song1': ga_input['song1_name'],
            'song2': ga_input['song2_name'],
            'midi_file': midi_filename
        }
        # Evict oldest runs beyond the cap
        if len(active_runs) > 5:
            oldest_key = next(iter(active_runs))
            active_runs.pop(oldest_key, None)
        
        # Prepare response
        response = {
            'success': True,
            'run_id': run_id,
            'best_fitness': best.fitness,
            'fitness_components': best.fitness_components,
            'fitness_history': results['fitness_history'],
            'avg_fitness_history': results['avg_fitness_history'],
            'generations': generations,
            'time_taken': results['time_taken'],
            'song1': ga_input['song1_name'],
            'song2': ga_input['song2_name'],
            'midi_file': midi_filename
        }
        
        print(f"✅ Generation complete! Best fitness: {best.fitness:.3f}")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download/<run_id>')
def download_midi(run_id):
    """Download generated MIDI file"""
    if run_id in active_runs:
        midi_file = active_runs[run_id]['midi_file']
        midi_path = os.path.join('data', 'generated', midi_file)
        if os.path.exists(midi_path):
            return send_file(midi_path, as_attachment=True, 
                           download_name=f"melodymorph_{run_id}.mid")
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/run/<run_id>')
def get_run_info(run_id):
    """Get information about a specific run"""
    if run_id in active_runs:
        run = active_runs[run_id]
        best = run['best']
        return jsonify({
            'success': True,
            'song1': run['song1'],
            'song2': run['song2'],
            'best_fitness': best.fitness,
            'fitness_components': best.fitness_components,
            'midi_file': run['midi_file']
        })
    return jsonify({'error': 'Run not found'}), 404

# Ensure required directories exist
os.makedirs('data/generated', exist_ok=True)

if __name__ == '__main__':
    print("\n🎵 Starting MelodyMorph AI...")
    print(f"📀 {dataset_manager.get_song_count()} songs loaded!")
    port = int(os.environ.get('PORT', 5000))
    print(f"📍 Open http://127.0.0.1:{port} in your browser")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)