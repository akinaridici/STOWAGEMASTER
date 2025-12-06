"""Advanced multi-phase stowage optimization algorithm with progress reporting"""

from typing import List, Dict, Optional, Tuple
from models.ship import Ship, Tank
from models.cargo import Cargo
from models.plan import StowagePlan, TankAssignment
from core.progress_reporter import ProgressReporter, ProgressStage
import copy


class AdvancedStowageOptimizerWithProgress:
    """Advanced optimizer with 8-phase approach (FAZ 0-7) and progress reporting"""
    
    def __init__(self, progress_reporter: Optional[ProgressReporter] = None):
        """Initialize optimizer with progress reporter
        
        Args:
            progress_reporter: Progress reporter for status updates
        """
        self.progress_reporter = progress_reporter
    
    def _report_progress(self, stage: ProgressStage, progress: float, message: str = ""):
        """Report progress if progress reporter is available
        
        Args:
            stage: Current optimization stage
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        if self.progress_reporter:
            self.progress_reporter.report_progress(stage, progress, message)
    
    def _check_cancellation(self) -> bool:
        """Check if optimization should be cancelled
        
        Returns:
            True if cancelled, False otherwise
        """
        if self.progress_reporter:
            return self.progress_reporter.is_cancelled()
        return False
    
    def optimize_advanced(self, ship: Ship, cargo_requests: List[Cargo], 
                        excluded_tanks: Optional[set[str]] = None,
                        fixed_assignments: Optional[Dict[str, TankAssignment]] = None,
                        settings: Optional[Dict] = None) -> StowagePlan:
        """Create optimized plan using 8-phase algorithm (FAZ 0-7) with progress reporting
        
        Args:
            ship: Ship with tank configuration
            cargo_requests: List of cargo loading requests
            excluded_tanks: Set of tank IDs excluded from planning
            fixed_assignments: Dict of fixed tank assignments (manual assignments) to preserve
            settings: Optimization settings dictionary
            
        Returns:
            StowagePlan with optimized assignments
        """
        # Get default settings if not provided
        if settings is None:
            from storage.storage_manager import StorageManager
            storage = StorageManager()
            settings = storage.get_default_settings()
        
        # Initialize plan
        plan = StowagePlan(
            ship_name=ship.name,
            ship_profile_id=ship.id,
            cargo_requests=cargo_requests,
            plan_name="Yeni Plan"
        )
        
        # Note: Fixed assignments are NOT added here - they are handled by MainWindow
        # Fixed tanks are added to excluded_tanks, so algorithm won't use them
        
        # Calculate available tanks (exclude excluded tanks and fixed assignment tanks)
        fixed_assignments = fixed_assignments or {}
        fixed_tank_ids = set(fixed_assignments.keys())
        excluded = (excluded_tanks or set()) | fixed_tank_ids  # Add fixed tanks to excluded
        available_tanks = {}
        for tank in ship.tanks:
            if tank.id not in excluded:
                # Full capacity available
                available_tanks[tank.id] = tank.volume
            # Fixed assignment tanks are excluded from available_tanks
            # They are already in the plan and should not be used for optimization
        
        # Separate mandatory and regular cargos
        mandatory_cargos = [c for c in cargo_requests if c.is_mandatory]
        regular_cargos = [c for c in cargo_requests if not c.is_mandatory]
        
        # Report initial setup
        self._report_progress(
            ProgressStage.INITIALIZING_POPULATION,
            0.0,
            f"Starting advanced optimization with {len(cargo_requests)} cargos ({len(mandatory_cargos)} mandatory, {len(regular_cargos)} regular)"
        )
        
        # FAZ 0: Mandatory cargo phase
        if mandatory_cargos:
            self._report_progress(
                ProgressStage.PLACING_MANDATORY,
                0.0,
                f"FAZ 0: Processing {len(mandatory_cargos)} mandatory cargos"
            )
            
            for i, cargo in enumerate(mandatory_cargos):
                if self._check_cancellation():
                    return self._create_cancelled_plan(ship, cargo_requests)
                
                progress = (i + 1) / len(mandatory_cargos) * 100
                self._report_progress(
                    ProgressStage.PLACING_MANDATORY,
                    progress,
                    f"FAZ 0: Processing mandatory cargo {i+1}/{len(mandatory_cargos)}: {cargo.name}"
                )
                
                # Process one mandatory cargo at a time
                temp_available = available_tanks.copy()
                temp_available = self._faz0_mandatory_cargo(
                    plan, [cargo], temp_available, ship, settings
                )
                available_tanks = temp_available
        
        # FAZ 1: Single tank fitting
        self._report_progress(
            ProgressStage.RUNNING_OPTIMIZATION,
            12.5,
            "FAZ 1: Single tank fitting"
        )
        
        remaining_regular = regular_cargos.copy()
        available_tanks = self._faz1_single_tank(
            plan, remaining_regular, available_tanks, ship, settings
        )
        remaining_regular = [c for c in remaining_regular 
                           if plan.get_cargo_total_loaded(c.unique_id) < c.quantity - 0.001]
        
        if self._check_cancellation():
            return self._create_cancelled_plan(ship, cargo_requests)
        
        # FAZ 2: Two tank fitting
        self._report_progress(
            ProgressStage.RUNNING_OPTIMIZATION,
            25.0,
            "FAZ 2: Two tank fitting"
        )
        
        available_tanks = self._faz2_two_tank(
            plan, remaining_regular, available_tanks, ship, settings
        )
        remaining_regular = [c for c in remaining_regular 
                           if plan.get_cargo_total_loaded(c.unique_id) < c.quantity - 0.001]
        
        if self._check_cancellation():
            return self._create_cancelled_plan(ship, cargo_requests)
        
        # FAZ 3: Three tank fitting
        self._report_progress(
            ProgressStage.RUNNING_OPTIMIZATION,
            37.5,
            "FAZ 3: Three tank fitting"
        )
        
        available_tanks = self._faz3_three_tank(
            plan, remaining_regular, available_tanks, ship, settings
        )
        remaining_regular = [c for c in remaining_regular 
                           if plan.get_cargo_total_loaded(c.unique_id) < c.quantity - 0.001]
        
        if self._check_cancellation():
            return self._create_cancelled_plan(ship, cargo_requests)
        
        # FAZ 4: Four tank fitting
        self._report_progress(
            ProgressStage.RUNNING_OPTIMIZATION,
            50.0,
            "FAZ 4: Four tank fitting"
        )
        
        available_tanks = self._faz4_four_tank(
            plan, remaining_regular, available_tanks, ship, settings
        )
        remaining_regular = [c for c in remaining_regular 
                           if plan.get_cargo_total_loaded(c.unique_id) < c.quantity - 0.001]
        
        if self._check_cancellation():
            return self._create_cancelled_plan(ship, cargo_requests)
        
        # FAZ 5: Five tank fitting
        self._report_progress(
            ProgressStage.RUNNING_OPTIMIZATION,
            62.5,
            "FAZ 5: Five tank fitting"
        )
        
        available_tanks = self._faz5_five_tank(
            plan, remaining_regular, available_tanks, ship, settings
        )
        remaining_regular = [c for c in remaining_regular 
                           if plan.get_cargo_total_loaded(c.unique_id) < c.quantity - 0.001]
        
        if self._check_cancellation():
            return self._create_cancelled_plan(ship, cargo_requests)
        
        # FAZ 6: Six tank fitting
        self._report_progress(
            ProgressStage.RUNNING_OPTIMIZATION,
            75.0,
            "FAZ 6: Six tank fitting"
        )
        
        available_tanks = self._faz6_six_tank(
            plan, remaining_regular, available_tanks, ship, settings
        )
        remaining_regular = [c for c in remaining_regular 
                           if plan.get_cargo_total_loaded(c.unique_id) < c.quantity - 0.001]
        
        if self._check_cancellation():
            return self._create_cancelled_plan(ship, cargo_requests)
        
        # FAZ 7: 7+ tank fitting (best-fit)
        self._report_progress(
            ProgressStage.RUNNING_OPTIMIZATION,
            87.5,
            "FAZ 7: Multi-tank best-fit"
        )
        
        available_tanks = self._faz7_multi_tank(
            plan, remaining_regular, available_tanks, ship, settings
        )
        
        # Finalization
        self._report_progress(
            ProgressStage.FINALIZING_RESULTS,
            95.0,
            "Finalizing optimization results"
        )
        
        self._report_progress(
            ProgressStage.POST_PROCESSING,
            100.0,
            "Advanced optimization completed successfully"
        )
        
        return plan
    
    def _create_cancelled_plan(self, ship: Ship, cargo_requests: List[Cargo]) -> StowagePlan:
        """Create a plan when optimization is cancelled
        
        Args:
            ship: Ship object
            cargo_requests: List of cargo requests
            
        Returns:
            Empty stowage plan indicating cancellation
        """
        plan = StowagePlan(
            ship_name=ship.name,
            ship_profile_id=ship.id,
            cargo_requests=cargo_requests,
            plan_name="Optimization Cancelled"
        )
        return plan
    
    # ==================== Helper Functions ====================
    
    @staticmethod
    def _calculate_tolerance_deviation(quantity: float, total_capacity: float) -> float:
        """Calculate deviation from ideal fit (0.0 = perfect fit)
        
        Returns:
            Absolute deviation ratio: abs(quantity - capacity) / capacity
        """
        if total_capacity <= 0:
            return float('inf')
        return abs(quantity - total_capacity) / total_capacity
    
    @staticmethod
    def _check_min_utilization(quantity: float, tank_volume: float, min_util: float) -> bool:
        """Check if quantity meets minimum utilization requirement"""
        if tank_volume <= 0:
            return False
        utilization = quantity / tank_volume
        return utilization >= min_util
    
    @staticmethod
    def _get_mid_section_rows(ship: Ship) -> Tuple[int, int]:
        """Get middle section row numbers (for FAZ 4 rule)
        
        Returns:
            (start_row, end_row) for mid-section
        """
        total_rows = (len(ship.tanks) + 1) // 2
        if total_rows <= 2:
            return (1, total_rows)
        
        # Middle rows (approximately center third)
        start_row = max(2, total_rows // 3 + 1)
        end_row = min(total_rows - 1, total_rows * 2 // 3 + 1)
        return (start_row, end_row)
    
    @staticmethod
    def _is_bow_or_stern_only(tank_ids: List[str], ship: Ship) -> bool:
        """Check if all tanks are in bow or stern sections
        
        Bow definition: First 3 rows (rows 1, 2, 3)
        Stern definition: Last 3 rows (for 9-row ship: rows 7, 8, 9)
        
        Returns True if ALL tanks are in bow section OR ALL tanks are in stern section.
        This is used to enforce the rule that 4-tank cargos cannot be clustered in bow or stern.
        """
        if not tank_ids:
            return False
        
        # Get total rows to determine bow/stern boundaries
        total_rows = (len(ship.tanks) + 1) // 2
        
        # Define bow as first 3 rows and stern as last 3 rows
        bow_rows = set(range(1, min(4, total_rows + 1)))  # Rows 1, 2, 3
        stern_start = max(1, total_rows - 2)  # Last 3 rows
        stern_rows = set(range(stern_start, total_rows + 1))
        
        bow_count = 0
        stern_count = 0
        mid_count = 0
        
        for tank_id in tank_ids:
            pos_info = ship.get_tank_position_info(tank_id)
            if pos_info:
                row_num = pos_info['row_number']
                if row_num in bow_rows:
                    bow_count += 1
                elif row_num in stern_rows:
                    stern_count += 1
                else:
                    mid_count += 1
        
        # Return True if ALL tanks are in bow OR ALL tanks are in stern
        # (i.e., no mid tanks present)
        return (bow_count == len(tank_ids)) or (stern_count == len(tank_ids))
    
    @staticmethod
    def _is_all_same_side(tank_ids: List[str], ship: Ship) -> bool:
        """Check if all tanks are on the same side (port or starboard)"""
        if not tank_ids:
            return False
        
        first_pos = ship.get_tank_position_info(tank_ids[0])
        if not first_pos:
            return False
        
        first_side = first_pos['side']
        for tank_id in tank_ids[1:]:
            pos_info = ship.get_tank_position_info(tank_id)
            if not pos_info or pos_info['side'] != first_side:
                return False
        
        return True
    
    @staticmethod
    def _get_tank_available_capacity(tank_id: str, plan: StowagePlan, 
                                     available_tanks: Dict[str, float], 
                                     ship: Ship) -> float:
        """Get actual available capacity for a tank considering existing assignments
        
        Args:
            tank_id: Tank ID
            plan: Current stowage plan
            available_tanks: Dictionary of available volumes
            ship: Ship object
            
        Returns:
            Actual available capacity (considering existing assignments)
        """
        tank = ship.get_tank_by_id(tank_id)
        if not tank:
            return 0.0
        
        # Check if tank already has an assignment
        existing_assignment = plan.get_assignment(tank_id)
        if existing_assignment:
            # Tank already has cargo, calculate remaining capacity
            already_loaded = existing_assignment.quantity_loaded
            return max(0.0, tank.volume - already_loaded)
        else:
            # Use available_tanks value, but ensure it doesn't exceed tank.volume
            return min(available_tanks.get(tank_id, 0.0), tank.volume)
    
    # ==================== FAZ 0: Mandatory Cargo ====================
    
    def _faz0_mandatory_cargo(self, plan: StowagePlan, mandatory_cargos: List[Cargo],
                              available_tanks: Dict[str, float], ship: Ship, 
                              settings: Dict) -> Dict[str, float]:
        """FAZ 0: Process mandatory cargos with retry logic
        
        Must place 100% of quantity, no reduction allowed.
        For 4+ tank cargos: cannot all be in bow or stern.
        """
        min_util = settings.get('min_utilization', 0.65)
        retry_increment = settings.get('mandatory_retry_increment', 0.01)
        max_relaxation = settings.get('mandatory_max_relaxation', 0.35)
        
        for cargo in mandatory_cargos:
            if self._check_cancellation():
                break
                
            remaining_qty = cargo.quantity
            original_tolerance = 0.0  # Start with exact fit
            
            # Try with increasing tolerance
            for attempt in range(int(max_relaxation / retry_increment) + 1):
                if self._check_cancellation():
                    break
                    
                tolerance = original_tolerance + (attempt * retry_increment)
                
                # Estimate how many tanks needed
                max_tank_vol = max(available_tanks.values()) if available_tanks else 0
                if max_tank_vol <= 0:
                    break  # No tanks available
                
                estimated_tanks = max(1, int((remaining_qty / max_tank_vol) + 0.5))
                
                # Try FAZ 1-7 based on estimated tanks needed
                placed = False
                temp_plan = StowagePlan(
                    ship_name=plan.ship_name,
                    ship_profile_id=plan.ship_profile_id,
                    cargo_requests=[cargo],
                    plan_name="temp"
                )
                temp_available = available_tanks.copy()
                
                if estimated_tanks == 1:
                    temp_available = self._faz1_single_tank(
                        temp_plan, [cargo], temp_available, ship, settings, tolerance
                    )
                elif estimated_tanks == 2:
                    temp_available = self._faz2_two_tank(
                        temp_plan, [cargo], temp_available, ship, settings, tolerance
                    )
                elif estimated_tanks == 3:
                    temp_available = self._faz3_three_tank(
                        temp_plan, [cargo], temp_available, ship, settings, tolerance
                    )
                elif estimated_tanks == 4:
                    temp_available = self._faz4_four_tank(
                        temp_plan, [cargo], temp_available, ship, settings, tolerance
                    )
                elif estimated_tanks == 5:
                    temp_available = self._faz5_five_tank(
                        temp_plan, [cargo], temp_available, ship, settings, tolerance
                    )
                elif estimated_tanks == 6:
                    temp_available = self._faz6_six_tank(
                        temp_plan, [cargo], temp_available, ship, settings, tolerance
                    )
                else:
                    temp_available = self._faz7_multi_tank(
                        temp_plan, [cargo], temp_available, ship, settings
                    )
                
                loaded = temp_plan.get_cargo_total_loaded(cargo.unique_id)
                
                # Check if fully loaded and meets restrictions
                if loaded >= remaining_qty - 0.001:
                    # CRITICAL RULE: For 4-tank cargos, check bow/stern restriction
                    # 4-tank cargos CANNOT be clustered in bow or stern
                    if estimated_tanks == 4:
                        assigned_tank_ids = [tid for tid, ass in temp_plan.assignments.items()
                                            if ass.cargo.unique_id == cargo.unique_id]
                        if len(assigned_tank_ids) == 4 and AdvancedStowageOptimizerWithProgress._is_bow_or_stern_only(assigned_tank_ids, ship):
                            continue  # Try next tolerance level - violates bow/stern restriction
                    
                    # Success: copy assignments to main plan
                    for tank_id, assignment in temp_plan.assignments.items():
                        plan.add_assignment(tank_id, assignment)
                    available_tanks = temp_available
                    placed = True
                    break
                
                # If we exhausted tolerance, try next phase
                if tolerance >= max_relaxation:
                    break
            
            # If still not placed, try other phases
            if not placed:
                # Try all phases sequentially with relaxed tolerance
                for faz_func in [
                    self._faz1_single_tank,
                    self._faz2_two_tank,
                    self._faz3_three_tank,
                    self._faz4_four_tank,
                    self._faz5_five_tank,
                    self._faz6_six_tank,
                    self._faz7_multi_tank
                ]:
                    if self._check_cancellation():
                        break
                        
                    temp_plan = StowagePlan(
                        ship_name=plan.ship_name,
                        ship_profile_id=plan.ship_profile_id,
                        cargo_requests=[cargo],
                        plan_name="temp"
                    )
                    temp_available = available_tanks.copy()
                    temp_available = faz_func(temp_plan, [cargo], temp_available, ship, settings, max_relaxation)
                    
                    loaded = temp_plan.get_cargo_total_loaded(cargo.unique_id)
                    if loaded >= remaining_qty - 0.001:
                        # CRITICAL RULE: Check bow/stern restriction for 4-tank cargos
                        assigned_tank_ids = [tid for tid, ass in temp_plan.assignments.items()
                                            if ass.cargo.unique_id == cargo.unique_id]
                        # 4-tank cargos CANNOT be clustered in bow or stern
                        if len(assigned_tank_ids) == 4:
                            if AdvancedStowageOptimizerWithProgress._is_bow_or_stern_only(assigned_tank_ids, ship):
                                continue  # Skip - violates bow/stern restriction
                        
                        for tank_id, assignment in temp_plan.assignments.items():
                            plan.add_assignment(tank_id, assignment)
                        available_tanks = temp_available
                        break
        
        return available_tanks
    
    # ==================== FAZ 1: Single Tank Fitting ====================
    
    def _faz1_single_tank(self, plan: StowagePlan, cargos: List[Cargo],
                          available_tanks: Dict[str, float], ship: Ship, 
                          settings: Dict, override_tolerance: Optional[float] = None) -> Dict[str, float]:
        """FAZ 1: Single tank fitting with tolerance
        
        Criteria: ±tolerance (default 5%), minimum 65% utilization
        No symmetry consideration
        """
        min_util = settings.get('min_utilization', 0.65)
        tolerance = override_tolerance if override_tolerance is not None else settings.get('faz1_single_tank_tolerance', 0.05)
        
        # Process each cargo
        for i, cargo in enumerate(cargos):
            if self._check_cancellation():
                break
                
            # Report progress for each cargo
            if len(cargos) > 1:
                progress = (i + 1) / len(cargos) * 100
                self._report_progress(
                    ProgressStage.RUNNING_OPTIMIZATION,
                    12.5 + (progress * 0.125),  # 12.5% to 25% range
                    f"FAZ 1: Processing cargo {i+1}/{len(cargos)}: {cargo.name}"
                )
            
            remaining_qty = cargo.quantity
            
            # Find best-fit tank
            best_tank_id = None
            best_deviation = float('inf')
            
            for tank_id, available_vol in available_tanks.items():
                if available_vol < remaining_qty * (1 - tolerance):
                    continue  # Too small even with tolerance
                
                tank = ship.get_tank_by_id(tank_id)
                if not tank:
                    continue
                
                # Check tolerance fit
                deviation = AdvancedStowageOptimizerWithProgress._calculate_tolerance_deviation(remaining_qty, tank.volume)
                if deviation > tolerance:
                    continue
                
                # Check minimum utilization
                if not AdvancedStowageOptimizerWithProgress._check_min_utilization(remaining_qty, tank.volume, min_util):
                    continue
                
                # Select best fit (closest to 0% deviation)
                if deviation < best_deviation:
                    best_deviation = deviation
                    best_tank_id = tank_id
            
            if best_tank_id:
                tank = ship.get_tank_by_id(best_tank_id)
                # Get actual available capacity considering existing assignments
                actual_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                    best_tank_id, plan, available_tanks, ship
                )
                qty_to_load = min(remaining_qty, actual_available, tank.volume)
                
                # Final safety check: ensure we don't exceed tank capacity
                existing_assignment = plan.get_assignment(best_tank_id)
                if existing_assignment:
                    total_loaded = existing_assignment.quantity_loaded + qty_to_load
                    if total_loaded > tank.volume:
                        qty_to_load = max(0.0, tank.volume - existing_assignment.quantity_loaded)
                
                if qty_to_load > 0.001:
                    assignment = TankAssignment(
                        tank_id=best_tank_id,
                        cargo=cargo,
                        quantity_loaded=qty_to_load
                    )
                    plan.add_assignment(best_tank_id, assignment)
                    available_tanks[best_tank_id] -= qty_to_load
                    
                    if available_tanks[best_tank_id] < 0.001:
                        available_tanks[best_tank_id] = 0
        
        return available_tanks
    
    # ==================== FAZ 2: Two Tank Fitting ====================
    
    def _faz2_two_tank(self, plan: StowagePlan, cargos: List[Cargo],
                      available_tanks: Dict[str, float], ship: Ship,
                      settings: Dict, override_tolerance: Optional[float] = None) -> Dict[str, float]:
        """FAZ 2: Two tank fitting with symmetric/asymmetric sub-phases
        
        Sub-phases:
        2A: Full symmetric (same row port/starboard)
        2B: Partial symmetric (different rows but balanced)
        2C: Asymmetric (same side, tolerance = symmetric / 5)
        """
        min_util = settings.get('min_utilization', 0.65)
        symmetric_tolerance = override_tolerance if override_tolerance is not None else settings.get('faz2_two_tank_tolerance', 0.05)
        asymmetric_factor = settings.get('faz2_asymmetric_tolerance_factor', 0.2)
        asymmetric_tolerance = symmetric_tolerance * asymmetric_factor
        
        for i, cargo in enumerate(cargos):
            if self._check_cancellation():
                break
                
            # Report progress for each cargo
            if len(cargos) > 1:
                progress = (i + 1) / len(cargos) * 100
                self._report_progress(
                    ProgressStage.RUNNING_OPTIMIZATION,
                    25.0 + (progress * 0.125),  # 25% to 37.5% range
                    f"FAZ 2: Processing cargo {i+1}/{len(cargos)}: {cargo.name}"
                )
            
            remaining_qty = cargo.quantity
            
            # Try 2A: Full symmetric (same row port/starboard)
            best_pair = None
            best_deviation = float('inf')
            best_type = None
            
            tank_pairs = ship.get_tank_pairs()
            for port_tank, starboard_tank in tank_pairs:
                port_id = port_tank.id
                starboard_id = starboard_tank.id
                
                if port_id not in available_tanks or starboard_id not in available_tanks:
                    continue
                
                # Get actual available capacities
                port_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                    port_id, plan, available_tanks, ship
                )
                starboard_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                    starboard_id, plan, available_tanks, ship
                )
                total_capacity = port_tank.volume + starboard_tank.volume
                
                # Check tolerance
                deviation = AdvancedStowageOptimizerWithProgress._calculate_tolerance_deviation(remaining_qty, total_capacity)
                if deviation > symmetric_tolerance:
                    continue
                
                # Distribute evenly with proper capacity checks
                port_qty = min(remaining_qty / 2, port_available, port_tank.volume)
                starboard_qty = min(remaining_qty - port_qty, starboard_available, starboard_tank.volume)
                
                # If starboard can't take remainder, adjust port
                if starboard_qty < remaining_qty - port_qty - 0.001:
                    starboard_qty = min(remaining_qty / 2, starboard_available, starboard_tank.volume)
                    port_qty = min(remaining_qty - starboard_qty, port_available, port_tank.volume)
                
                # Final safety check: ensure both don't exceed capacity
                port_qty = min(port_qty, port_available, port_tank.volume)
                starboard_qty = min(starboard_qty, starboard_available, starboard_tank.volume)
                
                # Check minimum utilization for both
                if not AdvancedStowageOptimizerWithProgress._check_min_utilization(port_qty, port_tank.volume, min_util):
                    continue
                if not AdvancedStowageOptimizerWithProgress._check_min_utilization(starboard_qty, starboard_tank.volume, min_util):
                    continue
                
                if deviation < best_deviation:
                    best_deviation = deviation
                    best_pair = (port_id, starboard_id, port_qty, starboard_qty)
                    best_type = 'symmetric'
            
            # Try 2B: Partial symmetric (different rows but port/starboard balance)
            if best_type != 'symmetric':
                for i_pair, (port1, star1) in enumerate(tank_pairs):
                    for j_pair, (port2, star2) in enumerate(tank_pairs[i_pair+1:], start=i_pair+1):
                        for combo in [(port1.id, star2.id), (star1.id, port2.id)]:
                            tank1_id, tank2_id = combo
                            if tank1_id not in available_tanks or tank2_id not in available_tanks:
                                continue
                            
                            tank1 = ship.get_tank_by_id(tank1_id)
                            tank2 = ship.get_tank_by_id(tank2_id)
                            if not tank1 or not tank2:
                                continue
                            
                            # Get actual available capacities
                            tank1_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                                tank1_id, plan, available_tanks, ship
                            )
                            tank2_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                                tank2_id, plan, available_tanks, ship
                            )
                            
                            total_cap = tank1.volume + tank2.volume
                            deviation = AdvancedStowageOptimizerWithProgress._calculate_tolerance_deviation(remaining_qty, total_cap)
                            if deviation > symmetric_tolerance:
                                continue
                            
                            # Distribute with proper capacity checks
                            qty1 = min(remaining_qty / 2, tank1_available, tank1.volume)
                            qty2 = min(remaining_qty - qty1, tank2_available, tank2.volume)
                            
                            # If tank2 can't take remainder, adjust tank1
                            if qty2 < remaining_qty - qty1 - 0.001:
                                qty2 = min(remaining_qty / 2, tank2_available, tank2.volume)
                                qty1 = min(remaining_qty - qty2, tank1_available, tank1.volume)
                            
                            # Final safety check
                            qty1 = min(qty1, tank1_available, tank1.volume)
                            qty2 = min(qty2, tank2_available, tank2.volume)
                            
                            if not AdvancedStowageOptimizerWithProgress._check_min_utilization(qty1, tank1.volume, min_util):
                                continue
                            if not AdvancedStowageOptimizerWithProgress._check_min_utilization(qty2, tank2.volume, min_util):
                                continue
                            
                            if deviation < best_deviation:
                                best_deviation = deviation
                                best_pair = (tank1_id, tank2_id, qty1, qty2)
                                best_type = 'partial_symmetric'
            
            # Try 2C: Asymmetric (same side)
            if best_type is None:
                all_tanks = [(tid, ship.get_tank_by_id(tid)) for tid in available_tanks.keys()]
                for i_tank, (tid1, tank1) in enumerate(all_tanks):
                    if not tank1:
                        continue
                    pos1 = ship.get_tank_position_info(tid1)
                    if not pos1:
                        continue
                    
                    for j_tank, (tid2, tank2) in enumerate(all_tanks[i_tank+1:], start=i_tank+1):
                        if not tank2:
                            continue
                        pos2 = ship.get_tank_position_info(tid2)
                        if not pos2 or pos2['side'] != pos1['side']:
                            continue
                        
                        # Get actual available capacities
                        tank1_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                            tid1, plan, available_tanks, ship
                        )
                        tank2_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                            tid2, plan, available_tanks, ship
                        )
                        
                        total_cap = tank1.volume + tank2.volume
                        deviation = AdvancedStowageOptimizerWithProgress._calculate_tolerance_deviation(remaining_qty, total_cap)
                        if deviation > asymmetric_tolerance:
                            continue
                        
                        # Distribute with proper capacity checks
                        qty1 = min(remaining_qty / 2, tank1_available, tank1.volume)
                        qty2 = min(remaining_qty - qty1, tank2_available, tank2.volume)
                        
                        # If tank2 can't take remainder, adjust tank1
                        if qty2 < remaining_qty - qty1 - 0.001:
                            qty2 = min(remaining_qty / 2, tank2_available, tank2.volume)
                            qty1 = min(remaining_qty - qty2, tank1_available, tank1.volume)
                        
                        # Final safety check
                        qty1 = min(qty1, tank1_available, tank1.volume)
                        qty2 = min(qty2, tank2_available, tank2.volume)
                        
                        if not AdvancedStowageOptimizerWithProgress._check_min_utilization(qty1, tank1.volume, min_util):
                            continue
                        if not AdvancedStowageOptimizerWithProgress._check_min_utilization(qty2, tank2.volume, min_util):
                            continue
                        
                        if deviation < best_deviation:
                            best_deviation = deviation
                            best_pair = (tid1, tid2, qty1, qty2)
                            best_type = 'asymmetric'
            
            # Place best pair found
            if best_pair:
                tank1_id, tank2_id, qty1, qty2 = best_pair
                
                assignment1 = TankAssignment(tank_id=tank1_id, cargo=cargo, quantity_loaded=qty1)
                plan.add_assignment(tank1_id, assignment1)
                available_tanks[tank1_id] -= qty1
                
                assignment2 = TankAssignment(tank_id=tank2_id, cargo=cargo, quantity_loaded=qty2)
                plan.add_assignment(tank2_id, assignment2)
                available_tanks[tank2_id] -= qty2
        
        return available_tanks
    
    # ==================== FAZ 3: Three Tank Fitting ====================
    
    def _faz3_three_tank(self, plan: StowagePlan, cargos: List[Cargo],
                        available_tanks: Dict[str, float], ship: Ship,
                        settings: Dict, override_tolerance: Optional[float] = None) -> Dict[str, float]:
        """FAZ 3: Three tank fitting
        
        Rule: Cannot have all 3 tanks on same side (at least 1 on opposite side)
        """
        min_util = settings.get('min_utilization', 0.65)
        tolerance = override_tolerance if override_tolerance is not None else settings.get('faz3_three_tank_tolerance', 0.04)
        
        for i, cargo in enumerate(cargos):
            if self._check_cancellation():
                break
                
            # Report progress for each cargo
            if len(cargos) > 1:
                progress = (i + 1) / len(cargos) * 100
                self._report_progress(
                    ProgressStage.RUNNING_OPTIMIZATION,
                    37.5 + (progress * 0.125),  # 37.5% to 50% range
                    f"FAZ 3: Processing cargo {i+1}/{len(cargos)}: {cargo.name}"
                )
            
            remaining_qty = cargo.quantity
            
            best_triplet = None
            best_deviation = float('inf')
            
            # Generate all possible triplets
            tank_list = [(tid, ship.get_tank_by_id(tid)) for tid in available_tanks.keys()]
            
            for i_tank, (tid1, tank1) in enumerate(tank_list):
                if not tank1:
                    continue
                for j_tank, (tid2, tank2) in enumerate(tank_list[i_tank+1:], start=i_tank+1):
                    if not tank2:
                        continue
                    for k_tank, (tid3, tank3) in enumerate(tank_list[j_tank+1:], start=j_tank+1):
                        if not tank3:
                            continue
                        
                        # Check side rule: cannot all be on same side
                        pos1 = ship.get_tank_position_info(tid1)
                        pos2 = ship.get_tank_position_info(tid2)
                        pos3 = ship.get_tank_position_info(tid3)
                        
                        if pos1 and pos2 and pos3:
                            sides = {pos1['side'], pos2['side'], pos3['side']}
                            if len(sides) == 1:  # All same side
                                continue
                        
                        # Get actual available capacities
                        tank1_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                            tid1, plan, available_tanks, ship
                        )
                        tank2_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                            tid2, plan, available_tanks, ship
                        )
                        tank3_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                            tid3, plan, available_tanks, ship
                        )
                        
                        total_cap = tank1.volume + tank2.volume + tank3.volume
                        deviation = AdvancedStowageOptimizerWithProgress._calculate_tolerance_deviation(remaining_qty, total_cap)
                        if deviation > tolerance:
                            continue
                        
                        # Distribute evenly with proper capacity checks
                        qty_per_tank = remaining_qty / 3
                        qty1 = min(qty_per_tank, tank1_available, tank1.volume)
                        qty2 = min(qty_per_tank, tank2_available, tank2.volume)
                        qty3 = min(qty_per_tank, tank3_available, tank3.volume)
                        
                        # Adjust if needed
                        total_assigned = qty1 + qty2 + qty3
                        if total_assigned < remaining_qty - 0.001:
                            remaining = remaining_qty - total_assigned
                            # Distribute remaining with proper capacity checks
                            if tank1_available - qty1 > 0.001:
                                add = min(remaining, tank1_available - qty1, max(0.0, tank1.volume - qty1))
                                qty1 += add
                                remaining -= add
                            if tank2_available - qty2 > 0.001 and remaining > 0.001:
                                add = min(remaining, tank2_available - qty2, max(0.0, tank2.volume - qty2))
                                qty2 += add
                                remaining -= add
                            if tank3_available - qty3 > 0.001 and remaining > 0.001:
                                add = min(remaining, tank3_available - qty3, max(0.0, tank3.volume - qty3))
                                qty3 += add
                                remaining -= add
                        
                        # Final safety check: ensure all quantities are within capacity
                        qty1 = min(qty1, tank1_available, tank1.volume)
                        qty2 = min(qty2, tank2_available, tank2.volume)
                        qty3 = min(qty3, tank3_available, tank3.volume)
                        
                        # Check minimum utilization
                        if not AdvancedStowageOptimizerWithProgress._check_min_utilization(qty1, tank1.volume, min_util):
                            continue
                        if not AdvancedStowageOptimizerWithProgress._check_min_utilization(qty2, tank2.volume, min_util):
                            continue
                        if not AdvancedStowageOptimizerWithProgress._check_min_utilization(qty3, tank3.volume, min_util):
                            continue
                        
                        if deviation < best_deviation:
                            best_deviation = deviation
                            best_triplet = (tid1, tid2, tid3, qty1, qty2, qty3)
            
            if best_triplet:
                tid1, tid2, tid3, qty1, qty2, qty3 = best_triplet
                
                plan.add_assignment(tid1, TankAssignment(tank_id=tid1, cargo=cargo, quantity_loaded=qty1))
                available_tanks[tid1] -= qty1
                plan.add_assignment(tid2, TankAssignment(tank_id=tid2, cargo=cargo, quantity_loaded=qty2))
                available_tanks[tid2] -= qty2
                plan.add_assignment(tid3, TankAssignment(tank_id=tid3, cargo=cargo, quantity_loaded=qty3))
                available_tanks[tid3] -= qty3
        
        return available_tanks
    
    # ==================== FAZ 4: Four Tank Fitting ====================
    
    def _faz4_four_tank(self, plan: StowagePlan, cargos: List[Cargo],
                       available_tanks: Dict[str, float], ship: Ship,
                       settings: Dict, override_tolerance: Optional[float] = None) -> Dict[str, float]:
        """FAZ 4: Four tank fitting
        
        CRITICAL RULES:
        - MUST NOT: All 4 tanks cannot be clustered in bow section
        - MUST NOT: All 4 tanks cannot be clustered in stern section
        - CAN: All 4 side-by-side only at mid-section (center rows)
        - CAN: Otherwise: spacing preferred (1 tank gap between)
        Split into 2×2 pairs using FAZ 2 criteria
        """
        min_util = settings.get('min_utilization', 0.65)
        tolerance = override_tolerance if override_tolerance is not None else settings.get('faz4_four_tank_tolerance', 0.04)
        
        for i, cargo in enumerate(cargos):
            if self._check_cancellation():
                break
                
            # Report progress for each cargo
            if len(cargos) > 1:
                progress = (i + 1) / len(cargos) * 100
                self._report_progress(
                    ProgressStage.RUNNING_OPTIMIZATION,
                    50.0 + (progress * 0.125),  # 50% to 62.5% range
                    f"FAZ 4: Processing cargo {i+1}/{len(cargos)}: {cargo.name}"
                )
            
            remaining_qty = cargo.quantity
            
            # Split into 2×2 pairs using FAZ 2 logic
            # Try to find two pairs that together fit the cargo
            best_combination = None
            best_total_deviation = float('inf')
            
            # Get all tank pairs
            tank_pairs = ship.get_tank_pairs()
            all_tanks_list = [(tid, ship.get_tank_by_id(tid)) for tid in available_tanks.keys()]
            
            # Try combinations of 2 pairs
            for i_pair, (port1, star1) in enumerate(tank_pairs):
                port1_id = port1.id
                star1_id = star1.id
                if port1_id not in available_tanks or star1_id not in available_tanks:
                    continue
                
                for j_pair, (port2, star2) in enumerate(tank_pairs[i_pair+1:], start=i_pair+1):
                    port2_id = port2.id
                    star2_id = star2.id
                    if port2_id not in available_tanks or star2_id not in available_tanks:
                        continue
                    
                    # CRITICAL RULE: 4-tank cargos cannot be clustered in bow or stern
                    # Check that not all 4 tanks are in bow or all in stern
                    tank_ids = [port1_id, star1_id, port2_id, star2_id]
                    if AdvancedStowageOptimizerWithProgress._is_bow_or_stern_only(tank_ids, ship):
                        continue  # Skip this combination - violates bow/stern restriction
                    
                    # Check mid-section rule for side-by-side
                    all_same_row = True
                    row_nums = set()
                    for tid in tank_ids:
                        pos = ship.get_tank_position_info(tid)
                        if pos:
                            row_nums.add(pos['row_number'])
                    if len(row_nums) == 1:
                        # All same row - check if mid-section
                        mid_start, mid_end = AdvancedStowageOptimizerWithProgress._get_mid_section_rows(ship)
                        if row_nums.pop() not in range(mid_start, mid_end + 1):
                            continue  # Not in mid-section
                    
                    # Try splitting cargo into two pairs
                    pair1_cap = port1.volume + star1.volume
                    pair2_cap = port2.volume + star2.volume
                    total_cap = pair1_cap + pair2_cap
                    
                    deviation = AdvancedStowageOptimizerWithProgress._calculate_tolerance_deviation(remaining_qty, total_cap)
                    if deviation > tolerance:
                        continue
                    
                    # Get actual available capacities
                    port1_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                        port1_id, plan, available_tanks, ship
                    )
                    star1_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                        star1_id, plan, available_tanks, ship
                    )
                    port2_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                        port2_id, plan, available_tanks, ship
                    )
                    star2_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                        star2_id, plan, available_tanks, ship
                    )
                    
                    # Distribute proportionally
                    qty1 = remaining_qty * (pair1_cap / total_cap)
                    qty2 = remaining_qty - qty1
                    
                    # Check if pairs can handle their quantities with FAZ 2 criteria
                    # Pair 1
                    port1_qty = min(qty1 / 2, port1_available, port1.volume)
                    star1_qty = min(qty1 - port1_qty, star1_available, star1.volume)
                    if star1_qty < qty1 - port1_qty - 0.001:
                        star1_qty = min(qty1 / 2, star1_available, star1.volume)
                        port1_qty = min(qty1 - star1_qty, port1_available, port1.volume)
                    
                    # Final safety check for pair 1
                    port1_qty = min(port1_qty, port1_available, port1.volume)
                    star1_qty = min(star1_qty, star1_available, star1.volume)
                    
                    if not AdvancedStowageOptimizerWithProgress._check_min_utilization(port1_qty, port1.volume, min_util):
                        continue
                    if not AdvancedStowageOptimizerWithProgress._check_min_utilization(star1_qty, star1.volume, min_util):
                        continue
                    
                    # Pair 2
                    port2_qty = min(qty2 / 2, port2_available, port2.volume)
                    star2_qty = min(qty2 - port2_qty, star2_available, star2.volume)
                    if star2_qty < qty2 - port2_qty - 0.001:
                        star2_qty = min(qty2 / 2, star2_available, star2.volume)
                        port2_qty = min(qty2 - star2_qty, port2_available, port2.volume)
                    
                    # Final safety check for pair 2
                    port2_qty = min(port2_qty, port2_available, port2.volume)
                    star2_qty = min(star2_qty, star2_available, star2.volume)
                    
                    if not AdvancedStowageOptimizerWithProgress._check_min_utilization(port2_qty, port2.volume, min_util):
                        continue
                    if not AdvancedStowageOptimizerWithProgress._check_min_utilization(star2_qty, star2.volume, min_util):
                        continue
                    
                    if deviation < best_total_deviation:
                        best_total_deviation = deviation
                        best_combination = (port1_id, star1_id, port2_id, star2_id,
                                          port1_qty, star1_qty, port2_qty, star2_qty)
            
            if best_combination:
                p1_id, s1_id, p2_id, s2_id, p1_qty, s1_qty, p2_qty, s2_qty = best_combination
                
                plan.add_assignment(p1_id, TankAssignment(tank_id=p1_id, cargo=cargo, quantity_loaded=p1_qty))
                available_tanks[p1_id] -= p1_qty
                plan.add_assignment(s1_id, TankAssignment(tank_id=s1_id, cargo=cargo, quantity_loaded=s1_qty))
                available_tanks[s1_id] -= s1_qty
                plan.add_assignment(p2_id, TankAssignment(tank_id=p2_id, cargo=cargo, quantity_loaded=p2_qty))
                available_tanks[p2_id] -= p2_qty
                plan.add_assignment(s2_id, TankAssignment(tank_id=s2_id, cargo=cargo, quantity_loaded=s2_qty))
                available_tanks[s2_id] -= s2_qty
        
        return available_tanks
    
    # ==================== FAZ 5: Five Tank Fitting ====================
    
    def _faz5_five_tank(self, plan: StowagePlan, cargos: List[Cargo],
                       available_tanks: Dict[str, float], ship: Ship,
                       settings: Dict, override_tolerance: Optional[float] = None) -> Dict[str, float]:
        """FAZ 5: Five tank fitting
        
        Rule: If 3 tanks on one side, other 2 must be on opposite side
        Strategies:
        5A: 2+2+1 (FAZ 2 twice + FAZ 1)
        5B: 3+2 (FAZ 3 + FAZ 2)
        """
        min_util = settings.get('min_utilization', 0.65)
        tolerance = override_tolerance if override_tolerance is not None else settings.get('faz5_five_tank_tolerance', 0.04)
        
        for i, cargo in enumerate(cargos):
            if self._check_cancellation():
                break
                
            # Report progress for each cargo
            if len(cargos) > 1:
                progress = (i + 1) / len(cargos) * 100
                self._report_progress(
                    ProgressStage.RUNNING_OPTIMIZATION,
                    62.5 + (progress * 0.125),  # 62.5% to 75% range
                    f"FAZ 5: Processing cargo {i+1}/{len(cargos)}: {cargo.name}"
                )
            
            remaining_qty = cargo.quantity
            
            best_solution = None
            best_score = float('inf')
            
            # Strategy 5A: 2+2+1
            # Try to find two pairs and one single tank
            # (This is complex - simplified: try all combinations)
            
            # Strategy 5B: 3+2
            # Try to find a triplet and a pair
            tank_list = [(tid, ship.get_tank_by_id(tid)) for tid in available_tanks.keys()]
            tank_pairs = ship.get_tank_pairs()
            
            # Try 3+2 strategy
            for i_tank, (tid1, tank1) in enumerate(tank_list):
                if not tank1:
                    continue
                for j_tank, (tid2, tank2) in enumerate(tank_list[i_tank+1:], start=i_tank+1):
                    if not tank2:
                        continue
                    for k_tank, (tid3, tank3) in enumerate(tank_list[j_tank+1:], start=j_tank+1):
                        if not tank3:
                            continue
                        
                        # Check side rule for triplet
                        pos1 = ship.get_tank_position_info(tid1)
                        pos2 = ship.get_tank_position_info(tid2)
                        pos3 = ship.get_tank_position_info(tid3)
                        
                        if pos1 and pos2 and pos3:
                            sides_3 = {pos1['side'], pos2['side'], pos3['side']}
                            if len(sides_3) == 1:  # All same side - need 2 on opposite
                                required_side = "starboard" if pos1['side'] == "port" else "port"
                            else:
                                required_side = None  # Already balanced
                        else:
                            required_side = None
                        
                        # Find pair for remaining 2
                        for port_tank, starboard_tank in tank_pairs:
                            port_id = port_tank.id
                            starboard_id = starboard_tank.id
                            
                            if port_id in [tid1, tid2, tid3] or starboard_id in [tid1, tid2, tid3]:
                                continue
                            
                            if port_id not in available_tanks or starboard_id not in available_tanks:
                                continue
                            
                            # Check side rule
                            if required_side:
                                pos_pair = ship.get_tank_position_info(port_id if required_side == "port" else starboard_id)
                                if not pos_pair or pos_pair['side'] != required_side:
                                    continue
                            
                            # Calculate quantities
                            triplet_cap = tank1.volume + tank2.volume + tank3.volume
                            pair_cap = port_tank.volume + starboard_tank.volume
                            total_cap = triplet_cap + pair_cap
                            
                            deviation = AdvancedStowageOptimizerWithProgress._calculate_tolerance_deviation(remaining_qty, total_cap)
                            if deviation > tolerance:
                                continue
                            
                            # Get actual available capacities
                            tank1_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                                tid1, plan, available_tanks, ship
                            )
                            tank2_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                                tid2, plan, available_tanks, ship
                            )
                            tank3_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                                tid3, plan, available_tanks, ship
                            )
                            port_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                                port_id, plan, available_tanks, ship
                            )
                            starboard_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                                starboard_id, plan, available_tanks, ship
                            )
                            
                            # Distribute
                            qty_3 = remaining_qty * (triplet_cap / total_cap)
                            qty_2 = remaining_qty - qty_3
                            
                            # Triplet distribution with proper capacity checks
                            qty1 = min(qty_3 / 3, tank1_available, tank1.volume)
                            qty2 = min(qty_3 / 3, tank2_available, tank2.volume)
                            qty3 = min(qty_3 - qty1 - qty2, tank3_available, tank3.volume)
                            
                            # If tank3 can't take remainder, redistribute
                            if qty3 < qty_3 - qty1 - qty2 - 0.001:
                                qty3 = min(qty_3 / 3, tank3_available, tank3.volume)
                                remaining_triplet = qty_3 - qty3
                                # Redistribute remaining between tank1 and tank2
                                qty1 = min(remaining_triplet / 2, tank1_available, tank1.volume)
                                qty2 = min(remaining_triplet - qty1, tank2_available, tank2.volume)
                                if qty2 < remaining_triplet - qty1 - 0.001:
                                    qty2 = min(remaining_triplet / 2, tank2_available, tank2.volume)
                                    qty1 = min(remaining_triplet - qty2, tank1_available, tank1.volume)
                            
                            # Final safety check for triplet
                            qty1 = min(qty1, tank1_available, tank1.volume)
                            qty2 = min(qty2, tank2_available, tank2.volume)
                            qty3 = min(qty3, tank3_available, tank3.volume)
                            
                            # Pair distribution with proper capacity checks
                            port_qty = min(qty_2 / 2, port_available, port_tank.volume)
                            starboard_qty = min(qty_2 - port_qty, starboard_available, starboard_tank.volume)
                            if starboard_qty < qty_2 - port_qty - 0.001:
                                starboard_qty = min(qty_2 / 2, starboard_available, starboard_tank.volume)
                                port_qty = min(qty_2 - starboard_qty, port_available, port_tank.volume)
                            
                            # Final safety check for pair
                            port_qty = min(port_qty, port_available, port_tank.volume)
                            starboard_qty = min(starboard_qty, starboard_available, starboard_tank.volume)
                            
                            # Check utilization
                            if not all([
                                AdvancedStowageOptimizerWithProgress._check_min_utilization(qty1, tank1.volume, min_util),
                                AdvancedStowageOptimizerWithProgress._check_min_utilization(qty2, tank2.volume, min_util),
                                AdvancedStowageOptimizerWithProgress._check_min_utilization(qty3, tank3.volume, min_util),
                                AdvancedStowageOptimizerWithProgress._check_min_utilization(port_qty, port_tank.volume, min_util),
                                AdvancedStowageOptimizerWithProgress._check_min_utilization(starboard_qty, starboard_tank.volume, min_util)
                            ]):
                                continue
                            
                            score = deviation
                            if score < best_score:
                                best_score = score
                                best_solution = ('3+2', tid1, tid2, tid3, port_id, starboard_id,
                                               qty1, qty2, qty3, port_qty, starboard_qty)
            
            if best_solution:
                strategy, tid1, tid2, tid3, p_id, s_id, q1, q2, q3, p_qty, s_qty = best_solution
                
                plan.add_assignment(tid1, TankAssignment(tank_id=tid1, cargo=cargo, quantity_loaded=q1))
                available_tanks[tid1] -= q1
                plan.add_assignment(tid2, TankAssignment(tank_id=tid2, cargo=cargo, quantity_loaded=q2))
                available_tanks[tid2] -= q2
                plan.add_assignment(tid3, TankAssignment(tank_id=tid3, cargo=cargo, quantity_loaded=q3))
                available_tanks[tid3] -= q3
                plan.add_assignment(p_id, TankAssignment(tank_id=p_id, cargo=cargo, quantity_loaded=p_qty))
                available_tanks[p_id] -= p_qty
                plan.add_assignment(s_id, TankAssignment(tank_id=s_id, cargo=cargo, quantity_loaded=s_qty))
                available_tanks[s_id] -= s_qty
        
        return available_tanks
    
    # ==================== FAZ 6: Six Tank Fitting ====================
    
    def _faz6_six_tank(self, plan: StowagePlan, cargos: List[Cargo],
                      available_tanks: Dict[str, float], ship: Ship,
                      settings: Dict, override_tolerance: Optional[float] = None) -> Dict[str, float]:
        """FAZ 6: Six tank fitting using 3×2 pair approach"""
        min_util = settings.get('min_utilization', 0.65)
        tolerance = override_tolerance if override_tolerance is not None else settings.get('faz2_two_tank_tolerance', 0.05)
        
        for i, cargo in enumerate(cargos):
            if self._check_cancellation():
                break
                
            # Report progress for each cargo
            if len(cargos) > 1:
                progress = (i + 1) / len(cargos) * 100
                self._report_progress(
                    ProgressStage.RUNNING_OPTIMIZATION,
                    75.0 + (progress * 0.125),  # 75% to 87.5% range
                    f"FAZ 6: Processing cargo {i+1}/{len(cargos)}: {cargo.name}"
                )
            
            remaining_qty = cargo.quantity
            
            # Find 3 symmetric pairs
            tank_pairs = ship.get_tank_pairs()
            best_combination = None
            best_deviation = float('inf')
            
            # Try combinations of 3 pairs
            for i_pair, pair1 in enumerate(tank_pairs):
                port1, star1 = pair1
                if port1.id not in available_tanks or star1.id not in available_tanks:
                    continue
                
                for j_pair, pair2 in enumerate(tank_pairs[i_pair+1:], start=i_pair+1):
                    port2, star2 = pair2
                    if port2.id not in available_tanks or star2.id not in available_tanks:
                        continue
                    
                    for k_pair, pair3 in enumerate(tank_pairs[j_pair+1:], start=j_pair+1):
                        port3, star3 = pair3
                        if port3.id not in available_tanks or star3.id not in available_tanks:
                            continue
                        
                        total_cap = (port1.volume + star1.volume + 
                                   port2.volume + star2.volume + 
                                   port3.volume + star3.volume)
                        
                        deviation = AdvancedStowageOptimizerWithProgress._calculate_tolerance_deviation(remaining_qty, total_cap)
                        if deviation > tolerance:
                            continue
                        
                        # Get actual available capacities
                        p1_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                            port1.id, plan, available_tanks, ship
                        )
                        s1_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                            star1.id, plan, available_tanks, ship
                        )
                        p2_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                            port2.id, plan, available_tanks, ship
                        )
                        s2_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                            star2.id, plan, available_tanks, ship
                        )
                        p3_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                            port3.id, plan, available_tanks, ship
                        )
                        s3_available = AdvancedStowageOptimizerWithProgress._get_tank_available_capacity(
                            star3.id, plan, available_tanks, ship
                        )
                        
                        # Distribute evenly across 3 pairs
                        qty_per_pair = remaining_qty / 3
                        
                        # Pair 1
                        p1_qty = min(qty_per_pair / 2, p1_available, port1.volume)
                        s1_qty = min(qty_per_pair - p1_qty, s1_available, star1.volume)
                        if s1_qty < qty_per_pair - p1_qty - 0.001:
                            s1_qty = min(qty_per_pair / 2, s1_available, star1.volume)
                            p1_qty = min(qty_per_pair - s1_qty, p1_available, port1.volume)
                        # Final safety check
                        p1_qty = min(p1_qty, p1_available, port1.volume)
                        s1_qty = min(s1_qty, s1_available, star1.volume)
                        
                        # Pair 2
                        p2_qty = min(qty_per_pair / 2, p2_available, port2.volume)
                        s2_qty = min(qty_per_pair - p2_qty, s2_available, star2.volume)
                        if s2_qty < qty_per_pair - p2_qty - 0.001:
                            s2_qty = min(qty_per_pair / 2, s2_available, star2.volume)
                            p2_qty = min(qty_per_pair - s2_qty, p2_available, port2.volume)
                        # Final safety check
                        p2_qty = min(p2_qty, p2_available, port2.volume)
                        s2_qty = min(s2_qty, s2_available, star2.volume)
                        
                        # Pair 3
                        p3_qty = min(qty_per_pair / 2, p3_available, port3.volume)
                        s3_qty = min(qty_per_pair - p3_qty, s3_available, star3.volume)
                        if s3_qty < qty_per_pair - p3_qty - 0.001:
                            s3_qty = min(qty_per_pair / 2, s3_available, star3.volume)
                            p3_qty = min(qty_per_pair - s3_qty, p3_available, port3.volume)
                        # Final safety check
                        p3_qty = min(p3_qty, p3_available, port3.volume)
                        s3_qty = min(s3_qty, s3_available, star3.volume)
                        
                        # Check utilization
                        if not all([
                            AdvancedStowageOptimizerWithProgress._check_min_utilization(p1_qty, port1.volume, min_util),
                            AdvancedStowageOptimizerWithProgress._check_min_utilization(s1_qty, star1.volume, min_util),
                            AdvancedStowageOptimizerWithProgress._check_min_utilization(p2_qty, port2.volume, min_util),
                            AdvancedStowageOptimizerWithProgress._check_min_utilization(s2_qty, star2.volume, min_util),
                            AdvancedStowageOptimizerWithProgress._check_min_utilization(p3_qty, port3.volume, min_util),
                            AdvancedStowageOptimizerWithProgress._check_min_utilization(s3_qty, star3.volume, min_util)
                        ]):
                            continue
                        
                        if deviation < best_deviation:
                            best_deviation = deviation
                            best_combination = (port1.id, star1.id, port2.id, star2.id, port3.id, star3.id,
                                              p1_qty, s1_qty, p2_qty, s2_qty, p3_qty, s3_qty)
            
            if best_combination:
                p1_id, s1_id, p2_id, s2_id, p3_id, s3_id, p1_qty, s1_qty, p2_qty, s2_qty, p3_qty, s3_qty = best_combination
                
                for tid, qty in [(p1_id, p1_qty), (s1_id, s1_qty), (p2_id, p2_qty), 
                               (s2_id, s2_qty), (p3_id, p3_qty), (s3_id, s3_qty)]:
                    plan.add_assignment(tid, TankAssignment(tank_id=tid, cargo=cargo, quantity_loaded=qty))
                    available_tanks[tid] -= qty
        
        return available_tanks
    
    # ==================== FAZ 7: Multi-Tank Best-Fit ====================
    
    def _faz7_multi_tank(self, plan: StowagePlan, cargos: List[Cargo],
                        available_tanks: Dict[str, float], ship: Ship,
                        settings: Dict) -> Dict[str, float]:
        """FAZ 7: Best-fit approach for 7+ tank cargos"""
        min_util = settings.get('min_utilization', 0.65)
        
        for i, cargo in enumerate(cargos):
            if self._check_cancellation():
                break
                
            # Report progress for each cargo
            if len(cargos) > 1:
                progress = (i + 1) / len(cargos) * 100
                self._report_progress(
                    ProgressStage.RUNNING_OPTIMIZATION,
                    87.5 + (progress * 0.125),  # 87.5% to 100% range
                    f"FAZ 7: Processing cargo {i+1}/{len(cargos)}: {cargo.name}"
                )
            
            remaining_qty = cargo.quantity
            
            # Sort tanks by available volume (descending)
            sorted_tanks = sorted(
                [(tid, vol, ship.get_tank_by_id(tid)) for tid, vol in available_tanks.items() if vol > 0.001],
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
                if not AdvancedStowageOptimizerWithProgress._check_min_utilization(qty_to_place, tank.volume, min_util):
                    continue
                
                assignment = TankAssignment(
                    tank_id=tank_id,
                    cargo=cargo,
                    quantity_loaded=qty_to_place
                )
                plan.add_assignment(tank_id, assignment)
                available_tanks[tank_id] -= qty_to_place
                remaining_qty -= qty_to_place
        
        return available_tanks