"""
Room Data Model
==============
Represents a room/space in the construction project.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from .wall import Wall


# Standard room types (Arabic) - أنواع الغرف بالعربي
ROOM_TYPES = [
    "[غير محدد]",
    "صالة",
    "غرفة نوم",
    "غرفة نوم رئيسية",
    "مطبخ",
    "حمام",
    "تواليت",
    "بلكون",
    "تراس",
    "ممر",
    "مخزن",
    "غسيل",
    "مكتب",
    "كراج",
    "مدخل",
    "غرفة خدمات",
    "غرفة ضيوف",
    "درج",
    "أخرى"
]

# English aliases for backward compatibility
ROOM_TYPES_EN = {
    "Living Room": "صالة",
    "Bedroom": "غرفة نوم",
    "Master Bedroom": "غرفة نوم رئيسية",
    "Kitchen": "مطبخ",
    "Bathroom": "حمام",
    "Toilet/WC": "تواليت",
    "Balcony": "بلكون",
    "Terrace": "تراس",
    "Hallway/Corridor": "ممر",
    "Storage/Closet": "مخزن",
    "Laundry Room": "غسيل",
    "Office/Study": "مكتب",
    "Garage": "كراج",
    "Entrance/Foyer": "مدخل",
    "Utility Room": "غرفة خدمات",
    "Guest Room": "غرفة ضيوف",
    "Stairs": "درج",
    "Other": "أخرى",
    "[Not Set]": "[غير محدد]"
}

# Standardized floor groupings (Arabic) - تصنيفات الطوابق
FLOOR_PROFILES = [
    "[غير محدد]",
    "بدروم",
    "أرضي",
    "ميزانين",
    "متكرر",
    "سطح",
    "بنتهاوس",
    "أخرى"
]

# English aliases for floor profiles
FLOOR_PROFILES_EN = {
    "Basement": "بدروم",
    "Ground": "أرضي",
    "Mezzanine": "ميزانين",
    "Typical": "متكرر",
    "Roof": "سطح",
    "Penthouse": "بنتهاوس",
    "Other": "أخرى",
    "[Not Set]": "[غير محدد]"
}


@dataclass
class Room:
    """
    Represents a room with calculated dimensions and areas.
    
    Attributes:
        name: Room identifier (e.g., "Living Room", "Room1")
        layer: AutoCAD layer name
        width: Width in meters (None if irregular shape)
        length: Length in meters (None if irregular shape)
        perimeter: Perimeter in meters
        area: Floor area in square meters
        room_type: Room category (Kitchen, Bathroom, Bedroom, etc.)
        opening_ids: List of assigned opening IDs (doors/windows)
        color: Custom display color
    """
    name: str
    layer: str
    area: float
    perimeter: float
    width: Optional[float] = None
    length: Optional[float] = None
    room_type: str = "[Not Set]"  # Room category for filtering/reporting
    opening_ids: List[str] = field(default_factory=list)
    color: Optional[str] = None  # Hex color (e.g., '#00d4ff')
    # New extended fields
    wall_height: Optional[float] = None  # Single uniform wall height (non-balcony)
    ceiling_finish_area: Optional[float] = None  # Cached ceiling area (usually = area)
    wall_finish_area: Optional[float] = None  # Cached wall finish area (net of openings)
    is_balcony: bool = False  # Special case: balcony may have multiple wall heights
    wall_segments: List[Dict[str, float]] = field(default_factory=list)  # For balcony: [{'length': L, 'height': H}, ...]
    ceramic_area: Optional[float] = None  # Total ceramic coverage inside room (deduction for paint)
    # NEW multi-floor support
    floor: int = 0  # Building level (0=Ground, 1=First, etc.)
    floor_profile: str = "[Not Set]"  # Ground / Typical / Roof grouping label
    walls: List[Wall] = field(default_factory=list)  # Explicit wall segments
    
    def __post_init__(self):
        """Validate data after initialization."""
        if self.area < 0:
            raise ValueError(f"Room area cannot be negative: {self.area}")
        if self.perimeter < 0:
            raise ValueError(f"Room perimeter cannot be negative: {self.perimeter}")
        if self.width is not None and self.width < 0:
            raise ValueError(f"Room width cannot be negative: {self.width}")
        if self.length is not None and self.length < 0:
            raise ValueError(f"Room length cannot be negative: {self.length}")
            
        # Migrate legacy wall_segments to Wall objects if needed
        if self.wall_segments and not self.walls:
            for i, seg in enumerate(self.wall_segments):
                length = float(seg.get('length', 0.0) or 0.0)
                height = float(seg.get('height', 0.0) or 0.0)
                if length > 0:
                    self.walls.append(Wall(
                        name=f"Wall {i+1}",
                        layer=self.layer,
                        length=length,
                        height=height
                    ))
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for backward compatibility.
        
        Returns:
            Dictionary representation compatible with old code.
        """
        return {
            'name': self.name,
            'layer': self.layer,
            'w': self.width,
            'l': self.length,
            'perim': self.perimeter,
            'area': self.area,
            'room_type': self.room_type,
            'opening_ids': self.opening_ids.copy(),
            'color': self.color,
            'wall_height': self.wall_height,
            'ceiling_finish_area': self.ceiling_finish_area,
            'wall_finish_area': self.wall_finish_area,
            'is_balcony': self.is_balcony,
            'wall_segments': [seg.copy() for seg in self.wall_segments],
            'ceramic_area': self.ceramic_area,
            'floor': self.floor,
            'floor_profile': self.floor_profile,
            'walls': [w.to_dict() for w in self.walls]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Room':
        """
        Create Room instance from dictionary.
        
        Args:
            data: Dictionary with room data (legacy format)
            
        Returns:
            Room instance
        """
        return cls(
            name=data.get('name', 'Room'),
            layer=data.get('layer', ''),
            width=data.get('w'),
            length=data.get('l'),
            perimeter=data.get('perim', 0.0),
            area=data.get('area', 0.0),
            room_type=data.get('room_type', '[Not Set]'),
            opening_ids=data.get('opening_ids', []),
            color=data.get('color'),
            wall_height=data.get('wall_height'),
            ceiling_finish_area=data.get('ceiling_finish_area'),
            wall_finish_area=data.get('wall_finish_area'),
            is_balcony=data.get('is_balcony', False),
            wall_segments=data.get('wall_segments', []) or [],
            ceramic_area=data.get('ceramic_area'),
            floor=int(data.get('floor', 0) or 0),
            floor_profile=data.get('floor_profile', data.get('level_group', '[Not Set]')) or '[Not Set]',
            walls=[Wall.from_dict(w) for w in data.get('walls', [])] or []
        )
    
    def calculate_wall_area(self, height: float) -> float:
        """Calculate gross wall area for a uniform height room (perimeter × height)."""
        if height < 0:
            raise ValueError(f"Wall height cannot be negative: {height}")
        return self.perimeter * height

    def calculate_segment_wall_area(self) -> float:
        """Calculate gross wall area from segment list (sum length × height)."""
        total = 0.0
        for seg in self.wall_segments:
            length = float(seg.get('length', 0.0) or 0.0)
            height = float(seg.get('height', 0.0) or 0.0)
            if length > 0 and height > 0:
                total += length * height
        return total

    def update_finish_areas(self, openings: List['Opening']) -> None:
        """Compute and cache wall & ceiling finish areas (net of openings) and finishes."""
        # 1. Basic Areas
        self.ceiling_finish_area = self.area
        
        # 2. Gross Wall Area
        if self.walls:
            gross_walls = sum(w.gross_area for w in self.walls if w.gross_area is not None)
        elif self.wall_segments:
            gross_walls = self.calculate_segment_wall_area()
        elif self.wall_height:
            gross_walls = self.calculate_wall_area(self.wall_height)
        else:
            gross_walls = 0.0
            
        # 3. Opening Deduction
        opening_total = self.get_opening_total_area(openings)
        self.wall_finish_area = max(0.0, gross_walls - opening_total)
        
        # 4. Ceramic Calculation
        ceramic_wall = 0.0
        ceramic_floor = 0.0
        ceramic_ceiling = 0.0
        
        # Aggregate from walls if available
        if self.walls:
            for w in self.walls:
                if w.ceramic_area > 0:
                    ceramic_wall += w.ceramic_area
        
        # Ceramic aggregation removed - use UnifiedCalculator.calculate_ceramic_by_room() instead
        # Legacy ceramic_area/ceramic_breakdown fields deprecated
    
    def get_opening_total_area(self, openings: List['Opening']) -> float:
        """
        Calculate total area of assigned openings.
        Checks both room.opening_ids AND opening.assigned_rooms.
        
        Args:
            openings: List of all available openings
            
        Returns:
            Total area of openings assigned to this room
        """
        total = 0.0
        for op in openings:
            is_assigned = False
            if isinstance(op, dict):
                op_name = op.get('name')
                assigned = op.get('assigned_rooms', [])
                area = op.get('area', 0.0)
            else:
                op_name = getattr(op, 'name', None)
                assigned = getattr(op, 'assigned_rooms', [])
                area = getattr(op, 'area', 0.0)
            assigned = assigned or []
            
            # Check 1: ID in room.opening_ids
            if op_name and op_name in self.opening_ids:
                is_assigned = True
            
            # Check 2: Room name in opening.assigned_rooms
            if not is_assigned:
                if assigned and self.name in assigned:
                    is_assigned = True
            
            if is_assigned:
                total += float(area or 0.0)
                
        return total
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        dims = f"{self.width}×{self.length}m" if self.width and self.length else f"{self.area:.2f}m²"
        openings = f", {len(self.opening_ids)} openings" if self.opening_ids else ""
        extra = ''
        if self.wall_height:
            extra += f", H={self.wall_height:.2f}"
        if self.is_balcony and self.wall_segments:
            extra += f", segments={len(self.wall_segments)}"
        return f"Room(floor={self.floor}, '{self.name}', {dims}{openings}{extra})"
