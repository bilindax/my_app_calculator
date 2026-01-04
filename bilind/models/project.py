"""
Project Data Model
==================

This module defines the data structure for a BILIND project, which acts as a
container for all takeoff data. This allows for easy serialization and
deserialization when saving or loading projects.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

from .room import Room
from .opening import Opening
from .wall import Wall
from .finish import FinishItem, CeramicZone
from .mortar import MortarLayer
from .baseboard import Baseboard

@dataclass
class Project:
    """
    Represents a single BILIND project, containing all takeoff data.
    """
    project_name: str = "Untitled Project"
    drawing_name: str = ""
    bilind_version: str = "2.0" # For future compatibility checks
    
    # Core takeoff data
    rooms: List[Room] = field(default_factory=list)
    doors: List[Opening] = field(default_factory=list)
    windows: List[Opening] = field(default_factory=list)
    walls: List[Wall] = field(default_factory=list)
    
    # Finishes data
    plaster_items: List[FinishItem] = field(default_factory=list)
    paint_items: List[FinishItem] = field(default_factory=list)
    tiles_items: List[FinishItem] = field(default_factory=list)
    
    # Materials data
    ceramic_zones: List[CeramicZone] = field(default_factory=list)
    mortar_layers: List[MortarLayer] = field(default_factory=list)  # NEW: Plaster/mortar calculations
    baseboards: List[Baseboard] = field(default_factory=list)        # NEW: Baseboard/skirting data
    
    # Costs data
    material_costs: Dict[str, Any] = field(default_factory=dict)
    
    # Custom floor names (user-defined)
    custom_floors: List[str] = field(default_factory=list)
    
    # Application settings
    scale: float = 1.0
    
    # Project-specific calculation settings
    default_wall_height: float = 3.0
    min_opening_deduction_area: float = 0.5  # Don't deduct openings smaller than this (m²)
    plaster_waste_percentage: float = 5.0    # Waste % for plaster
    paint_waste_percentage: float = 10.0     # Waste % for paint
    tiles_waste_percentage: float = 15.0     # Waste % for tiles
    plaster_under_ceramic: bool = True       # Does plaster continue behind ceramic? (True = Yes)
    
    # Decimal precision controls (separate for each measurement type)
    decimal_precision: int = 2               # General/legacy precision (for backward compatibility)
    decimal_precision_area: int = 2          # Precision for area measurements (m²)
    decimal_precision_length: int = 2        # Precision for length measurements (m)
    decimal_precision_weight: int = 1        # Precision for weight measurements (kg)
    decimal_precision_cost: int = 2          # Precision for cost/currency values

    # Display formatting
    use_thousands_separator: bool = False    # 1,234.56 grouping in UI
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the project and its contents to a dictionary for JSON serialization."""
        return {
            "project_name": self.project_name,
            "drawing_name": self.drawing_name,
            "bilind_version": self.bilind_version,
            "scale": self.scale,
            "default_wall_height": self.default_wall_height,
            "min_opening_deduction_area": self.min_opening_deduction_area,
            "plaster_waste_percentage": self.plaster_waste_percentage,
            "paint_waste_percentage": self.paint_waste_percentage,
            "tiles_waste_percentage": self.tiles_waste_percentage,
            "plaster_under_ceramic": self.plaster_under_ceramic,
            "decimal_precision": self.decimal_precision,
            "decimal_precision_area": self.decimal_precision_area,
            "decimal_precision_length": self.decimal_precision_length,
            "decimal_precision_weight": self.decimal_precision_weight,
            "decimal_precision_cost": self.decimal_precision_cost,
            "use_thousands_separator": self.use_thousands_separator,
            "rooms": [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.rooms],
            "doors": [o.to_dict() if hasattr(o, 'to_dict') else o for o in self.doors],
            "windows": [w.to_dict() if hasattr(w, 'to_dict') else w for w in self.windows],
            "walls": [w.to_dict() if hasattr(w, 'to_dict') else w for w in self.walls],
            "plaster_items": [i.to_dict() if hasattr(i, 'to_dict') else i for i in self.plaster_items],
            "paint_items": [i.to_dict() if hasattr(i, 'to_dict') else i for i in self.paint_items],
            "tiles_items": [i.to_dict() if hasattr(i, 'to_dict') else i for i in self.tiles_items],
            "ceramic_zones": [c.to_dict() if hasattr(c, 'to_dict') else c for c in self.ceramic_zones],
            "mortar_layers": [m.to_dict() if hasattr(m, 'to_dict') else m for m in self.mortar_layers],
            "baseboards": [b.to_dict() if hasattr(b, 'to_dict') else b for b in self.baseboards],
            "material_costs": self.material_costs,
            "custom_floors": list(self.custom_floors),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Creates a Project instance from a dictionary."""
        return cls(
            project_name=data.get("project_name", "Untitled Project"),
            drawing_name=data.get("drawing_name", ""),
            bilind_version=data.get("bilind_version", "1.0"),
            scale=data.get("scale", 1.0),
            default_wall_height=data.get("default_wall_height", 3.0),
            min_opening_deduction_area=data.get("min_opening_deduction_area", 0.5),
            plaster_waste_percentage=data.get("plaster_waste_percentage", 5.0),
            paint_waste_percentage=data.get("paint_waste_percentage", 10.0),
            tiles_waste_percentage=data.get("tiles_waste_percentage", 15.0),
            plaster_under_ceramic=data.get("plaster_under_ceramic", True),
            decimal_precision=data.get("decimal_precision", 2),
            decimal_precision_area=data.get("decimal_precision_area", 2),
            decimal_precision_length=data.get("decimal_precision_length", 2),
            decimal_precision_weight=data.get("decimal_precision_weight", 1),
            decimal_precision_cost=data.get("decimal_precision_cost", 2),
            use_thousands_separator=data.get("use_thousands_separator", False),
            rooms=[Room.from_dict(r) for r in data.get("rooms", [])],
            doors=[Opening.from_dict(o) for o in data.get("doors", [])],
            windows=[Opening.from_dict(w) for w in data.get("windows", [])],
            walls=[Wall.from_dict(w) for w in data.get("walls", [])],
            plaster_items=[FinishItem.from_dict(i, finish_type='plaster') for i in data.get("plaster_items", [])],
            paint_items=[FinishItem.from_dict(i, finish_type='paint') for i in data.get("paint_items", [])],
            tiles_items=[FinishItem.from_dict(i, finish_type='tiles') for i in data.get("tiles_items", [])],
            ceramic_zones=[CeramicZone.from_dict(c) for c in data.get("ceramic_zones", [])],
            mortar_layers=[MortarLayer.from_dict(m) for m in data.get("mortar_layers", [])],
            baseboards=[Baseboard.from_dict(b) for b in data.get("baseboards", [])],
            material_costs=data.get("material_costs", {}),
            custom_floors=data.get("custom_floors", []),
        )
