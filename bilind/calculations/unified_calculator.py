"""
Unified Calculator - Single Source of Truth
============================================
المحرك الموحد لكل الحسابات في النظام.
تم التحديث: 
1. حساب مساحة الأرضيات بدلاً من العدد.
2. حساب الزريقة (المحارة) خلف السيراميك (بدون خصم).
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re

@dataclass
class RoomCalculations:
    """نتائج حسابات غرفة واحدة"""
    room_name: str
    
    # Walls
    walls_gross: float
    walls_openings: float
    walls_net: float
    
    # Ceiling
    ceiling_area: float
    
    # Ceramic
    ceramic_wall: float
    ceramic_ceiling: float
    ceramic_floor: float
    
    # Plaster
    plaster_walls: float
    plaster_ceiling: float
    plaster_total: float
    
    # Paint
    paint_walls: float
    paint_ceiling: float
    paint_total: float
    
    # Baseboard
    baseboard_length: float
    
    # Stone
    stone_length: float = 0.0


@dataclass
class ZoneMetrics:
    """نتائج حسابات منطقة سيراميك واحدة (Zone)."""
    gross_area: float
    net_area: float
    deduction_area: float
    deduction_details: str


class UnifiedCalculator:
    def __init__(self, project: Any):
        self.project = project
        self._ceramic_by_room_cache: Optional[Dict[str, Dict[str, float]]] = None
        
        # Build Helper Maps Once
        self.rooms_map = {self._get_attr(r, 'name'): r for r in getattr(project, 'rooms', [])}
        self.all_openings = (getattr(project, 'doors', []) or []) + (getattr(project, 'windows', []) or [])
        self.openings_map = {self._get_attr(o, 'name'): o for o in self.all_openings}

    def _resolve_zone_geometry(self, zone: Any, room_obj: Any) -> float:
        """
        SSOT Fix: حل مشكلة المناطق الصفرية بالبحث عن الجدار المطابق
        """
        perim = float(self._get_attr(zone, 'perimeter', 0.0) or 0.0)
        if perim > 0.01:
            return perim

        # إذا المحيط 0، نحاول استنتاجه من اسم الجدار
        z_name = self._get_attr(zone, 'name', '')
        walls = self._get_attr(room_obj, 'walls', []) or []
        
        # محاولة 1: تطابق رقم الجدار
        match = re.search(r'(?:جدار|Wall)\s*(\d+)', z_name, re.IGNORECASE)
        if match and walls:
            try:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(walls):
                    w_len = float(self._get_attr(walls[idx], 'length', 0.0) or 0.0)
                    if w_len > 0: return w_len
            except:
                pass
        return 0.0

    def calculate_ceramic_by_room(self) -> Dict[str, Dict[str, float]]:
        if self._ceramic_by_room_cache is not None:
            return self._ceramic_by_room_cache
        
        result = {}
        zones = getattr(self.project, 'ceramic_zones', []) or []

        def _wall_number(name: str) -> Optional[int]:
            try:
                m = re.search(r"(\d+)", str(name or ""))
                return int(m.group(1)) if m else None
            except Exception:
                return None

        def _walls_match(a: str, b: str) -> bool:
            a = str(a or "").strip()
            b = str(b or "").strip()
            if not a or not b:
                return False
            if a == b:
                return True
            na = _wall_number(a)
            nb = _wall_number(b)
            return (na is not None) and (nb is not None) and (na == nb)
        
        # ORPHAN FILTER: Build valid walls map to exclude deleted walls
        valid_walls = set()
        for r in getattr(self.project, 'rooms', []):
            r_name = self._get_attr(r, 'name', '')
            walls = self._get_attr(r, 'walls', []) or []
            for i, w in enumerate(walls):
                w_name = self._get_attr(w, 'name', f'Wall {i+1}')
                valid_walls.add((r_name, w_name))
                
                # Support Arabic/English variants
                import re
                num_match = re.search(r'(\d+)', w_name)
                if num_match:
                    num = num_match.group(1)
                    valid_walls.add((r_name, f"Wall {num}"))
                    valid_walls.add((r_name, f"جدار {num}"))
        
        for zone in zones:
            room_name = self._get_attr(zone, 'room_name', '')
            if not room_name: continue
            
            if room_name not in result:
                result[room_name] = {'wall': 0.0, 'ceiling': 0.0, 'floor': 0.0}
            
            surface_type = self._get_attr(zone, 'surface_type', 'wall')
            room_obj = self.rooms_map.get(room_name)

            # If the user explicitly set an effective area for a wall zone,
            # treat it as authoritative and do not auto-derive from perimeter/height.
            # This preserves manual customization (e.g., after manual deductions).
            if surface_type == 'wall':
                try:
                    eff = float(self._get_attr(zone, 'effective_area', 0.0) or 0.0)
                except Exception:
                    eff = 0.0
                if eff > 0:
                    result[room_name]['wall'] += eff
                    continue
            
            # ORPHAN CHECK: Skip zones for deleted walls (ONLY if wall_name is specified)
            if surface_type == 'wall':
                z_wall = self._get_attr(zone, 'wall_name', '')
                z_name = self._get_attr(zone, 'name', '')
                
                # Only filter if wall_name is explicitly set
                if z_wall:
                    if (room_name, z_wall) not in valid_walls:
                        # Try extracting wall number from zone name as fallback
                        import re
                        num_match = re.search(r'(?:جدار|Wall)\s*(\d+)', z_name, re.IGNORECASE)
                        if num_match:
                            wall_num = num_match.group(1)
                            if (room_name, f"جدار {wall_num}") not in valid_walls and \
                               (room_name, f"Wall {wall_num}") not in valid_walls:
                                continue  # Skip orphan zone
                        else:
                            continue  # Skip if wall not found
                # If no wall_name specified, zone is valid (legacy zones)
            
            # --- Geometry Resolution ---
            if surface_type in ('floor', 'ceiling'):
                # Area-based surfaces: prefer effective_area/area; fall back cautiously.
                zone_area = float(self._get_attr(zone, 'effective_area', 0.0) or 0.0)
                if zone_area <= 0:
                    zone_area = float(self._get_attr(zone, 'area', 0.0) or 0.0)

                # Legacy fallback: some zones store (perimeter * height) instead of area.
                if zone_area <= 0:
                    z_perim = float(self._get_attr(zone, 'perimeter', 0.0) or 0.0)
                    z_height = float(self._get_attr(zone, 'height', 0.0) or 0.0)
                    zone_area = z_perim * z_height
                
                # Final fallback to room area only if zone has no meaningful area
                if zone_area <= 0.01 and room_obj:
                    zone_area = float(self._get_attr(room_obj, 'area', 0.0) or 0.0)

                if surface_type == 'ceiling':
                    result[room_name]['ceiling'] += zone_area
                else:
                    result[room_name]['floor'] += zone_area
                continue  # Skip deduction logic for area-based surfaces
                
            # Wall Logic continues here...
            height = float(self._get_attr(zone, 'height', 0.0) or 0.0)
            perim = float(self._get_attr(zone, 'perimeter', 0.0) or 0.0)
            
            if perim <= 0.001 and surface_type == 'wall' and room_obj:
                perim = self._resolve_zone_geometry(zone, room_obj)
            
            gross_area = perim * height
            
            # --- Deductions Logic (Walls Only) ---
            deduction = 0.0
            if surface_type == 'wall' and room_obj:
                z_start = float(self._get_attr(zone, 'start_height', 0.0) or 0.0)
                z_end = z_start + height
                zone_wall_name = str(self._get_attr(zone, 'wall_name', '') or '').strip()
                room_perim = self._get_perimeter(room_obj)
                
                for op_id in (self._get_attr(room_obj, 'opening_ids', []) or []):
                    opening = self.openings_map.get(op_id)
                    if not opening: continue

                    # If the opening is bound to a specific wall, only deduct it from that wall-zone.
                    opening_host_wall = str(self._get_attr(opening, 'host_wall', '') or '').strip()
                    if zone_wall_name and opening_host_wall and not _walls_match(zone_wall_name, opening_host_wall):
                        continue
                    
                    ow = self._get_opening_width(opening)
                    oh = self._get_opening_height(opening)
                    otyp = str(self._get_attr(opening, 'opening_type', '')).upper()
                    def_pl = 1.0 if otyp == 'WINDOW' else 0.0
                    place = float(self._get_attr(opening, 'placement_height', def_pl) or def_pl)
                    
                    op_top = place + oh
                    ov_start = max(z_start, place)
                    ov_end = min(z_end, op_top)
                    overlap_h = max(0.0, ov_end - ov_start)
                    
                    if overlap_h > 0:
                        qtys = self._get_attr(opening, 'room_quantities', {}) or {}
                        q = int(qtys.get(room_name, 1))

                        piece = (ow * overlap_h * q)

                        # If we can't reliably bind the opening to this exact wall-zone,
                        # distribute deduction proportionally to avoid subtracting the
                        # same opening multiple times across multiple wall zones.
                        if not (zone_wall_name and opening_host_wall) and room_perim > 0 and perim < room_perim * 0.95:
                            piece *= (perim / room_perim)

                        deduction += piece

            net = max(0.0, gross_area - deduction)
            
            # QUALITY ASSURANCE CHECK: Ceramic cannot exceed available wall area
            # This prevents logical errors where ceramic > plaster
            if surface_type == 'wall' and room_obj:
                room_walls_gross = self.calculate_walls_gross(room_obj)
                room_openings = self.calculate_openings_deduction(room_obj, exclude_ceramic_overlap=False)
                max_available = max(0.0, room_walls_gross - room_openings)
                
                # Cap ceramic at net wall area
                if net > max_available:
                    net = max_available
            
            if surface_type == 'wall': result[room_name]['wall'] += net
            else: result[room_name]['ceiling'] += net
            
        self._ceramic_by_room_cache = result
        return result

    def calculate_zone_metrics(self, zone: Any) -> ZoneMetrics:
        """SSOT: calculate one ceramic zone gross/net and deduction audit."""

        def _wall_number(name: str) -> Optional[int]:
            try:
                m = re.search(r"(\d+)", str(name or ""))
                return int(m.group(1)) if m else None
            except Exception:
                return None

        def _walls_match(a: str, b: str) -> bool:
            a = str(a or "").strip()
            b = str(b or "").strip()
            if not a or not b:
                return False
            if a == b:
                return True
            na = _wall_number(a)
            nb = _wall_number(b)
            return (na is not None) and (nb is not None) and (na == nb)

        room_name = str(self._get_attr(zone, 'room_name', '') or '').strip()
        surface_type = str(self._get_attr(zone, 'surface_type', 'wall') or 'wall').strip()
        room_obj = self.rooms_map.get(room_name) if room_name else None

        # Manual override: effective_area on wall zones is authoritative.
        if surface_type == 'wall':
            try:
                eff = float(self._get_attr(zone, 'effective_area', 0.0) or 0.0)
            except Exception:
                eff = 0.0
            if eff > 0:
                return ZoneMetrics(
                    gross_area=eff,
                    net_area=eff,
                    deduction_area=0.0,
                    deduction_details='Effective Area (Manual override)',
                )

        # Orphan filtering (match calculate_ceramic_by_room behavior)
        if surface_type == 'wall' and room_obj:
            z_wall = str(self._get_attr(zone, 'wall_name', '') or '').strip()
            if z_wall:
                valid_walls = set()
                walls = self._get_attr(room_obj, 'walls', []) or []
                for i, w in enumerate(walls):
                    w_name = self._get_attr(w, 'name', f'Wall {i+1}')
                    valid_walls.add((room_name, w_name))
                    num_match = re.search(r'(\d+)', str(w_name or ''))
                    if num_match:
                        num = num_match.group(1)
                        valid_walls.add((room_name, f"Wall {num}"))
                        valid_walls.add((room_name, f"جدار {num}"))

                if (room_name, z_wall) not in valid_walls:
                    z_name = str(self._get_attr(zone, 'name', '') or '')
                    num_match = re.search(r'(?:جدار|Wall)\s*(\d+)', z_name, re.IGNORECASE)
                    if num_match:
                        wall_num = num_match.group(1)
                        if (room_name, f"جدار {wall_num}") not in valid_walls and (room_name, f"Wall {wall_num}") not in valid_walls:
                            return ZoneMetrics(0.0, 0.0, 0.0, 'Orphan zone (wall deleted)')
                    else:
                        return ZoneMetrics(0.0, 0.0, 0.0, 'Orphan zone (wall deleted)')

        # Area-based zones (floor/ceiling): no opening deductions.
        if surface_type in ('floor', 'ceiling'):
            zone_area = float(self._get_attr(zone, 'effective_area', 0.0) or 0.0)
            if zone_area <= 0:
                zone_area = float(self._get_attr(zone, 'area', 0.0) or 0.0)
            if zone_area <= 0:
                z_perim = float(self._get_attr(zone, 'perimeter', 0.0) or 0.0)
                z_height = float(self._get_attr(zone, 'height', 0.0) or 0.0)
                zone_area = z_perim * z_height
            if zone_area <= 0.01 and room_obj:
                zone_area = float(self._get_attr(room_obj, 'area', 0.0) or 0.0)
            return ZoneMetrics(
                gross_area=zone_area,
                net_area=zone_area,
                deduction_area=0.0,
                deduction_details='لا يوجد خصم',
            )

        # Wall zone geometry
        height = float(self._get_attr(zone, 'height', 0.0) or 0.0)
        perim = float(self._get_attr(zone, 'perimeter', 0.0) or 0.0)
        if perim <= 0.001 and room_obj:
            perim = self._resolve_zone_geometry(zone, room_obj)
        gross_area = perim * height

        deduction = 0.0
        details_list: List[str] = []
        if room_obj:
            z_start = float(self._get_attr(zone, 'start_height', 0.0) or 0.0)
            z_end = z_start + height
            zone_wall_name = str(self._get_attr(zone, 'wall_name', '') or '').strip()
            room_perim = self._get_perimeter(room_obj)

            for op_id in (self._get_attr(room_obj, 'opening_ids', []) or []):
                opening = self.openings_map.get(op_id)
                if not opening:
                    continue

                opening_host_wall = str(self._get_attr(opening, 'host_wall', '') or '').strip()
                if zone_wall_name and opening_host_wall and not _walls_match(zone_wall_name, opening_host_wall):
                    continue

                ow = self._get_opening_width(opening)
                oh = self._get_opening_height(opening)
                otyp = str(self._get_attr(opening, 'opening_type', '')).upper()
                def_pl = 1.0 if otyp == 'WINDOW' else 0.0
                place = float(self._get_attr(opening, 'placement_height', def_pl) or def_pl)

                op_top = place + oh
                ov_start = max(z_start, place)
                ov_end = min(z_end, op_top)
                overlap_h = max(0.0, ov_end - ov_start)
                if overlap_h <= 0:
                    continue

                qtys = self._get_attr(opening, 'room_quantities', {}) or {}
                q = int(qtys.get(room_name, 1))
                piece = (ow * overlap_h * q)

                ratio_note = ''
                if not (zone_wall_name and opening_host_wall) and room_perim > 0 and perim < room_perim * 0.95:
                    ratio = perim / room_perim
                    piece *= ratio
                    ratio_note = f" (نسبة {int(ratio * 100)}%)"

                if piece > 0.0001:
                    deduction += piece
                    o_name = str(self._get_attr(opening, 'name', op_id) or op_id)
                    details_list.append(f"{o_name}: -{piece:.2f}م²{ratio_note}")

        net = max(0.0, gross_area - deduction)

        # Keep the same QA cap used by calculate_ceramic_by_room
        if room_obj:
            room_walls_gross = self.calculate_walls_gross(room_obj)
            room_openings = self.calculate_openings_deduction(room_obj, exclude_ceramic_overlap=False)
            max_available = max(0.0, room_walls_gross - room_openings)
            if net > max_available:
                net = max_available

        details_str = " | ".join(details_list) if details_list else 'لا يوجد خصم'
        return ZoneMetrics(
            gross_area=float(gross_area or 0.0),
            net_area=float(net or 0.0),
            deduction_area=float(deduction or 0.0),
            deduction_details=details_str,
        )

    def calculate_room(self, room: Any) -> RoomCalculations:
        room_name = self._get_attr(room, 'name', '')
        
        walls_gross = self.calculate_walls_gross(room)
        area = float(self._get_attr(room, 'area', 0.0) or 0.0)
        cer_data = self.calculate_ceramic_by_room().get(room_name, {'wall': 0, 'ceiling': 0, 'floor': 0})
        
        openings_deduct = self.calculate_openings_deduction(room, exclude_ceramic_overlap=False)
        openings_deduct_plaster = self.calculate_openings_deduction(room, exclude_ceramic_overlap=True)
        
        walls_net = max(0.0, walls_gross - openings_deduct)
        
        # FIX 2: Plaster Logic Updated
        # الزريقة تحسب لكامل الجدار (خلف السيراميك)
        # المعادلة القديمة: max(0.0, walls_gross - openings_deduct_plaster - cer_data['wall'])
        # المعادلة الجديدة: إزالة خصم السيراميك
        plaster_walls = max(0.0, walls_gross - openings_deduct_plaster)
        plaster_ceiling = max(0.0, area)
        
        # Paint Logic (الدهان يخصم السيراميك)
        paint_walls = max(0.0, plaster_walls - cer_data['wall'])
        paint_ceiling = max(0.0, plaster_ceiling - cer_data['ceiling'])
        
        baseboard = self.calculate_baseboard(room)
        stone_length = self.calculate_stone(room)
        
        return RoomCalculations(
            room_name=room_name,
            walls_gross=walls_gross,
            walls_openings=openings_deduct,
            walls_net=walls_net,
            ceiling_area=area,
            ceramic_wall=cer_data['wall'],
            ceramic_ceiling=cer_data['ceiling'],
            ceramic_floor=cer_data['floor'],
            plaster_walls=plaster_walls,
            plaster_ceiling=plaster_ceiling,
            plaster_total=plaster_walls + plaster_ceiling,
            paint_walls=paint_walls,
            paint_ceiling=paint_ceiling,
            paint_total=paint_walls + paint_ceiling,
            baseboard_length=baseboard,
            stone_length=stone_length
        )

    def calculate_plaster(self, room: Any) -> Dict[str, float]:
        """Legacy helper: return plaster breakdown dict used by older code/tests."""
        rc = self.calculate_room(room)
        return {
            'walls_net': float(rc.plaster_walls or 0.0),
            'ceiling': float(rc.plaster_ceiling or 0.0),
            'total': float(rc.plaster_total or 0.0),
        }

    def calculate_paint(self, room: Any) -> Dict[str, float]:
        """Legacy helper: return paint breakdown dict used by older code/tests."""
        rc = self.calculate_room(room)
        return {
            'walls': float(rc.paint_walls or 0.0),
            'ceiling': float(rc.paint_ceiling or 0.0),
            'total': float(rc.paint_total or 0.0),
        }

    # ... (بقية التوابع: calculate_all_rooms, calculate_totals, helpers تبقى كما هي) ...
    def calculate_all_rooms(self) -> List[RoomCalculations]:
        return [self.calculate_room(r) for r in getattr(self.project, 'rooms', [])]

    def calculate_totals(self) -> Dict[str, float]:
        rooms = self.calculate_all_rooms()
        return {
            'plaster_total': sum(r.plaster_total for r in rooms),
            'paint_total': sum(r.paint_total for r in rooms),
            'ceramic_wall': sum(r.ceramic_wall for r in rooms),
            'ceramic_ceiling': sum(r.ceramic_ceiling for r in rooms),
            'ceramic_floor': sum(r.ceramic_floor for r in rooms),
            'ceramic_total': sum(r.ceramic_wall + r.ceramic_ceiling + r.ceramic_floor for r in rooms),
            'baseboard_total': sum(r.baseboard_length for r in rooms),
            'area_total': sum(r.ceiling_area for r in rooms),
            'stone_total': sum(r.stone_length for r in rooms)
        }

    def _get_attr(self, obj, attr, default=None):
        return obj.get(attr, default) if isinstance(obj, dict) else getattr(obj, attr, default)

    def _get_perimeter(self, room):
        p = float(self._get_attr(room, 'perimeter', 0) or 0)
        if p > 0: return p
        walls = self._get_attr(room, 'walls', []) or []
        return sum(float(self._get_attr(w, 'length', 0) or 0) for w in walls)

    def _get_opening_width(self, o):
        return float(self._get_attr(o, 'width', 0) or self._get_attr(o, 'w', 0) or 0)

    def _get_opening_height(self, o):
        return float(self._get_attr(o, 'height', 0) or self._get_attr(o, 'h', 0) or 0)
    
    def calculate_walls_gross(self, room: Any) -> float:
        walls = self._get_attr(room, 'walls', []) or []
        h = float(self._get_attr(room, 'wall_height', 3.0) or 3.0)
        if walls:
            return sum(float(self._get_attr(w, 'length', 0) or 0) * float(self._get_attr(w, 'height', h) or h) for w in walls)
        return self._get_perimeter(room) * h

    def calculate_openings_deduction(self, room: Any, exclude_ceramic_overlap: bool = False) -> float:
        total = 0.0
        rname = self._get_attr(room, 'name', '')
        for oid in (self._get_attr(room, 'opening_ids', []) or []):
            o = self.openings_map.get(oid)
            if o:
                w = self._get_opening_width(o)
                h = self._get_opening_height(o)
                # إذا كانت "زريقة خلف السيراميك"، فلا يهمنا exclude_ceramic_overlap
                # لأننا أصلاً نحسب الزريقة كاملة الآن.
                # ولكن سنبقيه للدهان (إذا احتاجه).
                # بالنسبة للزريقة: نخصم الفتحة كاملة.
                
                # تعديل: إذا كان الطلب هو "زريقة خلف السيراميك"، فهذا يعني أننا نعامل الجدار كأنه "بدون سيراميك"
                # وبالتالي الخصم هو مساحة الفتحة العادية.
                
                effective_h = h
                # المنطق القديم للخصم الجزئي (فوق السيراميك) تم تعطيله عملياً للزريقة
                # لكننا سنبقيه إذا أردنا استخدامه في أماكن أخرى
                
                q = int((self._get_attr(o, 'room_quantities', {}) or {}).get(rname, 1))
                total += w * effective_h * q
        return total

    def calculate_baseboard(self, room: Any) -> float:
        perim = self._get_perimeter(room)
        deduct = 0.0
        rname = self._get_attr(room, 'name', '')
        for oid in (self._get_attr(room, 'opening_ids', []) or []):
            o = self.openings_map.get(oid)
            if o and str(self._get_attr(o, 'opening_type', '')).upper() == 'DOOR':
                w = self._get_opening_width(o)
                q = int((self._get_attr(o, 'room_quantities', {}) or {}).get(rname, 1))
                deduct += w * q
        return max(0.0, perim - deduct)

    def calculate_stone(self, room: Any) -> float:
        room_name = self._get_attr(room, 'name', '')
        opening_ids = self._get_attr(room, 'opening_ids', []) or []
        total_stone = 0.0
        for opening_id in opening_ids:
            opening = self.openings_map.get(opening_id)
            if not opening: continue
            width = self._get_opening_width(opening)
            height = self._get_opening_height(opening)
            opening_type = str(self._get_attr(opening, 'opening_type', '')).upper()
            room_quantities = self._get_attr(opening, 'room_quantities', {}) or {}
            quantity = int(room_quantities.get(room_name, 1))
            if opening_type == 'DOOR':
                perimeter = (2 * height) + width
            else:
                perimeter = 2 * (height + width)
            total_stone += (perimeter * quantity)
        return total_stone
