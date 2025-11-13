"""Genetic Algorithm optimizer for tanker stowage planning"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
import random
from models.ship import Ship, Tank
from models.cargo import Cargo, Receiver
from models.plan import StowagePlan, TankAssignment


@dataclass
class Chromosome:
    """Represents a solution (chromosome) in the genetic algorithm
    
    Each chromosome is a list of tuples: (cargo_unique_id, quantity)
    where each index corresponds to a tank ID in the ship.
    Empty tanks are represented as (None, 0).
    """
    genes: List[Tuple[Optional[str], float]]  # (cargo_id, quantity) for each tank
    tank_ids: List[str]  # Corresponding tank IDs
    
    def __post_init__(self):
        """Validate chromosome structure"""
        if len(self.genes) != len(self.tank_ids):
            raise ValueError("Genes and tank_ids must have same length")
    
    def copy(self) -> 'Chromosome':
        """Create a deep copy of the chromosome"""
        return Chromosome(
            genes=[(cargo_id, qty) for cargo_id, qty in self.genes],
            tank_ids=self.tank_ids.copy()
        )
    
    def get_tank_assignment(self, tank_index: int) -> Tuple[Optional[str], float]:
        """Get assignment for a specific tank"""
        if 0 <= tank_index < len(self.genes):
            return self.genes[tank_index]
        return (None, 0.0)
    
    def set_tank_assignment(self, tank_index: int, cargo_id: Optional[str], quantity: float):
        """Set assignment for a specific tank"""
        if 0 <= tank_index < len(self.genes):
            self.genes[tank_index] = (cargo_id, quantity)


class GeneticOptimizer:
    """Genetic Algorithm optimizer for tanker stowage planning"""
    
    def __init__(self, ship: Ship, cargo_requests: List[Cargo], 
                 excluded_tanks: Optional[Set[str]] = None,
                 fixed_assignments: Optional[Dict[str, TankAssignment]] = None,
                 settings: Optional[Dict] = None):
        """Initialize genetic optimizer
        
        Args:
            ship: Ship with tank configuration
            cargo_requests: List of cargo loading requests
            excluded_tanks: Set of tank IDs to exclude from planning
            fixed_assignments: Dict of fixed tank assignments (manual assignments) to preserve
            settings: Optimization settings dictionary
        """
        self.ship = ship
        self.cargo_requests = cargo_requests
        
        # Add fixed tank IDs to excluded_tanks (fixed assignments should not be used by algorithm)
        fixed_assignments = fixed_assignments or {}
        fixed_tank_ids = set(fixed_assignments.keys())
        self.excluded_tanks = (excluded_tanks or set()) | fixed_tank_ids
        
        # Get default settings if not provided
        if settings is None:
            from storage.storage_manager import StorageManager
            storage = StorageManager()
            settings = storage.get_default_settings()
        self.settings = settings
        
        # Separate mandatory and regular cargos
        self.mandatory_cargos = [c for c in cargo_requests if c.is_mandatory]
        self.regular_cargos = [c for c in cargo_requests if not c.is_mandatory]
        
        # Store mandatory assignments (will be populated during optimization)
        self.mandatory_assignments: Dict[str, TankAssignment] = {}
        
        # Get available tanks (not excluded - fixed tanks are already in excluded_tanks)
        self.available_tanks = [
            tank for tank in ship.tanks 
            if tank.id not in self.excluded_tanks
        ]
        self.tank_ids = [tank.id for tank in self.available_tanks]
        
        # Calculate available tank volumes (only for non-excluded tanks)
        self.tank_volumes = {}
        for tank in ship.tanks:
            if tank.id not in self.excluded_tanks:
                # Full capacity available
                self.tank_volumes[tank.id] = tank.volume
        
        # GA parameters from settings
        self.population_size = settings.get('ga_population_size', 500)
        self.max_generations = settings.get('ga_max_generations', 2000)
        self.crossover_rate = settings.get('ga_crossover_rate', 0.90)
        self.mutation_rate = settings.get('ga_mutation_rate', 0.11)
        self.tournament_size = settings.get('ga_tournament_size', 3)
        self.use_elitism = settings.get('ga_use_elitism', True)
        self.elitism_count = settings.get('ga_elitism_count', 5)
        
        # Penalty coefficients
        self.symmetry_penalty_coef = settings.get('ga_symmetry_penalty_coef', 3000.0)
        self.trim_penalty_coef = settings.get('ga_trim_penalty_coef', 1500.0)
        self.operational_penalty_coef = settings.get('ga_operational_penalty_coef', 100.0)
        
        # Constraint parameters
        self.receiver_tolerance = settings.get('ga_receiver_tolerance', 0.03)  # Default 3%
        
        # LCG calculation
        self.total_rows = (len(self.ship.tanks) + 1) // 2
        self.ideal_lcg_position = settings.get('ga_ideal_lcg_position', self.total_rows / 2.0)  # Geometric center
        
        # Track best fitness for convergence
        self.best_fitness_history = []
        self.convergence_threshold = settings.get('ga_convergence_threshold', 0.0001)
        self.convergence_generations = settings.get('ga_convergence_generations', 60)
    
    def _place_mandatory_cargos(self, available_tanks: Dict[str, float], 
                               settings: Dict) -> Dict[str, float]:
        """Place mandatory cargos using best-fit greedy approach
        
        Args:
            available_tanks: Dictionary of tank_id -> available_volume
            settings: Optimization settings dictionary
            
        Returns:
            Updated available_tanks dictionary with mandatory cargo capacities subtracted
        """
        min_util = settings.get('min_utilization', 0.65)
        
        # Reset mandatory assignments
        self.mandatory_assignments = {}
        
        for cargo in self.mandatory_cargos:
            remaining_qty = cargo.quantity
            
            # Sort tanks by available volume (descending)
            sorted_tanks = sorted(
                [(tid, vol, self.ship.get_tank_by_id(tid)) 
                 for tid, vol in available_tanks.items() if vol > 0.001],
                key=lambda x: x[1],
                reverse=True
            )
            
            # Greedy assignment: place in largest available tanks
            for tank_id, available_vol, tank in sorted_tanks:
                if remaining_qty < 0.001:
                    break
                
                if not tank:
                    continue
                
                qty_to_place = min(remaining_qty, available_vol, tank.volume)
                
                # Check minimum utilization
                if qty_to_place / tank.volume < min_util:
                    continue
                
                # Create assignment
                assignment = TankAssignment(
                    tank_id=tank_id,
                    cargo=cargo,
                    quantity_loaded=qty_to_place
                )
                self.mandatory_assignments[tank_id] = assignment
                available_tanks[tank_id] -= qty_to_place
                remaining_qty -= qty_to_place
                
                # Ensure available_tanks doesn't go negative
                if available_tanks[tank_id] < 0.001:
                    available_tanks[tank_id] = 0.0
        
        return available_tanks
    
    def create_initial_population(self) -> List[Chromosome]:
        """Create initial population of random valid chromosomes
        
        Returns:
            List of chromosomes forming the initial population
        """
        population = []
        
        for _ in range(self.population_size):
            chromosome = self._create_random_chromosome()
            # Repair chromosome to ensure constraints
            chromosome = self._repair_chromosome(chromosome)
            population.append(chromosome)
        
        return population
    
    def _create_random_chromosome(self) -> Chromosome:
        """Create a random chromosome (may violate constraints initially)"""
        genes = [(None, 0.0) for _ in self.tank_ids]
        
        # Randomly assign cargo to tanks (only regular cargos, mandatory already placed)
        for cargo in self.regular_cargos:
            remaining_qty = cargo.quantity
            
            # Try to place cargo in random tanks
            attempts = 0
            max_attempts = len(self.tank_ids) * 2
            
            while remaining_qty > 0.001 and attempts < max_attempts:
                attempts += 1
                
                # Randomly select a tank
                tank_idx = random.randint(0, len(self.tank_ids) - 1)
                tank_id = self.tank_ids[tank_idx]
                tank_volume = self.tank_volumes[tank_id]
                
                # Get current assignment
                current_cargo_id, current_qty = genes[tank_idx]
                
                # If tank is empty or has same cargo, try to add more
                if current_cargo_id is None or current_cargo_id == cargo.unique_id:
                    # Calculate how much we can add
                    if current_cargo_id is None:
                        available_space = tank_volume
                        current_qty = 0.0
                    else:
                        available_space = tank_volume - current_qty
                    
                    # Add random amount (up to remaining or available)
                    qty_to_add = min(remaining_qty, available_space)
                    if qty_to_add > 0.001:
                        genes[tank_idx] = (cargo.unique_id, current_qty + qty_to_add)
                        remaining_qty -= qty_to_add
        
        return Chromosome(genes=genes, tank_ids=self.tank_ids.copy())
    
    def _repair_chromosome(self, chromosome: Chromosome) -> Chromosome:
        """Repair chromosome to satisfy hard constraints
        
        Fixes:
        1. Tank capacity violations (reduce quantities)
        2. Receiver quantity violations (adjust to tolerance)
        """
        repaired = chromosome.copy()
        
        # Fix tank capacity violations
        for i, tank_id in enumerate(repaired.tank_ids):
            cargo_id, quantity = repaired.genes[i]
            if cargo_id is not None and quantity > 0:
                tank_volume = self.tank_volumes[tank_id]
                if quantity > tank_volume:
                    # Reduce to capacity
                    repaired.genes[i] = (cargo_id, tank_volume)
        
        # Fix receiver quantity violations (try to balance)
        # Only check regular cargos (mandatory already placed)
        for cargo in self.regular_cargos:
            total_loaded = sum(
                qty for cargo_id, qty in repaired.genes
                if cargo_id == cargo.unique_id
            )
            
            # Check if within tolerance
            min_allowed = cargo.quantity * (1 - self.receiver_tolerance)
            max_allowed = cargo.quantity * (1 + self.receiver_tolerance)
            
            if total_loaded < min_allowed:
                # Need to add more - try to add to existing tanks or empty tanks
                needed = min_allowed - total_loaded
                self._add_cargo_to_chromosome(repaired, cargo.unique_id, needed)
            elif total_loaded > max_allowed:
                # Need to reduce - reduce from tanks with this cargo
                excess = total_loaded - max_allowed
                self._remove_cargo_from_chromosome(repaired, cargo.unique_id, excess)
        
        return repaired
    
    def _add_cargo_to_chromosome(self, chromosome: Chromosome, cargo_id: str, quantity: float):
        """Try to add cargo quantity to chromosome"""
        remaining = quantity
        
        # First try to add to tanks that already have this cargo
        for i, (existing_cargo_id, existing_qty) in enumerate(chromosome.genes):
            if existing_cargo_id == cargo_id and remaining > 0.001:
                tank_id = chromosome.tank_ids[i]
                tank_volume = self.tank_volumes[tank_id]
                available = tank_volume - existing_qty
                to_add = min(remaining, available)
                if to_add > 0.001:
                    chromosome.genes[i] = (cargo_id, existing_qty + to_add)
                    remaining -= to_add
        
        # Then try empty tanks
        for i, (existing_cargo_id, existing_qty) in enumerate(chromosome.genes):
            if existing_cargo_id is None and remaining > 0.001:
                tank_id = chromosome.tank_ids[i]
                tank_volume = self.tank_volumes[tank_id]
                to_add = min(remaining, tank_volume)
                if to_add > 0.001:
                    chromosome.genes[i] = (cargo_id, to_add)
                    remaining -= to_add
    
    def _remove_cargo_from_chromosome(self, chromosome: Chromosome, cargo_id: str, quantity: float):
        """Remove cargo quantity from chromosome"""
        remaining = quantity
        
        # Remove from tanks with this cargo (prefer partially filled tanks)
        for i, (existing_cargo_id, existing_qty) in enumerate(chromosome.genes):
            if existing_cargo_id == cargo_id and remaining > 0.001:
                to_remove = min(remaining, existing_qty)
                new_qty = existing_qty - to_remove
                if new_qty < 0.001:
                    chromosome.genes[i] = (None, 0.0)
                else:
                    chromosome.genes[i] = (cargo_id, new_qty)
                remaining -= to_remove
    
    def calculate_fitness(self, chromosome: Chromosome) -> float:
        """Calculate fitness score for a chromosome
        
        Fitness = Total_Loaded_Weight - Symmetry_Penalty - Trim_Penalty - Operational_Penalty
        
        Returns:
            Fitness score (higher is better)
        """
        # Calculate total loaded weight/volume (main objective)
        total_loaded = sum(qty for _, qty in chromosome.genes)
        
        # Calculate penalties
        symmetry_penalty = self._calculate_symmetry_penalty(chromosome)
        trim_penalty = self._calculate_trim_penalty(chromosome)
        operational_penalty = self._calculate_operational_penalty(chromosome)
        
        # Fitness = total loaded - penalties
        fitness = total_loaded - symmetry_penalty - trim_penalty - operational_penalty
        
        return fitness
    
    def _calculate_symmetry_penalty(self, chromosome: Chromosome) -> float:
        """Calculate penalty for transverse imbalance (symmetry constraint)
        
        For cargo requiring 2+ tanks, they should not all be on the same side.
        Penalty is applied for each pair of tanks that are unbalanced.
        """
        penalty = 0.0
        
        # Get tank pairs (port/starboard pairs)
        tank_pairs = self.ship.get_tank_pairs()
        
        # For each cargo that uses 2+ tanks, check symmetry
        cargo_tank_map = {}  # cargo_id -> list of tank_ids
        for i, (cargo_id, qty) in enumerate(chromosome.genes):
            if cargo_id is not None and qty > 0.001:
                tank_id = chromosome.tank_ids[i]
                if cargo_id not in cargo_tank_map:
                    cargo_tank_map[cargo_id] = []
                cargo_tank_map[cargo_id].append(tank_id)
        
        # Check each cargo with 2+ tanks
        for cargo_id, tank_ids in cargo_tank_map.items():
            if len(tank_ids) >= 2:
                # Check if all tanks are on same side
                if self._all_tanks_same_side(tank_ids):
                    # Apply penalty based on number of tanks and imbalance
                    penalty += self.symmetry_penalty_coef * len(tank_ids)
        
        # Also check balance for each tank pair
        for port_tank, starboard_tank in tank_pairs:
            port_id = port_tank.id
            starboard_id = starboard_tank.id
            
            if port_id not in self.tank_ids or starboard_id not in self.tank_ids:
                continue
            
            port_idx = self.tank_ids.index(port_id)
            starboard_idx = self.tank_ids.index(starboard_id)
            
            port_cargo, port_qty = chromosome.genes[port_idx]
            starboard_cargo, starboard_qty = chromosome.genes[starboard_idx]
            
            # Calculate weight difference
            weight_diff = abs(port_qty - starboard_qty)
            
            # Apply penalty if difference is significant (more than 10% of average)
            avg_weight = (port_qty + starboard_qty) / 2.0
            if avg_weight > 0.001:
                imbalance_ratio = weight_diff / avg_weight
                if imbalance_ratio > 0.1:  # More than 10% imbalance
                    penalty += self.symmetry_penalty_coef * imbalance_ratio * 0.1
        
        return penalty
    
    def _all_tanks_same_side(self, tank_ids: List[str]) -> bool:
        """Check if all tanks are on the same side (port or starboard)"""
        if not tank_ids:
            return False
        
        first_pos = self.ship.get_tank_position_info(tank_ids[0])
        if not first_pos:
            return False
        
        first_side = first_pos['side']
        for tank_id in tank_ids[1:]:
            pos_info = self.ship.get_tank_position_info(tank_id)
            if not pos_info or pos_info['side'] != first_side:
                return False
        
        return True
    
    def _calculate_trim_penalty(self, chromosome: Chromosome) -> float:
        """Calculate penalty for longitudinal imbalance (trim constraint)
        
        Penalty based on deviation of LCG (Longitudinal Center of Gravity) from ideal position.
        """
        if len(self.tank_ids) == 0:
            return 0.0
        
        # Calculate LCG
        total_weight = 0.0
        weighted_position = 0.0
        
        for i, (cargo_id, qty) in enumerate(chromosome.genes):
            if cargo_id is not None and qty > 0.001:
                tank_id = chromosome.tank_ids[i]
                pos_info = self.ship.get_tank_position_info(tank_id)
                
                if pos_info:
                    row_number = pos_info['row_number']
                    total_weight += qty
                    weighted_position += qty * row_number
        
        if total_weight < 0.001:
            return 0.0
        
        # Calculate actual LCG position
        actual_lcg = weighted_position / total_weight
        
        # Calculate deviation from ideal
        deviation = abs(actual_lcg - self.ideal_lcg_position)
        
        # Normalize deviation (as ratio of total rows)
        normalized_deviation = deviation / self.total_rows if self.total_rows > 0 else 0
        
        # Apply penalty proportional to deviation
        penalty = self.trim_penalty_coef * normalized_deviation
        
        return penalty
    
    def _calculate_operational_penalty(self, chromosome: Chromosome) -> float:
        """Calculate penalty for operational inefficiency
        
        Penalty for each receiver using too many tanks (prefer fewer tanks per receiver).
        """
        penalty = 0.0
        
        # Count tanks used per receiver
        receiver_tank_count = {}  # cargo_id -> set of tank indices
        
        for i, (cargo_id, qty) in enumerate(chromosome.genes):
            if cargo_id is not None and qty > 0.001:
                if cargo_id not in receiver_tank_count:
                    receiver_tank_count[cargo_id] = set()
                receiver_tank_count[cargo_id].add(i)
        
        # Apply penalty for each receiver based on number of tanks used
        for cargo_id, tank_indices in receiver_tank_count.items():
            num_tanks = len(tank_indices)
            if num_tanks > 1:
                # Penalty increases with number of tanks (quadratic)
                penalty += self.operational_penalty_coef * (num_tanks - 1) ** 2
        
        return penalty
    
    def tournament_selection(self, population: List[Chromosome], 
                            fitness_scores: List[float]) -> Chromosome:
        """Select a parent using tournament selection
        
        Args:
            population: Current population
            fitness_scores: Fitness scores for each chromosome
            
        Returns:
            Selected chromosome
        """
        # Randomly select tournament_size individuals
        tournament_indices = random.sample(range(len(population)), 
                                         min(self.tournament_size, len(population)))
        
        # Find the best in tournament
        best_idx = tournament_indices[0]
        best_fitness = fitness_scores[best_idx]
        
        for idx in tournament_indices[1:]:
            if fitness_scores[idx] > best_fitness:
                best_fitness = fitness_scores[idx]
                best_idx = idx
        
        return population[best_idx].copy()
    
    def roulette_wheel_selection(self, population: List[Chromosome],
                                fitness_scores: List[float]) -> Chromosome:
        """Select a parent using roulette wheel selection
        
        Args:
            population: Current population
            fitness_scores: Fitness scores for each chromosome
            
        Returns:
            Selected chromosome
        """
        # Normalize fitness scores (shift to positive values)
        min_fitness = min(fitness_scores)
        if min_fitness < 0:
            shifted_scores = [f - min_fitness + 1.0 for f in fitness_scores]
        else:
            shifted_scores = [f + 1.0 for f in fitness_scores]
        
        # Calculate probabilities
        total_fitness = sum(shifted_scores)
        if total_fitness < 0.001:
            # If all fitness are very low, select randomly
            return random.choice(population).copy()
        
        probabilities = [f / total_fitness for f in shifted_scores]
        
        # Select based on probabilities using random.choices (Python 3.6+)
        # random.choices returns a list, so we take the first element
        selected = random.choices(population, weights=probabilities, k=1)[0]
        return selected.copy()
    
    def two_point_crossover(self, parent1: Chromosome, 
                           parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """Perform two-point crossover between two parents
        
        Args:
            parent1: First parent chromosome
            parent2: Second parent chromosome
            
        Returns:
            Tuple of two offspring chromosomes
        """
        if len(parent1.genes) < 2:
            # Not enough genes for crossover
            return parent1.copy(), parent2.copy()
        
        # Select two random crossover points
        point1 = random.randint(0, len(parent1.genes) - 1)
        point2 = random.randint(0, len(parent1.genes) - 1)
        
        if point1 > point2:
            point1, point2 = point2, point1
        
        # Create offspring
        offspring1 = Chromosome(
            genes=parent1.genes[:point1] + parent2.genes[point1:point2] + parent1.genes[point2:],
            tank_ids=parent1.tank_ids.copy()
        )
        
        offspring2 = Chromosome(
            genes=parent2.genes[:point1] + parent1.genes[point1:point2] + parent2.genes[point2:],
            tank_ids=parent2.tank_ids.copy()
        )
        
        # Repair offspring
        offspring1 = self._repair_chromosome(offspring1)
        offspring2 = self._repair_chromosome(offspring2)
        
        return offspring1, offspring2
    
    def mutate(self, chromosome: Chromosome) -> Chromosome:
        """Apply mutation to chromosome
        
        Randomly selects one of three mutation operators:
        1. Swap: Swap cargo between two tanks
        2. Transfer: Transfer part of cargo from one tank to another
        3. Shift: Shift cargo from one tank to another for same receiver
        
        Args:
            chromosome: Chromosome to mutate
            
        Returns:
            Mutated chromosome
        """
        mutated = chromosome.copy()
        
        # Randomly select mutation operator
        mutation_type = random.choice(['swap', 'transfer', 'shift'])
        
        if mutation_type == 'swap':
            mutated = self._mutate_swap(mutated)
        elif mutation_type == 'transfer':
            mutated = self._mutate_transfer(mutated)
        elif mutation_type == 'shift':
            mutated = self._mutate_shift(mutated)
        
        # Repair after mutation
        mutated = self._repair_chromosome(mutated)
        
        return mutated
    
    def _mutate_swap(self, chromosome: Chromosome) -> Chromosome:
        """Swap mutation: Swap cargo between two random tanks"""
        if len(chromosome.genes) < 2:
            return chromosome
        
        # Select two random tanks
        idx1, idx2 = random.sample(range(len(chromosome.genes)), 2)
        
        # Swap assignments
        chromosome.genes[idx1], chromosome.genes[idx2] = \
            chromosome.genes[idx2], chromosome.genes[idx1]
        
        return chromosome
    
    def _mutate_transfer(self, chromosome: Chromosome) -> Chromosome:
        """Transfer mutation: Transfer part of cargo from one tank to another"""
        # Find tanks with cargo
        filled_tanks = [
            i for i, (cargo_id, qty) in enumerate(chromosome.genes)
            if cargo_id is not None and qty > 0.001
        ]
        
        if len(filled_tanks) == 0:
            return chromosome
        
        # Select source tank
        source_idx = random.choice(filled_tanks)
        source_cargo_id, source_qty = chromosome.genes[source_idx]
        
        if source_qty < 0.001:
            return chromosome
        
        # Select target tank (prefer empty or same cargo)
        target_idx = random.randint(0, len(chromosome.genes) - 1)
        target_cargo_id, target_qty = chromosome.genes[target_idx]
        target_tank_id = chromosome.tank_ids[target_idx]
        target_volume = self.tank_volumes[target_tank_id]
        
        # Calculate transfer amount
        transfer_amount = min(
            source_qty * 0.3,  # Transfer up to 30% of source
            target_volume - target_qty  # Available space in target
        )
        
        if transfer_amount > 0.001:
            # Update source
            new_source_qty = source_qty - transfer_amount
            if new_source_qty < 0.001:
                chromosome.genes[source_idx] = (None, 0.0)
            else:
                chromosome.genes[source_idx] = (source_cargo_id, new_source_qty)
            
            # Update target
            if target_cargo_id == source_cargo_id:
                chromosome.genes[target_idx] = (source_cargo_id, target_qty + transfer_amount)
            elif target_cargo_id is None:
                chromosome.genes[target_idx] = (source_cargo_id, transfer_amount)
        
        return chromosome
    
    def _mutate_shift(self, chromosome: Chromosome) -> Chromosome:
        """Shift mutation: Shift cargo from one tank to another for same receiver"""
        # Group tanks by cargo
        cargo_tanks = {}  # cargo_id -> list of (idx, qty)
        
        for i, (cargo_id, qty) in enumerate(chromosome.genes):
            if cargo_id is not None and qty > 0.001:
                if cargo_id not in cargo_tanks:
                    cargo_tanks[cargo_id] = []
                cargo_tanks[cargo_id].append((i, qty))
        
        # Find cargo with multiple tanks
        suitable_cargos = [
            cargo_id for cargo_id, tanks in cargo_tanks.items()
            if len(tanks) > 1
        ]
        
        if len(suitable_cargos) == 0:
            return chromosome
        
        # Select cargo
        cargo_id = random.choice(suitable_cargos)
        tanks = cargo_tanks[cargo_id]
        
        # Select source and target tanks
        source_idx, source_qty = random.choice(tanks)
        target_idx = random.randint(0, len(chromosome.genes) - 1)
        target_tank_id = chromosome.tank_ids[target_idx]
        target_volume = self.tank_volumes[target_tank_id]
        target_cargo_id, target_qty = chromosome.genes[target_idx]
        
        # Calculate shift amount
        shift_amount = min(
            source_qty * 0.5,  # Shift up to 50% of source
            target_volume - target_qty  # Available space in target
        )
        
        if shift_amount > 0.001 and (target_cargo_id is None or target_cargo_id == cargo_id):
            # Update source
            new_source_qty = source_qty - shift_amount
            if new_source_qty < 0.001:
                chromosome.genes[source_idx] = (None, 0.0)
            else:
                chromosome.genes[source_idx] = (cargo_id, new_source_qty)
            
            # Update target
            if target_cargo_id == cargo_id:
                chromosome.genes[target_idx] = (cargo_id, target_qty + shift_amount)
            else:
                chromosome.genes[target_idx] = (cargo_id, shift_amount)
        
        return chromosome
    
    def optimize(self) -> StowagePlan:
        """Run genetic algorithm optimization
        
        Returns:
            Best StowagePlan found
        """
        # Step 1: Place mandatory cargos first using BEST FIT
        # Initialize available_tanks dictionary with full capacities
        available_tanks = {tank.id: tank.volume for tank in self.available_tanks}
        
        # Place mandatory cargos and update available_tanks
        if self.mandatory_cargos:
            available_tanks = self._place_mandatory_cargos(available_tanks, self.settings)
        
        # Update tank_volumes to reflect remaining capacity after mandatory placement
        # This ensures GA only uses remaining capacity
        for tank_id, remaining_capacity in available_tanks.items():
            if tank_id in self.tank_volumes:
                self.tank_volumes[tank_id] = remaining_capacity
        
        # If no regular cargos, return plan with only mandatory assignments
        if not self.regular_cargos:
            plan = StowagePlan(
                ship_name=self.ship.name,
                ship_profile_id=self.ship.id,
                cargo_requests=self.cargo_requests,
                plan_name="Genetik Algoritma Planı"
            )
            # Add mandatory assignments
            for tank_id, assignment in self.mandatory_assignments.items():
                plan.add_assignment(tank_id, assignment)
            return plan
        
        # Step 2: Run GA optimization for regular cargos only
        # Create initial population
        population = self.create_initial_population()
        
        # Evaluate fitness for initial population
        fitness_scores = [self.calculate_fitness(chrom) for chrom in population]
        
        # Track best solution
        best_idx = max(range(len(population)), key=lambda i: fitness_scores[i])
        best_chromosome = population[best_idx].copy()
        best_fitness = fitness_scores[best_idx]
        self.best_fitness_history = [best_fitness]
        
        # Main GA loop
        for generation in range(self.max_generations):
            # Create new population
            new_population = []
            
            # Elitism: Keep best individuals
            if self.use_elitism:
                sorted_indices = sorted(range(len(population)), 
                                       key=lambda i: fitness_scores[i], 
                                       reverse=True)
                for i in range(min(self.elitism_count, len(population))):
                    new_population.append(population[sorted_indices[i]].copy())
            
            # Generate offspring until population is filled
            while len(new_population) < self.population_size:
                # Selection
                parent1 = self.tournament_selection(population, fitness_scores)
                parent2 = self.tournament_selection(population, fitness_scores)
                
                # Crossover
                if random.random() < self.crossover_rate:
                    offspring1, offspring2 = self.two_point_crossover(parent1, parent2)
                else:
                    offspring1, offspring2 = parent1.copy(), parent2.copy()
                
                # Mutation
                if random.random() < self.mutation_rate:
                    offspring1 = self.mutate(offspring1)
                if random.random() < self.mutation_rate:
                    offspring2 = self.mutate(offspring2)
                
                new_population.append(offspring1)
                if len(new_population) < self.population_size:
                    new_population.append(offspring2)
            
            # Trim to population size
            new_population = new_population[:self.population_size]
            
            # Evaluate fitness for new population
            fitness_scores = [self.calculate_fitness(chrom) for chrom in new_population]
            
            # Update best solution
            current_best_idx = max(range(len(new_population)), 
                                 key=lambda i: fitness_scores[i])
            current_best_fitness = fitness_scores[current_best_idx]
            
            if current_best_fitness > best_fitness:
                best_chromosome = new_population[current_best_idx].copy()
                best_fitness = current_best_fitness
            
            self.best_fitness_history.append(best_fitness)
            
            # Check convergence
            if len(self.best_fitness_history) >= self.convergence_generations:
                recent_improvement = (
                    self.best_fitness_history[-1] - 
                    self.best_fitness_history[-self.convergence_generations]
                )
                if recent_improvement < self.convergence_threshold:
                    # Converged - no significant improvement
                    break
            
            # Update population
            population = new_population
        
        # Convert best chromosome to StowagePlan
        plan = self._chromosome_to_plan(best_chromosome)
        
        # Note: Fixed assignments are NOT added here - they are handled by MainWindow
        # Fixed tanks are already excluded from available_tanks, so algorithm won't use them
        
        # Post-processing: Fill empty tanks with remaining cargo
        plan = self._fill_empty_tanks_with_remaining_cargo(plan, self.settings)
        
        return plan
    
    def _chromosome_to_plan(self, chromosome: Chromosome) -> StowagePlan:
        """Convert chromosome to StowagePlan
        
        Args:
            chromosome: Best chromosome found
            
        Returns:
            StowagePlan with assignments (including mandatory assignments)
        """
        plan = StowagePlan(
            ship_name=self.ship.name,
            ship_profile_id=self.ship.id,
            cargo_requests=self.cargo_requests,
            plan_name="Genetik Algoritma Planı"
        )
        
        # First, add mandatory assignments (placed before GA optimization)
        for tank_id, assignment in self.mandatory_assignments.items():
            plan.add_assignment(tank_id, assignment)
        
        # Note: Fixed assignments are NOT added here - they are handled by MainWindow
        # Fixed tanks are already excluded from available_tanks, so they won't be in chromosome
        
        # Create cargo map for quick lookup
        cargo_map = {cargo.unique_id: cargo for cargo in self.cargo_requests}
        
        # Add assignments from chromosome (regular cargos only)
        # Fixed tanks are already excluded from available_tanks, so they won't appear here
        for i, (cargo_id, quantity) in enumerate(chromosome.genes):
            if cargo_id is not None and quantity > 0.001:
                tank_id = chromosome.tank_ids[i]
                
                # Skip if this tank already has a mandatory assignment
                if tank_id in self.mandatory_assignments:
                    continue
                # Note: Fixed tanks are already excluded from available_tanks, so they won't be in chromosome
                
                cargo = cargo_map.get(cargo_id)
                
                if cargo:
                    assignment = TankAssignment(
                        tank_id=tank_id,
                        cargo=cargo,
                        quantity_loaded=quantity
                    )
                    plan.add_assignment(tank_id, assignment)
        
        return plan
    
    def _fill_empty_tanks_with_remaining_cargo(self, plan: StowagePlan, 
                                               settings: Dict) -> StowagePlan:
        """Fill empty tanks with remaining cargo after GA optimization
        
        This is a post-processing step that runs after GA completes.
        It finds empty tanks and tries to fill them with the most needed remaining cargo.
        
        Args:
            plan: StowagePlan after GA optimization
            settings: Optimization settings dictionary
            
        Returns:
            Updated StowagePlan with additional assignments in empty tanks
        """
        min_util = settings.get('min_utilization', 0.65)
        
        # Step 1: Find empty tanks
        empty_tanks = []
        for tank in self.available_tanks:
            if tank.id not in self.excluded_tanks:
                assignment = plan.get_assignment(tank.id)
                if assignment is None:
                    empty_tanks.append(tank)
        
        # If no empty tanks, nothing to do
        if not empty_tanks:
            return plan
        
        # Step 2: Find remaining regular cargos (not mandatory)
        remaining_cargos = []
        for cargo in self.regular_cargos:
            total_loaded = plan.get_cargo_total_loaded(cargo.unique_id)
            remaining = cargo.quantity - total_loaded
            if remaining > 0.001:
                remaining_cargos.append((cargo, remaining))
        
        # If no remaining cargo, nothing to do
        if not remaining_cargos:
            return plan
        
        # Step 3: Sort remaining cargos by remaining quantity (descending)
        # Most needed cargo first
        remaining_cargos.sort(key=lambda x: x[1], reverse=True)
        
        # Step 4: Fill empty tanks with remaining cargo
        # Process each remaining cargo starting with the most needed
        for cargo, remaining_qty in remaining_cargos:
            if remaining_qty < 0.001:
                continue
            
            # Sort empty tanks by volume (ascending for best fit)
            # Try to find tanks that fit well
            available_empty_tanks = [
                tank for tank in empty_tanks
                if plan.get_assignment(tank.id) is None
            ]
            
            if not available_empty_tanks:
                break
            
            # Sort by volume (ascending - try smaller tanks first for better fit)
            available_empty_tanks.sort(key=lambda t: t.volume)
            
            for tank in available_empty_tanks:
                if remaining_qty < 0.001:
                    break
                
                # Calculate how much we can place
                qty_to_place = min(remaining_qty, tank.volume)
                
                # Check minimum utilization
                if qty_to_place / tank.volume < min_util:
                    continue  # Skip this tank, too small
                
                # Create assignment
                assignment = TankAssignment(
                    tank_id=tank.id,
                    cargo=cargo,
                    quantity_loaded=qty_to_place
                )
                plan.add_assignment(tank.id, assignment)
                remaining_qty -= qty_to_place
        
        return plan
    
    @staticmethod
    def validate_plan(ship: Ship, cargo_requests: List[Cargo]) -> Tuple[bool, str]:
        """Validate if cargo requests can be fulfilled
        
        Returns:
            (is_valid, error_message)
        """
        total_cargo_quantity = sum(cargo.quantity for cargo in cargo_requests)
        total_capacity = ship.get_total_capacity()
        
        if total_cargo_quantity > total_capacity * 1.1:  # 10% tolerance for GA
            return False, f"Toplam yük miktarı ({total_cargo_quantity:.2f}) geminin toplam kapasitesini ({total_capacity:.2f}) çok fazla aşıyor"
        
        return True, ""

