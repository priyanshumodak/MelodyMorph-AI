"""
Genetic Algorithm for Bollywood Mashup Generation
"""

import random
import numpy as np
from typing import List, Dict
from tqdm import tqdm
import time
from .chromosome import BollywoodChromosome
from .fitness import BollywoodFitness

class BollywoodGA:
    """
    Genetic Algorithm for Bollywood Mashup Generation
    """
    
    def __init__(self, 
                 source_tracks: List[List],
                 source_features: Dict,
                 population_size: int = 50,
                 elite_size: int = 10,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.7):
        
        self.source_tracks = source_tracks
        self.source_features = source_features
        self.population_size = population_size
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        # Pool of all available source tracks for mutations
        self.track_pool = []
        for track_list in source_tracks:
            if isinstance(track_list[0], list): # If it's a list of tracks (new format)
                for t in track_list: self.track_pool.append(t)
            else:
                self.track_pool.append(track_list)
        
        self.fitness_calculator = BollywoodFitness(source_features)
        self.population = []
        self.generation = 0
        self.best_fitness_history = []
        self.avg_fitness_history = []
        
        self.start_time = None
        self.end_time = None
        
    def initialize_population(self):
        """Create initial random population"""
        print("🎵 Initializing population...")
        self.population = []
        for i in range(self.population_size):
            chromosome = BollywoodChromosome.create_random(self.source_tracks)
            self.population.append(chromosome)
        
        # Evaluate initial population
        self._evaluate_population()
        print(f"✅ Initialized {self.population_size} chromosomes")
        print(f"   Best fitness: {self.population[0].fitness:.3f}")
        
    def _evaluate_population(self):
        """Evaluate fitness for entire population"""
        for chromosome in self.population:
            self.fitness_calculator.evaluate(chromosome)
        
        # Sort by fitness (descending)
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        
    def _selection(self) -> List[BollywoodChromosome]:
        """
        Tournament selection
        """
        selected = []
        
        # Keep elites (best chromosomes)
        selected.extend(self.population[:self.elite_size])
        
        # Tournament selection for rest
        while len(selected) < self.population_size:
            # Pick 5 random chromosomes
            tournament = random.sample(self.population, min(5, len(self.population)))
            # Select the best from tournament
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(winner)
        
        return selected
    
    def _crossover(self, parent1, parent2):
        """
        Create children by mixing parents
        Has 50% chance for Sectional (horizontal) or Vertical (track swap) crossover
        """
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        # 50% chance for Vertical Crossover (swapping whole tracks)
        if random.random() < 0.5:
            child1_tracks = [t[:] for t in parent1.tracks]
            child2_tracks = [t[:] for t in parent2.tracks]
            
            # Safely pick an index based on the available tracks
            available_tracks = min(len(parent1.tracks), len(parent2.tracks), 3)
            if available_tracks > 0:
                idx = random.randint(0, available_tracks - 1)
                child1_tracks[idx] = [n.copy() for n in parent2.tracks[idx]] if parent2.tracks[idx] else []
                child2_tracks[idx] = [n.copy() for n in parent1.tracks[idx]] if parent1.tracks[idx] else []
                
            child1 = BollywoodChromosome(child1_tracks)
            child2 = BollywoodChromosome(child2_tracks)
            
            # Inherit control genes
            child1.control_genes = parent1.control_genes.copy()
            child2.control_genes = parent2.control_genes.copy()
            return child1, child2

        # 50% Sectional Crossover (mixing segments)
        child1_tracks = []
        child2_tracks = []
        
        # Determine a random time split point (4-12 seconds)
        split_time = random.uniform(4.0, 10.0)
        
        for i in range(len(parent1.tracks)):
            p1_track = parent1.tracks[i]
            p2_track = parent2.tracks[i]
            
            p1_early = [n.copy() for n in p1_track if n['start'] < split_time]
            p1_late = [n.copy() for n in p1_track if n['start'] >= split_time]
            p2_early = [n.copy() for n in p2_track if n['start'] < split_time]
            p2_late = [n.copy() for n in p2_track if n['start'] >= split_time]
            
            child1_tracks.append(p1_early + p2_late)
            child2_tracks.append(p2_early + p1_late)
        
        return BollywoodChromosome(child1_tracks), BollywoodChromosome(child2_tracks)
    
    def _mutate(self, chromosome):
        """
        Apply random mutations
        """
        mutated = BollywoodChromosome([[n.copy() for n in track] for track in chromosome.tracks])
        mutated.control_genes = {k: v.copy() for k, v in chromosome.control_genes.items()}
        
        # Mutate pitch shifts
        for i in range(len(mutated.control_genes['pitch_shifts'])):
            if random.random() < self.mutation_rate * 2: # Double chance
                # Change by a guaranteed offset
                mutated.control_genes['pitch_shifts'][i] += random.choice([-2, -1, 1, 2])
                # Keep in range
                mutated.control_genes['pitch_shifts'][i] = max(-5, min(5, 
                    mutated.control_genes['pitch_shifts'][i]))
        
        # Mutate tempo scales (bigger jumps)
        for i in range(len(mutated.control_genes['tempo_scales'])):
            if random.random() < self.mutation_rate * 2:
                # Change by 5-15%
                mutated.control_genes['tempo_scales'][i] *= random.choice([random.uniform(0.85, 0.95), random.uniform(1.05, 1.15)])
                # Keep in range
                mutated.control_genes['tempo_scales'][i] = max(0.8, min(1.2, 
                    mutated.control_genes['tempo_scales'][i]))
                mutated.control_genes['tempo_scales'][i] = round(
                    mutated.control_genes['tempo_scales'][i], 2)
        
        # Swap whole track with one from pool (rare)
        if random.random() < self.mutation_rate:
            track_idx = random.randint(0, len(mutated.tracks) - 1)
            if self.track_pool:
                mutated.tracks[track_idx] = [n.copy() for n in random.choice(self.track_pool)]
        
        # Swap notes between tracks (rare)
        if random.random() < self.mutation_rate / 2:
            if len(mutated.tracks) >= 2:
                track1 = random.randint(0, len(mutated.tracks) - 1)
                track2 = random.randint(0, len(mutated.tracks) - 1)
                if (track1 != track2 and 
                    mutated.tracks[track1] and 
                    mutated.tracks[track2]):
                    idx1 = random.randint(0, len(mutated.tracks[track1]) - 1)
                    idx2 = random.randint(0, len(mutated.tracks[track2]) - 1)
                    (mutated.tracks[track1][idx1], 
                     mutated.tracks[track2][idx2]) = \
                        (mutated.tracks[track2][idx2], 
                         mutated.tracks[track1][idx1])
        
        return mutated
    
    def run(self, generations: int = 50):
        """
        Run the genetic algorithm
        """
        self.start_time = time.time()
        print(f"\n🎮 Starting GA with {generations} generations...")
        print("=" * 50)
        
        stalled_generations = 0
        last_best_fitness = -1.0
        
        for gen in range(generations):
            self.generation = gen
            
            # 1. ELITISM: Keep best individuals UNCHANGED
            elites = [c.copy() for c in self.population[:self.elite_size]]
            
            # 2. SELECTION: Choose parents for the rest of population
            selected = self._selection()
            
            # Create new population through crossover
            new_population = []
            for i in range(0, len(selected) - 1, 2):
                if i + 1 < len(selected):
                    child1, child2 = self._crossover(selected[i], selected[i+1])
                    new_population.append(child1)
                    new_population.append(child2)
            
            # Mutation
            mutated_population = []
            for chromosome in new_population:
                mutated = self._mutate(chromosome)
                mutated_population.append(mutated)
            
            # Ensure population size
            while len(mutated_population) < self.population_size:
                mutated_population.append(
                    BollywoodChromosome.create_random(self.source_tracks)
                )
            
            # 6. COMBINE: Elites + Mutated Children
            self.population = (elites + mutated_population)[:self.population_size]
            
            # Evaluate
            self._evaluate_population()
            
            # Track history
            self.best_fitness_history.append(self.population[0].fitness)
            self.avg_fitness_history.append(
                np.mean([c.fitness for c in self.population])
            )
            
            # Check for stall
            if self.population[0].fitness <= last_best_fitness + 0.0001:
                stalled_generations += 1
            else:
                stalled_generations = 0
                last_best_fitness = self.population[0].fitness
            
            # Mutation Boost if stalled
            original_mutation_rate = self.mutation_rate
            if stalled_generations >= 10:
                self.mutation_rate *= 2.0
                if gen % 5 == 0:
                    print(f"🔥 STALL DETECTED! Boosting mutation to {self.mutation_rate:.2f}")
            
            # Progress update every 5 generations
            if gen % 5 == 0 or gen == generations - 1:
                print(f"Gen {gen:3d} | Best: {self.population[0].fitness:.3f} | "
                      f"Avg: {self.avg_fitness_history[-1]:.3f} | "
                      f"Stall: {stalled_generations}")
            
            # Restore mutation rate if it was boosted
            self.mutation_rate = original_mutation_rate
        
        self.end_time = time.time()
        
        # Final report
        print("=" * 50)
        print(f"✅ GA Complete!")
        print(f"   Best fitness: {self.population[0].fitness:.3f}")
        print(f"   Time taken: {self.end_time - self.start_time:.1f} seconds")
        print(f"   Generations: {generations}")
        
        return {
            'best_fitness': self.population[0].fitness,
            'best_fitness_components': self.population[0].fitness_components,
            'fitness_history': self.best_fitness_history,
            'avg_fitness_history': self.avg_fitness_history,
            'generations': generations,
            'time_taken': self.end_time - self.start_time
        }
    
    def get_best(self):
        """Return the best chromosome"""
        return self.population[0]
    
    def get_top_n(self, n):
        """Return top N chromosomes"""
        return self.population[:min(n, len(self.population))]
    
    def get_population_stats(self):
        """Get statistics about current population"""
        if not self.population:
            return {}
        
        fitnesses = [c.fitness for c in self.population]
        return {
            'best': max(fitnesses),
            'worst': min(fitnesses),
            'average': np.mean(fitnesses),
            'std': np.std(fitnesses),
            'size': len(self.population)
        }