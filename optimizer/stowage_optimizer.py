"""Stowage plan optimization algorithm"""

from typing import List, Dict, Optional, Tuple, Callable
from models.ship import Ship, Tank
from models.cargo import Cargo
from models.plan import StowagePlan, TankAssignment
import random


class StowageOptimizer:
    """Optimizes cargo loading into ship tanks"""
    
    @staticmethod
    def optimize(ship: Ship, cargo_requests: List[Cargo], excluded_tanks: Optional[set[str]] = None) -> StowagePlan:
        """Create an optimized stowage plan
        
        Improved Algorithm:
        1. Sort cargo by priority (largest quantity first, then by receiver count)
        2. For each cargo, use smart tank selection:
           - First try: Find exact-fit tank (minimal waste)
           - Second try: Find best-fit tank (smallest that fits)
           - Third try: Use largest available tank for partial fill
        3. Maximize tank utilization by minimizing leftover space
        4. Handle multiple receivers by distributing across tanks
        
        Args:
            ship: Ship with tank configuration
            cargo_requests: List of cargo loading requests
            
        Returns:
            StowagePlan with optimized assignments
        """
        plan = StowagePlan(
            ship_name=ship.name,
            ship_profile_id=ship.id,
            cargo_requests=cargo_requests,
            plan_name="Yeni Plan"
        )
        
        # Create a copy of tanks for tracking available capacity
        # Exclude tanks that are marked as excluded from planning
        excluded = excluded_tanks or set()
        available_tanks = {tank.id: tank.volume for tank in ship.tanks if tank.id not in excluded}
        
        # Smart sorting: by quantity (largest first), then by receiver count
        # This prioritizes large cargoes and single-receiver cargoes
        sorted_cargo = sorted(
            cargo_requests, 
            key=lambda c: (c.quantity, -len(c.receivers) if c.receivers else 0),
            reverse=True
        )
        
        # Process each cargo request
        for cargo in sorted_cargo:
            remaining_quantity = cargo.quantity
            
            # Distribute this cargo across multiple tanks if needed
            while remaining_quantity > 0.001:  # Small tolerance for floating point
                # Strategy 1: Try to find exact-fit or near-exact-fit tank (waste < 1%)
                best_tank_id, waste_ratio = StowageOptimizer._find_optimal_tank(
                    remaining_quantity, available_tanks, ship, prefer_exact_fit=True
                )
                
                if best_tank_id is None:
                    # Strategy 2: Find best-fit tank (minimal waste)
                    best_tank_id, _ = StowageOptimizer._find_optimal_tank(
                        remaining_quantity, available_tanks, ship, prefer_exact_fit=False
                    )
                
                if best_tank_id is None:
                    # Strategy 3: Use largest available tank (may result in partial fill)
                    best_tank_id = StowageOptimizer._find_largest_available_tank(available_tanks, ship)
                    if best_tank_id is None:
                        # Cannot fulfill this cargo - break and report partial fulfillment
                        break
                
                tank = ship.get_tank_by_id(best_tank_id)
                quantity_to_load = min(remaining_quantity, available_tanks[best_tank_id])
                
                # Check minimum utilization constraint: tank must be at least 65% filled
                tank_utilization = quantity_to_load / tank.volume if tank.volume > 0 else 0
                
                if tank_utilization < 0.65:
                    # This tank would be less than 65% full - skip it and try to find another
                    # Remove this tank from consideration temporarily
                    original_volume = available_tanks[best_tank_id]
                    available_tanks[best_tank_id] = 0  # Mark as unavailable
                    
                    # Try to find another tank
                    alt_tank_id = StowageOptimizer._find_optimal_tank(
                        remaining_quantity, available_tanks, ship, prefer_exact_fit=False
                    )[0]
                    
                    if alt_tank_id:
                        # Found another tank, restore original and use alternative
                        available_tanks[best_tank_id] = original_volume
                        best_tank_id = alt_tank_id
                        tank = ship.get_tank_by_id(best_tank_id)
                        quantity_to_load = min(remaining_quantity, available_tanks[best_tank_id])
                        tank_utilization = quantity_to_load / tank.volume if tank.volume > 0 else 0
                    else:
                        # No suitable tank found that meets 65% constraint
                        available_tanks[best_tank_id] = original_volume  # Restore
                        break  # Skip this cargo, leave tank empty
                
                # If we still have a valid tank and it meets the constraint
                if tank_utilization >= 0.65:
                    # Create assignment
                    assignment = TankAssignment(
                        tank_id=best_tank_id,
                        cargo=cargo,
                        quantity_loaded=quantity_to_load
                    )
                    plan.add_assignment(best_tank_id, assignment)
                    
                    # Update available capacity
                    available_tanks[best_tank_id] -= quantity_to_load
                    remaining_quantity -= quantity_to_load
                else:
                    # Cannot place in any tank meeting 65% constraint
                    break
        
        return plan
    
    @staticmethod
    def _find_optimal_tank(quantity: float, available_tanks: Dict[str, float], 
                           ship: Ship, prefer_exact_fit: bool = False) -> Tuple[Optional[str], float]:
        """Find the optimal tank for the quantity
        
        Args:
            quantity: Quantity to place
            available_tanks: Dictionary of tank_id -> available_volume
            ship: Ship object
            prefer_exact_fit: If True, prefer tanks with minimal waste (<1%)
        
        Returns:
            Tuple of (tank_id, waste_ratio) or (None, 1.0) if no tank found
            waste_ratio = leftover_volume / tank_volume
            
        Note:
            Only considers tanks where quantity will fill at least 65% of the tank capacity
        """
        MIN_UTILIZATION = 0.65  # Minimum 65% tank utilization requirement
        best_tank_id = None
        best_score = float('inf')
        best_waste_ratio = 1.0
        
        for tank_id, available_volume in available_tanks.items():
            if available_volume < quantity:
                continue  # Tank too small for quantity
            
            # Get full tank capacity
            tank = ship.get_tank_by_id(tank_id)
            if not tank:
                continue
            
            # Calculate utilization (quantity / full tank capacity)
            utilization = quantity / tank.volume if tank.volume > 0 else 0
            
            # Skip tanks that would be less than 65% full
            if utilization < MIN_UTILIZATION:
                continue
            
            waste = available_volume - quantity
            waste_ratio = waste / available_volume if available_volume > 0 else 1.0
            
            # Score calculation: prefer higher utilization and lower waste
            if prefer_exact_fit:
                # For exact fit preference: heavily penalize waste > 1%
                if waste_ratio <= 0.01:
                    # Exact or near-exact fit - prefer this
                    score = waste_ratio * 0.1  # Very low score for exact fits
                else:
                    score = waste_ratio * 100  # High penalty for non-exact fits
            else:
                # For best-fit: balance between utilization and waste
                # Lower score = better choice
                score = waste_ratio + (1 - utilization) * 0.5
            
            if score < best_score:
                best_score = score
                best_tank_id = tank_id
                best_waste_ratio = waste_ratio
        
        return best_tank_id, best_waste_ratio
    
    @staticmethod
    def _find_largest_available_tank(available_tanks: Dict[str, float], 
                                    ship: Ship) -> Optional[str]:
        """Find the largest available tank
        
        Returns:
            Tank ID or None if no tanks available
        """
        best_tank_id = None
        max_volume = 0
        
        for tank_id, available_volume in available_tanks.items():
            if available_volume > max_volume and available_volume > 0.001:
                max_volume = available_volume
                best_tank_id = tank_id
        
        return best_tank_id
    
    @staticmethod
    def validate_plan(ship: Ship, cargo_requests: List[Cargo]) -> tuple[bool, str]:
        """Validate if cargo requests can be fulfilled
        
        Returns:
            (is_valid, error_message)
        """
        total_cargo_quantity = sum(cargo.quantity for cargo in cargo_requests)
        total_capacity = ship.get_total_capacity()
        
        if total_cargo_quantity > total_capacity:
            return False, f"Toplam yük miktarı ({total_cargo_quantity:.2f}) geminin toplam kapasitesini ({total_capacity:.2f}) aşıyor"
        
        if len(cargo_requests) > len(ship.tanks):
            # This is a warning, not necessarily an error
            # But if we have more cargo types than tanks, we need to check compatibility
            return True, ""  # Optimizer will handle distribution
        
        return True, ""
    
    @staticmethod
    def get_unfulfilled_cargo(plan: StowagePlan) -> List[Cargo]:
        """Get list of cargo that couldn't be fully loaded
        
        Returns:
            List of cargo with remaining quantities
        """
        unfulfilled = []
        
        for cargo in plan.cargo_requests:
            total_loaded = plan.get_cargo_total_loaded(cargo.unique_id)
            remaining = cargo.quantity - total_loaded
            
            if remaining > 0.001:  # Small tolerance
                # Create a copy with remaining quantity
                unfulfilled_cargo = Cargo(
                    cargo_type=cargo.cargo_type,
                    quantity=remaining,
                    receivers=cargo.receivers.copy()
                )
                unfulfilled.append(unfulfilled_cargo)
        
        return unfulfilled
    
    @staticmethod
    def score_plan(plan: StowagePlan, ship: Ship) -> float:
        """Score a stowage plan based on multiple criteria
        
        Scoring factors:
        - Completion rate (40%): How much of requested cargo was loaded
        - Tank utilization (30%): Overall capacity usage
        - Average fill rate (20%): Average tank fill percentage
        - Empty space penalty (10%): Penalty for unused tanks
        
        Returns:
            Score between 0-100 (higher is better)
        """
        if not plan or not ship or len(ship.tanks) == 0:
            return 0.0
        
        # 1. Completion rate (0-40 points)
        total_requested = sum(cargo.quantity for cargo in plan.cargo_requests)
        total_loaded = plan.get_total_loaded()
        completion_rate = (total_loaded / total_requested * 100) if total_requested > 0 else 0
        completion_score = completion_rate * 0.4
        
        # 2. Tank utilization (0-30 points)
        total_capacity = ship.get_total_capacity()
        tank_utilization = (total_loaded / total_capacity * 100) if total_capacity > 0 else 0
        utilization_score = tank_utilization * 0.3
        
        # 3. Average fill rate (0-20 points)
        fill_rates = []
        for tank in ship.tanks:
            assignment = plan.get_assignment(tank.id)
            if assignment:
                fill_rate = (assignment.quantity_loaded / tank.volume * 100) if tank.volume > 0 else 0
                fill_rates.append(fill_rate)
        
        avg_fill_rate = sum(fill_rates) / len(fill_rates) if fill_rates else 0
        fill_score = avg_fill_rate * 0.2
        
        # 4. Empty space penalty (0-10 points deducted)
        empty_tanks = sum(1 for tank in ship.tanks if plan.get_assignment(tank.id) is None)
        empty_penalty = (empty_tanks / len(ship.tanks) * 100) * 0.1
        empty_score = 10.0 - empty_penalty  # Max 10 points, reduced by penalty
        
        total_score = completion_score + utilization_score + fill_score + empty_score
        return min(total_score, 100.0)  # Cap at 100
    
    @staticmethod
    def optimize_multiple(ship: Ship, cargo_requests: List[Cargo], 
                         num_solutions: int = 5, excluded_tanks: Optional[set[str]] = None) -> List[Tuple[StowagePlan, float, str]]:
        """Generate multiple optimization solutions using different strategies
        
        Args:
            ship: Ship with tank configuration
            cargo_requests: List of cargo loading requests
            num_solutions: Number of different solutions to generate
            excluded_tanks: Set of tank IDs to exclude from planning
            
        Returns:
            List of tuples (plan, score, strategy_name) sorted by score (best first)
        """
        strategies = StowageOptimizer._get_cargo_sort_strategies(num_solutions)
        solutions = []
        
        for strategy_name, sort_key_func in strategies:
            try:
                plan = StowageOptimizer.optimize_with_sort(ship, cargo_requests, sort_key_func, excluded_tanks)
                score = StowageOptimizer.score_plan(plan, ship)
                solutions.append((plan, score, strategy_name))
            except Exception as e:
                # Skip failed strategies
                continue
        
        # Remove duplicates (same assignments)
        unique_solutions = StowageOptimizer._remove_duplicate_plans(solutions)
        
        # Sort by score (best first)
        unique_solutions.sort(key=lambda x: x[1], reverse=True)
        
        return unique_solutions
    
    @staticmethod
    def optimize_with_sort(ship: Ship, cargo_requests: List[Cargo],
                           sort_key_func: Callable[[Cargo], tuple], 
                           excluded_tanks: Optional[set[str]] = None) -> StowagePlan:
        """Optimize with custom sorting strategy
        
        Args:
            ship: Ship with tank configuration
            cargo_requests: List of cargo loading requests
            sort_key_func: Function to use for sorting cargo
            
        Returns:
            StowagePlan with optimized assignments
        """
        plan = StowagePlan(
            ship_name=ship.name,
            ship_profile_id=ship.id,
            cargo_requests=cargo_requests,
            plan_name="Yeni Plan"
        )
        
        # Create a copy of tanks for tracking available capacity
        # Exclude tanks that are marked as excluded from planning
        excluded = excluded_tanks or set()
        available_tanks = {tank.id: tank.volume for tank in ship.tanks if tank.id not in excluded}
        
        # Sort cargo using provided strategy
        sorted_cargo = sorted(cargo_requests, key=sort_key_func, reverse=True)
        
        # Process each cargo request (same logic as optimize())
        for cargo in sorted_cargo:
            remaining_quantity = cargo.quantity
            
            while remaining_quantity > 0.001:
                best_tank_id, waste_ratio = StowageOptimizer._find_optimal_tank(
                    remaining_quantity, available_tanks, ship, prefer_exact_fit=True
                )
                
                if best_tank_id is None:
                    best_tank_id, _ = StowageOptimizer._find_optimal_tank(
                        remaining_quantity, available_tanks, ship, prefer_exact_fit=False
                    )
                
                if best_tank_id is None:
                    best_tank_id = StowageOptimizer._find_largest_available_tank(available_tanks, ship)
                    if best_tank_id is None:
                        break
                
                tank = ship.get_tank_by_id(best_tank_id)
                quantity_to_load = min(remaining_quantity, available_tanks[best_tank_id])
                
                # Check minimum utilization constraint
                tank_utilization = quantity_to_load / tank.volume if tank.volume > 0 else 0
                
                if tank_utilization < 0.65:
                    original_volume = available_tanks[best_tank_id]
                    available_tanks[best_tank_id] = 0
                    
                    alt_tank_id = StowageOptimizer._find_optimal_tank(
                        remaining_quantity, available_tanks, ship, prefer_exact_fit=False
                    )[0]
                    
                    if alt_tank_id:
                        available_tanks[best_tank_id] = original_volume
                        best_tank_id = alt_tank_id
                        tank = ship.get_tank_by_id(best_tank_id)
                        quantity_to_load = min(remaining_quantity, available_tanks[best_tank_id])
                        tank_utilization = quantity_to_load / tank.volume if tank.volume > 0 else 0
                    else:
                        available_tanks[best_tank_id] = original_volume
                        break
                
                if tank_utilization >= 0.65:
                    assignment = TankAssignment(
                        tank_id=best_tank_id,
                        cargo=cargo,
                        quantity_loaded=quantity_to_load
                    )
                    plan.add_assignment(best_tank_id, assignment)
                    available_tanks[best_tank_id] -= quantity_to_load
                    remaining_quantity -= quantity_to_load
                else:
                    break
        
        return plan
    
    @staticmethod
    def _get_cargo_sort_strategies(num: int) -> List[Tuple[str, Callable]]:
        """Get different cargo sorting strategies
        
        Returns:
            List of (strategy_name, sort_key_function) tuples
        """
        strategies = []
        
        # Strategy 1: Quantity large first, then receiver count (default)
        strategies.append((
            "Miktar (Büyük→Küçük) + Alıcı",
            lambda c: (c.quantity, -len(c.receivers) if c.receivers else 0)
        ))
        
        # Strategy 2: Quantity small first, then receiver count
        strategies.append((
            "Miktar (Küçük→Büyük) + Alıcı",
            lambda c: (-c.quantity, -len(c.receivers) if c.receivers else 0)
        ))
        
        # Strategy 3: Receiver count (few first), then quantity
        strategies.append((
            "Alıcı Sayısı (Az→Çok) + Miktar",
            lambda c: (len(c.receivers) if c.receivers else 0, c.quantity)
        ))
        
        # Strategy 4: Receiver count (many first), then quantity
        strategies.append((
            "Alıcı Sayısı (Çok→Az) + Miktar",
            lambda c: (-len(c.receivers) if c.receivers else 0, c.quantity)
        ))
        
        # Strategy 5: Pure quantity (large first)
        strategies.append((
            "Sadece Miktar (Büyük→Küçük)",
            lambda c: c.quantity
        ))
        
        # Strategy 6: Pure quantity (small first)
        if num > 5:
            strategies.append((
                "Sadece Miktar (Küçük→Büyük)",
                lambda c: -c.quantity
            ))
        
        # Strategy 7-10: Random variations with different priorities
        for i in range(max(0, num - 6)):
            random_seed = i + 1000
            strategies.append((
                f"Rastgele Strateji {i+1}",
                lambda c, seed=random_seed: (
                    random.Random(seed + hash(c.cargo_type)).random(),
                    c.quantity,
                    len(c.receivers) if c.receivers else 0
                )
            ))
        
        return strategies[:num]
    
    @staticmethod
    def _remove_duplicate_plans(solutions: List[Tuple[StowagePlan, float, str]]) -> List[Tuple[StowagePlan, float, str]]:
        """Remove duplicate plans based on assignments
        
        Args:
            solutions: List of (plan, score, strategy_name) tuples
            
        Returns:
            List with duplicates removed, keeping best score for each unique plan
        """
        seen = {}
        unique = []
        
        for plan, score, strategy in solutions:
            # Create signature from assignments
            assignments_sig = tuple(sorted(
                (tank_id, assignment.cargo.cargo_type, round(assignment.quantity_loaded, 2))
                for tank_id, assignment in plan.assignments.items()
            ))
            
            if assignments_sig not in seen:
                seen[assignments_sig] = (plan, score, strategy)
                unique.append((plan, score, strategy))
            else:
                # If this solution has better score, replace
                existing_score = seen[assignments_sig][1]
                if score > existing_score:
                    # Remove old and add new
                    unique = [s for s in unique if s[0] != seen[assignments_sig][0]]
                    seen[assignments_sig] = (plan, score, strategy)
                    unique.append((plan, score, strategy))
        
        return unique

