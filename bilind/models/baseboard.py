"""
Baseboard/Skirting Data Model
==============================
Represents baseboard (نعلات) with material calculations.
"""

from dataclasses import dataclass
from typing import Dict, Any, Literal


@dataclass
class Baseboard:
    """
    Represents a baseboard/skirting installation.
    
    Baseboards (نعلات) are installed at the base of walls where they meet the floor.
    Calculation: room perimeter - door widths
    
    Attributes:
        name: Item name (e.g., "Room1 Baseboards")
        perimeter: Total wall perimeter in meters
        door_width_deduction: Total door widths to deduct (meters)
        material_type: Type of baseboard material
        height_cm: Baseboard height in centimeters (typically 7-15cm)
    """
    name: str
    perimeter: float
    door_width_deduction: float = 0.0
    material_type: Literal['wood', 'marble', 'mdf', 'pvc'] = 'wood'
    height_cm: float = 10.0
    
    # Material costs and characteristics (can be customized)
    MATERIAL_INFO = {
        'wood': {'name_ar': 'خشب', 'density_kg_m': 2.5, 'typical_cost_m': 5.0},
        'marble': {'name_ar': 'رخام', 'density_kg_m': 8.0, 'typical_cost_m': 15.0},
        'mdf': {'name_ar': 'MDF', 'density_kg_m': 1.8, 'typical_cost_m': 3.0},
        'pvc': {'name_ar': 'PVC', 'density_kg_m': 1.5, 'typical_cost_m': 4.0}
    }
    
    def __post_init__(self):
        """Validate inputs."""
        if self.perimeter <= 0:
            raise ValueError(f"Perimeter must be positive: {self.perimeter}")
        if self.door_width_deduction < 0:
            raise ValueError(f"Door deduction cannot be negative: {self.door_width_deduction}")
        if self.door_width_deduction > self.perimeter:
            raise ValueError(f"Door deduction ({self.door_width_deduction}m) exceeds perimeter ({self.perimeter}m)")
        if self.height_cm <= 0 or self.height_cm > 30:
            raise ValueError(f"Height must be between 0-30 cm: {self.height_cm}")
        if self.material_type not in self.MATERIAL_INFO:
            raise ValueError(f"Invalid material type: {self.material_type}")
    
    @property
    def net_length_m(self) -> float:
        """Calculate net baseboard length (perimeter - doors)."""
        return max(0.0, self.perimeter - self.door_width_deduction)
    
    @property
    def area_m2(self) -> float:
        """Calculate baseboard area (length × height)."""
        height_m = self.height_cm / 100.0
        return self.net_length_m * height_m
    
    @property
    def material_info(self) -> Dict[str, Any]:
        """Get material information."""
        return self.MATERIAL_INFO.get(self.material_type, {})
    
    @property
    def arabic_material_name(self) -> str:
        """Get Arabic material name."""
        return self.material_info.get('name_ar', self.material_type)
    
    def calculate_adhesive_kg(self) -> float:
        """
        Calculate adhesive/glue quantity for installation.
        Typical consumption: 0.3 kg per linear meter
        """
        return self.net_length_m * 0.3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'perimeter': self.perimeter,
            'door_width_deduction': self.door_width_deduction,
            'material_type': self.material_type,
            'height_cm': self.height_cm,
            'net_length_m': self.net_length_m,
            'area_m2': self.area_m2,
            'adhesive_kg': self.calculate_adhesive_kg()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Baseboard':
        """Create Baseboard from dictionary."""
        return cls(
            name=data.get('name', ''),
            perimeter=data.get('perimeter', 0.0),
            door_width_deduction=data.get('door_width_deduction', 0.0),
            material_type=data.get('material_type', 'wood'),
            height_cm=data.get('height_cm', 10.0)
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Baseboard('{self.name}', {self.net_length_m:.2f}m, {self.material_type})"
