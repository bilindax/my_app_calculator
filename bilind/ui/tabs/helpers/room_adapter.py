"""
Room Adapter - Unified access to Room (dict or dataclass)
==========================================================
This adapter provides a unified interface to access room data,
whether it's stored as a dict or a dataclass object.

Usage:
    room = RoomAdapter(room_dict_or_object)
    print(room.name)       # Works for both dict and dataclass
    print(room.area)
    room.walls.append(new_wall)  # Direct modification
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass


class RoomAdapter:
    """
    Unified adapter for Room objects.
    
    Provides consistent access to room properties regardless of
    whether the underlying data is a dict or a dataclass.
    
    Example:
        >>> room = RoomAdapter({'name': 'غرفة نوم 1', 'area': 15.5})
        >>> room.name
        'غرفة نوم 1'
        >>> room.area
        15.5
    """
    
    def __init__(self, room: Union[Dict, Any]):
        """
        Initialize adapter with a room object.
        
        Args:
            room: Either a dict or a Room dataclass instance
        """
        self._room = room
        self._is_dict = isinstance(room, dict)
    
    @property
    def raw(self) -> Union[Dict, Any]:
        """Get the underlying raw room object."""
        return self._room
    
    @property
    def is_dict(self) -> bool:
        """Check if underlying data is a dict."""
        return self._is_dict
    
    # === Basic Properties ===
    
    @property
    def name(self) -> str:
        """Room name."""
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
    def room_type(self) -> str:
        """Room type (e.g., 'غرفة نوم', 'مطبخ')."""
        return self._get('room_type', '[Not Set]')
    
    @room_type.setter
    def room_type(self, value: str):
        self._set('room_type', value)
    
    # === Dimensions ===
    
    @property
    def width(self) -> float:
        """Room width in meters."""
        return float(self._get('width', 0.0) or 0.0)
    
    @width.setter
    def width(self, value: float):
        self._set('width', float(value))
    
    @property
    def length(self) -> float:
        """Room length in meters."""
        return float(self._get('length', 0.0) or 0.0)
    
    @length.setter
    def length(self, value: float):
        self._set('length', float(value))
    
    @property
    def area(self) -> float:
        """Room area in m²."""
        return float(self._get('area', 0.0) or 0.0)
    
    @area.setter
    def area(self, value: float):
        self._set('area', float(value))
    
    @property
    def perimeter(self) -> float:
        """Room perimeter in meters (supports 'perim' and 'perimeter' keys)."""
        val = self._get('perim', None)
        if val is None:
            val = self._get('perimeter', 0.0)
        return float(val or 0.0)
    
    @perimeter.setter
    def perimeter(self, value: float):
        # Store in both keys for compatibility
        self._set('perim', float(value))
        if not self._is_dict:
            try:
                setattr(self._room, 'perimeter', float(value))
            except AttributeError:
                pass
    
    @property
    def wall_height(self) -> float:
        """Wall height in meters."""
        val = self._get('wall_height', None)
        return float(val) if val is not None else 3.0  # Default 3m
    
    @wall_height.setter
    def wall_height(self, value: float):
        self._set('wall_height', float(value))
    
    # === Balcony Properties ===
    
    @property
    def is_balcony(self) -> bool:
        """Whether room is a balcony/terrace."""
        return bool(self._get('is_balcony', False))
    
    @is_balcony.setter
    def is_balcony(self, value: bool):
        self._set('is_balcony', bool(value))
    
    @property
    def has_balcony(self) -> bool:
        """Whether room has a balcony attached (alias for is_balcony or separate field)."""
        # Check both 'has_balcony' and 'is_balcony' for flexibility
        val = self._get('has_balcony', None)
        if val is not None:
            return bool(val)
        return self.is_balcony
    
    @has_balcony.setter
    def has_balcony(self, value: bool):
        self._set('has_balcony', bool(value))
    
    @property
    def balcony_segments(self) -> List[float]:
        """Balcony wall segment lengths [side1, side2, side3, side4]."""
        return self._get('balcony_segments', []) or []
    
    @balcony_segments.setter
    def balcony_segments(self, value: List[float]):
        self._set('balcony_segments', list(value))
    
    # === Walls ===
    
    @property
    def walls(self) -> List:
        """List of walls associated with this room."""
        return self._get('walls', []) or []
    
    @walls.setter
    def walls(self, value: List):
        self._set('walls', list(value))
    
    # === Ceramic/Finishes ===
    
    @property
    def ceramic_breakdown(self) -> Dict:
        """Ceramic area breakdown {'wall': float, 'ceiling': float}."""
        return self._get('ceramic_breakdown', {}) or {}
    
    @ceramic_breakdown.setter
    def ceramic_breakdown(self, value: Dict):
        self._set('ceramic_breakdown', dict(value))
    
    @property
    def ceramic_zones(self) -> List:
        """List of ceramic zones in this room."""
        return self._get('ceramic_zones', []) or []
    
    @ceramic_zones.setter
    def ceramic_zones(self, value: List):
        self._set('ceramic_zones', list(value))
    
    @property
    def ceramic_area(self) -> float:
        """Total ceramic area in m²."""
        return float(self._get('ceramic_area', 0.0) or 0.0)
    
    @ceramic_area.setter
    def ceramic_area(self, value: float):
        self._set('ceramic_area', float(value))

    @property
    def plaster_area(self) -> float:
        """Total plaster area in m²."""
        return float(self._get('plaster_area', 0.0) or 0.0)
    
    @plaster_area.setter
    def plaster_area(self, value: float):
        self._set('plaster_area', float(value))

    @property
    def paint_area(self) -> float:
        """Total paint area in m²."""
        return float(self._get('paint_area', 0.0) or 0.0)
    
    @paint_area.setter
    def paint_area(self, value: float):
        self._set('paint_area', float(value))
    
    # === Computed Properties ===
    
    @property
    def walls_gross_area(self) -> float:
        """Gross wall area (perimeter × wall_height)."""
        return self.perimeter * self.wall_height
    
    @property
    def wall_count(self) -> int:
        """Number of walls."""
        return len(self.walls)
    
    # === Helper Methods ===
    
    def _get(self, key: str, default: Any = None) -> Any:
        """Get a value from the room object."""
        if self._is_dict:
            return self._room.get(key, default)
        return getattr(self._room, key, default)
    
    def _set(self, key: str, value: Any) -> None:
        """Set a value on the room object."""
        if self._is_dict:
            self._room[key] = value
        else:
            setattr(self._room, key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Public getter for arbitrary attributes."""
        return self._get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Public setter for arbitrary attributes."""
        self._set(key, value)
    
    def to_dict(self) -> Dict:
        """Convert room to dictionary representation."""
        if self._is_dict:
            return dict(self._room)
        # Convert dataclass to dict
        result = {}
        for key in ['name', 'layer', 'room_type', 'width', 'length', 'area', 
                    'perim', 'perimeter', 'wall_height', 'is_balcony', 
                    'balcony_segments', 'walls', 'ceramic_breakdown', 'ceramic_zones',
                    'ceramic_area', 'plaster_area', 'paint_area']:
            val = getattr(self._room, key, None)
            if val is not None:
                result[key] = val
        return result
    
    def __repr__(self) -> str:
        return f"RoomAdapter({self.name!r}, area={self.area:.2f}m², type={self.room_type!r})"
