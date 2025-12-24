"""
AutoCAD Export Module
=====================
Insert summary table into AutoCAD drawing.
"""

from tkinter import messagebox
from typing import List, Dict, Any, Callable, Optional
import win32com.client
import pythoncom


from bilind.models.project import Project


def insert_table_to_autocad(
    project: Project,
    acad: Any,  # Autocad instance
    doc: Any,   # Document instance
    scale: float,
    root_window: Any,  # Tkinter root for hide/show
    status_callback: Optional[Callable[[str, str], None]] = None
) -> bool:
    """
    Insert a summary table into AutoCAD drawing.
    
    Args:
        project: The project data object.
        acad: AutoCAD application instance
        doc: AutoCAD document instance
        scale: Drawing scale factor
        root_window: Tkinter root window to hide/show
        status_callback: Optional callback for status updates (message, icon)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if status_callback:
        status_callback("Generating summary table...", "📊")
    
    try:
        # 1. Compile Data
        data = [["Category", "Item", "Quantity", "Unit"]]
        
        # Rooms
        room_total_area = sum(r.area for r in project.rooms)
        if room_total_area > 0:
            data.append(["Rooms", "Total Area", f"{room_total_area:.2f}", "m²"])
        
        # Doors
        if project.doors:
            door_count = sum(d.quantity for d in project.doors)
            door_stone = sum(d.stone for d in project.doors)
            door_weight = sum(d.weight for d in project.doors)
            data.append(["Doors", "Total Count", str(door_count), "pcs"])
            if door_stone > 0:
                data.append(["Doors", "Stone (linear)", f"{door_stone:.2f}", "lm"])
            if door_weight > 0:
                data.append(["Doors", "Steel Weight", f"{door_weight:.1f}", "kg"])
        
        # Windows
        if project.windows:
            win_count = sum(w.quantity for w in project.windows)
            win_stone = sum(w.stone for w in project.windows)
            win_glass = sum(w.glass for w in project.windows)
            data.append(["Windows", "Total Count", str(win_count), "pcs"])
            if win_stone > 0:
                data.append(["Windows", "Stone (linear)", f"{win_stone:.2f}", "lm"])
            if win_glass > 0:
                data.append(["Windows", "Glass Area", f"{win_glass:.2f}", "m²"])
        
        # Walls
        if project.walls:
            wall_net_area = sum(w.net_area for w in project.walls)
            if wall_net_area > 0:
                data.append(["Walls", "Net Area", f"{wall_net_area:.2f}", "m²"])
        
        # Finishes
        plaster_total = sum(item.quantity for item in project.plaster_items)
        paint_total = sum(item.quantity for item in project.paint_items)
        tiles_total = sum(item.quantity for item in project.tiles_items)
        if plaster_total > 0:
            data.append(["Finishes", "Plaster", f"{plaster_total:.2f}", "m²"])
        if paint_total > 0:
            data.append(["Finishes", "Paint", f"{paint_total:.2f}", "m²"])
        if tiles_total > 0:
            data.append(["Finishes", "Floor Tiles", f"{tiles_total:.2f}", "m²"])
        
        # Ceramic Zones
        if project.ceramic_zones:
            ceramic_totals = {}
            for zone in project.ceramic_zones:
                category = zone.category
                area = zone.area
                ceramic_totals[category] = ceramic_totals.get(category, 0) + area
            for category, total_area in ceramic_totals.items():
                if total_area > 0:
                    data.append(["Ceramic Walls", category, f"{total_area:.2f}", "m²"])
        
        if len(data) <= 1:
            messagebox.showwarning("No Data", "There is no data to insert into a table.")
            return False
        
        # 2. Get Insertion Point from User
        root_window.withdraw()
        acad.prompt("Select table insertion point:")
        try:
            # Use the more robust GetPoint method with variants
            p1 = doc.Utility.GetPoint()
            insertion_point = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, p1)
        except Exception as e:
            print(f"Could not get point: {e}")
            messagebox.showerror("Error", "Could not get insertion point from AutoCAD.")
            root_window.deiconify()
            return False
        finally:
            root_window.deiconify()
        
        # 3. Create and Populate Table
        num_rows = len(data)
        num_cols = 4
        row_height = 8.0 * scale
        col_width = 40.0 * scale
        
        table = acad.model.AddTable(insertion_point, num_rows, num_cols, row_height, col_width)
        
        # Style the table
        table.SetAlignment(0, -1, 4)  # acMiddleCenter for all cells
        table.SetAlignment(1, -1, 1)  # acTopLeft for title row
        
        table.SetText(0, 0, "BILIND Project Summary")
        table.MergeCells(0, 0, 0, 3)  # Merge title row
        
        for r, row_data in enumerate(data):
            for c, cell_text in enumerate(row_data):
                table.SetText(r + 1, c, str(cell_text))
        
        # Header row style
        table.SetRowType(1, 1)  # acHeaderRow
        
        # 4. Generate and Insert Visual Charts (Better Graphics)
        try:
            from .visual_export import create_room_area_chart, create_finishes_chart
            
            # Chart 1: Room Areas
            chart1_path = create_room_area_chart(project)
            if chart1_path:
                # Position: Right of table
                table_width = num_cols * col_width
                gap = 10.0 * scale
                
                # Calculate insertion point for chart 1
                x, y, z = p1
                c1_x = x + table_width + gap
                c1_y = y
                c1_point = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (c1_x, c1_y, z))
                
                # Insert Raster
                # Scale factor estimation: Image is ~1500px wide. We want it ~table_width (160*scale).
                # 160 / 1500 ≈ 0.1
                image_scale = scale * 0.15
                
                try:
                    acad.model.AddRaster(chart1_path, c1_point, image_scale, 0.0)
                    
                    # Chart 2: Finishes
                    chart2_path = create_finishes_chart(project)
                    if chart2_path:
                        # Position: Right of Chart 1 (approx width 160*scale)
                        c2_x = c1_x + (table_width * 1.2)
                        c2_point = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (c2_x, y, z))
                        acad.model.AddRaster(chart2_path, c2_point, image_scale, 0.0)
                        
                except Exception as raster_err:
                    print(f"AddRaster failed (might not be supported in this AutoCAD version): {raster_err}")
                    
        except Exception as chart_err:
            print(f"Chart generation failed: {chart_err}")

        if status_callback:
            status_callback("✅ Summary table & charts inserted.", "📊")
        
        messagebox.showinfo("Success", "Summary table and visual charts have been inserted.")
        return True
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("AutoCAD Error", f"Failed to create table in AutoCAD.\n\nError: {e}")
        if status_callback:
            status_callback("Error inserting table.", "❌")
        return False
    finally:
        root_window.deiconify()
