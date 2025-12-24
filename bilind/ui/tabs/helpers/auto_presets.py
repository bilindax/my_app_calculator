"""
Auto Presets - Automatic Finish Calculations
=============================================
Applies automatic plaster/ceramic/paint rules project-wide based on room types.

This module was extracted from room_manager_tab.py for better maintainability.
"""

from typing import TYPE_CHECKING, Callable, Optional
from bilind.models.finish import CeramicZone

if TYPE_CHECKING:
    from bilind_main import BilindEnhanced


def classify_room_type(name: str, room_obj) -> str:
    """
    Classify room type for quick presets.
    
    Returns one of: 'kitchen', 'bath', 'toilet', 'sink', 'balcony', 'other'
    """
    nm = (name or '').lower()

    # Explicit flags or room_type on model/dict
    is_balcony_flag = False
    try:
        if isinstance(room_obj, dict):
            is_balcony_flag = (
                bool(room_obj.get('is_balcony')) or 
                str(room_obj.get('room_type', '')).lower() == 'balcony'
            )
        else:
            is_balcony_flag = (
                bool(getattr(room_obj, 'is_balcony', False)) or 
                str(getattr(room_obj, 'room_type', '')).lower() == 'balcony'
            )
    except Exception:
        is_balcony_flag = False

    if is_balcony_flag or 'balcon' in nm or 'بلكون' in nm or 'شرفة' in nm:
        return 'balcony'
    if ('حمام' in nm and 'ضيوف' not in nm) or ('bath' in nm):
        return 'bath'
    if any(k in nm for k in ['toilet', 'wc', 'w.c', 'تواليت', 'مرحاض']):
        return 'toilet'
    if any(k in nm for k in ['kitchen', 'مطبخ']):
        return 'kitchen'
    if any(k in nm for k in ['sink', 'مغسلة']):
        return 'sink'
    return 'other'


class AutoPresetsCalculator:
    """
    Calculates and applies automatic finish presets to all rooms.
    
    Applies:
    - Plaster to all walls and ceilings
    - Ceramic to bathrooms, toilets, kitchens (based on room type detection)
    - Paint to remaining areas after ceramic deduction
    """
    
    def __init__(self, app: 'BilindEnhanced'):
        """
        Initialize the calculator.
        
        Args:
            app: Main application instance
        """
        self.app = app
        self.proj = app.project
        
        # Totals
        self.total_plaster = 0.0
        self.total_paint = 0.0
        self.total_ceramic = 0.0
    
    def apply(self, kt_height: float = 1.5, sink_w: float = 1.2, 
              sink_h: float = 0.6, replace_auto: bool = True,
              on_complete: Optional[Callable] = None):
        """
        Apply automatic presets to all rooms.
        
        Args:
            kt_height: Kitchen/toilet ceramic height (default 1.5m)
            sink_w: Sink ceramic width (default 1.2m)
            sink_h: Sink ceramic height (default 0.6m)
            replace_auto: Replace existing [Auto] items (default True)
            on_complete: Callback function when complete
        """
        # Reset totals
        self.total_plaster = 0.0
        self.total_paint = 0.0
        self.total_ceramic = 0.0
        
        # Clear existing auto items if requested
        if replace_auto:
            self._clear_auto_items()
        
        # Process each room
        for room in self.proj.rooms:
            self._process_room(room, kt_height, sink_w, sink_h)
        
        # Refresh views
        self.app.refresh_rooms()
        self.app.refresh_finishes_tab()
        
        # Status message
        status_msg = (
            f"Auto Presets applied • Plaster: {self.total_plaster:.2f} m² • "
            f"Ceramic: {self.total_ceramic:.2f} m² • Paint: {self.total_paint:.2f} m²"
        )
        if self.total_ceramic == 0.0:
            status_msg += " • No ceramic zones detected (check room names: حمام, مطبخ, تواليت, WC, sink/مغسلة)"
        self.app.update_status(status_msg, icon="⚙️")
        
        if on_complete:
            on_complete()
    
    def _clear_auto_items(self):
        """Remove existing [Auto] prefixed items."""
        self.proj.plaster_items = [
            it for it in (self.proj.plaster_items or [])
            if not (isinstance(it, dict) and str(it.get('desc', '')).startswith('[Auto]'))
        ]
        self.proj.paint_items = [
            it for it in (self.proj.paint_items or [])
            if not (isinstance(it, dict) and str(it.get('desc', '')).startswith('[Auto]'))
        ]
        self.proj.ceramic_zones = [
            z for z in (self.proj.ceramic_zones or [])
            if not (
                getattr(z, 'name', '').startswith('[Auto]') or
                (isinstance(z, dict) and str(z.get('name', '')).startswith('[Auto]'))
            )
        ]

    def clear_room_auto_items(self, room):
        """Remove existing [Auto] items for a specific room."""
        room_name = self.app._room_name(room)
        
        # 1. Filter Ceramic Zones
        kept_zones = []
        for z in (self.proj.ceramic_zones or []):
            z_name = getattr(z, 'name', '') if not isinstance(z, dict) else z.get('name', '')
            z_room = getattr(z, 'room_name', '') if not isinstance(z, dict) else z.get('room_name', '')
            
            is_auto = str(z_name).startswith('[Auto]')
            # Check if this zone belongs to the room
            is_for_room = (z_room == room_name) or (room_name in str(z_name))
            
            if is_auto and is_for_room:
                continue # Remove it
            
            kept_zones.append(z)
        
        self.proj.ceramic_zones = kept_zones
        
        # 2. Filter Plaster/Paint
        self.proj.plaster_items = [
            it for it in (self.proj.plaster_items or [])
            if not (isinstance(it, dict) and str(it.get('desc', '')).startswith('[Auto]') and room_name in str(it.get('desc', '')))
        ]
        self.proj.paint_items = [
            it for it in (self.proj.paint_items or [])
            if not (isinstance(it, dict) and str(it.get('desc', '')).startswith('[Auto]') and room_name in str(it.get('desc', '')))
        ]
        
        # 3. Recalculate Room Ceramic Totals
        # We need to sum up areas of remaining zones for this room
        total_area = 0.0
        breakdown = {}
        
        for z in self.proj.ceramic_zones:
            z_name = getattr(z, 'name', '') if not isinstance(z, dict) else z.get('name', '')
            z_room = getattr(z, 'room_name', '') if not isinstance(z, dict) else z.get('room_name', '')
            
            # Check if this zone belongs to the room
            if (z_room == room_name) or (room_name in str(z_name)):
                area = float(getattr(z, 'effective_area', 0) or getattr(z, 'perimeter', 0) * getattr(z, 'height', 0))
                if isinstance(z, dict):
                    area = float(z.get('effective_area', 0) or z.get('perimeter', 0) * z.get('height', 0))
                
                stype = getattr(z, 'surface_type', 'wall') if not isinstance(z, dict) else z.get('surface_type', 'wall')
                
                total_area += area
                breakdown[stype] = breakdown.get(stype, 0.0) + area
            
        if isinstance(room, dict):
            room['ceramic_area'] = total_area
            room['ceramic_breakdown'] = breakdown
        else:
            room.ceramic_area = total_area
            room.ceramic_breakdown = breakdown
    
    def _process_room(self, room, kt_height: float, sink_w: float, sink_h: float):
        """Process a single room for auto presets."""
        name = self.app._room_name(room)
        kind = classify_room_type(name, room)
        perim = float(self.app._room_attr(room, 'perim', 'perimeter', 0.0) or 0.0)
        area = float(self.app._room_attr(room, 'area', 'area', 0.0) or 0.0)
        wall_h = float(self.app._room_attr(room, 'wall_height', 'wall_height', 0.0) or 0.0)
        
        # Plaster for walls
        if wall_h > 0:
            walls_plaster = perim * wall_h
            self.proj.plaster_items = self.proj.plaster_items or []
            self.proj.plaster_items.append({'desc': f"[Auto] Walls: {name}", 'area': walls_plaster})
            self.total_plaster += walls_plaster
        
        # Plaster for ceiling
        if area > 0:
            ceiling_plaster = area
            self.proj.plaster_items = self.proj.plaster_items or []
            self.proj.plaster_items.append({'desc': f"[Auto] Ceiling: {name}", 'area': ceiling_plaster})
            self.total_plaster += ceiling_plaster
        
        # Ceramic based on room type
        room_ceram_wall = 0.0
        room_ceram_ceiling = 0.0
        
        if kind == 'bath' and wall_h > 0:
            room_ceram_wall += self._add_ceramic_wall(room, name, perim, wall_h)
            if area > 0:
                room_ceram_ceiling += self._add_ceramic_ceiling(room, name, area)
        
        if kind in ('toilet', 'kitchen') and kt_height > 0:
            limit = min(kt_height, wall_h if wall_h > 0 else kt_height)
            room_ceram_wall += self._add_ceramic_wall(room, name, perim, limit)
        
        if kind == 'sink' and sink_w > 0 and sink_h > 0:
            room_ceram_wall += self._add_sink_ceramic(room, name, sink_w, sink_h)
        
        self.total_ceramic += (room_ceram_wall + room_ceram_ceiling)
        
        # Paint (remaining area after ceramic)
        wall_openings_area = self._get_openings_area(room)
        walls_plaster = perim * wall_h if wall_h > 0 else 0.0
        net_walls_paint = max(0.0, walls_plaster - room_ceram_wall - wall_openings_area)
        ceiling_plaster = area
        net_ceiling_paint = max(0.0, ceiling_plaster - room_ceram_ceiling)
        
        if net_walls_paint > 0:
            self.proj.paint_items = self.proj.paint_items or []
            self.proj.paint_items.append({'desc': f"[Auto] Walls Paint: {name}", 'area': net_walls_paint})
            self.total_paint += net_walls_paint
        
        if net_ceiling_paint > 0:
            self.proj.paint_items = self.proj.paint_items or []
            self.proj.paint_items.append({'desc': f"[Auto] Ceiling Paint: {name}", 'area': net_ceiling_paint})
            self.total_paint += net_ceiling_paint
    
    def _add_ceramic_wall(self, room, name: str, perim: float, h_end: float) -> float:
        """Add wall ceramic zone with opening deductions."""
        area = perim * max(0.0, h_end)
        
        # Deduct openings
        summary = self.app.get_room_opening_summary(room)
        
        for did in summary.get('door_ids', []):
            for d in self.app.project.doors:
                if self.app._opening_name(d) == did:
                    h = float(self.app._opening_attr(d, 'h', 'height', 0.0) or 0.0)
                    w = float(self.app._opening_attr(d, 'w', 'width', 0.0) or 0.0)
                    p = float(self.app._opening_attr(d, 'placement_height', 'placement_height', 0.0) or 0.0)
                    qty = int(self.app._opening_attr(d, 'qty', 'quantity', 1) or 1)
                    top = p + h
                    overlap_start = max(0.0, p)
                    overlap_end = min(h_end, top)
                    if overlap_end > overlap_start:
                        area -= (w * (overlap_end - overlap_start) * qty)
                    break
        
        for wid in summary.get('window_ids', []):
            for w in self.app.project.windows:
                if self.app._opening_name(w) == wid:
                    h = float(self.app._opening_attr(w, 'h', 'height', 0.0) or 0.0)
                    ww = float(self.app._opening_attr(w, 'w', 'width', 0.0) or 0.0)
                    p = float(self.app._opening_attr(w, 'placement_height', 'placement_height', 1.0) or 1.0)
                    qty = int(self.app._opening_attr(w, 'qty', 'quantity', 1) or 1)
                    top = p + h
                    overlap_start = max(0.0, p)
                    overlap_end = min(h_end, top)
                    if overlap_end > overlap_start:
                        area -= (ww * (overlap_end - overlap_start) * qty)
                    break
        
        area = max(0.0, area)
        
        if area > 0:
            zone = CeramicZone(
                name=f"[Auto] Ceramic Wall - {name}",
                category='Other',
                perimeter=perim,
                height=h_end,
                surface_type='wall'
            )
            self.proj.ceramic_zones.append(zone)
            self._update_room_ceramic(room, 'wall', area)
        
        return area
    
    def _add_ceramic_ceiling(self, room, name: str, area: float) -> float:
        """Add ceiling ceramic zone."""
        cz = CeramicZone(
            name=f"[Auto] Ceramic Ceiling - {name}",
            category='Other',
            perimeter=area,
            height=1.0,
            surface_type='ceiling'
        )
        self.proj.ceramic_zones.append(cz)
        self._update_room_ceramic(room, 'ceiling', area)
        return area
    
    def _add_sink_ceramic(self, room, name: str, sink_w: float, sink_h: float) -> float:
        """Add sink ceramic zone."""
        area_sink = sink_w * sink_h
        cz = CeramicZone(
            name=f"[Auto] Sink - {name}",
            category='Other',
            perimeter=area_sink,
            height=1.0,
            surface_type='wall'
        )
        self.proj.ceramic_zones.append(cz)
        self._update_room_ceramic(room, 'wall', area_sink)
        return area_sink
    
    def _update_room_ceramic(self, room, surface_type: str, area: float):
        """Update room's ceramic breakdown."""
        if isinstance(room, dict):
            room['ceramic_area'] = (room.get('ceramic_area', 0.0) or 0.0) + area
            breakdown = (room.get('ceramic_breakdown', {}) or {})
            breakdown[surface_type] = breakdown.get(surface_type, 0.0) + area
            room['ceramic_breakdown'] = breakdown
        else:
            cur = getattr(room, 'ceramic_area', 0.0) or 0.0
            setattr(room, 'ceramic_area', cur + area)
            breakdown = getattr(room, 'ceramic_breakdown', {}) or {}
            breakdown[surface_type] = breakdown.get(surface_type, 0.0) + area
            setattr(room, 'ceramic_breakdown', breakdown)
    
    def _get_openings_area(self, room) -> float:
        """Get total area of openings in a room."""
        summary = self.app.get_room_opening_summary(room)
        total = 0.0
        ids = summary.get('door_ids', []) + summary.get('window_ids', [])
        
        for oid in ids:
            for d in self.app.project.doors:
                if self.app._opening_name(d) == oid:
                    total += float(self.app._opening_attr(d, 'area', 'area', 0.0) or 0.0)
            for w in self.app.project.windows:
                if self.app._opening_name(w) == oid:
                    total += float(self.app._opening_attr(w, 'area', 'area', 0.0) or 0.0)
        
        return total


def apply_auto_presets(app: 'BilindEnhanced', kt_height: float = 1.5, 
                       sink_w: float = 1.2, sink_h: float = 0.6,
                       replace_auto: bool = True, on_complete: Optional[Callable] = None):
    """
    Convenience function to apply auto presets.
    
    Args:
        app: Main application instance
        kt_height: Kitchen/toilet ceramic height
        sink_w: Sink ceramic width
        sink_h: Sink ceramic height
        replace_auto: Replace existing auto items
        on_complete: Callback when complete
    """
    calculator = AutoPresetsCalculator(app)
    calculator.apply(kt_height, sink_w, sink_h, replace_auto, on_complete)
