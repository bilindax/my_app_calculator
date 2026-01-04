"""
Room Manager Tab - Complete Room Control Center
===============================================
Dedicated interface for managing rooms with all details, openings, and finishes in one place.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional, List, Dict
from bilind.models.wall import Wall
from bilind.ui.tabs.helpers import RoomAdapter, OpeningAdapter, show_ceramic_calculator
from bilind.calculations.unified_calculator import UnifiedCalculator
# Legacy room_metrics removed - uses UnifiedCalculator instead
from bilind.ui.visuals.room_canvas import RoomCanvas

if TYPE_CHECKING:
    from bilind_main import BilindEnhanced


class RoomManagerTab:
    """
    Room Manager tab for comprehensive room management.
    
    Features:
    - Split-pane layout: room list (left) + details panel (right)
    - Room dimensions and properties (width, length, wall height, balcony)
    - Assigned openings (doors, windows) with placement height
    - Finishes (ceramic, plaster, paint) with Auto Calc
    - Add/Edit/Delete/Duplicate operations
    """
    
    def __init__(self, parent: ttk.Notebook, app: 'BilindEnhanced'):
        """Initialize the Room Manager tab."""
        self.app = app
        self.parent = parent
        self.selected_room = None  # Currently selected room
        self.room_canvas = None  # Visual overview canvas
        self.room_visuals_frame = None
        
        # Main frame
        self.frame = ttk.Frame(parent, style='Main.TFrame')
        parent.add(self.frame, text="🏠 مدير الغرف")
        
        # Create split-pane layout
        self._create_split_pane()
        
        # Initial load of rooms
        self.refresh_rooms_list()
        
    def _create_split_pane(self):
        """Create horizontal split between room list and details panel."""
        # Main container with 2 columns (30% list, 70% details)
        self.frame.columnconfigure(0, weight=1, minsize=300)
        self.frame.columnconfigure(1, weight=3, minsize=600)
        self.frame.rowconfigure(0, weight=1)
        
        # Left panel: Room list
        self._create_room_list_panel()
        
        # Right panel: Room details
        self._create_room_details_panel()
        
    def _create_room_list_panel(self):
        """Create left panel with room list and controls."""
        list_frame = ttk.LabelFrame(
            self.frame,
            text="  📋 قائمة الغرف  ",
            padding=(12, 8),
            style='Card.TLabelframe'
        )
        list_frame.grid(row=0, column=0, sticky='nsew', padx=(8, 4), pady=8)
        
        # Search bar
        search_frame = ttk.Frame(list_frame, style='Main.TFrame')
        search_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(
            search_frame,
            text="🔍 بحث:",
            foreground=self.app.colors['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, 6))
        
        self.room_search_var = tk.StringVar()
        self.room_search_var.trace_add('write', self._filter_rooms)
        search_entry = ttk.Entry(search_frame, textvariable=self.room_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Rooms treeview
        tree_frame = ttk.Frame(list_frame, style='Main.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('Name', 'Area', 'Openings')
        self.rooms_list_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=15,
            selectmode='browse'
        )
        
        self.rooms_list_tree.heading('Name', text='الاسم')
        self.rooms_list_tree.heading('Area', text='المساحة')
        self.rooms_list_tree.heading('Openings', text='الفتحات')
        
        self.rooms_list_tree.column('Name', width=150)
        self.rooms_list_tree.column('Area', width=80)
        self.rooms_list_tree.column('Openings', width=60)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.rooms_list_tree.yview)
        self.rooms_list_tree.configure(yscrollcommand=vsb.set)
        
        self.rooms_list_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        
        # Bind selection event
        self.rooms_list_tree.bind('<<TreeviewSelect>>', self._on_room_selected)
        
        # Action buttons
        btn_frame = ttk.Frame(list_frame, style='Main.TFrame')
        btn_frame.pack(fill=tk.X, pady=(8, 0))
        
        ttk.Button(
            btn_frame,
            text="➕ إضافة",
            command=self._add_room,
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=(0, 4))
        
        ttk.Button(
            btn_frame,
            text="📋 نسخ",
            command=self._duplicate_room,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=4)
        
        ttk.Button(
            btn_frame,
            text="🗑️ حذف",
            command=self._delete_room,
            style='Danger.TButton'
        ).pack(side=tk.RIGHT)
        
    def _create_room_details_panel(self):
        """Create right panel with room details and controls."""
        details_frame = ttk.Frame(self.frame, style='Main.TFrame')
        details_frame.grid(row=0, column=1, sticky='nsew', padx=(4, 8), pady=8)
        details_frame.rowconfigure(0, weight=1)
        details_frame.columnconfigure(0, weight=1)
        
        # Scrollable canvas for details
        canvas = tk.Canvas(details_frame, bg=self.app.colors['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.details_content = ttk.Frame(canvas, style='Main.TFrame')
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        canvas_window = canvas.create_window((0, 0), window=self.details_content, anchor='nw')
        
        def _configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.itemconfig(canvas_window, width=event.width)
        
        self.details_content.bind('<Configure>', _configure_canvas)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # Store references to detail sections
        self.detail_sections = []
        
        # Build details sections
        self.detail_sections.append(self._create_room_properties_section())
        self.detail_sections.append(self._create_walls_section())
        self.detail_sections.append(self._create_room_visuals_section())
        self.detail_sections.append(self._create_openings_section())
        self.detail_sections.append(self._create_finishes_section())
        self.detail_sections.append(self._create_actions_section())
        
        # Initially show "No room selected" message
        self._show_no_selection_message()
        
    def _create_room_properties_section(self):
        """Create room dimensions and properties section."""
        props_frame = ttk.LabelFrame(
            self.details_content,
            text="  📐 خصائص الغرفة  ",
            padding=(12, 8),
            style='Card.TLabelframe'
        )
        props_frame.pack(fill=tk.X, padx=8, pady=(8, 4))
        
        # Name
        row = 0
        ttk.Label(
            props_frame,
            text="الاسم:",
            foreground=self.app.colors['text_secondary']
        ).grid(row=row, column=0, sticky='w', pady=4)
        
        self.room_name_var = tk.StringVar()
        self.room_name_entry = ttk.Entry(props_frame, textvariable=self.room_name_var, width=25)
        self.room_name_entry.grid(row=row, column=1, sticky='w', pady=4, padx=(8, 0))
        
        # Layer
        row += 1
        ttk.Label(
            props_frame,
            text="الطبقة:",
            foreground=self.app.colors['text_secondary']
        ).grid(row=row, column=0, sticky='w', pady=4)
        
        self.room_layer_var = tk.StringVar()
        ttk.Entry(props_frame, textvariable=self.room_layer_var, width=25).grid(
            row=row, column=1, sticky='w', pady=4, padx=(8, 0)
        )
        
        # Dimensions (2 columns layout)
        row += 1
        dims_frame = ttk.Frame(props_frame, style='Main.TFrame')
        dims_frame.grid(row=row, column=0, columnspan=4, sticky='ew', pady=8)
        
        # Width
        ttk.Label(
            dims_frame,
            text="العرض (م):",
            foreground=self.app.colors['text_secondary']
        ).grid(row=0, column=0, sticky='w', padx=(0, 4))
        
        self.room_width_var = tk.StringVar()
        ttk.Entry(dims_frame, textvariable=self.room_width_var, width=12).grid(
            row=0, column=1, sticky='w', padx=4
        )
        
        # Length
        ttk.Label(
            dims_frame,
            text="الطول (م):",
            foreground=self.app.colors['text_secondary']
        ).grid(row=0, column=2, sticky='w', padx=(12, 4))
        
        self.room_length_var = tk.StringVar()
        ttk.Entry(dims_frame, textvariable=self.room_length_var, width=12).grid(
            row=0, column=3, sticky='w', padx=4
        )
        
        # Perimeter (read-only)
        ttk.Label(
            dims_frame,
            text="المحيط (م):",
            foreground=self.app.colors['text_secondary']
        ).grid(row=1, column=0, sticky='w', padx=(0, 4), pady=(8, 0))
        
        self.room_perim_var = tk.StringVar()
        perim_entry = ttk.Entry(dims_frame, textvariable=self.room_perim_var, width=12, state='readonly')
        perim_entry.grid(row=1, column=1, sticky='w', padx=4, pady=(8, 0))
        
        # Area (read-only)
        ttk.Label(
            dims_frame,
            text="المساحة (م²):",
            foreground=self.app.colors['text_secondary']
        ).grid(row=1, column=2, sticky='w', padx=(12, 4), pady=(8, 0))
        
        self.room_area_var = tk.StringVar()
        area_entry = ttk.Entry(dims_frame, textvariable=self.room_area_var, width=12, state='readonly')
        area_entry.grid(row=1, column=3, sticky='w', padx=4, pady=(8, 0))
        
        # Wall Height
        row += 1
        ttk.Label(
            props_frame,
            text="ارتفاع الجدار (م):",
            foreground=self.app.colors['text_secondary']
        ).grid(row=row, column=0, sticky='w', pady=4)
        
        self.room_wall_height_var = tk.StringVar()
        ttk.Entry(props_frame, textvariable=self.room_wall_height_var, width=12).grid(
            row=row, column=1, sticky='w', pady=4, padx=(8, 0)
        )
        
        # Balcony checkbox
        row += 1
        self.room_has_balcony_var = tk.BooleanVar()
        ttk.Checkbutton(
            props_frame,
            text="بلكون / شرفة",
            variable=self.room_has_balcony_var,
            command=self._toggle_balcony_controls
        ).grid(row=row, column=0, columnspan=2, sticky='w', pady=4)
        
        # Balcony segments (initially hidden)
        row += 1
        self.balcony_frame = ttk.Frame(props_frame, style='Main.TFrame')
        self.balcony_frame.grid(row=row, column=0, columnspan=4, sticky='ew', pady=4)
        self.balcony_frame.grid_remove()  # Hide initially
        
        ttk.Label(
            self.balcony_frame,
            text="جدران البلكون (4 جهات):",
            foreground=self.app.colors['accent'],
            font=('Segoe UI', 9, 'italic')
        ).pack(anchor=tk.W, pady=(0, 4))
        
        segs_grid = ttk.Frame(self.balcony_frame, style='Main.TFrame')
        segs_grid.pack(fill=tk.X)
        
        self.balcony_seg_vars = []
        side_names = ['جهة 1', 'جهة 2', 'جهة 3', 'جهة 4']
        for i in range(4):
            ttk.Label(
                segs_grid,
                text=f"{side_names[i]}:",
                foreground=self.app.colors['text_secondary']
            ).grid(row=i//2, column=(i%2)*2, sticky='w', padx=(0 if i%2==0 else 12, 4), pady=2)
            
            var = tk.StringVar()
            self.balcony_seg_vars.append(var)
            ttk.Entry(segs_grid, textvariable=var, width=10).grid(
                row=i//2, column=(i%2)*2 + 1, sticky='w', padx=4, pady=2
            )

        # Quick balcony ceramic helper
        self.balcony_ceramic_height_var = tk.StringVar(value="1.0")
        helper_frame = ttk.Frame(self.balcony_frame, style='Main.TFrame')
        helper_frame.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(helper_frame, text="ارتفاع السيراميك (م):", foreground=self.app.colors['text_secondary']).pack(side=tk.LEFT)
        ttk.Entry(helper_frame, textvariable=self.balcony_ceramic_height_var, width=6).pack(side=tk.LEFT, padx=(4, 8))
        ttk.Button(helper_frame, text="🧱 إضافة سيراميك", style='Secondary.TButton', command=self._add_balcony_ceramic_for_room).pack(side=tk.LEFT)
        
        # Save button
        row += 1
        ttk.Button(
            props_frame,
            text="💾 حفظ التغييرات",
            command=self._save_room_properties,
            style='Accent.TButton'
        ).grid(row=row, column=0, columnspan=2, pady=(8, 0))
        
        return props_frame
        
    def _create_walls_section(self):
        """Create section for managing specific walls with opening assignments."""
        walls_frame = ttk.LabelFrame(
            self.details_content,
            text="  🧱 الجدران  ",
            padding=(12, 8),
            style='Card.TLabelframe'
        )
        walls_frame.pack(fill=tk.X, padx=8, pady=4)
        
        # Info label
        ttk.Label(
            walls_frame,
            text="💡 حدد الجدران وربط الأبواب والنوافذ بكل جدار",
            foreground=self.app.colors['text_muted'],
            font=('Segoe UI', 8, 'italic')
        ).pack(anchor='w', pady=(0, 4))
        
        # Container to ensure treeview + scrollbar layout
        tree_container = ttk.Frame(walls_frame, style='Main.TFrame')
        tree_container.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Walls Treeview with more columns
        self.walls_tree = ttk.Treeview(
            tree_container,
            columns=('Name', 'Length', 'Height', 'Area', 'Surface', 'Ceramic', 'Openings'),
            show='headings',
            height=5,
            style='Walls.Treeview'
        )
        
        self.walls_tree.heading('Name', text='الاسم')
        self.walls_tree.heading('Length', text='الطول')
        self.walls_tree.heading('Height', text='الارتفاع')
        self.walls_tree.heading('Area', text='المساحة')
        self.walls_tree.heading('Surface', text='التشطيب')
        self.walls_tree.heading('Ceramic', text='سيراميك جزئي')
        self.walls_tree.heading('Openings', text='الفتحات')
        
        self.walls_tree.column('Name', width=100)
        self.walls_tree.column('Length', width=70)
        self.walls_tree.column('Height', width=70)
        self.walls_tree.column('Area', width=80)
        self.walls_tree.column('Surface', width=80)
        self.walls_tree.column('Ceramic', width=130)
        self.walls_tree.column('Openings', width=100)
        
        # Scrollbar
        walls_scroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.walls_tree.yview)
        self.walls_tree.configure(yscrollcommand=walls_scroll.set)

        self.walls_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        walls_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Wall totals summary
        self.walls_summary_label = ttk.Label(
            walls_frame,
            text="📊 إجمالي: 0 جدران | المساحة: 0.00 م²",
            foreground=self.app.colors['accent'],
            font=('Segoe UI', 9)
        )
        self.walls_summary_label.pack(anchor='w', pady=(4, 8))
        
        # Buttons Row 1
        btn_frame = ttk.Frame(walls_frame, style='Main.TFrame')
        btn_frame.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Button(
            btn_frame,
            text="➕ إضافة جدار",
            command=self._add_wall,
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=(0, 4))
        
        ttk.Button(
            btn_frame,
            text="✏️ تعديل",
            command=self._edit_wall,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=4)
        
        ttk.Button(
            btn_frame,
            text="🔗 ربط فتحة",
            command=self._link_opening_to_wall,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=4)
        
        ttk.Button(
            btn_frame,
            text="🗑️ حذف",
            command=self._delete_wall,
            style='Danger.TButton'
        ).pack(side=tk.RIGHT)
        
        # Buttons Row 2 - Quick actions
        btn_frame2 = ttk.Frame(walls_frame, style='Main.TFrame')
        btn_frame2.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Button(
            btn_frame2,
            text="⚡ إنشاء من المحيط",
            command=self._auto_generate_walls,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=(0, 4))
        
        ttk.Button(
            btn_frame2,
            text="🔄 حساب الخصومات",
            command=self._recalculate_wall_deductions,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            btn_frame2,
            text="📏 تحويل وحدات الغرفة",
            command=self._convert_room_units,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT)
        
        return walls_frame

    def _convert_room_units(self):
        """Apply a unit conversion factor to ONLY the selected room."""
        if not self.selected_room:
            messagebox.showinfo("لا توجد غرفة", "اختر غرفة أولاً")
            return

        from tkinter import simpledialog
        from bilind.ui.tabs.helpers.room_adapter import RoomAdapter
        from bilind.ui.tabs.helpers.opening_adapter import OpeningAdapter

        adapter = RoomAdapter(self.selected_room)
        room_name = adapter.name
        if not room_name:
            messagebox.showwarning("خطأ", "اسم الغرفة غير معروف")
            return

        factor = simpledialog.askfloat(
            "تحويل وحدات الغرفة",
            "أدخل معامل التحويل للأطوال (مثال: سم ➜ متر = 0.01 ، مم ➜ متر = 0.001):",
            initialvalue=0.01,
            minvalue=0.000001,
        )
        if factor is None:
            return
        factor = float(factor)
        factor_area = factor * factor

        include_openings = messagebox.askyesno(
            "تحويل وحدات الغرفة",
            "هل تريد أيضاً تحويل أبعاد الفتحات (الأبواب/النوافذ) الخاصة بهذه الغرفة فقط؟\n\n"
            "(سيتم تحويل الفتحة فقط إذا كانت مرتبطة بهذه الغرفة وحدها.)"
        )

        if not messagebox.askyesno(
            "تأكيد",
            f"سيتم تحويل أبعاد الغرفة '{room_name}' بمعامل {factor}.\n\nهل تريد المتابعة؟"
        ):
            return

        def _scale_len(value):
            try:
                return float(value or 0.0) * factor
            except Exception:
                return value

        def _scale_area_value(value):
            try:
                return float(value or 0.0) * factor_area
            except Exception:
                return value

        # --- Scale room core fields ---
        if isinstance(self.selected_room, dict):
            for k in ('w', 'l', 'width', 'length', 'perim', 'perimeter', 'wall_height'):
                if k in self.selected_room and self.selected_room[k] is not None:
                    self.selected_room[k] = _scale_len(self.selected_room[k])
            for k in ('area',):
                if k in self.selected_room and self.selected_room[k] is not None:
                    self.selected_room[k] = _scale_area_value(self.selected_room[k])

            # Clear cached finish areas (they will be recomputed)
            for k in ('ceiling_finish_area', 'wall_finish_area', 'ceramic_area'):
                if k in self.selected_room:
                    self.selected_room[k] = None
        else:
            # dataclass Room
            if getattr(self.selected_room, 'width', None) is not None:
                self.selected_room.width = _scale_len(self.selected_room.width)
            if getattr(self.selected_room, 'length', None) is not None:
                self.selected_room.length = _scale_len(self.selected_room.length)
            if getattr(self.selected_room, 'perimeter', None) is not None:
                self.selected_room.perimeter = _scale_len(self.selected_room.perimeter)
            if getattr(self.selected_room, 'area', None) is not None:
                self.selected_room.area = _scale_area_value(self.selected_room.area)
            if getattr(self.selected_room, 'wall_height', None) is not None:
                self.selected_room.wall_height = _scale_len(self.selected_room.wall_height)

            self.selected_room.ceiling_finish_area = None
            self.selected_room.wall_finish_area = None
            self.selected_room.ceramic_area = None

        # --- Scale walls ---
        walls = adapter.walls
        for w in (walls or []):
            if isinstance(w, dict):
                if 'length' in w and w['length'] is not None:
                    w['length'] = _scale_len(w['length'])
                if 'height' in w and w['height'] is not None:
                    w['height'] = _scale_len(w['height'])
                if 'ceramic_height' in w and w['ceramic_height'] is not None:
                    w['ceramic_height'] = _scale_len(w['ceramic_height'])
                try:
                    ln = float(w.get('length') or 0.0)
                    ht = float(w.get('height') or 0.0)
                    w['gross_area'] = ln * ht
                    ch = float(w.get('ceramic_height') or 0.0)
                    if ch > 0:
                        w['ceramic_area'] = ln * ch
                except Exception:
                    pass
            else:
                if getattr(w, 'length', None) is not None:
                    w.length = _scale_len(w.length)
                if getattr(w, 'height', None) is not None:
                    w.height = _scale_len(w.height)
                if getattr(w, 'ceramic_height', None) is not None:
                    w.ceramic_height = _scale_len(w.ceramic_height)
                try:
                    w.gross_area = float(getattr(w, 'length', 0.0) or 0.0) * float(getattr(w, 'height', 0.0) or 0.0)
                    if float(getattr(w, 'ceramic_height', 0.0) or 0.0) > 0:
                        w.ceramic_area = float(getattr(w, 'length', 0.0) or 0.0) * float(getattr(w, 'ceramic_height', 0.0) or 0.0)
                except Exception:
                    pass

        # --- Optionally scale openings that are exclusive to this room ---
        if include_openings:
            for opening in list(self.app.project.doors or []) + list(self.app.project.windows or []):
                oad = OpeningAdapter(opening)
                assigned = list(oad.assigned_rooms or [])
                is_exclusive = (len(assigned) == 1 and assigned[0] == room_name)
                if not is_exclusive:
                    # If per-room quantities exist and only this room is present
                    rq = oad.room_quantities or {}
                    if isinstance(rq, dict) and rq and set(rq.keys()) == {room_name}:
                        is_exclusive = True
                if not is_exclusive:
                    continue

                if oad.is_dict:
                    if 'w' in opening and opening['w'] is not None:
                        opening['w'] = _scale_len(opening['w'])
                    if 'h' in opening and opening['h'] is not None:
                        opening['h'] = _scale_len(opening['h'])
                    if 'width' in opening and opening['width'] is not None:
                        opening['width'] = _scale_len(opening['width'])
                    if 'height' in opening and opening['height'] is not None:
                        opening['height'] = _scale_len(opening['height'])
                    if 'placement_height' in opening and opening['placement_height'] is not None:
                        opening['placement_height'] = _scale_len(opening['placement_height'])
                else:
                    try:
                        if getattr(opening, 'width', None) is not None:
                            opening.width = _scale_len(opening.width)
                        if getattr(opening, 'height', None) is not None:
                            opening.height = _scale_len(opening.height)
                        if getattr(opening, 'placement_height', None) is not None:
                            opening.placement_height = _scale_len(opening.placement_height)
                    except Exception:
                        pass

        # Recompute deductions and finishes for this room
        all_openings = list(self.app.project.doors) + list(self.app.project.windows)
        for w in (adapter.walls or []):
            if not isinstance(w, dict) and hasattr(w, 'recalculate_deductions'):
                try:
                    w.recalculate_deductions(all_openings)
                except Exception:
                    pass

        # Sync project references for exporters and refresh UI
        self.app._sync_project_references()
        self._load_room_details(self.selected_room)
        if hasattr(self.selected_room, 'update_finish_areas'):
            try:
                self.selected_room.update_finish_areas(all_openings)
            except Exception:
                pass
        self._recalculate_room_ceramic_with_openings(self.selected_room)
        metrics = self._compute_room_finish_metrics(self.selected_room)
        self._update_room_metrics_ui(metrics)

        if hasattr(self.app, 'refresh_after_wall_change'):
            self.app.refresh_after_wall_change()

        self.app.update_status(f"📏 تم تحويل وحدات الغرفة '{room_name}' بمعامل {factor}", icon="✅")

    def _create_room_visuals_section(self):
        """Create mini-visual section that sketches wall finishes."""
        visuals_frame = ttk.LabelFrame(
            self.details_content,
            text="  🖼️ مخطط الجدران  ",
            padding=(12, 8),
            style='Card.TLabelframe'
        )
        visuals_frame.pack(fill=tk.BOTH, padx=8, pady=4)

        ttk.Label(
            visuals_frame,
            text="رسم توضيحي للجدران مع ألوان التشطيب والفتحات",
            foreground=self.app.colors['text_muted'],
            font=('Segoe UI', 8, 'italic')
        ).pack(anchor='w')

        self.room_canvas = RoomCanvas(visuals_frame, self.app, height=320)
        self.room_canvas.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.room_visuals_frame = visuals_frame
        self.room_canvas.render_room(None)

        return visuals_frame

    def _add_wall(self):
        """Add a new wall to the selected room with full details."""
        if not self.selected_room:
            messagebox.showinfo("لا توجد غرفة", "اختر غرفة أولاً")
            return
        
        from bilind.models.wall import WALL_SURFACE_TYPES
            
        # Styled dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("➕ إضافة جدار جديد")
        dialog.configure(bg=self.app.colors['bg_secondary'])
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        width, height = 520, 550
        x = self.frame.winfo_rootx() + (self.frame.winfo_width() - width) // 2
        y = self.frame.winfo_rooty() + (self.frame.winfo_height() - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        container = ttk.Frame(dialog, padding=20, style='Main.TFrame')
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(
            container,
            text="🧱 بيانات الجدار الجديد",
            font=('Segoe UI Semibold', 12),
            foreground=self.app.colors['accent']
        ).pack(anchor='w', pady=(0, 12))
        
        # Form
        grid = ttk.Frame(container, style='Main.TFrame')
        grid.pack(fill=tk.X, pady=(0, 12))
        
        # Wall count for auto-naming
        wall_count = len(getattr(self.selected_room, 'walls', []) or []) + 1
        
        # Name
        ttk.Label(grid, text="الاسم:", foreground=self.app.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=6)
        name_var = tk.StringVar(value=f"جدار {wall_count}")
        ttk.Entry(grid, textvariable=name_var, width=30).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=6)
        
        # Direction
        ttk.Label(grid, text="الاتجاه:", foreground=self.app.colors['text_secondary']).grid(row=0, column=2, sticky='w', padx=(20, 0), pady=6)
        direction_var = tk.StringVar()
        direction_combo = ttk.Combobox(grid, textvariable=direction_var, values=['شمال', 'جنوب', 'شرق', 'غرب', 'داخلي', 'خارجي', ''], state='readonly', width=12)
        direction_combo.grid(row=0, column=3, sticky='w', padx=(10, 0), pady=6)
        
        # Length
        ttk.Label(grid, text="الطول (م):", foreground=self.app.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=6)
        length_var = tk.StringVar()
        ttk.Entry(grid, textvariable=length_var, width=12).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=6)
        
        # Height
        default_height = self.selected_room.wall_height if hasattr(self.selected_room, 'wall_height') and self.selected_room.wall_height else 3.0
        ttk.Label(grid, text="الارتفاع (م):", foreground=self.app.colors['text_secondary']).grid(row=1, column=2, sticky='w', padx=(20, 0), pady=6)
        height_var = tk.StringVar(value=str(default_height))
        ttk.Entry(grid, textvariable=height_var, width=12).grid(row=1, column=3, sticky='w', padx=(10, 0), pady=6)
        
        # Surface Type
        ttk.Label(grid, text="نوع التشطيب:", foreground=self.app.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=6)
        surface_var = tk.StringVar(value='دهان')
        surface_combo = ttk.Combobox(grid, textvariable=surface_var, values=WALL_SURFACE_TYPES, state='readonly', width=18)
        surface_combo.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=6)
        
        # Notes
        ttk.Label(grid, text="ملاحظات:", foreground=self.app.colors['text_secondary']).grid(row=2, column=2, sticky='w', padx=(20, 0), pady=6)
        notes_var = tk.StringVar()
        ttk.Entry(grid, textvariable=notes_var, width=18).grid(row=2, column=3, sticky='w', padx=(10, 0), pady=6)

        # Partial ceramic controls
        ceramic_height_var = tk.StringVar()
        ceramic_surface_var = tk.StringVar(value='سيراميك')
        ceramic_surface_options = [opt for opt in WALL_SURFACE_TYPES if opt not in ('شباك/فتحة', 'بدون تشطيب')]
        if not ceramic_surface_options:
            ceramic_surface_options = ['سيراميك']

        ttk.Label(grid, text="ارتفاع السيراميك (م):", foreground=self.app.colors['text_secondary']).grid(row=3, column=0, sticky='w', pady=6)
        ttk.Entry(grid, textvariable=ceramic_height_var, width=12).grid(row=3, column=1, sticky='w', padx=(10, 0), pady=6)
        ttk.Label(grid, text="نوع تغطية السيراميك:", foreground=self.app.colors['text_secondary']).grid(row=3, column=2, sticky='w', padx=(20, 0), pady=6)
        ttk.Combobox(grid, textvariable=ceramic_surface_var, values=ceramic_surface_options, state='readonly', width=18).grid(row=3, column=3, sticky='w', padx=(10, 0), pady=6)
        
        # Live Area calculation
        area_label = ttk.Label(grid, text="📐 المساحة: -- م²", foreground=self.app.colors['accent'], font=('Segoe UI Semibold', 10))
        area_label.grid(row=4, column=0, columnspan=4, sticky='w', pady=(12, 0))
        
        def update_area(*args):
            try:
                l = float(length_var.get() or 0)
                h = float(height_var.get() or 0)
                area = l * h
                area_label.config(text=f"📐 المساحة: {area:.2f} م²")
            except:
                area_label.config(text="📐 المساحة: -- م²")
        
        length_var.trace_add('write', update_area)
        height_var.trace_add('write', update_area)
        
        # ═══════════════════════════════════════════════════════════════
        # Opening Assignment Section
        # ═══════════════════════════════════════════════════════════════
        ttk.Separator(container, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)
        
        ttk.Label(
            container,
            text="🚪🪟 ربط الفتحات بهذا الجدار (اختياري)",
            font=('Segoe UI Semibold', 10),
            foreground=self.app.colors['accent']
        ).pack(anchor='w', pady=(0, 8))
        
        # Get room's openings
        room_openings = self.app.get_room_opening_summary(self.selected_room)
        available_doors = room_openings.get('door_ids', [])
        available_windows = room_openings.get('window_ids', [])
        
        openings_frame = ttk.Frame(container, style='Main.TFrame')
        openings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Doors
        doors_label_frame = ttk.LabelFrame(openings_frame, text="🚪 الأبواب", padding=(8, 6))
        doors_label_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        
        door_vars = {}
        if available_doors:
            for door_id in available_doors:
                var = tk.BooleanVar(value=False)
                door_vars[door_id] = var
                # Get door details
                door_info = ""
                for d in self.app.project.doors:
                    if self.app._opening_name(d) == door_id:
                        w = self.app._opening_attr(d, 'w', 'width', 0)
                        h = self.app._opening_attr(d, 'h', 'height', 0)
                        door_info = f" ({w:.1f}×{h:.1f}م)"
                        break
                ttk.Checkbutton(doors_label_frame, text=f"{door_id}{door_info}", variable=var).pack(anchor='w')
        else:
            ttk.Label(doors_label_frame, text="لا توجد أبواب مرتبطة بالغرفة", foreground=self.app.colors['text_muted']).pack(anchor='w')
        
        # Windows
        windows_label_frame = ttk.LabelFrame(openings_frame, text="🪟 النوافذ", padding=(8, 6))
        windows_label_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        
        window_vars = {}
        if available_windows:
            for win_id in available_windows:
                var = tk.BooleanVar(value=False)
                window_vars[win_id] = var
                # Get window details
                win_info = ""
                for w in self.app.project.windows:
                    if self.app._opening_name(w) == win_id:
                        width = self.app._opening_attr(w, 'w', 'width', 0)
                        height = self.app._opening_attr(w, 'h', 'height', 0)
                        win_info = f" ({width:.1f}×{height:.1f}م)"
                        break
                ttk.Checkbutton(windows_label_frame, text=f"{win_id}{win_info}", variable=var).pack(anchor='w')
        else:
            ttk.Label(windows_label_frame, text="لا توجد نوافذ مرتبطة بالغرفة", foreground=self.app.colors['text_muted']).pack(anchor='w')
        
        # ═══════════════════════════════════════════════════════════════
        # Action Buttons
        # ═══════════════════════════════════════════════════════════════
        btn_frame = ttk.Frame(container, style='Main.TFrame')
        btn_frame.pack(fill=tk.X, pady=(16, 0))
        
        def save():
            try:
                length = float(length_var.get())
                height = float(height_var.get())
                name = name_var.get().strip()
                ceramic_height = 0.0
                ceramic_height_raw = (ceramic_height_var.get() or "").strip()
                if ceramic_height_raw:
                    ceramic_height = float(ceramic_height_raw)
                    if ceramic_height < 0:
                        messagebox.showerror("خطأ", "ارتفاع السيراميك يجب أن يكون رقماً موجباً.")
                        return
                    if ceramic_height > height:
                        ceramic_height = height
                
                if length <= 0 or height <= 0:
                    messagebox.showerror("خطأ", "الطول والارتفاع يجب أن يكونا أكبر من صفر.")
                    return
                
                if not name:
                    messagebox.showerror("خطأ", "يرجى إدخال اسم الجدار.")
                    return
                
                # Collect selected openings
                selected_openings = []
                for door_id, var in door_vars.items():
                    if var.get():
                        selected_openings.append(door_id)
                for win_id, var in window_vars.items():
                    if var.get():
                        selected_openings.append(win_id)
                
                # Create new wall
                new_wall = Wall(
                    name=name,
                    layer=self.app._room_attr(self.selected_room, 'layer', 'layer', ''),
                    length=length,
                    height=height,
                    assigned_openings=selected_openings,
                    surface_type=surface_var.get(),
                    direction=direction_var.get(),
                    notes=notes_var.get(),
                    ceramic_height=ceramic_height,
                    ceramic_surface=ceramic_surface_var.get() or 'سيراميك'
                )
                
                # Calculate deductions from assigned openings
                all_openings = list(self.app.project.doors) + list(self.app.project.windows)
                new_wall.recalculate_deductions(all_openings)
                
                # Add wall to room (handle both dict and Room object)
                if isinstance(self.selected_room, dict):
                    if 'walls' not in self.selected_room:
                        self.selected_room['walls'] = []
                    self.selected_room['walls'].append(new_wall.to_dict())
                else:
                    if not hasattr(self.selected_room, 'walls') or self.selected_room.walls is None:
                        self.selected_room.walls = []
                    self.selected_room.walls.append(new_wall)
                
                # CRITICAL: Sync project references for Excel export
                self.app._sync_project_references()
                
                # Recalculate room finishes
                if hasattr(self.selected_room, 'update_finish_areas'):
                    self.selected_room.update_finish_areas(self.app.project.openings)
                
                self._load_room_details(self.selected_room)
                
                # Trigger refresh on dependent tabs
                if hasattr(self.app, 'refresh_after_wall_change'):
                    self.app.refresh_after_wall_change()
                
                self.app.update_status(f"✅ تم إضافة الجدار: {name}", icon="🧱")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("خطأ", "يرجى إدخال أرقام صحيحة للأبعاد وارتفاع السيراميك.")
        
        ttk.Button(btn_frame, text="💾 حفظ", command=save, style='Accent.TButton', width=14).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="❌ إلغاء", command=dialog.destroy, style='Secondary.TButton', width=14).pack(side=tk.RIGHT, padx=(0, 8))

    def _edit_wall(self):
        """Edit selected wall with full details."""
        if not self.selected_room:
            return
            
        selection = self.walls_tree.selection()
        if not selection:
            messagebox.showinfo("لا يوجد اختيار", "اختر جدار للتعديل")
            return
        
        from bilind.models.wall import WALL_SURFACE_TYPES
            
        index = self.walls_tree.index(selection[0])
        
        # Get walls list (handle both dict and Room object)
        if isinstance(self.selected_room, dict):
            walls = self.selected_room.get('walls', []) or []
        else:
            walls = getattr(self.selected_room, 'walls', []) or []
        
        if index >= len(walls):
            return
        
        wall_data = walls[index]
        # Convert dict to Wall object if needed for editing
        if isinstance(wall_data, dict):
            wall = Wall.from_dict(wall_data)
        else:
            wall = wall_data
        
        # Styled dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"✏️ تعديل الجدار: {wall.name}")
        dialog.configure(bg=self.app.colors['bg_secondary'])
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        width, height = 520, 550
        x = self.frame.winfo_rootx() + (self.frame.winfo_width() - width) // 2
        y = self.frame.winfo_rooty() + (self.frame.winfo_height() - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        container = ttk.Frame(dialog, padding=20, style='Main.TFrame')
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(
            container,
            text=f"🧱 تعديل: {wall.name}",
            font=('Segoe UI Semibold', 12),
            foreground=self.app.colors['accent']
        ).pack(anchor='w', pady=(0, 12))
        
        # Form
        grid = ttk.Frame(container, style='Main.TFrame')
        grid.pack(fill=tk.X, pady=(0, 12))
        
        # Name
        ttk.Label(grid, text="الاسم:", foreground=self.app.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=6)
        name_var = tk.StringVar(value=wall.name)
        ttk.Entry(grid, textvariable=name_var, width=30).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=6)
        
        # Direction
        ttk.Label(grid, text="الاتجاه:", foreground=self.app.colors['text_secondary']).grid(row=0, column=2, sticky='w', padx=(20, 0), pady=6)
        direction_var = tk.StringVar(value=getattr(wall, 'direction', ''))
        direction_combo = ttk.Combobox(grid, textvariable=direction_var, values=['شمال', 'جنوب', 'شرق', 'غرب', 'داخلي', 'خارجي', ''], state='readonly', width=12)
        direction_combo.grid(row=0, column=3, sticky='w', padx=(10, 0), pady=6)
        
        # Length
        ttk.Label(grid, text="الطول (م):", foreground=self.app.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=6)
        length_var = tk.StringVar(value=str(wall.length))
        ttk.Entry(grid, textvariable=length_var, width=12).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=6)
        
        # Height
        ttk.Label(grid, text="الارتفاع (م):", foreground=self.app.colors['text_secondary']).grid(row=1, column=2, sticky='w', padx=(20, 0), pady=6)
        height_var = tk.StringVar(value=str(wall.height))
        ttk.Entry(grid, textvariable=height_var, width=12).grid(row=1, column=3, sticky='w', padx=(10, 0), pady=6)
        
        # Surface Type
        ttk.Label(grid, text="نوع التشطيب:", foreground=self.app.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=6)
        surface_var = tk.StringVar(value=getattr(wall, 'surface_type', 'دهان'))
        surface_combo = ttk.Combobox(grid, textvariable=surface_var, values=WALL_SURFACE_TYPES, state='readonly', width=18)
        surface_combo.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=6)
        
        # Notes
        ttk.Label(grid, text="ملاحظات:", foreground=self.app.colors['text_secondary']).grid(row=2, column=2, sticky='w', padx=(20, 0), pady=6)
        notes_var = tk.StringVar(value=getattr(wall, 'notes', ''))
        ttk.Entry(grid, textvariable=notes_var, width=18).grid(row=2, column=3, sticky='w', padx=(10, 0), pady=6)

        # Partial ceramic controls
        ceramic_surface_options = [opt for opt in WALL_SURFACE_TYPES if opt not in ('شباك/فتحة', 'بدون تشطيب')]
        if not ceramic_surface_options:
            ceramic_surface_options = ['سيراميك']
        existing_height = getattr(wall, 'ceramic_height', 0.0) or 0.0
        ceramic_height_var = tk.StringVar(value=str(existing_height) if existing_height > 0 else "")
        ceramic_surface_var = tk.StringVar(value=getattr(wall, 'ceramic_surface', 'سيراميك'))

        ttk.Label(grid, text="ارتفاع السيراميك (م):", foreground=self.app.colors['text_secondary']).grid(row=3, column=0, sticky='w', pady=6)
        ttk.Entry(grid, textvariable=ceramic_height_var, width=12).grid(row=3, column=1, sticky='w', padx=(10, 0), pady=6)
        ttk.Label(grid, text="نوع تغطية السيراميك:", foreground=self.app.colors['text_secondary']).grid(row=3, column=2, sticky='w', padx=(20, 0), pady=6)
        ttk.Combobox(grid, textvariable=ceramic_surface_var, values=ceramic_surface_options, state='readonly', width=18).grid(row=3, column=3, sticky='w', padx=(10, 0), pady=6)
        
        # Live Area calculation
        area_label = ttk.Label(grid, text=f"📐 المساحة: {wall.gross_area:.2f} م²", foreground=self.app.colors['accent'], font=('Segoe UI Semibold', 10))
        area_label.grid(row=4, column=0, columnspan=4, sticky='w', pady=(12, 0))
        
        def update_area(*args):
            try:
                l = float(length_var.get() or 0)
                h = float(height_var.get() or 0)
                area = l * h
                area_label.config(text=f"📐 المساحة: {area:.2f} م²")
            except:
                area_label.config(text="📐 المساحة: -- م²")
        
        length_var.trace_add('write', update_area)
        height_var.trace_add('write', update_area)
        
        # ═══════════════════════════════════════════════════════════════
        # Opening Assignment Section
        # ═══════════════════════════════════════════════════════════════
        ttk.Separator(container, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)
        
        ttk.Label(
            container,
            text="🚪🪟 الفتحات المرتبطة بهذا الجدار",
            font=('Segoe UI Semibold', 10),
            foreground=self.app.colors['accent']
        ).pack(anchor='w', pady=(0, 8))
        
        # Get room's openings and current wall's openings
        room_openings = self.app.get_room_opening_summary(self.selected_room)
        available_doors = room_openings.get('door_ids', [])
        available_windows = room_openings.get('window_ids', [])
        current_openings = getattr(wall, 'assigned_openings', []) or []
        
        openings_frame = ttk.Frame(container, style='Main.TFrame')
        openings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Doors
        doors_label_frame = ttk.LabelFrame(openings_frame, text="🚪 الأبواب", padding=(8, 6))
        doors_label_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        
        door_vars = {}
        if available_doors:
            for door_id in available_doors:
                var = tk.BooleanVar(value=door_id in current_openings)
                door_vars[door_id] = var
                # Get door details
                door_info = ""
                for d in self.app.project.doors:
                    if self.app._opening_name(d) == door_id:
                        w = self.app._opening_attr(d, 'w', 'width', 0)
                        h = self.app._opening_attr(d, 'h', 'height', 0)
                        door_info = f" ({w:.1f}×{h:.1f}م)"
                        break
                ttk.Checkbutton(doors_label_frame, text=f"{door_id}{door_info}", variable=var).pack(anchor='w')
        else:
            ttk.Label(doors_label_frame, text="لا توجد أبواب مرتبطة بالغرفة", foreground=self.app.colors['text_muted']).pack(anchor='w')
        
        # Windows
        windows_label_frame = ttk.LabelFrame(openings_frame, text="🪟 النوافذ", padding=(8, 6))
        windows_label_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        
        window_vars = {}
        if available_windows:
            for win_id in available_windows:
                var = tk.BooleanVar(value=win_id in current_openings)
                window_vars[win_id] = var
                # Get window details
                win_info = ""
                for w in self.app.project.windows:
                    if self.app._opening_name(w) == win_id:
                        width = self.app._opening_attr(w, 'w', 'width', 0)
                        height = self.app._opening_attr(w, 'h', 'height', 0)
                        win_info = f" ({width:.1f}×{height:.1f}م)"
                        break
                ttk.Checkbutton(windows_label_frame, text=f"{win_id}{win_info}", variable=var).pack(anchor='w')
        else:
            ttk.Label(windows_label_frame, text="لا توجد نوافذ مرتبطة بالغرفة", foreground=self.app.colors['text_muted']).pack(anchor='w')
        
        # ═══════════════════════════════════════════════════════════════
        # Action Buttons
        # ═══════════════════════════════════════════════════════════════
        btn_frame = ttk.Frame(container, style='Main.TFrame')
        btn_frame.pack(fill=tk.X, pady=(16, 0))
        
        def save():
            try:
                length = float(length_var.get())
                height = float(height_var.get())
                name = name_var.get().strip()
                ceramic_height = 0.0
                ceramic_height_raw = (ceramic_height_var.get() or "").strip()
                if ceramic_height_raw:
                    ceramic_height = float(ceramic_height_raw)
                    if ceramic_height < 0:
                        messagebox.showerror("خطأ", "ارتفاع السيراميك يجب أن يكون رقماً موجباً.")
                        return
                    if ceramic_height > height:
                        ceramic_height = height
                
                if length <= 0 or height <= 0:
                    messagebox.showerror("خطأ", "الطول والارتفاع يجب أن يكونا أكبر من صفر.")
                    return
                
                if not name:
                    messagebox.showerror("خطأ", "يرجى إدخال اسم الجدار.")
                    return
                
                # Collect selected openings
                selected_openings = []
                for door_id, var in door_vars.items():
                    if var.get():
                        selected_openings.append(door_id)
                for win_id, var in window_vars.items():
                    if var.get():
                        selected_openings.append(win_id)
                
                # Update wall
                wall.name = name
                wall.length = length
                wall.height = height
                wall.gross_area = length * height
                wall.assigned_openings = selected_openings
                wall.surface_type = surface_var.get()
                wall.direction = direction_var.get()
                wall.notes = notes_var.get()
                wall.ceramic_height = ceramic_height
                wall.ceramic_surface = ceramic_surface_var.get() or 'سيراميك'
                
                # Recalculate deductions from assigned openings
                all_openings = list(self.app.project.doors) + list(self.app.project.windows)
                wall.recalculate_deductions(all_openings)
                
                # Update wall in room (handle both dict and Room object)
                if isinstance(self.selected_room, dict):
                    walls_list = self.selected_room.get('walls', []) or []
                    if index < len(walls_list):
                        walls_list[index] = wall.to_dict()
                else:
                    walls_list = getattr(self.selected_room, 'walls', []) or []
                    if index < len(walls_list):
                        walls_list[index] = wall
                
                # Check if all walls have same height -> update room wall_height
                if isinstance(self.selected_room, dict):
                    walls_list = self.selected_room.get('walls', []) or []
                    if walls_list:
                        heights = []
                        for w in walls_list:
                            h = w.get('height') if isinstance(w, dict) else getattr(w, 'height', None)
                            if h:
                                heights.append(float(h))
                        if heights and len(set(heights)) == 1:
                            self.selected_room['wall_height'] = heights[0]
                else:
                    walls_list = getattr(self.selected_room, 'walls', []) or []
                    if walls_list:
                        heights = []
                        for w in walls_list:
                            h = w.get('height') if isinstance(w, dict) else getattr(w, 'height', None)
                            if h:
                                heights.append(float(h))
                        if heights and len(set(heights)) == 1:
                            self.selected_room.wall_height = heights[0]
                
                # CRITICAL: Sync project references for Excel export
                self.app._sync_project_references()
                
                # Refresh room details and finishes after wall edit (affects plaster/paint)
                self._load_room_details(self.selected_room)
                if hasattr(self.selected_room, 'update_finish_areas'):
                    all_openings = list(self.app.project.doors) + list(self.app.project.windows)
                    self.selected_room.update_finish_areas(all_openings)
                self._recalculate_room_ceramic_with_openings(self.selected_room)
                metrics = self._compute_room_finish_metrics(self.selected_room)
                self._update_room_metrics_ui(metrics)
                
                # Trigger refresh on dependent tabs
                if hasattr(self.app, 'refresh_after_wall_change'):
                    self.app.refresh_after_wall_change()
                
                self.app.update_status(f"✅ تم تحديث الجدار: {name}", icon="🧱")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("خطأ", "يرجى إدخال أرقام صحيحة للأبعاد وارتفاع السيراميك.")
        
        ttk.Button(btn_frame, text="💾 حفظ", command=save, style='Accent.TButton', width=14).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="❌ إلغاء", command=dialog.destroy, style='Secondary.TButton', width=14).pack(side=tk.RIGHT, padx=(0, 8))

    def _delete_wall(self):
        """Delete selected wall."""
        if not self.selected_room:
            return
            
        selection = self.walls_tree.selection()
        if not selection:
            return
            
        if messagebox.askyesno("تأكيد", "هل تريد حذف هذا الجدار؟"):
            index = self.walls_tree.index(selection[0])
            # Handle both dict and Room object
            if isinstance(self.selected_room, dict):
                walls = self.selected_room.get('walls', []) or []
            else:
                walls = getattr(self.selected_room, 'walls', []) or []
            
            if index < len(walls):
                # Get wall name before deleting
                wall_data = walls[index]
                if isinstance(wall_data, dict):
                    wall_name = wall_data.get('name', '')
                else:
                    wall_name = getattr(wall_data, 'name', '')
                
                # Delete the wall
                walls.pop(index)
                
                # CRITICAL: Remove ceramic zones associated with this wall
                room_name = self.app._room_name(self.selected_room)
                if wall_name and room_name:
                    self._remove_wall_ceramic_zones(room_name, wall_name)
            
            # CRITICAL: Sync project references so Excel export sees current data
            self.app._sync_project_references()
            
            # Refresh UI and recalculate finishes
            self._load_room_details(self.selected_room)
            
            # Trigger refresh on dependent tabs (ceramic zones may be affected)
            if hasattr(self.app, 'refresh_after_wall_change'):
                self.app.refresh_after_wall_change()
            
            self.app.update_status("🗑️ تم حذف الجدار", icon="✅")

    def _remove_wall_ceramic_zones(self, room_name: str, wall_name: str):
        """Remove ceramic zones associated with a specific wall in a room."""
        if not room_name or not wall_name:
            return
        
        before_count = len(self.app.project.ceramic_zones)
        
        # Filter out ceramic zones that match this room and wall
        self.app.project.ceramic_zones = [
            z for z in self.app.project.ceramic_zones
            if not self._is_zone_for_wall(z, room_name, wall_name)
        ]
        
        removed = before_count - len(self.app.project.ceramic_zones)
        
        if removed > 0:
            # Sync to legacy attributes
            self.app.ceramic_zones = self.app.project.ceramic_zones
            
            # Refresh ceramic tab if available
            if hasattr(self.app, 'ceramic_tab'):
                self.app.ceramic_tab.refresh_data()
    
    def _is_zone_for_wall(self, zone, room_name: str, wall_name: str) -> bool:
        """Check if a ceramic zone belongs to a specific wall in a room."""
        # Get zone attributes (handle both dict and object)
        if isinstance(zone, dict):
            z_surface = zone.get('surface_type', 'wall')
            z_room = zone.get('room_name', '')
            z_wall = zone.get('wall_name', '')
            z_name = zone.get('name', '')
        else:
            z_surface = getattr(zone, 'surface_type', 'wall')
            z_room = getattr(zone, 'room_name', '')
            z_wall = getattr(zone, 'wall_name', '')
            z_name = getattr(zone, 'name', '')
        
        # Only check wall-type ceramic zones
        if z_surface != 'wall':
            return False
        
        # Only zones belonging to this room
        if z_room != room_name:
            return False
        
        # Check if zone matches this wall
        # Check 1: Explicit wall_name match (most reliable)
        if z_wall and z_wall == wall_name:
            return True
        
        # Check 2: Zone name contains pattern "RoomName - WallName"
        # This handles cases where wall_name wasn't saved but name follows pattern
        expected_pattern = f"{room_name} - {wall_name}"
        if expected_pattern in z_name:
            return True
        
        # Check 3: Legacy pattern - extract wall number from both
        # e.g., "Wall 2" matches "سيراميك - بلكون 2 - جدار 2"
        import re
        wall_num_match = re.search(r'(\d+)', wall_name)
        if wall_num_match:
            wall_num = wall_num_match.group(1)
            # Check if zone name ends with "جدار {num}" pattern
            if f"جدار {wall_num}" in z_name or f"Wall {wall_num}" in z_name:
                return True
        
        return False

    def _link_opening_to_wall(self):
        """Quick link: assign an opening to a selected wall."""
        if not self.selected_room:
            messagebox.showinfo("لا توجد غرفة", "اختر غرفة أولاً")
            return
            
        selection = self.walls_tree.selection()
        if not selection:
            messagebox.showinfo("لا يوجد اختيار", "اختر جدار لربط الفتحة به")
            return
        
        index = self.walls_tree.index(selection[0])
        
        # Handle both dict and Room object
        if isinstance(self.selected_room, dict):
            walls = self.selected_room.get('walls', []) or []
        else:
            walls = getattr(self.selected_room, 'walls', []) or []
        
        if index >= len(walls):
            return
        
        wall_data = walls[index]
        if isinstance(wall_data, dict):
            wall = Wall.from_dict(wall_data)
        else:
            wall = wall_data
        
        # Get room's openings
        room_openings = self.app.get_room_opening_summary(self.selected_room)
        available_doors = room_openings.get('door_ids', [])
        available_windows = room_openings.get('window_ids', [])
        
        if not available_doors and not available_windows:
            messagebox.showinfo("لا توجد فتحات", "الغرفة لا تحتوي على أبواب أو نوافذ")
            return
        
        # Create quick assignment dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"🔗 ربط فتحة بـ: {wall.name}")
        dialog.configure(bg=self.app.colors['bg_secondary'])
        dialog.transient(self.frame)
        dialog.grab_set()
        
        dialog.geometry("350x400")
        
        container = ttk.Frame(dialog, padding=16, style='Main.TFrame')
        container.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            container,
            text=f"🧱 الجدار: {wall.name} ({wall.length:.1f}×{wall.height:.1f}م)",
            font=('Segoe UI Semibold', 10),
            foreground=self.app.colors['accent']
        ).pack(anchor='w', pady=(0, 12))
        
        current_openings = getattr(wall, 'assigned_openings', []) or []
        
        # Doors
        ttk.Label(container, text="🚪 الأبواب:", foreground=self.app.colors['text_secondary']).pack(anchor='w')
        door_vars = {}
        for door_id in available_doors:
            var = tk.BooleanVar(value=door_id in current_openings)
            door_vars[door_id] = var
            door_info = ""
            for d in self.app.project.doors:
                if self.app._opening_name(d) == door_id:
                    w = self.app._opening_attr(d, 'w', 'width', 0)
                    h = self.app._opening_attr(d, 'h', 'height', 0)
                    door_info = f" ({w:.1f}×{h:.1f}م)"
                    break
            ttk.Checkbutton(container, text=f"{door_id}{door_info}", variable=var).pack(anchor='w', padx=20)
        
        if not available_doors:
            ttk.Label(container, text="لا توجد أبواب", foreground=self.app.colors['text_muted']).pack(anchor='w', padx=20)
        
        ttk.Separator(container, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Windows
        ttk.Label(container, text="🪟 النوافذ:", foreground=self.app.colors['text_secondary']).pack(anchor='w')
        window_vars = {}
        for win_id in available_windows:
            var = tk.BooleanVar(value=win_id in current_openings)
            window_vars[win_id] = var
            win_info = ""
            for w in self.app.project.windows:
                if self.app._opening_name(w) == win_id:
                    width = self.app._opening_attr(w, 'w', 'width', 0)
                    height = self.app._opening_attr(w, 'h', 'height', 0)
                    win_info = f" ({width:.1f}×{height:.1f}م)"
                    break
            ttk.Checkbutton(container, text=f"{win_id}{win_info}", variable=var).pack(anchor='w', padx=20)
        
        if not available_windows:
            ttk.Label(container, text="لا توجد نوافذ", foreground=self.app.colors['text_muted']).pack(anchor='w', padx=20)
        
        def save():
            selected = []
            for door_id, var in door_vars.items():
                if var.get():
                    selected.append(door_id)
            for win_id, var in window_vars.items():
                if var.get():
                    selected.append(win_id)
            
            wall.assigned_openings = selected
            
            # Recalculate deductions
            all_openings = list(self.app.project.doors) + list(self.app.project.windows)
            wall.recalculate_deductions(all_openings)
            
            # Update wall in room (handle both dict and Room object)
            if isinstance(self.selected_room, dict):
                walls_list = self.selected_room.get('walls', []) or []
                if index < len(walls_list):
                    walls_list[index] = wall.to_dict()
            else:
                walls_list = getattr(self.selected_room, 'walls', []) or []
                if index < len(walls_list):
                    walls_list[index] = wall
            
            self._load_room_details(self.selected_room)
            self.app.update_status(f"✅ تم ربط {len(selected)} فتحة بالجدار", icon="🔗")
            dialog.destroy()
        
        btn_frame = ttk.Frame(container, style='Main.TFrame')
        btn_frame.pack(fill=tk.X, pady=(16, 0))
        ttk.Button(btn_frame, text="💾 حفظ", command=save, style='Accent.TButton', width=12).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="❌ إلغاء", command=dialog.destroy, style='Secondary.TButton', width=12).pack(side=tk.RIGHT, padx=(0, 8))

    def _auto_distribute_openings(self, room):
        """Automatically distribute openings so each wall gets up to 2 doors and 2 windows."""
        if not room:
            return

        # Get all openings and their quantities for this room
        room_name = self.app._room_name(room)
        summary = self.app.get_room_opening_summary(room)
        door_instances: List[str] = []
        window_instances: List[str] = []
        
        # Flatten doors
        for door_id in summary.get('door_ids', []):
            # Find door object to get qty
            for d in self.app.project.doors:
                if self.app._opening_name(d) == door_id:
                    room_qtys = d.get('room_quantities', {}) if isinstance(d, dict) else getattr(d, 'room_quantities', {}) or {}
                    qty = int(room_qtys.get(room_name, 1))
                    door_instances.extend([door_id] * max(qty, 1))
                    break
        
        # Flatten windows
        for win_id in summary.get('window_ids', []):
            for w in self.app.project.windows:
                if self.app._opening_name(w) == win_id:
                    room_qtys = w.get('room_quantities', {}) if isinstance(w, dict) else getattr(w, 'room_quantities', {}) or {}
                    qty = int(room_qtys.get(room_name, 1))
                    window_instances.extend([win_id] * max(qty, 1))
                    break
        
        if not door_instances and not window_instances:
            return

        # Get walls
        if isinstance(room, dict):
            walls = room.get('walls', []) or []
        else:
            walls = getattr(room, 'walls', []) or []
            
        if not walls:
            return

        # Prepare slots with per-type counters
        wall_slots = []
        for wall in walls:
            if isinstance(wall, dict):
                wall['assigned_openings'] = []
                assigned_list = wall['assigned_openings']
            else:
                wall.assigned_openings = []
                assigned_list = wall.assigned_openings
            wall_slots.append({
                'wall': wall,
                'assigned': assigned_list,
                'door_count': 0,
                'window_count': 0,
            })

        def _assign_to_walls(opening_ids: List[str], kind: str) -> None:
            if not wall_slots:
                return
            max_per_wall = 2
            idx = 0
            for oid in opening_ids:
                if idx >= len(wall_slots):
                    idx = len(wall_slots) - 1
                slot = wall_slots[idx]
                slot['assigned'].append(oid)
                counter_key = 'door_count' if kind == 'door' else 'window_count'
                slot[counter_key] += 1
                if slot[counter_key] >= max_per_wall:
                    idx += 1

        # Assign independently so each wall can host 2 doors AND 2 windows
        _assign_to_walls(door_instances, 'door')
        _assign_to_walls(window_instances, 'window')
        
        # Recalculate deductions for all walls
        all_openings = list(self.app.project.doors) + list(self.app.project.windows)
        for wall in walls:
            if isinstance(wall, dict):
                # Convert to object to calc, then back
                w_obj = Wall.from_dict(wall)
                w_obj.recalculate_deductions(all_openings)
                # Update dict
                wall['deduct'] = w_obj.deduction_area
                wall['net'] = w_obj.net_area
                wall['net_area'] = w_obj.net_area
                wall['ceramic_area'] = w_obj.ceramic_area
            else:
                wall.recalculate_deductions(all_openings)

    def _auto_generate_walls(self):
        """Auto-generate walls from room perimeter (4 walls for rectangular rooms)."""
        if not self.selected_room:
            messagebox.showinfo("لا توجد غرفة", "اختر غرفة أولاً")
            return
        
        # Use the selected room directly
        actual_room = self.selected_room
            
        # Check if walls already exist
        existing_walls = []
        if isinstance(actual_room, dict):
            existing_walls = actual_room.get('walls', []) or []
        else:
            existing_walls = getattr(actual_room, 'walls', []) or []
            
        if existing_walls:
            if not messagebox.askyesno("تأكيد", f"يوجد بالفعل {len(existing_walls)} جدران.\nهل تريد استبدالها بالجدران التلقائية؟"):
                return
            # Clear existing walls
            if isinstance(actual_room, dict):
                actual_room['walls'] = []
            else:
                actual_room.walls = []
        
        width = self.app._room_attr(actual_room, 'w', 'width', None)
        length = self.app._room_attr(actual_room, 'l', 'length', None)
        perimeter = float(self.app._room_attr(actual_room, 'perim', 'perimeter', 0) or 0)
        wall_height = float(self.app._room_attr(actual_room, 'wall_height', 'wall_height', 3.0) or 3.0)
        room_layer = self.app._room_attr(actual_room, 'layer', 'layer', '')
        
        # Helper to add wall to room (handles dict and object)
        def add_wall_to_room(new_wall):
            if isinstance(actual_room, dict):
                if 'walls' not in actual_room:
                    actual_room['walls'] = []
                actual_room['walls'].append(new_wall.to_dict())
            else:
                if not hasattr(actual_room, 'walls') or actual_room.walls is None:
                    actual_room.walls = []
                actual_room.walls.append(new_wall)
        
        # Helper to get existing walls count
        def get_walls_count():
            if isinstance(actual_room, dict):
                return len(actual_room.get('walls', []) or [])
            else:
                return len(getattr(actual_room, 'walls', []) or [])
        
        if not width or not length:
            # Non-rectangular room: ask user how many walls
            dialog = tk.Toplevel(self.frame)
            dialog.title("إنشاء جدران من المحيط")
            dialog.configure(bg=self.app.colors['bg_secondary'])
            dialog.transient(self.frame)
            dialog.grab_set()
            dialog.geometry("350x200")
            
            container = ttk.Frame(dialog, padding=16, style='Main.TFrame')
            container.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(
                container,
                text=f"📐 المحيط: {perimeter:.2f}م | الارتفاع: {wall_height:.2f}م",
                foreground=self.app.colors['accent']
            ).pack(anchor='w', pady=(0, 12))
            
            ttk.Label(container, text="عدد الجدران:", foreground=self.app.colors['text_secondary']).pack(anchor='w')
            num_walls_var = tk.StringVar(value="4")
            ttk.Entry(container, textvariable=num_walls_var, width=10).pack(anchor='w', pady=(4, 12))
            
            def create():
                try:
                    n = int(num_walls_var.get())
                    if n <= 0:
                        return
                    wall_len = perimeter / n
                    for i in range(n):
                        new_wall = Wall(
                            name=f"جدار {get_walls_count() + 1}",
                            layer=room_layer,
                            length=wall_len,
                            height=wall_height
                        )
                        add_wall_to_room(new_wall)
                    
                    # Update selection and refresh
                    self.selected_room = actual_room
                    self._load_room_details(actual_room)
                    self.app.update_status(f"✅ تم إنشاء {n} جدران", icon="🧱")
                    dialog.destroy()
                except ValueError:
                    messagebox.showerror("خطأ", "أدخل رقم صحيح")
            
            ttk.Button(container, text="✅ إنشاء", command=create, style='Accent.TButton').pack(pady=8)
        else:
            # Rectangular room: create 4 walls
            walls_data = [
                ("جدار شمالي", float(width), wall_height, "شمال"),
                ("جدار جنوبي", float(width), wall_height, "جنوب"),
                ("جدار شرقي", float(length), wall_height, "شرق"),
                ("جدار غربي", float(length), wall_height, "غرب"),
            ]
            
            for name, w_len, h, direction in walls_data:
                new_wall = Wall(
                    name=name,
                    layer=room_layer,
                    length=w_len,
                    height=h,
                    direction=direction
                )
                add_wall_to_room(new_wall)
            
            # Update selection and refresh
            self.selected_room = actual_room
            
            # Auto-distribute existing openings to new walls
            self._auto_distribute_openings(actual_room)
            
            self._load_room_details(actual_room)
            self.app.update_status("✅ تم إنشاء 4 جدران (شمال/جنوب/شرق/غرب)", icon="🧱")

    def _recalculate_wall_deductions(self):
        """Recalculate deductions for all walls in selected room."""
        if not self.selected_room:
            return
        
        # Handle both dict and Room object
        if isinstance(self.selected_room, dict):
            walls = self.selected_room.get('walls', []) or []
        else:
            walls = getattr(self.selected_room, 'walls', []) or []
        
        if not walls:
            messagebox.showinfo("لا توجد جدران", "الغرفة لا تحتوي على جدران")
            return
        
        all_openings = list(self.app.project.doors) + list(self.app.project.windows)
        total_deduction = 0.0
        
        for i, wall_data in enumerate(walls):
            if isinstance(wall_data, dict):
                wall = Wall.from_dict(wall_data)
                wall.recalculate_deductions(all_openings)
                walls[i] = wall.to_dict()
                total_deduction += wall.deduction_area or 0
            else:
                if hasattr(wall_data, 'recalculate_deductions'):
                    wall_data.recalculate_deductions(all_openings)
                    total_deduction += getattr(wall_data, 'deduction_area', 0) or 0
        
        self._load_room_details(self.selected_room)
        self.app.update_status(f"✅ تم حساب الخصومات: {total_deduction:.2f}م²", icon="📊")

    def _auto_init_walls_if_needed(self, room):
        """Auto-generate walls for room if it has no walls but has dimensions.
        
        Refactored to use RoomAdapter for cleaner property access.
        """
        if room is None:
            return
        
        # Use RoomAdapter for unified access
        room_adapted = RoomAdapter(room)
        
        # Check if room already has walls
        walls = room_adapted.walls
        if walls:  # Already has walls
            return
        
        # Get dimensions
        width = room_adapted.width
        length = room_adapted.length
        perimeter = room_adapted.perimeter
        wall_height = room_adapted.wall_height
        room_layer = room_adapted.layer
        
        # Need either perimeter or width+length, and wall_height
        if perimeter <= 0 and (not width or not length):
            return  # No dimensions to work with
        
        if wall_height <= 0:
            wall_height = 3.0  # Default height if not set
        
        # Calculate perimeter from width/length if not available
        if perimeter <= 0 and width and length:
            perimeter = 2 * (float(width) + float(length))
        
        # Helper to add wall
        def add_wall(new_wall):
            if isinstance(room, dict):
                if 'walls' not in room:
                    room['walls'] = []
                room['walls'].append(new_wall.to_dict())
            else:
                if not hasattr(room, 'walls') or room.walls is None:
                    room.walls = []
                room.walls.append(new_wall)
        
        if width and length:
            # Rectangular room: create 4 walls
            w = float(width)
            l = float(length)
            walls_data = [
                ("جدار 1 (شمال)", w, wall_height, "شمال"),
                ("جدار 2 (شرق)", l, wall_height, "شرق"),
                ("جدار 3 (جنوب)", w, wall_height, "جنوب"),
                ("جدار 4 (غرب)", l, wall_height, "غرب"),
            ]
            
            for name, w_len, h, direction in walls_data:
                new_wall = Wall(
                    name=name,
                    layer=room_layer,
                    length=w_len,
                    height=h,
                    direction=direction,
                    gross_area=w_len * h
                )
                add_wall(new_wall)
        else:
            # Non-rectangular: create 4 equal walls from perimeter
            wall_len = perimeter / 4
            for i in range(4):
                new_wall = Wall(
                    name=f"جدار {i + 1}",
                    layer=room_layer,
                    length=wall_len,
                    height=wall_height,
                    gross_area=wall_len * wall_height
                )
                add_wall(new_wall)

    def _create_openings_section(self):
        """Create section for managing room openings (doors, windows)."""
        openings_frame = ttk.LabelFrame(
            self.details_content,
            text="  🚪🪟 الفتحات  ",
            padding=(12, 8),
            style='Card.TLabelframe'
        )
        openings_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        
        # Doors subsection
        ttk.Label(
            openings_frame,
            text="🚪 الأبواب",
            foreground=self.app.colors['accent'],
            font=('Segoe UI Semibold', 10)
        ).pack(anchor=tk.W, pady=(0, 4))
        
        self.doors_tree = ttk.Treeview(
            openings_frame,
            columns=('Name', 'Type', 'Size', 'Qty', 'Height'),
            show='headings',
            height=4
        )
        
        self.doors_tree.heading('Name', text='الاسم')
        self.doors_tree.heading('Type', text='النوع')
        self.doors_tree.heading('Size', text='ع×ا (م)')
        self.doors_tree.heading('Qty', text='العدد')
        self.doors_tree.heading('Height', text='من الأرض')
        
        self.doors_tree.column('Name', width=100)
        self.doors_tree.column('Type', width=80)
        self.doors_tree.column('Size', width=80)
        self.doors_tree.column('Qty', width=50)
        self.doors_tree.column('Height', width=80)
        
        self.doors_tree.pack(fill=tk.X, pady=(0, 4))
        
        doors_btn_frame = ttk.Frame(openings_frame, style='Main.TFrame')
        doors_btn_frame.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Button(
            doors_btn_frame,
            text="➕ إضافة",
            command=lambda: self._add_opening('DOOR'),
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=(0, 4))
        
        ttk.Button(
            doors_btn_frame,
            text="✏️ تعديل",
            command=lambda: self._edit_opening('DOOR'),
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=4)
        
        ttk.Button(
            doors_btn_frame,
            text="🗑️",
            command=lambda: self._remove_opening('DOOR'),
            style='Danger.TButton',
            width=4
        ).pack(side=tk.RIGHT)
        
        # Quick-add common door types
        quick_doors_frame = ttk.Frame(openings_frame, style='Main.TFrame')
        quick_doors_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(
            quick_doors_frame,
            text="إضافة سريعة:",
            foreground=self.app.colors['text_secondary'],
            font=('Segoe UI', 8)
        ).pack(side=tk.LEFT, padx=(0, 4))
        
        ttk.Button(
            quick_doors_frame,
            text="1×2 PVC",
            command=lambda: self._quick_add_opening('DOOR', '1.0×2.0 PVC'),
            style='Accent.TButton',
            width=10
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            quick_doors_frame,
            text="0.9×2 PVC",
            command=lambda: self._quick_add_opening('DOOR', '0.9×2.0 PVC'),
            style='Accent.TButton',
            width=10
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            quick_doors_frame,
            text="1×2 حديد 120",
            command=lambda: self._quick_add_opening('DOOR', '1.0×2.0 Steel 120kg'),
            style='Accent.TButton',
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        # Windows subsection
        ttk.Separator(openings_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        
        ttk.Label(
            openings_frame,
            text="🪟 النوافذ",
            foreground=self.app.colors['accent'],
            font=('Segoe UI Semibold', 10)
        ).pack(anchor=tk.W, pady=(0, 4))
        
        self.windows_tree = ttk.Treeview(
            openings_frame,
            columns=('Name', 'Type', 'Size', 'Qty', 'Height'),
            show='headings',
            height=4
        )
        
        self.windows_tree.heading('Name', text='الاسم')
        self.windows_tree.heading('Type', text='النوع')
        self.windows_tree.heading('Size', text='ع×ا (م)')
        self.windows_tree.heading('Qty', text='العدد')
        self.windows_tree.heading('Height', text='ارتفاع الدكة')
        
        self.windows_tree.column('Name', width=100)
        self.windows_tree.column('Type', width=80)
        self.windows_tree.column('Size', width=80)
        self.windows_tree.column('Qty', width=50)
        self.windows_tree.column('Height', width=80)
        
        self.windows_tree.pack(fill=tk.X, pady=(0, 4))
        
        windows_btn_frame = ttk.Frame(openings_frame, style='Main.TFrame')
        windows_btn_frame.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Button(
            windows_btn_frame,
            text="➕ إضافة",
            command=lambda: self._add_opening('WINDOW'),
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=(0, 4))
        
        ttk.Button(
            windows_btn_frame,
            text="✏️ تعديل",
            command=lambda: self._edit_opening('WINDOW'),
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=4)
        
        ttk.Button(
            windows_btn_frame,
            text="🗑️",
            command=lambda: self._remove_opening('WINDOW'),
            style='Danger.TButton',
            width=4
        ).pack(side=tk.RIGHT)
        
        # Quick-add common window types
        quick_windows_frame = ttk.Frame(openings_frame, style='Main.TFrame')
        quick_windows_frame.pack(fill=tk.X)
        
        ttk.Label(
            quick_windows_frame,
            text="إضافة سريعة:",
            foreground=self.app.colors['text_secondary'],
            font=('Segoe UI', 8)
        ).pack(side=tk.LEFT, padx=(0, 4))
        
        ttk.Button(
            quick_windows_frame,
            text="0.5×1.5 PVC",
            command=lambda: self._quick_add_opening('WINDOW', '0.5×1.5 PVC'),
            style='Accent.TButton',
            width=11
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            quick_windows_frame,
            text="1×1.5 ألمنيوم",
            command=lambda: self._quick_add_opening('WINDOW', '1.0×1.5 Aluminum'),
            style='Accent.TButton',
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            quick_windows_frame,
            text="1.6×1.4 ألمنيوم",
            command=lambda: self._quick_add_opening('WINDOW', '1.6×1.4 Aluminum'),
            style='Accent.TButton',
            width=12
        ).pack(side=tk.LEFT, padx=2)

        # Bulk assignment tools
        ttk.Separator(openings_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        bulk_frame = ttk.Frame(openings_frame, style='Main.TFrame')
        bulk_frame.pack(fill=tk.X, pady=(0,4))
        ttk.Label(bulk_frame, text="تعيين جماعي:", foreground=self.app.colors['text_secondary']).pack(side=tk.LEFT)
        ttk.Button(bulk_frame, text="أبواب ➜ غرف", style='Secondary.TButton', command=self._bulk_assign_doors).pack(side=tk.LEFT, padx=4)
        ttk.Button(bulk_frame, text="نوافذ ➜ غرف", style='Secondary.TButton', command=self._bulk_assign_windows).pack(side=tk.LEFT, padx=4)
        ttk.Button(bulk_frame, text="سيراميك ➜ غرف", style='Secondary.TButton', command=self._bulk_add_ceramic).pack(side=tk.LEFT, padx=4)
        
        # Wall-Opening Links for balconies
        wall_links_frame = ttk.Frame(openings_frame, style='Main.TFrame')
        wall_links_frame.pack(fill=tk.X, pady=(8,4))
        ttk.Button(
            wall_links_frame,
            text="🔗 عرض روابط الجدار-الفتحات (بلكون)",
            style='Secondary.TButton',
            command=self._show_wall_opening_links
        ).pack(fill=tk.X)
        
        # Auto Update All button
        auto_all_frame = ttk.Frame(openings_frame, style='Main.TFrame')
        auto_all_frame.pack(fill=tk.X, pady=(8,4))
        ttk.Button(
            auto_all_frame,
            text="⚡ تحديث تلقائي لجميع الغرف",
            style='Accent.TButton',
            command=self._auto_update_all_rooms
        ).pack(fill=tk.X)
        
        # Total Counter (for THIS room only)
        total_frame = ttk.Frame(openings_frame, style='Main.TFrame')
        total_frame.pack(fill=tk.X, pady=(8,4))
        self.openings_total_label = ttk.Label(
            total_frame, 
            text="📊 الإجمالي في هذه الغرفة: 0 أبواب | 0 نوافذ", 
            foreground=self.app.colors['accent'],
            font=('Segoe UI', 9, 'bold')
        )
        self.openings_total_label.pack(anchor='center')
        
        return openings_frame
        
    def _create_finishes_section(self):
        """Create section for finishes (ceramic, plaster, paint)."""
        finishes_frame = ttk.LabelFrame(
            self.details_content,
            text="  🎨 التشطيبات والحسابات  ",
            padding=(12, 8),
            style='Card.TLabelframe'
        )
        finishes_frame.pack(fill=tk.X, padx=8, pady=4)
        
        # Ceramic
        row = 0
        ttk.Label(
            finishes_frame,
            text="السيراميك (م²):",
            foreground=self.app.colors['text_secondary']
        ).grid(row=row, column=0, sticky='w', pady=4)
        
        self.room_ceramic_var = tk.StringVar()
        ceramic_entry = ttk.Entry(finishes_frame, textvariable=self.room_ceramic_var, width=12, state='readonly')
        ceramic_entry.grid(row=row, column=1, sticky='w', pady=4, padx=(8, 0))
        
        # Plaster
        row += 1
        ttk.Label(
            finishes_frame,
            text="البياض (م²):",
            foreground=self.app.colors['text_secondary']
        ).grid(row=row, column=0, sticky='w', pady=4)
        
        self.room_plaster_var = tk.StringVar()
        plaster_entry = ttk.Entry(finishes_frame, textvariable=self.room_plaster_var, width=12, state='readonly')
        plaster_entry.grid(row=row, column=1, sticky='w', pady=4, padx=(8, 0))
        
        # Paint
        row += 1
        ttk.Label(
            finishes_frame,
            text="الدهان (م²):",
            foreground=self.app.colors['text_secondary']
        ).grid(row=row, column=0, sticky='w', pady=4)
        
        self.room_paint_var = tk.StringVar()
        paint_entry = ttk.Entry(finishes_frame, textvariable=self.room_paint_var, width=12, state='readonly')
        paint_entry.grid(row=row, column=1, sticky='w', pady=4, padx=(8, 0))
        
        # Ceramic breakdown button
        row += 1
        ttk.Button(
            finishes_frame,
            text="🔍 عرض تفاصيل السيراميك",
            command=self._show_ceramic_details,
            style='Secondary.TButton',
            width=22
        ).grid(row=row, column=0, columnspan=2, pady=(4, 0), sticky='ew')
        
        # === NEW SPECIFIC AUTO-ADD BUTTONS ===
        # Separator
        row += 1
        ttk.Separator(finishes_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', pady=(10, 6))
        
        ttk.Label(
            finishes_frame,
            text="📦 إضافات تلقائية",
            foreground=self.app.colors['accent'],
            font=('Segoe UI', 9, 'bold')
        ).grid(row=row, column=0, columnspan=2, pady=(0, 4))
        
        # 1. Auto Add Plaster to All Walls
        row += 1
        ttk.Button(
            finishes_frame,
            text="🏗️ إضافة لياسة لجميع الجدران",
            command=self._auto_add_plaster_all_walls,
            style='Accent.TButton'
        ).grid(row=row, column=0, columnspan=2, pady=(4, 0), sticky='ew')
        
        # 2. Auto Add Ceramic to All Floors
        row += 1
        ttk.Button(
            finishes_frame,
            text="🟫 إضافة سيراميك لجميع الأرضيات",
            command=self._auto_add_ceramic_all_floors,
            style='Accent.TButton'
        ).grid(row=row, column=0, columnspan=2, pady=(4, 0), sticky='ew')
        
        # 3. Auto Add Ceramic to Walls (Kitchen/Toilet/Bath/Balcony)
        row += 1
        ttk.Button(
            finishes_frame,
            text="🧱 سيراميك جدران (مطبخ/حمام/تواليت/بلكون)",
            command=self._auto_add_ceramic_walls_dialog,
            style='Accent.TButton'
        ).grid(row=row, column=0, columnspan=2, pady=(4, 0), sticky='ew')
        
        # Manual Add Ceramic
        row += 1
        ttk.Button(
            finishes_frame,
            text="➕ إضافة سيراميك يدوي",
            command=self._add_ceramic_manual,
            style='Secondary.TButton'
        ).grid(row=row, column=0, columnspan=2, pady=(8, 0), sticky='ew')
        
        # Live Metrics (Reactive) panel
        row += 1
        metrics_frame = ttk.LabelFrame(
            finishes_frame,
            text="  📡 المقاييس الحية  ",
            padding=(8, 6),
            style='Card.TLabelframe'
        )
        metrics_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(10, 0))

        # Initialize metrics labels dictionary
        self.metrics_labels = {}

        metrics_spec = [
            ('walls_gross', 'جدران إجمالي (م²)'),
            ('openings', 'إجمالي الفتحات (م²)'),
            ('walls_net', 'جدران صافي (م²)'),
            ('plaster', 'لياسة (م²)'),
            ('cer_wall', 'سيراميك جدار (م²)'),
            ('cer_floor', 'سيراميك أرضية (م²)'),
            ('cer_ceiling', 'سيراميك سقف (م²)'),
            ('paint_walls', 'دهان جدران (م²)'),
            ('paint_ceiling', 'دهان سقف (م²)'),
        ]

        for r_idx, (key, label_text) in enumerate(metrics_spec):
            ttk.Label(
                metrics_frame,
                text=label_text + ':',
                foreground=self.app.colors['text_secondary']
            ).grid(row=r_idx, column=0, sticky='w', pady=2)
            value_lbl = ttk.Label(
                metrics_frame,
                text='-',
                style='Metrics.TLabel'
            )
            value_lbl.grid(row=r_idx, column=1, sticky='w', padx=(8,0), pady=2)
            self.metrics_labels[key] = value_lbl

        return finishes_frame
        
    def _create_actions_section(self):
        """Create bottom action buttons."""
        actions_frame = ttk.Frame(self.details_content, style='Main.TFrame')
        actions_frame.pack(fill=tk.X, padx=8, pady=(4, 8))
        
        ttk.Button(
            actions_frame,
            text="📊 عرض في الملخص",
            command=self._view_in_summary,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=(0, 4))
        
        ttk.Button(
            actions_frame,
            text="🔄 تحديث كل التابات",
            command=self._refresh_all_tabs,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=4)
        
        return actions_frame
        
    def _show_no_selection_message(self):
        """Show message when no room is selected."""
        # Hide all detail widgets
        for widget in self.details_content.winfo_children():
            widget.pack_forget()
        
        # Show centered message
        msg_frame = ttk.Frame(self.details_content, style='Main.TFrame')
        msg_frame.pack(expand=True, fill=tk.BOTH, pady=100)
        
        ttk.Label(
            msg_frame,
            text="🏠",
            font=('Segoe UI', 48),
            foreground=self.app.colors['text_muted']
        ).pack()
        
        ttk.Label(
            msg_frame,
            text="اختر غرفة لعرض التفاصيل",
            font=('Segoe UI', 14),
            foreground=self.app.colors['text_muted']
        ).pack(pady=(8, 0))
        self._render_room_visuals(None)
        
    def _show_details_widgets(self):
        """Show all detail widgets when a room is selected."""
        # Clear all widgets
        for widget in self.details_content.winfo_children():
            widget.pack_forget()
        
        # Repack detail sections in order
        if hasattr(self, 'detail_sections'):
            for section in self.detail_sections:
                if section and section.winfo_exists():
                    if section is self.room_visuals_frame:
                        section.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
                    else:
                        section.pack(fill=tk.X, padx=8, pady=4)
        
    # === Event Handlers ===
    
    def _filter_rooms(self, *args):
        """Filter rooms list based on search text."""
        self.refresh_rooms_list()
        
    def _on_room_selected(self, event):
        """Handle room selection in treeview."""
        selection = self.rooms_list_tree.selection()
        if not selection:
            self._show_no_selection_message()
            self.selected_room = None
            return
        
        # Get selected room via IID map if available, otherwise fallback to name
        item_id = selection[0]
        
        if hasattr(self, 'iid_room_map') and item_id in self.iid_room_map:
            self.selected_room = self.iid_room_map[item_id]
            self._load_room_details(self.selected_room)
            self._show_details_widgets()
            return

        # Fallback (legacy behavior)
        item_values = self.rooms_list_tree.item(item_id, 'values')
        room_name = item_values[0]
        
        # Find room in project
        for room in self.app.project.rooms:
            if self.app._room_name(room) == room_name:
                self.selected_room = room
                self._load_room_details(room)
                self._show_details_widgets()
                break
                
    def _load_room_details(self, room):
        """Load room data into detail widgets."""
        # Use the passed room object directly if possible
        # Only look up if we suspect we have a stale copy, but trusting the passed object is safer for duplicates
        actual_room = room
        
        # Update selected_room to the actual reference
        self.selected_room = actual_room
        
        # Auto-generate walls if room has none (but has dimensions)
        self._auto_init_walls_if_needed(actual_room)
        
        # Sync ceramic zones to walls for correct visualization
        self._sync_ceramic_zones_to_walls(actual_room)
        
        # Use RoomAdapter for unified property access
        room_adapted = RoomAdapter(actual_room)
        
        name = room_adapted.name
        layer = room_adapted.layer
        w = room_adapted.width or 0.0
        l = room_adapted.length or 0.0
        perim = room_adapted.perimeter
        area = room_adapted.area
        wall_h = room_adapted.wall_height
        has_balcony = room_adapted.has_balcony
        balcony_segs = room_adapted.balcony_segments
        ceramic = room_adapted.ceramic_area
        plaster = room_adapted.plaster_area
        paint = room_adapted.paint_area
        
        # Set property values
        self.room_name_var.set(name)
        self.room_layer_var.set(layer)
        self.room_width_var.set(f"{w:.2f}" if w else "")
        self.room_length_var.set(f"{l:.2f}" if l else "")
        self.room_perim_var.set(f"{perim:.2f}" if perim else "")
        self.room_area_var.set(f"{area:.2f}" if area else "")
        self.room_wall_height_var.set(f"{wall_h:.2f}" if wall_h else "")
        
        # Balcony
        self.room_has_balcony_var.set(has_balcony)
        if has_balcony and balcony_segs:
            for i, seg in enumerate(balcony_segs[:4]):
                self.balcony_seg_vars[i].set(f"{seg:.2f}" if seg else "0")
        self._toggle_balcony_controls()
        
        # Finishes
        # Show 0.00 instead of '-' when ceramic area is zero so users can see that auto presets ran
        if ceramic is None:
            self.room_ceramic_var.set("-")
        else:
            try:
                self.room_ceramic_var.set(f"{float(ceramic):.2f}")
            except Exception:
                self.room_ceramic_var.set("0.00")
        self.room_plaster_var.set(f"{plaster:.2f}" if plaster else "-")
        self.room_paint_var.set(f"{paint:.2f}" if paint else "-")
        
        # Load openings
        self._refresh_walls_tree()
        self._refresh_openings_trees()

        # Live metrics (reactive preview)
        try:
            metrics = self._compute_room_finish_metrics(room)
            self._update_room_metrics_ui(metrics)
        except Exception:
            pass
        self._render_room_visuals(room)
        
    def _toggle_balcony_controls(self):
        """Show/hide balcony segment inputs."""
        if self.room_has_balcony_var.get():
            self.balcony_frame.grid()
        else:
            self.balcony_frame.grid_remove()

    def _render_room_visuals(self, room):
        """Send latest room data to the visuals canvas."""
        if getattr(self, 'room_canvas', None) and self.room_canvas.winfo_exists():
            self.room_canvas.render_room(room)

    def _recalculate_wall_partial_ceramic(self, room, update_breakdown: bool = True) -> float:
        """Recompute partial ceramic bands defined per-wall and sync breakdown if needed."""
        if not room:
            return 0.0

        adapter = RoomAdapter(room)
        walls = adapter.walls or []
        total_partial = 0.0

        def _get(item, attr, default=None):
            if isinstance(item, dict):
                return item.get(attr, default)
            return getattr(item, attr, default)

        def _set(item, attr, value):
            if isinstance(item, dict):
                item[attr] = value
            else:
                setattr(item, attr, value)

        for idx, wall in enumerate(walls):
            length = float(_get(wall, 'length', 0.0) or 0.0)
            height = float(_get(wall, 'height', 0.0) or 0.0)
            ceramic_height = float(_get(wall, 'ceramic_height', 0.0) or 0.0)
            length = float(_get(wall, 'length', 0.0) or 0.0)
            height = float(_get(wall, 'height', 0.0) or 0.0)
            ceramic_height = float(_get(wall, 'ceramic_height', 0.0) or 0.0)

            if length <= 0 or height <= 0 or ceramic_height <= 0:
                _set(wall, 'ceramic_area', 0.0)
                continue

            ceramic_height = min(ceramic_height, height)
            _set(wall, 'ceramic_height', ceramic_height)
            ceramic_surface = _get(wall, 'ceramic_surface', 'سيراميك') or 'سيراميك'
            _set(wall, 'ceramic_surface', ceramic_surface)

            base_area = length * ceramic_height
            gross_area = float(_get(wall, 'gross_area', _get(wall, 'gross', length * height)) or 0.0)
            if gross_area == 0:
                gross_area = length * height
            net_area = float(_get(wall, 'net_area', _get(wall, 'net', gross_area)) or gross_area)

            if gross_area > 0 and net_area is not None:
                ratio = max(0.0, min(1.0, net_area / gross_area))
                ceramic_area = base_area * ratio
            else:
                ceramic_area = base_area

            _set(wall, 'ceramic_area', ceramic_area)
            total_partial += ceramic_area

        if update_breakdown:
            breakdown = adapter.ceramic_breakdown.copy() if adapter.ceramic_breakdown else {}
            prev_partial = float(breakdown.get('wall_partial', 0.0) or 0.0)
            base_wall = breakdown.get('wall_zones')
            if base_wall is None:
                recorded_wall = float(breakdown.get('wall', 0.0) or 0.0)
                base_wall = max(0.0, recorded_wall - prev_partial)
            breakdown['wall_zones'] = float(base_wall or 0.0)
            breakdown['wall_partial'] = total_partial
            breakdown['wall'] = breakdown['wall_zones'] + total_partial
            adapter.ceramic_breakdown = breakdown
            adapter.ceramic_area = self._ceramic_breakdown_total(breakdown)

        return total_partial

    @staticmethod
    def _ceramic_breakdown_total(breakdown: dict) -> float:
        """Sum ceramic breakdown values while skipping helper keys."""
        total = 0.0
        for key, value in (breakdown or {}).items():
            if key.endswith('_partial') or key.endswith('_zones'):
                continue
            try:
                total += float(value or 0.0)
            except (TypeError, ValueError):
                continue
        return total
            
    def _refresh_walls_tree(self):
        """Refresh walls treeview for selected room with full details."""
        # Clear existing
        for item in self.walls_tree.get_children():
            self.walls_tree.delete(item)
            
        if not self.selected_room:
            if hasattr(self, 'walls_summary_label'):
                self.walls_summary_label.config(text="📊 إجمالي: 0 جدران | المساحة: 0.00 م²")
            self._render_room_visuals(None)
            return
        
        # Use selected_room directly - avoid re-lookup by name which can fail with duplicates
        actual_room = self.selected_room
        
        # Try to auto-generate walls if room has none
        self._auto_init_walls_if_needed(actual_room)
        
        # Handle dict vs object for walls list
        if isinstance(actual_room, dict):
            walls = actual_room.get('walls', []) or []
        else:
            walls = getattr(actual_room, 'walls', []) or []

        # Refresh partial ceramic cache before showing UI (also clears stale values)
        partial_ceramic_total = self._recalculate_wall_partial_ceramic(actual_room, update_breakdown=True)
        
        # If still no walls, show a message
        if not walls:
            if hasattr(self, 'walls_summary_label'):
                summary_text = "📊 لا توجد جدران | اضغط 'إنشاء من المحيط' ⚡"
                if partial_ceramic_total > 0:
                    summary_text += f" | سيراميك جزئي: {partial_ceramic_total:.2f} م²"
                self.walls_summary_label.config(text=summary_text)
            self._render_room_visuals(actual_room)
            return
        
        total_area = 0.0
        total_net_area = 0.0
            
        # Populate walls
        for wall in walls:
            # Handle dict vs object for wall item
            if isinstance(wall, dict):
                name = wall.get('name', 'جدار')
                length = float(wall.get('length', 0.0) or 0.0)
                height = float(wall.get('height', 0.0) or 0.0)
                gross_area = float(wall.get('gross_area', wall.get('gross', 0.0)) or 0.0)
                if gross_area == 0 and length > 0 and height > 0:
                    gross_area = length * height
                surface_type = wall.get('surface_type', 'دهان')
                assigned_openings = wall.get('assigned_openings', []) or []
                net_area = float(wall.get('net_area', gross_area) or gross_area)
                ceramic_height = float(wall.get('ceramic_height', 0.0) or 0.0)
                ceramic_surface = wall.get('ceramic_surface', 'سيراميك')
                ceramic_area = float(wall.get('ceramic_area', 0.0) or 0.0)
            else:
                name = getattr(wall, 'name', 'جدار')
                length = float(getattr(wall, 'length', 0.0) or 0.0)
                height = float(getattr(wall, 'height', 0.0) or 0.0)
                gross_area = float(getattr(wall, 'gross_area', 0.0) or 0.0)
                if gross_area == 0 and length > 0 and height > 0:
                    gross_area = length * height
                surface_type = getattr(wall, 'surface_type', 'دهان')
                assigned_openings = getattr(wall, 'assigned_openings', []) or []
                net_area = float(getattr(wall, 'net_area', gross_area) or gross_area)
                ceramic_height = float(getattr(wall, 'ceramic_height', 0.0) or 0.0)
                ceramic_surface = getattr(wall, 'ceramic_surface', 'سيراميك')
                ceramic_area = float(getattr(wall, 'ceramic_area', 0.0) or 0.0)
            
            total_area += gross_area
            total_net_area += net_area
            
            # Format openings list
            openings_str = ','.join(assigned_openings) if assigned_openings else '-'
            if len(openings_str) > 15:
                openings_str = openings_str[:12] + '...'

            # Partial ceramic summary per wall
            if ceramic_height > 0:
                ceramic_display = f"{ceramic_height:.2f}م {ceramic_surface}"
                if ceramic_area > 0:
                    ceramic_display += f" • {ceramic_area:.2f}م²"
            else:
                ceramic_display = '-'
            
            # Display ceramic height if exists, otherwise wall height
            height_display = f"{ceramic_height:.2f}م" if ceramic_height > 0 else f"{height:.2f}م"

            self.walls_tree.insert('', tk.END, values=(
                name,
                f"{length:.2f}م",
                height_display,
                f"{gross_area:.2f}م²",
                surface_type,
                ceramic_display,
                openings_str
            ))
        
        # Force update to ensure visibility
        self.walls_tree.update_idletasks()
        
        # Update summary label for THIS room only
        if hasattr(self, 'walls_summary_label'):
            deduction = total_area - total_net_area
            summary_text = f"📊 {len(walls)} جدران | الإجمالي: {total_area:.2f} م²"
            if deduction > 0:
                summary_text += f" | الصافي: {total_net_area:.2f} م²"
            if partial_ceramic_total > 0:
                summary_text += f" | سيراميك جزئي: {partial_ceramic_total:.2f} م²"
            self.walls_summary_label.config(text=summary_text)
        self._render_room_visuals(actual_room)

    def _refresh_openings_trees(self):
        """Refresh doors and windows treeviews for selected room."""
        # Clear existing
        for item in self.doors_tree.get_children():
            self.doors_tree.delete(item)
        for item in self.windows_tree.get_children():
            self.windows_tree.delete(item)
        
        if not self.selected_room:
            return
        
        room_name = self.app._room_name(self.selected_room)
        
        # Get assigned openings
        room_openings = self.app.get_room_opening_summary(self.selected_room)
        door_ids = room_openings.get('door_ids', [])
        window_ids = room_openings.get('window_ids', [])
        
        # Populate doors
        for door in self.app.project.doors:
            door_name = self.app._opening_name(door)
            if door_name in door_ids:
                typ = self.app._opening_attr(door, 'type', 'material_type', '-')
                w = self.app._opening_attr(door, 'w', 'width', 0.0)
                h = self.app._opening_attr(door, 'h', 'height', 0.0)
                placement = self.app._opening_attr(door, 'placement_height', 'placement_height', 0.0)
                
                # Get room-specific quantity
                room_qtys = door.get('room_quantities', {}) if isinstance(door, dict) else getattr(door, 'room_quantities', {}) or {}
                qty = room_qtys.get(room_name, 1)
                
                self.doors_tree.insert('', tk.END, values=(
                    door_name,
                    typ,
                    f"{w:.2f}×{h:.2f}",
                    qty,
                    f"{placement:.2f}m" if placement is not None else "0.00m"
                ))
        
        # Populate windows
        for window in self.app.project.windows:
            win_name = self.app._opening_name(window)
            if win_name in window_ids:
                typ = self.app._opening_attr(window, 'type', 'material_type', '-')
                w = self.app._opening_attr(window, 'w', 'width', 0.0)
                h = self.app._opening_attr(window, 'h', 'height', 0.0)
                placement = self.app._opening_attr(window, 'placement_height', 'placement_height', 1.0)
                
                # Get room-specific quantity
                room_qtys = window.get('room_quantities', {}) if isinstance(window, dict) else getattr(window, 'room_quantities', {}) or {}
                qty = room_qtys.get(room_name, 1)
                
                self.windows_tree.insert('', tk.END, values=(
                    win_name,
                    typ,
                    f"{w:.2f}×{h:.2f}",
                    qty,
                    f"{placement:.2f}m" if placement is not None else "1.00m"
                ))

        # Update total counter
        if hasattr(self, 'openings_total_label'):
            d_count = 0
            w_count = 0
            # Sum quantities from tree items
            for item in self.doors_tree.get_children():
                try:
                    d_count += int(self.doors_tree.item(item, 'values')[3])
                except (ValueError, IndexError):
                    pass
            for item in self.windows_tree.get_children():
                try:
                    w_count += int(self.windows_tree.item(item, 'values')[3])
                except (ValueError, IndexError):
                    pass
            
            self.openings_total_label.config(text=f"📊 الإجمالي في هذه الغرفة: {d_count} أبواب | {w_count} نوافذ")

        # Recalculate ceramic with opening deductions (reactive)
        try:
            self._recalculate_room_ceramic_with_openings(self.selected_room)
            # Refresh ceramic display after recalculation
            if self.selected_room:
                ceramic = self.app._room_attr(self.selected_room, 'ceramic_area', 'ceramic_area', None)
                if ceramic is None:
                    self.room_ceramic_var.set("-")
                else:
                    try:
                        self.room_ceramic_var.set(f"{float(ceramic):.2f}")
                    except Exception:
                        self.room_ceramic_var.set("0.00")
        except Exception:
            pass
        
        # Update live metrics after openings refresh
        try:
            metrics = self._compute_room_finish_metrics(self.selected_room)
            self._update_room_metrics_ui(metrics)
        except Exception:
            pass
        self._render_room_visuals(self.selected_room)

    def _compute_room_finish_metrics(self, room):
        """Compute reactive finish metrics for a room using UnifiedCalculator.

        Uses UnifiedCalculator (Single Source of Truth) for consistent calculations.
        """
        # Ensure per-wall partial ceramic areas are computed on walls
        self._recalculate_wall_partial_ceramic(room, update_breakdown=False)

        from bilind.calculations.unified_calculator import UnifiedCalculator
        
        project = getattr(self.app, 'project', None)
        if not project:
            return
        
        calc = UnifiedCalculator(project)
        room_calc = calc.calculate_room(room)

        # Compute perimeter and wall height for UI display
        try:
            perimeter = float(getattr(room, 'perimeter', 0.0) or 0.0) if not isinstance(room, dict) else float(room.get('perimeter', room.get('perim', 0.0)) or 0.0)
        except Exception:
            perimeter = 0.0
        if perimeter <= 0:
            try:
                walls = room.get('walls', []) if isinstance(room, dict) else (getattr(room, 'walls', []) or [])
                perimeter = sum(float((w.get('length', 0.0) if isinstance(w, dict) else getattr(w, 'length', 0.0)) or 0.0) for w in (walls or []))
            except Exception:
                perimeter = 0.0

        try:
            wall_height = float(room.get('wall_height', 3.0) or 3.0) if isinstance(room, dict) else float(getattr(room, 'wall_height', 3.0) or 3.0)
        except Exception:
            wall_height = 3.0

        # Breakdown openings into doors/windows areas (for legacy UI fields)
        doors_area = 0.0
        windows_area = 0.0
        try:
            room_name = (room.get('name', '') if isinstance(room, dict) else getattr(room, 'name', ''))
            opening_ids = room.get('opening_ids', []) if isinstance(room, dict) else (getattr(room, 'opening_ids', []) or [])
            for oid in (opening_ids or []):
                opening = calc.openings_map.get(oid)
                if not opening:
                    continue
                otype = str(calc._get_attr(opening, 'opening_type', '') or '').upper()
                ow = float(calc._get_opening_width(opening) or 0.0)
                oh = float(calc._get_opening_height(opening) or 0.0)
                qtys = calc._get_attr(opening, 'room_quantities', {}) or {}
                q = int(qtys.get(room_name, 1) or 1)
                area = ow * oh * q
                if otype == 'DOOR':
                    doors_area += area
                elif otype == 'WINDOW':
                    windows_area += area
        except Exception:
            pass

        # Sync back to room model for display (deprecated fields)
        try:
            room_adapted = RoomAdapter(room)
            room_adapted.plaster_area = room_calc.plaster_total
            room_adapted.paint_area = room_calc.paint_total
        except Exception:
            pass

        return {
            'perimeter': perimeter,
            'wall_height': wall_height,
            'walls_gross': float(room_calc.walls_gross or 0.0),
            'doors_area': float(doors_area or 0.0),
            'windows_area': float(windows_area or 0.0),
            'openings_total': float(room_calc.walls_openings or 0.0),
            'walls_net': float(room_calc.walls_net or 0.0),
            'plaster': float(room_calc.plaster_total or 0.0),
            'cer_wall': float(room_calc.ceramic_wall or 0.0),
            'cer_floor': float(room_calc.ceramic_floor or 0.0),
            'cer_ceiling': float(room_calc.ceramic_ceiling or 0.0),
            'walls_paint': float(room_calc.paint_walls or 0.0),
            'ceiling_paint': float(room_calc.paint_ceiling or 0.0),
            'total_paint': float(room_calc.paint_total or 0.0)
        }

    def _update_room_metrics_ui(self, m):
        """Update metrics labels if the Live Metrics panel exists."""
        if not hasattr(self, 'metrics_labels') or not self.metrics_labels:
            return
        def fmt(v):
            try:
                return f"{float(v):.2f}"
            except Exception:
                return "-"
        
        # Safe update - only update keys that exist in the UI
        if 'walls_gross' in self.metrics_labels:
            self.metrics_labels['walls_gross']['text'] = fmt(m.get('walls_gross', 0))
        if 'openings' in self.metrics_labels:
            self.metrics_labels['openings']['text'] = fmt(m.get('openings_total', 0))
        if 'walls_net' in self.metrics_labels:
            self.metrics_labels['walls_net']['text'] = fmt(m.get('walls_net', 0))
        if 'plaster' in self.metrics_labels:
            self.metrics_labels['plaster']['text'] = fmt(m.get('plaster', 0))
        if 'cer_wall' in self.metrics_labels:
            self.metrics_labels['cer_wall']['text'] = fmt(m.get('cer_wall', 0))
        if 'cer_floor' in self.metrics_labels:
            self.metrics_labels['cer_floor']['text'] = fmt(m.get('cer_floor', 0))
        if 'cer_ceiling' in self.metrics_labels:
            self.metrics_labels['cer_ceiling']['text'] = fmt(m.get('cer_ceiling', 0))
        if 'paint_walls' in self.metrics_labels:
            self.metrics_labels['paint_walls']['text'] = fmt(m.get('walls_paint', 0))
        if 'paint_ceiling' in self.metrics_labels:
            self.metrics_labels['paint_ceiling']['text'] = fmt(m.get('ceiling_paint', 0))
        if 'paint_total' in self.metrics_labels:
            self.metrics_labels['paint_total']['text'] = fmt(m.get('total_paint', 0))

    def _recalculate_room_ceramic_with_openings(self, room):
        """Reactively recalculate wall ceramic by deducting overlapping doors/windows.
        
        Refactored to use RoomAdapter and OpeningAdapter for cleaner access.
        """
        if not room:
            return
        
        room_adapted = RoomAdapter(room)
        room_name = room_adapted.name
        
        # Find ceramic zones for this room
        room_zones = []
        for z in self.app.project.ceramic_zones:
            if isinstance(z, dict):
                z_name = z.get('name', '')
                z_room = z.get('room_name', '')
            else:
                z_name = getattr(z, 'name', '')
                z_room = getattr(z, 'room_name', '')
            
            # Prefer exact room_name match; fall back to name substring only if room_name is missing.
            if z_room and str(z_room) == str(room_name):
                room_zones.append(z)
            elif not z_room and room_name and room_name in (z_name or ''):
                room_zones.append(z)
        
        if not room_zones:
            return  # No ceramic to adjust
        
        room_openings = self.app.get_room_opening_summary(room)
        
        total_wall_ceramic = 0.0
        total_floor_ceramic = 0.0
        total_ceiling_ceramic = 0.0
        
        for zone in room_zones:
            if isinstance(zone, dict):
                surface = zone.get('surface_type', 'wall')
                perimeter = float(zone.get('perimeter', 0.0) or 0.0)
                height = float(zone.get('height', 0.0) or 0.0)
                ceramic_start = float(zone.get('start_height', 0.0) or 0.0)
                area = float(zone.get('area', 0.0) or 0.0)
                effective_area = float(zone.get('effective_area', 0.0) or 0.0)
            else:
                surface = getattr(zone, 'surface_type', 'wall')
                perimeter = float(getattr(zone, 'perimeter', 0.0) or 0.0)
                height = float(getattr(zone, 'height', 0.0) or 0.0)
                ceramic_start = float(getattr(zone, 'start_height', 0.0) or 0.0)
                area = getattr(zone, 'area', 0.0)
                effective_area = getattr(zone, 'effective_area', 0.0)

            if surface == 'floor':
                # Use effective area if set (e.g. manual entry), else calculated area
                val = (effective_area or 0.0) if effective_area and effective_area > 0 else area
                if val == 0 and perimeter > 0 and height > 0:
                    val = perimeter * height # Fallback
                total_floor_ceramic += val
                continue
            elif surface == 'ceiling':
                val = (effective_area or 0.0) if effective_area and effective_area > 0 else area
                if val == 0 and perimeter > 0 and height > 0:
                    val = perimeter * height
                total_ceiling_ceramic += val
                continue
            
            # Wall calculation with deductions
            ceramic_end = ceramic_start + height
            base_area = perimeter * height
            
            deductions = 0.0
            
            # Deduct doors - Multiply by quantity in room
            for door_id in room_openings.get('door_ids', []):
                for d in self.app.project.doors:
                    if self.app._opening_name(d) == door_id:
                        door_adapted = OpeningAdapter(d)
                        d_height = door_adapted.height
                        d_width = door_adapted.width
                        d_placement = door_adapted.placement_height
                        d_top = d_placement + d_height
                        
                        # Get quantity in this room
                        room_qtys = d.get('room_quantities', {}) if isinstance(d, dict) else getattr(d, 'room_quantities', {}) or {}
                        qty = int(room_qtys.get(room_name, 1))
                        
                        # Calculate overlap
                        overlap_start = max(ceramic_start, d_placement)
                        overlap_end = min(ceramic_end, d_top)
                        if overlap_end > overlap_start:
                            overlap_height = overlap_end - overlap_start
                            # Deduct ALL instances in room
                            deductions += float(d_width * overlap_height * qty)
                        break
            
            # Deduct windows - Multiply by quantity in room
            for win_id in room_openings.get('window_ids', []):
                for w in self.app.project.windows:
                    if self.app._opening_name(w) == win_id:
                        win_adapted = OpeningAdapter(w)
                        w_height = win_adapted.height
                        w_width = win_adapted.width
                        w_placement = win_adapted.placement_height
                        w_top = w_placement + w_height
                        
                        # Get quantity in this room
                        room_qtys = w.get('room_quantities', {}) if isinstance(w, dict) else getattr(w, 'room_quantities', {}) or {}
                        qty = int(room_qtys.get(room_name, 1))
                        
                        # Calculate overlap
                        overlap_start = max(ceramic_start, w_placement)
                        overlap_end = min(ceramic_end, w_top)
                        if overlap_end > overlap_start:
                            overlap_height = overlap_end - overlap_start
                            # Deduct ALL instances in room
                            deductions += float(w_width * overlap_height * qty)
                        break
            
            # Update zone's effective area (don't modify perimeter/height)
            net_area = max(0.0, base_area - deductions)
            if isinstance(zone, dict):
                zone['effective_area'] = net_area
            else:
                zone.effective_area = net_area
            total_wall_ceramic += net_area
        
        # Update room's ceramic_breakdown with new totals
        breakdown = room_adapted.ceramic_breakdown.copy() if room_adapted.ceramic_breakdown else {}
        partial_from_walls = float(breakdown.get('wall_partial', 0.0) or 0.0)
        breakdown['wall_zones'] = total_wall_ceramic
        breakdown['wall'] = total_wall_ceramic + partial_from_walls
        breakdown['floor'] = total_floor_ceramic
        breakdown['ceiling'] = total_ceiling_ceramic
        
        room_adapted.ceramic_breakdown = breakdown
        total_ceramic = self._ceramic_breakdown_total(breakdown)
        
        # Set back to original object
        if isinstance(room, dict):
            room['ceramic_breakdown'] = breakdown
            room['ceramic_area'] = total_ceramic
        else:
            room.ceramic_breakdown = breakdown
            room.ceramic_area = total_ceramic

    # === Bulk Assignment & Ceramic Methods ===

    def _bulk_assign_openings(self, opening_type: str):
        """Show dialog to assign one opening to multiple rooms."""
        # Choose source list
        source = self.app.project.doors if opening_type == 'DOOR' else self.app.project.windows
        if not source:
            messagebox.showinfo("No Openings", f"No {opening_type.lower()}s available to assign.")
            return
        if not self.app.project.rooms:
            messagebox.showinfo("No Rooms", "No rooms available.")
            return

        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Bulk Assign {opening_type.title()}s")
        dialog.configure(bg=self.app.colors['bg_secondary'])
        dialog.transient(self.frame)
        dialog.grab_set()

        container = ttk.Frame(dialog, padding=(14,10), style='Main.TFrame')
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Select Opening:", foreground=self.app.colors['text_secondary']).grid(row=0, column=0, sticky='w')
        opening_names = [self.app._opening_name(o) for o in source]
        opening_var = tk.StringVar(value=opening_names[0])
        ttk.Combobox(container, textvariable=opening_var, values=opening_names, state='readonly', width=18).grid(row=0, column=1, sticky='w')

        ttk.Label(container, text="Assign to Rooms:", foreground=self.app.colors['text_secondary']).grid(row=1, column=0, sticky='nw', pady=(8,0))
        rooms_frame = ttk.Frame(container, style='Main.TFrame')
        rooms_frame.grid(row=1, column=1, sticky='w', pady=(8,0))

        # Select All checkbox
        select_all_var = tk.BooleanVar(value=False)
        def toggle_all_rooms():
            state = select_all_var.get()
            for var, _ in room_vars:
                var.set(state)
        select_all_cb = ttk.Checkbutton(
            rooms_frame, 
            text="✓ Select All", 
            variable=select_all_var,
            command=toggle_all_rooms,
            style='Accent.TCheckbutton'
        )
        select_all_cb.grid(row=0, column=0, columnspan=3, sticky='w', padx=4, pady=(0,6))

        room_vars = []
        for idx, r in enumerate(self.app.project.rooms):
            var = tk.BooleanVar(value=False)
            room_vars.append((var, r))
            # Offset row by 1 because row 0 has Select All
            ttk.Checkbutton(rooms_frame, text=self.app._room_name(r), variable=var).grid(row=1+(idx//3), column=idx%3, sticky='w', padx=4, pady=2)

        mode_var = tk.StringVar(value='add')
        ttk.Label(container, text="Mode:", foreground=self.app.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=(10,0))
        ttk.Combobox(container, textvariable=mode_var, values=['add','set'], state='readonly', width=10).grid(row=2, column=1, sticky='w', pady=(10,0))

        def apply_assignment():
            opening_id = opening_var.get()
            selected_rooms = [self.app._room_name(r) for (v,r) in room_vars if v.get()]
            if not selected_rooms:
                messagebox.showwarning("No Rooms Selected", "Select at least one room.")
                return
            updated = self.app.association.assign_opening_to_rooms(opening_id, selected_rooms, mode=mode_var.get())
            
            # Recalculate ceramic for affected rooms (reactive deductions)
            for room in self.app.project.rooms:
                if self.app._room_name(room) in selected_rooms:
                    try:
                        # Auto-distribute openings to walls so they appear on drawing
                        self._auto_distribute_openings(room)
                        self._recalculate_room_ceramic_with_openings(room)
                    except Exception:
                        pass
            
            self.app.refresh_rooms()
            self._refresh_openings_trees()
            self.app.update_status(f"Assigned {opening_id} to {updated} room(s)", icon="✅")
            dialog.destroy()

        btns = ttk.Frame(container, style='Main.TFrame')
        btns.grid(row=3, column=0, columnspan=2, pady=(14,0))
        ttk.Button(btns, text="Apply", style='Accent.TButton', command=apply_assignment).pack(side=tk.LEFT, padx=(0,6))
        ttk.Button(btns, text="Cancel", style='Secondary.TButton', command=dialog.destroy).pack(side=tk.LEFT)

    def _bulk_assign_doors(self):
        self._bulk_assign_openings('DOOR')

    def _bulk_assign_windows(self):
        self._bulk_assign_openings('WINDOW')

    def _bulk_add_ceramic(self):
        """Open smart ceramic calculator dialog.
        
        Uses the new modular CeramicCalculatorDialog for better maintainability.
        """
        def on_complete():
            # Refresh views
            if hasattr(self.app, 'materials_tab') and hasattr(self.app.materials_tab, 'refresh_ceramic_zones'):
                self.app.materials_tab.refresh_ceramic_zones()
            if hasattr(self.app, 'finishes_tab'):
                self.app.refresh_finishes_tab()
            # Refresh current room
            if self.selected_room:
                self._load_room_details(self.selected_room)
                try:
                    self._recalculate_room_ceramic_with_openings(self.selected_room)
                    metrics = self._compute_room_finish_metrics(self.selected_room)
                    self._update_room_metrics_ui(metrics)
                except Exception:
                    pass
            self.refresh_rooms_list()
        
        show_ceramic_calculator(self.frame, self.app, on_complete)


    # === Action Methods ===
    # === Action Methods ===
    
    def _add_room(self):
        """Add a new room manually."""
        self.app.add_room_manual()
        self.refresh_rooms_list()
        
    def _duplicate_room(self):
        """Duplicate selected room."""
        if not self.selected_room:
            messagebox.showwarning("No Selection", "Please select a room to duplicate.")
            return
        
        # Create copy
        if isinstance(self.selected_room, dict):
            new_room = self.selected_room.copy()
            new_room['name'] = self.app._make_unique_name('ROOM', new_room.get('name', 'Room'))
        else:
            # Dataclass - use to_dict/from_dict
            room_dict = self.selected_room.to_dict()
            room_dict['name'] = self.app._make_unique_name('ROOM', room_dict.get('name', 'Room'))
            from bilind.models.room import Room
            new_room = Room.from_dict(room_dict)
        
        self.app.project.rooms.append(new_room)
        self.refresh_rooms_list()
        self.app.refresh_rooms()
        self.app.update_status(f"Duplicated room '{self.app._room_name(new_room)}'", icon="📋")
        
    def _delete_room(self):
        """Delete selected room."""
        if not self.selected_room:
            messagebox.showwarning("No Selection", "Please select a room to delete.")
            return
        
        room_name = self.app._room_name(self.selected_room)
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete room '{room_name}'?\n\nThis will also remove all assigned openings and finishes."
        )
        
        if confirm:
            self.app.project.rooms.remove(self.selected_room)
            self.selected_room = None
            self.refresh_rooms_list()
            self.app.refresh_rooms()
            self._show_no_selection_message()
            self.app.update_status(f"Deleted room '{room_name}'", icon="🗑️")
            
    def _save_room_properties(self):
        """Save edited room properties."""
        if not self.selected_room:
            return
        
        try:
            # Read values
            name = self.room_name_var.get().strip()
            layer = self.room_layer_var.get().strip()
            w = float(self.room_width_var.get() or 0)
            l = float(self.room_length_var.get() or 0)
            wall_h = float(self.room_wall_height_var.get() or 0) if self.room_wall_height_var.get() else None
            has_balcony = self.room_has_balcony_var.get()
            
            if w <= 0 or l <= 0:
                messagebox.showerror("Invalid Input", "Width and length must be positive values.")
                return
            
            # Calculate perimeter and area
            perim = 2 * (w + l)
            area = w * l
            
            # Balcony segments
            balcony_segs = []
            if has_balcony:
                for var in self.balcony_seg_vars:
                    try:
                        balcony_segs.append(float(var.get() or 0))
                    except:
                        balcony_segs.append(0.0)
            
            # Update room
            if isinstance(self.selected_room, dict):
                self.selected_room['name'] = name
                self.selected_room['layer'] = layer
                self.selected_room['w'] = w
                self.selected_room['l'] = l
                self.selected_room['perim'] = perim
                self.selected_room['area'] = area
                self.selected_room['wall_height'] = wall_h
                self.selected_room['has_balcony'] = has_balcony
                self.selected_room['balcony_segments'] = balcony_segs
            else:
                self.selected_room.name = name
                self.selected_room.layer = layer
                self.selected_room.width = w
                self.selected_room.length = l
                self.selected_room.perimeter = perim
                self.selected_room.area = area
                self.selected_room.wall_height = wall_h
                self.selected_room.has_balcony = has_balcony
                self.selected_room.balcony_segments = balcony_segs
            
            # Update display
            self.room_perim_var.set(f"{perim:.2f}")
            self.room_area_var.set(f"{area:.2f}")
            
            # Recalculate finishes (plaster/paint depend on wall_height)
            self._recalculate_room_ceramic_with_openings(self.selected_room)
            if hasattr(self.selected_room, 'update_finish_areas'):
                all_openings = list(self.app.project.doors) + list(self.app.project.windows)
                self.selected_room.update_finish_areas(all_openings)

            # Refresh live metrics to reflect new wall height on plaster/paint
            metrics = self._compute_room_finish_metrics(self.selected_room)
            self._update_room_metrics_ui(metrics)
            
            self.refresh_rooms_list()
            self.app.refresh_rooms()
            self.app.update_status(f"Saved room '{name}' - recalculated finishes", icon="💾")
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please enter valid numeric values.\n\n{e}")

    def _add_balcony_ceramic_for_room(self):
        """Generate ceramic zones for balcony using advanced dialog with per-wall control."""
        if not self.selected_room:
            messagebox.showwarning("No Room", "Select a balcony room first.")
            return
        
        # Check if it's a balcony
        has_balcony = False
        if isinstance(self.selected_room, dict):
            has_balcony = bool(self.selected_room.get('is_balcony', False))
        else:
            has_balcony = bool(getattr(self.selected_room, 'is_balcony', False))
        
        if not has_balcony:
            messagebox.showinfo("ليس بلكون", "هذه الغرفة غير مُعدَّة كبلكون.\n\nيرجى تعديل الغرفة وتفعيل خيار 'بلكون/شرفة' مع تحديد جدران البلكون.")
            return
        
        # Show advanced balcony ceramic dialog
        from bilind.ui.dialogs.balcony_ceramic_dialog import BalconyCeramicDialog
        
        dialog = BalconyCeramicDialog(self.frame, self.app, self.selected_room)
        result = dialog.show()
        
        if result:
            # Refresh UI
            if hasattr(self.app, 'materials_tab') and hasattr(self.app.materials_tab, 'refresh_ceramic_zones'):
                self.app.materials_tab.refresh_ceramic_zones()
            if hasattr(self.app, 'finishes_tab'):
                self.app.refresh_finishes_tab()
            self._load_room_details(self.selected_room)
            
            # Recalculate metrics
            try:
                self._recalculate_room_ceramic_with_openings(self.selected_room)
                metrics = self._compute_room_finish_metrics(self.selected_room)
                self._update_room_metrics_ui(metrics)
            except Exception:
                pass
            
            self.refresh_rooms_list()
            self.app.update_status(f"✅ Balcony ceramic added: {result['area']:.2f} m² ({result['zones']} wall(s))", icon="🧱")
            
    def _add_opening(self, opening_type: str):
        """Add door/window to current room."""
        if not self.selected_room:
            messagebox.showwarning("No Selection", "Please select a room first.")
            return
        
        # Call main app's add dialog with room assignment
        self.app.add_opening_manual(opening_type, assign_to_room=self.app._room_name(self.selected_room))
        
        # Auto-distribute to walls
        self._auto_distribute_openings(self.selected_room)
        
        self._refresh_openings_trees()
    
    def _quick_add_opening(self, opening_type: str, template_name: str):
        """Quick-add opening from template without showing dialog."""
        if not self.selected_room:
            messagebox.showwarning("No Selection", "Please select a room first to add opening.")
            return
        
        room_name = self.app._room_name(self.selected_room)
        
        # Check if this is an existing opening (marked with 📋 prefix)
        if template_name.startswith('📋 '):
            # Link existing opening instead of creating duplicate
            existing_name = template_name.replace('📋 ', '')
            storage = self.app.doors if opening_type == 'DOOR' else self.app.windows
            existing = next((o for o in storage if self.app._get_opening_name(o) == existing_name), None)
            if existing:
                # Ask for quantity for this room
                qty = self._ask_room_quantity(opening_type, existing_name, room_name)
                if qty is None:
                    return  # Cancelled
                
                # Use association manager to link
                self.app.association_manager.assign_opening_to_rooms(existing, [room_name])
                
                # Set room_quantities
                if isinstance(existing, dict):
                    if 'room_quantities' not in existing:
                        existing['room_quantities'] = {}
                    existing['room_quantities'][room_name] = qty
                else:
                    if not hasattr(existing, 'room_quantities') or existing.room_quantities is None:
                        existing.room_quantities = {}
                    existing.room_quantities[room_name] = qty
                
                # Auto-distribute to walls
                self._auto_distribute_openings(self.selected_room)
                
                self._refresh_openings_trees()
                self.refresh_rooms_list()
                self.app.refresh_openings()
                self.app.update_status(f"✅ تم ربط {qty} {existing_name} بـ {room_name}", "🔗")
            return
        
        # Get templates
        templates = self.app.get_opening_templates(opening_type)
        
        # Find matching template
        template = None
        for tmpl in templates:
            if tmpl['name'] == template_name:
                template = tmpl
                break
        
        if not template:
            messagebox.showerror("Template Not Found", f"Could not find template '{template_name}'")
            return
        
        # Ask for quantity for this room
        qty = self._ask_room_quantity(opening_type, template_name, room_name)
        if qty is None:
            return  # Cancelled
        
        # Create opening record directly
        storage = self.app._opening_storage(opening_type)
        prefix = 'D' if opening_type == 'DOOR' else 'W'
        name = self.app._make_unique_name(opening_type, f"{prefix}{len(storage)+1}")
        
        # _build_opening_record signature:
        # (opening_type, name, type_label, width, height, qty, weight, layer, placement_height)
        new_record = self.app._build_opening_record(
            opening_type,
            name,
            template['type'],
            template['width'],
            template['height'],
            qty,  # Total qty in project
            template.get('weight', 0),
            'Door' if opening_type == 'DOOR' else 'Window',
            template['placement_height']
        )
        
        # Assign to current room with room_quantities
        if isinstance(new_record, dict):
            new_record['assigned_rooms'] = [room_name]
            new_record['room_quantities'] = {room_name: qty}
        else:
            new_record.assigned_rooms = [room_name]
            new_record.room_quantities = {room_name: qty}
        
        storage.append(new_record)
        
        # Auto-distribute to walls
        self._auto_distribute_openings(self.selected_room)
        
        # Update UI
        self._refresh_openings_trees()
        self.refresh_rooms_list()
        self.app.refresh_openings()
        icon = "🚪" if opening_type == 'DOOR' else "🪟"
        self.app.update_status(f"✅ تمت إضافة {qty} × {template_name} إلى '{room_name}'", icon=icon)
    
    def _ask_room_quantity(self, opening_type: str, opening_name: str, room_name: str) -> Optional[int]:
        """Ask user for quantity of opening for this specific room."""
        from tkinter import simpledialog
        
        type_label = "باب" if opening_type == 'DOOR' else "شباك"
        
        try:
            result = simpledialog.askinteger(
                f"العدد لـ {room_name}",
                f"كم {type_label} '{opening_name}' في غرفة '{room_name}'؟",
                initialvalue=1,
                minvalue=1,
                maxvalue=50,
                parent=self.app.root  # Use main app root window
            )
            return result
        except Exception as e:
            # Fallback: return 1 if dialog fails
            print(f"Dialog error: {e}")
            return 1
        
    def _edit_opening(self, opening_type: str):
        """Edit selected opening directly with inline dialog."""
        tree = self.doors_tree if opening_type == 'DOOR' else self.windows_tree
        selection = tree.selection()
        
        if not selection:
            messagebox.showwarning("لا يوجد اختيار", f"اختر {'باب' if opening_type == 'DOOR' else 'نافذة'} للتعديل")
            return
        
        # Get opening name from selection
        item_values = tree.item(selection[0], 'values')
        opening_name = item_values[0]
        
        # Find opening in storage
        storage = self.app.project.doors if opening_type == 'DOOR' else self.app.project.windows
        opening_idx = None
        opening_obj = None
        
        for idx, opening in enumerate(storage):
            if self.app._opening_name(opening) == opening_name:
                opening_idx = idx
                opening_obj = opening
                break
        
        if opening_obj is None:
            messagebox.showerror("خطأ", f"لم يتم العثور على {'الباب' if opening_type == 'DOOR' else 'النافذة'}")
            return
        
        # Get current values
        opening_dict = self.app._opening_to_dict(opening_obj)
        type_catalog = self.app.door_types if opening_type == 'DOOR' else self.app.window_types
        
        # Room context (may be absent if user is editing openings as project-level data)
        room_name = self.app._room_name(self.selected_room) if self.selected_room else ''
        has_room_context = bool(room_name)

        # Quantity: room-specific when room selected; otherwise project total
        room_qtys = opening_dict.get('room_quantities', {}) or {}
        if has_room_context:
            room_qty = room_qtys.get(room_name, 1)
        else:
            room_qty = int(opening_dict.get('quantity', opening_dict.get('qty', 1)) or 1)
        
        # Create edit dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"✏️ تعديل {'الباب' if opening_type == 'DOOR' else 'النافذة'}: {opening_name}")
        dialog.configure(bg=self.app.colors['bg_secondary'])
        dialog.resizable(False, False)
        dialog.transient(self.frame)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=(18, 14), style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Variables
        name_var = tk.StringVar(value=opening_dict.get('name', ''))
        layer_var = tk.StringVar(value=opening_dict.get('layer', ''))
        type_var = tk.StringVar(value=opening_dict.get('type', list(type_catalog.keys())[0] if type_catalog else ''))
        width_var = tk.StringVar(value=str(opening_dict.get('w', opening_dict.get('width', 0.0))))
        height_var = tk.StringVar(value=str(opening_dict.get('h', opening_dict.get('height', 0.0))))
        room_qty_var = tk.StringVar(value=str(room_qty))  # Room-specific quantity
        placement_height = opening_dict.get('placement_height', 1.0 if opening_type == 'WINDOW' else 0.0)
        placement_var = tk.StringVar(value=str(placement_height))
        weight_each = opening_dict.get('weight_each', opening_dict.get('weight', 0.0))
        weight_var = tk.StringVar(value=str(weight_each)) if opening_type == 'DOOR' else None
        
        # Form fields
        row = 0
        ttk.Label(frame, text="الاسم:", foreground=self.app.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=name_var, width=22).grid(row=row, column=1, sticky='w', pady=6)
        
        row += 1
        ttk.Label(frame, text="الطبقة:", foreground=self.app.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=layer_var, width=22).grid(row=row, column=1, sticky='w', pady=6)
        
        row += 1
        ttk.Label(frame, text="النوع:", foreground=self.app.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        type_combo = ttk.Combobox(frame, textvariable=type_var, values=list(type_catalog.keys()), state='readonly', width=20)
        type_combo.grid(row=row, column=1, sticky='w', pady=6)
        
        row += 1
        ttk.Label(frame, text="العرض (م):", foreground=self.app.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=width_var, width=12).grid(row=row, column=1, sticky='w', pady=6)
        
        row += 1
        ttk.Label(frame, text="الارتفاع (م):", foreground=self.app.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=height_var, width=12).grid(row=row, column=1, sticky='w', pady=6)
        
        row += 1
        qty_label = "الكمية (في هذه الغرفة):" if has_room_context else "الكمية (إجمالي المشروع):"
        ttk.Label(frame, text=qty_label, foreground=self.app.colors['accent'], font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=room_qty_var, width=12).grid(row=row, column=1, sticky='w', pady=6)
        
        row += 1
        ttk.Label(frame, text="الارتفاع من الأرض (م):", foreground=self.app.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=placement_var, width=12).grid(row=row, column=1, sticky='w', pady=6)
        
        if opening_type == 'DOOR' and weight_var is not None:
            row += 1
            ttk.Label(frame, text="الوزن (كجم):", foreground=self.app.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
            ttk.Entry(frame, textvariable=weight_var, width=12).grid(row=row, column=1, sticky='w', pady=6)
        
        # Preview
        row += 1
        preview_var = tk.StringVar(value="")
        preview_label = ttk.Label(frame, textvariable=preview_var, foreground=self.app.colors['accent'], font=('Segoe UI', 9, 'italic'))
        preview_label.grid(row=row, column=0, columnspan=2, sticky='w', pady=(10, 4))
        
        def update_preview(*_):
            try:
                w = float(width_var.get())
                h = float(height_var.get())
                qty = max(1, int(room_qty_var.get()))
                area_total = w * h * qty
                if has_room_context:
                    preview_var.set(f"📐 المساحة في هذه الغرفة: {area_total:.2f} م²")
                else:
                    preview_var.set(f"📐 المساحة الإجمالية: {area_total:.2f} م²")
            except Exception:
                preview_var.set("")
        
        for var in (width_var, height_var, room_qty_var):
            var.trace_add('write', update_preview)
        update_preview()
        
        def save():
            try:
                name = name_var.get().strip() or opening_dict.get('name', '')
                layer = layer_var.get().strip() or opening_dict.get('layer', '')
                width = float(width_var.get())
                height = float(height_var.get())
                new_qty = max(1, int(room_qty_var.get()))
                placement = float(placement_var.get())
                
                if width <= 0 or height <= 0:
                    raise ValueError("العرض والارتفاع يجب أن يكونا أكبر من صفر")
                if placement < 0:
                    raise ValueError("الارتفاع من الأرض لا يمكن أن يكون سالباً")
                
                weight = float(weight_var.get()) if weight_var is not None else 0.0
                
                # Check unique name
                existing_names = {self.app._opening_name(o) for i, o in enumerate(storage) if i != opening_idx}
                if name in existing_names:
                    name = self.app._make_unique_name(opening_type, name)
                
                # Calculate total qty
                existing_room_qtys = opening_dict.get('room_quantities', {}) or {}
                if has_room_context:
                    existing_room_qtys[room_name] = new_qty  # Update this room's qty
                    total_qty = sum(existing_room_qtys.values()) if existing_room_qtys else new_qty
                else:
                    # Project-level edit: do not touch per-room quantities
                    total_qty = new_qty
                
                # Build new record with total qty
                new_record = self.app._build_opening_record(
                    opening_type, name, type_var.get(), width, height, total_qty, weight,
                    layer=layer, placement_height=placement
                )
                
                # Preserve assigned_rooms and room_quantities
                if isinstance(opening_obj, dict):
                    assigned = opening_obj.get('assigned_rooms', [])
                else:
                    assigned = getattr(opening_obj, 'assigned_rooms', [])
                
                if isinstance(new_record, dict):
                    new_record['assigned_rooms'] = assigned
                    # Store per-room quantities only when we have room context (avoid '' key confusion)
                    if has_room_context:
                        new_record['room_quantities'] = existing_room_qtys
                else:
                    new_record.assigned_rooms = assigned
                    if has_room_context:
                        new_record.room_quantities = existing_room_qtys
                
                # Update storage
                storage[opening_idx] = new_record
                
                # Re-distribute openings to walls based on new quantities (room context only)
                if self.selected_room is not None:
                    self._auto_distribute_openings(self.selected_room)
                
                # Recalculate wall deductions for all walls (room context only)
                if self.selected_room is not None:
                    if isinstance(self.selected_room, dict):
                        walls = self.selected_room.get('walls', []) or []
                    else:
                        walls = getattr(self.selected_room, 'walls', []) or []

                    all_openings = list(self.app.project.doors) + list(self.app.project.windows)
                    for wall_data in walls:
                        if isinstance(wall_data, dict):
                            from bilind.models.wall import Wall
                            wall_obj = Wall.from_dict(wall_data)
                            wall_obj.recalculate_deductions(all_openings)
                            wall_data['deduct'] = wall_obj.deduction_area
                            wall_data['net'] = wall_obj.net_area
                            wall_data['net_area'] = wall_obj.net_area
                            wall_data['ceramic_area'] = wall_obj.ceramic_area
                        else:
                            wall_data.recalculate_deductions(all_openings)
                
                # Refresh displays including walls tree and visuals
                self.app.refresh_openings()
                self._refresh_openings_trees()
                if self.selected_room is not None:
                    self._refresh_walls_tree()  # Refresh walls to show updated openings
                    self._render_room_visuals(self.selected_room)  # Update the drawing
                    self.refresh_rooms_list()  # Update the rooms list to reflect qty changes
                
                dialog.destroy()
                icon = "🚪" if opening_type == 'DOOR' else "🪟"
                if has_room_context:
                    self.app.update_status(
                        f"✅ تم تحديث {'الباب' if opening_type == 'DOOR' else 'النافذة'} '{name}' (الكمية في {room_name}: {new_qty})",
                        icon=icon,
                    )
                else:
                    self.app.update_status(
                        f"✅ تم تحديث {'الباب' if opening_type == 'DOOR' else 'النافذة'} '{name}' (الكمية الإجمالية: {new_qty})",
                        icon=icon,
                    )
                
            except ValueError as exc:
                messagebox.showerror("خطأ", f"خطأ: {exc}")
            except Exception as e:
                messagebox.showerror("خطأ", f"أدخل قيم رقمية صحيحة للعرض والارتفاع والعدد.\n{e}")
        
        # Buttons
        row += 1
        btn_frame = ttk.Frame(frame, style='Main.TFrame')
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(12, 0))
        
        ttk.Button(btn_frame, text="💾 حفظ", command=save, style='Accent.TButton', width=12).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="❌ إلغاء", command=dialog.destroy, style='Secondary.TButton', width=12).pack(side=tk.LEFT)
                
    def _remove_opening(self, opening_type: str):
        """Remove opening from current room (unassign)."""
        tree = self.doors_tree if opening_type == 'DOOR' else self.windows_tree
        selection = tree.selection()
        
        if not selection:
            messagebox.showwarning("No Selection", f"Please select a {opening_type.lower()} to remove.")
            return
        
        item_values = tree.item(selection[0], 'values')
        opening_name = item_values[0]
        
        confirm = messagebox.askyesno(
            "Confirm Removal",
            f"Remove {opening_type.lower()} '{opening_name}' from this room?\n\n(The opening will remain in the project)"
        )
        
        if confirm:
            # Unassign from room
            room_name = self.app._room_name(self.selected_room)
            storage = self.app.project.doors if opening_type == 'DOOR' else self.app.project.windows
            
            for opening in storage:
                if self.app._opening_name(opening) == opening_name:
                    if isinstance(opening, dict):
                        assigned = opening.get('assigned_rooms', [])
                        if room_name in assigned:
                            assigned.remove(room_name)
                    else:
                        if room_name in opening.assigned_rooms:
                            opening.assigned_rooms.remove(room_name)
                    break
            
            # Also remove from room's opening_ids list
            if isinstance(self.selected_room, dict):
                opening_ids = self.selected_room.get('opening_ids', [])
                if opening_name in opening_ids:
                    opening_ids.remove(opening_name)
                    self.selected_room['opening_ids'] = opening_ids
            else:
                opening_ids = getattr(self.selected_room, 'opening_ids', []) or []
                if opening_name in opening_ids:
                    opening_ids.remove(opening_name)
                    self.selected_room.opening_ids = opening_ids
            
            # Recalculate room's opening_total_area using association
            if hasattr(self.app, 'association') and self.app.association:
                new_area = self.app.association.calculate_room_opening_area(self.selected_room)
                if isinstance(self.selected_room, dict):
                    self.selected_room['opening_total_area'] = new_area
                else:
                    self.selected_room.opening_total_area = new_area
            
            # Remove from any walls in the room
            if isinstance(self.selected_room, dict):
                walls = self.selected_room.get('walls', [])
            else:
                walls = getattr(self.selected_room, 'walls', []) or []
                
            for wall in walls:
                assigned = []
                if isinstance(wall, dict):
                    assigned = wall.get('assigned_openings', [])
                    # Also check opening_ids
                    wall_opening_ids = wall.get('opening_ids', [])
                    if opening_name in wall_opening_ids:
                        wall_opening_ids.remove(opening_name)
                        wall['opening_ids'] = wall_opening_ids
                else:
                    assigned = getattr(wall, 'assigned_openings', [])
                    wall_opening_ids = getattr(wall, 'opening_ids', []) or []
                    if opening_name in wall_opening_ids:
                        wall_opening_ids.remove(opening_name)
                        wall.opening_ids = wall_opening_ids
                
                if opening_name in assigned:
                    assigned.remove(opening_name)
                    # Trigger recalculation for this wall
                    all_openings = list(self.app.project.doors) + list(self.app.project.windows)
                    if isinstance(wall, dict):
                        from bilind.models.wall import Wall
                        w_obj = Wall.from_dict(wall)
                        w_obj.recalculate_deductions(all_openings)
                        wall['deduct'] = w_obj.deduction_area
                        wall['net'] = w_obj.net_area
                        wall['net_area'] = w_obj.net_area
                    else:
                        wall.recalculate_deductions(all_openings)

            self._refresh_openings_trees()
            self.app.refresh_openings()
            # Also refresh rooms tab to update opening counts
            if hasattr(self.app, 'rooms_tab'):
                self.app.rooms_tab.refresh_data()
            self.app.update_status(f"Removed {opening_type.lower()} '{opening_name}' from room", icon="🗑️")

    def _show_ceramic_details(self):
        """Show detailed breakdown of ceramic areas."""
        if not self.selected_room:
            return

        room = self.selected_room
        room_name = room.get('name', '') if isinstance(room, dict) else getattr(room, 'name', '')

        # SSOT: Always compute using UnifiedCalculator so it matches Excel/Quantities.
        try:
            from ...calculations.unified_calculator import UnifiedCalculator
            calc = UnifiedCalculator(self.app.project)
            cer = (calc.calculate_ceramic_by_room() or {}).get(room_name, {})
            breakdown = {
                'wall': float(cer.get('wall', 0.0) or 0.0),
                'ceiling': float(cer.get('ceiling', 0.0) or 0.0),
                'floor': float(cer.get('floor', 0.0) or 0.0),
            }
            total = breakdown['wall'] + breakdown['ceiling'] + breakdown['floor']
        except Exception:
            # Fallback to stored values if calculator fails for any reason.
            if isinstance(room, dict):
                breakdown = room.get('ceramic_breakdown', {})
                total = room.get('ceramic_area', 0.0)
            else:
                breakdown = getattr(room, 'ceramic_breakdown', {})
                total = getattr(room, 'ceramic_area', 0.0)

        if not breakdown and float(total or 0.0) == 0:
            messagebox.showinfo("تفاصيل السيراميك", "لا يوجد سيراميك في هذه الغرفة.")
            return

        msg = f"إجمالي السيراميك: {float(total or 0.0):.2f} م²\n\n"
        msg += "التفاصيل:\n"
        
        translations = {
            'wall': 'جدران',
            'ceiling': 'سقف',
            'floor': 'أرضية',
            'skirting': 'وزرات'
        }

        for k, v in breakdown.items():
            if k.endswith('_partial') or k.endswith('_zones'):
                continue
            label = translations.get(k, k)
            try:
                msg += f"- {label}: {float(v or 0.0):.2f} م²\n"
            except (TypeError, ValueError):
                continue

        messagebox.showinfo("تفاصيل السيراميك", msg)

    # ═══════════════════════════════════════════════════════════════════
    # NEW AUTO-ADD METHODS
    # ═══════════════════════════════════════════════════════════════════
    
    def _auto_add_plaster_all_walls(self):
        """Add plaster to all walls in all rooms."""
        if not self.app.project.rooms:
            messagebox.showinfo("لا توجد غرف", "أضف غرف أولاً")
            return
        
        total_plaster = 0.0
        rooms_processed = 0
        
        for room in self.app.project.rooms:
            perim = float(self.app._room_attr(room, 'perim', 'perimeter', 0.0) or 0.0)
            wall_h = float(self.app._room_attr(room, 'wall_height', 'wall_height', 0.0) or 0.0)
            area = float(self.app._room_attr(room, 'area', 'area', 0.0) or 0.0)
            
            if wall_h <= 0:
                continue
            
            # Walls plaster = perimeter × wall_height
            walls_plaster = perim * wall_h
            # Ceiling plaster = room area  
            ceiling_plaster = area
            room_total = walls_plaster + ceiling_plaster
            
            # Update room's plaster_area
            if isinstance(room, dict):
                room['plaster_area'] = room_total
            else:
                room.plaster_area = room_total
            
            total_plaster += room_total
            rooms_processed += 1
        
        # Refresh UI
        self.app.refresh_rooms()
        if self.selected_room:
            self._load_room_details(self.selected_room)
        
        self.app.update_status(f"✅ تمت إضافة اللياسة لـ {rooms_processed} غرفة | الإجمالي: {total_plaster:.2f} م²", icon="🏗️")

    def _auto_add_ceramic_all_floors(self):
        """Add floor ceramic to all rooms."""
        if not self.app.project.rooms:
            messagebox.showinfo("لا توجد غرف", "أضف غرف أولاً")
            return
        
        from bilind.models.finish import CeramicZone
        
        # Delete existing floor ceramics first
        self.app.project.ceramic_zones = [
            z for z in self.app.project.ceramic_zones
            if (z.get('surface_type', '') if isinstance(z, dict) else getattr(z, 'surface_type', '')).lower() != 'floor'
        ]
        
        total_area = 0.0
        rooms_processed = 0
        
        for room in self.app.project.rooms:
            room_name = self.app._room_name(room)
            area = float(self.app._room_attr(room, 'area', 'area', 0.0) or 0.0)
            
            if area <= 0:
                continue
            
            # Create floor ceramic zone
            zone = CeramicZone.for_floor(
                area=area,
                room_name=room_name,
                name=f"أرضية - {room_name}"
            )
            self.app.project.ceramic_zones.append(zone)
            
            # Update room ceramic breakdown
            if isinstance(room, dict):
                room['ceramic_area'] = (room.get('ceramic_area', 0.0) or 0.0) + area
                breakdown = room.get('ceramic_breakdown', {}) or {}
                breakdown['floor'] = breakdown.get('floor', 0.0) + area
                room['ceramic_breakdown'] = breakdown
            else:
                room.ceramic_area = (getattr(room, 'ceramic_area', 0.0) or 0.0) + area
                breakdown = getattr(room, 'ceramic_breakdown', {}) or {}
                breakdown['floor'] = breakdown.get('floor', 0.0) + area
                room.ceramic_breakdown = breakdown
                
                # Recalculate finishes
                if hasattr(room, 'update_finish_areas'):
                    all_openings = list(self.app.project.doors) + list(self.app.project.windows)
                    room.update_finish_areas(all_openings)
            
            total_area += area
            rooms_processed += 1
        
        # Refresh UI
        self.app.refresh_rooms()
        if self.selected_room:
            self._load_room_details(self.selected_room)
        
        self.app.update_status(f"✅ تمت إضافة سيراميك الأرضيات لـ {rooms_processed} غرفة | الإجمالي: {total_area:.2f} م²", icon="🟫")

    def _auto_add_ceramic_walls_dialog(self):
        """Show advanced dialog to add ceramic to walls with per-wall control."""
        from bilind.ui.tabs.helpers.auto_presets import classify_room_type
        from bilind.models.finish import CeramicZone
        from bilind.ui.tabs.helpers import RoomAdapter
        
        if not self.app.project.rooms:
            messagebox.showinfo("لا توجد غرف", "أضف غرف أولاً")
            return
        
        # Create dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("🧱 إضافة سيراميك للجدران - متقدم")
        dialog.configure(bg=self.app.colors['bg_secondary'])
        dialog.transient(self.frame)
        dialog.grab_set()
        dialog.geometry("950x750")
        dialog.minsize(900, 700)
        
        # Main container
        main_frame = ttk.Frame(dialog, padding=12, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Frame(main_frame, style='Main.TFrame')
        header.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header,
            text="🧱 سيراميك الجدران - تحكم متقدم",
            font=('Segoe UI Semibold', 14),
            foreground=self.app.colors['accent']
        ).pack(anchor='w')
        
        ttk.Label(
            header,
            text="اختر الغرف والجدران وحدد ارتفاع السيراميك لكل جدار",
            foreground=self.app.colors['text_secondary']
        ).pack(anchor='w', pady=(4, 0))
        
        # Create paned window for room list and details
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=8)
        
        # Left panel - Room list
        left_frame = ttk.LabelFrame(paned, text="📋 الغرف", padding=8)
        paned.add(left_frame, weight=1)
        
        # Room type filter
        filter_frame = ttk.Frame(left_frame, style='Main.TFrame')
        filter_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(filter_frame, text="فلتر:").pack(side=tk.LEFT)
        filter_var = tk.StringVar(value="الكل")
        filter_combo = ttk.Combobox(filter_frame, textvariable=filter_var, width=15, state='readonly')
        filter_combo['values'] = ['الكل', 'مطبخ', 'حمام', 'تواليت', 'بلكون']
        filter_combo.pack(side=tk.LEFT, padx=4)
        
        # Rooms treeview
        # Use a stable unique iid per room object to avoid crashes when names repeat
        rooms_tree = ttk.Treeview(left_frame, columns=('type', 'area', 'walls'), height=15, show='tree headings')
        rooms_tree.heading('#0', text='الغرفة')
        rooms_tree.heading('type', text='النوع')
        rooms_tree.heading('area', text='المساحة')
        rooms_tree.heading('walls', text='جدران')
        rooms_tree.column('#0', width=160)
        rooms_tree.column('type', width=80)
        rooms_tree.column('area', width=60)
        rooms_tree.column('walls', width=50)
        
        rooms_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=rooms_tree.yview)
        rooms_tree.configure(yscrollcommand=rooms_scroll.set)
        rooms_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        rooms_tree.pack(fill=tk.BOTH, expand=True)
        
        # Room selection state
        # Keyed by stable room iid to avoid duplicate-name collisions
        room_selection = {}  # room_key -> {...}
        current_room_name = tk.StringVar(value="")  # stores room_key

        # Default selection should be scoped to the room the user opened the dialog from.
        selected_room_key = f"room-{id(self.selected_room)}" if getattr(self, 'selected_room', None) is not None else ""
        
        # Populate rooms
        def populate_rooms(filter_type='الكل'):
            rooms_tree.delete(*rooms_tree.get_children())
            name_counts = {}
            for room in self.app.project.rooms:
                room_key = f"room-{id(room)}"
                room_name = self.app._room_name(room)
                rtype = classify_room_type(room_name, room)
                adapter = RoomAdapter(room)
                
                # Map internal type to Arabic
                type_map = {'kitchen': 'مطبخ', 'bath': 'حمام', 'toilet': 'تواليت', 'balcony': 'بلكون', 'bedroom': 'غرفة نوم', 'living': 'صالة'}
                ar_type = type_map.get(rtype, 'أخرى')
                
                # Apply filter
                if filter_type != 'الكل' and ar_type != filter_type:
                    continue

                # Display name (disambiguate duplicates)
                name_counts[room_name] = name_counts.get(room_name, 0) + 1
                display_name = room_name if name_counts[room_name] == 1 else f"{room_name} ({name_counts[room_name]})"
                
                walls = adapter.walls
                wall_count = len(walls) if walls else 0
                
                # Initialize selection state
                if room_key not in room_selection:
                    # Default: select ONLY the current room to avoid applying to other rooms unintentionally.
                    default_selected = bool(selected_room_key and room_key == selected_room_key)
                    default_height = {'kitchen': 1.5, 'bath': 2.4, 'toilet': 1.5, 'balcony': 1.2}.get(rtype, 1.5)
                    room_selection[room_key] = {
                        'selected': default_selected,
                        'default_height': default_height,
                        'rtype': rtype,
                        'room': room,
                        'room_name': room_name,
                        'display_name': display_name,
                        'walls': []  # Will be populated when room is selected
                    }
                else:
                    # Keep display name updated when filter changes
                    room_selection[room_key]['display_name'] = display_name
                
                # Add to tree
                tags = ('selected',) if room_selection[room_key]['selected'] else ()
                rooms_tree.insert('', 'end', iid=room_key, text=display_name, values=(ar_type, f"{adapter.area:.1f}", wall_count), tags=tags)
        
        # Style for selected rooms
        rooms_tree.tag_configure('selected', background='#2d4a5e')
        
        populate_rooms()

        # Focus the current room to reduce accidental multi-room application
        if selected_room_key and selected_room_key in rooms_tree.get_children(''):
            try:
                rooms_tree.selection_set(selected_room_key)
                rooms_tree.see(selected_room_key)
                current_room_name.set(selected_room_key)
            except Exception:
                pass
        
        def on_filter_change(*_):
            populate_rooms(filter_var.get())
        filter_combo.bind('<<ComboboxSelected>>', on_filter_change)
        
        # Right panel - Wall details
        right_frame = ttk.LabelFrame(paned, text="🧱 تفاصيل الجدران", padding=8)
        paned.add(right_frame, weight=2)
        
        # Room header in right panel
        room_header = ttk.Frame(right_frame, style='Main.TFrame')
        room_header.pack(fill=tk.X, pady=(0, 8))
        
        room_name_label = ttk.Label(room_header, text="اختر غرفة من القائمة", font=('Segoe UI Semibold', 11))
        room_name_label.pack(anchor='w')
        
        room_info_label = ttk.Label(room_header, text="", foreground=self.app.colors['text_secondary'])
        room_info_label.pack(anchor='w')
        
        # Enable/disable room checkbox
        room_enabled_var = tk.BooleanVar(value=False)
        room_enabled_check = ttk.Checkbutton(
            room_header,
            text="✅ تفعيل سيراميك لهذه الغرفة",
            variable=room_enabled_var
        )
        room_enabled_check.pack(anchor='w', pady=(8, 0))
        
        # Quick height control
        quick_frame = ttk.Frame(right_frame, style='Main.TFrame')
        quick_frame.pack(fill=tk.X, pady=8)
        
        ttk.Label(quick_frame, text="ارتفاع موحد لكل الجدران:").pack(side=tk.LEFT)
        quick_height_var = tk.StringVar(value="1.5")
        quick_height_entry = ttk.Entry(quick_frame, textvariable=quick_height_var, width=8)
        quick_height_entry.pack(side=tk.LEFT, padx=4)
        ttk.Label(quick_frame, text="م").pack(side=tk.LEFT)
        
        def apply_quick_height():
            try:
                h = float(quick_height_var.get())
                # Apply to tracked height variables (widget tree-walking is unreliable due to nesting)
                for enabled_var, height_var, _wall in wall_controls:
                    if enabled_var.get():
                        height_var.set(str(h))
            except:
                pass
        
        ttk.Button(quick_frame, text="تطبيق على الكل", command=apply_quick_height, style='Secondary.TButton').pack(side=tk.LEFT, padx=8)
        
        # Walls scrollable area
        walls_frame = ttk.Frame(right_frame, style='Main.TFrame')
        walls_frame.pack(fill=tk.BOTH, expand=True)
        
        walls_canvas = tk.Canvas(walls_frame, bg=self.app.colors['bg_secondary'], highlightthickness=0)
        walls_scroll = ttk.Scrollbar(walls_frame, orient=tk.VERTICAL, command=walls_canvas.yview)
        walls_canvas.configure(yscrollcommand=walls_scroll.set)
        walls_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        walls_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        walls_canvas_inner = ttk.Frame(walls_canvas, style='Main.TFrame')
        walls_canvas.create_window((0, 0), window=walls_canvas_inner, anchor='nw')
        
        def update_walls_scroll(e=None):
            walls_canvas.configure(scrollregion=walls_canvas.bbox('all'))
        walls_canvas_inner.bind('<Configure>', update_walls_scroll)
        
        # Current wall controls storage
        wall_controls = []  # [(enabled_var, height_var, wall_obj), ...]
        
        # Helper to safely get wall attributes - defined at dialog level so apply() can use it
        def wall_attr(wall, attr, default=None):
            if isinstance(wall, dict):
                return wall.get(attr, default)
            return getattr(wall, attr, default)
        
        def load_room_walls(room_name):
            # Clear existing
            for child in walls_canvas_inner.winfo_children():
                child.destroy()
            wall_controls.clear()
            
            if not room_name or room_name not in room_selection:
                return
            
            room_data = room_selection[room_name]
            room = room_data['room']
            adapter = RoomAdapter(room)
            walls = adapter.walls or []
            
            room_name_label.configure(text=f"🏠 {room_data.get('display_name', room_data.get('room_name', room_name))}")
            room_info_label.configure(text=f"{adapter.room_type} | مساحة: {adapter.area:.2f} م² | محيط: {adapter.perimeter:.2f} م | {len(walls)} جدران")
            
            # Update room enabled checkbox
            room_enabled_var.set(room_data['selected'])
            quick_height_var.set(str(room_data['default_height']))
            
            if not walls:
                # Create default walls based on perimeter if no walls exist
                if adapter.perimeter > 0:
                    # Create 4 default walls for rectangular room or use perimeter
                    default_height = room_data['default_height']
                    if adapter.width > 0 and adapter.length > 0:
                        # Rectangular - 4 walls
                        from bilind.models.wall import Wall
                        walls = [
                            Wall(name="جدار 1", length=adapter.width, height=default_height),
                            Wall(name="جدار 2", length=adapter.length, height=default_height),
                            Wall(name="جدار 3", length=adapter.width, height=default_height),
                            Wall(name="جدار 4", length=adapter.length, height=default_height),
                        ]
                    else:
                        # Irregular - single wall with full perimeter
                        from bilind.models.wall import Wall
                        walls = [Wall(name="جميع الجدران", length=adapter.perimeter, height=default_height)]
                else:
                    ttk.Label(
                        walls_canvas_inner,
                        text="⚠️ لا يمكن إنشاء جدران\nالغرفة بدون محيط محدد",
                        foreground=self.app.colors['text_muted'],
                        justify='center'
                    ).pack(pady=20)
                    return
            
            # Create wall cards
            saved_walls = room_data.get('walls', []) or []

            for i, wall in enumerate(walls):
                wall_card = ttk.LabelFrame(
                    walls_canvas_inner,
                    text=f"جدار {i+1}",
                    padding=8
                )
                wall_card.pack(fill=tk.X, pady=4, padx=4)
                
                # Wall info
                info_frame = ttk.Frame(wall_card, style='Main.TFrame')
                info_frame.pack(fill=tk.X)
                
                w_length = wall_attr(wall, 'length', 0.0)
                wall_height = wall_attr(wall, 'height', None)
                try:
                    wall_height = float(wall_height) if wall_height is not None else float(adapter.wall_height or room_data['default_height'])
                except Exception:
                    wall_height = float(room_data['default_height'])

                ceramic_h = wall_attr(wall, 'ceramic_height', 0.0)
                try:
                    ceramic_h = float(ceramic_h or 0.0)
                except Exception:
                    ceramic_h = 0.0
                if ceramic_h <= 0:
                    ceramic_h = float(room_data['default_height'])

                # Apply saved state if exists (enabled, height) for this index
                if i < len(saved_walls):
                    try:
                        saved_enabled, saved_h, _ = saved_walls[i]
                        if saved_h:
                            ceramic_h = float(saved_h)
                    except Exception:
                        pass
                ttk.Label(
                    info_frame,
                    text=f"📏 الطول: {w_length:.2f} م  |  ارتفاع الجدار: {wall_height:.2f} م  |  مساحة السيراميك الحالية: {w_length * ceramic_h:.2f} م²",
                    foreground=self.app.colors['text_secondary']
                ).pack(side=tk.LEFT)
                
                # Controls
                controls_frame = ttk.Frame(wall_card, style='Main.TFrame')
                controls_frame.pack(fill=tk.X, pady=(8, 0))
                
                # Enable checkbox
                default_enabled = True
                if i < len(saved_walls):
                    try:
                        saved_enabled, saved_h, _ = saved_walls[i]
                        default_enabled = bool(saved_enabled)
                    except Exception:
                        pass
                enabled_var = tk.BooleanVar(value=default_enabled)
                ttk.Checkbutton(
                    controls_frame,
                    text="تفعيل",
                    variable=enabled_var
                ).pack(side=tk.LEFT)
                
                # Height input
                ttk.Label(controls_frame, text="ارتفاع السيراميك:").pack(side=tk.LEFT, padx=(16, 4))
                height_val = ceramic_h
                height_var = tk.StringVar(value=str(height_val))
                height_entry = ttk.Entry(controls_frame, textvariable=height_var, width=8)
                height_entry.pack(side=tk.LEFT)
                ttk.Label(controls_frame, text="م").pack(side=tk.LEFT, padx=(2, 8))
                
                # Preview area
                w_length = wall_attr(wall, 'length', 0.0)
                preview_area = w_length * height_val
                preview_label = ttk.Label(
                    controls_frame,
                    text=f"≈ {preview_area:.2f} م²",
                    foreground=self.app.colors['accent']
                )
                preview_label.pack(side=tk.LEFT, padx=8)
                
                def update_preview(var, lbl, length):
                    def _update(*_):
                        try:
                            h = float(var.get())
                            lbl.configure(text=f"≈ {length * h:.2f} م²")
                        except:
                            lbl.configure(text="؟")
                    return _update
                
                height_var.trace_add('write', update_preview(height_var, preview_label, w_length))
                
                wall_controls.append((enabled_var, height_var, wall))
            
            update_walls_scroll()
        
        def on_room_enabled_change(*_):
            room_name = current_room_name.get()
            if room_name and room_name in room_selection:
                room_selection[room_name]['selected'] = room_enabled_var.get()
                # Update tree tag
                if room_enabled_var.get():
                    rooms_tree.item(room_name, tags=('selected',))
                else:
                    rooms_tree.item(room_name, tags=())
        
        room_enabled_var.trace_add('write', on_room_enabled_change)
        
        def on_room_select(event):
            sel = rooms_tree.selection()
            if sel:
                # Preserve current room settings before switching
                prev_name = current_room_name.get()
                if prev_name and prev_name in room_selection and wall_controls:
                    room_selection[prev_name]['walls'] = [
                        (ev.get(), hv.get(), w) for ev, hv, w in wall_controls
                    ]

                room_name = sel[0]
                current_room_name.set(room_name)
                load_room_walls(room_name)
        
        rooms_tree.bind('<<TreeviewSelect>>', on_room_select)

        # If we preselected the current room above, load its walls now.
        try:
            _initial_key = current_room_name.get()
            if _initial_key and _initial_key in room_selection:
                load_room_walls(_initial_key)
        except Exception:
            pass
        
        # Summary panel
        summary_frame = ttk.LabelFrame(main_frame, text="📊 ملخص", padding=8)
        summary_frame.pack(fill=tk.X, pady=(8, 0))
        
        summary_label = ttk.Label(
            summary_frame,
            text="اختر الغرف من القائمة لحساب الإجمالي",
            foreground=self.app.colors['text_secondary']
        )
        summary_label.pack(anchor='w')
        
        def update_summary():
            total_area = 0.0
            rooms_count = 0
            walls_count = 0
            
            for name, data in room_selection.items():
                # تخطَّ الغرف التي لا هي مفعّلة ولا فيها أي جدار مفعّل في الحوار
                has_enabled_walls = any(ev for (ev, _, _) in data.get('walls', []) if ev)
                if not data['selected'] and not has_enabled_walls:
                    continue

                adapter = RoomAdapter(data['room'])
                walls = adapter.walls or []

                if data['walls']:
                    # Use saved wall settings
                    for enabled, height_str, wall in data['walls']:
                        if enabled:
                            try:
                                h = float(height_str)
                                w_length = wall_attr(wall, 'length', 0.0)
                                total_area += w_length * h
                                walls_count += 1
                            except:
                                pass
                else:
                    # Use default height
                    for wall in walls:
                        w_length = wall_attr(wall, 'length', 0.0)
                        total_area += w_length * data['default_height']
                        walls_count += 1

                rooms_count += 1
            
            summary_label.configure(
                text=f"📐 المساحة التقديرية: {total_area:.2f} م²  |  {rooms_count} غرف  |  {walls_count} جدران"
            )
        
        # Update summary periodically
        def periodic_update():
            # Save current room walls
            room_name = current_room_name.get()
            if room_name and room_name in room_selection and wall_controls:
                room_selection[room_name]['walls'] = [
                    (ev.get(), hv.get(), w) for ev, hv, w in wall_controls
                ]
            update_summary()
            dialog.after(500, periodic_update)
        
        periodic_update()
        
        # Buttons
        btn_frame = ttk.Frame(main_frame, style='Main.TFrame')
        btn_frame.pack(fill=tk.X, pady=(12, 0))

        def _delete_wall_ceramic_for_rooms(room_names: set[str]):
            if not room_names:
                return 0
            before = len(self.app.project.ceramic_zones)
            self.app.project.ceramic_zones = [
                z for z in self.app.project.ceramic_zones
                if not (
                    (isinstance(z, dict) and str(z.get('surface_type', 'wall')).lower() == 'wall' and str(z.get('room_name', '')) in room_names)
                    or (hasattr(z, 'surface_type') and str(getattr(z, 'surface_type', 'wall')).lower() == 'wall' and str(getattr(z, 'room_name', '')) in room_names)
                )
            ]
            removed = before - len(self.app.project.ceramic_zones)

            # Reset breakdown per room object
            for data in room_selection.values():
                r = data.get('room')
                rname = data.get('room_name')
                if not r or rname not in room_names:
                    continue

                # Clear wall-level ceramic fields so ceramic doesn't "stick" via walls list.
                walls = getattr(r, 'walls', None) if not isinstance(r, dict) else r.get('walls')
                walls = walls or []
                for wall in walls:
                    if isinstance(wall, dict):
                        wall['ceramic_height'] = 0.0
                        wall['ceramic_area'] = 0.0
                        wall['ceramic_surface'] = ''
                    else:
                        if hasattr(wall, 'ceramic_height'):
                            wall.ceramic_height = 0.0
                        if hasattr(wall, 'ceramic_area'):
                            wall.ceramic_area = 0.0
                        if hasattr(wall, 'ceramic_surface'):
                            wall.ceramic_surface = ''

                if isinstance(r, dict):
                    breakdown = r.get('ceramic_breakdown', {}) or {}
                    breakdown['wall'] = 0.0
                    breakdown['wall_zones'] = 0.0
                    breakdown['wall_partial'] = 0.0
                    r['ceramic_breakdown'] = breakdown
                    r['ceramic_area'] = breakdown.get('floor', 0.0) + breakdown.get('ceiling', 0.0)
                else:
                    breakdown = getattr(r, 'ceramic_breakdown', {}) or {}
                    breakdown['wall'] = 0.0
                    breakdown['wall_zones'] = 0.0
                    breakdown['wall_partial'] = 0.0
                    r.ceramic_breakdown = breakdown
                    r.ceramic_area = breakdown.get('floor', 0.0) + breakdown.get('ceiling', 0.0)

                # Recompute finish totals using UnifiedCalculator
                if hasattr(self.app, '_recompute_room_finish'):
                    self.app._recompute_room_finish(r)
            return removed

        def delete_current_room_ceramic():
            key = current_room_name.get()
            if not key or key not in room_selection:
                messagebox.showinfo("Info", "اختر غرفة أولاً")
                return
            rname = room_selection[key].get('room_name')
            if not rname:
                return
            if not messagebox.askyesno("Confirm", f"حذف سيراميك الجدران للغرفة: {rname} ؟"):
                return
            removed = _delete_wall_ceramic_for_rooms({rname})
            self.app.refresh_rooms()
            if hasattr(self.app, 'ceramic_tab'):
                self.app.ceramic_tab.refresh_data()
            self.app.update_status(f"🗑️ حذف سيراميك الجدران ({removed}) للغرفة: {rname}", icon="🗑️")

        def delete_all_rooms_ceramic():
            if not self.app.project.ceramic_zones:
                messagebox.showinfo("Info", "لا يوجد سيراميك")
                return
            if not messagebox.askyesno("Confirm", "حذف سيراميك الجدران لكل الغرف؟"):
                return
            room_names = {data.get('room_name') for data in room_selection.values() if data.get('room_name')}
            removed = _delete_wall_ceramic_for_rooms(room_names)
            self.app.refresh_rooms()
            if hasattr(self.app, 'ceramic_tab'):
                self.app.ceramic_tab.refresh_data()
            self.app.update_status(f"🧹 حذف سيراميك الجدران لكل الغرف ({removed})", icon="🧹")
        
        def apply():
            # Save current room walls first
            room_name = current_room_name.get()
            if room_name and room_name in room_selection and wall_controls:
                room_selection[room_name]['walls'] = [
                    (ev.get(), hv.get(), w) for ev, hv, w in wall_controls
                ]
            
            # أولاً: احذف مناطق السيراميك القديمة للغرف المختارة (استبدال، مو مضاعفة)
            rooms_to_process = set()
            rooms_to_process_objs = []
            for key, data in room_selection.items():
                has_enabled_walls = any(ev for (ev, _, _) in data.get('walls', []) if ev)
                if data['selected'] or has_enabled_walls:
                    rooms_to_process.add(data.get('room_name'))
                    rooms_to_process_objs.append(data.get('room'))
            
            # حذف مناطق السيراميك الحالية لهذه الغرف فقط
            self.app.project.ceramic_zones = [
                z for z in self.app.project.ceramic_zones
                if not (
                    (isinstance(z, dict) and z.get('room_name') in rooms_to_process and z.get('surface_type') == 'wall')
                    or (hasattr(z, 'room_name') and getattr(z, 'room_name', '') in rooms_to_process and getattr(z, 'surface_type', '') == 'wall')
                )
            ]
            
            # Reset ceramic_breakdown['wall'] for all affected rooms (by object)
            for r in rooms_to_process_objs:
                if not r:
                    continue
                if isinstance(r, dict):
                    breakdown = r.get('ceramic_breakdown', {}) or {}
                    breakdown['wall'] = 0.0
                    r['ceramic_breakdown'] = breakdown
                    r['ceramic_area'] = breakdown.get('floor', 0.0) + breakdown.get('ceiling', 0.0)
                else:
                    breakdown = getattr(r, 'ceramic_breakdown', {}) or {}
                    breakdown['wall'] = 0.0
                    r.ceramic_breakdown = breakdown
                    r.ceramic_area = breakdown.get('floor', 0.0) + breakdown.get('ceiling', 0.0)
            
            total_area = 0.0
            zones_created = 0
            rooms_processed = 0
            
            for key, data in room_selection.items():
                # Skip rooms that are neither globally selected nor have any enabled walls
                has_enabled_walls = any(ev for (ev, _, _) in data.get('walls', []) if ev)
                if not data['selected'] and not has_enabled_walls:
                    continue

                room = data['room']
                adapter = RoomAdapter(room)
                walls = adapter.walls or []

                # إذا لم تكن هناك جدران في الموديل ولا في الحوار، نتخطّى الغرفة فعلاً
                if not walls and not data['walls']:
                    continue
                
                room_wall_area = 0.0
                room_display = data.get('room_name') or key
                
                if data['walls']:
                    # Use saved wall settings
                    for i, (enabled, height_str, wall) in enumerate(data['walls']):
                        if not enabled:
                            continue
                        try:
                            h = float(height_str)
                            if h <= 0:
                                continue
                            
                            # CRITICAL: Get actual wall from room.walls, not dialog reference
                            if i < len(walls):
                                actual_wall = walls[i]
                                w_length = wall_attr(actual_wall, 'length', 0.0)
                                wall_name = wall_attr(actual_wall, 'name', f"Wall {i+1}")
                            else:
                                # Fallback (shouldn't happen)
                                w_length = wall_attr(wall, 'length', 0.0)
                                wall_name = wall_attr(wall, 'name', f"Wall {i+1}")
                            
                            if w_length <= 0:
                                continue  # Skip walls with no length
                            
                            wall_area = w_length * h
                            room_wall_area += wall_area
                            
                            # Update the ACTUAL wall in room's walls list
                            if i < len(walls):
                                actual_wall = walls[i]
                                if isinstance(actual_wall, dict):
                                    actual_wall['ceramic_height'] = h
                                    actual_wall['ceramic_area'] = wall_area
                                    actual_wall['ceramic_surface'] = 'سيراميك'
                                else:
                                    actual_wall.ceramic_height = h
                                    actual_wall.ceramic_area = wall_area
                                    actual_wall.ceramic_surface = 'سيراميك'
                            
                            # Create zone for each wall
                            zone = CeramicZone(
                                name=f"سيراميك - {room_display} - جدار {i+1}",
                                category='Kitchen' if data['rtype'] == 'kitchen' else 'Bathroom' if data['rtype'] in ['bath', 'toilet'] else 'Other',
                                perimeter=w_length,
                                height=h,
                                surface_type='wall',
                                room_name=room_display,
                                wall_name=wall_name
                            )
                            self.app.project.ceramic_zones.append(zone)
                            zones_created += 1
                            total_area += wall_area
                        except Exception:
                            pass
                else:
                    # Use default height for all walls
                    h = data['default_height']
                    for i, wall in enumerate(walls):
                        w_length = wall_attr(wall, 'length', 0.0)
                        wall_area = w_length * h
                        room_wall_area += wall_area
                        
                        # Update wall object with ceramic info
                        if isinstance(wall, dict):
                            wall['ceramic_height'] = h
                            wall['ceramic_area'] = wall_area
                            wall['ceramic_surface'] = 'سيراميك'
                        else:
                            wall.ceramic_height = h
                            wall.ceramic_area = wall_area
                            wall.ceramic_surface = 'سيراميك'
                        
                        # Get wall name for this zone
                        wall_name = wall_attr(wall, 'name', f"Wall {i+1}")
                        
                        zone = CeramicZone(
                            name=f"سيراميك - {room_display} - جدار {i+1}",
                            category='Kitchen' if data['rtype'] == 'kitchen' else 'Bathroom' if data['rtype'] in ['bath', 'toilet'] else 'Other',
                            perimeter=w_length,
                            height=h,
                            surface_type='wall',
                            room_name=room_display,
                            wall_name=wall_name
                        )
                        self.app.project.ceramic_zones.append(zone)
                        zones_created += 1
                        total_area += wall_area
                
                # Update room ceramic data
                if room_wall_area > 0:
                    if isinstance(room, dict):
                        room['ceramic_area'] = (room.get('ceramic_area', 0.0) or 0.0) + room_wall_area
                        breakdown = room.get('ceramic_breakdown', {}) or {}
                        breakdown['wall'] = breakdown.get('wall', 0.0) + room_wall_area
                        room['ceramic_breakdown'] = breakdown
                    else:
                        room.ceramic_area = (getattr(room, 'ceramic_area', 0.0) or 0.0) + room_wall_area
                        breakdown = getattr(room, 'ceramic_breakdown', {}) or {}
                        breakdown['wall'] = breakdown.get('wall', 0.0) + room_wall_area
                        room.ceramic_breakdown = breakdown
                        
                        # Recalculate paint/plaster based on new ceramic
                        if hasattr(room, 'update_finish_areas'):
                            all_openings = list(self.app.project.doors) + list(self.app.project.windows)
                            room.update_finish_areas(all_openings)
                    
                    rooms_processed += 1
            
            # Refresh ALL affected rooms with ceramic recalculation
            for key, data in room_selection.items():
                if data['selected']:
                    room = data['room']
                    self._recalculate_room_ceramic_with_openings(room)
                    if hasattr(self.app, '_recompute_room_finish'):
                        self.app._recompute_room_finish(room)
            
            # Refresh UI
            self.app.refresh_rooms()
            if hasattr(self.app, 'ceramic_tab'):
                self.app.ceramic_tab.refresh_data()
            if self.selected_room:
                self._sync_ceramic_zones_to_walls(self.selected_room)
                self._load_room_details(self.selected_room)
                metrics = self._compute_room_finish_metrics(self.selected_room)
                self._update_room_metrics_ui(metrics)
            
            dialog.destroy()
            self.app.update_status(
                f"✅ تم إنشاء {zones_created} منطقة سيراميك لـ {rooms_processed} غرف | الإجمالي: {total_area:.2f} م²",
                icon="🧱"
            )
        
        ttk.Button(btn_frame, text="🗑️ حذف سيراميك الغرفة", command=delete_current_room_ceramic, style='Warning.TButton', width=18).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="🧹 حذف سيراميك كل الغرف", command=delete_all_rooms_ceramic, style='Danger.TButton', width=20).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Button(btn_frame, text="✅ تطبيق", command=apply, style='Accent.TButton', width=16).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="❌ إلغاء", command=dialog.destroy, style='Secondary.TButton', width=16).pack(side=tk.RIGHT, padx=(0, 8))
        
        # Select first room if available
        children = rooms_tree.get_children()
        if children:
            rooms_tree.selection_set(children[0])
            on_room_select(None)
            
    def _add_ceramic_manual(self):
        """Add a ceramic zone manually to the current room - SIMPLIFIED VERSION."""
        if not self.selected_room:
            messagebox.showwarning("لا يوجد اختيار", "الرجاء اختيار غرفة أولاً")
            return
        
        room_name = self.app._room_name(self.selected_room)
        adapter = RoomAdapter(self.selected_room)
        
        # Simple dialog
        dialog = tk.Toplevel(self.app.root)
        dialog.title(f"إضافة سيراميك - {room_name}")
        dialog.geometry("450x380")
        dialog.configure(bg=self.app.colors['bg_primary'])
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20, style='Card.TFrame')
        frame.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(
            frame,
            text=f"🧱 إضافة سيراميك للغرفة: {room_name}",
            font=('Segoe UI', 12, 'bold'),
            foreground=self.app.colors['accent']
        ).pack(pady=(0, 15))
        
        # Room info
        info_text = f"📐 مساحة الغرفة: {adapter.area:.2f} م²  |  محيط: {adapter.perimeter:.2f} م  |  ارتفاع: {adapter.wall_height:.2f} م"
        ttk.Label(frame, text=info_text, foreground=self.app.colors['text_secondary']).pack(pady=(0, 15))
        
        # Surface type selection
        surface_var = tk.StringVar(value='floor')
        
        ttk.Label(frame, text="نوع السطح:", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        
        surfaces_frame = ttk.Frame(frame, style='Main.TFrame')
        surfaces_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Radiobutton(
            surfaces_frame,
            text="🟫 أرضية (الكامل)",
            variable=surface_var,
            value='floor',
            style='Accent.TRadiobutton'
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            surfaces_frame,
            text="⬛ سقف (الكامل)",
            variable=surface_var,
            value='ceiling',
            style='Accent.TRadiobutton'
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            surfaces_frame,
            text="🧱 جدران (مخصص)",
            variable=surface_var,
            value='wall',
            style='Accent.TRadiobutton'
        ).pack(side=tk.LEFT, padx=10)
        
        # Area/Height inputs (conditional)
        inputs_frame = ttk.Frame(frame, style='Main.TFrame')
        inputs_frame.pack(fill='x', pady=10)
        
        area_label = ttk.Label(inputs_frame, text="المساحة (م²):")
        area_var = tk.StringVar(value=f"{adapter.area:.2f}")
        area_entry = ttk.Entry(inputs_frame, textvariable=area_var, width=15)
        
        height_label = ttk.Label(inputs_frame, text="الارتفاع (م):")
        height_var = tk.StringVar(value="1.20")
        height_entry = ttk.Entry(inputs_frame, textvariable=height_var, width=15)
        
        def update_inputs(*args):
            surface = surface_var.get()
            # Clear frame
            for widget in inputs_frame.winfo_children():
                widget.pack_forget()
            
            if surface in ['floor', 'ceiling']:
                area_label.pack(side=tk.LEFT, padx=(0, 5))
                area_entry.pack(side=tk.LEFT)
                area_var.set(f"{adapter.area:.2f}")
                ttk.Label(inputs_frame, text="  (المساحة الافتراضية لكامل الغرفة)",
                         foreground=self.app.colors['text_muted']).pack(side=tk.LEFT, padx=5)
            elif surface == 'wall':
                height_label.pack(side=tk.LEFT, padx=(0, 5))
                height_entry.pack(side=tk.LEFT)
                ttk.Label(inputs_frame, text="  م  (من الأرض)",
                         foreground=self.app.colors['text_muted']).pack(side=tk.LEFT, padx=5)
        
        surface_var.trace_add('write', update_inputs)
        update_inputs()
        
        # Preview
        preview_var = tk.StringVar(value="")
        preview_label = ttk.Label(
            frame,
            textvariable=preview_var,
            font=('Segoe UI', 10, 'bold'),
            foreground=self.app.colors['success']
        )
        preview_label.pack(pady=15)
        
        def update_preview(*args):
            try:
                surface = surface_var.get()
                if surface in ['floor', 'ceiling']:
                    area = float(area_var.get() or 0)
                    preview_var.set(f"✓ سيتم إضافة {area:.2f} م² سيراميك {'أرضية' if surface == 'floor' else 'سقف'}")
                elif surface == 'wall':
                    height = float(height_var.get() or 0)
                    wall_area = adapter.perimeter * height
                    preview_var.set(f"✓ سيتم إضافة {wall_area:.2f} م² سيراميك جدران")
            except:
                preview_var.set("⚠️ أدخل قيمة صحيحة")
        
        area_var.trace_add('write', update_preview)
        height_var.trace_add('write', update_preview)
        surface_var.trace_add('write', update_preview)
        update_preview()
        
        # Buttons
        buttons_frame = ttk.Frame(frame, style='Main.TFrame')
        buttons_frame.pack(pady=20)
        
        result = {'confirmed': False}
        
        def confirm():
            result['confirmed'] = True
            result['surface'] = surface_var.get()
            result['area'] = float(area_var.get() or 0) if surface_var.get() in ['floor', 'ceiling'] else 0
            result['height'] = float(height_var.get() or 0) if surface_var.get() == 'wall' else 0
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        ttk.Button(
            buttons_frame,
            text="✓ إضافة",
            command=confirm,
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="✗ إلغاء",
            command=cancel
        ).pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()
        
        if not result.get('confirmed'):
            return
        
        # حذف السيراميك القديم من نفس النوع لهذه الغرفة (استبدال مو مضاعفة)
        surface = result['surface']

        def _zone_room(z):
            return z.get('room_name') if isinstance(z, dict) else getattr(z, 'room_name', '')

        def _zone_surface(z):
            val = z.get('surface_type') if isinstance(z, dict) else getattr(z, 'surface_type', '')
            return str(val or '').lower()

        surface_l = surface.lower()
        self.app.project.ceramic_zones = [
            z for z in self.app.project.ceramic_zones
            if not (_zone_room(z) == room_name and _zone_surface(z) == surface_l)
        ]
        
        # Create ceramic zone
        from bilind.models.finish import CeramicZone
        
        zone_name = f"{room_name} - {'أرضية' if surface == 'floor' else 'سقف' if surface == 'ceiling' else 'جدران'}"
        
        if surface in ['floor', 'ceiling']:
            zone = CeramicZone(
                name=zone_name,
                room_name=room_name,
                surface_type=surface,
                perimeter=0,  # Not used for floor/ceiling
                height=0,     # Not used for floor/ceiling
                effective_area=result['area'],
                category='Other'
            )
        else:  # wall
            zone = CeramicZone(
                name=zone_name,
                room_name=room_name,
                surface_type='wall',
                perimeter=adapter.perimeter,
                height=result['height'],
                category='Other'
            )
        
        self.app.project.ceramic_zones.append(zone)
        
        # Recalculate
        self._recalculate_room_ceramic_with_openings(self.selected_room)
        if hasattr(self.selected_room, 'update_finish_areas'):
            all_openings = list(self.app.project.doors) + list(self.app.project.windows)
            self.selected_room.update_finish_areas(all_openings)
        
        self._load_room_details(self.selected_room)
        self.app.refresh_after_ceramic_change()
        
        self.app.update_status(f"✓ تمت إضافة {zone_name}", icon="🧱")

    def _sync_ceramic_zones_to_walls(self, room):
        """Sync global ceramic zones to wall properties for visualization."""
        if not room: return
        
        room_name = self.app._room_name(room)
        
        per_wall_heights: Dict[str, float] = {}
        fallback_height = 0.0
        
        for z in self.app.project.ceramic_zones:
            z_name = self.app._zone_attr(z, 'name', '')
            z_room = self.app._zone_attr(z, 'room_name', '')
            z_surface = self.app._zone_attr(z, 'surface_type', 'wall')
            wall_name = self.app._zone_attr(z, 'wall_name', None)
            
            is_for_room = (z_room == room_name) or (room_name and room_name in str(z_name))
            if z_surface != 'wall' or not is_for_room:
                continue
            height_val = float(self.app._zone_attr(z, 'height', 0.0) or 0.0)
            if wall_name:
                per_wall_heights[wall_name] = max(per_wall_heights.get(wall_name, 0.0), height_val)
            else:
                fallback_height = max(fallback_height, height_val)

        walls = getattr(room, 'walls', []) if not isinstance(room, dict) else room.get('walls', [])
        if not walls:
            return

        if not per_wall_heights and fallback_height <= 0:
            return

        for wall in walls:
            w_name = wall.get('name') if isinstance(wall, dict) else getattr(wall, 'name', None)
            target_height = per_wall_heights.get(w_name)
            if target_height is None and fallback_height > 0:
                target_height = fallback_height
            if target_height is None:
                continue
            if isinstance(wall, dict):
                wall['ceramic_height'] = target_height
                wall['ceramic_surface'] = 'سيراميك'
            else:
                wall.ceramic_height = target_height
                wall.ceramic_surface = 'سيراميك'

    def _auto_calc_current_room(self):
        """Run Auto Calc on current room only."""
        if not self.selected_room:
            messagebox.showwarning("No Selection", "Please select a room first.")
            return
        
        # Call app's auto calculation directly on this room
        room_dict = self.selected_room.to_dict() if hasattr(self.selected_room, 'to_dict') else self.selected_room
        
        # Check wall height
        wall_h = float(room_dict.get('wall_height', 0.0) or 0.0)
        if wall_h <= 0:
            messagebox.showwarning(
                "Missing Wall Height",
                "Please set wall height before auto-calculating."
            )
            return
        
        # Determine gross walls
        perim = float(room_dict.get('perim', 0.0) or 0.0)
        segments = room_dict.get('wall_segments') if room_dict.get('is_balcony') else []
        if segments:
            gross = 0.0
            for seg in segments:
                try:
                    gross += float(seg.get('length', 0.0) or 0.0) * float(seg.get('height', 0.0) or 0.0)
                except Exception:
                    pass
        else:
            gross = perim * wall_h if wall_h > 0 else 0.0
        
        # Opening deduction
        try:
            opening_area = self.app.association.calculate_room_opening_area(self.selected_room)
        except Exception:
            opening_area = 0.0
        
        net_wall = max(0.0, gross - opening_area)
        
        # Update room
        if isinstance(self.selected_room, dict):
            self.selected_room['wall_finish_area'] = net_wall
        else:
            self.selected_room.wall_finish_area = net_wall
        
        # Recompute plaster/paint
        self.app._recompute_room_finish(self.selected_room)
        
        # Reload display
        self._load_room_details(self.selected_room)
        self.app.refresh_rooms()
        self._load_room_details(self.selected_room)
        
        room_name = self.app._room_name(self.selected_room)
        self.app.update_status(f"Auto calculated finishes for '{room_name}'", icon="🔄")
    
    def _auto_update_all_rooms(self):
        """Recalculate all room deductions (openings, ceramics) for all rooms using UnifiedCalculator."""
        if not self.app.project.rooms:
            messagebox.showinfo("No Rooms", "No rooms to update.")
            return
        
        # Confirm action
        total_rooms = len(self.app.project.rooms)
        confirm = messagebox.askyesno(
            "Auto Update All Rooms",
            f"This will recalculate openings deductions and ceramic areas for all {total_rooms} rooms using the Unified Calculator.\n\n"
            "Continue?",
            icon='question'
        )
        if not confirm:
            return
        
        # Use UnifiedCalculator
        calc = UnifiedCalculator(self.app.project)
        results = calc.calculate_all_rooms()
        
        updated_count = 0
        
        # Map results back to rooms
        for i, room in enumerate(self.app.project.rooms):
            # Find result for this room
            room_name = self.app._room_name(room)
            res = next((r for r in results if r.room_name == room_name), None)
            
            if not res:
                continue
            
            # Update room attributes
            breakdown = {
                'wall': res.ceramic_wall,
                'ceiling': res.ceramic_ceiling,
                'floor': res.ceramic_floor,
            }
            
            if isinstance(room, dict):
                room['wall_finish_area'] = res.walls_net
                room['ceiling_finish_area'] = res.ceiling_area
                room['plaster_area'] = res.plaster_total
                room['paint_area'] = res.paint_total
                room['ceramic_area'] = res.ceramic_wall + res.ceramic_ceiling + res.ceramic_floor
                room['ceramic_breakdown'] = breakdown
            else:
                room.wall_finish_area = res.walls_net
                room.ceiling_finish_area = res.ceiling_area
                room.plaster_area = res.plaster_total
                room.paint_area = res.paint_total
                room.ceramic_area = res.ceramic_wall + res.ceramic_ceiling + res.ceramic_floor
                room.ceramic_breakdown = breakdown
            
            updated_count += 1
        
        # Refresh all displays
        self.app.refresh_rooms()
        self.refresh_rooms_list()
        if self.selected_room:
            self._load_room_details(self.selected_room)
        
        msg = f"Updated {updated_count} room(s) using Unified Calculator"
        self.app.update_status(msg, icon="⚡")
        messagebox.showinfo("Auto Update Complete", msg)
        
    def _view_in_summary(self):
        """Switch to Summary tab to view room statistics."""
        # Switch to Summary tab (index 7 in original layout)
        if hasattr(self.app, 'notebook'):
            self.app.notebook.select(6)  # Summary tab
            
    def _refresh_all_tabs(self):
        """Refresh all tabs to reflect changes."""
        self.app.refresh_rooms()
        self.app.refresh_openings()
        self.app.refresh_walls()
        self.app.update_status("Refreshed all tabs", icon="🔄")
        
    # === Public Methods ===
    
    def refresh_rooms_list(self):
        """Refresh the rooms list treeview."""
        # Initialize map if not exists
        self.iid_room_map = {}

        # Preserve current selection (room name) before clearing
        prev_selection_name = None
        sel = self.rooms_list_tree.selection()
        if sel:
            try:
                prev_selection_name = self.rooms_list_tree.item(sel[0], 'values')[0]
            except Exception:
                prev_selection_name = None

        # Clear existing items
        for item in self.rooms_list_tree.get_children():
            self.rooms_list_tree.delete(item)
        
        # Get search filter
        search_text = self.room_search_var.get().lower()
        
        # Populate
        reselect_iid = None
        for room in self.app.project.rooms:
            name = self.app._room_name(room)
            area = self.app._room_attr(room, 'area', 'area', 0.0)
            
            # Get opening count with per-room quantities
            summary = self.app.get_room_opening_summary(room)
            door_ids = summary.get('door_ids', [])
            window_ids = summary.get('window_ids', [])
            
            # Calculate total quantities for THIS room using room_quantities
            door_qty_total = 0
            for did in door_ids:
                for d in self.app.project.doors:
                    d_name = d.get('name') if isinstance(d, dict) else getattr(d, 'name', '')
                    if d_name == did:
                        # Check room_quantities first, fallback to qty=1 per room
                        room_qtys = d.get('room_quantities', {}) if isinstance(d, dict) else getattr(d, 'room_quantities', {}) or {}
                        if name in room_qtys:
                            door_qty_total += int(room_qtys[name] or 1)
                        else:
                            door_qty_total += 1  # Default: 1 per room assignment
                        break
            
            window_qty_total = 0
            for wid in window_ids:
                for w in self.app.project.windows:
                    w_name = w.get('name') if isinstance(w, dict) else getattr(w, 'name', '')
                    if w_name == wid:
                        # Check room_quantities first, fallback to qty=1 per room
                        room_qtys = w.get('room_quantities', {}) if isinstance(w, dict) else getattr(w, 'room_quantities', {}) or {}
                        if name in room_qtys:
                            window_qty_total += int(room_qtys[name] or 1)
                        else:
                            window_qty_total += 1  # Default: 1 per room assignment
                        break
            
            openings_text = f"{door_qty_total}D + {window_qty_total}W"
            
            # Apply filter
            if search_text and search_text not in name.lower():
                continue
            
            iid = self.rooms_list_tree.insert('', tk.END, values=(
                name,
                f"{area:.2f}" if area else "-",
                openings_text
            ))
            
            # Map IID to room object
            self.iid_room_map[iid] = room

            if prev_selection_name and name == prev_selection_name:
                reselect_iid = iid

        # Restore selection if possible
        if reselect_iid:
            try:
                self.rooms_list_tree.selection_set(reselect_iid)
                self.rooms_list_tree.focus(reselect_iid)
                # Update selected_room reference
                if reselect_iid in self.iid_room_map:
                    self.selected_room = self.iid_room_map[reselect_iid]
                
                # Refresh details panel for restored room
                self._show_details_widgets()
                self._refresh_openings_trees()
            except Exception:
                pass
    
    def _show_wall_opening_links(self):
        """Show dialog displaying which openings are linked to which walls (for balconies)."""
        if not self.selected_room:
            messagebox.showinfo("No Selection", "Please select a room first.")
            return
        
        # Check if balcony with wall segments
        if isinstance(self.selected_room, dict):
            is_balcony = self.selected_room.get('is_balcony', False)
            segments = self.selected_room.get('wall_segments', []) or []
        else:
            is_balcony = getattr(self.selected_room, 'is_balcony', False)
            segments = getattr(self.selected_room, 'wall_segments', []) or []
        
        if not is_balcony or not segments:
            messagebox.showinfo(
                "Not Applicable",
                "Wall-opening links are only for balconies with configured wall segments.\n\n"
                "To configure a balcony:\n"
                "1. Edit room and enable 'Balcony' mode\n"
                "2. Define wall segments\n"
                "3. Use 'Balcony Ceramic' dialog to assign openings to walls"
            )
            return
        
        # Create dialog
        dlg = tk.Toplevel(self.app.root)
        dlg.title(f"Wall-Opening Links: {self.app._room_name(self.selected_room)}")
        dlg.geometry("700x500")
        dlg.configure(bg=self.app.colors['bg_secondary'])
        dlg.transient(self.app.root)
        dlg.grab_set()
        
        main = ttk.Frame(dlg, padding=(16, 12), style='Main.TFrame')
        main.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(
            main,
            text=f"🔗 Wall-Opening Assignments",
            font=('Segoe UI Semibold', 14)
        ).pack(anchor='w', pady=(0, 8))
        
        ttk.Label(
            main,
            text="Shows which doors/windows are assigned to each wall segment for accurate ceramic deductions.",
            foreground=self.app.colors['text_secondary'],
            font=('Segoe UI', 9)
        ).pack(anchor='w', pady=(0, 12))
        
        # Scrollable content
        canvas = tk.Canvas(main, bg=self.app.colors['bg_secondary'], highlightthickness=0)
        scroll = ttk.Scrollbar(main, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        content = ttk.Frame(canvas, style='Main.TFrame')
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        
        # Display each wall and its openings
        for i, seg in enumerate(segments):
            wall_frame = ttk.LabelFrame(
                content,
                text=f"Wall {i+1} - {seg.get('length', 0):.2f}m × {seg.get('height', 0):.2f}m",
                padding=(12, 8),
                style='Card.TLabelframe'
            )
            wall_frame.pack(fill=tk.X, pady=6, padx=4)
            
            # Get assigned openings for this wall
            opening_ids = seg.get('opening_ids', []) or []
            
            if not opening_ids:
                ttk.Label(
                    wall_frame,
                    text="❌ No openings assigned to this wall",
                    foreground=self.app.colors.get('text_secondary', '#94a3b8'),
                    font=('Segoe UI', 9, 'italic')
                ).pack(anchor='w')
            else:
                ttk.Label(
                    wall_frame,
                    text="✅ Assigned openings:",
                    foreground=self.app.colors.get('success', '#10b981'),
                    font=('Segoe UI Semibold', 9)
                ).pack(anchor='w', pady=(0, 6))
                
                # List each opening
                for opening_id in opening_ids:
                    # Find the opening
                    opening = None
                    opening_type = "Unknown"
                    
                    for d in self.app.project.doors:
                        if self.app._opening_name(d) == opening_id:
                            opening = d
                            opening_type = "Door"
                            break
                    
                    if not opening:
                        for w in self.app.project.windows:
                            if self.app._opening_name(w) == opening_id:
                                opening = w
                                opening_type = "Window"
                                break
                    
                    if opening:
                        mat = self.app._opening_attr(opening, 'type', 'material_type', '-')
                        w_val = self.app._opening_attr(opening, 'w', 'width', 0.0)
                        h_val = self.app._opening_attr(opening, 'h', 'height', 0.0)
                        p = self.app._opening_attr(opening, 'placement_height', 'placement_height', 0.0)
                        
                        icon = "🚪" if opening_type == "Door" else "🪟"
                        detail_text = f"{icon} {opening_id} ({mat}) - {w_val:.2f}×{h_val:.2f}m @ {p:.2f}m height"
                    else:
                        detail_text = f"❓ {opening_id} (not found in project)"
                    
                    ttk.Label(
                        wall_frame,
                        text=f"  • {detail_text}",
                        font=('Segoe UI', 9)
                    ).pack(anchor='w', pady=2)
        
        # Close button
        ttk.Button(
            main,
            text="Close",
            command=dlg.destroy,
            style='Secondary.TButton'
        ).pack(pady=(12, 0))

