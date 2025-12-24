"""
Comprehensive Quantity Book Export
==================================
Exports a multi-sheet Excel workbook covering all project quantities in detail.
Designed for professional quantity surveying (QS).
"""

from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from typing import Any, Callable, Optional, List, Dict

# ===== STYLES =====
COLOR_HEADER_BG = "1F4E78"  # Dark Blue
COLOR_HEADER_FG = "FFFFFF"
COLOR_SUBTOTAL_BG = "DDEBF7"
COLOR_TOTAL_BG = "BDD7EE"

FONT_HEADER = Font(name='Segoe UI', bold=True, size=11, color=COLOR_HEADER_FG)
FONT_NORMAL = Font(name='Segoe UI', size=10)
FONT_BOLD = Font(name='Segoe UI', bold=True, size=10)

BORDER_THIN = Border(
    left=Side(style='thin', color='BFBFBF'),
    right=Side(style='thin', color='BFBFBF'),
    top=Side(style='thin', color='BFBFBF'),
    bottom=Side(style='thin', color='BFBFBF')
)

ALIGN_CENTER = Alignment(horizontal='center', vertical='center', wrap_text=True)
ALIGN_RIGHT = Alignment(horizontal='right', vertical='center', wrap_text=True) # For numbers
ALIGN_LEFT = Alignment(horizontal='left', vertical='center', wrap_text=True)   # For text (Arabic is RTL, but cell align left usually means start)

def setup_sheet(ws, title, is_rtl=True):
    ws.title = title
    if is_rtl:
        ws.sheet_view.rightToLeft = True
    ws.sheet_view.showGridLines = False

def write_header(ws, headers, row=1):
    for col, text in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=text)
        cell.font = FONT_HEADER
        cell.fill = PatternFill(start_color=COLOR_HEADER_BG, end_color=COLOR_HEADER_BG, fill_type="solid")
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_THIN

def write_row(ws, row_idx, data, center_cols=None):
    for col, val in enumerate(data, 1):
        cell = ws.cell(row=row_idx, column=col, value=val)
        cell.font = FONT_NORMAL
        cell.border = BORDER_THIN
        
        # Alignment
        if center_cols and col in center_cols:
            cell.alignment = ALIGN_CENTER
        elif isinstance(val, (int, float)):
            cell.alignment = ALIGN_CENTER # Numbers center usually looks okay, or right
            if isinstance(val, float):
                cell.number_format = '0.00'
        else:
            cell.alignment = ALIGN_CENTER # Default center for Arabic text often looks better in tables

def auto_fit(ws):
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if cell.value:
                    val_len = len(str(cell.value))
                    if '\n' in str(cell.value):
                        val_len = max(len(line) for line in str(cell.value).split('\n'))
                    max_length = max(max_length, val_len)
            except:
                pass
        adjusted_width = min(max_length + 4, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

def export_comprehensive_book(
    project: Any,
    filepath: str,
    app: Any = None, # To access helper methods if needed
    status_cb: Optional[Callable[[str, str], None]] = None,
    selected_sheets: Optional[List[str]] = None
) -> bool:
    
    if status_cb:
        status_cb("Generating Comprehensive Book...", "📊")

    wb = openpyxl.Workbook()
    # Remove default sheet if we are going to create specific ones
    if selected_sheets:
        wb.remove(wb.active)
    
    # Helper to safely get attributes
    def val(obj, attr, default=None):
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)
    
    # Helper to get perimeter (handles 'perimeter' and 'perim' variants)
    def get_perim(room):
        if isinstance(room, dict):
            return float(room.get('perimeter', 0.0) or room.get('perim', 0.0) or 0.0)
        p = getattr(room, 'perimeter', 0.0)
        if not p:
            p = getattr(room, 'perim', 0.0)
        return float(p or 0.0)

    # Helper to get opening width (handles 'width' and 'w' variants)
    def get_opening_width(opening):
        if isinstance(opening, dict):
            # Check 'w' first (primary key from build_opening_record), then 'width'
            v = opening.get('w')
            if v is None or v == 0:
                v = opening.get('width')
            return float(v or 0.0)
        # For objects, check both attributes
        w = getattr(opening, 'w', None)
        if w is None or w == 0:
            w = getattr(opening, 'width', 0.0)
        return float(w or 0.0)

    # Helper to get opening height (handles 'height' and 'h' variants)
    def get_opening_height(opening):
        if isinstance(opening, dict):
            # Check 'h' first (primary key from build_opening_record), then 'height'
            v = opening.get('h')
            if v is None or v == 0:
                v = opening.get('height')
            return float(v or 0.0)
        # For objects, check both attributes
        h = getattr(opening, 'h', None)
        if h is None or h == 0:
            h = getattr(opening, 'height', 0.0)
        return float(h or 0.0)

    # Helper to get opening quantity (handles 'quantity' and 'qty' variants)
    def get_opening_qty(opening):
        if isinstance(opening, dict):
            # Check 'qty' first (primary key from build_opening_record), then 'quantity'
            v = opening.get('qty')
            if v is None or v == 0:
                v = opening.get('quantity')
            return int(v or 1)
        # For objects, check both attributes
        q = getattr(opening, 'qty', None)
        if q is None or q == 0:
            q = getattr(opening, 'quantity', 1)
        return int(q or 1)

    # Helper to deduplicate openings by name and drop invalid/zero-qty ones
    def unique_openings(openings):
        seen = set()
        result = []
        for o in openings or []:
            name = val(o, 'name', '-')
            qty = get_opening_qty(o)
            if not name or name in seen or qty <= 0:
                continue
            seen.add(name)
            result.append(o)
        return result

    # Helper to check if sheet should be generated
    def should_gen(key):
        if not selected_sheets: return True
        return key in selected_sheets

    # Build a set of valid wall identifiers (room_name, wall_name) from actual room.walls
    def get_valid_wall_keys():
        """Returns a set of (room_name, wall_name) tuples for existing walls."""
        import re
        valid_keys = set()
        for room in project.rooms:
            room_name = val(room, 'name', '')
            walls = val(room, 'walls', []) or []
            for i, w in enumerate(walls):
                w_name = val(w, 'name', f'Wall {i+1}')
                valid_keys.add((room_name, w_name))
                # Also extract wall number for pattern matching
                num_match = re.search(r'(\d+)', w_name)
                if num_match:
                    # Add Arabic pattern variant
                    valid_keys.add((room_name, f"جدار {num_match.group(1)}"))
        return valid_keys
    
    def get_wall_length_from_room(room_name: str, wall_name: str) -> float:
        """Get actual wall length from room.walls by name."""
        import re
        for room in project.rooms:
            if val(room, 'name', '') != room_name:
                continue
            walls = val(room, 'walls', []) or []
            for i, w in enumerate(walls):
                w_name = val(w, 'name', f'Wall {i+1}')
                if w_name == wall_name:
                    return float(val(w, 'length', 0.0) or 0.0)
                # Also check by wall number
                num_match = re.search(r'(\d+)', wall_name)
                w_num_match = re.search(r'(\d+)', w_name)
                if num_match and w_num_match and num_match.group(1) == w_num_match.group(1):
                    return float(val(w, 'length', 0.0) or 0.0)
        return 0.0
    
    def fix_ceramic_zone_data(zone):
        """Fix ceramic zone with missing perimeter by reading from actual wall."""
        import re
        surface_type = val(zone, 'surface_type', 'wall')
        if surface_type != 'wall':
            return zone  # Only fix wall zones
        
        perim = float(val(zone, 'perimeter', 0.0) or 0.0)
        
        # Try to find actual wall length
        z_room = val(zone, 'room_name', '')
        z_wall = val(zone, 'wall_name', '')
        z_name = val(zone, 'name', '')
        z_height = float(val(zone, 'height', 0.0) or 0.0)
        
        # Find the room to check room perimeter
        room_obj = None
        room_perim = 0.0
        if z_room:
            for r in project.rooms:
                if val(r, 'name', '') == z_room:
                    room_obj = r
                    room_perim = get_perim(r)
                    break
        
        actual_length = 0.0
        
        # Method 1: Use wall_name directly
        if z_wall and z_room:
            actual_length = get_wall_length_from_room(z_room, z_wall)
        
        # Method 2: Extract wall number from zone name
        if actual_length <= 0 and z_room:
            num_match = re.search(r'(?:جدار|Wall)\s*(\d+)', z_name, re.IGNORECASE)
            if num_match:
                wall_num = num_match.group(1)
                # Try both naming conventions
                actual_length = get_wall_length_from_room(z_room, f"Wall {wall_num}")
                if actual_length <= 0:
                    actual_length = get_wall_length_from_room(z_room, f"جدار {wall_num}")
        
        # DECISION: When to update?
        # 1. If perimeter is 0 (missing)
        # 2. If perimeter equals room perimeter BUT actual wall is smaller (bug fix for 15.7 issue)
        should_update = False
        if actual_length > 0:
            if perim <= 0.001:
                should_update = True
            elif room_perim > 0 and abs(perim - room_perim) < 0.01 and abs(actual_length - room_perim) > 0.01:
                # Zone has room perimeter, but wall is different -> Fix it
                should_update = True
        
        if should_update:
            # Create fixed copy
            if isinstance(zone, dict):
                fixed = zone.copy()
                fixed['perimeter'] = actual_length
                fixed['area'] = actual_length * z_height
                fixed['adhesive_kg'] = (actual_length * z_height) * 3.0  # Wall adhesive rate
                fixed['grout_kg'] = (actual_length * z_height) * 0.5
                return fixed
            else:
                # For object, just update and return
                zone.perimeter = actual_length
                zone.area = actual_length * z_height
                zone.adhesive_kg = zone.area * 3.0
                zone.grout_kg = zone.area * 0.5
                return zone
        
        return zone
    
    def filter_orphan_ceramic_zones(zones):
        """Filter out ceramic wall zones that reference deleted walls."""
        import re
        valid_keys = get_valid_wall_keys()
        filtered = []
        
        for z in zones:
            surface_type = val(z, 'surface_type', 'wall')
            
            # Non-wall zones pass through (floor, ceiling)
            if surface_type != 'wall':
                filtered.append(z)
                continue
            
            z_room = val(z, 'room_name', '')
            z_wall = val(z, 'wall_name', '')
            z_name = val(z, 'name', '')
            
            # Check 1: Direct wall_name match
            if z_wall and (z_room, z_wall) in valid_keys:
                filtered.append(fix_ceramic_zone_data(z))  # Fix data if needed
                continue
            
            # Check 2: Extract wall number from zone name and validate
            # Pattern: "سيراميك - RoomName - جدار N" or "... - Wall N"
            num_match = re.search(r'(?:جدار|Wall)\s*(\d+)', z_name, re.IGNORECASE)
            if num_match and z_room:
                wall_num = num_match.group(1)
                if (z_room, f"جدار {wall_num}") in valid_keys or (z_room, f"Wall {wall_num}") in valid_keys:
                    filtered.append(fix_ceramic_zone_data(z))  # Fix data if needed
                    continue
            
            # Zone doesn't match any existing wall - skip it (orphaned)
            # print(f"[EXPORT] Skipping orphan ceramic zone: {z_name}")
        
        return filtered

    # Openings Lookup (needed by all sections)
    openings_map = {val(o, 'name'): o for o in project.doors + project.windows}

    # ==================== USE UNIFIED CALCULATOR ====================
    # Single Source of Truth - all calculations from one place
    from ..calculations.unified_calculator import UnifiedCalculator
    
    calc = UnifiedCalculator(project)
    
    # Pre-calculate ceramic values per room (shared by all sections)
    ceramic_by_room = calc.calculate_ceramic_by_room()
    
    # Pre-calculate all room metrics (for validation)
    all_room_calcs = calc.calculate_all_rooms()
    project_totals = calc.calculate_totals()
    # ================================================================

    # 1. SUMMARY (ملخص)
    if should_gen('summary'):
        if not wb.sheetnames:
            ws_sum = wb.create_sheet("ملخص المشروع")
        else:
            ws_sum = wb.create_sheet("ملخص المشروع")
        
        setup_sheet(ws_sum, "ملخص المشروع")
    
        ws_sum['B2'] = "ملخص كميات المشروع"
        ws_sum['B2'].font = Font(name='Segoe UI', size=18, bold=True, color=COLOR_HEADER_BG)
        ws_sum['B2'].alignment = Alignment(horizontal='right')
        
        ws_sum['B3'] = f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}"
        
        # ==================== USE UNIFIED CALCULATOR ====================
        # Get all totals from UnifiedCalculator (already calculated above)
        total_rooms = len(project.rooms)
        total_area = sum(float(val(r, 'area', 0.0) or 0.0) for r in project.rooms)
        
        tot_plaster = project_totals['plaster_total']
        tot_paint = project_totals['paint_total']
        tot_ceramic_wall = project_totals['ceramic_wall'] + project_totals['ceramic_ceiling']
        tot_ceramic_floor = project_totals['ceramic_floor']
        tot_ceramic_net = project_totals['ceramic_total']
        tot_baseboard = project_totals['baseboard_total']
        # ================================================================
        
        # Stone calculation (still needs manual loop - not part of core calculations)
        tot_stone_linear = 0.0
        for o in unique_openings(project.doors + project.windows):
            qty = get_opening_qty(o)
            w = get_opening_width(o)
            h = get_opening_height(o)
            
            # Correct Stone Perimeter Logic
            # Doors: 2 sides + top (2h + w)
            # Windows: 4 sides (2h + 2w)
            if str(val(o, 'opening_type', '')).upper() == 'DOOR':
                perim_one = (2 * h) + w
            else:
                perim_one = 2 * (w + h)
                
            tot_stone_linear += (perim_one * qty)

        summary_data = [
            ("عدد الغرف", total_rooms, "غرفة"),
            ("مساحة الأرضيات الإجمالية", total_area, "م²"),
            ("أعمال الزريقة (لياسة)", tot_plaster, "م²"),
            ("أعمال الدهان", tot_paint, "م²"),
            ("سيراميك الجدران", tot_ceramic_wall, "م²"),
            ("سيراميك الأرضيات", tot_ceramic_floor, "م²"),
            ("سيراميك (إجمالي صافي)", tot_ceramic_net, "م²"),
            ("نعلات (وزرات)", tot_baseboard, "م.ط"),
            ("حجر (إطارات فتحات)", tot_stone_linear, "م.ط"),
        ]
        
        r_idx = 5
        for title, val_num, unit in summary_data:
            ws_sum.cell(row=r_idx, column=2, value=title).font = FONT_BOLD
            ws_sum.cell(row=r_idx, column=3, value=val_num).number_format = '0.00'
            ws_sum.cell(row=r_idx, column=4, value=unit)
            r_idx += 1
            
        auto_fit(ws_sum)

    # 2. ROOMS (الغرف)
    if should_gen('rooms'):
        ws_rooms = wb.create_sheet("مساحة الغرف")
        setup_sheet(ws_rooms, "مساحة الغرف")
        headers_rooms = [
            "م", "اسم الغرفة", "نوع الغرفة", "الطابق", "الأبعاد", "المحيط (م)", "الارتفاع (م)",
            "مساحة الأرضية (م²)", "مساحة الجدران القائمة (م²)", "مساحة الفتحات (م²)", "مساحة الجدران الصافية (م²)",
            "نعلات (م.ط)", "سيراميك جدران (م²)", "سيراميك أرضيات (م²)", "سيراميك سقف (م²)",
            "ملاحظات"
        ]
        write_header(ws_rooms, headers_rooms)
        
        r_idx = 2
        total_floor_area = 0.0
        total_walls_gross = 0.0
        total_walls_net = 0.0
        total_openings_area = 0.0
        total_baseboard = 0.0
        total_c_wall = 0.0
        total_c_floor = 0.0
        total_c_ceil = 0.0
        
        for i, r in enumerate(project.rooms, 1):
            name = val(r, 'name', '-')
            room_type = val(r, 'room_type', '[غير محدد]') or '[غير محدد]'
            floor = val(r, 'floor', 0)
            w = float(val(r, 'width', 0.0) or 0.0)
            l = float(val(r, 'length', 0.0) or 0.0)
            
            # Perimeter Logic: Check 'perimeter' then 'perim'
            perim = get_perim(r)
            
            note = ""
            walls = val(r, 'walls', []) or []

            # Heuristic: if there are many wall edges, treat the room as irregular for reporting.
            # This avoids misleading width/length (often bounding-box-derived) for non-rectangles.
            is_irregular = len(walls) > 4

            # Normalize displayed W/L ordering (always show smaller×larger)
            w_disp, l_disp = (min(w, l), max(w, l)) if (w > 0 and l > 0) else (0.0, 0.0)

            if (w > 0 and l > 0) and not is_irregular:
                dims = f"{w_disp:.2f}×{l_disp:.2f}"
            else:
                # Irregular shape: list wall lengths (more informative than W/L)
                if walls:
                    wall_lens = [f"{float(val(wl, 'length', 0.0)):.2f}" for wl in walls]
                    dims = "+".join(wall_lens)
                    if len(dims) > 30:
                        dims = dims[:27] + "..."
                    note = "شكل غير منتظم (أطوال الأضلاع)"
                else:
                    dims = "-"
                    note = "شكل غير منتظم"

                # If W/L exist, clarify they are approximate (usually from bounding box/estimate)
                if w > 0 and l > 0:
                    note = (note + " | " if note else "") + f"أبعاد تقريبية: {w_disp:.2f}×{l_disp:.2f}"
                
            h = float(val(r, 'wall_height', 0.0) or 3.0)
            area = float(val(r, 'area', 0.0) or 0.0)

            walls = val(r, 'walls', []) or []
            walls_gross = 0.0
            wall_heights_list = []
            if walls:
                for wl in walls:
                    w_len = float(val(wl, 'length', 0.0) or 0.0)
                    w_h = float(val(wl, 'height', h) or h)
                    if w_len > 0 and w_h > 0:
                        walls_gross += w_len * w_h
                        wall_heights_list.append(f"{w_h:.2f}")
            else:
                walls_gross = perim * h
            
            # Openings & Baseboard Deductions
            op_area = 0.0
            door_width_deduct = 0.0
            op_ids = val(r, 'opening_ids', []) or []
            for oid in op_ids:
                o = openings_map.get(oid)
                if o:
                    ow = get_opening_width(o)
                    oh = get_opening_height(o)
                    # Use room-specific quantity
                    room_qtys = val(o, 'room_quantities', {}) or {}
                    qty = int(room_qtys.get(name, 1))
                    op_area += (ow * oh * qty)
                    if str(val(o, 'opening_type', '')).upper() == 'DOOR':
                        door_width_deduct += (ow * qty)
            
            walls_net = max(0, walls_gross - op_area)
            baseboard_len = max(0, perim - door_width_deduct)
            
            # Ceramic
            breakdown = val(r, 'ceramic_breakdown', {}) or {}
            c_wall = float(breakdown.get('wall', 0.0) or 0.0)
            c_floor = float(breakdown.get('floor', 0.0) or 0.0)
            c_ceil = float(breakdown.get('ceiling', 0.0) or 0.0)
            
            if wall_heights_list and len(set(wall_heights_list)) > 1:
                note = (note + " | " if note else "") + f"ارتفاعات: {' | '.join(wall_heights_list)}"

            # Add to totals
            total_floor_area += area
            total_walls_gross += walls_gross
            total_walls_net += walls_net
            total_openings_area += op_area
            total_baseboard += baseboard_len
            total_c_wall += c_wall
            total_c_floor += c_floor
            total_c_ceil += c_ceil
            
            row_data = [
                i, name, room_type, floor, dims, perim, h, 
                area, walls_gross, op_area, walls_net,
                baseboard_len, c_wall, c_floor, c_ceil,
                note
            ]
            write_row(ws_rooms, r_idx, row_data)
            r_idx += 1
        
        # Write totals row
        ws_rooms.cell(row=r_idx, column=1, value="").font = FONT_BOLD
        ws_rooms.cell(row=r_idx, column=2, value="الإجمالي").font = FONT_BOLD
        
        # Map totals to columns (1-based index)
        # 8: Floor Area, 9: Walls Gross, 10: Openings, 11: Walls Net
        # 12: Baseboard, 13: Cer Wall, 14: Cer Floor, 15: Cer Ceil
        totals_map = {
            8: total_floor_area,
            9: total_walls_gross,
            10: total_openings_area,
            11: total_walls_net,
            12: total_baseboard,
            13: total_c_wall,
            14: total_c_floor,
            15: total_c_ceil
        }
        
        for col, val_num in totals_map.items():
            cell = ws_rooms.cell(row=r_idx, column=col, value=val_num)
            cell.font = FONT_BOLD
            cell.number_format = '0.00'
            
        for col in range(1, 17):
            ws_rooms.cell(row=r_idx, column=col).fill = PatternFill(start_color=COLOR_TOTAL_BG, end_color=COLOR_TOTAL_BG, fill_type="solid")
            ws_rooms.cell(row=r_idx, column=col).border = BORDER_THIN
        
        auto_fit(ws_rooms)

    # 3. PLASTER (الزريقة)
    if should_gen('plaster'):
        ws_plaster = wb.create_sheet("أعمال الزريقة")
        setup_sheet(ws_plaster, "أعمال الزريقة")
        headers_plaster = [
            "م", "الموقع / الغرفة", "العنصر", "الطول (م)", "الارتفاع (م)", "المساحة القائمة (م²)",
            "خصم الفتحات (م²)", "سيراميك (م²)", "المساحة الصافية (م²)", "ملاحظات"
        ]
        write_header(ws_plaster, headers_plaster)
        
        r_idx = 2
        seq = 1
        total_gross_plaster = 0.0
        total_op_deduct = 0.0
        total_cer_deduct = 0.0
        total_net_plaster = 0.0
        
        for r in project.rooms:
            name = val(r, 'name', '-')
            perim = get_perim(r)
            h = float(val(r, 'wall_height', 0.0) or 3.0)
            area = float(val(r, 'area', 0.0) or 0.0)
            
            # Wall Row - Use actual walls if available
            walls = val(r, 'walls', []) or []
            wall_heights_list = []
            if walls:
                walls_gross = 0.0
                walls_total_len = 0.0
                for w in walls:
                    w_len = float(val(w, 'length', 0.0) or 0.0)
                    w_h = float(val(w, 'height', h) or h)
                    if w_len > 0 and w_h > 0:
                        walls_gross += w_len * w_h
                        walls_total_len += w_len
                        wall_heights_list.append(f"{w_h:.2f}")
            else:
                walls_gross = perim * h
                walls_total_len = perim
            
            op_area = 0.0
            op_ids = val(r, 'opening_ids', []) or []
            for oid in op_ids:
                o = openings_map.get(oid)
                if o:
                    ow = get_opening_width(o)
                    oh = get_opening_height(o)
                    # Use room-specific quantity
                    room_qtys = val(o, 'room_quantities', {}) or {}
                    qty = int(room_qtys.get(name, 1))
                    op_area += (ow * oh * qty)
            
            # Use calculated ceramic values from ceramic_by_room (same as summary/paint)
            room_ceramic = ceramic_by_room.get(name, {'wall': 0.0, 'ceiling': 0.0, 'floor': 0.0})
            c_wall = room_ceramic['wall']
            
            # Plaster is applied BEFORE ceramic - only deduct openings
            walls_net_plaster = max(0, walls_gross - op_area)
            
            # Build note with wall heights and ceramic info
            note_wall = ""
            if wall_heights_list and len(set(wall_heights_list)) > 1:
                note_wall = f"ارتفاعات: {' | '.join(wall_heights_list)}"
            if c_wall > 0:
                if note_wall:
                    note_wall += f" | سيراميك ({c_wall:.2f} م²)"
                else:
                    note_wall = f"يوجد سيراميك ({c_wall:.2f} م²) فوق الزريقة"
            
            total_gross_plaster += walls_gross
            total_op_deduct += op_area
            total_cer_deduct += c_wall  # Track ceramic but don't deduct from plaster
            total_net_plaster += walls_net_plaster

            mixed_heights = bool(walls and wall_heights_list and len(set(wall_heights_list)) > 1)
            wall_len_cell = float(walls_total_len or 0.0) if walls_total_len else 0.0
            wall_h_cell = "" if mixed_heights else (float(wall_heights_list[0]) if (walls and wall_heights_list) else float(h))
            write_row(ws_plaster, r_idx, [seq, name, "جدران", wall_len_cell, wall_h_cell, walls_gross, op_area, c_wall, walls_net_plaster, note_wall])
            r_idx += 1
            seq += 1

            # Detail rows when mixed heights: show each wall gross area
            if walls and len(set(wall_heights_list)) > 1:
                for w_idx, w in enumerate(walls, 1):
                    w_len = float(val(w, 'length', 0.0) or 0.0)
                    w_h = float(val(w, 'height', h) or h)
                    if w_len <= 0 or w_h <= 0:
                        continue
                    w_area = w_len * w_h
                    write_row(ws_plaster, r_idx, ["", f"{name} - جدار {w_idx}", "تفصيل", w_len, w_h, w_area, "", "", "", ""]) 
                    r_idx += 1
            
            # Ceiling Row
            c_ceil = room_ceramic['ceiling']
            # Plaster is applied BEFORE ceramic on ceiling too
            ceil_net = area
            
            note_ceil = ""
            if c_ceil > 0:
                note_ceil = f"يوجد سيراميك ({c_ceil:.2f} م²) فوق الزريقة"
            
            total_gross_plaster += area
            total_cer_deduct += c_ceil  # Track but don't deduct
            total_net_plaster += ceil_net
                
            write_row(ws_plaster, r_idx, [seq, name, "سقف", "", "", area, 0.0, c_ceil, ceil_net, note_ceil])
            r_idx += 1
            seq += 1
        
        # Totals row
        ws_plaster.cell(row=r_idx, column=2, value="الإجمالي").font = FONT_BOLD
        ws_plaster.cell(row=r_idx, column=6, value=total_gross_plaster).font = FONT_BOLD
        ws_plaster.cell(row=r_idx, column=6).number_format = '0.00'
        ws_plaster.cell(row=r_idx, column=7, value=total_op_deduct).font = FONT_BOLD
        ws_plaster.cell(row=r_idx, column=7).number_format = '0.00'
        ws_plaster.cell(row=r_idx, column=8, value=total_cer_deduct).font = FONT_BOLD
        ws_plaster.cell(row=r_idx, column=8).number_format = '0.00'
        ws_plaster.cell(row=r_idx, column=9, value=total_net_plaster).font = FONT_BOLD
        ws_plaster.cell(row=r_idx, column=9).number_format = '0.00'
        for col in range(1, 11):
            ws_plaster.cell(row=r_idx, column=col).fill = PatternFill(start_color=COLOR_TOTAL_BG, end_color=COLOR_TOTAL_BG, fill_type="solid")
            ws_plaster.cell(row=r_idx, column=col).border = BORDER_THIN
            
        auto_fit(ws_plaster)

    # 4. CERAMIC (السيراميك)
    if should_gen('ceramic'):
        ws_cer = wb.create_sheet("السيراميك")
        setup_sheet(ws_cer, "السيراميك")
        headers_cer = ["م", "المنطقة / الغرفة", "النوع", "المحيط (م)", "الارتفاع (م)", "المساحة القائمة (م²)", "خصم الفتحات (م²)", "المساحة الصافية (م²)", "اللاصق (كغ)", "روبة (كغ)"]
        write_header(ws_cer, headers_cer)
        
        r_idx = 2
        total_cer_area = 0.0
        total_deduct = 0.0
        total_net_area = 0.0
        total_adhesive = 0.0
        total_grout = 0.0
        
        # CRITICAL: Filter out orphan ceramic zones (walls that no longer exist)
        valid_ceramic_zones = filter_orphan_ceramic_zones(project.ceramic_zones)
        
        for i, z in enumerate(valid_ceramic_zones, 1):
            zname = val(z, 'name', '-')
            stype = val(z, 'surface_type', 'wall')
            stype_ar = "جدران" if stype == 'wall' else "أرضية"
            perim = float(val(z, 'perimeter', 0.0) or 0.0)
            h = float(val(z, 'height', 0.0) or 0.0)
            
            # Calculate Gross Area
            gross_area = perim * h
            
            # Calculate Deductions (Openings)
            deduction = 0.0
            z_room_name = val(z, 'room_name', '')
            
            # Only calculate deductions for walls, and if we have room info
            if stype == 'wall' and z_room_name:
                # Find room object
                room_obj = next((r for r in project.rooms if val(r, 'name', '') == z_room_name), None)
                if room_obj:
                    z_start = float(val(z, 'start_height', 0.0) or 0.0)
                    z_end = z_start + h
                    
                    op_ids = val(room_obj, 'opening_ids', []) or []
                    for oid in op_ids:
                        o = openings_map.get(oid)
                        if not o: continue
                        
                        # Get opening geometry
                        ow = get_opening_width(o)
                        oh = get_opening_height(o)
                        
                        # Get placement (sill height)
                        # Default: Window=1.0m, Door=0.0m
                        otype = str(val(o, 'opening_type', '')).upper()
                        def_place = 1.0 if otype == 'WINDOW' else 0.0
                        place = float(val(o, 'placement_height', def_place) or def_place)
                        
                        o_bottom = place
                        o_top = place + oh
                        
                        # Calculate vertical overlap
                        overlap_start = max(z_start, o_bottom)
                        overlap_end = min(z_end, o_top)
                        overlap_h = max(0.0, overlap_end - overlap_start)
                        
                        if overlap_h > 0:
                            # Get quantity in this room
                            room_qtys = val(o, 'room_quantities', {}) or {}
                            qty = int(room_qtys.get(z_room_name, 1))
                            
                            # Deduction = Width * Overlap * Qty
                            # Note: This assumes the opening is fully within the ceramic zone horizontally
                            # Since we don't have horizontal placement, we assume full width deduction
                            # proportional to the wall length? No, usually full width is deducted.
                            # However, if the zone is only part of the room (e.g. one wall), 
                            # we should only deduct if the opening is on THAT wall.
                            # Current data model links zones to walls via 'wall_name' if available.
                            
                            z_wall_name = val(z, 'wall_name', '')
                            should_deduct = True
                            
                            # If zone is linked to a specific wall, check if opening is on that wall
                            # Opening 'assigned_walls' or similar?
                            # Currently openings are linked to rooms, not specific walls in the simple model.
                            # BUT, if we have 'wall_name' in zone, we can try to be smarter.
                            # If we don't know which wall the opening is on, we might over-deduct if we deduct from all zones.
                            # HEURISTIC: If zone covers the whole room (perimeter ~ room perimeter), deduct all.
                            # If zone is partial, we might be over-deducting.
                            # For now, we will deduct proportionally if zone perimeter < room perimeter?
                            # Or just deduct full width and let the user verify.
                            # BETTER: Use the logic from room_metrics which handles this via 'shares' or similar.
                            # But here we are in a simple export script.
                            
                            # Let's check if we can match wall names.
                            # Openings don't usually store 'wall_name' in the simple model.
                            # So we will assume if the zone is a "Wall Zone", it might intersect.
                            # To be safe, we can check if zone perimeter is close to room perimeter.
                            room_perim = get_perim(room_obj)
                            if room_perim > 0 and perim < room_perim * 0.9:
                                # Partial zone (e.g. one wall).
                                # We don't know if the door is on this wall.
                                # Distribute deduction proportionally to perimeter?
                                # Deduction = (Opening Area Overlap) * (Zone Perim / Room Perim)
                                ratio = perim / room_perim
                                deduction += (ow * overlap_h * qty) * ratio
                            else:
                                # Full room zone, deduct full opening
                                deduction += (ow * overlap_h * qty)
            
            # CRITICAL FIX: Use safe_zone_area to calculate area (avoids stale stored values)
            from ..calculations.helpers import safe_zone_area
            
            safe_area = safe_zone_area(z)
            
            # Determine if safe_area is a "Net" area (from effective_area) or "Gross" area
            # We check if it differs significantly from gross_area
            if abs(safe_area - gross_area) > 0.001:
                # It's different from gross, so it must be a valid effective area (Net Area)
                net_area = safe_area
                # Force deduction to match the math: Deduction = Gross - Net
                # This ensures the table is mathematically consistent even if our calculated deduction was off
                if gross_area > net_area:
                    deduction = gross_area - net_area
                else:
                    # If Net >= Gross (e.g. waste factor added manually?), show 0 deduction
                    deduction = 0.0
            else:
                # It equals gross area (so no effective area, or effective was rejected)
                # We use our calculated deduction from overlap logic
                net_area = max(0.0, gross_area - deduction)
                # deduction variable is already calculated above
            
            # Recalculate materials based on Net Area
            adh = net_area * (5.0 if stype == 'floor' else 3.0)
            grout = net_area * 0.5
            
            total_cer_area += gross_area
            total_deduct += deduction
            total_net_area += net_area
            total_adhesive += adh
            total_grout += grout
            
            write_row(ws_cer, r_idx, [i, zname, stype_ar, perim, h, gross_area, deduction, net_area, adh, grout])
            r_idx += 1
        
        # Totals row
        ws_cer.cell(row=r_idx, column=2, value="الإجمالي").font = FONT_BOLD
        ws_cer.cell(row=r_idx, column=6, value=total_cer_area).font = FONT_BOLD
        ws_cer.cell(row=r_idx, column=6).number_format = '0.00'
        ws_cer.cell(row=r_idx, column=7, value=total_deduct).font = FONT_BOLD
        ws_cer.cell(row=r_idx, column=7).number_format = '0.00'
        ws_cer.cell(row=r_idx, column=8, value=total_net_area).font = FONT_BOLD
        ws_cer.cell(row=r_idx, column=8).number_format = '0.00'
        ws_cer.cell(row=r_idx, column=9, value=total_adhesive).font = FONT_BOLD
        ws_cer.cell(row=r_idx, column=9).number_format = '0.00'
        ws_cer.cell(row=r_idx, column=10, value=total_grout).font = FONT_BOLD
        ws_cer.cell(row=r_idx, column=10).number_format = '0.00'
        for col in range(1, 11):
            ws_cer.cell(row=r_idx, column=col).fill = PatternFill(start_color=COLOR_TOTAL_BG, end_color=COLOR_TOTAL_BG, fill_type="solid")
            ws_cer.cell(row=r_idx, column=col).border = BORDER_THIN
        auto_fit(ws_cer)

    # 5. PAINT (الدهان)
    if should_gen('paint'):
        ws_paint = wb.create_sheet("الدهان")
        setup_sheet(ws_paint, "الدهان")
        headers_paint = [
            "م", "الغرفة", "نوع الغرفة", "الطول (م)", "الارتفاع (م)", "مساحة الجدران القائمة (م²)",
            "خصم الفتحات (م²)", "خصم السيراميك (م²)", "دهان جدران صافي (م²)", "دهان سقف (م²)", "الإجمالي (م²)"
        ]
        write_header(ws_paint, headers_paint)
        
        r_idx = 2
        total_paint_wall = 0.0
        total_paint_ceil = 0.0
        
        for i, r in enumerate(project.rooms, 1):
            name = val(r, 'name', '-')
            room_type = val(r, 'room_type', '[غير محدد]') or '[غير محدد]'
            perim = get_perim(r)
            h = float(val(r, 'wall_height', 0.0) or 3.0)
            area = float(val(r, 'area', 0.0) or 0.0)

            walls = val(r, 'walls', []) or []
            walls_gross = 0.0
            walls_total_len = 0.0
            if walls:
                for wl in walls:
                    w_len = float(val(wl, 'length', 0.0) or 0.0)
                    w_h = float(val(wl, 'height', h) or h)
                    if w_len > 0 and w_h > 0:
                        walls_gross += w_len * w_h
                        walls_total_len += w_len
            else:
                walls_gross = perim * h
                walls_total_len = perim

            # Net Walls
            op_area = 0.0
            op_ids = val(r, 'opening_ids', []) or []
            for oid in op_ids:
                o = openings_map.get(oid)
                if o:
                    ow = get_opening_width(o)
                    oh = get_opening_height(o)
                    # Use room-specific quantity
                    room_qtys = val(o, 'room_quantities', {}) or {}
                    qty = int(room_qtys.get(name, 1))
                    op_area += (ow * oh * qty)
            
            # Use calculated ceramic values from ceramic_by_room (same as summary)
            room_ceramic = ceramic_by_room.get(name, {'wall': 0.0, 'ceiling': 0.0, 'floor': 0.0})
            c_wall = room_ceramic['wall']
            c_ceil = room_ceramic['ceiling']
            
            paint_wall = max(0, walls_gross - op_area - c_wall)
            paint_ceil = max(0, area - c_ceil)
            total = paint_wall + paint_ceil
            
            total_paint_wall += paint_wall
            total_paint_ceil += paint_ceil
            
            mixed_heights = bool(walls and len(set([f"{float(val(wl, 'height', h) or h):.2f}" for wl in walls])) > 1)
            wall_len_cell = float(walls_total_len or 0.0) if walls_total_len else 0.0
            wall_h_cell = "" if mixed_heights else float(h)
            write_row(ws_paint, r_idx, [
                i, name, room_type,
                wall_len_cell, wall_h_cell, walls_gross,
                op_area, c_wall,
                paint_wall, paint_ceil, total
            ])
            r_idx += 1

            # Detail rows when mixed heights: show each wall net paint (with proportional deductions)
            if mixed_heights:
                for w_idx, wl in enumerate(walls, 1):
                    w_len = float(val(wl, 'length', 0.0) or 0.0)
                    w_h = float(val(wl, 'height', h) or h)
                    if w_len <= 0 or w_h <= 0:
                        continue
                    w_area_gross = w_len * w_h
                    # Distribute openings and ceramic deductions proportionally by wall area
                    share_ratio = (w_area_gross / walls_gross) if walls_gross > 0 else 0.0
                    w_op_deduct = op_area * share_ratio
                    w_cer_deduct = c_wall * share_ratio
                    w_paint_net = max(0.0, w_area_gross - w_op_deduct - w_cer_deduct)
                    write_row(ws_paint, r_idx, [
                        "", f"{name} - جدار {w_idx}", "تفصيل",
                        w_len, w_h, w_area_gross,
                        w_op_deduct, w_cer_deduct, w_paint_net, "", ""
                    ])
                    r_idx += 1
        
        # Totals row
        ws_paint.cell(row=r_idx, column=2, value="الإجمالي").font = FONT_BOLD
        ws_paint.cell(row=r_idx, column=9, value=total_paint_wall).font = FONT_BOLD
        ws_paint.cell(row=r_idx, column=9).number_format = '0.00'
        ws_paint.cell(row=r_idx, column=10, value=total_paint_ceil).font = FONT_BOLD
        ws_paint.cell(row=r_idx, column=10).number_format = '0.00'
        ws_paint.cell(row=r_idx, column=11, value=total_paint_wall + total_paint_ceil).font = FONT_BOLD
        ws_paint.cell(row=r_idx, column=11).number_format = '0.00'
        for col in range(1, 12):
            ws_paint.cell(row=r_idx, column=col).fill = PatternFill(start_color=COLOR_TOTAL_BG, end_color=COLOR_TOTAL_BG, fill_type="solid")
            ws_paint.cell(row=r_idx, column=col).border = BORDER_THIN
        auto_fit(ws_paint)

    # 6. BASEBOARDS (النعلات)
    if should_gen('baseboards'):
        ws_base = wb.create_sheet("النعلات")
        setup_sheet(ws_base, "النعلات")
        headers_base = ["م", "الغرفة", "نوع الغرفة", "المحيط (م)", "خصم الأبواب (م)", "صافي النعلات (م.ط)"]
        write_header(ws_base, headers_base)
        
        r_idx = 2
        total_perim = 0.0
        total_door_deduct = 0.0
        total_net_base = 0.0
        
        for i, r in enumerate(project.rooms, 1):
            name = val(r, 'name', '-')
            room_type = val(r, 'room_type', '[غير محدد]') or '[غير محدد]'
            perim = get_perim(r)
            
            deduct = 0.0
            op_ids = val(r, 'opening_ids', []) or []
            for oid in op_ids:
                o = openings_map.get(oid)
                if o and str(val(o, 'opening_type', '')).upper() == 'DOOR':
                    ow = get_opening_width(o)
                    # Use room-specific quantity if available, else default to 1
                    room_qtys = val(o, 'room_quantities', {}) or {}
                    qty = int(room_qtys.get(name, 1))
                    deduct += (ow * qty)
            
            net = max(0, perim - deduct)
            
            total_perim += perim
            total_door_deduct += deduct
            total_net_base += net
            
            write_row(ws_base, r_idx, [i, name, room_type, perim, deduct, net])
            r_idx += 1
        
        # Totals row
        ws_base.cell(row=r_idx, column=2, value="الإجمالي").font = FONT_BOLD
        ws_base.cell(row=r_idx, column=4, value=total_perim).font = FONT_BOLD
        ws_base.cell(row=r_idx, column=4).number_format = '0.00'
        ws_base.cell(row=r_idx, column=5, value=total_door_deduct).font = FONT_BOLD
        ws_base.cell(row=r_idx, column=5).number_format = '0.00'
        ws_base.cell(row=r_idx, column=6, value=total_net_base).font = FONT_BOLD
        ws_base.cell(row=r_idx, column=6).number_format = '0.00'
        for col in range(1, 7):
            ws_base.cell(row=r_idx, column=col).fill = PatternFill(start_color=COLOR_TOTAL_BG, end_color=COLOR_TOTAL_BG, fill_type="solid")
            ws_base.cell(row=r_idx, column=col).border = BORDER_THIN
        auto_fit(ws_base)

    # 7. STONE & OPENINGS (الحجر والفتحات)
    if should_gen('stone'):
        ws_stone = wb.create_sheet("الحجر والفتحات")
        setup_sheet(ws_stone, "الحجر والفتحات")
        headers_stone = [
            "م", "العنصر", "النوع", "المادة", "العدد", "الأبعاد", 
            "مساحة الفتحة (م²)", "محيط الحجر (م.ط)", "مساحة الأباجور (م²)", "وزن الحديد (كغ)"
        ]
        write_header(ws_stone, headers_stone)
        
        r_idx = 2
        total_op_area = 0.0
        total_stone = 0.0
        total_shutter = 0.0
        total_weight = 0.0
        
        filtered_ops = unique_openings(project.doors + project.windows)

        for i, o in enumerate(filtered_ops, 1):
            name = val(o, 'name', '-')
            otype = "باب" if str(val(o, 'opening_type', '')).upper() == 'DOOR' else "شباك"
            material = val(o, 'material_type', '-') or val(o, 'type', '-') or '-'
            qty = get_opening_qty(o)
            w = get_opening_width(o)
            h = get_opening_height(o)
            dims = f"{w:.2f}x{h:.2f}"
            
            area_one = w * h
            area_total = area_one * qty
            
            # Stone Perimeter (Perimeter * Qty)
            # Doors: 2 sides + top (2h + w)
            # Windows: 4 sides (2h + 2w)
            if str(val(o, 'opening_type', '')).upper() == 'DOOR':
                perim_one = (2 * h) + w
            else:
                perim_one = 2 * (w + h)
                
            stone_total = perim_one * qty
            
            # Shutter (Abajour) - Assume for Windows only
            shutter_area = area_total if otype == "شباك" else 0.0
            
            # Metal Weight
            # Check material type
            mat = str(val(o, 'material_type', '')).lower()
            is_metal = any(x in mat for x in ['metal', 'iron', 'steel', 'حديد', 'معدن'])
            weight = 0.0
            if is_metal:
                weight = float(val(o, 'weight', 0.0) or 0.0)
                if weight == 0:
                    weight = area_total * 25.0 
            
            total_op_area += area_total
            total_stone += stone_total
            total_shutter += shutter_area
            total_weight += weight
            
            write_row(ws_stone, r_idx, [i, name, otype, material, qty, dims, area_total, stone_total, shutter_area, weight])
            r_idx += 1
        
        # Totals row
        ws_stone.cell(row=r_idx, column=2, value="الإجمالي").font = FONT_BOLD
        ws_stone.cell(row=r_idx, column=7, value=total_op_area).font = FONT_BOLD
        ws_stone.cell(row=r_idx, column=7).number_format = '0.00'
        ws_stone.cell(row=r_idx, column=8, value=total_stone).font = FONT_BOLD
        ws_stone.cell(row=r_idx, column=8).number_format = '0.00'
        ws_stone.cell(row=r_idx, column=9, value=total_shutter).font = FONT_BOLD
        ws_stone.cell(row=r_idx, column=9).number_format = '0.00'
        ws_stone.cell(row=r_idx, column=10, value=total_weight).font = FONT_BOLD
        ws_stone.cell(row=r_idx, column=10).number_format = '0.00'
        for col in range(1, 11):
            ws_stone.cell(row=r_idx, column=col).fill = PatternFill(start_color=COLOR_TOTAL_BG, end_color=COLOR_TOTAL_BG, fill_type="solid")
        auto_fit(ws_stone)

    # 8. WALLS (الجدران)
    if should_gen('walls'):
        ws_walls = wb.create_sheet("الجدران")
        setup_sheet(ws_walls, "الجدران")
        headers_walls = [
            "م", "اسم الجدار", "الطبقة", "الطول (م)", "الارتفاع (م)", 
            "المساحة القائمة (م²)", "الخصومات (م²)", "المساحة الصافية (م²)"
        ]
        write_header(ws_walls, headers_walls)
        
        r_idx = 2
        total_wall_len = 0.0
        total_wall_gross = 0.0
        total_wall_deduct = 0.0
        total_wall_net = 0.0
        
        for i, w in enumerate(project.walls, 1):
            name = val(w, 'name', f'Wall{i}')
            layer = val(w, 'layer', '-')
            length = float(val(w, 'length', 0.0) or 0.0)
            height = float(val(w, 'height', 0.0) or 0.0)
            gross = float(val(w, 'gross_area', 0.0) or val(w, 'gross', 0.0) or 0.0)
            if gross == 0 and length > 0 and height > 0:
                gross = length * height
            deduct = float(val(w, 'deduction_area', 0.0) or val(w, 'deduct', 0.0) or 0.0)
            net = float(val(w, 'net_area', 0.0) or val(w, 'net', 0.0) or 0.0)
            if net == 0:
                net = max(0, gross - deduct)
            
            total_wall_len += length
            total_wall_gross += gross
            total_wall_deduct += deduct
            total_wall_net += net
            
            write_row(ws_walls, r_idx, [i, name, layer, length, height, gross, deduct, net])
            r_idx += 1
        
        # Totals row
        ws_walls.cell(row=r_idx, column=2, value="الإجمالي").font = FONT_BOLD
        ws_walls.cell(row=r_idx, column=4, value=total_wall_len).font = FONT_BOLD
        ws_walls.cell(row=r_idx, column=4).number_format = '0.00'
        ws_walls.cell(row=r_idx, column=6, value=total_wall_gross).font = FONT_BOLD
        ws_walls.cell(row=r_idx, column=6).number_format = '0.00'
        ws_walls.cell(row=r_idx, column=7, value=total_wall_deduct).font = FONT_BOLD
        ws_walls.cell(row=r_idx, column=7).number_format = '0.00'
        ws_walls.cell(row=r_idx, column=8, value=total_wall_net).font = FONT_BOLD
        ws_walls.cell(row=r_idx, column=8).number_format = '0.00'
        for col in range(1, 9):
            ws_walls.cell(row=r_idx, column=col).fill = PatternFill(start_color=COLOR_TOTAL_BG, end_color=COLOR_TOTAL_BG, fill_type="solid")
        auto_fit(ws_walls)

    # 9. CEILING TILES (الأسقف المستعارة)
    # Assuming we list all ceilings, user can filter
    if should_gen('ceiling_tiles'):
        ws_ceil = wb.create_sheet("الأسقف المستعارة")
        setup_sheet(ws_ceil, "الأسقف المستعارة")
        headers_ceil = ["م", "الغرفة", "نوع الغرفة", "المساحة (م²)", "ملاحظات"]
        write_header(ws_ceil, headers_ceil)
        
        r_idx = 2
        total_ceil_area = 0.0
        
        for i, r in enumerate(project.rooms, 1):
            name = val(r, 'name', '-')
            room_type = val(r, 'room_type', '[غير محدد]') or '[غير محدد]'
            area = float(val(r, 'area', 0.0) or 0.0)
            # Check if ceramic ceiling exists
            breakdown = val(r, 'ceramic_breakdown', {}) or {}
            c_ceil = float(breakdown.get('ceiling', 0.0) or 0.0)
            
            note = ""
            if c_ceil > 0:
                note = f"يوجد سيراميك سقف ({c_ceil:.2f} م²)"
            
            total_ceil_area += area
                
            write_row(ws_ceil, r_idx, [i, name, room_type, area, note])
            r_idx += 1
        
        # Totals row
        ws_ceil.cell(row=r_idx, column=2, value="الإجمالي").font = FONT_BOLD
        ws_ceil.cell(row=r_idx, column=4, value=total_ceil_area).font = FONT_BOLD
        ws_ceil.cell(row=r_idx, column=4).number_format = '0.00'
        for col in range(1, 6):
            ws_ceil.cell(row=r_idx, column=col).fill = PatternFill(start_color=COLOR_TOTAL_BG, end_color=COLOR_TOTAL_BG, fill_type="solid")
        auto_fit(ws_ceil)

    # 10. FLOOR TILES (بلاط الأرضيات)
    if should_gen('floor_tiles'):
        ws_floor = wb.create_sheet("بلاط الأرضيات")
        setup_sheet(ws_floor, "بلاط الأرضيات")
        headers_floor = ["م", "الغرفة", "نوع الغرفة", "المساحة (م²)", "سيراميك أرضية؟", "ملاحظات"]
        write_header(ws_floor, headers_floor)
        
        r_idx = 2
        total_floor = 0.0
        total_cer_floor = 0.0
        
        for i, r in enumerate(project.rooms, 1):
            name = val(r, 'name', '-')
            room_type = val(r, 'room_type', '[غير محدد]') or '[غير محدد]'
            area = float(val(r, 'area', 0.0) or 0.0)
            
            breakdown = val(r, 'ceramic_breakdown', {}) or {}
            c_floor = float(breakdown.get('floor', 0.0) or 0.0)
            
            has_cer = "نعم" if c_floor > 0 else "لا"
            note = f"سيراميك: {c_floor:.2f} م²" if c_floor > 0 else ""
            
            total_floor += area
            total_cer_floor += c_floor
                
            write_row(ws_floor, r_idx, [i, name, room_type, area, has_cer, note])
            r_idx += 1
        
        # Totals row
        ws_floor.cell(row=r_idx, column=2, value="الإجمالي").font = FONT_BOLD
        ws_floor.cell(row=r_idx, column=4, value=total_floor).font = FONT_BOLD
        ws_floor.cell(row=r_idx, column=4).number_format = '0.00'
        ws_floor.cell(row=r_idx, column=6, value=f"إجمالي السيراميك: {total_cer_floor:.2f} م²").font = FONT_BOLD
        for col in range(1, 7):
            ws_floor.cell(row=r_idx, column=col).fill = PatternFill(start_color=COLOR_TOTAL_BG, end_color=COLOR_TOTAL_BG, fill_type="solid")
            ws_floor.cell(row=r_idx, column=col).border = BORDER_THIN
        auto_fit(ws_floor)

    # Remove default sheet if it's still there and empty (only if we created others)
    if len(wb.sheetnames) > 1 and 'Sheet' in wb.sheetnames:
        try:
            wb.remove(wb['Sheet'])
        except:
            pass

    # Save
    try:
        wb.save(filepath)
        if status_cb:
            status_cb(f"تم حفظ الملف: {filepath}", "✅")
        return True
    except Exception as e:
        if status_cb:
            status_cb(f"خطأ في الحفظ: {e}", "❌")
        return False

