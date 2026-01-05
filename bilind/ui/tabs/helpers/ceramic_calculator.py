"""
Smart Ceramic Calculator Dialog
Extracted from room_manager_tab.py for better maintainability.

This module provides an advanced ceramic calculator with:
- Quick presets for common scenarios (bathroom, kitchen, balcony)
- Smart room detection based on room type
- Opening deduction calculations
- Floor and wall ceramic support
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Callable
from bilind.models.finish import CeramicZone
from bilind.ui.tabs.helpers.room_adapter import RoomAdapter
from bilind.calculations.unified_calculator import UnifiedCalculator
import statistics

if TYPE_CHECKING:
    from bilind_main import BilindEnhanced


# Preset definitions with smart defaults
CERAMIC_PRESETS = {
    'bathroom_full': {
        'name': 'حمام كامل', 
        'icon': '🚿', 
        'surface': 'wall', 
        # Use project.default_wall_height at runtime (avoids hardcoding 2.4m)
        'height': None,
        'category': 'Bathroom', 
        'floor': True
    },
    'bathroom_half': {
        'name': 'حمام نصفي', 
        'icon': '🛁', 
        'surface': 'wall', 
        'height': 1.5, 
        'category': 'Bathroom', 
        'floor': True
    },
    'kitchen_backsplash': {
        'name': 'مطبخ (خلف الكاونتر)', 
        'icon': '🍳', 
        'surface': 'wall', 
        'height': 0.6, 
        'start': 0.9, 
        'category': 'Kitchen', 
        'floor': False
    },
    'kitchen_full': {
        'name': 'مطبخ كامل', 
        'icon': '🏠', 
        'surface': 'wall', 
        # Use project.default_wall_height at runtime (avoids hardcoding 2.4m)
        'height': None,
        'category': 'Kitchen', 
        'floor': True
    },
    'floor_only': {
        'name': 'أرضية فقط', 
        'icon': '🟫', 
        'surface': 'floor', 
        'height': 0, 
        'category': 'Other', 
        'floor': True
    },
    'balcony': {
        'name': 'بلكون/شرفة', 
        'icon': '🌅', 
        'surface': 'wall', 
        'height': 1.2, 
        'category': 'Other', 
        'floor': True
    },
}


class CeramicCalculatorDialog:
    """
    Smart Ceramic Calculator Dialog.
    
    Provides an advanced interface for calculating and adding ceramic zones
    to rooms with intelligent defaults and presets.
    """
    
    def __init__(self, parent_frame: tk.Widget, app: 'BilindEnhanced', 
                 on_complete: Optional[Callable] = None):
        """
        Initialize the ceramic calculator dialog.
        
        Args:
            parent_frame: Parent tkinter widget
            app: Main application instance (BilindEnhanced)
            on_complete: Callback function when ceramic is added
        """
        self.parent = parent_frame
        self.app = app
        self.on_complete = on_complete
        self.dialog = None
        self.room_vars: List[tuple] = []  # [(BooleanVar, room), ...]
        
        # State variables (will be initialized in _create_ui)
        self.surface_var = None
        self.height_var = None
        self.start_height_var = None
        self.category_var = None
        self.include_floor_var = None
        self.auto_deduct_var = None
        self.preview_label = None
    
    def show(self):
        """Show the ceramic calculator dialog."""
        if not self.app.project.rooms:
            messagebox.showinfo("لا توجد غرف", "أضف غرف أولاً قبل إضافة السيراميك.")
            return
        
        self._create_dialog()
        self._create_ui()
    
    def _create_dialog(self):
        """Create the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("🧠 حاسبة السيراميك الذكية - Smart Ceramic Calculator")
        self.dialog.configure(bg=self.app.colors['bg_secondary'])
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.geometry("850x750")
        self.dialog.resizable(True, True)
        self.dialog.minsize(800, 700)
    
    def _create_ui(self):
        """Create the main UI components."""
        # Main scrollable container
        main_canvas = tk.Canvas(
            self.dialog, 
            bg=self.app.colors['bg_secondary'], 
            highlightthickness=0
        )
        main_scrollbar = ttk.Scrollbar(
            self.dialog, 
            orient=tk.VERTICAL, 
            command=main_canvas.yview
        )
        container = ttk.Frame(main_canvas, padding=(16, 12), style='Main.TFrame')
        
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create window item and store its ID
        window_item = main_canvas.create_window((0, 0), window=container, anchor='nw')
        
        def on_frame_configure(e):
            """Update scrollregion when frame size changes"""
            main_canvas.configure(scrollregion=main_canvas.bbox('all'))
            
        def on_canvas_configure(e):
            """Resize frame to match canvas width"""
            # Subtract a bit for scrollbar if needed, or just use full width
            main_canvas.itemconfig(window_item, width=e.width)
            
        container.bind("<Configure>", on_frame_configure)
        main_canvas.bind("<Configure>", on_canvas_configure)
        
        # Initialize state variables
        self.surface_var = tk.StringVar(value='wall')
        self.height_var = tk.StringVar(value='1.5')
        self.start_height_var = tk.StringVar(value='0.0')
        self.category_var = tk.StringVar(value='Other')
        self.include_floor_var = tk.BooleanVar(value=False)
        self.auto_deduct_var = tk.BooleanVar(value=True)
        
        # Create sections
        self._create_presets_section(container)
        self._create_config_section(container)
        self._create_rooms_section(container)
        self._create_preview_section(container)
        self._create_buttons_section(container)
        
        # Initial preview update
        self._update_preview()
    
    def _create_presets_section(self, container: ttk.Frame):
        """Create quick presets section."""
        presets_frame = ttk.LabelFrame(
            container, 
            text="⚡ إعدادات سريعة - Quick Presets", 
            padding=(12, 10), 
            style='Card.TLabelframe'
        )
        presets_frame.pack(fill=tk.X, pady=(0, 12))
        
        preset_desc = ttk.Label(
            presets_frame, 
            text="اختر نوع السيراميك للتطبيق السريع:", 
            foreground=self.app.colors['text_secondary']
        )
        preset_desc.pack(anchor='w', pady=(0, 8))
        
        presets_btns = ttk.Frame(presets_frame, style='Main.TFrame')
        presets_btns.pack(fill=tk.X)
        
        # Create preset buttons
        for i, (key, preset) in enumerate(CERAMIC_PRESETS.items()):
            btn = ttk.Button(
                presets_btns,
                text=f"{preset['icon']} {preset['name']}",
                command=lambda k=key: self._apply_preset(k),
                style='Secondary.TButton',
                width=18
            )
            btn.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky='ew')
        
        for i in range(3):
            presets_btns.columnconfigure(i, weight=1)
    
    def _create_config_section(self, container: ttk.Frame):
        """Create configuration section."""
        config_frame = ttk.LabelFrame(
            container, 
            text="⚙️ إعدادات السيراميك - Configuration", 
            padding=(12, 10), 
            style='Card.TLabelframe'
        )
        config_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Row 1: Surface Type & Category
        row1 = ttk.Frame(config_frame, style='Main.TFrame')
        row1.pack(fill=tk.X, pady=(0, 8))
        
        # Surface type
        ttk.Label(row1, text="السطح:", width=10).pack(side=tk.LEFT)
        surface_combo = ttk.Combobox(
            row1, 
            textvariable=self.surface_var, 
            values=['wall', 'floor', 'ceiling'],
            state='readonly',
            width=12
        )
        surface_combo.pack(side=tk.LEFT, padx=(0, 20))
        surface_combo.bind('<<ComboboxSelected>>', lambda e: self._update_preview())
        
        # Category
        ttk.Label(row1, text="التصنيف:", width=10).pack(side=tk.LEFT)
        category_combo = ttk.Combobox(
            row1, 
            textvariable=self.category_var, 
            values=['Bathroom', 'Kitchen', 'Other'],
            state='readonly',
            width=12
        )
        category_combo.pack(side=tk.LEFT)
        
        # Row 2: Height settings
        row2 = ttk.Frame(config_frame, style='Main.TFrame')
        row2.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(row2, text="الارتفاع (م):", width=12).pack(side=tk.LEFT)
        height_entry = ttk.Entry(row2, textvariable=self.height_var, width=8)
        height_entry.pack(side=tk.LEFT, padx=(0, 20))
        height_entry.bind('<KeyRelease>', lambda e: self._update_preview())
        
        ttk.Label(row2, text="بداية من (م):", width=12).pack(side=tk.LEFT)
        start_entry = ttk.Entry(row2, textvariable=self.start_height_var, width=8)
        start_entry.pack(side=tk.LEFT)
        start_entry.bind('<KeyRelease>', lambda e: self._update_preview())
        
        # Row 3: Options
        row3 = ttk.Frame(config_frame, style='Main.TFrame')
        row3.pack(fill=tk.X)
        
        floor_cb = ttk.Checkbutton(
            row3, 
            text="تضمين الأرضية", 
            variable=self.include_floor_var,
            command=self._update_preview
        )
        floor_cb.pack(side=tk.LEFT, padx=(0, 20))
        
        deduct_cb = ttk.Checkbutton(
            row3, 
            text="خصم الفتحات تلقائياً", 
            variable=self.auto_deduct_var
        )
        deduct_cb.pack(side=tk.LEFT)
    
    def _create_rooms_section(self, container: ttk.Frame):
        """Create rooms selection section."""
        rooms_frame = ttk.LabelFrame(
            container, 
            text="🏠 اختر الغرف - Select Rooms", 
            padding=(12, 10), 
            style='Card.TLabelframe'
        )
        rooms_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        
        # Select all checkbox
        select_all_var = tk.BooleanVar(value=False)
        
        def toggle_all():
            state = select_all_var.get()
            for var, _ in self.room_vars:
                var.set(state)
            self._update_preview()
        
        select_all_cb = ttk.Checkbutton(
            rooms_frame,
            text="✓ تحديد الكل",
            variable=select_all_var,
            command=toggle_all
        )
        select_all_cb.pack(anchor='w', pady=(0, 8))
        
        # Scrollable room list
        rooms_canvas = tk.Canvas(
            rooms_frame, 
            bg=self.app.colors['bg_primary'], 
            highlightthickness=1,
            highlightbackground=self.app.colors['border'],
            height=200
        )
        rooms_scrollbar = ttk.Scrollbar(
            rooms_frame, 
            orient=tk.VERTICAL, 
            command=rooms_canvas.yview
        )
        rooms_inner = ttk.Frame(rooms_canvas, style='Main.TFrame')
        
        rooms_canvas.configure(yscrollcommand=rooms_scrollbar.set)
        rooms_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        rooms_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rooms_canvas.create_window((0, 0), window=rooms_inner, anchor='nw')
        
        def on_rooms_configure(e):
            rooms_canvas.configure(scrollregion=rooms_canvas.bbox('all'))
        rooms_inner.bind("<Configure>", on_rooms_configure)
        
        # Populate rooms
        self.room_vars = []
        for i, room in enumerate(self.app.project.rooms):
            var = tk.BooleanVar(value=False)
            name = self.app._room_name(room)
            area = float(self.app._room_attr(room, 'area', 'area', 0.0) or 0.0)
            perim = float(self.app._room_attr(room, 'perim', 'perimeter', 0.0) or 0.0)
            room_type = self.app._room_attr(room, 'room_type', 'room_type', '')
            
            cb = ttk.Checkbutton(
                rooms_inner,
                text=f"{name} | {area:.1f}م² | محيط: {perim:.1f}م | {room_type}",
                variable=var,
                command=self._update_preview
            )
            cb.grid(row=i, column=0, sticky='w', padx=4, pady=2)
            self.room_vars.append((var, room))
    
    def _create_preview_section(self, container: ttk.Frame):
        """Create preview section."""
        preview_frame = ttk.LabelFrame(
            container, 
            text="📊 المعاينة - Preview", 
            padding=(12, 10), 
            style='Card.TLabelframe'
        )
        preview_frame.pack(fill=tk.X, pady=(0, 12))
        
        self.preview_label = ttk.Label(
            preview_frame,
            text="اختر غرف لرؤية المعاينة...",
            foreground=self.app.colors['text_secondary'],
            wraplength=700
        )
        self.preview_label.pack(anchor='w')
    
    def _create_buttons_section(self, container: ttk.Frame):
        """Create action buttons section."""
        btns_frame = ttk.Frame(container, style='Main.TFrame')
        btns_frame.pack(fill=tk.X, pady=(8, 0))
        
        ttk.Button(
            btns_frame,
            text="❌ إلغاء",
            command=self.dialog.destroy,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(
            btns_frame,
            text="✅ إضافة السيراميك",
            command=self._apply_ceramic,
            style='Accent.TButton'
        ).pack(side=tk.RIGHT)
    
    def _apply_preset(self, preset_key: str):
        """Apply a preset configuration."""
        preset = CERAMIC_PRESETS[preset_key]
        self.surface_var.set(preset['surface'])
        self.category_var.set(preset['category'])
        self.include_floor_var.set(preset.get('floor', False))
        self.start_height_var.set(str(preset.get('start', 0.0)))
        
        # Auto-select matching rooms
        for var, room in self.room_vars:
            room_type = str(self.app._room_attr(room, 'room_type', 'room_type', '') or '')
            name = str(self.app._room_name(room) or '').lower()
            
            should_select = False
            if preset['category'] == 'Bathroom':
                should_select = any(k in room_type or k in name for k in ['حمام', 'bath', 'wc', 'toilet'])
            elif preset['category'] == 'Kitchen':
                should_select = any(k in room_type or k in name for k in ['مطبخ', 'kitchen'])
            elif preset_key == 'balcony':
                should_select = any(k in room_type or k in name for k in ['بلكون', 'شرفة', 'balcony', 'terrace'])
            
            if should_select:
                var.set(True)
        
        # Resolve height (smart logic)
        preset_h = preset.get('height', None)
        if preset_h in (None, '', 0, 0.0):
            # Try to resolve from selected rooms
            selected_rooms = [room for var, room in self.room_vars if var.get()]
            resolved_heights = []
            
            if selected_rooms:
                calc = UnifiedCalculator(self.app.project)
                for room in selected_rooms:
                    adapter = RoomAdapter(room)
                    
                    # Priority 1: Explicit wall_height
                    wh = adapter.wall_height
                    if wh not in (None, '', 0, 0.0):
                        resolved_heights.append(float(wh))
                        continue
                        
                    # Priority 2: Derive from walls
                    walls_gross = calc.calculate_walls_gross(room)
                    perim = adapter.perimeter
                    if walls_gross > 0 and perim > 0:
                        resolved_heights.append(walls_gross / perim)
            
            if resolved_heights:
                # Use the most common height (mode) to handle outliers
                try:
                    preset_h = statistics.mode(resolved_heights)
                except:
                    preset_h = resolved_heights[0]
            
            # Fallback to project default if still not found
            if preset_h in (None, '', 0, 0.0):
                preset_h = float(getattr(self.app.project, 'default_wall_height', 3.0) or 3.0)
                
        self.height_var.set(str(preset_h))
        
        self._update_preview()
    
    def _update_preview(self):
        """Update the preview display."""
        selected = [(var, room) for var, room in self.room_vars if var.get()]
        
        if not selected:
            self.preview_label.config(text="اختر غرف لرؤية المعاينة...")
            return
        
        try:
            height = float(self.height_var.get() or 0)
        except ValueError:
            height = 0
        
        surface = self.surface_var.get()
        include_floor = self.include_floor_var.get()
        
        total_wall = 0.0
        total_floor = 0.0
        
        for _, room in selected:
            perim = float(self.app._room_attr(room, 'perim', 'perimeter', 0.0) or 0.0)
            area = float(self.app._room_attr(room, 'area', 'area', 0.0) or 0.0)
            
            if surface == 'wall' and height > 0:
                total_wall += perim * height
            elif surface == 'floor':
                total_floor += area
            elif surface == 'ceiling':
                total_floor += area  # ceiling uses area
            
            if include_floor and surface == 'wall':
                total_floor += area
        
        preview_text = f"📦 {len(selected)} غرفة محددة"
        if total_wall > 0:
            preview_text += f" | جدران: {total_wall:.1f} م²"
        if total_floor > 0:
            preview_text += f" | أرضيات: {total_floor:.1f} م²"
        
        total = total_wall + total_floor
        preview_text += f" | الإجمالي: {total:.1f} م²"
        
        self.preview_label.config(text=preview_text)
    
    def _apply_ceramic(self):
        """Apply ceramic zones to selected rooms."""
        selected = [(var, room) for var, room in self.room_vars if var.get()]
        
        if not selected:
            messagebox.showwarning("لم يتم التحديد", "الرجاء تحديد غرفة واحدة على الأقل.")
            return
        
        try:
            height = float(self.height_var.get() or 0)
            start_height = float(self.start_height_var.get() or 0)
        except ValueError:
            messagebox.showerror("خطأ", "قيم الارتفاع غير صالحة.")
            return
        
        surface = self.surface_var.get()
        category = self.category_var.get()
        include_floor = self.include_floor_var.get()
        auto_deduct = self.auto_deduct_var.get()
        
        total_added = 0.0
        zones_count = 0
        
        # Determine types to process (for clearing duplicates)
        types_to_process = []
        if surface == 'wall': types_to_process.append('wall')
        elif surface == 'floor': types_to_process.append('floor')
        elif surface == 'ceiling': types_to_process.append('ceiling')
        
        if include_floor and 'floor' not in types_to_process:
            types_to_process.append('floor')
        
        for _, room in selected:
            # Clear existing auto zones of these types to prevent duplicates
            self._clear_existing_auto_zones(room, types_to_process)
            
            name = self.app._room_name(room)
            perim = float(self.app._room_attr(room, 'perim', 'perimeter', 0.0) or 0.0)
            area = float(self.app._room_attr(room, 'area', 'area', 0.0) or 0.0)
            
            # Wall ceramic
            if surface == 'wall' and height > 0 and perim > 0:
                wall_area = perim * height
                
                # Deduct openings if enabled
                if auto_deduct:
                    wall_area = self._deduct_openings(room, wall_area, height, start_height)
                
                zone = CeramicZone(
                    name=f"[Auto] {surface.title()} - {name}",
                    category=category,
                    perimeter=perim,
                    height=height,
                    surface_type='wall',
                    start_height=start_height,
                    room_name=name
                )
                zone.effective_area = wall_area
                self.app.project.ceramic_zones.append(zone)
                total_added += wall_area
                zones_count += 1
            
            # Floor ceramic
            if (surface == 'floor' or include_floor) and area > 0:
                zone = CeramicZone(
                    name=f"[Auto] Floor - {name}",
                    category=category,
                    perimeter=area,  # For floor, we store area in perimeter field
                    height=1.0,
                    surface_type='floor',
                    room_name=name
                )
                zone.effective_area = area
                self.app.project.ceramic_zones.append(zone)
                total_added += area
                zones_count += 1
            
            # Ceiling ceramic
            if surface == 'ceiling' and area > 0:
                zone = CeramicZone(
                    name=f"[Auto] Ceiling - {name}",
                    category=category,
                    perimeter=area,
                    height=1.0,
                    surface_type='ceiling',
                    room_name=name
                )
                zone.effective_area = area
                self.app.project.ceramic_zones.append(zone)
                total_added += area
                zones_count += 1
                
            # Recalculate room totals
            self._recalculate_room_totals(room)
        
        # Close dialog
        self.dialog.destroy()
        
        # Show result
        messagebox.showinfo(
            "تم الإضافة",
            f"تمت إضافة {zones_count} منطقة سيراميك\nالمساحة الإجمالية: {total_added:.1f} م²"
        )
        
        # Callback
        if self.on_complete:
            self.on_complete()
    
    def _clear_existing_auto_zones(self, room, surface_types: List[str]):
        """Remove existing [Auto] zones of specific surface types for a room."""
        room_name = self.app._room_name(room)
        kept_zones = []
        
        for z in (self.app.project.ceramic_zones or []):
            z_name = getattr(z, 'name', '') if not isinstance(z, dict) else z.get('name', '')
            z_room = getattr(z, 'room_name', '') if not isinstance(z, dict) else z.get('room_name', '')
            z_surface = getattr(z, 'surface_type', 'wall') if not isinstance(z, dict) else z.get('surface_type', 'wall')
            
            is_auto = str(z_name).startswith('[Auto]')
            is_for_room = (z_room == room_name) or (room_name in str(z_name))
            should_remove = is_auto and is_for_room and (z_surface in surface_types)
            
            if should_remove:
                continue 
            
            kept_zones.append(z)
            
        self.app.project.ceramic_zones = kept_zones

    def _recalculate_room_totals(self, room):
        """Recalculate ceramic totals for a room from all its zones."""
        room_name = self.app._room_name(room)
        total_area = 0.0
        breakdown = {}
        
        for z in self.app.project.ceramic_zones:
            z_name = getattr(z, 'name', '') if not isinstance(z, dict) else z.get('name', '')
            z_room = getattr(z, 'room_name', '') if not isinstance(z, dict) else z.get('room_name', '')
            
            # Check if this zone belongs to the room
            if (z_room == room_name) or (room_name in str(z_name)):
                area = float(getattr(z, 'effective_area', 0) or getattr(z, 'perimeter', 0) * getattr(z, 'height', 0))
                if isinstance(z, dict):
                    area = float(z.get('effective_area', 0) or z.get('perimeter', 0) * z.get('height', 0))
                
                stype = getattr(z, 'surface_type', 'wall') if not isinstance(z, dict) else z.get('surface_type', 'wall')
                
                total_area += area
                breakdown[stype] = breakdown.get(stype, 0.0) + area
            
        if isinstance(room, dict):
            room['ceramic_area'] = total_area
            room['ceramic_breakdown'] = breakdown
        else:
            room.ceramic_area = total_area
            room.ceramic_breakdown = breakdown
    
    def _deduct_openings(self, room, wall_area: float, height: float, start_height: float) -> float:
        """Deduct opening areas from wall ceramic."""
        from bilind.ui.tabs.helpers import OpeningAdapter
        
        openings = self.app.get_room_opening_summary(room)
        deductions = 0.0
        ceramic_end = start_height + height
        
        # Doors
        for door_id in openings.get('door_ids', []):
            for d in self.app.project.doors:
                if self.app._opening_name(d) == door_id:
                    adapter = OpeningAdapter(d)
                    d_height = adapter.height
                    d_width = adapter.width
                    d_placement = adapter.placement_height
                    d_top = d_placement + d_height
                    
                    # Calculate overlap
                    overlap_start = max(start_height, d_placement)
                    overlap_end = min(ceramic_end, d_top)
                    if overlap_end > overlap_start:
                        overlap_height = overlap_end - overlap_start
                        deductions += d_width * overlap_height
                    break
        
        # Windows
        for win_id in openings.get('window_ids', []):
            for w in self.app.project.windows:
                if self.app._opening_name(w) == win_id:
                    adapter = OpeningAdapter(w)
                    w_height = adapter.height
                    w_width = adapter.width
                    w_placement = adapter.placement_height
                    w_top = w_placement + w_height
                    
                    # Calculate overlap
                    overlap_start = max(start_height, w_placement)
                    overlap_end = min(ceramic_end, w_top)
                    if overlap_end > overlap_start:
                        overlap_height = overlap_end - overlap_start
                        deductions += w_width * overlap_height
                    break
        
        return max(0.0, wall_area - deductions)
    
    def _update_room_ceramic(self, room, surface_type: str, area: float):
        """Update room's ceramic breakdown."""
        if isinstance(room, dict):
            breakdown = room.get('ceramic_breakdown', {}) or {}
            breakdown[surface_type] = breakdown.get(surface_type, 0.0) + area
            room['ceramic_breakdown'] = breakdown
            room['ceramic_area'] = sum(breakdown.values())
        else:
            breakdown = getattr(room, 'ceramic_breakdown', {}) or {}
            breakdown[surface_type] = breakdown.get(surface_type, 0.0) + area
            room.ceramic_breakdown = breakdown
            room.ceramic_area = sum(breakdown.values())


def show_ceramic_calculator(parent_frame: tk.Widget, app: 'BilindEnhanced', 
                           on_complete: Optional[Callable] = None):
    """
    Convenience function to show the ceramic calculator dialog.
    
    Args:
        parent_frame: Parent tkinter widget
        app: Main application instance
        on_complete: Callback when ceramic is added
    """
    dialog = CeramicCalculatorDialog(parent_frame, app, on_complete)
    dialog.show()
