"""Cargo and Receiver model classes"""

from dataclasses import dataclass, field
from typing import List
import uuid


@dataclass
class Receiver:
    """Represents a cargo receiver"""
    name: str
    
    def to_dict(self) -> dict:
        """Convert receiver to dictionary for JSON serialization"""
        return {
            'name': self.name
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Receiver':
        """Create Receiver from dictionary"""
        return cls(name=data['name'])


@dataclass
class Cargo:
    """Represents a cargo loading request"""
    cargo_type: str
    quantity: float  # Volume in m³ (calculated from ton / density)
    receivers: List[Receiver] = field(default_factory=list)
    unique_id: str = None
    is_mandatory: bool = False
    ton: float = None  # Weight in tons
    density: float = None  # Density in ton/m³
    
    def __post_init__(self):
        """Generate ID if not provided, calculate volume if ton and density provided"""
        if not self.unique_id:
            self.unique_id = str(uuid.uuid4())
        
        # Only calculate volume if quantity is not set (0 or None) AND ton/density are provided
        # This prevents overwriting manually entered quantities
        # IMPORTANT: Only recalculate if quantity is exactly 0.0 or None
        # If quantity has any non-zero value (even very small), preserve it
        if (self.quantity is None or self.quantity == 0.0) and self.ton is not None and self.density is not None and self.density > 0:
            self.quantity = self.ton / self.density
    
    def add_receiver(self, receiver: Receiver):
        """Add a receiver to this cargo"""
        if receiver not in self.receivers:
            self.receivers.append(receiver)
    
    def get_receiver_names(self) -> str:
        """Get comma-separated receiver names"""
        if not self.receivers:
            return "Genel"
        return ", ".join([r.name for r in self.receivers])
    
    def to_dict(self) -> dict:
        """Convert cargo to dictionary for JSON serialization"""
        return {
            'unique_id': self.unique_id,
            'cargo_type': self.cargo_type,
            'quantity': self.quantity,
            'receivers': [r.to_dict() for r in self.receivers],
            'is_mandatory': self.is_mandatory,
            'ton': self.ton,
            'density': self.density
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Cargo':
        """Create Cargo from dictionary
        
        IMPORTANT: Preserves the exact quantity value from JSON.
        Only recalculates quantity if it's None or 0.0 AND ton/density are provided.
        This ensures that manually entered quantities are never overwritten.
        """
        receivers = [Receiver.from_dict(r_data) for r_data in data.get('receivers', [])]
        
        # Preserve original quantity from JSON
        # Use None if quantity is not present, so __post_init__ can decide whether to calculate
        original_quantity = data.get('quantity')
        if original_quantity is None:
            original_quantity = 0.0  # Default to 0.0 if not present
        
        cargo = cls(
            unique_id=data.get('unique_id', ''),
            cargo_type=data['cargo_type'],
            quantity=original_quantity,  # Use original quantity from JSON
            receivers=receivers,
            is_mandatory=data.get('is_mandatory', False),  # Backward compatibility
            ton=data.get('ton'),
            density=data.get('density')
        )
        
        # __post_init__ will handle quantity calculation if needed
        # It only calculates if quantity is 0 or None AND ton/density are provided
        # This preserves manually entered quantities (even if they're very small)
        
        return cargo

