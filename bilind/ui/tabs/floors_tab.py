import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from bilind.models.room import FLOOR_PROFILES
from bilind.calculations.unified_calculator import UnifiedCalculator, RoomCalculations
from .base_tab import BaseTab

if TYPE_CHECKING:
    from bilind_main import BilindEnhanced


# Type alias for cached metrics map
RoomMetricsContext = Dict[str, RoomCalculations]


class FloorsTab(BaseTab):
    """
    Floors/Levels Tab - Organize rooms by floor level.
    
    This tab allows users to:
    - Group rooms by floor (Ground, First, Second, etc.)
    - View per-floor totals (Area, Walls, Plaster, Paint, Ceramic)
    - Quickly assign/unassign multiple rooms
    - Supports both floor_profile (text) and floor (number)
    """
    
    def __init__(self, notebook: tk.Widget, app: 'BilindEnhanced'):
        # Note: FloorsTab uses notebook as parent (legacy pattern)
        self.notebook = notebook
        self.app = app
        self.colors = app.colors
        self.frame: Optional[ttk.Frame] = None
        self.selected_floor: Optional[str] = None
        self._ctx_cache: Optional[RoomMetricsContext] = None  # Cache for metrics context
    
    @property
    def custom_floors(self) -> set:
        """Get custom floors from project (synced with save/load)."""
        return set(getattr(self.app.project, 'custom_floors', []) or [])
    
    @custom_floors.setter
    def custom_floors(self, value: set):
        """Save custom floors to project."""
        self.app.project.custom_floors = list(value)
        
    def create(self) -> ttk.Frame:
        self.frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)
        
        # --- Left Panel: Floor List ---
        left_panel = ttk.LabelFrame(self.frame, text="🏢 Floors / Levels", padding=10, style='Card.TLabelframe')
        left_panel.grid(row=0, column=0, sticky='ns', padx=10, pady=10)
        
        # Floor List
        self.floors_tree = ttk.Treeview(left_panel, columns=('Name', 'Rooms', 'Area'), show='headings', height=15)
        self.floors_tree.heading('Name', text='Floor Name')
        self.floors_tree.heading('Rooms', text='Rooms')
        self.floors_tree.heading('Area', text='Total Area')
        self.floors_tree.column('Name', width=100)
        self.floors_tree.column('Rooms', width=50, anchor='center')
        self.floors_tree.column('Area', width=80, anchor='center')
        self.floors_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.floors_tree.bind('<<TreeviewSelect>>', self._on_floor_selected)
        
        # Add/Delete Floor Buttons
        btn_frame = ttk.Frame(left_panel, style='Main.TFrame')
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="+ Add Floor", style='Accent.TButton', command=self._add_floor).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        ttk.Button(btn_frame, text="- Delete", style='Secondary.TButton', command=self._delete_floor).pack(side=tk.LEFT, expand=True, fill=tk.X)

        # --- Middle Panel: Assigned Rooms ---
        mid_panel = ttk.LabelFrame(self.frame, text="Assigned Rooms", padding=10, style='Card.TLabelframe')
        mid_panel.grid(row=0, column=1, sticky='nsew', padx=(0, 10), pady=10)
        
        self.assigned_tree = ttk.Treeview(mid_panel, columns=('Name', 'Area', 'Walls', 'Type'), show='headings', selectmode='extended')
        self.assigned_tree.heading('Name', text='Room Name')
        self.assigned_tree.heading('Area', text='Area (m²)')
        self.assigned_tree.heading('Walls', text='Walls (m²)')
        self.assigned_tree.heading('Type', text='Type')
        self.assigned_tree.column('Name', width=140)
        self.assigned_tree.column('Area', width=70, anchor='center')
        self.assigned_tree.column('Walls', width=70, anchor='center')
        self.assigned_tree.column('Type', width=90)
        self.assigned_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Unassign Button
        ttk.Button(mid_panel, text="Remove from Floor →", style='Secondary.TButton', command=self._unassign_rooms).pack(anchor='e')

        # --- Right Panel: Available Rooms ---
        right_panel = ttk.LabelFrame(self.frame, text="Available Rooms (All)", padding=10, style='Card.TLabelframe')
        right_panel.grid(row=0, column=2, sticky='ns', padx=(0, 10), pady=10)
        
        self.available_tree = ttk.Treeview(right_panel, columns=('Name', 'Area', 'Current'), show='headings', selectmode='extended')
        self.available_tree.heading('Name', text='Room Name')
        self.available_tree.heading('Area', text='Area')
        self.available_tree.heading('Current', text='Current Floor')
        self.available_tree.column('Name', width=150)
        self.available_tree.column('Area', width=80, anchor='center')
        self.available_tree.column('Current', width=100)
        self.available_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Assign Button
        ttk.Button(right_panel, text="← Assign to Floor", style='Accent.TButton', command=self._assign_rooms).pack(anchor='w')

        # --- Bottom Panel: Totals ---
        bottom_panel = ttk.LabelFrame(self.frame, text="Floor Totals", padding=10, style='Card.TLabelframe')
        bottom_panel.grid(row=1, column=0, columnspan=3, sticky='ew', padx=10, pady=(0, 10))
        
        self.lbl_total_area = ttk.Label(bottom_panel, text="Total Area: 0.00 m²", font=('Segoe UI', 10, 'bold'))
        self.lbl_total_area.pack(side=tk.LEFT, padx=20)
        
        self.lbl_total_walls = ttk.Label(bottom_panel, text="Walls: 0.00 m²", font=('Segoe UI', 10))
        self.lbl_total_walls.pack(side=tk.LEFT, padx=20)
        
        self.lbl_total_plaster = ttk.Label(bottom_panel, text="Plaster: 0.00 m²", font=('Segoe UI', 10))
        self.lbl_total_plaster.pack(side=tk.LEFT, padx=20)
        
        self.lbl_total_ceramic = ttk.Label(bottom_panel, text="Ceramic: 0.00 m²", font=('Segoe UI', 10))
        self.lbl_total_ceramic.pack(side=tk.LEFT, padx=20)
        
        self.lbl_total_paint = ttk.Label(bottom_panel, text="Paint: 0.00 m²", font=('Segoe UI', 10))
        self.lbl_total_paint.pack(side=tk.LEFT, padx=20)

        self._refresh_floors_list()
        self._refresh_available_rooms()
        
        return self.frame

    # ==================== HELPER METHODS ====================
    
    def _get_default_wall_height(self) -> float:
        """Get default wall height from project settings."""
        return float(getattr(self.app.project, 'default_wall_height', 3.0) or 3.0)
    
    def _build_metrics_context(self) -> RoomMetricsContext:
        """Build and cache room metrics using UnifiedCalculator (SSOT)."""
        calc = UnifiedCalculator(self.app.project)
        calcs = calc.calculate_all_rooms()
        self._ctx_cache = {c.room_name: c for c in calcs}
        return self._ctx_cache
    
    def _get_ctx(self) -> RoomMetricsContext:
        """Get cached context or build new one."""
        if self._ctx_cache is None:
            return self._build_metrics_context()
        return self._ctx_cache

    def _get_metrics_for_room(self, room: Any) -> Optional[RoomCalculations]:
        """Return RoomCalculations for a room if available."""
        ctx = self._get_ctx()
        name = self.app._room_name(room)
        return ctx.get(name)
    
    def _invalidate_ctx(self):
        """Clear the cached context (call when data changes)."""
        self._ctx_cache = None
    
    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float."""
        try:
            return float(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    # ==================== REFRESH METHODS ====================

    def _refresh_floors_list(self):
        """Refresh the list of floors with room counts and total areas."""
        for item in self.floors_tree.get_children():
            self.floors_tree.delete(item)
            
        # Collect unique floors from rooms
        floors = set()
        # Add standard profiles
        for p in FLOOR_PROFILES:
            if p != "[Not Set]":
                floors.add(p)
        
        # Add custom floors
        floors.update(self.custom_floors)
                
        # Add existing used floors from rooms
        for room in self.app.project.rooms:
            f = self.app._room_attr(room, 'floor_profile', 'floor_profile', '[Not Set]')
            if f and f != "[Not Set]":
                floors.add(f)
        
        # Calculate totals per floor
        floor_data: Dict[str, Dict[str, float]] = {}
        for f in floors:
            floor_data[f] = {'count': 0, 'area': 0.0}
        
        for room in self.app.project.rooms:
            rf = self.app._room_attr(room, 'floor_profile', 'floor_profile', '[Not Set]')
            if rf in floor_data:
                floor_data[rf]['count'] += 1
                floor_data[rf]['area'] += self._safe_float(
                    self.app._room_attr(room, 'area', 'area', 0.0)
                )
                
        for f in sorted(list(floors)):
            data = floor_data[f]
            self.floors_tree.insert('', tk.END, values=(f, data['count'], f"{data['area']:.1f}"))

    def _on_floor_selected(self, event):
        selection = self.floors_tree.selection()
        if not selection:
            self.selected_floor = None
            self._clear_assigned_view()
            return
            
        self.selected_floor = self.floors_tree.item(selection[0], 'values')[0]
        self._invalidate_ctx()  # Rebuild context for new selection
        self._refresh_assigned_rooms()
        self._calculate_totals()

    def _refresh_assigned_rooms(self):
        for item in self.assigned_tree.get_children():
            self.assigned_tree.delete(item)
            
        if not self.selected_floor:
            return
        
        for room in self.app.project.rooms:
            rf = self.app._room_attr(room, 'floor_profile', 'floor_profile', '[Not Set]')
            if rf == self.selected_floor:
                name = self.app._room_name(room)
                metrics = self._get_metrics_for_room(room)
                if not metrics:
                    continue
                area = metrics.ceiling_area  # floor area
                walls = metrics.walls_gross
                rtype = self.app._room_attr(room, 'room_type', 'room_type', '[Not Set]')
                self.assigned_tree.insert('', tk.END, values=(name, f"{area:.2f}", f"{walls:.2f}", rtype))

    def _refresh_available_rooms(self):
        for item in self.available_tree.get_children():
            self.available_tree.delete(item)
            
        for room in self.app.project.rooms:
            rf = self.app._room_attr(room, 'floor_profile', 'floor_profile', '[Not Set]')
            # Show all rooms, but indicate current floor
            name = self.app._room_name(room)
            area = self._safe_float(self.app._room_attr(room, 'area', 'area', 0.0))
            self.available_tree.insert('', tk.END, values=(name, f"{area:.2f}", rf))

    def _add_floor(self):
        name = simpledialog.askstring("New Floor", "Enter Floor Name (e.g., 'Second Floor'):", parent=self.frame)
        if name and name.strip():
            name = name.strip()
            # Add to project's custom floors
            floors = self.custom_floors
            floors.add(name)
            self.custom_floors = floors
            
            self._refresh_floors_list()
            # Auto-select the new floor
            for item in self.floors_tree.get_children():
                if self.floors_tree.item(item, 'values')[0] == name:
                    self.floors_tree.selection_set(item)
                    self.floors_tree.see(item)
                    self.selected_floor = name
                    self._refresh_assigned_rooms()
                    break
            
            self.app.update_status(f"Added floor: {name}", icon="➕")

    def _delete_floor(self):
        if not self.selected_floor:
            messagebox.showwarning("No Selection", "Select a floor first.")
            return
        if messagebox.askyesno("Delete Floor", f"Remove floor '{self.selected_floor}'? Rooms will be unassigned."):
            # Unassign all rooms
            for room in self.app.project.rooms:
                rf = self.app._room_attr(room, 'floor_profile', 'floor_profile', '[Not Set]')
                if rf == self.selected_floor:
                    if isinstance(room, dict):
                        room['floor_profile'] = '[Not Set]'
                    else:
                        room.floor_profile = '[Not Set]'
            
            # Remove from custom floors if present
            floors = self.custom_floors
            floors.discard(self.selected_floor)
            self.custom_floors = floors
            
            deleted_floor = self.selected_floor
            self.selected_floor = None
            
            self._invalidate_ctx()
            self._refresh_floors_list()
            self._clear_assigned_view()
            self._refresh_available_rooms()
            
            self.app.update_status(f"Deleted floor: {deleted_floor}", icon="🗑️")

    def _assign_rooms(self):
        if not self.selected_floor:
            messagebox.showwarning("No Floor", "Select a floor first.")
            return
            
        selection = self.available_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Select rooms to assign from the Available Rooms list.")
            return
            
        assigned_count = 0
        for item in selection:
            vals = self.available_tree.item(item, 'values')
            name = vals[0]
            # Find room
            for room in self.app.project.rooms:
                if self.app._room_name(room) == name:
                    if isinstance(room, dict):
                        room['floor_profile'] = self.selected_floor
                    else:
                        room.floor_profile = self.selected_floor
                    assigned_count += 1
                    break
        
        self._invalidate_ctx()  # Data changed
        self._refresh_assigned_rooms()
        self._refresh_available_rooms()
        self._refresh_floors_list()
        self._calculate_totals()
        
        if assigned_count > 0:
            self.app.update_status(f"Assigned {assigned_count} room(s) to {self.selected_floor}", icon="✅")

    def _unassign_rooms(self):
        selection = self.assigned_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Select rooms to remove from this floor.")
            return
        
        unassigned_count = 0
        for item in selection:
            vals = self.assigned_tree.item(item, 'values')
            name = vals[0]
            for room in self.app.project.rooms:
                if self.app._room_name(room) == name:
                    if isinstance(room, dict):
                        room['floor_profile'] = '[Not Set]'
                    else:
                        room.floor_profile = '[Not Set]'
                    unassigned_count += 1
                    break
        
        self._invalidate_ctx()  # Data changed
        self._refresh_assigned_rooms()
        self._refresh_available_rooms()
        self._refresh_floors_list()
        self._calculate_totals()
        
        if unassigned_count > 0:
            self.app.update_status(f"Removed {unassigned_count} room(s) from {self.selected_floor}", icon="🗑️")

    def _clear_assigned_view(self):
        for item in self.assigned_tree.get_children():
            self.assigned_tree.delete(item)
        self.lbl_total_area.config(text="Total Area: 0.00 m²")
        self.lbl_total_walls.config(text="Walls: 0.00 m²")
        self.lbl_total_plaster.config(text="Plaster: 0.00 m²")
        self.lbl_total_ceramic.config(text="Ceramic: 0.00 m²")
        self.lbl_total_paint.config(text="Paint: 0.00 m²")

    def _calculate_totals(self):
        if not self.selected_floor:
            self._clear_assigned_view()
            return
            
        t_area = 0.0
        t_walls = 0.0
        t_plaster = 0.0
        t_ceramic = 0.0
        t_paint = 0.0

        for room in self.app.project.rooms:
            rf = self.app._room_attr(room, 'floor_profile', 'floor_profile', '[Not Set]')
            if rf == self.selected_floor:
                metrics = self._get_metrics_for_room(room)
                if not metrics:
                    continue
                t_area += metrics.ceiling_area
                t_walls += metrics.walls_gross
                t_plaster += metrics.plaster_total
                t_ceramic += (metrics.ceramic_wall + metrics.ceramic_floor + metrics.ceramic_ceiling)
                t_paint += metrics.paint_total
                
        self.lbl_total_area.config(text=f"Total Area: {t_area:.2f} m²")
        self.lbl_total_walls.config(text=f"Walls: {t_walls:.2f} m²")
        self.lbl_total_plaster.config(text=f"Plaster: {t_plaster:.2f} m²")
        self.lbl_total_ceramic.config(text=f"Ceramic: {t_ceramic:.2f} m²")
        self.lbl_total_paint.config(text=f"Paint: {t_paint:.2f} m²")
    
    def refresh_data(self):
        """Refresh all data in the tab. Called by main app when data changes."""
        self._invalidate_ctx()  # Clear cache when data changes externally
        self._refresh_floors_list()
        self._refresh_available_rooms()
        if self.selected_floor:
            self._refresh_assigned_rooms()
            self._calculate_totals()
