"""
Dataset Manager for handling Bollywood MIDI files
COMPLETE UPDATED VERSION - VERTICAL MASHUP support
"""

import os
import json
import pickle
import random
import numpy as np
from ..feature_extraction.midi_parser import BollywoodMIDIParser

class DatasetManager:
    """
    Manage Bollywood MIDI dataset
    """
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.midi_dir = os.path.join(data_dir, 'midi_files')
        self.real_midi_dir = os.path.join(data_dir, 'real_midi_files')
        self.processed_dir = os.path.join(data_dir, 'processed')
        self.cache_file = os.path.join(data_dir, 'feature_cache.pkl')
        
        # Create directories
        os.makedirs(self.midi_dir, exist_ok=True)
        os.makedirs(self.real_midi_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        
        self.parser = BollywoodMIDIParser()
        self.dataset = []
        
        # Cache-first: try loading from cache for instant startup
        self.load_cache()
        
        if len(self.dataset) > 0:
            print(f"⚡ Loaded {len(self.dataset)} songs from cache (instant)")
        else:
            # Only scan filesystem if cache is empty
            print("\n🔍 No cache found, scanning MIDI files from Discover MIDI...")
            loaded = self.load_discover_midi_files()
            
            if loaded > 0:
                print(f"✅ Successfully loaded {loaded} REAL MIDI files!")
                self._save_cache()
            else:
                print("📀 No MIDI files found, creating samples...")
                self.add_sample_dataset()
    
    def load_discover_midi_files(self):
        """
        DIRECTLY load MIDI files from Discover MIDI Dataset (including subfolders)
        Now with Bollywood filtering!
        """
        # Path to Discover MIDI
        discover_path = "Discover-MIDI-Dataset"
        if not os.path.exists(discover_path):
            print(f"❌ Discover MIDI not found at {discover_path}")
            return 0
        
        # Path to MIDIs folder
        midi_dir = os.path.join(discover_path, "MIDIs")
        if not os.path.exists(midi_dir):
            print(f"❌ MIDIs folder not found at {midi_dir}")
            return 0
        
        print(f"📁 Found MIDI folder at: {midi_dir}")
        
        # RECURSIVELY find all MIDI files in subfolders
        all_midis = []
        print("🔍 Searching for MIDI files in subfolders...")
        
        # Walk through all subfolders
        file_count = 0
        for root, dirs, files in os.walk(midi_dir):
            for file in files:
                if file.endswith('.mid') or file.endswith('.midi'):
                    file_count += 1
                    if file_count % 100000 == 0:  # Progress update every 100k files
                        print(f"   Found {file_count} files so far...")
                    full_path = os.path.join(root, file)
                    # Store relative path from midi_dir
                    rel_path = os.path.relpath(full_path, midi_dir)
                    all_midis.append(rel_path)
        
        print(f"📀 Found {len(all_midis)} total MIDI files in dataset")
        
        # ===== FILTER FOR BOLLYWOOD/INDIAN SONGS =====
        print("🔍 Filtering for Bollywood/Indian songs...")
        
        # Keywords that might indicate Bollywood/Indian music
        bollywood_keywords = [
            'bollywood', 'hindi', 'indian', 'bhangra', 'tamil', 'telugu',
            'raag', 'raga', 'desi', 'bolly', 'kumar', 'lata', 'rafi',
            'kishore', 'asha', 'sonu', 'shreya', 'arijit', 'himesh',
            'pritam', 'rahman', 'anand', 'rajesh', 'mukesh', 'mahendra',
            'hindustani', 'carnatic', 'filmi', 'sargam', 'taal', 'tala',
            'dhun', 'thumri', 'ghazal', 'bhajan', 'qawwali', 'sufi'
        ]
        
        # Filter MIDIs that might be Bollywood
        bollywood_midis = []
        for midi_path in all_midis:
            lower_path = midi_path.lower()
            if any(keyword in lower_path for keyword in bollywood_keywords):
                bollywood_midis.append(midi_path)
        
        print(f"🎵 Found {len(bollywood_midis)} potential Bollywood MIDI files")
        
        # If we found Bollywood songs, use those instead of random
        if len(bollywood_midis) > 0:
            all_midis = bollywood_midis
            print(f"✅ Using {len(all_midis)} Bollywood files!")
        else:
            print("⚠️ No Bollywood files found, using random files")
        # ===== END OF FILTER =====
        
        if len(all_midis) == 0:
            print("❌ No MIDI files found anywhere!")
            return 0
        
        # Show which subfolders have files
        subfolders = {}
        for midi_path in all_midis[:100]:  # Check first 100
            if '\\' in midi_path:
                folder = midi_path.split('\\')[0]
            elif '/' in midi_path:
                folder = midi_path.split('/')[0]
            else:
                folder = 'root'
            subfolders[folder] = subfolders.get(folder, 0) + 1
        
        print(f"📊 MIDI files distribution (sample):")
        for folder, count in list(subfolders.items())[:10]:
            print(f"   Folder '{folder}': {count} files in sample")
        
        # Load a variety of files from different subfolders
        sample_size = min(50, len(all_midis))
        
        # Use random sampling to get variety
        import random
        selected_indices = random.sample(range(len(all_midis)), sample_size)
        selected_midis = [all_midis[i] for i in selected_indices]
        
        print(f"📊 Loading {sample_size} random MIDI files from various subfolders...")
        
        loaded_count = 0
        for i, rel_path in enumerate(selected_midis):
            try:
                # Full path to file
                full_path = os.path.join(midi_dir, rel_path)
                filename = os.path.basename(rel_path)
                
                print(f"   Loading {i+1}/{sample_size}: {rel_path[:40]}...")
                
                parsed = self.parser.parse_midi(full_path)
                
                if parsed:
                    # Create a nice display name using the subfolder and filename
                    folder_name = os.path.dirname(rel_path)
                    if folder_name:
                        name = f"[{folder_name}] {filename}"
                    else:
                        name = filename
                    
                    name = name.replace('.mid', '').replace('.midi', '')
                    name = name.replace('_', ' ').replace('-', ' ')
                    
                    # Remove numbers at start
                    import re
                    name = re.sub(r'^\d+\s*', '', name)
                    
                    # Truncate if too long
                    if len(name) > 45:
                        name = name[:42] + "..."
                    
                    # If name is empty after cleaning, use path
                    if not name.strip():
                        name = f"Song from {folder_name if folder_name else 'root'}"
                    
                    # Add metadata
                    parsed['metadata'] = {
                        'name': name.strip(),
                        'original_filename': filename,
                        'folder': folder_name,
                        'full_path': rel_path,
                        'source': 'Discover MIDI',
                        'is_real': True,
                        'is_bollywood': any(k in rel_path.lower() for k in bollywood_keywords),
                        'index': i
                    }
                    
                    self.dataset.append(parsed)
                    loaded_count += 1
                    
            except Exception as e:
                print(f"      ⚠️ Error loading {rel_path}: {e}")
        
        print(f"✅ Loaded {loaded_count} MIDI files!")
        bollywood_count = sum(1 for s in self.dataset if s.get('metadata', {}).get('is_bollywood', False))
        print(f"   🎵 Bollywood files: {bollywood_count}")
        return loaded_count
    
    def add_sample_dataset(self):
        """Create sample dataset for testing"""
        print("📀 Creating sample dataset...")
        
        # Create 5 sample songs
        sample_songs = [
            {
                'name': 'Kal Ho Na Ho (Sample)',
                'raga': 'yaman',
                'tempo': 95,
                'mood': 'emotional',
                'scale': [0, 2, 4, 5, 7, 9, 11]
            },
            {
                'name': 'Tum Hi Ho (Sample)',
                'raga': 'bhairav',
                'tempo': 85,
                'mood': 'romantic',
                'scale': [0, 1, 4, 5, 7, 8, 11]
            },
            {
                'name': 'Bole Chudiyan (Sample)',
                'raga': 'desh',
                'tempo': 120,
                'mood': 'celebratory',
                'scale': [0, 2, 4, 5, 7, 9, 10]
            },
            {
                'name': 'Kabira (Sample)',
                'raga': 'bhimpalasi',
                'tempo': 90,
                'mood': 'soulful',
                'scale': [0, 2, 3, 5, 7, 8, 10]
            },
            {
                'name': 'Gerua (Sample)',
                'raga': 'kafi',
                'tempo': 100,
                'mood': 'romantic',
                'scale': [0, 2, 3, 5, 7, 8, 10]
            }
        ]
        
        for song in sample_songs:
            # Create dummy tracks
            tracks = self._create_dummy_tracks(song)
            
            # Create song entry
            song_entry = {
                'filename': f"{song['name']}.mid",
                'tracks': tracks,
                'track_types': ['drums', 'bass', 'melody'],
                'tempo': song['tempo'],
                'features': self._extract_features(tracks),
                'raga': {
                    'name': song['raga'],
                    'confidence': 0.8,
                    'notes': song['scale'],
                    'vadi': song['scale'][2] if len(song['scale']) > 2 else 0,
                    'samvadi': song['scale'][4] if len(song['scale']) > 4 else 7
                },
                'metadata': {
                    'name': song['name'],
                    'mood': song['mood'],
                    'source': 'sample',
                    'is_real': False
                }
            }
            
            self.dataset.append(song_entry)
        
        print(f"✅ Added {len(self.dataset)} sample songs")
    
    def _create_dummy_tracks(self, song_info):
        """Create dummy MIDI tracks for testing"""
        
        tracks = []
        scale = song_info['scale']
        tempo = song_info['tempo']
        
        # Make each song slightly different by using a seed
        seed = hash(song_info['name']) % 100
        
        # 1. Drum track with different patterns
        drums = []
        for i in range(0, 32):
            beat = i * (60 / tempo)
            # Different drum patterns based on song
            if seed % 3 == 0:
                # Pattern A
                if i % 4 == 0:
                    drums.append({
                        'pitch': 36,  # Bass drum
                        'start': beat,
                        'end': beat + 0.1,
                        'velocity': 100,
                        'duration': 0.1
                    })
            elif seed % 3 == 1:
                # Pattern B
                if i % 2 == 0:
                    drums.append({
                        'pitch': 38,  # Snare
                        'start': beat,
                        'end': beat + 0.1,
                        'velocity': 90,
                        'duration': 0.1
                    })
            else:
                # Pattern C
                if i % 6 == 0:
                    drums.append({
                        'pitch': 42,  # Closed hi-hat
                        'start': beat,
                        'end': beat + 0.1,
                        'velocity': 80,
                        'duration': 0.1
                    })
        tracks.append(drums)
        
        # 2. Bass track with different root notes
        bass = []
        base_note = 40 + (seed % 5)  # Different bass notes per song
        for i in range(0, 16):
            beat = i * (60 / tempo) * 2
            scale_note = scale[(i + seed) % len(scale)]
            bass.append({
                'pitch': base_note + scale_note,
                'start': beat,
                'end': beat + 0.8,
                'velocity': 80,
                'duration': 0.8
            })
        tracks.append(bass)
        
        # 3. Melody track with different patterns
        melody = []
        base_melody = 60 + (seed % 3)  # Different starting notes
        
        # Different melodic patterns
        if seed % 4 == 0:
            pattern = scale + scale[::-1]  # Up and down
        elif seed % 4 == 1:
            pattern = [scale[0], scale[2], scale[4], scale[6], scale[4], scale[2]]  # Arpeggio
        elif seed % 4 == 2:
            pattern = scale * 2  # Repetition
        else:
            pattern = scale + [scale[4], scale[5], scale[6]]  # Custom
        
        for i in range(0, 32):
            beat = i * (60 / tempo) / 2
            note_idx = i % len(pattern)
            melody.append({
                'pitch': base_melody + pattern[note_idx],
                'start': beat,
                'end': beat + 0.3,
                'velocity': 90,
                'duration': 0.3
            })
        tracks.append(melody)
        
        return tracks
    
    def _extract_features(self, tracks):
        """Extract basic features from tracks"""
        features = {
            'note_density': [],
            'pitch_range': [],
            'avg_pitch': []
        }
        
        for track in tracks:
            if track:
                pitches = [n['pitch'] for n in track]
                times = [n['start'] for n in track]
                
                if len(times) > 1:
                    duration = max(times) - min(times)
                    density = len(track) / duration if duration > 0 else 0
                else:
                    density = 1
                
                features['note_density'].append(density)
                features['pitch_range'].append(max(pitches) - min(pitches))
                features['avg_pitch'].append(np.mean(pitches))
            else:
                features['note_density'].append(0)
                features['pitch_range'].append(0)
                features['avg_pitch'].append(0)
        
        return features
    
    def _save_cache(self):
        """Save dataset to cache"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.dataset, f)
            print(f"💾 Saved {len(self.dataset)} songs to cache")
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def load_cache(self):
        """Load dataset from cache"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.dataset = pickle.load(f)
                print(f"📂 Loaded {len(self.dataset)} songs from cache")
            except Exception as e:
                print(f"Error loading cache: {e}")
                self.dataset = []
    
    def get_song(self, index):
        """Get song by index"""
        if 0 <= index < len(self.dataset):
            return self.dataset[index]
        return None
    
    def get_song_names(self):
        """Get list of readable song names"""
        names = []
        used_names = set()
        
        for i, song in enumerate(self.dataset):
            # Try to get a meaningful name
            if song.get('metadata', {}).get('is_real', False):
                # It's a real MIDI file - try to make a nice name
                folder = song['metadata'].get('folder', '')
                filename = song['metadata'].get('original_filename', '')
                is_bollywood = song['metadata'].get('is_bollywood', False)
                
                # Try to extract a meaningful name from the path
                # First, get just the filename without extension
                name = filename.replace('.mid', '').replace('.midi', '')
                
                # Check if it's a hash (all hex characters and long)
                if len(name) > 20 and all(c in '0123456789abcdef' for c in name.lower()):
                    # It's a hash filename - walk path parts to find a meaningful name
                    path_parts = song['metadata'].get('full_path', '').replace('/', '\\').split('\\')
                    meaningful_part = None
                    for part in reversed(path_parts[:-1]):
                        # Accept only parts that are NOT purely numeric and NOT short hex strings
                        if (part
                            and not part.strip().isdigit()
                            and len(part) > 1
                            and not all(c in '0123456789abcdef' for c in part.lower())):
                            meaningful_part = part
                            break
                    if meaningful_part:
                        name = f"Song from {meaningful_part}"
                    else:
                        name = f"Track {i+1}"
                
                # Clean up - replace underscores and hyphens with spaces
                name = name.replace('_', ' ').replace('-', ' ')
                
                # Capitalize words
                name = ' '.join(word.capitalize() for word in name.split())
                
                # Remove any weird characters
                import re
                name = re.sub(r'[^\w\s]', '', name)
                
                # Truncate if too long
                if len(name) > 35:
                    name = name[:32] + "..."
                
                # Add emoji based on type
                if is_bollywood:
                    display_name = f"🎬 {name}"  # Bollywood gets movie emoji
                else:
                    display_name = f"🎵 {name}"  # Others get music note
                
            else:
                # It's a sample Bollywood song
                base_name = song.get('metadata', {}).get('name', f"Sample {i+1}")
                display_name = f"🎬 {base_name}"
            
            # Make name unique if duplicate
            if display_name in used_names:
                counter = 2
                while f"{display_name} ({counter})" in used_names:
                    counter += 1
                display_name = f"{display_name} ({counter})"
            
            used_names.add(display_name)
            names.append(display_name)
        
        return names
    
    def get_song_count(self):
        """Get number of songs in dataset"""
        return len(self.dataset)
    
    def prepare_for_ga(self, song1_idx, song2_idx):
        """
        Prepare two songs for GA input - VERTICAL MASHUP version
        All tracks will play simultaneously
        """
        song1 = self.dataset[song1_idx]
        song2 = self.dataset[song2_idx]
        
        # Make sure we have enough tracks
        tracks1 = song1['tracks']
        tracks2 = song2['tracks']
        
        # Pad tracks if needed
        while len(tracks1) < 3:
            tracks1.append([])
        while len(tracks2) < 3:
            tracks2.append([])
        
        # VERTICAL MASHUP: All tracks play simultaneously
        # Drums from song1, Bass from song2, Melody from song1
        # PROVIDE ALL TRACKS: GA will pick and evolve from these
        source_tracks = [tracks1, tracks2]
        
        # Extract features for fitness functions
        source_features = {
            'raga1': song1.get('raga', {'name': 'unknown', 'notes': [0,2,4,5,7,9,11]}),
            'raga2': song2.get('raga', {'name': 'unknown', 'notes': [0,2,4,5,7,9,11]}),
            'density1': song1['features']['note_density'][2] if len(song1['features']['note_density']) > 2 else 4.0,
            'density2': song2['features']['note_density'][2] if len(song2['features']['note_density']) > 2 else 4.0,
            'tempo1': song1.get('tempo', 100),
            'tempo2': song2.get('tempo', 100)
        }
        
        # Get song names
        song1_name = song1.get('metadata', {}).get('name', 
                     song1.get('filename', 'Song 1').replace('.mid', ''))
        song2_name = song2.get('metadata', {}).get('name', 
                     song2.get('filename', 'Song 2').replace('.mid', ''))
        
        # Clean names
        song1_name = song1_name.replace('_', ' ').replace('-', ' ').strip()
        song2_name = song2_name.replace('_', ' ').replace('-', ' ').strip()
        
        # Add emoji for real songs
        if song1.get('metadata', {}).get('is_real', False):
            song1_name = f"🎵 {song1_name}"
        if song2.get('metadata', {}).get('is_real', False):
            song2_name = f"🎵 {song2_name}"
        
        # Truncate if needed
        if len(song1_name) > 35:
            song1_name = song1_name[:32] + "..."
        if len(song2_name) > 35:
            song2_name = song2_name[:32] + "..."
        
        return {
            'source_tracks': source_tracks,
            'source_features': source_features,
            'song1_name': song1_name,
            'song2_name': song2_name
        }