"""
Improved Fitness Functions for Better Sounding Mashups
"""

import numpy as np
from typing import Dict, List

class BollywoodFitness:
    """
    STRICT fitness evaluation for better sounding mashups
    """
    
    def __init__(self, source_features):
        self.source_features = source_features
        self.weights = {
            'key_compatibility': 0.35,     # 35% - Increased for better harmony
            'rhythm_alignment': 0.25,       # 25% - Increased for better groove
            'note_density': 0.10,            # 10%
            'pitch_range': 0.10,             # 10%
            'melodic_flow': 0.10,            # 10%
            'dissonance': 0.10               # 10%
        }
        
    def evaluate(self, chromosome):
        """
        Evaluate with STRICT penalties for bad combinations
        """
        # --- APPLY MUTATIONS FOR EVALUATION ---
        eval_tracks = []
        for i, track in enumerate(chromosome.tracks):
            if not track:
                eval_tracks.append([])
                continue
            
            pitch_shift = chromosome.control_genes['pitch_shifts'][i] if i < len(chromosome.control_genes['pitch_shifts']) else 0
            tempo_scale = chromosome.control_genes['tempo_scales'][i] if i < len(chromosome.control_genes['tempo_scales']) else 1.0
            
            eval_track = []
            for note in track:
                eval_track.append({
                    'pitch': note['pitch'] + pitch_shift,
                    'start': note['start'] * tempo_scale,
                    'end': note['end'] * tempo_scale,
                    'velocity': note.get('velocity', 90)
                })
            eval_tracks.append(eval_track)
            
        # Temporarily use mutated tracks for scoring
        original_tracks = chromosome.tracks
        chromosome.tracks = eval_tracks
        
        scores = {}
        
        # Calculate each component
        scores['key_compatibility'] = self._calculate_key_score(chromosome)
        scores['rhythm_alignment'] = self._calculate_rhythm_score(chromosome)
        scores['note_density'] = self._calculate_density_score(chromosome)
        scores['pitch_range'] = self._calculate_range_score(chromosome)
        scores['melodic_flow'] = self._calculate_melodic_score(chromosome)
        scores['dissonance'] = self._calculate_dissonance_score(chromosome)
        
        # Restore original unmutated tracks
        chromosome.tracks = original_tracks
        
        # Calculate weighted total
        total_fitness = sum(
            scores[key] * self.weights[key] 
            for key in scores
        )

        # Apply PENALTIES for obviously bad combinations
        penalty = 1.0
        
        # Penalty 1: Too many repeated notes (boring)
        if scores['melodic_flow'] < 0.3:
            penalty *= 0.7
            
        # Penalty 2: Extreme pitch shifts (sounds like chipmunks)
        if max(abs(s) for s in chromosome.control_genes['pitch_shifts']) > 5:
            penalty *= 0.5
            
        # Penalty 3: Tempo too different
        tempo1 = self.source_features.get('tempo1', 100)
        tempo2 = self.source_features.get('tempo2', 100)
        if abs(tempo1 - tempo2) > 30:
            penalty *= 0.8
            
        # Penalty 4: Lacking creativity (carbon copy of source)
        original = True
        for p in chromosome.control_genes['pitch_shifts']:
            if p != 0: original = False
        for t in chromosome.control_genes['tempo_scales']:
            if abs(t - 1.0) > 0.01: original = False
            
        if original:
            penalty *= 0.75  # 25% penalty for just copying the original track!
            
        # Penalty 5: Empty tracks (prefer verticality)
        non_empty_tracks = sum(1 for t in chromosome.tracks if t)
        if non_empty_tracks < 3:
            penalty *= (non_empty_tracks / 3.0)  # Linear penalty for missing tracks
            
        # Apply penalty
        chromosome.fitness = total_fitness * penalty
        chromosome.fitness_components = scores
        
        return scores
    
    def _calculate_key_score(self, chromosome):
        """
        STRICT key compatibility - must be close on circle of fifths
        """
        try:
            # Get keys from source features
            raga1 = self.source_features.get('raga1', {})
            raga2 = self.source_features.get('raga2', {})
            
            # If no key info, assume compatible
            if not raga1 or not raga2:
                return 0.8
            
            # Get root notes (simplified key detection)
            notes1 = set(raga1.get('notes', [0, 2, 4, 5, 7, 9, 11]))
            notes2 = set(raga2.get('notes', [0, 2, 4, 5, 7, 9, 11]))
            
            # Calculate overlap
            intersection = len(notes1 & notes2)
            original_overlap = intersection / max(len(notes1), len(notes2))
            
            # STEEPER GRADIENT: Square it to reward high overlap more than mediocre
            overlap = original_overlap ** 2
            
            # Bonus if they share characteristic notes
            vadi1 = raga1.get('vadi')
            vadi2 = raga2.get('vadi')
            
            if vadi1 and vadi2 and vadi1 == vadi2:
                overlap = min(1.0, overlap + 0.1)
            
            return overlap
            
        except Exception:
            return 0.5
    
    def _calculate_rhythm_score(self, chromosome):
        """
        Rhythmic alignment - beats must line up
        """
        try:
            # Get drum track
            drum_track = chromosome.tracks[0] if len(chromosome.tracks) > 0 else []
            
            if len(drum_track) < 4:
                return 0.5
            
            # Calculate beat intervals
            beat_times = [note['start'] for note in drum_track]
            intervals = np.diff(beat_times)
            
            if len(intervals) == 0:
                return 0.5
            
            # Good rhythm = consistent intervals (low std deviation)
            interval_std = np.std(intervals)
            mean_interval = np.mean(intervals)
            
            # Normalize: lower std = better
            if mean_interval == 0:
                consistency = 0.5
            else:
                consistency = 1.0 / (1.0 + interval_std / mean_interval)
            
            return min(1.0, consistency)
            
        except Exception:
            return 0.5
    
    def _calculate_density_score(self, chromosome):
        """
        Note density should match source songs
        """
        try:
            # Get source densities
            source1_density = self.source_features.get('density1', 4.0)
            source2_density = self.source_features.get('density2', 4.0)
            
            # Calculate target range
            min_density = min(source1_density, source2_density)
            max_density = max(source1_density, source2_density)
            
            # Calculate actual density (melody track)
            melody = chromosome.tracks[2] if len(chromosome.tracks) > 2 else []
            
            if len(melody) < 2:
                return 0.5
            
            time_range = melody[-1]['end'] - melody[0]['start']
            actual_density = len(melody) / time_range if time_range > 0 else 4.0
            
            # Score based on being WITHIN the range
            if min_density <= actual_density <= max_density:
                return 1.0
            elif actual_density < min_density:
                return actual_density / min_density
            else:
                return max_density / actual_density
            
        except Exception:
            return 0.5
    
    def _calculate_range_score(self, chromosome):
        """
        Pitch range should be similar to source songs
        """
        try:
            # Get melody track
            melody = chromosome.tracks[2] if len(chromosome.tracks) > 2 else []
            
            if len(melody) < 2:
                return 0.5
            
            pitches = [note['pitch'] for note in melody]
            actual_range = max(pitches) - min(pitches)
            
            # Ideal range for melody (about 2 octaves = 24 semitones)
            ideal_range = 24
            
            # Score based on closeness to ideal
            score = 1.0 - min(1.0, abs(actual_range - ideal_range) / ideal_range)
            
            return max(0.3, score)
            
        except Exception:
            return 0.5
    
    def _calculate_melodic_score(self, chromosome):
        """
        Smooth melodic lines without huge jumps
        """
        try:
            melody = chromosome.tracks[2] if len(chromosome.tracks) > 2 else []
            
            if len(melody) < 3:
                return 0.5
            
            # Calculate intervals between consecutive notes
            intervals = []
            for i in range(1, len(melody)):
                interval = abs(melody[i]['pitch'] - melody[i-1]['pitch'])
                intervals.append(interval)
            
            if not intervals:
                return 0.5
            
            # Good melodies:
            # 1. Not too many large jumps (> 12 semitones)
            large_jumps = sum(1 for i in intervals if i > 12)
            jump_penalty = large_jumps / len(intervals)
            
            # 2. Some variety (not all same interval)
            unique_intervals = len(set(intervals))
            variety = min(1.0, unique_intervals / 5)
            
            # 3. Mostly stepwise motion (intervals of 1-2 semitones)
            small_steps = sum(1 for i in intervals if i <= 2)
            step_weight = small_steps / len(intervals)
            
            # Combine
            score = (variety * 0.3) + (step_weight * 0.7)
            score = score * (1 - jump_penalty * 0.5)
            
            return min(1.0, max(0.2, score))
            
        except Exception:
            return 0.5
    
    def _calculate_dissonance_score(self, chromosome):
        """
        Avoid notes that clash when played together
        """
        try:
            # Get all tracks
            all_notes = []
            for track in chromosome.tracks:
                all_notes.extend(track)
            
            if len(all_notes) < 5:
                return 0.5
            
            # Check for dissonant intervals when notes play simultaneously
            dissonance_penalty = 0
            
            # Sort by start time
            all_notes.sort(key=lambda x: x['start'])
            
            # Check overlapping notes
            for i in range(len(all_notes)):
                note1 = all_notes[i]
                for j in range(i+1, min(i+10, len(all_notes))):
                    note2 = all_notes[j]
                    
                    # If notes overlap in time
                    if note2['start'] < note1['end']:
                        interval = abs(note1['pitch'] - note2['pitch']) % 12
                        
                        # Dissonant intervals (in semitones)
                        dissonant = [1, 2, 6, 11]  # minor 2nd, major 2nd, tritone, major 7th.
                        
                        if interval in dissonant:
                            # Stricter penalty for half-steps (most dissonant)
                            if interval == 1 or interval == 11:
                                dissonance_penalty += 3
                            else:
                                dissonance_penalty += 1
            
            # Normalize penalty
            total_overlaps = len(all_notes) * 5  # approximate
            if total_overlaps > 0:
                penalty_ratio = dissonance_penalty / total_overlaps
                score = 1.0 - min(1.0, penalty_ratio)
            else:
                score = 1.0
            
            return score
            
        except Exception:
            return 0.5