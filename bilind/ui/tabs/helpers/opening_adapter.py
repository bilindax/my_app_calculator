"""
Opening Adapter - Unified access to Opening (dict or dataclass)
================================================================
This adapter provides a unified interface to access door/window data,
whether it's stored as a dict or a dataclass object.

Usage:
    door = OpeningAdapter(door_dict_or_object)
    print(door.name)
    print(door.width, door.height)
    print(door.room_quantity('غرفة نوم 1'))  # Per-room qty
"""

from typing import Any, Dict, List, Optional, Union


class OpeningAdapter:
    """
    Unified adapter for Opening objects (doors/windows).
    
    Provides consistent access to opening properties regardless of
    whether the underlying data is a dict or a dataclass.
    
    Example:
        >>> door = OpeningAdapter({'name': 'D1', 'w': 0.9, 'h': 2.1, 'qty': 2})
        >>> door.name
        'D1'
        >>> door.area_each
        1.89
    """
    
    def __init__(self, opening: Union[Dict, Any]):
        """
        Initialize adapter with an opening object.
        
        Args:
            opening: Either a dict or an Opening dataclass instance
        """
        self._opening = opening
        self._is_dict = isinstance(opening, dict)
    
    @property
    def raw(self) -> Union[Dict, Any]:
        """Get the underlying raw opening object."""
        return self._opening
    
    @property
    def is_dict(self) -> bool:
        """Check if underlying data is a dict."""
        return self._is_dict
    
    # === Basic Properties ===
    
    @property
    def name(self) -> str:
        """Opening name (e.g., 'D1', 'W2')."""
        return self._get('name', '')
    
    @name.setter
    def name(self, value: str):
        self._set('name', value)
    
    @property
    def layer(self) -> str:
        """AutoCAD layer name."""
        return self._get('layer', '')
    
    @layer.setter
    def layer(self, value: str):
        self._set('layer', value)
    
    @property
    def opening_type(self) -> str:
        """Type: 'DOOR' or 'WINDOW'."""
        return self._get('opening_type', 'DOOR')
    
    @property
    def material_type(self) -> str:
        """Material type (e.g., 'خشب', 'ألمنيوم'). Also checks 'type' key."""
        val = self._get('material_type', None)
        if val is None:
            val = self._get('type', 'قياسي')
        return val or 'قياسي'
    
    @material_type.setter
    def material_type(self, value: str):
        self._set('material_type', value)
        self._set('type', value)  # Keep both in sync
    
    # === Dimensions ===
    
    @property
    def width(self) -> float:
        """Width in meters (supports 'w' and 'width' keys)."""
        val = self._get('w', None)
        if val is None:
            val = self._get('width', 0.0)
        return float(val or 0.0)
    
    @width.setter
    def width(self, value: float):
        self._set('w', float(value))
        self._set('width', float(value))
    
    @property
    def height(self) -> float:
        """Height in meters (supports 'h' and 'height' keys)."""
        val = self._get('h', None)
        if val is None:
            val = self._get('height', 0.0)
        return float(val or 0.0)
    
    @height.setter
    def height(self, value: float):
        self._set('h', float(value))
        self._set('height', float(value))
    
    @property
    def placement_height(self) -> float:
        """Height from floor to opening sill (meters)."""
        val = self._get('placement_height', None)
        if val is None:
            # Default: 1.0m for windows, 0.0m for doors
            return 1.0 if self.opening_type == 'WINDOW' else 0.0
        return float(val)
    
    @placement_height.setter
    def placement_height(self, value: float):
        self._set('placement_height', float(value))
    
    # === Quantity ===
    
    @property
    def qty(self) -> int:
        """Total quantity in project (supports 'qty' and 'quantity' keys)."""
        val = self._get('qty', None)
        if val is None:
            val = self._get('quantity', 1)
        return int(val or 1)
    
    @qty.setter
    def qty(self, value: int):
        self._set('qty', int(value))
        self._set('quantity', int(value))
    
    @property
    def room_quantities(self) -> Dict[str, int]:
        """Per-room quantities: {'غرفة نوم 1': 2, 'صالة': 1}."""
        return self._get('room_quantities', {}) or {}
    
    @room_quantities.setter
    def room_quantities(self, value: Dict[str, int]):
        self._set('room_quantities', dict(value))
    
    def room_quantity(self, room_name: str) -> int:
        """Get quantity for a specific room."""
        return self.room_quantities.get(room_name, 1)
    
    def qty_for_room(self, room_name: str) -> int:
        """Alias for room_quantity - get quantity for a specific room."""
        return self.room_quantity(room_name)
    
    def set_room_quantity(self, room_name: str, qty: int) -> None:
        """Set quantity for a specific room."""
        rq = self.room_quantities
        rq[room_name] = int(qty)
        self.room_quantities = rq
    
    # === Room Assignment ===
    
    @property
    def assigned_rooms(self) -> List[str]:
        """List of room names this opening is assigned to."""
        return self._get('assigned_rooms', []) or []
    
    @assigned_rooms.setter
    def assigned_rooms(self, value: List[str]):
        self._set('assigned_rooms', list(value))
    
    def is_assigned_to(self, room_name: str) -> bool:
        """Check if opening is assigned to a specific room."""
        return room_name in self.assigned_rooms
    
    def assign_to_room(self, room_name: str, qty: int = 1) -> None:
        """Assign opening to a room with specified quantity."""
        rooms = self.assigned_rooms
        if room_name not in rooms:
            rooms.append(room_name)
            self.assigned_rooms = rooms
        self.set_room_quantity(room_name, qty)
    
    def unassign_from_room(self, room_name: str) -> None:
        """Remove assignment from a room."""
        rooms = self.assigned_rooms
        if room_name in rooms:
            rooms.remove(room_name)
            self.assigned_rooms = rooms
        # Remove from room_quantities too
        rq = self.room_quantities
        if room_name in rq:
            del rq[room_name]
            self.room_quantities = rq
    
    # === Computed Properties ===
    
    @property
    def area_each(self) -> float:
        """Area of one opening in m²."""
        return self.width * self.height
    
    @property
    def area_total(self) -> float:
        """Total area for all quantities."""
        return self.area_each * self.qty
    
    def area_for_room(self, room_name: str) -> float:
        """Total area for openings in a specific room."""
        return self.area_each * self.room_quantity(room_name)
    
    @property
    def perimeter_each(self) -> float:
        """Perimeter of one opening in meters."""
        return 2 * (self.width + self.height)
    
    @property
    def perimeter_total(self) -> float:
        """Total perimeter for all quantities."""
        return self.perimeter_each * self.qty
    
    @property
    def is_shared(self) -> bool:
        """Whether opening is assigned to multiple rooms."""
        return len(self.assigned_rooms) > 1
    
    # === Weight (Doors) ===
    
    @property
    def weight_each(self) -> float:
        """Weight per door in kg."""
        val = self._get('weight_each', None)
        if val is None:
            val = self._get('weight', 0.0)
        return float(val or 0.0)
    
    @weight_each.setter
    def weight_each(self, value: float):
        self._set('weight_each', float(value))
        self._set('weight', float(value))
    
    @property
    def weight_total(self) -> float:
        """Total weight for all doors."""
        return self.weight_each * self.qty
    
    # === Helper Methods ===
    
    def _get(self, key: str, default: Any = None) -> Any:
        """Get a value from the opening object."""
        if self._is_dict:
            return self._opening.get(key, default)
        return getattr(self._opening, key, default)
    
    def _set(self, key: str, value: Any) -> None:
        """Set a value on the opening object."""
        if self._is_dict:
            self._opening[key] = value
        else:
            try:
                setattr(self._opening, key, value)
            except AttributeError:
                pass  # Dataclass may have frozen fields
    
    def get(self, key: str, default: Any = None) -> Any:
        """Public getter for arbitrary attributes."""
        return self._get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Public setter for arbitrary attributes."""
        self._set(key, value)
    
    def to_dict(self) -> Dict:
        """Convert opening to dictionary representation."""
        return {
            'name': self.name,
            'layer': self.layer,
            'opening_type': self.opening_type,
            'type': self.material_type,
            'w': self.width,
            'h': self.height,
            'qty': self.qty,
            'placement_height': self.placement_height,
            'weight_each': self.weight_each,
            'assigned_rooms': self.assigned_rooms,
            'room_quantities': self.room_quantities,
        }
    
    def __repr__(self) -> str:
        return f"OpeningAdapter({self.name!r}, {self.width}×{self.height}m, qty={self.qty})"
