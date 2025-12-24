"""
PDF Export Module
=================
Export project data to PDF format with professional formatting.
"""

from datetime import datetime
from tkinter import filedialog, messagebox
from typing import List, Dict, Any, Callable, Tuple, Optional

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


from bilind.models.project import Project


def export_to_pdf(
    project: Project,
    fmt_func: Callable[[Optional[float], int], str],
    calculate_cost_func: Callable[[], Tuple[float, List[Dict[str, Any]]]],
    colors_dict: Dict[str, str],
    status_callback: Optional[Callable[[str, str], None]] = None
) -> bool:
    """
    Export all project data to PDF file with formatting.
    
    Args:
        project: The project data object.
        fmt_func: Function to format numbers (value, digits) -> str
        calculate_cost_func: Function that returns (total_cost, cost_details)
        colors_dict: Dictionary of color codes for styling
        status_callback: Optional callback for status updates (message, icon)
    
    Returns:
        bool: True if export successful, False otherwise
    """
    if not HAS_REPORTLAB:
        messagebox.showerror(
            "Missing Dependency",
            "ReportLab is required for PDF export. Please run: pip install reportlab"
        )
        if status_callback:
            status_callback("PDF export failed: missing reportlab.", "❌")
        return False
    
    if status_callback:
        status_callback("Generating PDF report...", "📕")
    
    filename = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF Document", "*.pdf")],
        initialfile=f"BILIND_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
    )
    
    if not filename:
        if status_callback:
            status_callback("PDF export cancelled.", "🚫")
        return False
    
    try:
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        story.append(Paragraph("BILIND Project Summary", styles['Title']))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles['Normal']
        ))
        story.append(Spacer(1, 0.3 * inch))
        
        def add_section(title, headers, data_rows):
            """Add a formatted section to the PDF."""
            if not data_rows:
                return
            story.append(Paragraph(title, styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
            
            table_data = [headers] + data_rows
            t = Table(table_data, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(colors_dict['accent'])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(colors_dict['bg_card'])),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor(colors_dict['text_primary'])),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(colors_dict['border']))
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3 * inch))
        
        # Helpers for dict/dataclass access
        def val(obj, dkey, attr, default=None):
            if isinstance(obj, dict):
                return obj.get(dkey, default)
            return getattr(obj, attr, default)

        # Helper for openings lookup
        openings_by_name: Dict[str, Any] = {}
        for d in project.doors:
            n = val(d, 'name', 'name')
            if n:
                openings_by_name[n] = d
        for w in project.windows:
            n = val(w, 'name', 'name')
            if n:
                openings_by_name[n] = w

        def room_openings_area(room) -> float:
            ids = getattr(room, 'opening_ids', None)
            if ids is None and isinstance(room, dict):
                ids = room.get('opening_ids', [])
            ids = ids or []
            total = 0.0
            for oid in ids:
                o = openings_by_name.get(oid)
                if o is None:
                    continue
                total += float(val(o, 'area', 'area', 0.0) or 0.0)
            return total

        def room_doors_width(room) -> float:
            ids = getattr(room, 'opening_ids', None)
            if ids is None and isinstance(room, dict):
                ids = room.get('opening_ids', [])
            ids = ids or []
            total = 0.0
            for oid in ids:
                o = openings_by_name.get(oid)
                if o is None:
                    continue
                # heuristics for door
                if isinstance(o, dict):
                    is_window = (o.get('glass', 0.0) or 0.0) > 0
                    is_door = not is_window
                    w = float(o.get('w', 0.0) or 0.0)
                    qty = int(o.get('qty', 1) or 1)
                else:
                    typ = getattr(o, 'opening_type', None)
                    is_door = (typ == 'DOOR')
                    w = float(getattr(o, 'width', 0.0) or 0.0)
                    qty = int(getattr(o, 'quantity', 1) or 1)
                if is_door:
                    total += w * qty
            return total

        # Rooms Data
        if project.rooms:
            room_headers = ["Name", "Layer", "W×L (m)", "Perim (m)", "Area (m²)", "Ht (m)", "Ceramic", "Plaster", "Paint"]
            room_rows = []
            for r in project.rooms:
                name = val(r, 'name', 'name', '-')
                layer = val(r, 'layer', 'layer', '-')
                w = val(r, 'w', 'width', None)
                l = val(r, 'l', 'length', None)
                p = val(r, 'perim', 'perimeter', None)
                a = val(r, 'area', 'area', None)
                wall_h = val(r, 'wall_height', 'wall_height', None)
                ceramic = val(r, 'ceramic_area', 'ceramic_area', None)
                plaster = val(r, 'plaster_area', 'plaster_area', None)
                paint = val(r, 'paint_area', 'paint_area', None)
                room_rows.append([
                    name,
                    layer,
                    f"{fmt_func(w, 2)}×{fmt_func(l, 2)}",
                    fmt_func(p, 2),
                    fmt_func(a, 2),
                    fmt_func(wall_h, 2),
                    fmt_func(ceramic, 2),
                    fmt_func(plaster, 2),
                    fmt_func(paint, 2)
                ])
            add_section("📐 Rooms", room_headers, room_rows)
        
        # Doors Data
        if project.doors:
            door_headers = ["Name", "Type", "Qty", "W×H (m)", "Stone (lm)", "Area (m²)", "Steel (kg)"]
            door_rows = []
            for d in project.doors:
                name = val(d, 'name', 'name', '-')
                typ = val(d, 'type', 'material_type', '-')
                qty = val(d, 'qty', 'quantity', 0)
                w = val(d, 'w', 'width', None)
                h = val(d, 'h', 'height', None)
                stone = val(d, 'stone', 'stone_linear', None)
                area = val(d, 'area', 'area', None)
                weight = val(d, 'weight', 'weight', None)  # may be None for dataclasses
                door_rows.append([
                    name,
                    typ,
                    qty,
                    f"{fmt_func(w, 2)}×{fmt_func(h, 2)}",
                    fmt_func(stone, 2),
                    fmt_func(area, 2),
                    fmt_func(weight, 1)
                ])
            add_section("🚪 Doors", door_headers, door_rows)
        
        # Windows Data
        if project.windows:
            win_headers = ["Name", "Type", "Qty", "W×H (m)", "Stone (lm)", "Glass (m²)"]
            win_rows = []
            for w in project.windows:
                name = val(w, 'name', 'name', '-')
                typ = val(w, 'type', 'material_type', '-')
                qty = val(w, 'qty', 'quantity', 0)
                width = val(w, 'w', 'width', None)
                height = val(w, 'h', 'height', None)
                stone = val(w, 'stone', 'stone_linear', None)
                # glass may be stored or computed
                if isinstance(w, dict):
                    glass = w.get('glass', None)
                else:
                    try:
                        glass = float(getattr(w, 'calculate_glass_area')())
                    except Exception:
                        glass = None
                win_rows.append([
                    name,
                    typ,
                    qty,
                    f"{fmt_func(width, 2)}×{fmt_func(height, 2)}",
                    fmt_func(stone, 2),
                    fmt_func(glass, 2)
                ])
            add_section("🪟 Windows", win_headers, win_rows)
        
        # Walls Data
        if project.walls:
            wall_headers = ["Name", "L×H (m)", "Gross (m²)", "Deduct (m²)", "Net (m²)"]
            wall_rows = []
            for w in project.walls:
                name = val(w, 'name', 'name', '-')
                length = val(w, 'length', 'length', None)
                height = val(w, 'height', 'height', None)
                gross = val(w, 'gross', 'gross_area', None)
                deduct = val(w, 'deduct', 'deduction_area', None)
                net = val(w, 'net', 'net_area', None)
                wall_rows.append([
                    name,
                    f"{fmt_func(length, 2)}×{fmt_func(height, 2)}",
                    fmt_func(gross, 2),
                    fmt_func(deduct, 2),
                    fmt_func(net, 2)
                ])
            add_section("🧱 Walls", wall_headers, wall_rows)
        
        # Finishes Data
        all_finishes = [
            ('Plaster', project.plaster_items),
            ('Paint', project.paint_items),
            ('Tiles', project.tiles_items)
        ]
        if any(f[1] for f in all_finishes):
            # Align with Excel export: Description + Area (m²)
            finish_headers = ["Type", "Description", "Area", "Unit"]
            finish_rows = []
            for f_type, f_items in all_finishes:
                if not f_items:
                    continue
                for item in f_items:
                    if isinstance(item, dict):
                        desc = item.get('desc', '-')
                        area = item.get('area', 0.0)
                    else:
                        desc = getattr(item, 'description', '-')
                        area = getattr(item, 'area', 0.0)
                    finish_rows.append([
                        f_type,
                        desc,
                        fmt_func(area, 2),
                        'm²'
                    ])
            add_section("🎨 Finishes", finish_headers, finish_rows)
        
        # Area Book (دفتر المساحة)
        if project.rooms:
            ab_headers = [
                "Room", "Layer", "Perim (m)", "Height (m)", "Floor (m²)",
                "Openings (m²)", "Walls Gross (m²)", "Walls Net (m²)",
                "Baseboards (m)", "Door Width (m)"
            ]
            default_h = getattr(project, 'default_wall_height', 3.0)
            ab_rows = []
            for r in project.rooms:
                name = val(r, 'name', 'name', '-')
                layer = val(r, 'layer', 'layer', '-')
                perim = float(val(r, 'perim', 'perimeter', 0.0) or 0.0)
                floor = float(val(r, 'area', 'area', 0.0) or 0.0)
                open_area = room_openings_area(r)
                walls_gross = perim * default_h
                walls_net = max(0.0, walls_gross - open_area)
                doors_width = room_doors_width(r)
                baseboards = max(0.0, perim - doors_width)
                ab_rows.append([
                    name,
                    layer,
                    fmt_func(perim, 2),
                    fmt_func(default_h, 2),
                    fmt_func(floor, 2),
                    fmt_func(open_area, 2),
                    fmt_func(walls_gross, 2),
                    fmt_func(walls_net, 2),
                    fmt_func(baseboards, 2),
                    fmt_func(doors_width, 2)
                ])
            add_section("📓 Area Book", ab_headers, ab_rows)

        # Cost Estimation Data
        total_cost, cost_details = calculate_cost_func()
        if total_cost > 0:
            cost_headers = ["Item", "Quantity", "Unit", "Cost/Unit", "Total"]
            cost_rows = [[
                item['item'],
                f"{item['qty']:.2f}",
                item['unit'],
                f"{item['cost']:.2f}",
                f"{item['total']:.2f}"
            ] for item in cost_details]
            cost_rows.append(['', '', '', 'TOTAL', f"{total_cost:.2f}"])
            add_section("💰 Cost Estimation", cost_headers, cost_rows)
        
        doc.build(story)
        
        if status_callback:
            import os
            status_callback(f"PDF report saved: {os.path.basename(filename)}", "✅")
        
        messagebox.showinfo("Success", f"Successfully exported PDF report to:\n{filename}")
        return True
        
    except Exception as e:
        messagebox.showerror("Export Error", f"An unexpected error occurred during PDF export:\n{e}")
        if status_callback:
            status_callback("PDF export failed.", "❌")
        return False
