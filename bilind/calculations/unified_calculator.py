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

# 1. تعريف كائن النتائج الموحد (The Truth Object)
@dataclass
class RoomCalculatedMetrics:
    room_name: str
    floor_area: float
    wall_area_net: float
    ceiling_area: float
    
    # الكميات
    zariqa_walls: float
    zariqa_ceiling: float
    paint_walls: float
    paint_ceiling: float
    ceramic_floor: float
    ceramic_walls: float
    ceramic_ceiling: float
    
    # النعلات (الحقل المصحح)
    baseboard_length_net: float
    baseboard_status: str  # لتوضيح سبب الإلغاء (مثلاً: "ملغى لوجود سيراميك")
    
    stone_frames_length: float

    @property
    def total_ceramic(self) -> float:
        """الإجمالي الحقيقي للسيراميك (أرضيات + جدران + أسقف)"""
        return self.ceramic_floor + self.ceramic_walls + self.ceramic_ceiling

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
        self.rooms = list(getattr(project, 'rooms', []) or [])
        self.rooms_map = {self._get_attr(r, 'name'): r for r in self.rooms if self._get_attr(r, 'name')}
        self.rooms_map_norm = {self._norm_text(self._get_attr(r, 'name')): r for r in self.rooms if self._get_attr(r, 'name')}

        self.all_openings = (getattr(project, 'doors', []) or []) + (getattr(project, 'windows', []) or [])
        self.openings_map = {self._get_attr(o, 'name'): o for o in self.all_openings if self._get_attr(o, 'name')}
        self.room_opening_ids_map = self._build_room_opening_ids_map()

    def _norm_text(self, x: Any) -> str:
        s = str(x or '').strip().lower()
        s = ' '.join(s.split())
        # Arabic-Indic digits -> Western
        trans = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
        return s.translate(trans)

    def _opening_id(self, oid: Any) -> str:
        if oid is None:
            return ''
        if isinstance(oid, str):
            return oid.strip()
        # Some flows may store an Opening object directly.
        name = self._get_attr(oid, 'name', '')
        return str(name or '').strip()

    def _resolve_room_name(self, room_name: Any) -> str:
        raw = str(room_name or '').strip()
        if not raw:
            return ''
        if raw in self.rooms_map:
            return raw
        r = self.rooms_map_norm.get(self._norm_text(raw))
        if r:
            return str(self._get_attr(r, 'name', raw) or raw).strip()
        return raw

    def _build_room_opening_ids_map(self) -> Dict[str, set]:
        """Merge openings from room.opening_ids, per-wall opening_ids, and opening-assigned room mappings."""
        room_opening_ids: Dict[str, set] = {}

        # 1) From rooms + their walls
        for r in self.rooms:
            rname = str(self._get_attr(r, 'name', '') or '').strip()
            if not rname:
                continue
            s = room_opening_ids.setdefault(rname, set())
            for oid in (self._get_attr(r, 'opening_ids', []) or []):
                on = self._opening_id(oid)
                if on:
                    s.add(on)
            for w in (self._get_attr(r, 'walls', []) or []):
                for oid in (self._get_attr(w, 'opening_ids', []) or []):
                    on = self._opening_id(oid)
                    if on:
                        s.add(on)

        # 2) From opening.assigned_rooms / opening.room_quantities keys
        for o in self.all_openings:
            oname = str(self._get_attr(o, 'name', '') or '').strip()
            if not oname:
                continue
            candidates = set()
            assigned = self._get_attr(o, 'assigned_rooms', None)
            if isinstance(assigned, str) and assigned.strip():
                candidates |= {x.strip() for x in assigned.split(',') if x.strip()}
            elif isinstance(assigned, (list, tuple, set)):
                candidates |= {str(x or '').strip() for x in assigned if str(x or '').strip()}

            qtys = self._get_attr(o, 'room_quantities', None)
            if isinstance(qtys, dict) and qtys:
                candidates |= {str(k or '').strip() for k in qtys.keys() if str(k or '').strip()}

            for cand in candidates:
                rname = self._resolve_room_name(cand)
                if not rname:
                    continue
                room_opening_ids.setdefault(rname, set()).add(oname)

        return room_opening_ids

    def _iter_room_opening_ids(self, room: Any) -> List[str]:
        rname = str(self._get_attr(room, 'name', '') or '').strip()
        if not rname:
            return []
        merged = self.room_opening_ids_map.get(rname)
        if merged:
            return list(merged)
        # Fallback
        ids = []
        for oid in (self._get_attr(room, 'opening_ids', []) or []):
            on = self._opening_id(oid)
            if on:
                ids.append(on)
        return ids

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
                idx = int(self._norm_text(match.group(1))) - 1
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
                m = re.search(r"(\d+)", self._norm_text(name))
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
            r_name = self._resolve_room_name(self._get_attr(r, 'name', '') or '')
            walls = self._get_attr(r, 'walls', []) or []
            for i, w in enumerate(walls):
                w_name = self._get_attr(w, 'name', f'Wall {i+1}')
                valid_walls.add((r_name, w_name))
                
                # Support Arabic/English variants
                import re
                num_match = re.search(r'(\d+)', self._norm_text(w_name))
                if num_match:
                    num = num_match.group(1)
                    valid_walls.add((r_name, f"Wall {num}"))
                    valid_walls.add((r_name, f"جدار {num}"))
        
        for zone in zones:
            room_name = self._resolve_room_name(self._get_attr(zone, 'room_name', '') or '')
            if not room_name:
                continue
            
            if room_name not in result:
                result[room_name] = {'wall': 0.0, 'ceiling': 0.0, 'floor': 0.0}
            
            surface_type = self._get_attr(zone, 'surface_type', 'wall')
            room_obj = self.rooms_map.get(room_name) or self.rooms_map_norm.get(self._norm_text(room_name))

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
                
                for op_id in (self._iter_room_opening_ids(room_obj) or []):
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
            # EXCEPTION: Bathroom/Toilet ceramic can go "behind" openings (tiling around fixtures)
            if surface_type == 'wall' and room_obj:
                zone_category = str(self._get_attr(zone, 'category', '') or '').upper()
                if zone_category != 'BATHROOM':  # Allow bathroom ceramic to exceed net wall area
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
                m = re.search(r"(\d+)", self._norm_text(name))
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

        room_name_raw = str(self._get_attr(zone, 'room_name', '') or '').strip()
        room_name = self._resolve_room_name(room_name_raw)
        surface_type = str(self._get_attr(zone, 'surface_type', 'wall') or 'wall').strip()
        room_obj = (self.rooms_map.get(room_name) or self.rooms_map_norm.get(self._norm_text(room_name))) if room_name else None
        
        # DEBUG CERAMIC DEDUCTIONS
        zone_name = str(self._get_attr(zone, 'name', '?') or '?')
        # DISABLED: effective_area contains old-style deduction (full opening area).
        # We now use overlap-based deduction for accuracy.
        # Manual override via effective_area is no longer supported for wall zones.
        # if surface_type == 'wall':
        #     try:
        #         eff = float(self._get_attr(zone, 'effective_area', 0.0) or 0.0)
        #     except Exception:
        #         eff = 0.0
        #     if eff > 0:
        #         return ZoneMetrics(
        #             gross_area=eff,
        #             net_area=eff,
        #             deduction_area=0.0,
        #             deduction_details='Effective Area (Manual override)',
        #         )

        # Orphan filtering (match calculate_ceramic_by_room behavior)
        if surface_type == 'wall' and room_obj:
            z_wall = str(self._get_attr(zone, 'wall_name', '') or '').strip()
            if z_wall:
                valid_walls = set()
                walls = self._get_attr(room_obj, 'walls', []) or []
                for i, w in enumerate(walls):
                    w_name = self._get_attr(w, 'name', f'Wall {i+1}')
                    valid_walls.add((room_name, w_name))
                    num_match = re.search(r'(\d+)', self._norm_text(w_name))
                    if num_match:
                        num = num_match.group(1)
                        valid_walls.add((room_name, f"Wall {num}"))
                        valid_walls.add((room_name, f"جدار {num}"))

                if (room_name, z_wall) not in valid_walls:
                    z_name = str(self._get_attr(zone, 'name', '') or '')
                    num_match = re.search(r'(?:جدار|Wall)\s*(\d+)', self._norm_text(z_name), re.IGNORECASE)
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

            for op_id in (self._iter_room_opening_ids(room_obj) or []):
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
                q = int(qtys.get(room_name, qtys.get(room_name_raw, 1)))
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
        # EXCEPTION: Bathroom ceramic can exceed net wall area (behind fixtures)
        if room_obj:
            zone_category = str(self._get_attr(zone, 'category', '') or '').upper()
            if zone_category != 'BATHROOM':
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
    def get_room_metrics(self, room) -> RoomCalculatedMetrics:
        """
        هذه هي الدالة الوحيدة المسموح لملفات التصدير باستدعائها.
        تقوم بجميع الحسابات وتطبيق قواعد العمل (Business Rules).
        """
        # 1. الحسابات الأساسية
        # Use get_verified_area if available (for polygon support), else fallback to standard area
        if hasattr(room, 'get_verified_area'):
            floor_area = float(room.get_verified_area())
        else:
            floor_area = float(self._get_attr(room, 'area', 0.0) or 0.0)
            
        # Calculate room metrics using existing logic
        rc = self.calculate_room(room)
        
        # 2. حساب السيراميك (Already calculated in rc)
        ceramic_w = rc.ceramic_wall
        ceramic_f = rc.ceramic_floor
        ceramic_c = rc.ceramic_ceiling
        
        # 3. قاعدة النعلات (Fixing the Logical Flaw)
        baseboard_len = 0.0
        baseboard_note = ""
        
        if ceramic_w > 0.1:  # إذا كان هناك سيراميك جدران
            baseboard_len = 0.0
            baseboard_note = "ملغى (يوجد سيراميك جدران)"
        else:
            # حساب المحيط الصافي بعد خصم فتحات الأبواب التي تصل للأرض
            # This logic is already in calculate_baseboard, but we need to be explicit about the rule
            baseboard_len = rc.baseboard_length
            baseboard_note = "محتسب"

        # 4. إرجاع الكائن "المختوم"
        return RoomCalculatedMetrics(
            room_name=rc.room_name,
            floor_area=round(floor_area, 4),
            wall_area_net=round(rc.walls_net, 4),
            ceiling_area=round(rc.ceiling_area, 4),
            zariqa_walls=round(rc.plaster_walls, 4),
            zariqa_ceiling=round(rc.plaster_ceiling, 4),
            paint_walls=round(rc.paint_walls, 4),
            paint_ceiling=round(rc.paint_ceiling, 4),
            ceramic_floor=round(ceramic_f, 4),
            ceramic_walls=round(ceramic_w, 4),
            ceramic_ceiling=round(ceramic_c, 4),
            baseboard_length_net=round(baseboard_len, 2),
            baseboard_status=baseboard_note,
            stone_frames_length=round(rc.stone_length, 2)
        )

    def get_physical_openings_data(self) -> Dict[str, Any]:
        """
        حساب الكميات الفيزيائية للفتحات (العدد الفعلي والحجر).
        هذا هو المصدر الوحيد للحقيقة للأعداد الإجمالية.
        """
        all_doors = getattr(self.project, 'doors', []) or []
        all_windows = getattr(self.project, 'windows', []) or []
        
        doors_qty = 0
        windows_qty = 0
        stone_linear = 0.0

        def _opening_total_qty(opening: Any) -> int:
            room_qtys = self._get_attr(opening, 'room_quantities', None)
            if isinstance(room_qtys, dict) and room_qtys:
                total = 0
                for q in room_qtys.values():
                    try:
                        total += max(1, int(q))
                    except (TypeError, ValueError):
                        total += 1
                return max(1, total)

            qty_val = self._get_attr(opening, 'quantity', None)
            if qty_val is None:
                qty_val = self._get_attr(opening, 'qty', None)
            try:
                return max(1, int(qty_val or 1))
            except (TypeError, ValueError):
                return 1
        
        # معالجة الأبواب
        for d in all_doors:
            # الكمية: نأخذ الرقم quantity المخزن في الكائن
            qty = _opening_total_qty(d)
            doors_qty += qty
            
            # حساب الحجر (مركزي): 2 ارتفاع + 1 عرض
            w = self._get_opening_width(d)
            h = self._get_opening_height(d)
            stone_linear += ((2 * h) + w) * qty

        # معالجة الشبابيك
        for w_item in all_windows:
            qty = _opening_total_qty(w_item)
            windows_qty += qty
            
            # حساب الحجر (مركزي): 2 ارتفاع + 2 عرض
            w = self._get_opening_width(w_item)
            h = self._get_opening_height(w_item)
            stone_linear += (2 * (w + h)) * qty
            
        return {
            "doors_count": doors_qty,
            "windows_count": windows_qty,
            "total_count": doors_qty + windows_qty,
            "total_stone_linear": stone_linear
        }

    def get_project_summary(self, rooms: List) -> dict:
        """تجميع البيانات للملخص من نفس المصدر
        
        CRITICAL: الحجر يُحسب per-room لأنه يرتبط بالفتحات داخل كل غرفة.
        إذا كان باب مشترك بين غرفتين، يظهر في حساب كلا الغرفتين.
        هذا يضمن: الملخص = مجموع التفاصيل (SSOT Compliance).
        """
        all_metrics = [self.get_room_metrics(r) for r in rooms]
        
        return {
            "total_floor_area": sum(m.floor_area for m in all_metrics),
            "total_ceramic": sum(m.total_ceramic for m in all_metrics),
            "total_ceramic_floor": sum(m.ceramic_floor for m in all_metrics),
            "total_ceramic_wall": sum(m.ceramic_walls for m in all_metrics),
            "total_ceramic_ceiling": sum(m.ceramic_ceiling for m in all_metrics),
            "total_baseboard": sum(m.baseboard_length_net for m in all_metrics),
            "total_plaster": sum(m.zariqa_walls + m.zariqa_ceiling for m in all_metrics),
            "total_paint": sum(m.paint_walls + m.paint_ceiling for m in all_metrics),
            "total_stone": sum(m.stone_frames_length for m in all_metrics)  # Per-room sum (handles shared openings correctly)
        }

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
        if p > 0:
            return p

        # Legacy support: many older flows store perimeter under 'perim'
        p = float(self._get_attr(room, 'perim', 0) or 0)
        if p > 0:
            return p

        walls = self._get_attr(room, 'walls', []) or []
        return sum(float(self._get_attr(w, 'length', 0) or 0) for w in walls)

    def _get_opening_width(self, o):
        return float(self._get_attr(o, 'width', 0) or self._get_attr(o, 'w', 0) or 0)

    def _get_opening_height(self, o):
        return float(self._get_attr(o, 'height', 0) or self._get_attr(o, 'h', 0) or 0)
    
    def calculate_walls_gross(self, room: Any) -> float:
        walls = self._get_attr(room, 'walls', []) or []
        default_h = float(getattr(self.project, 'default_wall_height', 3.0) or 3.0)
        h = float(self._get_attr(room, 'wall_height', default_h) or default_h)
        if walls:
            return sum(float(self._get_attr(w, 'length', 0) or 0) * float(self._get_attr(w, 'height', h) or h) for w in walls)
        return self._get_perimeter(room) * h

    def calculate_openings_deduction(self, room: Any, exclude_ceramic_overlap: bool = False) -> float:
        total = 0.0
        rname = self._get_attr(room, 'name', '')
        for oid in (self._iter_room_opening_ids(room) or []):
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
        for oid in (self._iter_room_opening_ids(room) or []):
            o = self.openings_map.get(oid)
            if o and str(self._get_attr(o, 'opening_type', '')).upper() == 'DOOR':
                w = self._get_opening_width(o)
                q = int((self._get_attr(o, 'room_quantities', {}) or {}).get(rname, 1))
                deduct += w * q
        return max(0.0, perim - deduct)

    def calculate_stone(self, room: Any) -> float:
        room_name = self._get_attr(room, 'name', '')
        opening_ids = self._iter_room_opening_ids(room) or []
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
