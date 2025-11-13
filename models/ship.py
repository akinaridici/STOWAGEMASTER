"""Ship and Tank model classes"""

from dataclasses import dataclass
from typing import List, Tuple
import uuid


@dataclass
class Tank:
    """Represents a single tank on a ship"""
    id: str
    name: str
    volume: float  # Volume in m³ or tons
    
    def __post_init__(self):
        """Generate ID if not provided"""
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> dict:
        """Convert tank to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'volume': self.volume
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Tank':
        """Create Tank from dictionary"""
        return cls(
            id=data.get('id', ''),
            name=data['name'],
            volume=data['volume']
        )


@dataclass
class Ship:
    """Represents a ship with multiple tanks"""
    name: str
    tanks: List[Tank]
    id: str = None
    
    def __post_init__(self):
        """Generate ID if not provided"""
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def get_total_capacity(self) -> float:
        """Calculate total capacity of all tanks"""
        return sum(tank.volume for tank in self.tanks)
    
    def get_tank_by_id(self, tank_id: str) -> Tank:
        """Get tank by its ID"""
        for tank in self.tanks:
            if tank.id == tank_id:
                return tank
        return None
    
    def get_tank_position_info(self, tank_id: str) -> dict:
        """Get tank position information (bow/stern, port/starboard, row number)
        
        Returns:
            dict with keys: 'row_number', 'side' ('port' or 'starboard'), 
            'position' ('bow', 'mid', 'stern')
        """
        tank = self.get_tank_by_id(tank_id)
        if not tank:
            return None
        
        # Find tank index in list
        try:
            tank_index = next(i for i, t in enumerate(self.tanks) if t.id == tank_id)
        except StopIteration:
            return None
        
        # Calculate row number: (index // 2) + 1
        row_number = (tank_index // 2) + 1
        
        # Determine side: even index = port, odd index = starboard
        side = "port" if tank_index % 2 == 0 else "starboard"
        
        # Determine position (bow/stern/mid) based on row number
        total_rows = (len(self.tanks) + 1) // 2
        if row_number == 1:
            position = "bow"
        elif row_number == total_rows:
            position = "stern"
        else:
            position = "mid"
        
        return {
            'row_number': row_number,
            'side': side,
            'position': position,
            'index': tank_index
        }
    
    def get_tank_pairs(self) -> List[Tuple[Tank, Tank]]:
        """Get all port-starboard tank pairs
        
        Returns:
            List of tuples (port_tank, starboard_tank) for same row numbers
        """
        pairs = []
        tank_groups = {}
        
        for idx, tank in enumerate(self.tanks):
            row_number = (idx // 2) + 1
            side = "port" if idx % 2 == 0 else "starboard"
            
            if row_number not in tank_groups:
                tank_groups[row_number] = {}
            tank_groups[row_number][side] = tank
        
        for row_number in sorted(tank_groups.keys()):
            if "port" in tank_groups[row_number] and "starboard" in tank_groups[row_number]:
                pairs.append((
                    tank_groups[row_number]["port"],
                    tank_groups[row_number]["starboard"]
                ))
        
        return pairs
    
    def is_bow_tank(self, tank_id: str) -> bool:
        """Check if tank is in bow section (row 1)"""
        info = self.get_tank_position_info(tank_id)
        return info and info['position'] == 'bow'
    
    def is_stern_tank(self, tank_id: str) -> bool:
        """Check if tank is in stern section (last row)"""
        info = self.get_tank_position_info(tank_id)
        return info and info['position'] == 'stern'
    
    def to_dict(self) -> dict:
        """Convert ship to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'tanks': [tank.to_dict() for tank in self.tanks]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Ship':
        """Create Ship from dictionary"""
        tanks = [Tank.from_dict(tank_data) for tank_data in data.get('tanks', [])]
        return cls(
            id=data.get('id', ''),
            name=data['name'],
            tanks=tanks
        )

