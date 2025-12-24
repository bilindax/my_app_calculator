"""
Unified Calculator - Single Source of Truth
============================================
المحرك الموحد لكل الحسابات في النظام.

الهدف: القضاء على التناقضات بين UI، Excel، والأقسام المختلفة.

Usage:
    from bilind.calculations.unified_calculator import UnifiedCalculator
    
    calc = UnifiedCalculator(project)
    plaster = calc.calculate_plaster(room)
    paint = calc.calculate_paint(room)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class RoomCalculations:
    """نتائج حسابات غرفة واحدة"""
    room_name: str
    
    # Walls
    walls_gross: float  # إجمالي مساحة الجدران
    walls_openings: float  # خصومات الفتحات
    walls_net: float  # صافي الجدران (بعد الفتحات)
    
    # Ceiling
    ceiling_area: float  # مساحة السقف
    
    # Ceramic
    ceramic_wall: float  # سيراميك الجدران
    ceramic_ceiling: float  # سيراميك السقف
    ceramic_floor: float  # سيراميك الأرضية
    
    # Plaster (المحارة)
    plaster_walls: float  # محارة الجدران (walls_net)
    plaster_ceiling: float  # محارة السقف (ceiling)
    plaster_total: float  # إجمالي المحارة
    
    # Paint (الدهان)
    paint_walls: float  # دهان الجدران (walls_net - ceramic_wall)
    paint_ceiling: float  # دهان السقف (ceiling - ceramic_ceiling)
    paint_total: float  # إجمالي الدهان
    
    # Baseboard
    baseboard_length: float  # طول النعلات (perimeter - door widths)


class UnifiedCalculator:
    """
    المحرك الموحد للحسابات - كل الحسابات تمر من هنا فقط.
    
    القواعد:
    1. مصدر واحد للبيانات: ceramic_zones (ليس ceramic_breakdown)
    2. منطق واحد: walls objects أولاً، ثم perimeter × height
    3. لا caching - كل حساب يتم on-demand
    """
    
    def __init__(self, project: Any):
        """
        Args:
            project: كائن المشروع (Project instance)
        """
        self.project = project
        self._ceramic_by_room_cache: Optional[Dict[str, Dict[str, float]]] = None
    
    def calculate_ceramic_by_room(self) -> Dict[str, Dict[str, float]]:
        """
        حساب السيراميك لكل غرفة من ceramic_zones مع خصم الفتحات المتقاطعة.
        
        Returns:
            {
                'room_name': {
                    'wall': float,      # بعد خصم الفتحات
                    'ceiling': float,   # بعد خصم الفتحات
                    'floor': float
                }
            }
        
        Note: يحسب Net Area (بعد خصم الفتحات المتقاطعة) - نفس منطق Excel Details.
        """
        if self._ceramic_by_room_cache is not None:
            return self._ceramic_by_room_cache
        
        from .helpers import safe_zone_area
        
        result = {}
        
        # Filter valid zones
        zones = getattr(self.project, 'ceramic_zones', []) or []
        
        # Build openings map once
        all_openings = (getattr(self.project, 'doors', []) or []) + \
                       (getattr(self.project, 'windows', []) or [])
        openings_map = {self._get_attr(o, 'name'): o for o in all_openings}
        
        # Build rooms map
        rooms_map = {self._get_attr(r, 'name'): r for r in getattr(self.project, 'rooms', [])}
        
        for zone in zones:
            room_name = self._get_attr(zone, 'room_name', '')
            if not room_name:
                continue
            
            if room_name not in result:
                result[room_name] = {'wall': 0.0, 'ceiling': 0.0, 'floor': 0.0}
            
            surface_type = self._get_attr(zone, 'surface_type', 'wall')
            gross_area = safe_zone_area(zone)
            
            # Calculate deductions for wall ceramic only (same as Excel logic)
            deduction = 0.0
            if surface_type == 'wall':
                room_obj = rooms_map.get(room_name)
                if room_obj:
                    zone_start = float(self._get_attr(zone, 'start_height', 0.0) or 0.0)
                    zone_height = float(self._get_attr(zone, 'height', 0.0) or 0.0)
                    zone_end = zone_start + zone_height
                    
                    opening_ids = self._get_attr(room_obj, 'opening_ids', []) or []
                    
                    for opening_id in opening_ids:
                        opening = openings_map.get(opening_id)
                        if not opening:
                            continue
                        
                        # Get opening geometry
                        o_width = self._get_opening_width(opening)
                        o_height = self._get_opening_height(opening)
                        
                        # Get placement height
                        opening_type = str(self._get_attr(opening, 'opening_type', '')).upper()
                        default_placement = 1.0 if opening_type == 'WINDOW' else 0.0
                        placement = float(self._get_attr(opening, 'placement_height', default_placement) or default_placement)
                        
                        o_bottom = placement
                        o_top = placement + o_height
                        
                        # Calculate vertical overlap
                        overlap_start = max(zone_start, o_bottom)
                        overlap_end = min(zone_end, o_top)
                        overlap_height = max(0.0, overlap_end - overlap_start)
                        
                        if overlap_height > 0:
                            # Get room-specific quantity
                            room_quantities = self._get_attr(opening, 'room_quantities', {}) or {}
                            quantity = int(room_quantities.get(room_name, 1))
                            
                            # Check if partial zone
                            zone_perim = float(self._get_attr(zone, 'perimeter', 0.0) or 0.0)
                            room_perim = self._get_perimeter(room_obj)
                            
                            if room_perim > 0 and zone_perim < room_perim * 0.9:
                                # Partial zone - proportional deduction
                                ratio = zone_perim / room_perim
                                deduction += (o_width * overlap_height * quantity) * ratio
                            else:
                                # Full zone - full deduction
                                deduction += (o_width * overlap_height * quantity)
            
            # Net area after deductions
            net_area = max(0.0, gross_area - deduction)
            
            if surface_type == 'wall':
                result[room_name]['wall'] += net_area
            elif surface_type == 'floor':
                result[room_name]['floor'] += net_area
            else:  # ceiling
                result[room_name]['ceiling'] += net_area
        
        self._ceramic_by_room_cache = result
        return result
    
    def calculate_walls_gross(self, room: Any) -> float:
        """
        حساب إجمالي مساحة الجدران.
        
        Logic:
            1. إذا وُجدت walls objects: sum(length × height)
            2. وإلا: perimeter × wall_height
        
        Returns:
            مساحة الجدران بالمتر المربع
        """
        walls = self._get_attr(room, 'walls', []) or []
        
        if walls:
            total = 0.0
            default_height = float(self._get_attr(room, 'wall_height', 3.0) or 3.0)
            
            for wall in walls:
                length = float(self._get_attr(wall, 'length', 0.0) or 0.0)
                height = float(self._get_attr(wall, 'height', default_height) or default_height)
                
                if length > 0 and height > 0:
                    total += length * height
            
            return total
        else:
            # Fallback to perimeter calculation
            perimeter = self._get_perimeter(room)
            height = float(self._get_attr(room, 'wall_height', 3.0) or 3.0)
            return perimeter * height
    
    def calculate_openings_deduction(self, room: Any, exclude_ceramic_overlap: bool = False) -> float:
        """
        حساب مجموع مساحة الفتحات في الغرفة.
        
        Args:
            room: كائن الغرفة
            exclude_ceramic_overlap: إذا True، يخصم فقط المساحة فوق السيراميك
        
        Uses: room_quantities (لكل فتحة قد تكون في عدة غرف)
        
        Returns:
            مساحة الفتحات بالمتر المربع
        """
        room_name = self._get_attr(room, 'name', '')
        opening_ids = self._get_attr(room, 'opening_ids', []) or []
        
        # Build openings map
        all_openings = (getattr(self.project, 'doors', []) or []) + \
                       (getattr(self.project, 'windows', []) or [])
        openings_map = {self._get_attr(o, 'name'): o for o in all_openings}
        
        # Get max ceramic height in this room if we need to exclude overlap
        max_ceramic_height = 0.0
        if exclude_ceramic_overlap:
            zones = getattr(self.project, 'ceramic_zones', []) or []
            for zone in zones:
                if self._get_attr(zone, 'room_name', '') == room_name:
                    surface_type = self._get_attr(zone, 'surface_type', 'wall')
                    if surface_type == 'wall':
                        start_h = float(self._get_attr(zone, 'start_height', 0.0) or 0.0)
                        zone_h = float(self._get_attr(zone, 'height', 0.0) or 0.0)
                        zone_top = start_h + zone_h
                        max_ceramic_height = max(max_ceramic_height, zone_top)
        
        total_deduction = 0.0
        
        for opening_id in opening_ids:
            opening = openings_map.get(opening_id)
            if not opening:
                continue
            
            width = self._get_opening_width(opening)
            height = self._get_opening_height(opening)
            
            # Get placement height (sill height)
            opening_type = str(self._get_attr(opening, 'opening_type', '')).upper()
            default_placement = 1.0 if opening_type == 'WINDOW' else 0.0
            placement = float(self._get_attr(opening, 'placement_height', default_placement) or default_placement)
            
            # Calculate effective height for deduction
            effective_height = height
            if exclude_ceramic_overlap and max_ceramic_height > 0:
                # Only deduct the part above ceramic
                opening_bottom = placement
                opening_top = placement + height
                
                # Calculate the part above ceramic
                above_ceramic_height = max(0.0, opening_top - max_ceramic_height)
                
                # If opening starts above ceramic, use full height
                # If opening is completely below ceramic, no deduction
                # If opening overlaps, use only the part above
                if opening_bottom >= max_ceramic_height:
                    effective_height = height  # Fully above ceramic
                elif opening_top <= max_ceramic_height:
                    effective_height = 0.0  # Fully below ceramic (covered by ceramic)
                else:
                    effective_height = above_ceramic_height  # Partial overlap
            
            # Get room-specific quantity
            room_quantities = self._get_attr(opening, 'room_quantities', {}) or {}
            quantity = int(room_quantities.get(room_name, 1))
            
            total_deduction += (width * effective_height * quantity)
        
        return total_deduction
    
    def calculate_plaster(self, room: Any) -> Dict[str, float]:
        """
        حساب المحارة (الزريقة).
        
        Logic:
            - المحارة تُوضع قبل السيراميك
            - تُخصم الفتحات (فقط الجزء فوق السيراميك)
            - المنطقة المغطاة بالسيراميك لا تحتاج محارة (محجوبة)
        
        Returns:
            {
                'walls_gross': float,
                'walls_net': float,  # بعد خصم الفتحات والسيراميك
                'ceiling': float,
                'total': float
            }
        """
        walls_gross = self.calculate_walls_gross(room)
        
        # خصم الفتحات (فقط الجزء فوق السيراميك)
        openings = self.calculate_openings_deduction(room, exclude_ceramic_overlap=True)
        
        # خصم السيراميك الجداري (لأنه يغطي المحارة)
        room_name = self._get_attr(room, 'name', '')
        ceramic_by_room = self.calculate_ceramic_by_room()
        ceramic = ceramic_by_room.get(room_name, {'wall': 0.0, 'ceiling': 0.0, 'floor': 0.0})
        
        walls_net = max(0.0, walls_gross - openings - ceramic['wall'])
        
        ceiling = float(self._get_attr(room, 'area', 0.0) or 0.0)
        
        return {
            'walls_gross': walls_gross,
            'walls_net': walls_net,
            'ceiling': ceiling,
            'total': walls_net + ceiling
        }
    
    def calculate_paint(self, room: Any) -> Dict[str, float]:
        """
        حساب الدهان.
        
        Logic:
            - الدهان = المحارة - السيراميك
            - Paint Walls = walls_net - ceramic_wall
            - Paint Ceiling = ceiling - ceramic_ceiling
        
        Returns:
            {
                'walls': float,
                'ceiling': float,
                'total': float
            }
        """
        plaster = self.calculate_plaster(room)
        
        room_name = self._get_attr(room, 'name', '')
        ceramic_by_room = self.calculate_ceramic_by_room()
        ceramic = ceramic_by_room.get(room_name, {'wall': 0.0, 'ceiling': 0.0, 'floor': 0.0})
        
        walls_paint = max(0.0, plaster['walls_net'] - ceramic['wall'])
        ceiling_paint = max(0.0, plaster['ceiling'] - ceramic['ceiling'])
        
        return {
            'walls': walls_paint,
            'ceiling': ceiling_paint,
            'total': walls_paint + ceiling_paint
        }
    
    def calculate_baseboard(self, room: Any) -> float:
        """
        حساب طول النعلات (الوزرات).
        
        Logic:
            - Baseboard = perimeter - door widths
        
        Returns:
            الطول بالمتر الطولي
        """
        room_name = self._get_attr(room, 'name', '')
        perimeter = self._get_perimeter(room)
        
        # Calculate door widths deduction
        opening_ids = self._get_attr(room, 'opening_ids', []) or []
        all_openings = (getattr(self.project, 'doors', []) or []) + \
                       (getattr(self.project, 'windows', []) or [])
        openings_map = {self._get_attr(o, 'name'): o for o in all_openings}
        
        door_width_deduction = 0.0
        
        for opening_id in opening_ids:
            opening = openings_map.get(opening_id)
            if not opening:
                continue
            
            opening_type = str(self._get_attr(opening, 'opening_type', '')).upper()
            if opening_type == 'DOOR':
                width = self._get_opening_width(opening)
                room_quantities = self._get_attr(opening, 'room_quantities', {}) or {}
                quantity = int(room_quantities.get(room_name, 1))
                door_width_deduction += (width * quantity)
        
        return max(0.0, perimeter - door_width_deduction)
    
    def calculate_room(self, room: Any) -> RoomCalculations:
        """
        حساب كامل لغرفة واحدة (كل القيم).
        
        Returns:
            RoomCalculations object with all metrics
        """
        room_name = self._get_attr(room, 'name', '')
        
        # Walls
        walls_gross = self.calculate_walls_gross(room)
        walls_openings = self.calculate_openings_deduction(room)
        walls_net = max(0.0, walls_gross - walls_openings)
        
        # Ceiling
        ceiling_area = float(self._get_attr(room, 'area', 0.0) or 0.0)
        
        # Ceramic
        ceramic_by_room = self.calculate_ceramic_by_room()
        ceramic = ceramic_by_room.get(room_name, {'wall': 0.0, 'ceiling': 0.0, 'floor': 0.0})
        
        # Plaster
        plaster_walls = walls_net
        plaster_ceiling = ceiling_area
        plaster_total = plaster_walls + plaster_ceiling
        
        # Paint
        paint_walls = max(0.0, walls_net - ceramic['wall'])
        paint_ceiling = max(0.0, ceiling_area - ceramic['ceiling'])
        paint_total = paint_walls + paint_ceiling
        
        # Baseboard
        baseboard_length = self.calculate_baseboard(room)
        
        return RoomCalculations(
            room_name=room_name,
            walls_gross=walls_gross,
            walls_openings=walls_openings,
            walls_net=walls_net,
            ceiling_area=ceiling_area,
            ceramic_wall=ceramic['wall'],
            ceramic_ceiling=ceramic['ceiling'],
            ceramic_floor=ceramic['floor'],
            plaster_walls=plaster_walls,
            plaster_ceiling=plaster_ceiling,
            plaster_total=plaster_total,
            paint_walls=paint_walls,
            paint_ceiling=paint_ceiling,
            paint_total=paint_total,
            baseboard_length=baseboard_length
        )
    
    def calculate_all_rooms(self) -> List[RoomCalculations]:
        """
        حساب كامل لكل الغرف في المشروع.
        
        Returns:
            List of RoomCalculations
        """
        rooms = getattr(self.project, 'rooms', []) or []
        return [self.calculate_room(room) for room in rooms]
    
    def calculate_totals(self) -> Dict[str, float]:
        """
        حساب الإجماليات للمشروع كاملاً.
        
        Returns:
            {
                'plaster_total': float,
                'paint_total': float,
                'ceramic_wall': float,
                'ceramic_floor': float,
                'ceramic_total': float,
                'baseboard_total': float,
                'area_total': float  # Room floor areas
            }
        """
        all_rooms = self.calculate_all_rooms()
        
        # Sum room floor areas from original rooms
        area_total = sum(
            float(self._get_attr(room, 'area', 0.0) or 0.0) 
            for room in self.project.rooms
        )
        
        return {
            'plaster_total': sum(r.plaster_total for r in all_rooms),
            'paint_total': sum(r.paint_total for r in all_rooms),
            'ceramic_wall': sum(r.ceramic_wall for r in all_rooms),
            'ceramic_ceiling': sum(r.ceramic_ceiling for r in all_rooms),
            'ceramic_floor': sum(r.ceramic_floor for r in all_rooms),
            'ceramic_total': sum(r.ceramic_wall + r.ceramic_ceiling + r.ceramic_floor for r in all_rooms),
            'baseboard_total': sum(r.baseboard_length for r in all_rooms),
            'area_total': area_total
        }
    
    # ==================== Helper Methods ====================
    
    def _get_attr(self, obj: Any, attr: str, default: Any = None) -> Any:
        """Get attribute from dict or object"""
        if isinstance(obj, dict):
            return obj.get(attr, default)
        else:
            return getattr(obj, attr, default)
    
    def _get_perimeter(self, room: Any) -> float:
        """Get room perimeter"""
        perim = self._get_attr(room, 'perimeter', 0.0)
        if perim and perim > 0:
            return float(perim)
        
        # Fallback: calculate from walls
        walls = self._get_attr(room, 'walls', []) or []
        if walls:
            return sum(float(self._get_attr(w, 'length', 0.0) or 0.0) for w in walls)
        
        return 0.0
    
    def _get_opening_width(self, opening: Any) -> float:
        """Get opening width"""
        width = self._get_attr(opening, 'width', None)
        if width is not None:
            return float(width)
        
        # Fallback patterns
        dim = self._get_attr(opening, 'dimensions', '')
        if 'x' in str(dim).lower():
            parts = str(dim).lower().split('x')
            if len(parts) >= 1:
                try:
                    return float(parts[0].strip())
                except:
                    pass
        
        return 1.0  # Default
    
    def _get_opening_height(self, opening: Any) -> float:
        """Get opening height"""
        height = self._get_attr(opening, 'height', None)
        if height is not None:
            return float(height)
        
        # Fallback patterns
        dim = self._get_attr(opening, 'dimensions', '')
        if 'x' in str(dim).lower():
            parts = str(dim).lower().split('x')
            if len(parts) >= 2:
                try:
                    return float(parts[1].strip())
                except:
                    pass
        
        return 2.0  # Default
