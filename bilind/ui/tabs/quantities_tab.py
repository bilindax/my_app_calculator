"""
Quantities Tab
==============
Consolidated view of lengths and areas across Rooms, Walls, Doors, and Windows
with quick totals, edit/delete shortcuts, and an option to insert a table into AutoCAD.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, List, Tuple, Dict, Any

from .base_tab import BaseTab

if TYPE_CHECKING:
    from bilind_main import BilindEnhanced


class QuantitiesTab(BaseTab):
    """Tab that shows a combined ledger of quantities (lengths and areas)."""

    def __init__(self, parent: tk.Widget, app: 'BilindEnhanced'):
        super().__init__(parent, app)
        self.rows: List[Tuple[str, str, float, float, str, int]] = []  # (category, name, length, area, layer, source_index)
        self.tree: ttk.Treeview | None = None
        self.total_length_var = tk.StringVar(value="0.00 m")
        self.total_area_var = tk.StringVar(value="0.00 m²")
        self.category_var = tk.StringVar(value="[All]")
        self.search_var = tk.StringVar(value="")

    def create(self) -> tk.Frame:
        frame = ttk.Frame(self.parent, style='Main.TFrame')

        # Header
        self._create_header(frame)

        # Toolbar
        self._create_toolbar(frame)

        # Table
        self._create_table(frame)

        # Footer totals
        self._create_footer(frame)

        # Initial load
        self.refresh_data()
        return frame

    def _create_header(self, parent):
        hero = ttk.Frame(parent, style='Hero.TFrame', padding=(18, 20))
        hero.pack(fill=tk.X, padx=16, pady=(16, 8))

        ttk.Label(hero, text="📏 Quantities (Lengths & Areas)", style='HeroHeading.TLabel').pack(anchor=tk.W)
        ttk.Label(hero, text="Quick overview of all elements with totals, edit/delete shortcuts, and AutoCAD table export.", style='HeroSubheading.TLabel').pack(anchor=tk.W, pady=(6, 0))

    def _create_toolbar(self, parent):
        bar = ttk.Frame(parent, style='Toolbar.TFrame', padding=(12, 10))
        bar.pack(fill=tk.X, padx=16, pady=(0, 8))

        # Category filter
        ttk.Label(bar, text="Category:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(0, 6))
        self.category_combo = ttk.Combobox(
            bar,
            textvariable=self.category_var,
            state='readonly',
            width=16,
            values=['[All]', 'Rooms', 'Walls', 'Doors', 'Windows']
        )
        self.category_combo.pack(side=tk.LEFT)
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filter())

        # Search
        ttk.Label(bar, text="  🔍 Search:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(12, 6))
        search_entry = ttk.Entry(bar, textvariable=self.search_var, width=26)
        search_entry.pack(side=tk.LEFT)
        search_entry.bind('<KeyRelease>', lambda e: self._apply_filter())

        self.create_button(bar, "❌ Clear", self._clear_filter, 'Small.TButton', width=120, height=36).pack(side=tk.LEFT, padx=6)

        # Actions
        self.create_button(bar, "✏️ Edit", self._edit_selected, 'Secondary.TButton').pack(side=tk.RIGHT, padx=4)
        self.create_button(bar, "🗑️ Delete", self._delete_selected, 'Danger.TButton').pack(side=tk.RIGHT, padx=4)

        self.create_button(bar, "📘 دفتر الكميات الشامل", self._export_comprehensive_book, 'Accent.TButton').pack(side=tk.RIGHT, padx=6)
        self.create_button(bar, "📑 دفتر المساحة الموحد", self._export_master_sheet, 'Accent.TButton').pack(side=tk.RIGHT, padx=6)
        self.create_button(bar, "📊 Insert Table to AutoCAD", self._insert_table_to_autocad, 'Accent.TButton').pack(side=tk.RIGHT, padx=6)

    def _create_table(self, parent):
        table_frame = ttk.Frame(parent, style='Main.TFrame', padding=(12, 10))
        table_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        columns = ('Category', 'Name', 'Layer', 'Length (m)', 'Area (m²)')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=14, selectmode='browse')

        for col, text, width, anchor in [
            ('Category', 'Category', 110, tk.W),
            ('Name', 'Name', 200, tk.W),
            ('Layer', 'Layer', 120, tk.W),
            ('Length (m)', 'Length (m)', 110, tk.CENTER),
            ('Area (m²)', 'Area (m²)', 110, tk.CENTER),
        ]:
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor=anchor)

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        if hasattr(self.app, 'enhance_treeview'):
            self.app.enhance_treeview(tree)

        self.tree = tree

    def _create_footer(self, parent):
        footer = ttk.Frame(parent, style='Main.TFrame', padding=(12, 6))
        footer.pack(fill=tk.X, padx=16, pady=(0, 16))

        ttk.Label(footer, text="Total Length:", style='Caption.TLabel').pack(side=tk.LEFT)
        ttk.Label(footer, textvariable=self.total_length_var, style='Metrics.TLabel').pack(side=tk.LEFT, padx=(6, 16))

        ttk.Label(footer, text="Total Area:", style='Caption.TLabel').pack(side=tk.LEFT)
        ttk.Label(footer, textvariable=self.total_area_var, style='Metrics.TLabel').pack(side=tk.LEFT, padx=(6, 16))
        
        # Add finish calculations summary using UnifiedCalculator
        ttk.Separator(footer, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=12)
        
        self.plaster_total_var = tk.StringVar(value="0.00 m²")
        self.paint_total_var = tk.StringVar(value="0.00 m²")
        self.ceramic_total_var = tk.StringVar(value="0.00 m²")
        
        ttk.Label(footer, text="محارة:", style='Caption.TLabel', foreground='#4CAF50').pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(footer, textvariable=self.plaster_total_var, style='Metrics.TLabel', foreground='#4CAF50').pack(side=tk.LEFT, padx=(0, 12))
        
        ttk.Label(footer, text="دهان:", style='Caption.TLabel', foreground='#2196F3').pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(footer, textvariable=self.paint_total_var, style='Metrics.TLabel', foreground='#2196F3').pack(side=tk.LEFT, padx=(0, 12))
        
        ttk.Label(footer, text="سيراميك:", style='Caption.TLabel', foreground='#FF9800').pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(footer, textvariable=self.ceramic_total_var, style='Metrics.TLabel', foreground='#FF9800').pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(footer, text="Tip: Double-click an item to edit it.", style='Caption.TLabel').pack(side=tk.RIGHT)

        # Double-click edit binding
        if self.tree:
            self.tree.bind('<Double-1>', lambda e: self._edit_selected())

    # Data & filtering
    def refresh_data(self):
        self.rows = self._build_rows()
        self._apply_filter()

    def _build_rows(self) -> List[Tuple[str, str, float, float, str, int]]:
        rows: List[Tuple[str, str, float, float, str, int]] = []
        app = self.app
        # Rooms
        for idx, r in enumerate(app.project.rooms):
            if isinstance(r, dict):
                name = r.get('name', f'Room{idx+1}')
                layer = r.get('layer', '')
                perim = float(r.get('perim', 0.0) or 0.0)
                area = float(r.get('area', 0.0) or 0.0)
            else:
                name = getattr(r, 'name', f'Room{idx+1}')
                layer = getattr(r, 'layer', '')
                perim = float(getattr(r, 'perimeter', 0.0) or 0.0)
                area = float(getattr(r, 'area', 0.0) or 0.0)
            rows.append(('Rooms', name, perim, area, layer, idx))

        # Walls (Global)
        for idx, w in enumerate(app.project.walls):
            if isinstance(w, dict):
                name = w.get('name', f'Wall{idx+1}')
                layer = w.get('layer', '')
                length = float(w.get('length', 0.0) or 0.0)
                area = float(w.get('net', w.get('gross', 0.0)) or 0.0)
            else:
                name = getattr(w, 'name', f'Wall{idx+1}')
                layer = getattr(w, 'layer', '')
                length = float(getattr(w, 'length', 0.0) or 0.0)
                area = float(getattr(w, 'net_area', getattr(w, 'gross_area', 0.0)) or 0.0)
            rows.append(('Walls', name, length, area, layer, idx))

        # Walls (Room-specific)
        for r_idx, r in enumerate(app.project.rooms):
            if hasattr(r, 'walls') and r.walls:
                room_name = getattr(r, 'name', f'Room{r_idx+1}')
                for w_idx, w in enumerate(r.walls):
                    name = f"{w.name} ({room_name})"
                    layer = w.layer
                    length = w.length
                    area = w.net_area if w.net_area is not None else w.gross_area
                    # Use a special index format or just -1 to indicate it's not in the global list
                    # For now, we won't support direct editing of room walls from here easily without more complex logic
                    rows.append(('Walls', name, length, area, layer, -1))

        # Doors
        for idx, d in enumerate(app.project.doors):
            if isinstance(d, dict):
                name = d.get('name', f'Door{idx+1}')
                layer = d.get('layer', '')
                length = float(d.get('perim', 0.0) or 0.0)
                area = float(d.get('area', 0.0) or 0.0)
            else:
                od = d.to_dict()
                name = od.get('name', f'Door{idx+1}')
                layer = od.get('layer', '')
                length = float(od.get('perim', 0.0) or 0.0)
                area = float(od.get('area', 0.0) or 0.0)
            rows.append(('Doors', name, length, area, layer, idx))

        # Windows
        for idx, w in enumerate(app.project.windows):
            if isinstance(w, dict):
                name = w.get('name', f'Window{idx+1}')
                layer = w.get('layer', '')
                length = float(w.get('perim', 0.0) or 0.0)
                area = float(w.get('area', 0.0) or 0.0)
            else:
                wd = w.to_dict()
                name = wd.get('name', f'Window{idx+1}')
                layer = wd.get('layer', '')
                length = float(wd.get('perim', 0.0) or 0.0)
                area = float(wd.get('area', 0.0) or 0.0)
            rows.append(('Windows', name, length, area, layer, idx))

        return rows

    def _apply_filter(self):
        if not self.tree:
            return
        cat = self.category_var.get()
        query = (self.search_var.get() or '').lower().strip()

        # Clear
        self.tree.delete(*self.tree.get_children())

        # Filter
        filtered = [r for r in self.rows if (cat == '[All]' or r[0] == cat)]
        if query:
            filtered = [r for r in filtered if query in f"{r[0]} {r[1]} {r[4]}".lower()]

        # Insert
        total_length = 0.0
        total_area = 0.0
        for i, (category, name, length, area, layer, source_idx) in enumerate(filtered):
            values = (category, name, layer, self.app._fmt(length, digits=self.app.project.decimal_precision_length), self.app._fmt(area, digits=self.app.project.decimal_precision_area))
            iid = self.tree.insert('', tk.END, values=values)
            # store metadata
            self.tree.set(iid, 'Category', category)
            self.tree.set(iid, 'Name', name)
            self.tree.set(iid, 'Layer', layer)
            # attach hidden mapping via tags dict
            self.tree.item(iid, tags=(f"src_{category}_{source_idx}",))
            total_length += length or 0.0
            total_area += area or 0.0

        self.total_length_var.set(f"{total_length:.2f} m")
        self.total_area_var.set(f"{total_area:.2f} m²")
        
        # Calculate finish totals using UnifiedCalculator
        try:
            from bilind.calculations.unified_calculator import UnifiedCalculator
            calc = UnifiedCalculator(self.app.project)
            totals = calc.calculate_totals()
            
            self.plaster_total_var.set(f"{totals['plaster_total']:.2f} m²")
            self.paint_total_var.set(f"{totals['paint_total']:.2f} m²")
            self.ceramic_total_var.set(f"{totals['ceramic_total']:.2f} m²")
        except Exception as e:
            # Fallback to zeros if calculation fails
            self.plaster_total_var.set("0.00 m²")
            self.paint_total_var.set("0.00 m²")
            self.ceramic_total_var.set("0.00 m²")

    def _clear_filter(self):
        self.category_var.set('[All]')
        self.search_var.set('')
        self._apply_filter()

    # Actions
    def _parse_selection(self) -> Tuple[str, int] | None:
        if not self.tree:
            return None
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select an item first.")
            return None
        tag = next(iter(self.tree.item(sel[0], 'tags') or []), '')
        try:
            _, category, idx = tag.split('_', 2)
            return category, int(idx)
        except Exception:
            return None

    def _edit_selected(self):
        parsed = self._parse_selection()
        if not parsed:
            return
        category, idx = parsed
        # Select item in source tree and call edit methods
        if category == 'Rooms':
            tree = self.app.rooms_tab.rooms_tree
            self._select_index(tree, idx)
            self.app.edit_room()
        elif category == 'Walls':
            tree = self.app.walls_tab.walls_tree
            self._select_index(tree, idx)
            self.app.edit_wall()
        elif category == 'Doors':
            tree = self.app.rooms_tab.doors_tree
            self._select_index(tree, idx)
            self.app.edit_opening('DOOR')
        elif category == 'Windows':
            tree = self.app.rooms_tab.windows_tree
            self._select_index(tree, idx)
            self.app.edit_opening('WINDOW')

    def _delete_selected(self):
        parsed = self._parse_selection()
        if not parsed:
            return
        category, idx = parsed
        if category == 'Rooms':
            if not messagebox.askyesno("Confirm", "Delete selected room?"):
                return
            del self.app.project.rooms[idx]
            self.app.refresh_rooms()
        elif category == 'Walls':
            if not messagebox.askyesno("Confirm", "Delete selected wall?"):
                return
            del self.app.project.walls[idx]
            self.app.refresh_walls()
        elif category == 'Doors':
            if not messagebox.askyesno("Confirm", "Delete selected door?"):
                return
            # Cascade: remove from rooms + walls + quantities
            if hasattr(self.app, 'delete_opening_at_index'):
                self.app.delete_opening_at_index('DOOR', idx, confirm=False)
            else:
                del self.app.project.doors[idx]
                self.app.refresh_openings()
        elif category == 'Windows':
            if not messagebox.askyesno("Confirm", "Delete selected window?"):
                return
            # Cascade: remove from rooms + walls + quantities
            if hasattr(self.app, 'delete_opening_at_index'):
                self.app.delete_opening_at_index('WINDOW', idx, confirm=False)
            else:
                del self.app.project.windows[idx]
                self.app.refresh_openings()
        self.refresh_data()
        self.app.update_status("Item deleted", icon="🗑️")

    def _select_index(self, tree: ttk.Treeview, idx: int):
        # Ensure tree has all items (clear filters when possible)
        try:
            # Rooms filters
            if tree is getattr(self.app.rooms_tab, 'rooms_tree', None):
                self.app.rooms_tab._clear_filter(self.app.rooms_tab.rooms_filter, tree, 'rooms', self.app.project.rooms)
            elif tree is getattr(self.app.rooms_tab, 'doors_tree', None):
                self.app.rooms_tab._clear_filter(self.app.rooms_tab.doors_filter, tree, 'doors', self.app.project.doors)
            elif tree is getattr(self.app.rooms_tab, 'windows_tree', None):
                self.app.rooms_tab._clear_filter(self.app.rooms_tab.windows_filter, tree, 'windows', self.app.project.windows)
            elif tree is getattr(self.app.walls_tab, 'walls_tree', None):
                # walls tab has its own clear
                self.app.walls_tab._clear_walls_filter()
        except Exception:
            pass

        children = tree.get_children()
        if not children:
            return
        idx = max(0, min(idx, len(children) - 1))
        target = children[idx]
        tree.selection_set(target)
        tree.see(target)

    def _insert_table_to_autocad(self):
        # Validate AutoCAD availability
        acad = getattr(self.app, 'acad', None)
        doc = getattr(self.app, 'doc', None)
        if not acad or not doc:
            messagebox.showwarning("AutoCAD Not Available", "AutoCAD must be running with a drawing open.")
            return

        # Build table data from filtered view
        items = []
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, 'values')
            items.append(list(vals))
        if not items:
            messagebox.showinfo("No Data", "There are no quantities to insert.")
            return

        # Prepend header
        data = [["Category", "Name", "Layer", "Length (m)", "Area (m²)"]] + items

        # Ask for insertion point and insert table via COM
        try:
            import win32com.client
            import pythoncom
            self.app.root.withdraw()
            acad.prompt("Pick insertion point for quantities table:")
            p = doc.Utility.GetPoint()
            insertion_point = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, p)
        except Exception as e:
            self.app.root.deiconify()
            messagebox.showerror("AutoCAD", f"Failed to get insertion point.\n{e}")
            return
        finally:
            try:
                self.app.root.deiconify()
            except Exception:
                pass

        # Create the table
        try:
            row_h = 8.0 * float(getattr(self.app.project, 'scale', 1.0) or 1.0)
            col_w = 40.0 * float(getattr(self.app.project, 'scale', 1.0) or 1.0)
            rows = len(data) + 1  # +1 for title row
            cols = len(data[0])

            table = doc.ModelSpace.AddTable(insertion_point, rows, cols, row_h, col_w)
            # Title row
            table.SetText(0, 0, "BILIND Quantities")
            table.MergeCells(0, 0, 0, cols - 1)

            # Header row style
            # Fill header row
            for c, header in enumerate(data[0]):
                table.SetText(1, c, str(header))

            # Body
            for r, row in enumerate(data[1:], start=2):
                for c, value in enumerate(row):
                    table.SetText(r, c, str(value))

            messagebox.showinfo("Success", "Quantities table inserted into AutoCAD.")
            self.app.update_status("Quantities table inserted into AutoCAD", icon="📊")
        except Exception as e:
            messagebox.showerror("AutoCAD", f"Failed to create table.\n{e}")

    def _select_sheets_dialog(self) -> List[str] | None:
        """Show a dialog to select which sheets to export."""
        dialog = tk.Toplevel(self.parent.winfo_toplevel())
        dialog.title("Select Sheets - اختر الصفحات")
        dialog.geometry("400x550")
        dialog.transient(self.parent.winfo_toplevel())
        dialog.grab_set()
        
        # Center
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'+{x}+{y}')

        ttk.Label(dialog, text="Select sheets to generate:", font=('Segoe UI', 10, 'bold')).pack(pady=15)

        sheet_options = [
            ('summary', 'Summary & Dashboard (الملخص)'),
            ('rooms', 'Room Details (تفاصيل الغرف)'),
            ('plaster', 'Plaster Works (اللياسة)'),
            ('ceramic', 'Ceramic Works (السيراميك)'),
            ('paint', 'Paint Works (الدهانات)'),
            ('openings', 'Openings (الأبواب والشبابيك)'),
            ('baseboards', 'Baseboards (النعلات)'),
            ('stone', 'Stone Works (الحجر)'),
            ('walls', 'Masonry/Walls (المباني)'),
            ('ceiling_tiles', 'Ceiling Tiles (بلاط الأسقف)'),
            ('floor_tiles', 'Floor Tiles (بلاط الأرضيات)'),
        ]

        vars_dict = {}
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=5)

        # Select All
        all_var = tk.BooleanVar(value=True)
        def toggle_all():
            for k in vars_dict:
                vars_dict[k].set(all_var.get())
        
        ttk.Checkbutton(frame, text="Select All (تحديد الكل)", variable=all_var, command=toggle_all).pack(anchor='w', pady=(0, 10))
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=5)

        for key, label in sheet_options:
            var = tk.BooleanVar(value=True)
            vars_dict[key] = var
            ttk.Checkbutton(frame, text=label, variable=var).pack(anchor='w', pady=3)

        result = []
        def on_ok():
            selected = [k for k, v in vars_dict.items() if v.get()]
            if not selected:
                messagebox.showwarning("Warning", "Select at least one sheet.", parent=dialog)
                return
            result.extend(selected)
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', pady=20, padx=20)
        ttk.Button(btn_frame, text="Export", command=on_ok, style='Accent.TButton').pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right', padx=5)

        self.parent.wait_window(dialog)
        return result if result else None

    def _export_comprehensive_book(self):
        """Export the comprehensive Quantity Book with selected sheets."""
        if not self.app.project.rooms:
            messagebox.showinfo("لا توجد غرف", "أضف الغرف أولاً قبل التصدير.")
            return

        # 1. Select Sheets
        selected_sheets = self._select_sheets_dialog()
        if not selected_sheets:
            return

        # 2. Select File Path
        filepath = self.app._ask_save_path('دفتر_الكميات_الشامل.xlsx', 'excel')
        if not filepath:
            return

        try:
            from bilind.export.excel_comprehensive_book import export_comprehensive_book
            export_comprehensive_book(
                self.app.project, 
                filepath, 
                app=self.app, 
                status_cb=self.app.update_status,
                selected_sheets=selected_sheets
            )
            messagebox.showinfo("تم التصدير", f"تم حفظ دفتر الكميات الشامل في:\n{filepath}")
        except Exception as exc:
            messagebox.showerror("فشل التصدير", f"حدث خطأ أثناء التصدير:\n{exc}")

    def _export_master_sheet(self):
        """Export the Master Sheet (Unified View)."""
        if not self.app.project.rooms:
            messagebox.showinfo("لا توجد غرف", "أضف الغرف أولاً قبل التصدير.")
            return

        filepath = self.app._ask_save_path('دفتر_المساحة_الموحد.xlsx', 'excel')
        if not filepath:
            return

        try:
            from bilind.export.master_sheet_export import export_master_sheet
            export_master_sheet(
                self.app.project, 
                filepath, 
                app=self.app, 
                status_cb=self.app.update_status
            )
            messagebox.showinfo("تم التصدير", f"تم حفظ دفتر المساحة الموحد في:\n{filepath}")
        except Exception as exc:
            messagebox.showerror("فشل التصدير", f"حدث خطأ أثناء التصدير:\n{exc}")

