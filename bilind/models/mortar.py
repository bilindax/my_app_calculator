"""
Mortar/Plaster Layer Data Model
================================
Represents plaster/mortar layers with thickness and material calculations.
"""

from dataclasses import dataclass
from typing import Dict, Any, Literal, Tuple


@dataclass
class MortarLayer:
    """
    Represents a plaster/mortar layer with material calculations.
    
    Mortar types and specifications:
    - Rough (خشنة): 20-30mm, 1:4 cement:sand ratio
    - Fine (ناعمة): 2-5mm, 1:3 cement:sand ratio  
    - Screeding (مسمار): 10-20mm, 1:5 cement:sand ratio
    
    Attributes:
        name: Layer name/description
        area: Area in square meters
        thickness_mm: Thickness in millimeters
        mortar_type: Type of mortar application
    """
    name: str
    area: float
    thickness_mm: float
    mortar_type: Literal['rough', 'fine', 'screeding']
    
    # Mix ratios (cement : sand by volume)
    MIX_RATIOS = {
        'rough': {'cement': 1, 'sand': 4},      # خشنة
        'fine': {'cement': 1, 'sand': 3},       # ناعمة
        'screeding': {'cement': 1, 'sand': 5}   # مسمار
    }
    
    # Default thicknesses (mm)
    DEFAULT_THICKNESS = {
        'rough': 25,
        'fine': 3,
        'screeding': 15
    }
    
    # Material densities
    CEMENT_DENSITY = 1440  # kg/m³ (dry bulk density)
    SAND_DENSITY = 1600    # kg/m³ (dry bulk density)
    CEMENT_BAG_WEIGHT = 50 # kg per bag
    
    def __post_init__(self):
        """Validate inputs."""
        if self.area <= 0:
            raise ValueError(f"Area must be positive: {self.area}")
        if self.thickness_mm <= 0:
            raise ValueError(f"Thickness must be positive: {self.thickness_mm}")
        if self.mortar_type not in self.MIX_RATIOS:
            raise ValueError(f"Invalid mortar type: {self.mortar_type}")
    
    @property
    def volume_m3(self) -> float:
        """Calculate total volume in cubic meters."""
        thickness_m = self.thickness_mm / 1000.0
        return self.area * thickness_m
    
    @property
    def mix_ratio(self) -> Dict[str, int]:
        """Get cement:sand ratio for this mortar type."""
        return self.MIX_RATIOS[self.mortar_type]
    
    def calculate_materials(self) -> Dict[str, float]:
        """
        Calculate sand and cement quantities.
        
        Returns:
            Dictionary with:
            - sand_m3: Sand volume in cubic meters
            - cement_kg: Cement weight in kilograms
            - cement_bags: Number of 50kg cement bags (rounded up)
            - total_volume_m3: Total mortar volume
        """
        total_parts = self.mix_ratio['cement'] + self.mix_ratio['sand']
        cement_volume = self.volume_m3 * (self.mix_ratio['cement'] / total_parts)
        sand_volume = self.volume_m3 * (self.mix_ratio['sand'] / total_parts)
        
        # Calculate weights
        cement_kg = cement_volume * self.CEMENT_DENSITY
        cement_bags = int(cement_kg / self.CEMENT_BAG_WEIGHT) + (1 if cement_kg % self.CEMENT_BAG_WEIGHT > 0 else 0)
        
        return {
            'sand_m3': sand_volume,
            'cement_kg': cement_kg,
            'cement_bags': cement_bags,
            'total_volume_m3': self.volume_m3,
            'sand_kg': sand_volume * self.SAND_DENSITY
        }
    
    def get_material_summary(self) -> str:
        """
        Get human-readable material summary.
        
        Returns:
            Formatted string with material quantities
        """
        materials = self.calculate_materials()
        return (
            f"Vol: {materials['total_volume_m3']:.3f} m³ • "
            f"Sand: {materials['sand_m3']:.2f} m³ ({materials['sand_kg']:.0f} kg) • "
            f"Cement: {materials['cement_bags']} bags ({materials['cement_kg']:.1f} kg)"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        materials = self.calculate_materials()
        return {
            'name': self.name,
            'area': self.area,
            'thickness_mm': self.thickness_mm,
            'mortar_type': self.mortar_type,
            'volume_m3': self.volume_m3,
            **materials
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MortarLayer':
        """Create MortarLayer from dictionary."""
        return cls(
            name=data.get('name', ''),
            area=data.get('area', 0.0),
            thickness_mm=data.get('thickness_mm', 25.0),
            mortar_type=data.get('mortar_type', 'rough')
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"MortarLayer('{self.name}', {self.area:.2f}m² × {self.thickness_mm}mm, {self.mortar_type})"


@dataclass 
class CeramicAdhesive:
    """
    Calculate ceramic tile adhesive and grout requirements.
    
    Adhesive consumption rates:
    - Floor tiles: 5 kg/m² (8mm notched trowel)
    - Wall tiles: 3 kg/m² (6mm notched trowel)
    
    Grout consumption: ~0.5 kg/m² (depends on joint width)
    """
    name: str
    area: float
    surface_type: Literal['floor', 'wall']
    
    # Consumption rates (kg/m²)
    ADHESIVE_RATES = {
        'floor': 5.0,  # 8mm trowel
        'wall': 3.0    # 6mm trowel
    }
    GROUT_RATE = 0.5  # kg/m² (average for 2-3mm joints)
    
    def __post_init__(self):
        """Validate inputs."""
        if self.area <= 0:
            raise ValueError(f"Area must be positive: {self.area}")
        if self.surface_type not in self.ADHESIVE_RATES:
            raise ValueError(f"Invalid surface type: {self.surface_type}")
    
    @property
    def adhesive_kg(self) -> float:
        """Calculate adhesive quantity in kg."""
        return self.area * self.ADHESIVE_RATES[self.surface_type]
    
    @property
    def grout_kg(self) -> float:
        """Calculate grout quantity in kg."""
        return self.area * self.GROUT_RATE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'area': self.area,
            'surface_type': self.surface_type,
            'adhesive_kg': self.adhesive_kg,
            'grout_kg': self.grout_kg
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CeramicAdhesive':
        """Create from dictionary."""
        return cls(
            name=data.get('name', ''),
            area=data.get('area', 0.0),
            surface_type=data.get('surface_type', 'floor')
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"CeramicAdhesive('{self.name}', {self.area:.2f}m², {self.surface_type}, {self.adhesive_kg:.1f}kg adhesive)"
