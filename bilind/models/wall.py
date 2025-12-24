"""
Wall Data Model
==============
Represents walls with gross and net areas after deductions.
Includes WallSurface for multi-surface walls (balconies, terraces).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Literal


# أنواع أسطح الجدران - Wall Surface Types
WALL_SURFACE_TYPES = [
    "دهان",           # Paint
    "سيراميك",        # Ceramic tiles
    "حجر",            # Stone
    "بدون تشطيب",     # No finish (raw concrete)
    "شباك/فتحة",      # Window/Opening (no wall area)
    "زجاج",           # Glass
    "درابزين",        # Railing/Parapet
]


@dataclass
class WallSurface:
    """
    Represents a wall segment with a specific surface finish.
    Used for balconies and spaces with multiple wall types.
    
    مثال للبلكون:
        - جدار 1: طول 3م، ارتفاع 1.2م، نوع: درابزين
        - جدار 2: طول 2م، ارتفاع 3م، نوع: دهان
        - جدار 3: طول 3م، ارتفاع 2م، نوع: شباك/فتحة
    
    Attributes:
        length: Wall segment length in meters
        height: Wall segment height in meters
        surface_type: Type of surface finish
        has_opening: Whether this segment has an opening
        opening_area: Area of opening if any
        notes: Additional notes
    """
    length: float
    height: float
    surface_type: str = "دهان"
    has_opening: bool = False
    opening_area: float = 0.0
    notes: str = ""
    
    def __post_init__(self):
        """Validate data."""
        if self.length < 0:
            raise ValueError(f"Length cannot be negative: {self.length}")
        if self.height < 0:
            raise ValueError(f"Height cannot be negative: {self.height}")
        if self.opening_area < 0:
            raise ValueError(f"Opening area cannot be negative: {self.opening_area}")
    
    @property
    def gross_area(self) -> float:
        """Calculate gross area (length × height)."""
        return self.length * self.height
    
    @property
    def net_area(self) -> float:
        """Calculate net area after opening deduction."""
        return max(0.0, self.gross_area - self.opening_area)
    
    @property
    def is_paintable(self) -> bool:
        """Check if this surface needs paint."""
        return self.surface_type == "دهان"
    
    @property
    def is_ceramic(self) -> bool:
        """Check if this surface is ceramic/tiles."""
        return self.surface_type == "سيراميك"
    
    @property
    def is_opening(self) -> bool:
        """Check if this is an opening (window/door)."""
        return self.surface_type == "شباك/فتحة" or self.has_opening
    
    @property
    def needs_plaster(self) -> bool:
        """Check if this surface needs plaster (base coat)."""
        # Plaster needed for paint and ceramic, not for openings or raw concrete
        return self.surface_type in ["دهان", "سيراميك"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'length': self.length,
            'height': self.height,
            'surface_type': self.surface_type,
            'has_opening': self.has_opening,
            'opening_area': self.opening_area,
            'gross_area': self.gross_area,
            'net_area': self.net_area,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WallSurface':
        """Create from dictionary."""
        return cls(
            length=float(data.get('length', 0) or 0),
            height=float(data.get('height', 0) or 0),
            surface_type=data.get('surface_type', 'دهان'),
            has_opening=data.get('has_opening', False),
            opening_area=float(data.get('opening_area', 0) or 0),
            notes=data.get('notes', '')
        )
    
    def __repr__(self) -> str:
        return f"WallSurface({self.length:.1f}×{self.height:.1f}م, {self.surface_type}, {self.net_area:.1f}م²)"


@dataclass
class Wall:
    """
    Represents a wall with calculated areas.
    
    Attributes:
        name: Wall identifier (e.g., "Wall1", "North Wall", "جدار 1")
        layer: AutoCAD layer name
        length: Wall length in meters
        height: Wall height in meters
        gross_area: Gross wall area (length × height)
        deduction_area: Total area to deduct (openings)
        net_area: Net wall area after deductions
        assigned_openings: List of opening IDs (doors/windows) on this wall
        surface_type: نوع السطح (دهان، سيراميك، حجر، إلخ)
        direction: اتجاه الجدار (شمال، جنوب، شرق، غرب، داخلي)
        notes: ملاحظات إضافية
    """
    name: str
    layer: str
    length: float
    height: float
    gross_area: Optional[float] = None
    deduction_area: float = 0.0
    net_area: Optional[float] = None
    assigned_openings: List[str] = field(default_factory=list)  # Opening IDs on this wall
    surface_type: str = "دهان"  # Default: Paint
    direction: str = ""  # Wall direction/orientation
    notes: str = ""  # Additional notes
    ceramic_height: float = 0.0  # Height of partial ceramic finish (m)
    ceramic_surface: str = "سيراميك"  # Ceramic finish type/label
    ceramic_area: float = 0.0  # Effective ceramic area after deductions
    
    def __post_init__(self):
        """Validate and calculate areas."""
        if self.length <= 0:
            raise ValueError(f"Wall length must be positive: {self.length}")
        if self.height <= 0:
            raise ValueError(f"Wall height must be positive: {self.height}")
        
        # Calculate gross area if not provided
        if self.gross_area is None:
            self.gross_area = self.length * self.height
        
        # Calculate net area if not provided
        if self.net_area is None:
            self.net_area = max(0.0, self.gross_area - self.deduction_area)

        # Normalize ceramic values (height + area)
        self._normalize_ceramic_segment()

    def _normalize_ceramic_segment(self):
        """Clamp ceramic height and refresh its effective area."""
        ceramic_height = float(self.ceramic_height or 0.0)
        if ceramic_height <= 0:
            self.ceramic_height = 0.0
            self.ceramic_area = 0.0
            if not self.ceramic_surface:
                self.ceramic_surface = "سيراميك"
            return

        ceramic_height = min(ceramic_height, self.height)
        self.ceramic_height = ceramic_height
        if not self.ceramic_surface:
            self.ceramic_surface = "سيراميك"

        base_area = self.length * ceramic_height
        if self.gross_area and self.gross_area > 0 and self.net_area is not None:
            ratio = max(0.0, min(1.0, self.net_area / self.gross_area))
            self.ceramic_area = base_area * ratio
        else:
            self.ceramic_area = base_area
    
    def add_deduction(self, area: float):
        """
        Add an opening deduction and recalculate net area.
        
        Args:
            area: Opening area to deduct in m²
        """
        if area < 0:
            raise ValueError(f"Deduction area cannot be negative: {area}")
        self.deduction_area += area
        self.net_area = max(0.0, self.gross_area - self.deduction_area)
        self._normalize_ceramic_segment()
    
    def reset_deductions(self):
        """Reset all deductions and recalculate net area."""
        self.deduction_area = 0.0
        self.net_area = self.gross_area
        self._normalize_ceramic_segment()
    
    def calculate_volume(self, thickness: float = 0.2) -> float:
        """
        Calculate wall volume.
        
        Args:
            thickness: Wall thickness in meters (default 0.2m = 20cm)
            
        Returns:
            Wall volume in cubic meters
        """
        if thickness <= 0:
            raise ValueError(f"Wall thickness must be positive: {thickness}")
        return self.net_area * thickness
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for backward compatibility.
        
        Returns:
            Dictionary representation compatible with old code.
        """
        return {
            'name': self.name,
            'layer': self.layer,
            'length': self.length,
            'height': self.height,
            'gross': self.gross_area,
            'deduct': self.deduction_area,
            'net': self.net_area,
            'assigned_openings': self.assigned_openings.copy() if self.assigned_openings else [],
            'surface_type': self.surface_type,
            'direction': self.direction,
            'notes': self.notes,
            'ceramic_height': self.ceramic_height,
            'ceramic_height_m': self.ceramic_height,
            'ceramic_surface': self.ceramic_surface,
            'ceramic_surface_type': self.ceramic_surface,
            'ceramic_area': self.ceramic_area
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Wall':
        """
        Create Wall instance from dictionary.
        
        Args:
            data: Dictionary with wall data (legacy format)
            
        Returns:
            Wall instance
        """
        return cls(
            name=data.get('name', 'Wall'),
            layer=data.get('layer', ''),
            length=data.get('length', 0.0),
            height=data.get('height', 0.0),
            gross_area=data.get('gross'),
            deduction_area=data.get('deduct', 0.0),
            net_area=data.get('net'),
            assigned_openings=data.get('assigned_openings', []) or [],
            surface_type=data.get('surface_type', 'دهان'),
            direction=data.get('direction', ''),
            notes=data.get('notes', ''),
            ceramic_height=float(data.get('ceramic_height', data.get('ceramic_height_m', 0.0)) or 0.0),
            ceramic_surface=data.get('ceramic_surface', data.get('ceramic_surface_type', 'سيراميك')),
            ceramic_area=float(data.get('ceramic_area', 0.0) or 0.0)
        )

    @property
    def has_partial_ceramic(self) -> bool:
        """Check if wall has a ceramic band configured."""
        return self.ceramic_height > 0
    
    @property
    def deduction_percentage(self) -> float:
        """Calculate percentage of wall area that is deducted."""
        if self.gross_area == 0:
            return 0.0
        return (self.deduction_area / self.gross_area) * 100
    
    def assign_opening(self, opening_id: str) -> bool:
        """
        Assign an opening (door/window) to this wall.
        
        Args:
            opening_id: Opening ID to assign
            
        Returns:
            True if assigned successfully, False if already assigned
        """
        if opening_id not in self.assigned_openings:
            self.assigned_openings.append(opening_id)
            return True
        return False
    
    def unassign_opening(self, opening_id: str) -> bool:
        """
        Remove an opening from this wall.
        
        Args:
            opening_id: Opening ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if opening_id in self.assigned_openings:
            self.assigned_openings.remove(opening_id)
            return True
        return False
    
    def has_opening(self, opening_id: str) -> bool:
        """Check if an opening is assigned to this wall."""
        return opening_id in self.assigned_openings
    
    def get_openings_count(self) -> int:
        """Get number of openings assigned to this wall."""
        return len(self.assigned_openings)
    
    def recalculate_deductions(self, openings: List[Dict[str, Any]]) -> float:
        """
        Recalculate deduction area based on assigned openings.
        
        Args:
            openings: List of all openings (doors + windows)
            
        Returns:
            Total deduction area
        """
        self.deduction_area = 0.0
        
        for opening in openings:
            # Get opening ID
            if isinstance(opening, dict):
                opening_id = opening.get('name', '')
                area = float(opening.get('area', 0.0) or 0.0)
            else:
                opening_id = getattr(opening, 'name', '')
                area = float(getattr(opening, 'area', 0.0) or 0.0)
            
            # Count occurrences of this opening on the wall
            count = self.assigned_openings.count(opening_id)
            if count > 0:
                self.deduction_area += area * count
        
        self.net_area = max(0.0, self.gross_area - self.deduction_area)
        self._normalize_ceramic_segment()
        return self.deduction_area
    
    @property
    def is_paintable(self) -> bool:
        """Check if this wall needs paint."""
        return self.surface_type == "دهان"
    
    @property
    def is_ceramic(self) -> bool:
        """Check if this wall has ceramic tiles."""
        return self.surface_type == "سيراميك"
    
    @property
    def needs_plaster(self) -> bool:
        """Check if this wall needs plaster (base coat)."""
        return self.surface_type in ["دهان", "سيراميك"]
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        deduct_pct = f" (-{self.deduction_percentage:.1f}%)" if self.deduction_area > 0 else ""
        return f"Wall('{self.name}', {self.length:.2f}×{self.height:.2f}m, net={self.net_area:.2f}m²{deduct_pct})"
