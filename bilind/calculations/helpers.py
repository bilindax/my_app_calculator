"""
Calculation Helper Functions
============================
Standalone calculation functions that don't require application state.
"""

from typing import Dict, Any, Optional, Union, Mapping


def safe_zone_area(zone: Union[Mapping, Any]) -> float:
    """
    Safely calculate ceramic zone area from perimeter × height.
    
    CRITICAL FIX: Always recalculate from perimeter × height for dict zones
    to avoid stale 'area' and 'effective_area' values.
    
    For floor/ceiling zones where height=1.0 and perimeter=area value,
    the calculation still works: perimeter × 1.0 = area.
    
    Args:
        zone: CeramicZone object or dict
        
    Returns:
        Area in m²
    """
    # Helper to get value from dict or object
    def _val(key: str, attr: str, default: Any = 0.0) -> Any:
        if isinstance(zone, Mapping):
            return zone.get(key, default)
        return getattr(zone, attr, default)
    
    # Get geometry values
    perim = 0.0
    height = 0.0
    
    def _to_float(val: Any) -> float:
        try:
            # Handle comma decimal separators (e.g., "1,5") coming from Excel/CSV-like inputs
            if isinstance(val, str):
                val = val.replace(',', '.')
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    perim = _to_float(_val('perimeter', 'perimeter', 0.0) or 0.0)
    height = _to_float(_val('height', 'height', 0.0) or 0.0)
    
    # Get surface type to handle floor zones specially
    surface_type = str(_val('surface_type', 'surface_type', 'wall') or 'wall').lower()
    
    # ALWAYS calculate from geometry for reliable results
    gross_area = 0.0
    if perim > 0 and height > 0:
        gross_area = perim * height
    
    # SPECIAL CASE: Floor zones with bad data (perimeter=1.0, height=1.0 but area should be larger)
    # This happens when floor ceramic was created with wrong perimeter value
    if surface_type == 'floor' and gross_area == 1.0:
        # Check if stored area is larger (likely correct)
        stored_area = _val('area', 'area', 0.0)
        try:
            stored_val = float(stored_area or 0.0)
            if stored_val > 1.0:
                # Stored area is likely correct (e.g., 10.79 instead of 1.0)
                return stored_val
        except (TypeError, ValueError):
            pass
    
    # Check effective_area (manual override or deduction)
    effective = _val('effective_area', 'effective_area', None)
    if effective is not None and effective != '':
        try:
            eff_val = float(effective)
            # Only use effective area if it's positive and makes sense
            if eff_val > 0 and gross_area > 0:
                # SPECIAL EXCEPTION: For floor/ceiling zones, trust effective_area if it's significantly larger than gross_area (1.0)
                # This handles the case where floor/ceiling zones use dummy 1x1 geometry but have real area in effective_area
                if surface_type in ('floor', 'ceiling') and gross_area <= 1.1 and eff_val > gross_area:
                    return eff_val

                # If effective is wildly larger than gross (e.g. 20.5 vs 2.25), it's stale -> use gross
                if eff_val > gross_area * 1.15: 
                    return gross_area
                # If effective is much smaller than gross (e.g. 1.0 vs 10.79), it's likely wrong -> use gross
                # Exception: if effective is close to gross (within 15%), it might be a valid deduction
                if eff_val < gross_area * 0.85:
                    # Likely wrong/stale data unless it's a legitimate deduction
                    # For floor zones where height=1.0, effective_area=1.0 is clearly wrong when area=10.79
                    return gross_area
                # Otherwise trust effective (it's a reasonable deduction, e.g. 9.5 vs 10.0)
                return eff_val
            elif eff_val > 0 and gross_area == 0:
                # No geometry, trust effective if available
                return eff_val
        except (TypeError, ValueError):
            pass
    
    # No valid effective area, use gross if available
    if gross_area > 0:
        return gross_area

    # Last resort: stored area
    stored_area = _val('area', 'area', 0.0)
    try:
        return float(stored_area or 0.0)
    except (TypeError, ValueError):
        return 0.0


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float with fallback.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def build_opening_record(
    opening_type: str,
    name: str,
    type_label: str,
    width: float,
    height: float,
    qty: int,
    weight: float = 0.0,
    layer: Optional[str] = None,
    placement_height: Optional[float] = None,
    total_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a normalized dictionary for doors/windows with calculated fields.
    
    Args:
        opening_type: 'DOOR' or 'WINDOW'
        name: Opening identifier (e.g., 'D1', 'W2')
        type_label: Material type (e.g., 'Wood', 'Aluminum')
        width: Width in meters
        height: Height in meters
        qty: Quantity (must be >= 1)
        weight: Weight per unit in kg (for doors only)
        layer: AutoCAD layer name
        placement_height: Height from floor to sill (meters) - defaults to 1.0m for windows, 0.0m for doors
        total_count: Total number of this opening type across all rooms/walls (for wall quantity calculations)
        
    Returns:
        Dictionary with calculated fields:
        - perim_each: Perimeter of one opening
        - perim: Total perimeter (all qty)
        - area_each: Area of one opening
        - area: Total area (all qty)
        - stone: Linear meters for stone surrounds
        - weight_each: Weight per opening (doors only)
        - weight: Total weight (doors only)
        - glass_each: Glass area per window (windows only)
        - glass: Total glass area (windows only)
        - placement_height: Height from floor (meters)
    """
    width = float(width)
    height = float(height)
    qty = max(1, int(qty))
    
    # Auto-set placement_height if not provided
    if placement_height is None:
        placement_height = 1.0 if opening_type == 'WINDOW' else 0.0
    
    # Calculate perimeter and area
    perim_each = 2 * (width + height)
    area_each = width * height
    area_total = area_each * qty
    perim_total = perim_each * qty
    stone_total = perim_total  # Linear meters for stone surrounds
    
    # Total count defaults to qty if not specified
    total_count = total_count if total_count is not None else qty
    
    record = {
        'name': name,
        'opening_type': opening_type,  # Store the type for filtering
        'layer': layer or type_label or opening_type,
        'type': type_label,
        'w': width,
        'h': height,
        'qty': qty,
        'total_count': total_count,  # Total across all rooms/walls
        'placement_height': placement_height,
        'perim_each': perim_each,
        'perim': perim_total,
        'area_each': area_each,
        'area': area_total,
        'stone': stone_total,
        'weight_each': float(weight) if opening_type == 'DOOR' else 0.0,
        'weight': float(weight) * qty if opening_type == 'DOOR' else 0.0
    }
    
    # Add glass calculations for windows
    if opening_type == 'WINDOW':
        glass_each = area_each * 0.85  # 85% glass, 15% frame
        record['glass_each'] = glass_each
        record['glass'] = glass_each * qty
    else:
        record['glass_each'] = 0.0
        record['glass'] = 0.0
    
    return record


def format_number(value: Any, digits: int = 2, default: str = '-', thousands: bool = False) -> str:
    """
    Format a numeric value for display in UI.
    
    Args:
        value: Number to format (int, float, or convertible string)
        digits: Number of decimal places
        default: String to return if value is invalid
        
    Returns:
        Formatted string (e.g., "123.46") or default if invalid
        
    Examples:
        >>> format_number(123.456)
        '123.46'
        >>> format_number(123.456, digits=3)
        '123.456'
        >>> format_number(None)
        '-'
        >>> format_number("invalid")
        '-'
    """
    try:
        num = float(value)
        if thousands:
            return f"{num:,.{digits}f}"
        return f"{num:.{digits}f}"
    except (TypeError, ValueError):
        return default
