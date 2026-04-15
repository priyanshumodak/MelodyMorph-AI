"""
Chromosome representation for Bollywood mashup
Each chromosome is a potential mashup solution
UPDATED VERSION - VERTICAL MASHUP (tracks play simultaneously)
"""

import random
import numpy as np
import os

# Try to import pretty_midi
try:
    import pretty_midi
    HAS_PRETTY_MIDI = True
except ImportError:
    print("⚠️ pretty_midi not installed. Install with: pip install pretty_midi")
    HAS_PRETTY_MIDI = False

class BollywoodChromosome:
    """
    Represents a mashup candidate with multiple tracks playing simultaneously
    """
    
    def __init__(self, track_data=None):
        """Initialize with optional track data"""
        self.tracks = track_data or []  # List of tracks, each track is list of notes
        self.control_genes = {
            'pitch_shifts': [0, 0, 0],      # Semitones per track
            'tempo_scales': [1.0, 1.0, 1.0], # Time stretch factors
            'track_volumes': [100, 80, 90],  # Volume levels
            'instrument_choices': [0, 0, 0]  # Instrument variations
        }
        self.fitness = 0.0
        self.fitness_components = {}
        self.id = random.randint(1000, 9999)  # Random ID for tracking
        self.creation_generation = 0
        
    def copy(self):
        """Create a deep copy of this chromosome"""
        new_c = BollywoodChromosome([track[:] for track in self.tracks])
        new_c.control_genes = {k: v.copy() for k, v in self.control_genes.items()}
        new_c.fitness = self.fitness
        new_c.fitness_components = self.fitness_components.copy()
        new_c.creation_generation = self.creation_generation
        return new_c
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'fitness': self.fitness,
            'fitness_components': self.fitness_components,
            'control_genes': self.control_genes,
            'track_count': len(self.tracks),
            'note_counts': [len(track) for track in self.tracks]
        }
    
    def to_midi(self, output_path):
        """
        Convert chromosome to MIDI file with MULTI-TRACK mixing (vertical mashup)
        All tracks play SIMULTANEOUSLY
        """
        if not HAS_PRETTY_MIDI:
            print("⚠️ pretty_midi not installed, cannot create MIDI")
            return False
        
        try:
            # Create MIDI object
            midi = pretty_midi.PrettyMIDI(initial_tempo=120)
            
            # Instrument mapping for different tracks
            instrument_programs = {
                'drums': [0, 16, 24, 25, 26],      # Piano, Organ, Guitar, Nylon Guitar, Steel Guitar
                'bass': [32, 33, 34, 35, 43],       # Bass, Bass, Bass, Bass, Contrabass
                'melody': [40, 41, 42, 48, 56]      # Violin, Viola, Cello, Strings, Trumpet
            }
            
            # TRACK 0: Drums/Percussion (plays simultaneously with others)
            if len(self.tracks) > 0 and self.tracks[0]:
                # Choose instrument
                instrument_idx = self.control_genes['instrument_choices'][0] % len(instrument_programs['drums'])
                program = instrument_programs['drums'][instrument_idx]
                
                # Use normal instrument for track 0 (forcing it to drums causes silence for melody)
                drum_instrument = pretty_midi.Instrument(program=program, name='Rhythm')
                
                for note in self.tracks[0]:
                    # Apply tempo scaling only (drums don't pitch shift)
                    tempo_scale = self.control_genes['tempo_scales'][0]
                    start = note['start'] * tempo_scale
                    end = note['end'] * tempo_scale
                    
                    # Ensure valid note duration
                    if end <= start:
                        end = start + 0.1
                    
                    # Apply volume
                    velocity = int(note.get('velocity', 100) * self.control_genes['track_volumes'][0] / 100)
                    velocity = max(60, min(120, velocity)) # Increased minimum volume
                    
                    midi_note = pretty_midi.Note(
                        velocity=velocity,
                        pitch=note['pitch'],
                        start=start,
                        end=end
                    )
                    drum_instrument.notes.append(midi_note)
                
                if drum_instrument.notes:
                    midi.instruments.append(drum_instrument)
            
            # TRACK 1: Bass/Harmony (plays simultaneously with others)
            if len(self.tracks) > 1 and self.tracks[1]:
                # Choose instrument
                instrument_idx = self.control_genes['instrument_choices'][1] % len(instrument_programs['bass'])
                program = instrument_programs['bass'][instrument_idx]
                
                bass_instrument = pretty_midi.Instrument(program=program, name='Bass')
                
                for note in self.tracks[1]:
                    # Apply pitch shift
                    pitch_shift = self.control_genes['pitch_shifts'][1]
                    # Limit extreme shifts
                    if abs(pitch_shift) > 5:
                        pitch_shift = 5 if pitch_shift > 0 else -5
                    
                    pitch = note['pitch'] + pitch_shift
                    pitch = max(30, min(100, int(pitch)))
                    
                    # Apply tempo scaling
                    tempo_scale = self.control_genes['tempo_scales'][1]
                    start = note['start'] * tempo_scale
                    end = note['end'] * tempo_scale
                    
                    # Ensure valid note duration
                    if end <= start:
                        end = start + 0.1
                    
                    # Apply volume
                    velocity = int(note.get('velocity', 80) * self.control_genes['track_volumes'][1] / 100)
                    velocity = max(50, min(120, velocity))
                    
                    midi_note = pretty_midi.Note(
                        velocity=velocity,
                        pitch=pitch,
                        start=start,
                        end=end
                    )
                    bass_instrument.notes.append(midi_note)
                
                if bass_instrument.notes:
                    midi.instruments.append(bass_instrument)
            
            # TRACK 2: Melody (plays simultaneously with others)
            if len(self.tracks) > 2 and self.tracks[2]:
                # Choose instrument
                instrument_idx = self.control_genes['instrument_choices'][2] % len(instrument_programs['melody'])
                program = instrument_programs['melody'][instrument_idx]
                
                melody_instrument = pretty_midi.Instrument(program=program, name='Melody')
                
                for note in self.tracks[2]:
                    # Apply pitch shift
                    pitch_shift = self.control_genes['pitch_shifts'][2]
                    if abs(pitch_shift) > 5:
                        pitch_shift = 5 if pitch_shift > 0 else -5
                    
                    pitch = note['pitch'] + pitch_shift
                    pitch = max(40, min(90, int(pitch)))
                    
                    # Apply tempo scaling
                    tempo_scale = self.control_genes['tempo_scales'][2]
                    start = note['start'] * tempo_scale
                    end = note['end'] * tempo_scale
                    
                    # Ensure valid note duration
                    if end <= start:
                        end = start + 0.1
                    
                    # Apply volume
                    velocity = int(note.get('velocity', 90) * self.control_genes['track_volumes'][2] / 100)
                    velocity = max(50, min(120, velocity))
                    
                    midi_note = pretty_midi.Note(
                        velocity=velocity,
                        pitch=pitch,
                        start=start,
                        end=end
                    )
                    melody_instrument.notes.append(midi_note)
                
                if melody_instrument.notes:
                    midi.instruments.append(melody_instrument)
            
            # Save MIDI file
            if midi.instruments:
                total_notes = sum(len(inst.notes) for inst in midi.instruments)
                if total_notes == 0:
                    print("⚠️ WARNING: MIDI object has instruments but ZERO notes!")
                    return False
                
                midi.write(output_path)
                print(f"✅ Created vertical mashup with {len(midi.instruments)} tracks and {total_notes} notes")
                return True
            else:
                print("⚠️ No instruments with notes to save")
                return False
            
        except Exception as e:
            print(f"Error creating MIDI: {e}")
            return False
    
    @staticmethod
    def _normalize_track(track):
        """Shift all notes so the track starts at time 0"""
        if not track:
            return []
        t = sorted(track, key=lambda n: n['start'])
        offset = t[0]['start']
        return [{**n, 'start': round(n['start'] - offset, 4),
                      'end':   round(n['end']   - offset, 4)} for n in t]

    @staticmethod
    def _loop_track(track, target_duration):
        """
        Repeat a (normalized) track until it fills target_duration seconds.
        This ensures we always have enough material to blend.
        """
        if not track:
            return []
        src_dur = max(n['end'] for n in track) if track else 0.0
        if src_dur <= 0:
            return [n.copy() for n in track]

        result = []
        offset = 0.0
        while offset < target_duration:
            for note in track:
                new_start = round(note['start'] + offset, 4)
                new_end   = round(note['end']   + offset, 4)
                if new_start >= target_duration:
                    continue
                result.append({
                    'pitch':    note['pitch'],
                    'start':    new_start,
                    'end':      min(new_end, target_duration),
                    'velocity': note.get('velocity', 80),
                    'duration': round(min(new_end, target_duration) - new_start, 4)
                })
            offset += src_dur
        return result

    @staticmethod
    def _blend_two_tracks(track1, track2, segment_sec=6.0, total_duration=30.0):
        """
        TRUE MASHUP: loop both tracks to fill total_duration, then alternate
        segments so BOTH songs are clearly audible throughout the output.

        Output structure (example, segment_sec=6, total=30s):
          0-6s  → Song 1
          6-12s → Song 2
          12-18s→ Song 1
          18-24s→ Song 2
          24-30s→ Song 1
        """
        t1n = BollywoodChromosome._normalize_track(track1)
        t2n = BollywoodChromosome._normalize_track(track2)

        t1_long = BollywoodChromosome._loop_track(t1n, total_duration)
        t2_long = BollywoodChromosome._loop_track(t2n, total_duration)

        # Fallback if one song is empty
        if not t1_long:
            return t2_long
        if not t2_long:
            return t1_long

        result = []
        seg_idx = 0
        cursor  = 0.0

        while cursor < total_duration:
            seg_end = min(cursor + segment_sec, total_duration)
            src = t1_long if seg_idx % 2 == 0 else t2_long

            for note in src:
                if note['start'] >= cursor and note['start'] < seg_end:
                    result.append(note.copy())

            cursor  = seg_end
            seg_idx += 1

        return result

    @staticmethod
    def create_random(source_tracks):
        """
        Create random chromosome by OVERLAYING both songs simultaneously.
        Both songs' notes go into each track slot at the same time —
        the GA then evolves pitch_shifts / tempo_scales to make them harmonize.
        """
        chromosome = BollywoodChromosome()
        chromosome.tracks = []

        # Separate the two songs' track lists
        song_track_lists = []
        for item in source_tracks:
            if item and isinstance(item[0], list):
                song_track_lists.append(item)
            elif item:
                song_track_lists.append([item])

        while len(song_track_lists) < 2:
            song_track_lists.append([[], [], []])

        tracks1 = list(song_track_lists[0])
        tracks2 = list(song_track_lists[1])

        while len(tracks1) < 3: tracks1.append([])
        while len(tracks2) < 3: tracks2.append([])

        total_dur = 30.0   # output length

        for i in range(3):
            t1 = tracks1[i] if tracks1[i] else []
            t2 = tracks2[i] if tracks2[i] else []

            t1n = BollywoodChromosome._normalize_track(t1)
            t2n = BollywoodChromosome._normalize_track(t2)

            t1_long = BollywoodChromosome._loop_track(t1n, total_dur)
            t2_long = BollywoodChromosome._loop_track(t2n, total_dur)

            # ── TRUE OVERLAY: both songs play at the same time ──
            merged = t1_long + t2_long
            merged.sort(key=lambda n: n['start'])
            chromosome.tracks.append(merged)

        # Random initial pitch shifts so the GA has variety to evolve from
        chromosome.control_genes['pitch_shifts']       = [random.randint(-3, 3) for _ in range(3)]
        chromosome.control_genes['tempo_scales']       = [round(random.uniform(0.95, 1.05), 2) for _ in range(3)]
        chromosome.control_genes['track_volumes']      = [random.randint(70, 100) for _ in range(3)]
        chromosome.control_genes['instrument_choices'] = [random.randint(0, 4)    for _ in range(3)]

        return chromosome



    
    def crossover(self, other, point=None):
        """
        Create two children by mixing with another chromosome
        """
        if point is None:
            point = random.randint(0, len(self.tracks))
        
        child1_tracks = []
        child2_tracks = []
        
        for i in range(len(self.tracks)):
            if i < point:
                child1_tracks.append([note.copy() for note in self.tracks[i]] if self.tracks[i] else [])
                child2_tracks.append([note.copy() for note in other.tracks[i]] if other.tracks[i] else [])
            else:
                child1_tracks.append([note.copy() for note in other.tracks[i]] if other.tracks[i] else [])
                child2_tracks.append([note.copy() for note in self.tracks[i]] if self.tracks[i] else [])
        
        child1 = BollywoodChromosome(child1_tracks)
        child2 = BollywoodChromosome(child2_tracks)
        
        # Mix control genes
        for key in self.control_genes:
            # 50% chance to take from either parent
            if random.random() > 0.5:
                child1.control_genes[key] = self.control_genes[key].copy()
                child2.control_genes[key] = other.control_genes[key].copy()
            else:
                child1.control_genes[key] = other.control_genes[key].copy()
                child2.control_genes[key] = self.control_genes[key].copy()
            
            # Sometimes swap individual values
            if isinstance(child1.control_genes[key], list):
                for j in range(len(child1.control_genes[key])):
                    if random.random() < 0.3:
                        temp = child1.control_genes[key][j]
                        child1.control_genes[key][j] = child2.control_genes[key][j]
                        child2.control_genes[key][j] = temp
        
        return child1, child2
    
    def mutate(self, mutation_rate=0.1):
        """
        Apply random mutations to create a variant
        """
        mutated = BollywoodChromosome()
        mutated.tracks = []
        
        # Deep copy tracks
        for track in self.tracks:
            if track:
                mutated.tracks.append([note.copy() for note in track])
            else:
                mutated.tracks.append([])
        
        mutated.control_genes = {k: v.copy() for k, v in self.control_genes.items()}
        
        # Mutate pitch shifts
        for i in range(len(mutated.control_genes['pitch_shifts'])):
            if random.random() < mutation_rate:
                # Change by -1, 0, or +1
                mutated.control_genes['pitch_shifts'][i] += random.randint(-1, 1)
                # Keep in range
                mutated.control_genes['pitch_shifts'][i] = max(-3, min(3, 
                    mutated.control_genes['pitch_shifts'][i]))
        
        # Mutate tempo scales
        for i in range(len(mutated.control_genes['tempo_scales'])):
            if random.random() < mutation_rate:
                # Change by 2-5%
                mutated.control_genes['tempo_scales'][i] *= random.uniform(0.95, 1.05)
                # Keep in range
                mutated.control_genes['tempo_scales'][i] = max(0.85, min(1.15, 
                    mutated.control_genes['tempo_scales'][i]))
                mutated.control_genes['tempo_scales'][i] = round(
                    mutated.control_genes['tempo_scales'][i], 2)
        
        # Mutate volumes
        for i in range(len(mutated.control_genes['track_volumes'])):
            if random.random() < mutation_rate:
                mutated.control_genes['track_volumes'][i] += random.randint(-10, 10)
                mutated.control_genes['track_volumes'][i] = max(50, min(120, 
                    mutated.control_genes['track_volumes'][i]))
        
        # Mutate instrument choices
        for i in range(len(mutated.control_genes.get('instrument_choices', [0,0,0]))):
            if random.random() < mutation_rate:
                mutated.control_genes['instrument_choices'][i] = random.randint(0, 4)
        
        return mutated
    
    def __str__(self):
        return f"Chromosome #{self.id} | Fitness: {self.fitness:.3f}"