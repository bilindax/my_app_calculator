"""
CSV Export Module
=================
Export project data to CSV format.
"""

import csv
from datetime import datetime
from tkinter import filedialog, messagebox
from typing import List, Dict, Any, Callable

from ..models.project import Project


def export_to_csv(
    project: Project,
    fmt_func: Callable[[float, int], str],
    status_callback: Callable[[str, str], None] = None
) -> bool:
    """
    Export all project data to CSV file.
    
    Args:
        project: The project data object.
        fmt_func: Function to format numbers (value, digits) -> str
        status_callback: Optional callback for status updates (message, icon)
    
    Returns:
        bool: True if export successful, False otherwise
    """
    filename = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV", "*.csv")],
        initialfile=f"bilind_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    
    if not filename:
        return False
    
    try:
        # Unpack data from project
        rooms = project.rooms
        doors = project.doors
        windows = project.windows
        walls = project.walls
        plaster_items = project.plaster_items
        paint_items = project.paint_items
        tiles_items = project.tiles_items
        ceramic_zones = project.ceramic_zones

        # Helpers to support dicts and dataclasses
        def get_val(obj, dict_key: str, attr_name: str, default=None):
            if isinstance(obj, dict):
                return obj.get(dict_key, default)
            return getattr(obj, attr_name, default)

        # Calculate totals (robust to dict/dataclass)
        def door_stone_val(d):
            return get_val(d, 'stone', 'stone_linear', 0.0)

        def door_weight_val(d):
            # Legacy dicts may have 'weight'; dataclass Opening doesn't store weight
            val = get_val(d, 'weight', 'weight', None)
            return 0.0 if val is None else val

        def window_stone_val(w):
            return get_val(w, 'stone', 'stone_linear', 0.0)

        def window_glass_val(w):
            if isinstance(w, dict):
                return w.get('glass', 0.0)
            # Try method; fallback to 0.0
            try:
                return float(w.calculate_glass_area())
            except Exception:
                return 0.0

        door_stone = sum(door_stone_val(d) for d in doors)
        door_weight = sum(door_weight_val(d) for d in doors)
        window_stone = sum(window_stone_val(w) for w in windows)
        window_glass = sum(window_glass_val(w) for w in windows)

        def finish_area_total(items):
            total = 0.0
            for it in items:
                if isinstance(it, dict):
                    total += it.get('area', 0.0)
                else:
                    total += getattr(it, 'area', 0.0)
            return total

        plaster_total = finish_area_total(plaster_items)
        paint_total = finish_area_total(paint_items)
        tiles_total = finish_area_total(tiles_items)

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            # Rooms section
            writer.writerow(["ROOMS"])
            writer.writerow(["Name", "Type", "Layer", "Width (m)", "Length (m)", "Perimeter (m)", "Area (m²)", "Wall H (m)", "Wall Finish (m²)", "Ceiling (m²)", "Ceramic (m²)", "Plaster (m²)", "Paint (m²)"])
            for r in rooms:
                name = get_val(r, 'name', 'name', '-')
                r_type = get_val(r, 'room_type', 'room_type', '[Not Set]')
                layer = get_val(r, 'layer', 'layer', '-')
                width = get_val(r, 'w', 'width', None)
                length = get_val(r, 'l', 'length', None)
                perim = get_val(r, 'perim', 'perimeter', None)
                area = get_val(r, 'area', 'area', None)
                wall_h = get_val(r, 'wall_height', 'wall_height', None)
                wall_finish = get_val(r, 'wall_finish_area', 'wall_finish_area', None)
                ceiling_finish = get_val(r, 'ceiling_finish_area', 'ceiling_finish_area', None)
                ceramic = get_val(r, 'ceramic_area', 'ceramic_area', None)
                plaster = get_val(r, 'plaster_area', 'plaster_area', None)
                paint = get_val(r, 'paint_area', 'paint_area', None)
                writer.writerow([
                    name,
                    r_type,
                    layer,
                    fmt_func(width, 2),
                    fmt_func(length, 2),
                    fmt_func(perim, 2),
                    fmt_func(area, 2),
                    fmt_func(wall_h, 2),
                    fmt_func(wall_finish, 2),
                    fmt_func(ceiling_finish, 2),
                    fmt_func(ceramic, 2),
                    fmt_func(plaster, 2),
                    fmt_func(paint, 2)
                ])

            # Area Book section (per-room)
            if rooms:
                writer.writerow([])
                writer.writerow(["AREA BOOK (ROOMS)"])
                writer.writerow([
                    "Room", "Type", "Layer", "Perimeter (m)", "Height (m)", "Floor (m²)",
                    "Openings (m²)", "Walls Gross (m²)", "Walls Net (m²)",
                    "Baseboards (m)", "Door Width Deduct (m)", "Ceiling (m²)", "Openings"
                ])

                # Build opening lookup
                def get_v(o, k, a, d=None):
                    return o.get(k, d) if isinstance(o, dict) else getattr(o, a, d)
                openings = {}
                for d_item in doors:
                    n = get_v(d_item, 'name', 'name')
                    if n:
                        openings[n] = d_item
                for w_item in windows:
                    n = get_v(w_item, 'name', 'name')
                    if n:
                        openings[n] = w_item

                default_h = getattr(project, 'default_wall_height', 3.0)
                for r in rooms:
                    name = get_val(r, 'name', 'name', '-')
                    r_type = get_val(r, 'room_type', 'room_type', '[Not Set]')
                    layer = get_val(r, 'layer', 'layer', '-')
                    perim = float(get_val(r, 'perim', 'perimeter', 0.0) or 0.0)
                    floor = float(get_val(r, 'area', 'area', 0.0) or 0.0)
                    room_h = get_val(r, 'wall_height', 'wall_height', None)
                    # opening ids
                    if hasattr(r, 'opening_ids'):
                        ids = getattr(r, 'opening_ids') or []
                    elif isinstance(r, dict):
                        ids = r.get('opening_ids', []) or []
                    else:
                        ids = []
                    # compute opening area and door width deduction
                    open_area = 0.0
                    doors_width = 0.0
                    for oid in ids:
                        o = openings.get(oid)
                        if not o:
                            continue
                        open_area += float(get_v(o, 'area', 'area', 0.0) or 0.0)
                        # determine if door and add width * qty
                        if isinstance(o, dict):
                            is_window = (o.get('glass', 0.0) or 0.0) > 0
                            if not is_window:
                                doors_width += float(o.get('w', 0.0) or 0.0) * int(o.get('qty', 1) or 1)
                        else:
                            if getattr(o, 'opening_type', None) == 'DOOR':
                                doors_width += float(getattr(o, 'width', 0.0) or 0.0) * int(getattr(o, 'quantity', 1) or 1)
                    # Use room-specific height if provided
                    height_used = float(room_h) if room_h else default_h
                    # Balcony multi-segment support (sum of segments if present)
                    segs = get_val(r, 'wall_segments', 'wall_segments', []) or []
                    if segs:
                        gross_segments = 0.0
                        for s in segs:
                            try:
                                gross_segments += float(s.get('length', 0.0) or 0.0) * float(s.get('height', 0.0) or 0.0)
                            except Exception:
                                pass
                        walls_gross = gross_segments
                    else:
                        walls_gross = perim * height_used
                    walls_net = max(0.0, walls_gross - open_area)
                    baseboards_m = max(0.0, perim - doors_width)
                    openings_txt = ','.join(ids) if ids else '-'
                    writer.writerow([
                        name,
                        r_type,
                        layer,
                        f"{perim:.2f}",
                        f"{height_used:.2f}",
                        f"{floor:.2f}",
                        f"{open_area:.2f}",
                        f"{walls_gross:.2f}",
                        f"{walls_net:.2f}",
                        f"{baseboards_m:.2f}",
                        f"{doors_width:.2f}",
                        f"{floor:.2f}",
                        openings_txt
                    ])

            # Doors section
            writer.writerow([])
            writer.writerow(["DOORS"])
            writer.writerow(["Name", "Layer", "Type", "Qty", "Width (m)", "Height (m)", "Stone (lm)", "Area (m²)", "Steel (kg)"])
            for d in doors:
                name = get_val(d, 'name', 'name', '-')
                layer = get_val(d, 'layer', 'layer', '-')
                typ = get_val(d, 'type', 'material_type', '-')
                qty = get_val(d, 'qty', 'quantity', 0)
                width = get_val(d, 'w', 'width', None)
                height = get_val(d, 'h', 'height', None)
                stone = door_stone_val(d)
                area = get_val(d, 'area', 'area', None)
                weight = door_weight_val(d)
                writer.writerow([
                    name,
                    layer,
                    typ,
                    qty,
                    fmt_func(width, 2),
                    fmt_func(height, 2),
                    fmt_func(stone, 2),
                    fmt_func(area, 2),
                    fmt_func(weight, 1)
                ])

            # Windows section
            writer.writerow([])
            writer.writerow(["WINDOWS"])
            writer.writerow(["Name", "Layer", "Type", "Qty", "Width (m)", "Height (m)", "Stone (lm)", "Area (m²)", "Glass (m²)"])
            for w in windows:
                name = get_val(w, 'name', 'name', '-')
                layer = get_val(w, 'layer', 'layer', '-')
                typ = get_val(w, 'type', 'material_type', '-')
                qty = get_val(w, 'qty', 'quantity', 0)
                width = get_val(w, 'w', 'width', None)
                height = get_val(w, 'h', 'height', None)
                stone = window_stone_val(w)
                area = get_val(w, 'area', 'area', None)
                glass = window_glass_val(w)
                writer.writerow([
                    name,
                    layer,
                    typ,
                    qty,
                    fmt_func(width, 2),
                    fmt_func(height, 2),
                    fmt_func(stone, 2),
                    fmt_func(area, 2),
                    fmt_func(glass, 2)
                ])

            # Walls section
            if walls:
                writer.writerow([])
                writer.writerow(["WALLS"])
                writer.writerow(["Name", "Layer", "Length (m)", "Height (m)", "Gross (m²)", "Deduct (m²)", "Net (m²)"])
                for w in walls:
                    name = get_val(w, 'name', 'name', '-')
                    layer = get_val(w, 'layer', 'layer', '-')
                    length = get_val(w, 'length', 'length', None)
                    height = get_val(w, 'height', 'height', None)
                    gross = get_val(w, 'gross', 'gross_area', None)
                    deduct = get_val(w, 'deduct', 'deduction_area', None)
                    net = get_val(w, 'net', 'net_area', None)
                    writer.writerow([
                        name,
                        layer,
                        fmt_func(length, 2),
                        fmt_func(height, 2),
                        fmt_func(gross, 2),
                        fmt_func(deduct, 2),
                        fmt_func(net, 2)
                    ])

            # Stone & Steel summary
            writer.writerow([])
            writer.writerow(["STONE & STEEL SUMMARY"])
            writer.writerow(["Doors stone (lm)", f"{door_stone:.2f}"])
            writer.writerow(["Windows stone (lm)", f"{window_stone:.2f}"])
            writer.writerow(["Steel weight (kg)", f"{door_weight:.1f}"])
            writer.writerow(["Window glass (m²)", f"{window_glass:.2f}"])

            # Finishes section
            writer.writerow([])
            writer.writerow(["FINISHES"])
            writer.writerow(["Type", "Area (m²)"])
            writer.writerow(["Plaster", f"{plaster_total:.2f}"])
            writer.writerow(["Paint", f"{paint_total:.2f}"])
            writer.writerow(["Tiles", f"{tiles_total:.2f}"])

            # Ceramic zones section
            if ceramic_zones:
                writer.writerow([])
                writer.writerow(["CERAMIC WALL ZONES"])
                writer.writerow(["Name", "Category", "Perimeter (m)", "Height (m)", "Area (m²)", "Notes"])
                for zone in ceramic_zones:
                    name = get_val(zone, 'name', 'name', '-')
                    category = get_val(zone, 'category', 'category', '-')
                    perimeter = get_val(zone, 'perimeter', 'perimeter', 0.0)
                    height = get_val(zone, 'height', 'height', 0.0)
                    # area may be property for dataclass or stored in dict
                    area = get_val(zone, 'area', 'area', None)
                    notes = get_val(zone, 'notes', 'notes', '')
                    writer.writerow([
                        name,
                        category,
                        f"{perimeter:.2f}",
                        f"{height:.2f}",
                        f"{(0.0 if area is None else area):.2f}",
                        notes
                    ])
        
        messagebox.showinfo("Success", f"✅ Saved:\n{filename}")
        
        if status_callback:
            import os
            status_callback(f"CSV exported: {os.path.basename(filename)}", "💾")
        
        return True
        
    except Exception as e:
        messagebox.showerror("Export Error", f"Failed to export CSV:\n{e}")
        if status_callback:
            status_callback("CSV export failed", "❌")
        return False
