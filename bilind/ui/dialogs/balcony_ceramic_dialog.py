"""
Advanced Balcony Ceramic Dialog
Allows detailed control of ceramic on each balcony wall with opening deductions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional


class BalconyCeramicDialog:
    """Advanced dialog for balcony ceramic with per-wall control and opening assignment."""
    
    def __init__(self, parent, app, room):
        """
        Args:
            parent: Parent widget
            app: Main application instance
            room: Room dict or object (must be a balcony)
        """
        self.parent = parent
        self.app = app
        self.room = room
        self.result = None
        
        # Extract room data
        self.room_name = app._room_name(room)
        
        # Get balcony segments
        if isinstance(room, dict):
            self.segments = room.get('wall_segments', []) or []
            self.is_balcony = room.get('is_balcony', False)
        else:
            self.segments = getattr(room, 'wall_segments', []) or []
            self.is_balcony = getattr(room, 'is_balcony', False)
        
        if not self.is_balcony or not self.segments:
            messagebox.showwarning("ليس بلكون", "هذه الغرفة غير مُعدَّة كبلكون مع تحديد جدران البلكون.")
            return
        
        # Get room openings
        self.openings_summary = app.get_room_opening_summary(room)
        self.door_ids = self.openings_summary.get('door_ids', [])
        self.window_ids = self.openings_summary.get('window_ids', [])
        
        # UI state
        self.wall_ceramic_vars = []  # [(enabled_var, height_var, start_height_var)]
        self.wall_opening_vars = []  # [[(opening_id, var)...] for each wall]
        
        self._create_dialog()
    
    def _create_dialog(self):
        """Create the dialog UI."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"🏗️ سيراميك البلكون: {self.room_name}")
        self.dialog.geometry("900x700")
        self.dialog.resizable(True, True)
        self.dialog.minsize(850, 650)
        self.dialog.configure(bg=self.app.colors['bg_secondary'])
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main container
        main = ttk.Frame(self.dialog, padding=(16, 12), style='Main.TFrame')
        main.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Frame(main, style='Main.TFrame')
        header.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(
            header,
            text=f"🏗️ إعدادات سيراميك البلكون المتقدمة",
            font=('Segoe UI Semibold', 14)
        ).pack(anchor='w')
        
        ttk.Label(
            header,
            text="حدد ارتفاع السيراميك لكل جدار وربط الفتحات لخصمها تلقائياً",
            foreground=self.app.colors['text_secondary'],
            font=('Segoe UI', 9)
        ).pack(anchor='w', pady=(4, 0))
        
        # Scrollable content
        canvas_frame = ttk.Frame(main, style='Main.TFrame')
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        
        canvas = tk.Canvas(canvas_frame, bg=self.app.colors['bg_secondary'], highlightthickness=0)
        scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        content = ttk.Frame(canvas, style='Main.TFrame')
        canvas.create_window((0, 0), window=content, anchor='nw')
        
        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox('all'))
        canvas.bind('<Configure>', _on_configure)
        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        
        # Wall configuration cards
        for i, seg in enumerate(self.segments):
            self._create_wall_card(content, i, seg)
        
        # Buttons
        btn_frame = ttk.Frame(main, style='Main.TFrame')
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(
            btn_frame,
            text="✅ Apply Ceramic",
            command=self._on_apply,
            style='Accent.TButton',
            width=20
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(
            btn_frame,
            text="❌ Cancel",
            command=self.dialog.destroy,
            style='Secondary.TButton',
            width=15
        ).pack(side=tk.LEFT)
    
    def _create_wall_card(self, parent, wall_idx: int, segment: dict):
        """Create a card for one wall."""
        length = float(segment.get('length', 0.0) or 0.0)
        height = float(segment.get('height', 0.0) or 0.0)
        
        # Get existing opening assignments from segment
        existing_openings = segment.get('opening_ids', []) or []
        
        card = ttk.LabelFrame(
            parent,
            text=f"Wall {wall_idx + 1} - {length:.2f}m × {height:.2f}m",
            padding=(12, 10),
            style='Card.TLabelframe'
        )
        card.pack(fill=tk.X, pady=8, padx=4)
        
        # Show existing openings if any
        if existing_openings:
            existing_frame = ttk.Frame(card, style='Main.TFrame')
            existing_frame.pack(fill=tk.X, pady=(0, 8))
            ttk.Label(
                existing_frame,
                text=f"📌 Currently assigned: {', '.join(existing_openings)}",
                foreground=self.app.colors.get('success', '#10b981'),
                font=('Segoe UI', 9, 'italic')
            ).pack(anchor='w')
        
        # Enable ceramic checkbox
        enabled_var = tk.BooleanVar(value=True)
        enable_check = ttk.Checkbutton(
            card,
            text="🧱 Add ceramic to this wall",
            variable=enabled_var,
            command=lambda: self._toggle_wall_controls(wall_idx, enabled_var.get())
        )
        enable_check.pack(anchor='w', pady=(0, 8))
        
        # Controls frame
        controls = ttk.Frame(card, style='Main.TFrame')
        controls.pack(fill=tk.X)
        
        # Ceramic height settings
        height_frame = ttk.Frame(controls, style='Main.TFrame')
        height_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(height_frame, text="Ceramic Start Height (m):").pack(side=tk.LEFT, padx=(0, 4))
        start_var = tk.StringVar(value="0.0")
        ttk.Entry(height_frame, textvariable=start_var, width=10).pack(side=tk.LEFT, padx=4)
        
        ttk.Label(height_frame, text="Ceramic End Height (m):").pack(side=tk.LEFT, padx=(12, 4))
        end_var = tk.StringVar(value="1.6")
        ttk.Entry(height_frame, textvariable=end_var, width=10).pack(side=tk.LEFT, padx=4)
        
        # Openings assignment
        if self.door_ids or self.window_ids:
            openings_frame = ttk.LabelFrame(controls, text="Assign Openings to This Wall", padding=(8, 6))
            openings_frame.pack(fill=tk.X, pady=(4, 0))
            
            opening_vars = []
            
            # Doors
            if self.door_ids:
                ttk.Label(openings_frame, text="🚪 Doors:", font=('Segoe UI Semibold', 9)).pack(anchor='w', pady=(0, 4))
                for door_id in self.door_ids:
                    door = self._find_opening_by_id(door_id, 'door')
                    if door:
                        # Pre-select if already assigned to this wall
                        is_assigned = door_id in existing_openings
                        var = tk.BooleanVar(value=is_assigned)
                        door_type = self.app._opening_attr(door, 'type', 'material_type', '-')
                        w = self.app._opening_attr(door, 'w', 'width', 0.0)
                        h = self.app._opening_attr(door, 'h', 'height', 0.0)
                        
                        ttk.Checkbutton(
                            openings_frame,
                            text=f"  {door_id} ({door_type} - {w:.2f}×{h:.2f}m)",
                            variable=var
                        ).pack(anchor='w', pady=2)
                        
                        opening_vars.append((door_id, 'door', var))
            
            # Windows
            if self.window_ids:
                ttk.Label(openings_frame, text="🪟 Windows:", font=('Segoe UI Semibold', 9)).pack(anchor='w', pady=(8, 4))
                for win_id in self.window_ids:
                    window = self._find_opening_by_id(win_id, 'window')
                    if window:
                        # Pre-select if already assigned to this wall
                        is_assigned = win_id in existing_openings
                        var = tk.BooleanVar(value=is_assigned)
                        win_type = self.app._opening_attr(window, 'type', 'material_type', '-')
                        w = self.app._opening_attr(window, 'w', 'width', 0.0)
                        h = self.app._opening_attr(window, 'h', 'height', 0.0)
                        
                        ttk.Checkbutton(
                            openings_frame,
                            text=f"  {win_id} ({win_type} - {w:.2f}×{h:.2f}m)",
                            variable=var
                        ).pack(anchor='w', pady=2)
                        
                        opening_vars.append((win_id, 'window', var))
            
            self.wall_opening_vars.append(opening_vars)
        else:
            self.wall_opening_vars.append([])
        
        # Store variables
        self.wall_ceramic_vars.append((enabled_var, end_var, start_var, controls))
    
    def _toggle_wall_controls(self, wall_idx: int, enabled: bool):
        """Enable/disable controls for a wall."""
        if wall_idx < len(self.wall_ceramic_vars):
            controls_frame = self.wall_ceramic_vars[wall_idx][3]
            for child in controls_frame.winfo_children():
                child.configure(state='normal' if enabled else 'disabled')
    
    def _find_opening_by_id(self, opening_id: str, opening_type: str):
        """Find opening by ID."""
        storage = self.app.project.doors if opening_type == 'door' else self.app.project.windows
        for opening in storage:
            if self.app._opening_name(opening) == opening_id:
                return opening
        return None
    
    def _on_apply(self):
        """Apply ceramic zones for enabled walls."""
        from bilind.models.finish import CeramicZone
        
        # 1. Clear existing balcony zones for this room to prevent duplicates
        self._clear_existing_balcony_zones()
        
        total_area = 0.0
        zones_created = 0
        
        for wall_idx, (enabled_var, end_var, start_var, _) in enumerate(self.wall_ceramic_vars):
            if not enabled_var.get():
                continue  # Skip disabled walls
            
            try:
                start_h = float(start_var.get() or 0.0)
                end_h = float(end_var.get() or 0.0)
                
                if end_h <= start_h:
                    messagebox.showerror("Invalid Height", f"Wall {wall_idx+1}: End height must be greater than start height.")
                    return
                
                ceramic_height = end_h - start_h
                wall_length = float(self.segments[wall_idx].get('length', 0.0) or 0.0)
                
                if wall_length <= 0:
                    continue
                
                # Calculate base area
                base_area = wall_length * ceramic_height
                
                # Deduct assigned openings AND save assignments to segment
                deductions = 0.0
                assigned_opening_ids = []
                
                if wall_idx < len(self.wall_opening_vars):
                    for opening_id, opening_type, var in self.wall_opening_vars[wall_idx]:
                        if var.get():  # Opening assigned to this wall
                            assigned_opening_ids.append(opening_id)
                            
                            opening = self._find_opening_by_id(opening_id, opening_type)
                            if opening:
                                o_width = float(self.app._opening_attr(opening, 'w', 'width', 0.0) or 0.0)
                                o_height = float(self.app._opening_attr(opening, 'h', 'height', 0.0) or 0.0)
                                o_placement = float(self.app._opening_attr(opening, 'placement_height', 'placement_height', 0.0) or 0.0)
                                o_top = o_placement + o_height
                                
                                # Calculate overlap
                                overlap_start = max(start_h, o_placement)
                                overlap_end = min(end_h, o_top)
                                
                                if overlap_end > overlap_start:
                                    overlap_height = overlap_end - overlap_start
                                    deductions += o_width * overlap_height
                
                # Save opening assignments to wall segment
                if isinstance(self.room, dict):
                    if 'wall_segments' not in self.room:
                        self.room['wall_segments'] = []
                    if wall_idx < len(self.room['wall_segments']):
                        self.room['wall_segments'][wall_idx]['opening_ids'] = assigned_opening_ids
                else:
                    if not hasattr(self.room, 'wall_segments'):
                        setattr(self.room, 'wall_segments', [])
                    if wall_idx < len(self.room.wall_segments):
                        self.room.wall_segments[wall_idx]['opening_ids'] = assigned_opening_ids
                
                net_area = max(0.0, base_area - deductions)
                
                if net_area > 0:
                    zone = CeramicZone(
                        name=f"[Balcony] Wall {wall_idx+1} - {self.room_name}",
                        category='Other',
                        perimeter=wall_length,
                        height=ceramic_height,
                        start_height=start_h,
                        surface_type='wall',
                        room_name=self.room_name
                    )
                    zone.effective_area = float(net_area)
                    
                    self.app.project.ceramic_zones.append(zone)
                    total_area += net_area
                    zones_created += 1
                
            except ValueError as e:
                messagebox.showerror("Invalid Input", f"Wall {wall_idx+1}: Please enter valid numeric values.\n{e}")
                return
        
        # 2. Recalculate totals for the room
        self._recalculate_room_totals()
        
        if zones_created > 0:
            self.result = {'zones': zones_created, 'area': total_area}
            messagebox.showinfo("Success", f"✅ Created {zones_created} ceramic zone(s)\n\nTotal area: {total_area:.2f} m²")
            self.dialog.destroy()
        else:
            messagebox.showwarning("No Ceramic", "No ceramic zones were created. Please enable at least one wall.")
            
    def _clear_existing_balcony_zones(self):
        """Remove existing [Balcony] zones for this room."""
        kept_zones = []
        for z in (self.app.project.ceramic_zones or []):
            z_name = getattr(z, 'name', '') if not isinstance(z, dict) else z.get('name', '')
            z_room = getattr(z, 'room_name', '') if not isinstance(z, dict) else z.get('room_name', '')
            
            is_balcony_zone = str(z_name).startswith('[Balcony]')
            is_for_room = (z_room == self.room_name) or (self.room_name in str(z_name))
            
            if is_balcony_zone and is_for_room:
                continue
            kept_zones.append(z)
        self.app.project.ceramic_zones = kept_zones

    def _recalculate_room_totals(self):
        """Recalculate ceramic totals for the room."""
        total_area = 0.0
        breakdown = {}
        
        for z in self.app.project.ceramic_zones:
            z_name = getattr(z, 'name', '') if not isinstance(z, dict) else z.get('name', '')
            z_room = getattr(z, 'room_name', '') if not isinstance(z, dict) else z.get('room_name', '')
            
            if (z_room == self.room_name) or (self.room_name in str(z_name)):
                area = float(getattr(z, 'effective_area', 0) or getattr(z, 'perimeter', 0) * getattr(z, 'height', 0))
                if isinstance(z, dict):
                    area = float(z.get('effective_area', 0) or z.get('perimeter', 0) * z.get('height', 0))
                
                stype = getattr(z, 'surface_type', 'wall') if not isinstance(z, dict) else z.get('surface_type', 'wall')
                
                total_area += area
                breakdown[stype] = breakdown.get(stype, 0.0) + area
            
        if isinstance(self.room, dict):
            self.room['ceramic_area'] = total_area
            self.room['ceramic_breakdown'] = breakdown
        else:
            self.room.ceramic_area = total_area
            self.room.ceramic_breakdown = breakdown
    
    def show(self):
        """Show dialog and return result."""
        if hasattr(self, 'dialog'):
            self.dialog.wait_window()
            return self.result
        return None
