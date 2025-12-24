"""Ceramic zone normalization utilities.

Goal: keep wall-type ceramic zones consistent with the current room wall model.

Root bug addressed:
- Some code paths were overwriting *per-wall* ceramic zones' perimeter with the
  *total room wall length* (room perimeter / sum of walls), producing values
  like 15.70 for "Wall 4".
  
CRITICAL FIX (Dec 2025):
- When perimeter is updated, the stored 'area' field in dict zones becomes stale.
- This normalizer now ALWAYS recalculates 'area' = perimeter × height for dict zones,
  unless effective_area is explicitly set (non-zero).
- This fixes the bug where 1.5m × 1.5m showed wrong area due to outdated 'area' value.

This module provides a single normalization pass that:
- Detects per-wall zones (by wall_name or by name pattern like "جدار 4" / "Wall 4")
- Updates their perimeter to the matching wall.length
- Recomputes derived quantities for dict-based zones (area/adhesive/grout)
- Respects explicit effective_area overrides (for opening deductions)

It is intentionally app-state-free so it can be unit tested.
"""

from __future__ import annotations

import re
from typing import Any, Optional, Tuple


_WALL_NUM_RE = re.compile(r"(?:\bwall\b|جدار)\s*(\d+)", re.IGNORECASE)


def _val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _set(obj: Any, key: str, value: Any) -> None:
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)


def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        if isinstance(x, str):
            x = x.replace(',', '.')  # Support comma decimals
        return float(x)
    except Exception:
        return default


def _room_name(room: Any) -> str:
    return str(_val(room, "name", "") or "")


def _wall_name(wall: Any) -> str:
    return str(_val(wall, "name", "") or "")


def _wall_length(wall: Any) -> float:
    return _as_float(_val(wall, "length", 0.0) or 0.0)


def _find_wall_number(text: str) -> Optional[int]:
    if not text:
        return None
    m = _WALL_NUM_RE.search(text)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def _find_room(project: Any, room_name: str) -> Optional[Any]:
    if not room_name:
        return None
    for r in getattr(project, "rooms", []) or []:
        if _room_name(r) == room_name:
            return r
    return None


def _find_wall(room: Any, wall_name: Optional[str], wall_num: Optional[int]) -> Optional[Any]:
    walls = _val(room, "walls", []) or []
    if wall_name:
        for w in walls:
            if _wall_name(w) == wall_name:
                return w

    if wall_num is not None:
        for w in walls:
            n = _find_wall_number(_wall_name(w))
            if n == wall_num:
                return w

    return None


def _sum_wall_lengths(room: Any) -> float:
    walls = _val(room, "walls", []) or []
    if not walls:
        # Fall back to room perimeter fields
        perim = _val(room, "perimeter", None)
        if perim is None:
            perim = _val(room, "perim", 0.0)
        return _as_float(perim or 0.0)
    return sum(_wall_length(w) for w in walls)


def normalize_ceramic_wall_zones(project: Any) -> Tuple[int, int]:
    """Normalize wall-type ceramic zones to match room wall lengths.

    Returns:
        (zones_updated, zones_skipped)
    """

    zones = getattr(project, "ceramic_zones", []) or []
    updated = 0
    skipped = 0

    for z in zones:
        surface = str(_val(z, "surface_type", "wall") or "wall").lower()
        if surface != "wall":
            continue

        z_name = str(_val(z, "name", "") or "")
        z_room_name = str(_val(z, "room_name", "") or "")
        z_wall_name = _val(z, "wall_name", None)
        z_wall_name = str(z_wall_name) if z_wall_name else ""

        # Some legacy zones don't store room_name; try extracting from common patterns.
        # Examples:
        # - "سيراميك - بلكون 2 - جدار 4"
        # - "[Balcony] Wall 4 - بلكون 2"
        if not z_room_name and z_name:
            # Arabic pattern: "سيراميك - ROOM - جدار N"
            parts = [p.strip() for p in z_name.split("-")]
            if len(parts) >= 3 and "سيراميك" in parts[0]:
                z_room_name = parts[1]

        room = _find_room(project, z_room_name)
        if not room:
            skipped += 1
            continue

        wall_num = _find_wall_number(z_wall_name) or _find_wall_number(z_name)

        # Decide if zone is per-wall specific.
        is_specific = bool(z_wall_name) or (wall_num is not None)

        if is_specific:
            wall = _find_wall(room, z_wall_name if z_wall_name else None, wall_num)
            if not wall:
                skipped += 1
                continue

            new_perim = _wall_length(wall)
            if new_perim <= 0:
                skipped += 1
                continue

            # Update linkage
            _set(z, "room_name", _room_name(room))
            _set(z, "wall_name", _wall_name(wall))

            old_perim = _as_float(_val(z, "perimeter", 0.0) or 0.0)
            if abs(old_perim - new_perim) > 1e-6:
                _set(z, "perimeter", new_perim)

            # CRITICAL FIX: Always recompute area based on perimeter × height
            # unless effective_area is explicitly set (non-zero).
            effective_area = _val(z, "effective_area", None)
            h = _as_float(_val(z, "height", 0.0) or 0.0)
            
            if h > 0:
                # Calculate area from geometry
                calculated_area = new_perim * h
                
                # For dict zones: always update derived fields to match current geometry
                if isinstance(z, dict):
                    # Check if effective_area is valid (not stale)
                    use_effective = False
                    if effective_area not in (None, 0, 0.0, ""):
                        eff_val = _as_float(effective_area)
                        # If effective area is significantly larger than calculated area (e.g. > 10% larger),
                        # it's likely stale from a previous larger wall size. Invalidate it.
                        if eff_val <= calculated_area * 1.1:
                            use_effective = True
                        else:
                            # Stale effective_area detected (e.g. 20.5 vs 2.25) -> Clear it
                            z["effective_area"] = None
                    
                    if use_effective:
                        z["area"] = _as_float(effective_area)
                    else:
                        z["area"] = calculated_area
                    
                    # Update adhesive and grout based on final area
                    final_area = z["area"]
                    z["adhesive_kg"] = final_area * 3.0
                    z["grout_kg"] = final_area * 0.5
                # For object zones: area/adhesive/grout are computed properties

            updated += 1
            continue

        # Whole-room wall zone: keep it aligned with sum of wall lengths
        total_len = _sum_wall_lengths(room)
        if total_len <= 0:
            skipped += 1
            continue

        old_perim = _as_float(_val(z, "perimeter", 0.0) or 0.0)
        if abs(old_perim - total_len) > 1e-6:
            _set(z, "perimeter", total_len)

        # CRITICAL FIX: Always recompute area for whole-room zones too
        effective_area = _val(z, "effective_area", None)
        h = _as_float(_val(z, "height", 0.0) or 0.0)
        
        if h > 0:
            calculated_area = total_len * h
            
            if isinstance(z, dict):
                # If effective_area is set and non-zero, use it; otherwise use calculated
                if effective_area not in (None, 0, 0.0, ""):
                    z["area"] = _as_float(effective_area)
                else:
                    z["area"] = calculated_area
                
                final_area = z["area"]
                z["adhesive_kg"] = final_area * 3.0
                z["grout_kg"] = final_area * 0.5

        updated += 1

    return updated, skipped
