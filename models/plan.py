"""Stowage Plan model class"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from models.cargo import Cargo


@dataclass
class TankAssignment:
    """Represents a cargo assignment to a tank"""
    tank_id: str
    cargo: Cargo
    quantity_loaded: float  # Actual quantity loaded in this tank
    
    def to_dict(self) -> dict:
        """Convert assignment to dictionary"""
        return {
            'tank_id': self.tank_id,
            'cargo': self.cargo.to_dict(),
            'quantity_loaded': self.quantity_loaded
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TankAssignment':
        """Create TankAssignment from dictionary"""
        return cls(
            tank_id=data['tank_id'],
            cargo=Cargo.from_dict(data['cargo']),
            quantity_loaded=data['quantity_loaded']
        )


@dataclass
class StowagePlan:
    """Represents a complete stowage plan"""
    ship_name: str
    ship_profile_id: str
    cargo_requests: List[Cargo]
    assignments: Dict[str, TankAssignment] = field(default_factory=dict)  # tank_id -> assignment
    excluded_tanks: List[str] = field(default_factory=list)  # Tank IDs excluded from planning
    created_date: Optional[datetime] = None
    plan_name: str = None
    notes: str = None  # Detailed notes for the plan
    id: str = None
    
    def __post_init__(self):
        """Initialize default values"""
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_date:
            self.created_date = datetime.now()
        if not self.plan_name:
            self.plan_name = f"Plan_{self.created_date.strftime('%Y%m%d_%H%M%S')}"
    
    def add_assignment(self, tank_id: str, assignment: TankAssignment):
        """Add or update a tank assignment
        
        Args:
            tank_id: Tank ID
            assignment: Tank assignment
        """
        self.assignments[tank_id] = assignment
    
    def get_assignment(self, tank_id: str) -> Optional[TankAssignment]:
        """Get assignment for a tank"""
        return self.assignments.get(tank_id)
    
    def remove_assignment(self, tank_id: str):
        """Remove assignment for a tank"""
        if tank_id in self.assignments:
            del self.assignments[tank_id]
    
    def get_total_loaded(self) -> float:
        """Calculate total quantity loaded"""
        return sum(assignment.quantity_loaded for assignment in self.assignments.values())
    
    def get_cargo_total_loaded(self, cargo_unique_id: str) -> float:
        """Get total loaded quantity for a specific cargo"""
        total = 0.0
        for assignment in self.assignments.values():
            if assignment.cargo.unique_id == cargo_unique_id:
                total += assignment.quantity_loaded
        return total
    
    def get_remaining_cargos(self, fixed_assignments: Optional[Dict[str, TankAssignment]] = None) -> List[Cargo]:
        """Get list of cargos that still have remaining quantity to load
        
        Args:
            fixed_assignments: Optional dict of fixed assignments to consider
            
        Returns:
            List of cargos with remaining quantity > 0.001
        """
        remaining_cargos = []
        fixed_assignments = fixed_assignments or {}
        
        for cargo in self.cargo_requests:
            # Calculate total loaded including fixed assignments
            total_loaded = self.get_cargo_total_loaded(cargo.unique_id)
            
            # Add fixed assignments that are not in plan yet
            for tank_id, assignment in fixed_assignments.items():
                if assignment.cargo.unique_id == cargo.unique_id:
                    total_loaded += assignment.quantity_loaded
            
            remaining = cargo.quantity - total_loaded
            if remaining > 0.001:
                # Create a copy of cargo with adjusted quantity
                from models.cargo import Cargo, Receiver
                remaining_cargo = Cargo(
                    cargo_type=cargo.cargo_type,
                    quantity=remaining,
                    receivers=[Receiver(name=r.name) for r in cargo.receivers],
                    unique_id=cargo.unique_id,
                    is_mandatory=cargo.is_mandatory,
                    ton=cargo.ton,
                    density=cargo.density
                )
                remaining_cargos.append(remaining_cargo)
        
        return remaining_cargos
    
    def get_remaining_tanks(self, ship, fixed_assignments: Optional[Dict[str, TankAssignment]] = None, 
                           excluded_tanks: Optional[set] = None) -> List:
        """Get list of tanks that are not assigned (excluding only fixed assignments)
        
        Args:
            ship: Ship object with tanks
            fixed_assignments: Optional dict of fixed assignments to exclude
            excluded_tanks: Optional set of excluded tank IDs
            
        Returns:
            List of Tank objects that are available for planning
            
        Note:
            Only fixed assignments are excluded. Algorithm results (non-fixed assignments)
            are NOT excluded, so that "Plan Remaining Cargos" can be called multiple times
            and will recalculate available tanks correctly.
        """
        fixed_assignments = fixed_assignments or {}
        excluded_tanks = excluded_tanks or set()
        
        remaining_tanks = []
        # Only exclude fixed tank IDs, not algorithm results
        fixed_tank_ids = set(fixed_assignments.keys())
        
        for tank in ship.tanks:
            # Exclude only fixed tanks and excluded tanks
            # Algorithm results (non-fixed assignments) are NOT excluded
            if tank.id not in fixed_tank_ids and tank.id not in excluded_tanks:
                remaining_tanks.append(tank)
        
        return remaining_tanks
    
    def to_dict(self) -> dict:
        """Convert plan to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'plan_name': self.plan_name,
            'ship_name': self.ship_name,
            'ship_profile_id': self.ship_profile_id,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'notes': self.notes,
            'cargo_requests': [cargo.to_dict() for cargo in self.cargo_requests],
            'assignments': {
                tank_id: assignment.to_dict() 
                for tank_id, assignment in self.assignments.items()
            },
            'excluded_tanks': list(self.excluded_tanks) if self.excluded_tanks else []
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StowagePlan':
        """Create StowagePlan from dictionary"""
        cargo_requests = [Cargo.from_dict(c_data) for c_data in data.get('cargo_requests', [])]
        
        assignments = {}
        for tank_id, assignment_data in data.get('assignments', {}).items():
            assignments[tank_id] = TankAssignment.from_dict(assignment_data)
        
        created_date = None
        if data.get('created_date'):
            created_date = datetime.fromisoformat(data['created_date'])
        
        # Load excluded tanks (backward compatible - if not present, use empty list)
        excluded_tanks = data.get('excluded_tanks', [])
        if excluded_tanks is None:
            excluded_tanks = []
        
        return cls(
            id=data.get('id', ''),
            plan_name=data.get('plan_name', ''),
            ship_name=data['ship_name'],
            ship_profile_id=data['ship_profile_id'],
            created_date=created_date,
            notes=data.get('notes', ''),
            cargo_requests=cargo_requests,
            assignments=assignments,
            excluded_tanks=excluded_tanks
        )

