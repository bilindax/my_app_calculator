"""
Finish Item Data Model
======================
Represents finish items (plaster, paint, tiles, ceramic zones).
"""

from dataclasses import dataclass
from typing import Dict, Any, Literal, Optional


@dataclass
class FinishItem:
    """
    Represents a finish item with description and area.
    
    Attributes:
        description: Item description (e.g., "Room1", "Walls: Room1")
        area: Area in square meters (can be negative for deductions)
        finish_type: Type of finish ('plaster', 'paint', 'tiles')
        waste_percentage: Waste percentage for this item (optional, uses project default if None)
    """
    description: str
    area: float
    finish_type: Literal['plaster', 'paint', 'tiles']
    waste_percentage: float = None  # None means use project default
    
    def __post_init__(self):
        """Validate finish type."""
        valid_types = ['plaster', 'paint', 'tiles']
        if self.finish_type not in valid_types:
            raise ValueError(f"Invalid finish type: {self.finish_type}. Must be one of {valid_types}")
    
    @property
    def is_deduction(self) -> bool:
        """Check if this is a deduction (negative area)."""
        return self.area < 0
    
    @property
    def absolute_area(self) -> float:
        """Get absolute value of area."""
        return abs(self.area)
    
    def calculate_area_with_waste(self, default_waste: float = 0.0) -> float:
        """
        Calculate area including waste percentage.
        
        Args:
            default_waste: Default waste percentage if not set on item
            
        Returns:
            Area with waste added (or subtracted for negative areas)
        """
        waste = self.waste_percentage if self.waste_percentage is not None else default_waste
        multiplier = 1.0 + (waste / 100.0)
        return self.area * multiplier
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for backward compatibility.
        
        Returns:
            Dictionary representation compatible with old code.
        """
        result = {
            'desc': self.description,
            'area': self.area
        }
        if self.waste_percentage is not None:
            result['waste_pct'] = self.waste_percentage
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], finish_type: str) -> 'FinishItem':
        """
        Create FinishItem instance from dictionary.
        
        Args:
            data: Dictionary with finish data (legacy format)
            finish_type: Type of finish
            
        Returns:
            FinishItem instance
        """
        return cls(
            description=data.get('desc', ''),
            area=data.get('area', 0.0),
            finish_type=finish_type,
            waste_percentage=data.get('waste_pct')
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        sign = "-" if self.is_deduction else "+"
        return f"FinishItem({self.finish_type}, '{self.description}', {sign}{self.absolute_area:.2f}m²)"


@dataclass
class CeramicZone:
    """
    Represents a ceramic tile zone in kitchens/bathrooms.
    
    SIMPLIFIED USAGE:
        # For floor tiles - just use area:
        zone = CeramicZone.for_floor(area=12.0, room_name="Bathroom")
        
        # For wall tiles - use perimeter and height:
        zone = CeramicZone.for_wall(perimeter=10.0, height=2.5, room_name="Kitchen")
        
        # Or with all parameters:
        zone = CeramicZone(perimeter=10.0, height=2.5, category='Kitchen')
    
    Attributes:
        name: Zone name (auto-generated if not provided)
        category: Category ('Kitchen', 'Bathroom', 'Other')
        perimeter: Wall perimeter in meters (can be 1.0 for floor tiles using area)
        height: Tile height in meters (can be 1.0 for floor tiles using area)
        surface_type: Surface type ('floor' or 'wall') for adhesive calculation
        notes: Additional notes
    """
    # Required for walls, but factory methods handle this for floors
    perimeter: float = 1.0  # Default for floor tiles using effective_area
    height: float = 1.0     # Default for floor tiles using effective_area
    # Optional fields with smart defaults
    name: str = ""
    category: Literal['Kitchen', 'Bathroom', 'Other'] = 'Other'
    surface_type: Literal['floor', 'wall'] = 'wall'
    # Start height from floor for wall ceramic (m). Defaults to 0.0 (from floor).
    start_height: float = 0.0
    # Effective area after deductions (m²). None means use perimeter × height.
    effective_area: Optional[float] = None
    # Optional explicit room linkage for accurate per-room deductions
    room_name: Optional[str] = None
    wall_name: Optional[str] = None  # Optional wall binding for per-wall visualization
    notes: str = ""
    
    # Adhesive and grout consumption rates (kg/m²)
    ADHESIVE_RATES = {
        'floor': 5.0,    # 8mm notched trowel for floor tiles
        'wall': 3.0,     # 6mm notched trowel for wall tiles
        'ceiling': 3.0   # Treat ceiling like wall for adhesive estimation
    }
    GROUT_RATE = 0.5  # kg/m² (average for 2-3mm joints)
    
    def __post_init__(self):
        """Validate data and auto-generate name if needed."""
        # Allow 0 perimeter/height for manual area input or floor tiles
        if self.effective_area is None:
            if self.perimeter <= 0:
                raise ValueError("Perimeter must be positive")
            if self.height <= 0:
                raise ValueError("Height must be positive")
        if self.surface_type not in self.ADHESIVE_RATES:
            raise ValueError(f"Invalid surface type: {self.surface_type}")
        if self.surface_type not in self.ADHESIVE_RATES:
            raise ValueError(f"Invalid surface type: {self.surface_type}")
        
        # Auto-generate name if not provided
        if not self.name:
            surface_ar = "أرضية" if self.surface_type == 'floor' else "حائط"
            room_part = f" - {self.room_name}" if self.room_name else ""
            self.name = f"سيراميك {surface_ar}{room_part}"
    
    @classmethod
    def for_floor(cls, area: float, room_name: str = None, 
                  category: Literal['Kitchen', 'Bathroom', 'Other'] = 'Other',
                  name: str = "", notes: str = "") -> 'CeramicZone':
        """
        Create a floor ceramic zone with just the area.
        
        Args:
            area: Floor area in m²
            room_name: Associated room name
            category: 'Kitchen', 'Bathroom', or 'Other'
            name: Optional custom name
            notes: Additional notes
            
        Returns:
            CeramicZone configured for floor tiles
        """
        return cls(
            perimeter=1.0,  # Dummy value
            height=1.0,     # Dummy value
            name=name,
            category=category,
            surface_type='floor',
            effective_area=area,
            room_name=room_name,
            notes=notes
        )
    
    @classmethod
    def for_wall(cls, perimeter: float, height: float, room_name: str = None,
                 category: Literal['Kitchen', 'Bathroom', 'Other'] = 'Other',
                 start_height: float = 0.0, name: str = "", notes: str = "") -> 'CeramicZone':
        """
        Create a wall ceramic zone.
        
        Args:
            perimeter: Wall perimeter in meters
            height: Tile height from start_height
            room_name: Associated room name
            category: 'Kitchen', 'Bathroom', or 'Other'
            start_height: Height from floor where tiles start (default 0)
            name: Optional custom name
            notes: Additional notes
            
        Returns:
            CeramicZone configured for wall tiles
        """
        return cls(
            perimeter=perimeter,
            height=height,
            name=name,
            category=category,
            surface_type='wall',
            start_height=start_height,
            room_name=room_name,
            notes=notes
        )
    
    @property
    def area(self) -> float:
        """Calculate ceramic area (perimeter × height)."""
        if self.effective_area is not None:
            return self.effective_area
        return self.perimeter * self.height
    
    @property
    def adhesive_kg(self) -> float:
        """Calculate adhesive quantity in kg based on surface type."""
        return self.area * self.ADHESIVE_RATES[self.surface_type]
    
    @property
    def grout_kg(self) -> float:
        """Calculate grout quantity in kg."""
        return self.area * self.GROUT_RATE
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for backward compatibility.
        
        Returns:
            Dictionary representation compatible with old code.
        """
        return {
            'name': self.name,
            'category': self.category,
            'perimeter': self.perimeter,
            'height': self.height,
            'surface_type': self.surface_type,
            'start_height': self.start_height,
            'effective_area': self.effective_area,
            'room_name': self.room_name,
            'wall_name': self.wall_name,
            'area': self.area,
            'adhesive_kg': self.adhesive_kg,
            'grout_kg': self.grout_kg,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CeramicZone':
        """
        Create CeramicZone instance from dictionary.
        
        Args:
            data: Dictionary with ceramic zone data (legacy format)
            
        Returns:
            CeramicZone instance
        """
        return cls(
            name=data.get('name', ''),
            category=data.get('category', 'Other'),
            perimeter=data.get('perimeter', 0.0),
            height=data.get('height', 0.0),
            surface_type=data.get('surface_type', 'wall'),
            start_height=data.get('start_height', 0.0),
            effective_area=data.get('effective_area', None),
            room_name=data.get('room_name'),
            wall_name=data.get('wall_name'),
            notes=data.get('notes', '')
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"CeramicZone('{self.name}', {self.category}, {self.surface_type}, {self.area:.2f}m²)"
