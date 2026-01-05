"""
Opening Data Model
=================
Represents doors and windows in the construction project.
"""

from dataclasses import dataclass
from typing import Dict, Any, Literal, List, Optional


@dataclass
class Opening:
    """
    Represents a door or window with calculated properties.
    
    SIMPLIFIED USAGE:
        # Create a door with minimal info:
        door = Opening(name="D1", opening_type='DOOR', width=0.9, height=2.1)
        
        # Create a window:
        window = Opening(name="W1", opening_type='WINDOW', width=1.5, height=1.2)
        
        # With full details:
        door = Opening(name="D2", opening_type='DOOR', material_type='خشب', 
                       width=1.0, height=2.2, quantity=2)
    
    Attributes:
        name: Opening identifier (e.g., "D1", "W2")
        opening_type: 'DOOR' or 'WINDOW'
        width: Width in meters
        height: Height in meters
        material_type: Material (e.g., 'Wood', 'Aluminum') - optional, defaults to 'قياسي'
        layer: AutoCAD layer name
        quantity: Number of identical openings
        placement_height: Height from floor to opening sill (meters) - default 1.0m for windows, 0.0m for doors
        host_wall: Name of the wall this opening is associated with (optional)
    """
    name: str
    opening_type: Literal['DOOR', 'WINDOW']
    width: float
    height: float
    material_type: str = "قياسي"  # Default to "Standard" in Arabic
    layer: str = ""
    quantity: int = 1
    placement_height: float = None  # Will be auto-set in __post_init__
    host_wall: str = None  # Name of associated wall
    # Shared assignment support
    assigned_rooms: Optional[List[str]] = None  # Rooms this opening belongs to
    share_mode: Optional[Literal['single', 'split', 'custom']] = None  # How to deduct across rooms
    room_shares: Optional[Dict[str, float]] = None  # Per-room share overrides (sum<=1.0)
    room_quantities: Optional[Dict[str, int]] = None  # Per-room quantity (e.g., {'غرفة نوم': 2, 'صالة': 1})
    
    def __post_init__(self):
        """Validate and calculate derived fields."""
        if self.width <= 0:
            raise ValueError(f"Opening width must be positive: {self.width}")
        if self.height <= 0:
            raise ValueError(f"Opening height must be positive: {self.height}")
        if self.quantity < 1:
            raise ValueError(f"Opening quantity must be at least 1: {self.quantity}")
        
        # Auto-set placement_height if not provided
        if self.placement_height is None:
            # Default: 1.0m for windows (sill height), 0.0m for doors (floor level)
            self.placement_height = 1.0 if self.opening_type == 'WINDOW' else 0.0
    
    @property
    def perimeter_each(self) -> float:
        """Perimeter of one opening in meters."""
        return 2 * (self.width + self.height)
    
    @property
    def perimeter(self) -> float:
        """Total perimeter for all quantities."""
        return self.perimeter_each * self.quantity
    
    @property
    def area_each(self) -> float:
        """Area of one opening in m²."""
        return self.width * self.height
    
    @property
    def area(self) -> float:
        """Total area for all quantities."""
        return self.area_each * self.quantity
    
    @property
    def stone_linear(self) -> float:
        """Linear meters for stone surrounds (total perimeter)."""
        return self.perimeter
    
    def set_weight(self, weight_per_unit: float) -> float:
        """
        Set and return total weight for doors.
        
        Args:
            weight_per_unit: Weight per door in kg
            
        Returns:
            Total weight for all doors
        """
        if self.opening_type != 'DOOR':
            return 0.0
        return weight_per_unit * self.quantity
    
    def calculate_glass_area(self, glass_percentage: float = 0.85) -> float:
        """
        Calculate glass area for windows.
        
        Args:
            glass_percentage: Percentage of opening that is glass (default 85%)
            
        Returns:
            Total glass area for all windows
        """
        if self.opening_type != 'WINDOW':
            return 0.0
        return self.area * glass_percentage
    
    def to_dict(self, weight: float = 0.0) -> Dict[str, Any]:
        """
        Convert to dictionary for backward compatibility.
        
        Args:
            weight: Weight per unit (for doors)
            
        Returns:
            Dictionary representation compatible with old code.
        """
        result = {
            'name': self.name,
            'opening_type': self.opening_type,  # Include for proper type identification
            'type': self.material_type,
            'material_type': self.material_type,  # Include both for compatibility
            'layer': self.layer,
            'w': self.width,
            'h': self.height,
            'width': self.width,  # Include both for compatibility
            'height': self.height,  # Include both for compatibility
            'qty': self.quantity,
            'quantity': self.quantity,  # Include both for compatibility
            'placement_height': self.placement_height,
            'perim_each': self.perimeter_each,
            'perim': self.perimeter,
            'area_each': self.area_each,
            'area': self.area,
            'stone': self.stone_linear,
            'weight_each': weight if self.opening_type == 'DOOR' else 0.0,
            'weight': weight * self.quantity if self.opening_type == 'DOOR' else 0.0,
        }
        
        if self.host_wall:
            result['host_wall'] = self.host_wall
        # Shared options
        if self.assigned_rooms:
            result['assigned_rooms'] = list(self.assigned_rooms)
        if self.share_mode:
            result['share_mode'] = self.share_mode
        if self.room_shares:
            result['room_shares'] = dict(self.room_shares)

        if self.room_quantities:
            # Persist per-room quantities (critical for Room Manager edits)
            result['room_quantities'] = dict(self.room_quantities)
        
        if self.opening_type == 'WINDOW':
            glass_area = self.calculate_glass_area()
            result['glass_each'] = glass_area / self.quantity
            result['glass'] = glass_area
        else:
            result['glass_each'] = 0.0
            result['glass'] = 0.0
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Opening':
        """
        Create Opening instance from dictionary.
        
        Args:
            data: Dictionary with opening data (legacy format)
            
        Returns:
            Opening instance
        """
        # Determine opening type from data - check 'opening_type' first, then fallback to glass heuristic
        opening_type = data.get('opening_type')
        if not opening_type:
            opening_type = 'WINDOW' if data.get('glass', 0) > 0 else 'DOOR'
        
        # Get placement_height with defaults for backward compatibility
        placement_height = data.get('placement_height')
        if placement_height is None:
            placement_height = 1.0 if opening_type == 'WINDOW' else 0.0
        
        # Get width/height - prioritize full names, fallback to short names
        width = data.get('width')
        if width is None:
            width = data.get('w', 0.0)
        height = data.get('height')
        if height is None:
            height = data.get('h', 0.0)
        quantity = data.get('quantity')
        if quantity is None:
            quantity = data.get('qty', 1)

        # Restore per-room quantities (if present)
        room_quantities_raw = data.get('room_quantities')
        room_quantities: Optional[Dict[str, int]] = None
        if isinstance(room_quantities_raw, dict) and room_quantities_raw:
            normalized: Dict[str, int] = {}
            for room_name, q in room_quantities_raw.items():
                if not room_name:
                    continue
                try:
                    normalized[str(room_name)] = max(1, int(q))
                except (TypeError, ValueError):
                    normalized[str(room_name)] = 1
            room_quantities = normalized or None
        
        return cls(
            name=data.get('name', 'Opening'),
            opening_type=opening_type,
            width=float(width or 0.0),
            height=float(height or 0.0),
            material_type=data.get('material_type') or data.get('type', 'قياسي'),
            layer=data.get('layer', ''),
            quantity=int(quantity or 1),
            placement_height=placement_height,
            host_wall=data.get('host_wall'),
            assigned_rooms=data.get('assigned_rooms'),
            share_mode=data.get('share_mode'),
            room_shares=data.get('room_shares'),
            room_quantities=room_quantities,
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        type_symbol = "🚪" if self.opening_type == 'DOOR' else "🪟"
        dims = f"{self.width:.2f}×{self.height:.2f}m"
        qty = f"×{self.quantity}" if self.quantity > 1 else ""
        return f"{type_symbol} Opening('{self.name}', {self.material_type}, {dims}{qty})"
