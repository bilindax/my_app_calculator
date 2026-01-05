"""
Rooms Tab
=========
UI tab for managing rooms, doors, and windows in the project.
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING
from tkinter import colorchooser
from tkinter import simpledialog

from .base_tab import BaseTab

if TYPE_CHECKING:
    from bilind_main import BilindEnhanced


class RoomsTab(BaseTab):
    """
    Tab for managing rooms, doors, and windows.
    
    Provides:
    - Room picking and management
    - Door/window picking and management
    - Search/filter functionality
    - Calculated metrics display
    """
    
    def __init__(self, parent: tk.Widget, app: 'BilindEnhanced'):
        """Initialize the rooms tab."""
        super().__init__(parent, app)

        # Runtime mapping from Treeview iid -> underlying room record.
        # This avoids relying on visible columns (simple vs advanced view) for lookups.
        self._room_iid_to_record = {}
        
    def create(self) -> tk.Frame:
        """Create and return the configured rooms tab frame."""
        # Header
        self.create_header(
            "BILIND Spaces & Openings",
            "Plan your rooms, doors, and windows with a modern interface and automatically calculated metrics."
        )
        
        # Top controls
        self._create_controls()
        
        # Scrollable content area
        canvas, scrollable_frame = self._create_scrollable_area()
        
        # Rooms section
        self._create_rooms_section(scrollable_frame)
        
        # Doors section
        self._create_doors_section(scrollable_frame)
        
        # Windows section
        self._create_windows_section(scrollable_frame)
        
        return self.frame
    
    def _create_controls(self):
        """Create the top control bar with scale and action buttons."""
        ctrl_frame = ttk.Frame(self.frame, style='Main.TFrame', padding=(12, 12))
        ctrl_frame.pack(fill=tk.X, padx=16, pady=(4, 12))
        
        # Scale input
        ttk.Label(
            ctrl_frame,
            text="Scale",
            foreground=self.colors['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, 6))
        
        self.app.scale_var = tk.StringVar(value="1.0")
        ttk.Entry(
            ctrl_frame,
            textvariable=self.app.scale_var,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Action buttons
        actions = [
            ("📏 Calibrate Scale", self.app.calibrate_scale, 'info'),
            ("🏠 Pick Rooms", self.app.pick_rooms, 'accent'),
            ("🏷️ Pick by Type", self.app.pick_rooms_by_type, 'accent'),
            ("🚪 Pick Doors", self.app.pick_doors, 'accent'),
            ("🪟 Pick Windows", self.app.pick_windows, 'accent'),
            ("🔄 Reset", self.app.reset_all, 'warning'),
            ("📡 Sync", self.app.toggle_sync, 'secondary')
        ]
        
        for text, command, style in actions:
            self.create_button(ctrl_frame, text, command, style).pack(side=tk.LEFT, padx=6)

    def refresh_data(self):
        """Refreshes all treeviews in the tab with the latest data from the app."""
        # Update layer filter options first
        self._update_layer_filters()
        
        # Then refresh the treeviews
        self._filter_treeview(self.rooms_tree, self.rooms_filter.get(), 'rooms', self.app.project.rooms)
        self._filter_treeview(self.doors_tree, self.doors_filter.get(), 'doors', self.app.project.doors)
        self._filter_treeview(self.windows_tree, self.windows_filter.get(), 'windows', self.app.project.windows)
        self.app.update_status("Main tab refreshed.", icon="🔄")
    
    def _update_layer_filters(self):
        """Update layer and room type combobox values from current datasets."""
        # Extract unique layers from rooms
        rooms_layers = set()
        rooms_types = set()
        floors = set()
        for record in self.app.project.rooms:
            layer = record.get('layer') if isinstance(record, dict) else getattr(record, 'layer', None)
            room_type = record.get('room_type', '[Not Set]') if isinstance(record, dict) else getattr(record, 'room_type', '[Not Set]')
            floor_val = record.get('floor', 0) if isinstance(record, dict) else getattr(record, 'floor', 0)
            if layer:
                rooms_layers.add(layer)
            if room_type:
                rooms_types.add(room_type)
            try:
                floors.add(int(floor_val))
            except Exception:
                pass
        
        self.rooms_layer_combo['values'] = ['[All]'] + sorted(rooms_layers)
        
        # Import ROOM_TYPES for room type filter
        from bilind.models.room import ROOM_TYPES
        # Combine standard types with any custom types found in data
        all_types = set(ROOM_TYPES) | rooms_types
        self.rooms_type_combo['values'] = ['[All]'] + sorted([t for t in all_types if t != '[Not Set]']) + ['[Not Set]']

        # Floors filter values (as strings). If combo not created yet, skip.
        if hasattr(self, 'rooms_floor_combo'):
            floor_values = ['[All]'] + [str(f) for f in sorted(floors)]
            self.rooms_floor_combo['values'] = floor_values
        
        # Extract unique layers from doors
        doors_layers = set()
        for record in self.app.project.doors:
            layer = record.get('layer') if isinstance(record, dict) else getattr(record, 'layer', None)
            if layer:
                doors_layers.add(layer)
        self.doors_layer_combo['values'] = ['[All]'] + sorted(doors_layers)
        
        # Extract unique layers from windows
        windows_layers = set()
        for record in self.app.project.windows:
            layer = record.get('layer') if isinstance(record, dict) else getattr(record, 'layer', None)
            if layer:
                windows_layers.add(layer)
        self.windows_layer_combo['values'] = ['[All]'] + sorted(windows_layers)

    def _filter_treeview(self, tree, query, data_key, dataset):
        """Filters a treeview based on search query, layer selection, and room type."""
        query = (query or '').strip().lower()

        # Rebuild mapping for current visible rooms.
        if data_key == 'rooms':
            self._room_iid_to_record = {}
        
        # Get selected layer filter
        selected_layer = None
        selected_type = None
        selected_floor = None
        
        if data_key == 'rooms' and hasattr(self, 'rooms_layer_var'):
            selected_layer = self.rooms_layer_var.get()
            selected_type = self.rooms_type_var.get() if hasattr(self, 'rooms_type_var') else None
            selected_floor = self.rooms_floor_var.get() if hasattr(self, 'rooms_floor_var') else None
        elif data_key == 'doors' and hasattr(self, 'doors_layer_var'):
            selected_layer = self.doors_layer_var.get()
        elif data_key == 'windows' and hasattr(self, 'windows_layer_var'):
            selected_layer = self.windows_layer_var.get()
        
        if selected_layer == "[All]":
            selected_layer = None
        if selected_type == "[All]":
            selected_type = None
        if selected_floor == "[All]":
            selected_floor = None
        
        tree.delete(*tree.get_children())
        for record in dataset:
            
            if data_key == 'rooms':
                values = self._format_room_row(record)
            elif data_key == 'doors':
                values = self._format_door_row(record)
            elif data_key == 'windows':
                values = self._format_window_row(record)
            else:
                continue

            if not values:
                continue
            
            # Get layer for filtering
            record_layer = record.get('layer') if isinstance(record, dict) else getattr(record, 'layer', None)
            
            # Get room type for filtering (rooms only)
            record_type = None
            record_floor = None
            if data_key == 'rooms':
                record_type = record.get('room_type', '[Not Set]') if isinstance(record, dict) else getattr(record, 'room_type', '[Not Set]')
                record_floor = record.get('floor', 0) if isinstance(record, dict) else getattr(record, 'floor', 0)
            
            # Apply layer filter
            if selected_layer and record_layer != selected_layer:
                continue
            
            # Apply room type filter (rooms only)
            if selected_type and record_type != selected_type:
                continue
            # Apply floor filter (rooms only)
            if selected_floor is not None and selected_floor != "[All]":
                try:
                    if int(record_floor) != int(selected_floor):
                        continue
                except Exception:
                    pass
                
            # Apply text search filter
            row_text = ' '.join(str(v).lower() for v in values)
            if not query or query in row_text:
                # Insert row first
                if data_key == 'rooms':
                    iid = f"room_{id(record)}"
                    iid = tree.insert('', tk.END, iid=iid, values=values)
                    self._room_iid_to_record[iid] = record
                else:
                    iid = tree.insert('', tk.END, values=values)
                
                # Build tag list
                tags = []
                
                # Add alternating row tag for styling
                row_index = len(tree.get_children()) - 1
                alt_tag = 'evenrow' if row_index % 2 == 0 else 'oddrow'
                tags.append(alt_tag)
                
                # Add room color tag if applicable
                if data_key == 'rooms':
                    room = record
                    color = None
                    if isinstance(room, dict):
                        color = room.get('color')
                    else:
                        color = getattr(room, 'color', None)
                    
                    if color:
                        color_tag = f"room_color_{color}"
                        if color_tag not in tree.tag_names():
                            tree.tag_configure(color_tag, background=color)
                        tags.append(color_tag)
                
                # Apply all tags at once
                if tags:
                    tree.item(iid, tags=tuple(tags))
        
        # Update totals
        if data_key == 'rooms' and hasattr(self, 'rooms_totals_label'):
            self._update_rooms_totals(tree)
        elif data_key == 'doors' and hasattr(self, 'doors_totals_label'):
            self._update_doors_totals(tree)
        elif data_key == 'windows' and hasattr(self, 'windows_totals_label'):
            self._update_windows_totals(tree)

    def _update_rooms_totals(self, tree):
        """Calculate and display totals for all visible rooms in the treeview."""
        # Get visible rooms from tree mapping
        visible_rooms = []
        for iid in tree.get_children():
            room = self._room_iid_to_record.get(iid)
            if room:
                visible_rooms.append(room)
        
        total_count = len(visible_rooms)
        
        if not visible_rooms:
            totals_text = "📊 الإجمالي: 0 غرفة | المساحة: 0.00 م² | البياض: 0.00 م² | الدهان: 0.00 م²"
            self.rooms_totals_label.config(text=totals_text)
            return
        
        # Use UnifiedCalculator for accurate totals
        from bilind.calculations.unified_calculator import UnifiedCalculator
        from bilind.models.project import Project
        
        # Create temporary project with only visible rooms
        temp_project = Project(
            project_name=self.app.project.project_name,
            rooms=visible_rooms,
            doors=self.app.project.doors,
            windows=self.app.project.windows,
            walls=self.app.project.walls,
            ceramic_zones=self.app.project.ceramic_zones
        )
        
        calc = UnifiedCalculator(temp_project)
        totals = calc.calculate_totals()
        
        # Arabic totals
        totals_text = (
            f"📊 الإجمالي: {total_count} غرفة | "
            f"المساحة: {totals['area_total']:.2f} م² | "
            f"البياض: {totals['plaster_total']:.2f} م² | "
            f"الدهان: {totals['paint_total']:.2f} م²"
        )
        self.rooms_totals_label.config(text=totals_text)

    def _update_doors_totals(self, tree):
        """Calculate and display totals for all visible doors in the treeview."""
        total_count = 0
        total_qty = 0
        total_area = 0.0
        total_weight = 0.0
        total_stone = 0.0
        
        for item in tree.get_children():
            total_count += 1
            values = tree.item(item)['values']
            # Columns: Name(0), Type(1), W(2), H(3), Qty(4), Perim(5), Area(6), Stone(7), Weight(8)
            try:
                qty = int(values[4]) if values[4] != '-' else 1
                total_qty += qty
            except (IndexError, ValueError, TypeError):
                total_qty += 1
            
            try:
                area_val = values[6]
                if area_val != '-':
                    total_area += float(area_val)
            except (IndexError, ValueError, TypeError):
                pass
            
            try:
                stone_val = values[7]
                if stone_val != '-':
                    total_stone += float(stone_val)
            except (IndexError, ValueError, TypeError):
                pass
            
            try:
                weight_val = values[8]
                if weight_val != '-':
                    total_weight += float(weight_val)
            except (IndexError, ValueError, TypeError):
                pass
        
        # Arabic totals
        totals_text = (
            f"📊 الإجمالي: {total_count} نوع ({total_qty} باب) | "
            f"المساحة: {total_area:.2f} م² | "
            f"الحجر: {total_stone:.2f} م.ط | "
            f"الوزن: {total_weight:.1f} كجم"
        )
        self.doors_totals_label.config(text=totals_text)

    def _update_windows_totals(self, tree):
        """Calculate and display totals for all visible windows in the treeview."""
        total_count = 0
        total_qty = 0
        total_glass = 0.0
        total_stone = 0.0
        
        for item in tree.get_children():
            total_count += 1
            values = tree.item(item)['values']
            # Columns: Name(0), Type(1), W(2), H(3), Qty(4), Perim(5), Glass(6), Stone(7)
            try:
                qty = int(values[4]) if values[4] != '-' else 1
                total_qty += qty
            except (IndexError, ValueError, TypeError):
                total_qty += 1
            
            try:
                glass_val = values[6]
                if glass_val != '-':
                    total_glass += float(glass_val)
            except (IndexError, ValueError, TypeError):
                pass
            
            try:
                stone_val = values[7]
                if stone_val != '-':
                    total_stone += float(stone_val)
            except (IndexError, ValueError, TypeError):
                pass
        
        # Arabic totals
        totals_text = (
            f"📊 الإجمالي: {total_count} نوع ({total_qty} شباك) | "
            f"الزجاج: {total_glass:.2f} م² | "
            f"الحجر: {total_stone:.2f} م.ط"
        )
        self.windows_totals_label.config(text=totals_text)

    def _clear_filter(self, entry_widget, tree, data_key, dataset):
        """Clears the filter entry, resets layer and type filters, and refreshes the treeview."""
        entry_widget.delete(0, tk.END)
        
        # Reset layer filter to [All]
        if data_key == 'rooms' and hasattr(self, 'rooms_layer_var'):
            self.rooms_layer_var.set("[All]")
            if hasattr(self, 'rooms_type_var'):
                self.rooms_type_var.set("[All]")
        elif data_key == 'doors' and hasattr(self, 'doors_layer_var'):
            self.doors_layer_var.set("[All]")
        elif data_key == 'windows' and hasattr(self, 'windows_layer_var'):
            self.windows_layer_var.set("[All]")
        
        self._filter_treeview(tree, '', data_key, dataset)

    def _format_room_row(self, record):
        """Formats a room record for the treeview including finish fields."""
        if isinstance(record, dict):
            self.app._ensure_room_names()
            name = record.get('name', '-')
            room_type = record.get('room_type', '[Not Set]')
            floor = record.get('floor', 0)
            layer = record.get('layer', '-')
            width = record.get('w')
            length = record.get('l')
            perimeter = record.get('perim')
            area = record.get('area')
            wall_h = record.get('wall_height')
            wall_finish = record.get('wall_finish_area')
            ceiling = record.get('ceiling_finish_area')
            ceramic = record.get('ceramic_area')
            plaster = record.get('plaster_area')
            paint = record.get('paint_area')
            summary_target = record
        else:
            name = getattr(record, 'name', '-')
            room_type = getattr(record, 'room_type', '[Not Set]')
            floor = getattr(record, 'floor', 0)
            layer = getattr(record, 'layer', '-')
            width = getattr(record, 'width', None)
            length = getattr(record, 'length', None)
            perimeter = getattr(record, 'perimeter', None)
            area = getattr(record, 'area', None)
            wall_h = getattr(record, 'wall_height', None)
            wall_finish = getattr(record, 'wall_finish_area', None)
            ceiling = getattr(record, 'ceiling_finish_area', None)
            ceramic = getattr(record, 'ceramic_area', None)
            plaster = getattr(record, 'plaster_area', None)
            paint = getattr(record, 'paint_area', None)
            summary_target = record

        # Check if we're in simple or advanced view
        is_simple = hasattr(self, 'show_advanced_columns') and not self.show_advanced_columns.get()
        
        if is_simple:
            # Simple view: Name, Type, Area, Plaster, Paint, Openings
            return (
                name,
                room_type,
                self.app._fmt(area),
                self.app._fmt(plaster),
                self.app._fmt(paint),
                self.app.get_room_opening_summary_text(summary_target),
            )
        else:
            # Advanced view: All columns
            return (
                name,
                room_type,
                floor,
                layer,
                self.app.get_room_opening_summary_text(summary_target),
                self.app._fmt(width),
                self.app._fmt(length),
                self.app._fmt(perimeter),
                self.app._fmt(area),
                self.app._fmt(wall_h),
                self.app._fmt(wall_finish),
                self.app._fmt(ceiling),
                self.app._fmt(ceramic),
                self.app._fmt(plaster),
                self.app._fmt(paint)
            )
    
    def _toggle_columns_view(self):
        """Toggle between simple (6 columns) and advanced (15 columns) view."""
        is_advanced = self.show_advanced_columns.get()
        
        # Get current data
        current_data = list(self.app.project.rooms)
        
        # Clear tree
        self.rooms_tree.delete(*self.rooms_tree.get_children())
        
        # Reconfigure columns
        if is_advanced:
            cols = self._advanced_columns
        else:
            cols = self._simple_columns
        
        # Update treeview columns
        self.rooms_tree['columns'] = tuple(c[0] for c in cols)
        
        for col, text, width in cols:
            self.rooms_tree.heading(col, text=text)
            self.rooms_tree.column(col, width=width, anchor=tk.CENTER)
        
        # Refresh data with new format
        self.refresh_data()

    def _format_door_row(self, record):
        """Formats a door record for the treeview."""
        if isinstance(record, dict):
            self.app._ensure_opening_names('DOOR')
            door_dict = record
        else:
            weight = self.app.door_types.get(getattr(record, 'material_type', ''), {}).get('weight', 0)
            door_dict = record.to_dict(weight=weight)
        return (
            door_dict.get('name', '-'),
            door_dict.get('type', '-'),
            self.app._fmt(door_dict.get('w')),
            self.app._fmt(door_dict.get('h')),
            door_dict.get('qty', 1),
            self.app._fmt(door_dict.get('perim')),
            self.app._fmt(door_dict.get('area')),
            self.app._fmt(door_dict.get('stone')),
            self.app._fmt(door_dict.get('weight'), digits=1)
        )

    def _format_window_row(self, record):
        """Formats a window record for the treeview."""
        if isinstance(record, dict):
            self.app._ensure_opening_names('WINDOW')
            window_dict = record
        else:
            window_dict = record.to_dict()
        return (
            window_dict.get('name', '-'),
            window_dict.get('type', '-'),
            self.app._fmt(window_dict.get('w')),
            self.app._fmt(window_dict.get('h')),
            window_dict.get('qty', 1),
            self.app._fmt(window_dict.get('perim')),
            self.app._fmt(window_dict.get('glass')),
            self.app._fmt(window_dict.get('stone'))
        )
    
    def _create_scrollable_area(self):
        """Create and return canvas with scrollable frame."""
        canvas = tk.Canvas(
            self.frame,
            bg=self.colors['bg_primary'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            self.frame,
            orient=tk.VERTICAL,
            command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas, style='Main.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollable components
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 16), pady=(0, 16))
        
        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        return canvas, scrollable_frame
    
    def _create_rooms_section(self, parent):
        """Create the rooms management section."""
        frame = ttk.LabelFrame(
            parent,
            text="📋 Rooms",
            style='Card.TLabelframe',
            padding=(15, 12)
        )
        frame.pack(fill=tk.X, padx=12, pady=8)
        
        # Button bar - Row 1: Basic CRUD operations
        btn_bar1 = ttk.Frame(frame, style='Main.TFrame')
        btn_bar1.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Label(btn_bar1, text="📝 Manage:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(0, 8))
        
        crud_buttons = [
            ("➕ Add", lambda: self.app.add_room_manual(), 'accent'),
            ("✏️ Edit", lambda: self.app.edit_room(), 'secondary'),
            ("🗑️ Delete", lambda: self.app.delete_room(), 'danger'),
            ("🗑️ Delete Multiple", lambda: self.app.delete_multiple('rooms'), 'danger'),
            ("� Import CSV", lambda: self.app.import_rooms_from_csv(), 'info')
        ]
        
        for text, command, style in crud_buttons:
            self.create_button(btn_bar1, text, command, style).pack(side=tk.LEFT, padx=3)
        # Duplicate visible rooms to another floor
        self.create_button(
            btn_bar1,
            "📄 Duplicate to Floor…",
            self._duplicate_visible_rooms_to_floor,
            'secondary'
        ).pack(side=tk.LEFT, padx=3)
        
        # Button bar - Row 2: Calculations and assignments
        btn_bar2 = ttk.Frame(frame, style='Main.TFrame')
        btn_bar2.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(btn_bar2, text="🧮 Calculate:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(0, 8))
        
        calc_buttons = [
            ("🔗 Assign Openings", lambda: self.app.assign_openings_to_room(), 'accent'),
            ("🔎 Details", self._show_room_details, 'secondary'),
            ("⚡ Auto Calc", lambda: self.app.auto_calculate_room(), 'accent'),
            ("⚡⚡ Auto Calc All", lambda: self.app.auto_calculate_all_rooms(), 'accent'),
            ("🧱 Set Ceramic", lambda: self.app.set_room_ceramic(), 'secondary'),
            ("📏 Change Wall Height", self._change_wall_height, 'secondary'),
            ("🏗️ Variable Wall Heights", lambda: self.app.edit_balcony_heights(), 'secondary'),
            ("🧱 Parapet from Perimeter", self._set_parapet_from_perimeter, 'secondary')
        ]
        
        for text, command, style in calc_buttons:
            btn = self.create_button(btn_bar2, text, command, style)
            btn.pack(side=tk.LEFT, padx=3)
            # Add tooltips for clarity
            if "Auto Calc All" in text:
                self._add_tooltip(btn, "Automatically calculate finishes for ALL rooms")
            elif "Auto Calc" in text and "All" not in text:
                self._add_tooltip(btn, "Calculate finishes for selected room (walls + ceiling - openings - ceramic)")
            elif "Ceramic" in text:
                self._add_tooltip(btn, "Set ceramic area for selected room (deducted from paint)")
            elif "Change Wall Height" in text:
                self._add_tooltip(btn, "Change wall height for selected room or all visible rooms")
            elif "Variable Wall Heights" in text:
                self._add_tooltip(btn, "Edit per-wall heights (balcony/roof/stair/lightwell)")
            elif "Parapet" in text:
                self._add_tooltip(btn, "Set parapet height using room perimeter (uniform)")
            elif "Assign" in text:
                self._add_tooltip(btn, "Link doors/windows to selected room")
            elif "Details" in text:
                self._add_tooltip(btn, "Show full per-room finishes breakdown")
        
        # Search filter
        filter_frame = ttk.Frame(frame, style='Main.TFrame')
        filter_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(filter_frame, text="🔍 Filter:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(0, 6))
        self.rooms_filter = ttk.Entry(filter_frame, width=25)
        self.rooms_filter.pack(side=tk.LEFT)
        self.rooms_filter.bind(
            '<KeyRelease>',
            lambda e: self._filter_treeview(self.rooms_tree, self.rooms_filter.get(), 'rooms', self.app.project.rooms)
        )
        self.create_button(
            filter_frame,
            "❌ Clear",
            lambda: self._clear_filter(self.rooms_filter, self.rooms_tree, 'rooms', self.app.project.rooms),
            'Small.TButton',
            width=120,
            height=36
        ).pack(side=tk.LEFT, padx=5)
        
        # Layer filter
        ttk.Label(filter_frame, text="  📐 Layer:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(12, 6))
        self.rooms_layer_var = tk.StringVar(value="[All]")
        self.rooms_layer_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.rooms_layer_var,
            width=15,
            state='readonly'
        )
        self.rooms_layer_combo.pack(side=tk.LEFT)
        self.rooms_layer_combo.bind(
            '<<ComboboxSelected>>',
            lambda e: self._filter_treeview(self.rooms_tree, self.rooms_filter.get(), 'rooms', self.app.project.rooms)
        )
        
        # Room type filter
        ttk.Label(filter_frame, text="  🏠 Type:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(12, 6))
        self.rooms_type_var = tk.StringVar(value="[All]")
        self.rooms_type_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.rooms_type_var,
            width=15,
            state='readonly'
        )
        self.rooms_type_combo.pack(side=tk.LEFT)
        self.rooms_type_combo.bind(
            '<<ComboboxSelected>>',
            lambda e: self._filter_treeview(self.rooms_tree, self.rooms_filter.get(), 'rooms', self.app.project.rooms)
        )
        
        # Floor filter
        ttk.Label(filter_frame, text="  🧱 Floor:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(12, 6))
        self.rooms_floor_var = tk.StringVar(value="[All]")
        self.rooms_floor_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.rooms_floor_var,
            width=10,
            state='readonly'
        )
        self.rooms_floor_combo.pack(side=tk.LEFT)
        self.rooms_floor_combo.bind(
            '<<ComboboxSelected>>',
            lambda e: self._filter_treeview(self.rooms_tree, self.rooms_filter.get(), 'rooms', self.app.project.rooms)
        )
        
        # Toggle for simple/advanced view
        self.show_advanced_columns = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filter_frame,
            text="🔧 عرض التفاصيل",
            variable=self.show_advanced_columns,
            command=self._toggle_columns_view,
            style='Switch.TCheckbutton'
        ).pack(side=tk.RIGHT, padx=(20, 0))
        
        # Treeview
        tree_frame = ttk.Frame(frame, style='Main.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        
        # Define column configurations - الأعمدة الأساسية والمتقدمة
        self._simple_columns = [
            ('Name', 'الاسم', 140),
            ('Type', 'النوع', 120),
            ('Area', 'المساحة م²', 100),
            ('Plaster', 'البياض م²', 100),
            ('Paint', 'الدهان م²', 100),
            ('Openings', 'الفتحات', 100),
        ]
        
        self._advanced_columns = [
            ('Name', 'الاسم', 120),
            ('Type', 'النوع', 100),
            ('Floor', 'الطابق', 70),
            ('Layer', 'الطبقة', 80),
            ('Openings', 'الفتحات', 90),
            ('W', 'العرض م', 70),
            ('L', 'الطول م', 70),
            ('Perim', 'المحيط م', 80),
            ('Area', 'المساحة م²', 80),
            ('Wall H', 'ارتفاع م', 70),
            ('Wall Finish', 'تشطيب حائط', 90),
            ('Ceiling', 'السقف م²', 80),
            ('Ceramic', 'السيراميك م²', 90),
            ('Plaster', 'البياض م²', 85),
            ('Paint', 'الدهان م²', 85)
        ]
        
        # Start with simple view
        current_cols = self._simple_columns
        
        self.rooms_tree = ttk.Treeview(
            tree_frame,
            columns=tuple(c[0] for c in current_cols),
            show='headings',
            selectmode='extended',
            height=8
        )
        
        for col, text, width in current_cols:
            self.rooms_tree.heading(col, text=text)
            self.rooms_tree.column(col, width=width, anchor=tk.CENTER)
        
        # Vertical scrollbar
        rooms_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.rooms_tree.yview)
        self.rooms_tree.configure(yscrollcommand=rooms_scroll_y.set)
        
        # Horizontal scrollbar (mainly for advanced view)
        rooms_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.rooms_tree.xview)
        self.rooms_tree.configure(xscrollcommand=rooms_scroll_x.set)
        
        self.rooms_tree.grid(row=0, column=0, sticky='nsew')
        rooms_scroll_y.grid(row=0, column=1, sticky='ns')
        rooms_scroll_x.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Configure alternating row colors
        self.rooms_tree.tag_configure('oddrow', background='#1a1d23')
        self.rooms_tree.tag_configure('evenrow', background='#24272f')
        
        # Totals footer - الإجماليات بالعربي
        self.rooms_totals_label = ttk.Label(
            frame,
            text="📊 الإجمالي: 0 غرفة | المساحة: 0.00 م² | البياض: 0.00 م² | الدهان: 0.00 م²",
            style='Metrics.TLabel'
        )
        self.rooms_totals_label.pack(fill=tk.X, pady=(4, 8))

        # Context menu for rooms - قائمة النقر اليمنى للغرف
        menu = tk.Menu(self.rooms_tree, tearoff=0)
        menu.add_command(label="🎨 تعيين لون...", command=self._set_room_color)
        menu.add_command(label="❌ مسح اللون", command=self._clear_room_color)
        menu.add_separator()
        menu.add_command(label="🚪 أضف باب لهذه الغرفة...", command=self._add_door_to_room)
        menu.add_command(label="🪟 أضف شباك لهذه الغرفة...", command=self._add_window_to_room)
        menu.add_command(label="🔗 تعيين فتحات...", command=lambda: self.app.assign_openings_to_room())
        menu.add_separator()
        menu.add_command(label="⚡ سيراميك سريع", command=self._quick_ceramic_for_room)
        menu.add_command(label="🧱 تعيين سيراميك يدوي...", command=lambda: self.app.set_room_ceramic())
        menu.add_separator()
        menu.add_command(label="⚡ حساب تلقائي", command=lambda: self.app.auto_calculate_room())
        menu.add_command(label="🔎 تفاصيل...", command=self._show_room_details)
        menu.add_separator()
        menu.add_command(label="🏗️ جدران متعددة (بلكون)...", command=lambda: self.app.edit_balcony_heights())
        menu.add_command(label="📄 نسخ إلى طابق آخر...", command=self._duplicate_visible_rooms_to_floor)

        def _on_right_click(event):
            try:
                row = self.rooms_tree.identify_row(event.y)
                if row:
                    self.rooms_tree.selection_set(row)
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        self.rooms_tree.bind("<Button-3>", _on_right_click)

    def _get_selected_room(self):
        """Safely resolve the selected room object from current Treeview selection."""
        sel = self.rooms_tree.selection()
        if not sel:
            return None

        iid = sel[0]
        rec = self._room_iid_to_record.get(iid)
        if rec is not None:
            return rec

        # Fallback (older behavior) if mapping not available
        vals = self.rooms_tree.item(iid).get('values') or []
        if not vals:
            return None
        name = vals[0]
        for r in self.app.project.rooms:
            r_name = r.get('name') if isinstance(r, dict) else getattr(r, 'name', None)
            if r_name == name:
                return r
        return None

    def _get_selected_rooms(self):
        """Return a list of selected room records (supports multi-select)."""
        selected = []
        for iid in self.rooms_tree.selection() or []:
            rec = self._room_iid_to_record.get(iid)
            if rec is not None:
                selected.append(rec)
        return selected

    def _change_wall_height(self):
        """Change wall height for selected room or all visible rooms."""
        try:
            from tkinter import simpledialog, messagebox
            
            # Ask for new wall height
            new_height = simpledialog.askfloat(
                "Change Wall Height",
                "Enter new wall height (m):",
                minvalue=0.1,
                maxvalue=20.0,
                parent=self.frame
            )
            
            if new_height is None:
                return
            
            selected_rooms = self._get_selected_rooms()

            # If nothing selected, choose scope.
            apply_to_all_visible = False
            apply_to_all_project = False
            if not selected_rooms:
                choice = messagebox.askyesnocancel(
                    "Change Wall Height",
                    "No rooms selected.\n\n"
                    "YES = Apply to ALL rooms in the PROJECT\n"
                    "NO  = Apply to ALL VISIBLE rooms (current filter)\n"
                    "CANCEL = Cancel",
                    icon='question',
                    parent=self.frame
                )
                if choice is None:
                    return
                if choice is True:
                    apply_to_all_project = True
                else:
                    apply_to_all_visible = True

            target_rooms = selected_rooms
            if apply_to_all_project:
                # Apply to all rooms regardless of current filter.
                target_rooms = list(self.app.project.rooms or [])
            elif apply_to_all_visible:
                target_rooms = [
                    self._room_iid_to_record[iid]
                    for iid in (self.rooms_tree.get_children() or [])
                    if iid in self._room_iid_to_record
                ]

            updated_count = 0
            for room in target_rooms:
                # Update explicit walls (used by the room drawing canvas and finish calculations)
                if isinstance(room, dict):
                    walls = room.get('walls') or []
                else:
                    walls = getattr(room, 'walls', []) or []

                for w in walls:
                    try:
                        if isinstance(w, dict):
                            w['height'] = float(new_height)
                        else:
                            setattr(w, 'height', float(new_height))
                    except Exception:
                        continue

                if isinstance(room, dict):
                    room['wall_height'] = new_height
                    # Ensure uniform-height mode uses empty segments (not None)
                    room['wall_segments'] = []
                else:
                    setattr(room, 'wall_height', new_height)
                    # Room.wall_segments must stay a list (None breaks to_dict serialization)
                    setattr(room, 'wall_segments', [])
                updated_count += 1

            # Recalculate
            if hasattr(self.app, 'auto_calculate_all_rooms') and (apply_to_all_project or apply_to_all_visible or len(selected_rooms) > 1):
                self.app.auto_calculate_all_rooms()
            elif hasattr(self.app, 'auto_calculate_room'):
                self.app.auto_calculate_room()

            self.refresh_data()
            # Refresh dependent tabs if present
            if hasattr(self.app, 'coatings_tab'):
                self.app.coatings_tab.refresh_data()
            if hasattr(self.app, 'ceramic_tab'):
                self.app.ceramic_tab.refresh_data()

            # Refresh the room drawing canvas if it exists (Room Manager tab)
            try:
                rm = getattr(self.app, 'room_manager_tab', None)
                if rm is not None and getattr(rm, 'room_canvas', None) and rm.room_canvas.winfo_exists():
                    # If a room is selected in manager, redraw it
                    rm.room_canvas.render_room(getattr(rm, 'selected_room', None))
            except Exception:
                pass

            self.app.update_status(
                f"Updated {updated_count} room(s) to height {new_height:.2f}m",
                icon="✅"
            )
                
        except Exception as e:
            self.app.update_status(f"Failed to change wall height: {e}", icon="❌")

    def _set_parapet_from_perimeter(self):
        """Set uniform parapet wall (segments = [perimeter × height]) for selected room."""
        try:
            room = self._get_selected_room()
            if not room:
                self.app.update_status("Select a room first to set parapet.", icon="ℹ️")
                return
            # Ask for parapet height (m)
            from tkinter import simpledialog
            h = simpledialog.askfloat("Parapet Height", "Enter parapet height (m):", minvalue=0.0, maxvalue=5.0, parent=self.frame)
            if h is None:
                return
            # Get perimeter
            perim = room.get('perim') if isinstance(room, dict) else getattr(room, 'perimeter', 0.0)
            try:
                perim = float(perim or 0.0)
            except Exception:
                perim = 0.0
            if perim <= 0 or h <= 0:
                self.app.update_status("Perimeter or height is zero — cannot set parapet.", icon="⚠️")
                return
            seg = {'length': perim, 'height': h}
            # Assign segments; do not force is_balcony — model now uses segments if present
            if isinstance(room, dict):
                room['wall_segments'] = [seg]
                room['wall_height'] = None
            else:
                setattr(room, 'wall_segments', [seg])
                setattr(room, 'wall_height', None)
            # Trigger refresh
            if hasattr(self.app, 'auto_calculate_room'):  # recompute finish caches if available
                self.app.auto_calculate_room()
            self.refresh_data()
            self.app.update_status(f"Parapet set: {h:.2f} m over perimeter {perim:.2f} m.", icon="✅")
        except Exception as e:
            self.app.update_status(f"Parapet failed: {e}", icon="❌")

    def _duplicate_visible_rooms_to_floor(self):
        """Duplicate all visible rooms in the tree to a target floor."""
        try:
            target_floor = simpledialog.askinteger("Duplicate Rooms", "Target floor (integer):", parent=self.frame, minvalue=-20, maxvalue=200)
            if target_floor is None:
                return
            # Build a quick lookup for rooms by (name, layer)
            def _key_for(rec):
                if isinstance(rec, dict):
                    return (rec.get('name'), rec.get('layer'))
                return (getattr(rec, 'name', None), getattr(rec, 'layer', None))
            room_map = {}
            for rec in self.app.project.rooms:
                room_map.setdefault(_key_for(rec), []).append(rec)
            added = 0
            for iid in self.rooms_tree.get_children():
                vals = self.rooms_tree.item(iid)['values']
                if not vals:
                    continue
                name = vals[0]
                layer = vals[3]  # With Floor column inserted, layer index=3
                matches = room_map.get((name, layer), [])
                if not matches:
                    continue
                src = matches[0]
                # Create duplicate record
                if isinstance(src, dict):
                    dup = src.copy()
                    dup['floor'] = int(target_floor)
                    # Keep name same; floor distinguishes
                    self.app.project.rooms.append(dup)
                    added += 1
                else:
                    from bilind.models.room import Room
                    dup = Room(
                        name=getattr(src, 'name', 'Room'),
                        layer=getattr(src, 'layer', ''),
                        width=getattr(src, 'width', None),
                        length=getattr(src, 'length', None),
                        perimeter=getattr(src, 'perimeter', 0.0),
                        area=getattr(src, 'area', 0.0),
                        room_type=getattr(src, 'room_type', '[Not Set]'),
                        opening_ids=list(getattr(src, 'opening_ids', []) or []),
                        color=getattr(src, 'color', None),
                        wall_height=getattr(src, 'wall_height', None),
                        ceiling_finish_area=getattr(src, 'ceiling_finish_area', None),
                        wall_finish_area=getattr(src, 'wall_finish_area', None),
                        is_balcony=getattr(src, 'is_balcony', False),
                        wall_segments=list(getattr(src, 'wall_segments', []) or []),
                        ceramic_area=getattr(src, 'ceramic_area', None),
                        plaster_area=getattr(src, 'plaster_area', None),
                        paint_area=getattr(src, 'paint_area', None),
                        floor=int(target_floor)
                    )
                    self.app.project.rooms.append(dup)
                    added += 1
            self.refresh_data()
            self.app.update_status(f"Duplicated {added} rooms to floor {target_floor}.", icon="✅")
        except Exception as e:
            self.app.update_status(f"Duplicate failed: {e}", icon="⚠️")

    def _set_room_color(self):
        sel = self.rooms_tree.selection()
        if not sel:
            return
        idx = self.rooms_tree.index(sel[0])
        room = self.app.project.rooms[idx]
        color_code = colorchooser.askcolor(title="Choose room color")[1]
        if not color_code:
            return
        if isinstance(room, dict):
            room['color'] = color_code
        else:
            setattr(room, 'color', color_code)
        self.refresh_data()
        self.app.update_status(f"Set color for {getattr(room, 'name', room.get('name','Room'))}", icon="🎨")

    def _clear_room_color(self):
        sel = self.rooms_tree.selection()
        if not sel:
            return
        idx = self.rooms_tree.index(sel[0])
        room = self.app.project.rooms[idx]
        if isinstance(room, dict):
            room.pop('color', None)
        else:
            setattr(room, 'color', None)
        self.refresh_data()
        self.app.update_status("Cleared room color", icon="🧹")
    
    def _add_door_to_room(self):
        """Add a new door and automatically assign it to the selected room."""
        room = self._get_selected_room()
        if not room:
            self.app.update_status("اختر غرفة أولاً", icon="ℹ️")
            return
        
        room_name = room.get('name') if isinstance(room, dict) else getattr(room, 'name', '')
        
        # Call the app's add door method with room assignment
        if hasattr(self.app, '_add_opening_dialog'):
            door_data = self.app._add_opening_dialog("إضافة باب", 'DOOR', assign_to_room=room_name)
            if door_data:
                from bilind.models.opening import Opening
                door = Opening(
                    name=door_data.get('name', f"D{len(self.app.project.doors)+1}"),
                    opening_type='DOOR',
                    width=door_data.get('w', 0.9),
                    height=door_data.get('h', 2.1),
                    material_type=door_data.get('type', 'قياسي'),
                    quantity=door_data.get('qty', 1)
                )
                self.app.project.doors.append(door)
                
                linked = 0
                if hasattr(self.app, '_link_opening_to_room'):
                    linked = self.app._link_opening_to_room(door.name, room_name)
                if not linked:
                    # Fallback to opening_ids if association helper unavailable
                    if isinstance(room, dict):
                        room.setdefault('opening_ids', []).append(door.name)
                    else:
                        if not hasattr(room, 'opening_ids') or room.opening_ids is None:
                            room.opening_ids = []
                        room.opening_ids.append(door.name)
                
                self.refresh_data()
                self.app.update_status(f"تمت إضافة الباب {door.name} للغرفة {room_name}", icon="🚪")
        else:
            self.app.update_status("لا يمكن إضافة باب - الدالة غير متوفرة", icon="⚠️")
    
    def _add_window_to_room(self):
        """Add a new window and automatically assign it to the selected room."""
        room = self._get_selected_room()
        if not room:
            self.app.update_status("اختر غرفة أولاً", icon="ℹ️")
            return
        
        room_name = room.get('name') if isinstance(room, dict) else getattr(room, 'name', '')
        
        # Call the app's add window method with room assignment
        if hasattr(self.app, '_add_opening_dialog'):
            window_data = self.app._add_opening_dialog("إضافة شباك", 'WINDOW', assign_to_room=room_name)
            if window_data:
                from bilind.models.opening import Opening
                window = Opening(
                    name=window_data.get('name', f"W{len(self.app.project.windows)+1}"),
                    opening_type='WINDOW',
                    width=window_data.get('w', 1.0),
                    height=window_data.get('h', 1.2),
                    material_type=window_data.get('type', 'قياسي'),
                    quantity=window_data.get('qty', 1)
                )
                self.app.project.windows.append(window)
                
                linked = 0
                if hasattr(self.app, '_link_opening_to_room'):
                    linked = self.app._link_opening_to_room(window.name, room_name)
                if not linked:
                    if isinstance(room, dict):
                        room.setdefault('opening_ids', []).append(window.name)
                    else:
                        if not hasattr(room, 'opening_ids') or room.opening_ids is None:
                            room.opening_ids = []
                        room.opening_ids.append(window.name)
                
                self.refresh_data()
                self.app.update_status(f"تمت إضافة الشباك {window.name} للغرفة {room_name}", icon="🪟")
        else:
            self.app.update_status("لا يمكن إضافة شباك - الدالة غير متوفرة", icon="⚠️")
    
    def _quick_ceramic_for_room(self):
        """Auto-generate ceramic zones based on room type defaults."""
        room = self._get_selected_room()
        if not room:
            self.app.update_status("اختر غرفة أولاً", icon="ℹ️")
            return
        
        room_name = room.get('name') if isinstance(room, dict) else getattr(room, 'name', '')
        room_type = room.get('room_type') if isinstance(room, dict) else getattr(room, 'room_type', '')
        room_area = float(room.get('area', 0) if isinstance(room, dict) else getattr(room, 'area', 0) or 0)

        # Perimeter key is inconsistent across legacy dicts/objects: prefer `perim`, fallback to `perimeter`.
        if isinstance(room, dict):
            room_perim_raw = room.get('perim', None)
            if room_perim_raw is None:
                room_perim_raw = room.get('perimeter', 0)
        else:
            room_perim_raw = getattr(room, 'perim', None)
            if room_perim_raw is None:
                room_perim_raw = getattr(room, 'perimeter', 0)
        try:
            room_perim = float(room_perim_raw or 0.0)
        except Exception:
            room_perim = 0.0
        
        # Get defaults for this room type
        from bilind.core.config import get_room_defaults
        defaults = get_room_defaults(room_type)
        
        ceramic_config = defaults.get('ceramic')
        if not ceramic_config:
            from tkinter import messagebox
            messagebox.showinfo("سيراميك سريع", 
                f"نوع الغرفة '{room_type}' لا يحتاج سيراميك بالإفتراضي.\n"
                "استخدم 'تعيين سيراميك يدوي' لإضافة سيراميك مخصص.")
            return
        
        from bilind.models.finish import CeramicZone
        zones_to_add = []
        
        wall_h = ceramic_config.get('wall_height', 0)
        floor_ceramic = ceramic_config.get('floor', False)
        category = ceramic_config.get('category', 'Other')

        # Bathrooms/toilets: users expect "full-wall" ceramic by default.
        # Override the default 1.6m band with the room's effective wall height.
        if str(room_type or '').strip() in ('حمام', 'تواليت') and room_perim > 0:
            try:
                from bilind.calculations.unified_calculator import UnifiedCalculator
                calc = UnifiedCalculator(self.app.project)
                walls_gross = float(calc.calculate_walls_gross(room) or 0.0)
                if walls_gross > 0:
                    wall_h = max(float(wall_h or 0.0), walls_gross / room_perim)
            except Exception:
                # Fallback to room field if calculator isn't available
                try:
                    if isinstance(room, dict):
                        wall_h = max(float(wall_h or 0.0), float(room.get('wall_height', 0.0) or 0.0))
                    else:
                        wall_h = max(float(wall_h or 0.0), float(getattr(room, 'wall_height', 0.0) or 0.0))
                except Exception:
                    pass
        
        # Wall ceramic
        if wall_h > 0 and room_perim > 0:
            wall_zone = CeramicZone.for_wall(
                perimeter=room_perim,
                height=wall_h,
                room_name=room_name,
                category=category,
                name=f"سيراميك حائط - {room_name}"
            )
            zones_to_add.append(wall_zone)
        
        # Floor ceramic
        if floor_ceramic and room_area > 0:
            floor_zone = CeramicZone.for_floor(
                area=room_area,
                room_name=room_name,
                category=category,
                name=f"سيراميك أرضية - {room_name}"
            )
            zones_to_add.append(floor_zone)
        
        if zones_to_add:
            # Show confirmation
            from tkinter import messagebox
            from bilind.calculations.unified_calculator import UnifiedCalculator
            calc = UnifiedCalculator(self.app.project)

            msg = f"سيتم إنشاء السيراميك التالي للغرفة '{room_name}' (مع خصم الفتحات تلقائياً):\n\n"
            total_net = 0.0
            for z in zones_to_add:
                surface_type = (getattr(z, 'surface_type', '') or '').lower()
                if surface_type == 'wall':
                    m = calc.calculate_zone_metrics(z)
                    total_net += float(m.net_area or 0.0)
                    if (m.deduction_area or 0.0) > 0.0001:
                        msg += f"• {z.name}: {m.net_area:.2f} م² (خصم فتحات {m.deduction_area:.2f})\n"
                    else:
                        msg += f"• {z.name}: {m.net_area:.2f} م²\n"
                else:
                    a = float(getattr(z, 'area', 0.0) or 0.0)
                    total_net += a
                    msg += f"• {z.name}: {a:.2f} م²\n"
            msg += f"\nالإجمالي: {total_net:.2f} م²"
            
            if messagebox.askyesno("سيراميك سريع", msg):
                # Delete existing ceramics for this room first
                self.app.project.ceramic_zones = [
                    z for z in self.app.project.ceramic_zones
                    if (z.get('room_name') if isinstance(z, dict) else getattr(z, 'room_name', None)) != room_name
                ]
                self.app.project.ceramic_zones.extend(zones_to_add)
                self.refresh_data()
                # Refresh coatings tab if exists
                if hasattr(self.app, 'coatings_tab'):
                    self.app.coatings_tab.refresh_data()
                if hasattr(self.app, 'ceramic_tab'):
                    self.app.ceramic_tab.refresh_data()
                self.app.update_status(f"تمت إضافة {len(zones_to_add)} منطقة سيراميك", icon="✅")
        else:
            from tkinter import messagebox
            messagebox.showinfo("سيراميك سريع", "لا يوجد سيراميك للإضافة.")
    
    def _show_room_details(self):
        """Show a detailed per-room breakdown: plaster (walls/ceiling), paint, ceramics, openings, baseboards."""
        room = self._get_selected_room()
        if not room:
            self.app.update_status("Select a room to view details.", icon="ℹ️")
            return

        def _val(obj, dkey, attr, default=None):
            if isinstance(obj, dict):
                return obj.get(dkey, default)
            return getattr(obj, attr, default)

        name = _val(room, 'name', 'name', '-')
        layer = _val(room, 'layer', 'layer', '-')
        floor_no = _val(room, 'floor', 'floor', 0)
        perim = float(_val(room, 'perim', 'perimeter', 0.0) or 0.0)
        area = float(_val(room, 'area', 'area', 0.0) or 0.0)

        # Determine wall height: segments override single height, else project default
        wall_h = _val(room, 'wall_height', 'wall_height', None)
        segments = _val(room, 'wall_segments', 'wall_segments', None) or []
        default_h = float(getattr(self.app.project, 'default_wall_height', 3.0) or 3.0)

        def walls_gross_area():
            if segments:
                try:
                    return sum(float(s.get('length', 0.0)) * float(s.get('height', 0.0)) for s in segments)
                except Exception:
                    return 0.0
            h = float(wall_h) if wall_h not in (None, '') else default_h
            return perim * h

        # Build openings assigned to this room
        opening_ids = []
        assoc = getattr(self.app, 'association', None)
        if assoc is not None:
            opening_ids = assoc.get_room_opening_ids(room) or []
        else:
            opening_ids = _val(room, 'opening_ids', 'opening_ids', []) or []

        # Also include openings that list this room as assigned
        room_name = name or ''
        for coll in (self.app.project.doors, self.app.project.windows):
            for o in coll:
                try:
                    oname = _val(o, 'name', 'name', None)
                    assigned = (o.get('assigned_rooms') if isinstance(o, dict) else getattr(o, 'assigned_rooms', [])) or []
                    if oname and room_name and room_name in assigned and oname not in opening_ids:
                        opening_ids.append(oname)
                except Exception:
                    continue

        def _opening_unit_size(oid):
            od = self.app._get_opening_dict_by_name(oid)
            if not od:
                return 0.0, 0.0, None
            return float(od.get('w', 0.0) or 0.0), float(od.get('h', 0.0) or 0.0), (od.get('type', '') or od.get('opening_type', '')).upper()

        # Compute openings breakdown (unit per room)
        doors_qty = 0
        windows_qty = 0
        doors_area = 0.0
        windows_area = 0.0
        doors_width_sum = 0.0  # for baseboards
        for oid in opening_ids:
            w, h, typ = _opening_unit_size(oid)
            if w <= 0 or h <= 0:
                continue
            if typ == 'WINDOW':
                windows_qty += 1
                windows_area += w * h
            else:
                doors_qty += 1
                doors_area += w * h
                doors_width_sum += w

        openings_area = doors_area + windows_area
        gross_walls = walls_gross_area()
        walls_net = max(0.0, gross_walls - openings_area)
        baseboards_m = max(0.0, perim - doors_width_sum)

        # Use UnifiedCalculator for consistent calculations
        from bilind.calculations.unified_calculator import UnifiedCalculator
        calc = UnifiedCalculator(self.app.project)
        room_calc = calc.calculate_room(room)
        
        # Ceramic breakdown from UnifiedCalculator
        cer_wall = room_calc.ceramic_wall
        cer_ceiling = room_calc.ceramic_ceiling
        cer_floor = room_calc.ceramic_floor

        # Plaster breakdown from UnifiedCalculator
        wall_plaster_net = room_calc.plaster_walls
        ceiling_plaster_net = room_calc.plaster_ceiling
        plaster_total = room_calc.plaster_total

        # Paint breakdown from UnifiedCalculator
        walls_paint_net = room_calc.paint_walls
        ceiling_paint = room_calc.paint_ceiling
        paint_total = room_calc.paint_total

        # Build dialog UI
        dlg = tk.Toplevel(self.frame)
        dlg.title(f"Room Details – {name}")
        dlg.configure(bg=self.colors['bg_secondary'])
        dlg.transient(self.frame)
        dlg.grab_set()

        container = ttk.Frame(dlg, padding=(16, 12), style='Main.TFrame')
        container.pack(fill=tk.BOTH, expand=True)

        def row(r, label, value, unit=''):
            ttk.Label(container, text=label, style='Caption.TLabel').grid(row=r, column=0, sticky='w', pady=4)
            ttk.Label(container, text=value, foreground=self.colors['text_primary']).grid(row=r, column=1, sticky='w', pady=4)
            if unit:
                ttk.Label(container, text=unit, foreground=self.colors['text_secondary']).grid(row=r, column=2, sticky='w', pady=4)

        r = 0
        # Basic
        row(r, "Room • الغرفة", f"[{floor_no}] {name}"); r += 1
        row(r, "Layer • الطبقة", layer); r += 1
        row(r, "Perimeter • المحيط", f"{perim:.2f}", "m"); r += 1
        row(r, "Floor Area • مساحة الأرضية", f"{area:.2f}", "m²"); r += 1
        row(r, "Wall Height • ارتفاع الجدار", f"{(wall_h if wall_h not in (None,'') else default_h):.2f}", "m"); r += 1
        row(r, "Walls Gross • الجدران الإجمالي", f"{gross_walls:.2f}", "m²"); r += 1

        # Openings
        row(r, "Doors Qty • عدد الأبواب", str(doors_qty)); r += 1
        row(r, "Windows Qty • عدد الشبابيك", str(windows_qty)); r += 1
        row(r, "Openings Area • مساحة الفتحات", f"{openings_area:.2f}", "m²"); r += 1
        row(r, "Walls Net • الجدران الصافي", f"{walls_net:.2f}", "m²"); r += 1
        row(r, "Baseboards (نعلات)", f"{baseboards_m:.2f}", "m"); r += 1

        # Ceramics
        ttk.Separator(container, orient='horizontal').grid(row=r, column=0, columnspan=3, sticky='ew', pady=(8, 8)); r += 1
        row(r, "Ceramic Wall • سيراميك الجدار", f"{cer_wall:.2f}", "m²"); r += 1
        row(r, "Ceramic Ceiling • سيراميك السقف", f"{cer_ceiling:.2f}", "m²"); r += 1
        row(r, "Ceramic Floor • سيراميك الأرضية", f"{cer_floor:.2f}", "m²"); r += 1

        # Plaster
        ttk.Separator(container, orient='horizontal').grid(row=r, column=0, columnspan=3, sticky='ew', pady=(8, 8)); r += 1
        row(r, "Wall Plaster (Net) • لياسة الجدران (صافي)", f"{wall_plaster_net:.2f}", "m²"); r += 1
        row(r, "Ceiling Plaster (Net) • لياسة السقف (صافي)", f"{ceiling_plaster_net:.2f}", "m²"); r += 1
        row(r, "Plaster Total • مجموع اللياسة", f"{plaster_total:.2f}", "m²"); r += 1

        # Paint
        ttk.Separator(container, orient='horizontal').grid(row=r, column=0, columnspan=3, sticky='ew', pady=(8, 8)); r += 1
        row(r, "Walls Paint Net • دهان الجدران (صافي)", f"{walls_paint_net:.2f}", "m²"); r += 1
        row(r, "Ceiling Paint • دهان السقف", f"{ceiling_paint:.2f}", "m²"); r += 1
        row(r, "Paint Total • مجموع الدهان", f"{paint_total:.2f}", "m²"); r += 1

        # Openings list
        openings_text = '-'
        try:
            openings_text = self.app.association.format_opening_list(room, max_items=8)
        except Exception:
            openings_text = ','.join(opening_ids) if opening_ids else '-'
        ttk.Separator(container, orient='horizontal').grid(row=r, column=0, columnspan=3, sticky='ew', pady=(8, 8)); r += 1
        row(r, "Openings • الفتحات", openings_text, ""); r += 1

        # Buttons
        btn_bar = ttk.Frame(dlg, padding=(16, 8), style='Main.TFrame')
        btn_bar.pack(fill=tk.X)
        ttk.Button(btn_bar, text="Close", command=dlg.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)
    
    def _add_tooltip(self, widget, text):
        """Add a simple tooltip to a widget."""
        def on_enter(event):
            self.app.update_status(text, icon="ℹ️")
        def on_leave(event):
            self.app.update_status(self.app._default_status)
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _create_doors_section(self, parent):
        """Create the doors management section."""
        frame = ttk.LabelFrame(
            parent,
            text="🚪 Doors",
            style='Card.TLabelframe',
            padding=(15, 12)
        )
        frame.pack(fill=tk.X, padx=12, pady=8)
        
        # Button bar
        btn_bar = ttk.Frame(frame, style='Main.TFrame')
        btn_bar.pack(fill=tk.X, pady=(0, 8))
        
        buttons = [
            ("➕ Add", lambda: self.app.add_opening_manual('DOOR'), 'Accent.TButton'),
            ("✏️ Edit", lambda: self.app.edit_opening('DOOR'), 'Secondary.TButton'),
            ("🗑️ Delete", lambda: self.app.delete_opening('DOOR'), 'Danger.TButton'),
            ("🗑️ Delete Multiple", lambda: self.app.delete_multiple('doors'), 'Danger.TButton')
        ]
        
        for text, command, style in buttons:
            self.create_button(btn_bar, text, command, style).pack(side=tk.LEFT, padx=4)
        
        # Search filter
        filter_frame = ttk.Frame(frame, style='Main.TFrame')
        filter_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(filter_frame, text="🔍 Filter:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(0, 6))
        self.doors_filter = ttk.Entry(filter_frame, width=25)
        self.doors_filter.pack(side=tk.LEFT)
        self.doors_filter.bind(
            '<KeyRelease>',
            lambda e: self._filter_treeview(self.doors_tree, self.doors_filter.get(), 'doors', self.app.project.doors)
        )
        self.create_button(
            filter_frame,
            "❌ Clear",
            lambda: self._clear_filter(self.doors_filter, self.doors_tree, 'doors', self.app.project.doors),
            'Small.TButton',
            width=120,
            height=36
        ).pack(side=tk.LEFT, padx=5)
        
        # Layer filter
        ttk.Label(filter_frame, text="  📐 Layer:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(12, 6))
        self.doors_layer_var = tk.StringVar(value="[All]")
        self.doors_layer_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.doors_layer_var,
            width=15,
            state='readonly'
        )
        self.doors_layer_combo.pack(side=tk.LEFT)
        self.doors_layer_combo.bind(
            '<<ComboboxSelected>>',
            lambda e: self._filter_treeview(self.doors_tree, self.doors_filter.get(), 'doors', self.app.project.doors)
        )
        
        # Treeview
        doors_tree_frame = ttk.Frame(frame, style='Main.TFrame')
        doors_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        
        door_columns = ('Name', 'Type', 'W', 'H', 'Qty', 'Perim', 'Area', 'Stone', 'Weight', 'Host Wall')
        self.doors_tree = ttk.Treeview(
            doors_tree_frame,
            columns=door_columns,
            show='headings',
            selectmode='browse',
            height=5
        )
        
        for col, text, width in [
            ('Name', 'Name', 100),
            ('Type', 'Type', 110),
            ('W', 'Width (m)', 90),
            ('H', 'Height (m)', 90),
            ('Qty', 'Qty', 60),
            ('Perim', 'Perimeter (m)', 120),
            ('Area', 'Area (m²)', 110),
            ('Stone', 'Stone (lm)', 110),
            ('Weight', 'Weight (kg)', 120),
            ('Host Wall', 'Host Wall', 130)
        ]:
            self.doors_tree.heading(col, text=text)
            anchor = tk.CENTER if col not in ['Name', 'Type'] else tk.W
            self.doors_tree.column(col, width=width, anchor=anchor)
        
        # Vertical scrollbar
        doors_scroll_y = ttk.Scrollbar(doors_tree_frame, orient=tk.VERTICAL, command=self.doors_tree.yview)
        self.doors_tree.configure(yscrollcommand=doors_scroll_y.set)
        
        # Horizontal scrollbar
        doors_scroll_x = ttk.Scrollbar(doors_tree_frame, orient=tk.HORIZONTAL, command=self.doors_tree.xview)
        self.doors_tree.configure(xscrollcommand=doors_scroll_x.set)
        
        self.doors_tree.grid(row=0, column=0, sticky='nsew')
        doors_scroll_y.grid(row=0, column=1, sticky='ns')
        doors_scroll_x.grid(row=1, column=0, sticky='ew')
        
        doors_tree_frame.grid_rowconfigure(0, weight=1)
        doors_tree_frame.grid_columnconfigure(0, weight=1)
        
        # Apply modern styling enhancements
        if hasattr(self.app, 'enhance_treeview'):
            self.app.enhance_treeview(self.doors_tree)
        
        # Totals footer for doors
        self.doors_totals_label = ttk.Label(
            frame,
            text="📊 الإجمالي: 0 باب | المساحة: 0.00 م² | الوزن: 0.0 كجم",
            style='Metrics.TLabel'
        )
        self.doors_totals_label.pack(fill=tk.X, pady=(4, 8))
    
    def _create_windows_section(self, parent):
        """Create the windows management section."""
        frame = ttk.LabelFrame(
            parent,
            text="🪟 Windows",
            style='Card.TLabelframe',
            padding=(15, 12)
        )
        frame.pack(fill=tk.X, padx=12, pady=8)
        
        # Button bar
        btn_bar = ttk.Frame(frame, style='Main.TFrame')
        btn_bar.pack(fill=tk.X, pady=(0, 8))
        
        buttons = [
            ("➕ Add", lambda: self.app.add_opening_manual('WINDOW'), 'Accent.TButton'),
            ("✏️ Edit", lambda: self.app.edit_opening('WINDOW'), 'Secondary.TButton'),
            ("🗑️ Delete", lambda: self.app.delete_opening('WINDOW'), 'Danger.TButton'),
            ("🗑️ Delete Multiple", lambda: self.app.delete_multiple('windows'), 'Danger.TButton')
        ]
        
        for text, command, style in buttons:
            self.create_button(btn_bar, text, command, style).pack(side=tk.LEFT, padx=4)
        
        # Search filter
        filter_frame = ttk.Frame(frame, style='Main.TFrame')
        filter_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(filter_frame, text="🔍 Filter:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(0, 6))
        self.windows_filter = ttk.Entry(filter_frame, width=25)
        self.windows_filter.pack(side=tk.LEFT)
        self.windows_filter.bind(
            '<KeyRelease>',
            lambda e: self._filter_treeview(self.windows_tree, self.windows_filter.get(), 'windows', self.app.project.windows)
        )
        self.create_button(
            filter_frame,
            "❌ Clear",
            lambda: self._clear_filter(self.windows_filter, self.windows_tree, 'windows', self.app.project.windows),
            'Small.TButton',
            width=120,
            height=36
        ).pack(side=tk.LEFT, padx=5)
        
        # Layer filter
        ttk.Label(filter_frame, text="  📐 Layer:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(12, 6))
        self.windows_layer_var = tk.StringVar(value="[All]")
        self.windows_layer_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.windows_layer_var,
            width=15,
            state='readonly'
        )
        self.windows_layer_combo.pack(side=tk.LEFT)
        self.windows_layer_combo.bind(
            '<<ComboboxSelected>>',
            lambda e: self._filter_treeview(self.windows_tree, self.windows_filter.get(), 'windows', self.app.project.windows)
        )
        
        # Treeview
        windows_tree_frame = ttk.Frame(frame, style='Main.TFrame')
        windows_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        
        window_columns = ('Name', 'Type', 'W', 'H', 'Qty', 'Perim', 'Glass', 'Stone', 'Host Wall')
        self.windows_tree = ttk.Treeview(
            windows_tree_frame,
            columns=window_columns,
            show='headings',
            selectmode='browse',
            height=5
        )
        
        for col, text, width in [
            ('Name', 'Name', 100),
            ('Type', 'Type', 110),
            ('W', 'Width (m)', 90),
            ('H', 'Height (m)', 90),
            ('Qty', 'Qty', 60),
            ('Perim', 'Perimeter (m)', 120),
            ('Glass', 'Glass (m²)', 120),
            ('Stone', 'Stone (lm)', 120),
            ('Host Wall', 'Host Wall', 130)
        ]:
            self.windows_tree.heading(col, text=text)
            anchor = tk.CENTER if col not in ['Name', 'Type'] else tk.W
            self.windows_tree.column(col, width=width, anchor=anchor)
        
        # Vertical scrollbar
        windows_scroll_y = ttk.Scrollbar(windows_tree_frame, orient=tk.VERTICAL, command=self.windows_tree.yview)
        self.windows_tree.configure(yscrollcommand=windows_scroll_y.set)
        
        # Horizontal scrollbar
        windows_scroll_x = ttk.Scrollbar(windows_tree_frame, orient=tk.HORIZONTAL, command=self.windows_tree.xview)
        self.windows_tree.configure(xscrollcommand=windows_scroll_x.set)
        
        self.windows_tree.grid(row=0, column=0, sticky='nsew')
        windows_scroll_y.grid(row=0, column=1, sticky='ns')
        windows_scroll_x.grid(row=1, column=0, sticky='ew')
        
        windows_tree_frame.grid_rowconfigure(0, weight=1)
        windows_tree_frame.grid_columnconfigure(0, weight=1)
        
        # Apply modern styling enhancements
        if hasattr(self.app, 'enhance_treeview'):
            self.app.enhance_treeview(self.windows_tree)
        
        # Totals footer for windows
        self.windows_totals_label = ttk.Label(
            frame,
            text="📊 الإجمالي: 0 شباك | الزجاج: 0.00 م² | الحجر: 0.00 م.ط",
            style='Metrics.TLabel'
        )
        self.windows_totals_label.pack(fill=tk.X, pady=(4, 8))
