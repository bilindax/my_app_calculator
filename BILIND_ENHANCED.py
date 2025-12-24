"""
BILIND AutoCAD Extension - Enhanced Version
============================================
Features:
- ✅ Rooms with accurate W×L dimensions
- ✅ Separate Doors and Windows picking
- ✅ Walls with openings deduction
- ✅ Finishes calculator (Plaster/Paint/Tiles)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import csv
import os
from datetime import datetime
import time

try:
    from pyautocad import Autocad
    import win32com.client
    import pythoncom
except ImportError:
    print("❌ Missing dependencies. Run: pip install pyautocad pywin32")
    exit(1)

class BilindEnhanced:
    def __init__(self, root):
        self.root = root
        self.root.title("BILIND Enhanced - AutoCAD Calculator")
        self.root.geometry("1040x780")
        # Enhanced color palette with perfect harmony
        self.colors = {
            'bg_primary': '#0a0e1a',      # Deep space blue
            'bg_secondary': '#1e2139',    # Rich midnight
            'bg_card': '#2a2f4a',         # Elegant card background
            'accent': '#00d4ff',          # Vibrant cyan
            'accent_light': '#66e3ff',    # Light cyan
            'accent_dark': '#0099cc',     # Deep cyan
            'text_primary': '#ffffff',    # Pure white
            'text_secondary': '#a8b5d1',  # Soft blue-white
            'text_muted': '#6b7280',      # Muted grey
            'success': '#10b981',         # Modern green
            'warning': '#f59e0b',         # Warm amber
            'danger': '#ef4444',          # Clean red
            'secondary': '#6366f1',       # Modern indigo
            'border': '#374151',          # Subtle border
            'hover': '#374151'            # Hover state
        }
        self.root.configure(bg=self.colors['bg_primary'])

        # Opening type catalogs
        self.door_types = {
            'Wood': {
                'weight': 25,
                'material': 'Wood',
                'description': 'Wood door - default 25kg each'
            },
            'Steel': {
                'weight': 0,
                'material': 'Steel',
                'description': 'Steel door - enter actual weight'
            },
            'PVC': {
                'weight': 15,
                'material': 'PVC',
                'description': 'PVC door - default 15kg each'
            }
        }

        self.window_types = {
            'Aluminum': {
                'material': 'Aluminum',
                'description': 'Aluminum frame with clear glass'
            },
            'PVC': {
                'material': 'PVC',
                'description': 'PVC frame with double glazing'
            },
            'Wood': {
                'material': 'Wood',
                'description': 'Traditional wooden sash or casement'
            },
            'Steel': {
                'material': 'Steel',
                'description': 'Steel/metal frame window'
            }
        }
        
        # AutoCAD connection
        try:
            self.acad = Autocad(create_if_not_exists=False)
            self.doc = self.acad.doc
            self.root.title(f"BILIND Enhanced - {self.doc.Name}")
        except:
            messagebox.showerror("Error", "AutoCAD not running!")
            self.root.destroy()
            return
        
        # Data storage
        self.scale = 1.0
        self.rooms = []
        self.doors = []
        self.windows = []
        self.walls = []
        
        # Finishes - detailed tracking
        self.plaster_items = []  # [{'desc': 'Room 1', 'area': 25.5}, ...]
        self.paint_items = []
        self.tiles_items = []
        self.ceramic_zones = []  # [{'name': 'Kitchen', 'category': 'Kitchen', 'perimeter': 8.5, 'height': 0.8, 'area': 6.8, 'notes': ''}]
        
        self._status_after_id = None
        self._default_status = "جاهز - Ready"

        self.create_ui()

    # === STYLE & HELPERS ================================================== #

    def _setup_styles(self):
        """Configure ttk styles for a modern dark UI."""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            # Fallback to default without breaking execution
            pass

        colors = self.colors
        style.configure('Main.TFrame', background=colors['bg_secondary'])
        style.configure('Card.TLabelframe',
            background=colors['bg_card'],
            foreground=colors['text_primary'],
            bordercolor=colors['border'])
        style.configure('Card.TLabelframe.Label',
            background=colors['bg_card'],
            foreground=colors['accent'],
            font=('Segoe UI Semibold', 11))
        style.configure('Hero.TFrame', background=colors['accent_dark'])
        style.configure('HeroHeading.TLabel',
            background=colors['accent_dark'],
            foreground='white',
            font=('Segoe UI Semibold', 18))
        style.configure('HeroSubheading.TLabel',
            background=colors['accent_dark'],
            foreground='white',
            font=('Segoe UI', 11))
        style.configure('Metrics.TLabel',
            background=colors['bg_secondary'],
            foreground=colors['accent'],
            font=('Segoe UI Semibold', 11))

        tree_font = ('Segoe UI', 10)
        style.configure('Treeview',
                background=colors['bg_card'],
                fieldbackground=colors['bg_card'],
                foreground=colors['text_primary'],
                rowheight=28,
                font=tree_font)
        style.configure('Treeview.Heading',
            background=colors['accent'],
            foreground=colors['bg_primary'],
            relief='flat',
            font=('Segoe UI Semibold', 10))
        style.map('Treeview',
              background=[('selected', colors['accent_light'])],
              foreground=[('selected', colors['bg_primary'])])
        style.configure('Stone.Treeview',
            background=colors['bg_secondary'],
            fieldbackground=colors['bg_secondary'],
            foreground=colors['text_secondary'],
            font=tree_font)
        style.configure('Stone.Treeview.Heading',
            background=colors['warning'],
            foreground=colors['bg_primary'],
            font=('Segoe UI Semibold', 10))

        style.configure('Accent.TButton',
                background=colors['accent'],
                foreground='white',
                font=('Segoe UI Semibold', 10),
                padding=6)
        style.map('Accent.TButton',
              background=[('active', colors['accent_light'])])

        style.configure('Danger.TButton',
                background=colors['danger'],
                foreground='white',
                font=('Segoe UI Semibold', 10),
                padding=6)
        style.map('Danger.TButton', background=[('active', '#d50032')])

        style.configure('Secondary.TButton',
                background=colors['secondary'],
                foreground='white',
                font=('Segoe UI', 10),
                padding=6)
        style.map('Secondary.TButton', background=[('active', colors['hover'])])

        style.configure('Warning.TButton',
            background=colors['warning'],
            foreground=colors['bg_primary'],
            font=('Segoe UI Semibold', 10),
            padding=6)
        style.map('Warning.TButton', background=[('active', '#ffb347')])

        style.configure('Accent.TNotebook', background=colors['bg_secondary'])
        style.configure('Accent.TNotebook.Tab', font=('Segoe UI Semibold', 10))
        style.map('Accent.TNotebook.Tab',
              background=[('selected', colors['bg_card'])],
              foreground=[('selected', colors['accent'])])

        style.configure('Toolbar.TFrame', background=colors['bg_secondary'])
        style.configure('Caption.TLabel',
            background=colors['bg_secondary'],
            foreground=colors['text_secondary'],
            font=('Segoe UI', 9))
        style.configure('Small.TButton',
            background=colors['bg_card'],
            foreground=colors['text_secondary'],
            font=('Segoe UI', 9),
            padding=(8, 4))
        style.map('Small.TButton',
            background=[('active', colors['hover'])],
            foreground=[('active', colors['text_primary'])])

        style.configure('Status.TFrame', background=colors['bg_primary'])
        style.configure('Status.TLabel',
            background=colors['bg_primary'],
            foreground=colors['text_secondary'],
            font=('Segoe UI', 9))

        style.configure('Walls.Treeview',
            background=colors['bg_card'],
            fieldbackground=colors['bg_card'],
            foreground=colors['text_primary'],
            rowheight=28,
            font=('Segoe UI', 10))
        style.configure('Walls.Treeview.Heading',
            background=colors['secondary'],
            foreground=colors['bg_primary'],
            font=('Segoe UI Semibold', 10))
        style.map('Walls.Treeview',
            background=[('selected', colors['accent_light'])],
            foreground=[('selected', colors['bg_primary'])])

    def _opening_storage(self, opening_type):
        return self.doors if opening_type == 'DOOR' else self.windows

    def _ensure_room_names(self):
        for idx, room in enumerate(self.rooms, start=1):
            room.setdefault('name', f"Room{idx}")

    def _ensure_wall_names(self):
        for idx, wall in enumerate(self.walls, start=1):
            wall.setdefault('name', f"Wall{idx}")

    def _ensure_opening_names(self, opening_type):
        storage = self._opening_storage(opening_type)
        prefix = 'D' if opening_type == 'DOOR' else 'W'
        for idx, item in enumerate(storage, start=1):
            item.setdefault('name', f"{prefix}{idx}")

    def _make_unique_name(self, opening_type, base_name):
        storage = self._opening_storage(opening_type)
        existing = {item.get('name') for item in storage if item.get('name')}
        if base_name not in existing:
            return base_name
        suffix = 2
        while f"{base_name}{suffix}" in existing:
            suffix += 1
        return f"{base_name}{suffix}"

    def _build_opening_record(self, opening_type, name, type_label, width, height, qty, weight=0.0, layer=None):
        """Create a normalized dictionary for doors/windows."""
        width = float(width)
        height = float(height)
        qty = int(qty)
        qty = max(1, qty)

        perim_each = 2 * (width + height)
        area_each = width * height
        area_total = area_each * qty
        perim_total = perim_each * qty
        stone_total = perim_total  # حجر الملابن طول خطي بالمتر

        record = {
            'name': name,
            'layer': layer or type_label or opening_type,
            'type': type_label,
            'w': width,
            'h': height,
            'qty': qty,
            'perim_each': perim_each,
            'perim': perim_total,
            'area_each': area_each,
            'area': area_total,
            'stone': stone_total,
            'weight_each': float(weight) if opening_type == 'DOOR' else 0.0,
            'weight': float(weight) * qty if opening_type == 'DOOR' else 0.0
        }

        if opening_type == 'WINDOW':
            glass_each = area_each * 0.85
            record['glass_each'] = glass_each
            record['glass'] = glass_each * qty
        else:
            record['glass_each'] = 0.0
            record['glass'] = 0.0

        return record

    def _fmt(self, value, digits=2, default='-'):
        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return default

    def update_status(self, message, icon=""):
        """Update the persistent status bar with an optional icon."""
        if not hasattr(self, 'status_var'):
            return

        display_text = f"{icon} {message}".strip() if icon else message
        self.status_var.set(display_text)

        if self._status_after_id:
            self.root.after_cancel(self._status_after_id)
        self._status_after_id = self.root.after(4500, lambda: self.status_var.set(self._default_status))

    def _format_tree_row(self, data_key, record):
        if data_key == 'rooms':
            return (
                record.get('name', '-'),
                record.get('layer', '-'),
                self._fmt(record.get('w')),
                self._fmt(record.get('l')),
                self._fmt(record.get('perim')),
                self._fmt(record.get('area'))
            )
        if data_key == 'doors':
            return (
                record.get('name', '-'),
                record.get('type', '-'),
                self._fmt(record.get('w')),
                self._fmt(record.get('h')),
                record.get('qty', 1),
                self._fmt(record.get('perim')),
                self._fmt(record.get('area')),
                self._fmt(record.get('stone')),
                self._fmt(record.get('weight'), digits=1)
            )
        if data_key == 'windows':
            return (
                record.get('name', '-'),
                record.get('type', '-'),
                self._fmt(record.get('w')),
                self._fmt(record.get('h')),
                record.get('qty', 1),
                self._fmt(record.get('perim')),
                self._fmt(record.get('glass')),
                self._fmt(record.get('stone'))
            )
        if data_key == 'walls':
            return (
                record.get('name', '-'),
                record.get('layer', '-'),
                f"{record.get('length', 0):.2f}",
                f"{record.get('height', 0):.2f}",
                f"{record.get('gross', 0):.2f}",
                f"{record.get('deduct', 0):.2f}",
                f"{record.get('net', 0):.2f}"
            )
        return ()

    def _filter_treeview(self, tree, query, data_key):
        if tree is None:
            return []

        dataset = getattr(self, data_key, [])
        if data_key == 'rooms':
            self._ensure_room_names()
        elif data_key == 'doors':
            self._ensure_opening_names('DOOR')
        elif data_key == 'windows':
            self._ensure_opening_names('WINDOW')
        elif data_key == 'walls':
            self._ensure_wall_names()

        query = (query or '').strip().lower()
        filtered_records = []

        tree.delete(*tree.get_children())
        for record in dataset:
            values = self._format_tree_row(data_key, record)
            if not values:
                continue
            row_text = ' '.join(str(v).lower() for v in values)
            if not query or query in row_text:
                tree.insert('', tk.END, values=values)
                filtered_records.append(record)

        return filtered_records

    def _clear_filter(self, entry_widget, tree, data_key):
        entry_widget.delete(0, tk.END)
        return self._filter_treeview(tree, '', data_key)
    
    def create_ui(self):
        """Create main UI with tabs"""
        self._setup_styles()
        notebook = ttk.Notebook(self.root)
        notebook.configure(style='Accent.TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 0))
        tab_bg = self.colors['bg_secondary']
        
        # Tab 1: Main Data
        tab1 = tk.Frame(notebook, bg=tab_bg)
        notebook.add(tab1, text="📐 Main")
        self.create_main_tab(tab1)
        
        # Tab 2: Walls
        tab2 = tk.Frame(notebook, bg=tab_bg)
        notebook.add(tab2, text="🧱 Walls")
        self.create_walls_tab(tab2)
        
        # Tab 3: Finishes
        tab3 = tk.Frame(notebook, bg=tab_bg)
        notebook.add(tab3, text="🎨 Finishes")
        self.create_finishes_tab(tab3)

        # Tab 4: Materials & Metrics
        tab4 = tk.Frame(notebook, bg=tab_bg)
        notebook.add(tab4, text="🧮 Materials")
        self.create_materials_tab(tab4)
        
        # Tab 5: Summary
        tab5 = tk.Frame(notebook, bg=tab_bg)
        notebook.add(tab5, text="📊 Summary")
        self.create_summary_tab(tab5)

        status_frame = ttk.Frame(self.root, style='Status.TFrame', padding=(18, 6))
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_var = tk.StringVar(value=self._default_status)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT)
    
    def create_main_tab(self, parent):
        """Main tab with rooms and openings"""
        parent.configure(bg=self.colors['bg_secondary'])

        hero = ttk.Frame(parent, style='Hero.TFrame', padding=(18, 20))
        hero.pack(fill=tk.X, padx=16, pady=(16, 8))
        ttk.Label(hero,
              text="BILIND Spaces & Openings",
              style='HeroHeading.TLabel').pack(anchor=tk.W)
        ttk.Label(hero,
              text="خطط غرفك، أبوابك، شبابيكك مع واجهة زجاجية عصرية ومسارات حجر محسوبة تلقائياً",
              style='HeroSubheading.TLabel').pack(anchor=tk.W, pady=(6, 0))

        # Top controls
        ctrl_frame = ttk.Frame(parent, style='Main.TFrame', padding=(12, 12))
        ctrl_frame.pack(fill=tk.X, padx=16, pady=(4, 12))

        ttk.Label(ctrl_frame, text="Scale", foreground=self.colors['text_secondary']).pack(side=tk.LEFT, padx=(0, 6))
        self.scale_var = tk.StringVar(value="1.0")
        ttk.Entry(ctrl_frame, textvariable=self.scale_var, width=8).pack(side=tk.LEFT, padx=(0, 10))

        actions = [
            ("🏠 Pick Rooms", self.pick_rooms, 'Accent.TButton'),
            ("🚪 Pick Doors", self.pick_doors, 'Accent.TButton'),
            ("🪟 Pick Windows", self.pick_windows, 'Accent.TButton'),
            ("🔄 Reset", self.reset_all, 'Warning.TButton')
        ]
        for text, command, style in actions:
            ttk.Button(ctrl_frame, text=text, command=command, style=style).pack(side=tk.LEFT, padx=6)

        # Create scrollable content area
        canvas = tk.Canvas(parent, bg=self.colors['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
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
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Utility to build section frames
        def build_section(title, buttons, min_height=200):
            frame = ttk.LabelFrame(scrollable_frame, text=title, style='Card.TLabelframe', padding=(15, 12))
            frame.pack(fill=tk.X, padx=12, pady=8)
            frame.configure(height=min_height)

            btn_bar = ttk.Frame(frame, style='Main.TFrame')
            btn_bar.pack(fill=tk.X, pady=(0, 8))
            for btn_text, btn_cmd, btn_style in buttons:
                ttk.Button(btn_bar, text=btn_text, command=btn_cmd, style=btn_style).pack(side=tk.LEFT, padx=4)

            return frame

        # Rooms section
        rooms_buttons = [
            ("➕ Add", lambda: self.add_room_manual(), 'Accent.TButton'),
            ("✏️ Edit", lambda: self.edit_room(), 'Secondary.TButton'),
            ("🗑️ Delete", lambda: self.delete_room(), 'Danger.TButton'),
            ("🗑️ Delete Multiple", lambda: self.delete_multiple('rooms'), 'Danger.TButton'),
            ("🧮 Calculate Finishes", lambda: self.calculate_room_finishes(), 'Accent.TButton')
        ]
        rooms_frame = build_section("📋 ROOMS / الغرف", rooms_buttons, min_height=220)

        # Search filter for rooms
        filter_frame = ttk.Frame(rooms_frame, style='Main.TFrame')
        filter_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(filter_frame, text="🔍 Filter:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(0, 6))
        self.rooms_filter = ttk.Entry(filter_frame, width=25)
        self.rooms_filter.pack(side=tk.LEFT)
        self.rooms_filter.bind('<KeyRelease>', lambda e: self._filter_treeview(self.rooms_tree, self.rooms_filter.get(), 'rooms'))
        ttk.Button(filter_frame, text="❌ Clear", command=lambda: self._clear_filter(self.rooms_filter, self.rooms_tree, 'rooms'), 
                  style='Small.TButton').pack(side=tk.LEFT, padx=5)
        
        # Enhanced rooms treeview with better styling
        tree_frame = ttk.Frame(rooms_frame, style='Main.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        
        self.rooms_tree = ttk.Treeview(tree_frame,
                                       columns=('Name', 'Layer', 'W', 'L', 'Perim', 'Area'),
                                       show='headings',
                                       selectmode='browse',
                                       height=6)
        for col, text, width in [
            ('Name', 'Name', 110),
            ('Layer', 'Layer', 100),
            ('W', 'Width (m)', 90),
            ('L', 'Length (m)', 90),
            ('Perim', 'Perimeter (m)', 120),
            ('Area', 'Area (m²)', 110)
        ]:
            self.rooms_tree.heading(col, text=text)
            self.rooms_tree.column(col, width=width, anchor=tk.CENTER)

        rooms_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.rooms_tree.yview)
        self.rooms_tree.configure(yscrollcommand=rooms_scroll.set)
        
        # Pack with proper layout
        self.rooms_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rooms_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Doors section
        doors_buttons = [
            ("➕ Add", lambda: self.add_opening_manual('DOOR'), 'Accent.TButton'),
            ("✏️ Edit", lambda: self.edit_opening('DOOR'), 'Secondary.TButton'),
            ("🗑️ Delete", lambda: self.delete_opening('DOOR'), 'Danger.TButton'),
            ("🗑️ Delete Multiple", lambda: self.delete_multiple('doors'), 'Danger.TButton')
        ]
        doors_frame = build_section("🚪 DOORS / الأبواب", doors_buttons, min_height=200)
        
        # Search filter for doors
        filter_frame = ttk.Frame(doors_frame, style='Main.TFrame')
        filter_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(filter_frame, text="🔍 Filter:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(0, 6))
        self.doors_filter = ttk.Entry(filter_frame, width=25)
        self.doors_filter.pack(side=tk.LEFT)
        self.doors_filter.bind('<KeyRelease>', lambda e: self._filter_treeview(self.doors_tree, self.doors_filter.get(), 'doors'))
        ttk.Button(filter_frame, text="❌ Clear", command=lambda: self._clear_filter(self.doors_filter, self.doors_tree, 'doors'), 
                  style='Small.TButton').pack(side=tk.LEFT, padx=5)

        # Enhanced doors treeview with better scrolling
        doors_tree_frame = ttk.Frame(doors_frame, style='Main.TFrame')
        doors_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        
        door_columns = ('Name', 'Type', 'W', 'H', 'Qty', 'Perim', 'Area', 'Stone', 'Weight')
        self.doors_tree = ttk.Treeview(doors_tree_frame,
                                       columns=door_columns,
                                       show='headings',
                                       selectmode='browse',
                                       height=5)
        for col, text, width in [
            ('Name', 'Name', 100),
            ('Type', 'Type', 110),
            ('W', 'Width (m)', 90),
            ('H', 'Height (m)', 90),
            ('Qty', 'Qty', 60),
            ('Perim', 'Perimeter (m)', 120),
            ('Area', 'Area (m²)', 110),
            ('Stone', 'Stone (lm)', 110),
            ('Weight', 'Weight (kg)', 120)
        ]:
            self.doors_tree.heading(col, text=text)
            anchor = tk.CENTER if col not in ['Name', 'Type'] else tk.W
            self.doors_tree.column(col, width=width, anchor=anchor)

        doors_scroll = ttk.Scrollbar(doors_tree_frame, orient=tk.VERTICAL, command=self.doors_tree.yview)
        self.doors_tree.configure(yscrollcommand=doors_scroll.set)
        
        # Pack with enhanced layout
        self.doors_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        doors_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Windows section
        windows_buttons = [
            ("➕ Add", lambda: self.add_opening_manual('WINDOW'), 'Accent.TButton'),
            ("✏️ Edit", lambda: self.edit_opening('WINDOW'), 'Secondary.TButton'),
            ("🗑️ Delete", lambda: self.delete_opening('WINDOW'), 'Danger.TButton'),
            ("🗑️ Delete Multiple", lambda: self.delete_multiple('windows'), 'Danger.TButton')
        ]
        windows_frame = build_section("🪟 WINDOWS / الشبابيك", windows_buttons, min_height=200)
        
        # Search filter for windows
        filter_frame = ttk.Frame(windows_frame, style='Main.TFrame')
        filter_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(filter_frame, text="🔍 Filter:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(0, 6))
        self.windows_filter = ttk.Entry(filter_frame, width=25)
        self.windows_filter.pack(side=tk.LEFT)
        self.windows_filter.bind('<KeyRelease>', lambda e: self._filter_treeview(self.windows_tree, self.windows_filter.get(), 'windows'))
        ttk.Button(filter_frame, text="❌ Clear", command=lambda: self._clear_filter(self.windows_filter, self.windows_tree, 'windows'), 
                  style='Small.TButton').pack(side=tk.LEFT, padx=5)
        
        # Enhanced windows treeview with better scrolling
        windows_tree_frame = ttk.Frame(windows_frame, style='Main.TFrame')
        windows_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        
        window_columns = ('Name', 'Type', 'W', 'H', 'Qty', 'Perim', 'Glass', 'Stone')
        self.windows_tree = ttk.Treeview(windows_tree_frame,
                                         columns=window_columns,
                                         show='headings',
                                         selectmode='browse',
                                         height=5)
        for col, text, width in [
            ('Name', 'Name', 100),
            ('Type', 'Type', 110),
            ('W', 'Width (m)', 90),
            ('H', 'Height (m)', 90),
            ('Qty', 'Qty', 60),
            ('Perim', 'Perimeter (m)', 120),
            ('Glass', 'Glass (m²)', 120),
            ('Stone', 'Stone (lm)', 120)
        ]:
            self.windows_tree.heading(col, text=text)
            anchor = tk.CENTER if col not in ['Name', 'Type'] else tk.W
            self.windows_tree.column(col, width=width, anchor=anchor)

        windows_scroll = ttk.Scrollbar(windows_tree_frame, orient=tk.VERTICAL, command=self.windows_tree.yview)
        self.windows_tree.configure(yscrollcommand=windows_scroll.set)
        
        # Pack with enhanced layout
        self.windows_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        windows_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_walls_tab(self, parent):
        """Walls workspace with modern styling and quick filters."""
        parent.configure(bg=self.colors['bg_secondary'])

        hero = ttk.Frame(parent, style='Hero.TFrame', padding=(18, 20))
        hero.pack(fill=tk.X, padx=16, pady=(16, 12))
        ttk.Label(hero,
                  text="Wall Ledger & Deductions",
                  style='HeroHeading.TLabel').pack(anchor=tk.W)
        ttk.Label(hero,
                  text="التقط الجدران، خصم الفتحات، وتابع المساحات الصافية بعرض أنيق ومنظم",
                  style='HeroSubheading.TLabel').pack(anchor=tk.W, pady=(6, 0))

        toolbar = ttk.Frame(parent, style='Toolbar.TFrame', padding=(12, 10))
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 12))
        toolbar.columnconfigure(0, weight=1)

        btn_container = ttk.Frame(toolbar, style='Toolbar.TFrame')
        btn_container.grid(row=0, column=0, sticky='w')
        wall_actions = [
            ("🧱 Pick Walls", self.pick_walls, 'Accent.TButton'),
            ("➖ Deduct Openings", self.deduct_from_walls, 'Warning.TButton'),
            ("✏️ Edit", self.edit_wall, 'Secondary.TButton'),
            ("🗑️ Delete", self.delete_wall, 'Danger.TButton'),
            ("🗑️ Delete Multiple", lambda: self.delete_multiple('walls'), 'Danger.TButton')
        ]
        for text, command, style in wall_actions:
            ttk.Button(btn_container, text=text, command=command, style=style).pack(side=tk.LEFT, padx=4)

        filter_frame = ttk.Frame(toolbar, style='Toolbar.TFrame')
        filter_frame.grid(row=0, column=1, sticky='e')
        ttk.Label(filter_frame, text="🔍 Filter:", style='Caption.TLabel').pack(side=tk.LEFT, padx=(0, 6))
        self.walls_filter = ttk.Entry(filter_frame, width=24)
        self.walls_filter.pack(side=tk.LEFT)
        self.walls_filter.bind('<KeyRelease>', lambda e: self._filter_treeview(self.walls_tree, self.walls_filter.get(), 'walls'))
        ttk.Button(filter_frame,
                   text="❌ Clear",
                   command=lambda: self._clear_filter(self.walls_filter, self.walls_tree, 'walls'),
                   style='Small.TButton').pack(side=tk.LEFT, padx=6)

        table_frame = ttk.Frame(parent, style='Main.TFrame', padding=(12, 10))
        table_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))

        columns = ('Name', 'Layer', 'Length', 'Height', 'Gross', 'Deduct', 'Net')
        self.walls_tree = ttk.Treeview(table_frame,
                                       columns=columns,
                                       show='headings',
                                       style='Walls.Treeview',
                                       selectmode='browse',
                                       height=12)
        headings = {
            'Name': ('Name', 110, tk.W),
            'Layer': ('Layer', 120, tk.W),
            'Length': ('Length (m)', 110, tk.CENTER),
            'Height': ('Height (m)', 110, tk.CENTER),
            'Gross': ('Gross (m²)', 120, tk.CENTER),
            'Deduct': ('Deduct (m²)', 120, tk.CENTER),
            'Net': ('Net (m²)', 120, tk.CENTER)
        }
        for col in columns:
            text, width, anchor = headings[col]
            self.walls_tree.heading(col, text=text)
            self.walls_tree.column(col, width=width, anchor=anchor)

        walls_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.walls_tree.yview)
        self.walls_tree.configure(yscrollcommand=walls_scroll.set)
        self.walls_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        walls_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        metrics_frame = ttk.Frame(parent, style='Main.TFrame', padding=(16, 8))
        metrics_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        self.wall_metrics_var = tk.StringVar(value="Net wall area: 0.00 m²")
        ttk.Label(metrics_frame,
                  textvariable=self.wall_metrics_var,
                  style='Metrics.TLabel').pack(anchor=tk.W)
    
    def create_finishes_tab(self, parent):
        """Finishes calculator with modern UI"""
        parent.configure(bg=self.colors['bg_secondary'])
        
        hero = ttk.Frame(parent, style='Hero.TFrame', padding=(18, 20))
        hero.pack(fill=tk.X, padx=16, pady=(16, 8))
        ttk.Label(hero,
                  text="Wall Finishes Calculator",
                  style='HeroHeading.TLabel').pack(anchor=tk.W)
        ttk.Label(hero,
                  text="احسب الزريقة، الدهان، والبلاط من مساحات الغرف أو محيطات الجدران",
                  style='HeroSubheading.TLabel').pack(anchor=tk.W, pady=(6, 0))
        
        # Plaster
        plaster_frame = ttk.LabelFrame(parent, text="🏗️ PLASTER / زريقة", style='Card.TLabelframe', padding=(12, 10))
        plaster_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 8))
        
        plaster_btns = ttk.Frame(plaster_frame, style='Main.TFrame')
        plaster_btns.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(plaster_btns, text="➕ Room Areas", command=lambda: self.add_finish_from_source('plaster', 'rooms'), style='Accent.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(plaster_btns, text="📐 Room Walls", command=lambda: self.add_walls_from_rooms('plaster'), style='Accent.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(plaster_btns, text="🧱 Wall Net", command=lambda: self.add_finish_from_source('plaster', 'walls'), style='Secondary.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(plaster_btns, text="✍️ Manual", command=lambda: self.add_finish_manual('plaster'), style='Secondary.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(plaster_btns, text="➖ Deduct", command=lambda: self.deduct_ceramic_from_finish('plaster'), style='Warning.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(plaster_btns, text="✏️ Edit", command=lambda: self.edit_finish_item('plaster'), style='Secondary.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(plaster_btns, text="🗑️ Del", command=lambda: self.delete_finish_item('plaster'), style='Danger.TButton').pack(side=tk.LEFT, padx=3)
        
        # Plaster details table
        self.plaster_tree = ttk.Treeview(plaster_frame, columns=('Description', 'Area'), show='headings', height=4)
        self.plaster_tree.heading('Description', text='Description')
        self.plaster_tree.heading('Area', text='Area (m²)')
        self.plaster_tree.column('Description', width=400)
        self.plaster_tree.column('Area', width=120, anchor=tk.CENTER)
        ttk.Scrollbar(plaster_frame, orient=tk.VERTICAL, command=self.plaster_tree.yview).pack(side=tk.RIGHT, fill=tk.Y)
        self.plaster_tree.pack(fill=tk.BOTH, expand=True)
        
        self.plaster_label = ttk.Label(plaster_frame, text="Total = 0.00 m²", style='Metrics.TLabel')
        self.plaster_label.pack(anchor=tk.W, pady=(8, 0))
        
        # Paint
        paint_frame = ttk.LabelFrame(parent, text="🎨 PAINT / دهان", style='Card.TLabelframe', padding=(12, 10))
        paint_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        
        paint_btns = ttk.Frame(paint_frame, style='Main.TFrame')
        paint_btns.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(paint_btns, text="➕ Room Areas", command=lambda: self.add_finish_from_source('paint', 'rooms'), style='Accent.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(paint_btns, text="📐 Room Walls", command=lambda: self.add_walls_from_rooms('paint'), style='Accent.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(paint_btns, text="🧱 Wall Net", command=lambda: self.add_finish_from_source('paint', 'walls'), style='Secondary.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(paint_btns, text="✍️ Manual", command=lambda: self.add_finish_manual('paint'), style='Secondary.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(paint_btns, text="➖ Deduct", command=lambda: self.deduct_ceramic_from_finish('paint'), style='Warning.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(paint_btns, text="✏️ Edit", command=lambda: self.edit_finish_item('paint'), style='Secondary.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(paint_btns, text="🗑️ Del", command=lambda: self.delete_finish_item('paint'), style='Danger.TButton').pack(side=tk.LEFT, padx=3)
        
        # Paint details table
        self.paint_tree = ttk.Treeview(paint_frame, columns=('Description', 'Area'), show='headings', height=4)
        self.paint_tree.heading('Description', text='Description')
        self.paint_tree.heading('Area', text='Area (m²)')
        self.paint_tree.column('Description', width=400)
        self.paint_tree.column('Area', width=120, anchor=tk.CENTER)
        ttk.Scrollbar(paint_frame, orient=tk.VERTICAL, command=self.paint_tree.yview).pack(side=tk.RIGHT, fill=tk.Y)
        self.paint_tree.pack(fill=tk.BOTH, expand=True)
        
        self.paint_label = ttk.Label(paint_frame, text="Total = 0.00 m²", style='Metrics.TLabel')
        self.paint_label.pack(anchor=tk.W, pady=(8, 0))
        
        # Tiles
        tiles_frame = ttk.LabelFrame(parent, text="🟦 TILES / بلاط", style='Card.TLabelframe', padding=(12, 10))
        tiles_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        
        tiles_btns = ttk.Frame(tiles_frame, style='Main.TFrame')
        tiles_btns.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(tiles_btns, text="➕ Room Areas", command=lambda: self.add_finish_from_source('tiles', 'rooms'), style='Accent.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(tiles_btns, text="📐 Room Walls", command=lambda: self.add_walls_from_rooms('tiles'), style='Accent.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(tiles_btns, text="🧱 Wall Net", command=lambda: self.add_finish_from_source('tiles', 'walls'), style='Secondary.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(tiles_btns, text="✍️ Manual", command=lambda: self.add_finish_manual('tiles'), style='Secondary.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(tiles_btns, text="➖ Deduct", command=lambda: self.deduct_ceramic_from_finish('tiles'), style='Warning.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(tiles_btns, text="✏️ Edit", command=lambda: self.edit_finish_item('tiles'), style='Secondary.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(tiles_btns, text="🗑️ Del", command=lambda: self.delete_finish_item('tiles'), style='Danger.TButton').pack(side=tk.LEFT, padx=3)
        
        # Tiles details table
        self.tiles_tree = ttk.Treeview(tiles_frame, columns=('Description', 'Area'), show='headings', height=4)
        self.tiles_tree.heading('Description', text='Description')
        self.tiles_tree.heading('Area', text='Area (m²)')
        self.tiles_tree.column('Description', width=400)
        self.tiles_tree.column('Area', width=120, anchor=tk.CENTER)
        ttk.Scrollbar(tiles_frame, orient=tk.VERTICAL, command=self.tiles_tree.yview).pack(side=tk.RIGHT, fill=tk.Y)
        self.tiles_tree.pack(fill=tk.BOTH, expand=True)
        
        self.tiles_label = ttk.Label(tiles_frame, text="Total = 0.00 m²", style='Metrics.TLabel')
        self.tiles_label.pack(anchor=tk.W, pady=(8, 0))

    def create_materials_tab(self, parent):
        """Stone, weight, and ceramic metrics"""
        parent.configure(bg=self.colors['bg_secondary'])

        hero = ttk.Frame(parent, style='Hero.TFrame', padding=(18, 20))
        hero.pack(fill=tk.X, padx=16, pady=(16, 12))
        ttk.Label(hero,
                  text="Material Intelligence Dashboard",
                  style='HeroHeading.TLabel').pack(anchor=tk.W)
        ttk.Label(hero,
                  text="تابع حساب حجر الملابن، أوزان الأبواب الحديد، ومساحات سيراميك مطبخك وحماماتك في مكان واحد",
                  style='HeroSubheading.TLabel').pack(anchor=tk.W, pady=(6, 0))

        stone_frame = ttk.LabelFrame(parent, text="🪨 Stone & Steel Ledger / ملخص الحجر والحديد", style='Card.TLabelframe', padding=(14, 12))
        stone_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 10))

        self.stone_tree = ttk.Treeview(stone_frame,
                                       columns=(
                                           'Name', 'Kind', 'Type', 'Qty', 'Stone', 'Area', 'Weight'
                                       ),
                                       show='headings',
                                       height=7)
        self.stone_tree.column('Name', width=110, anchor=tk.W)
        self.stone_tree.column('Kind', width=90, anchor=tk.CENTER)
        self.stone_tree.column('Type', width=120, anchor=tk.W)
        self.stone_tree.column('Qty', width=70, anchor=tk.CENTER)
        self.stone_tree.column('Stone', width=110, anchor=tk.CENTER)
        self.stone_tree.column('Area', width=110, anchor=tk.CENTER)
        self.stone_tree.column('Weight', width=110, anchor=tk.CENTER)
        for col, text in [
            ('Name', 'Name'),
            ('Kind', 'Kind'),
            ('Type', 'Type'),
            ('Qty', 'Qty'),
            ('Stone', 'Stone (lm)'),
            ('Area', 'Area (m²)'),
            ('Weight', 'Steel (kg)')
        ]:
            self.stone_tree.heading(col, text=text)

        stone_scroll = ttk.Scrollbar(stone_frame, orient=tk.VERTICAL, command=self.stone_tree.yview)
        self.stone_tree.configure(yscrollcommand=stone_scroll.set)
        stone_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.stone_tree.pack(fill=tk.BOTH, expand=True)

        self.stone_metrics_label = ttk.Label(stone_frame,
                                             text="Stone totals ready",
                                             style='Metrics.TLabel')
        self.stone_metrics_label.pack(anchor=tk.W, pady=(8, 0))

        ceramic_frame = ttk.LabelFrame(parent, text="🧼 Kitchen & Bath Ceramic Planner / حساب سيراميك الحوائط", style='Card.TLabelframe', padding=(14, 12))
        ceramic_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        btn_bar = ttk.Frame(ceramic_frame, style='Main.TFrame')
        btn_bar.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_bar, text="➕ Add Zone", command=self.add_ceramic_zone, style='Accent.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text="✏️ Edit", command=self.edit_ceramic_zone, style='Secondary.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text="🗑️ Delete", command=self.delete_ceramic_zone, style='Danger.TButton').pack(side=tk.LEFT, padx=4)

        self.ceramic_tree = ttk.Treeview(ceramic_frame,
                                         columns=('Name', 'Category', 'Perimeter', 'Height', 'Area', 'Notes'),
                                         show='headings',
                                         height=6)
        for col, text, width, anchor in [
            ('Name', 'Zone', 140, tk.W),
            ('Category', 'Category', 110, tk.CENTER),
            ('Perimeter', 'Perimeter (m)', 120, tk.CENTER),
            ('Height', 'Tile Height (m)', 130, tk.CENTER),
            ('Area', 'Area (m²)', 110, tk.CENTER),
            ('Notes', 'Notes', 200, tk.W)
        ]:
            self.ceramic_tree.heading(col, text=text)
            self.ceramic_tree.column(col, width=width, anchor=anchor)

        ceramic_scroll = ttk.Scrollbar(ceramic_frame, orient=tk.VERTICAL, command=self.ceramic_tree.yview)
        self.ceramic_tree.configure(yscrollcommand=ceramic_scroll.set)
        ceramic_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.ceramic_tree.pack(fill=tk.BOTH, expand=True)

        self.ceramic_totals_label = ttk.Label(ceramic_frame,
                                             text="No ceramic zones yet",
                                             style='Metrics.TLabel')
        self.ceramic_totals_label.pack(anchor=tk.W, pady=(8, 0))

    # === MATERIALS CONTROLS ===

    def refresh_materials_tab(self):
        """Refresh stone/weight table and ceramic metrics."""
        if hasattr(self, 'stone_tree'):
            for item in self.stone_tree.get_children():
                self.stone_tree.delete(item)

            doors_stone = 0.0
            windows_stone = 0.0
            steel_weight = 0.0
            door_area = 0.0
            window_glass = 0.0

            for door in self.doors:
                self.stone_tree.insert('', tk.END, values=(
                    door.get('name', '-'),
                    'Door',
                    door.get('type', '-'),
                    door.get('qty', 1),
                    self._fmt(door.get('stone')),
                    self._fmt(door.get('area')),
                    self._fmt(door.get('weight'), digits=1)
                ))
                doors_stone += float(door.get('stone', 0) or 0)
                door_area += float(door.get('area', 0) or 0)
                steel_weight += float(door.get('weight', 0) or 0)

            for window in self.windows:
                self.stone_tree.insert('', tk.END, values=(
                    window.get('name', '-'),
                    'Window',
                    window.get('type', '-'),
                    window.get('qty', 1),
                    self._fmt(window.get('stone')),
                    self._fmt(window.get('area')),
                    '-'
                ))
                windows_stone += float(window.get('stone', 0) or 0)
                window_glass += float(window.get('glass', 0) or 0)

            metrics = (
                f"Doors stone: {doors_stone:.2f} lm • Windows stone: {windows_stone:.2f} lm"
                f" • Steel weight: {steel_weight:.1f} kg • Door area: {door_area:.2f} m²"
            )
            if window_glass > 0:
                metrics += f" • Glass area: {window_glass:.2f} m²"
            self.stone_metrics_label.config(text=metrics)

        self.refresh_ceramic_zones()

    def refresh_ceramic_zones(self):
        """Refresh ceramic planner table."""
        if not hasattr(self, 'ceramic_tree'):
            return

        for item in self.ceramic_tree.get_children():
            self.ceramic_tree.delete(item)

        totals = {'Kitchen': 0.0, 'Bathroom': 0.0, 'Other': 0.0}
        for zone in self.ceramic_zones:
            category = zone.get('category', 'Other')
            area = float(zone.get('area', 0) or 0)
            totals.setdefault(category, 0.0)
            totals[category] += area
            self.ceramic_tree.insert('', tk.END, values=(
                zone.get('name', '-'),
                category,
                self._fmt(zone.get('perimeter')),
                self._fmt(zone.get('height')),
                self._fmt(area),
                zone.get('notes', '')
            ))

        total_area = sum(totals.values())
        kitchen = totals.get('Kitchen', 0.0)
        bathroom = totals.get('Bathroom', 0.0)
        other = total_area - kitchen - bathroom
        summary = (
            f"Kitchen: {kitchen:.2f} m² • Bathroom: {bathroom:.2f} m²"
        )
        if other > 0:
            summary += f" • Other: {other:.2f} m²"
        summary += f" • Total ceramic: {total_area:.2f} m²"
        self.ceramic_totals_label.config(text=summary if self.ceramic_zones else "No ceramic zones yet")

    def _ceramic_zone_dialog(self, title, defaults=None):
        """Enhanced dialog for ceramic zone input with modern styling"""
        defaults = defaults or {}
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("480x320")
        dialog.configure(bg=self.colors['bg_primary'])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog and ensure it appears on top
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (480 // 2)
        y = (dialog.winfo_screenheight() // 2) - (320 // 2)
        dialog.geometry(f"480x320+{x}+{y}")
        dialog.lift()
        dialog.attributes('-topmost', True)
        dialog.after(200, lambda: dialog.attributes('-topmost', False))

        frame = ttk.Frame(dialog, style='Main.TFrame', padding=(18, 16))
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Zone name", foreground=self.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=(0, 8))
        name_var = tk.StringVar(value=defaults.get('name', ''))
        ttk.Entry(frame, textvariable=name_var, width=28).grid(row=0, column=1, sticky='w', pady=(0, 8))

        ttk.Label(frame, text="Category", foreground=self.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=6)
        category_var = tk.StringVar(value=defaults.get('category', 'Kitchen'))
        category_combo = ttk.Combobox(frame,
                                      textvariable=category_var,
                                      values=('Kitchen', 'Bathroom', 'Other'),
                                      state='readonly',
                                      width=25)
        category_combo.grid(row=1, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Wall perimeter (m)", foreground=self.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=6)
        perimeter_var = tk.StringVar(value=str(defaults.get('perimeter', '')))
        ttk.Entry(frame, textvariable=perimeter_var, width=18).grid(row=2, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Tile height (m)", foreground=self.colors['text_secondary']).grid(row=3, column=0, sticky='w', pady=6)
        height_var = tk.StringVar(value=str(defaults.get('height', '')))
        ttk.Entry(frame, textvariable=height_var, width=18).grid(row=3, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Notes", foreground=self.colors['text_secondary']).grid(row=4, column=0, sticky='nw', pady=6)
        notes_var = tk.StringVar(value=defaults.get('notes', ''))
        ttk.Entry(frame, textvariable=notes_var, width=28).grid(row=4, column=1, sticky='w', pady=6)

        result = {}

        def save():
            try:
                name = name_var.get().strip() or 'Ceramic Zone'
                perimeter = float(perimeter_var.get())
                height = float(height_var.get())
                if perimeter <= 0 or height <= 0:
                    raise ValueError
                area = perimeter * height
                result.update({
                    'name': name,
                    'category': category_var.get(),
                    'perimeter': perimeter,
                    'height': height,
                    'area': area,
                    'notes': notes_var.get().strip()
                })
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Perimeter and height must be positive numbers")

        button_bar = ttk.Frame(dialog, style='Main.TFrame', padding=(18, 10))
        button_bar.pack(fill=tk.X)
        ttk.Button(button_bar, text="Save", command=save, style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)

        dialog.wait_window()
        return result if result else None

    def add_ceramic_zone(self):
        zone = self._ceramic_zone_dialog("Add ceramic zone")
        if zone:
            self.ceramic_zones.append(zone)
            self.refresh_materials_tab()
            self.update_summary()
            self.update_status(f"Added ceramic zone: {zone.get('name', '-')}", icon="🧼")

    def edit_ceramic_zone(self):
        if not hasattr(self, 'ceramic_tree'):
            return
        selection = self.ceramic_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a ceramic zone to edit")
            return
        idx = self.ceramic_tree.index(selection[0])
        zone = self.ceramic_zones[idx]
        updated = self._ceramic_zone_dialog("Edit ceramic zone", defaults=zone)
        if updated:
            self.ceramic_zones[idx] = updated
            self.refresh_materials_tab()
            self.update_summary()
            self.update_status(f"Updated ceramic zone: {updated.get('name', '-')}", icon="🧼")

    def delete_ceramic_zone(self):
        if not hasattr(self, 'ceramic_tree'):
            return
        selection = self.ceramic_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a ceramic zone to delete")
            return
        if not messagebox.askyesno("Delete", "Delete selected ceramic zone?"):
            return
        idx = self.ceramic_tree.index(selection[0])
        del self.ceramic_zones[idx]
        self.refresh_materials_tab()
        self.update_summary()
        self.update_status("Deleted ceramic zone", icon="🧼")
    
    def create_summary_tab(self, parent):
        """Summary workspace with unified styling."""
        parent.configure(bg=self.colors['bg_secondary'])

        hero = ttk.Frame(parent, style='Hero.TFrame', padding=(18, 20))
        hero.pack(fill=tk.X, padx=16, pady=(16, 12))
        ttk.Label(hero,
                  text="Project Summary & Exports",
                  style='HeroHeading.TLabel').pack(anchor=tk.W)
        ttk.Label(hero,
                  text="أنشئ ملخص المواد المفصل، انسخه أو صدره بلمسة واحدة، مع نسق داكن أنيق",
                  style='HeroSubheading.TLabel').pack(anchor=tk.W, pady=(6, 0))

        toolbar = ttk.Frame(parent, style='Toolbar.TFrame', padding=(12, 10))
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 12))

        ttk.Button(toolbar, text="🔄 Refresh", command=self.update_summary, style='Accent.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="📋 Copy", command=self.copy_summary, style='Secondary.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="💾 Export CSV", command=self.export_csv, style='Accent.TButton').pack(side=tk.LEFT, padx=4)

        text_frame = ttk.Frame(parent, style='Main.TFrame', padding=(12, 10))
        text_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        self.summary_text = scrolledtext.ScrolledText(text_frame,
                                                      width=92,
                                                      height=28,
                                                      font=('Consolas', 10),
                                                      wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text.configure(
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_light'],
            insertbackground=self.colors['accent'],
            relief='flat',
            borderwidth=0,
            padx=10,
            pady=10
        )

        ttk.Label(parent,
                  text="💡 استخدم Refresh لتحديث الأرقام فوراً بعد أي تعديل",
                  style='Caption.TLabel').pack(anchor=tk.W, padx=18, pady=(0, 18))
    
    # === PICKING FUNCTIONS ===
    
    def pick_rooms(self):
        """Pick rooms from AutoCAD"""
        self.update_scale()
        self.update_status("Picking rooms from AutoCAD...", icon="🏠")
        self.root.withdraw()
        
        try:
            # Delete old selection sets
            self._delete_all_selections()
            
            # Prompt user
            print("\n=== Selecting ROOMS ===")
            self.acad.prompt("Select ROOMS (closed polylines/hatches):")
            
            # Create selection set
            ss = self.doc.SelectionSets.Add("BILIND_ROOMS")
            ss.SelectOnScreen()
            
            count = 0
            print(f"Processing {ss.Count} objects...")
            
            for i in range(ss.Count):
                try:
                    obj = ss.Item(i)
                    
                    # Get Area - REQUIRED
                    try:
                        area = float(obj.Area)
                    except:
                        print(f"Object {i}: No Area property")
                        continue
                    
                    if area <= 0.0001:
                        print(f"Object {i}: Area too small: {area}")
                        continue
                    
                    # Get other properties
                    try:
                        perim = float(obj.Length)
                    except:
                        perim = 0.0
                    
                    try:
                        layer = str(obj.Layer)
                    except:
                        layer = "Unknown"
                    
                    # Get BoundingBox for W×L - طريقة محسّنة
                    w_str, l_str = "-", "-"
                    w_value = None
                    l_value = None
                    w_du = l_du = 0.0
                    
                    # محاولة 1: استخدام VARIANT (الطريقة الأحدث)
                    try:
                        min_variant = win32com.client.VARIANT(
                            pythoncom.VT_ARRAY | pythoncom.VT_R8,
                            (0.0, 0.0, 0.0)
                        )
                        max_variant = win32com.client.VARIANT(
                            pythoncom.VT_ARRAY | pythoncom.VT_R8,
                            (0.0, 0.0, 0.0)
                        )
                        obj.GetBoundingBox(min_variant, max_variant)
                        
                        minPt = min_variant.value
                        maxPt = max_variant.value
                        
                        if minPt and maxPt and len(minPt) >= 2 and len(maxPt) >= 2:
                            w_du = abs(float(maxPt[0]) - float(minPt[0]))
                            l_du = abs(float(maxPt[1]) - float(minPt[1]))
                            print(f"Object {i}: VARIANT BBox W={w_du:.4f}, L={l_du:.4f}")
                    except Exception as e:
                        print(f"Object {i}: VARIANT failed: {e}")
                        
                        # محاولة 2: استخدام طريقة قديمة كـ fallback
                        try:
                            minPt = [0.0, 0.0, 0.0]
                            maxPt = [0.0, 0.0, 0.0]
                            obj.GetBoundingBox(minPt, maxPt)
                            w_du = abs(float(maxPt[0]) - float(minPt[0]))
                            l_du = abs(float(maxPt[1]) - float(minPt[1]))
                            print(f"Object {i}: Array BBox W={w_du:.4f}, L={l_du:.4f}")
                        except Exception as e2:
                            print(f"Object {i}: Array also failed: {e2}")
                    
                    # تحويل الأبعاد إلى strings
                    if w_du > 0.001 and l_du > 0.001:
                        w = w_du * self.scale
                        l = l_du * self.scale
                        w_value = w
                        l_value = l
                        w_str = f"{w:.2f}"
                        l_str = f"{l:.2f}"
                        print(f"Object {i}: ✅ W={w_str}m L={l_str}m Area={area * self.scale * self.scale:.2f}m²")
                    else:
                        # محاولة حساب تقريبي من المحيط والمساحة
                        if perim > 0.001 and area > 0.001:
                            # تقدير تقريبي: للمستطيل P = 2(W+L) و A = W*L
                            # حل معادلة تربيعية تقريبية
                            p_scaled = perim * self.scale / 2  # W + L
                            a_scaled = area * self.scale * self.scale
                            
                            # تقدير بسيط: افترض مربع أو مستطيل قريب
                            try:
                                import math
                                # حل: W*L = A و W+L = P/2
                                # W = (P/2 ± sqrt((P/2)² - 4A))/2
                                discriminant = (p_scaled ** 2) - (4 * a_scaled)
                                if discriminant >= 0:
                                    w = (p_scaled + math.sqrt(discriminant)) / 2
                                    l = a_scaled / w if w > 0.001 else 0
                                    if w > 0.001 and l > 0.001:
                                        w_value = w
                                        l_value = l
                                        w_str = f"{w:.2f}"
                                        l_str = f"{l:.2f}"
                                        print(f"Object {i}: ✅ Estimated W={w_str}m L={l_str}m from Perim+Area")
                            except:
                                pass
                        
                        if w_str == "-":
                            print(f"Object {i}: ⚠️ Could not determine W×L (showing Area only)")
                    
                    self.rooms.append({
                        'name': f"Room{len(self.rooms) + 1}",
                        'layer': layer,
                        'w': w_value,
                        'l': l_value,
                        'perim': perim * self.scale,
                        'area': area * self.scale * self.scale
                    })
                    count += 1
                    
                except Exception as e:
                    print(f"Object {i}: Error: {e}")
                    continue
            
            ss.Delete()
            self.refresh_rooms()
            
            if count > 0:
                messagebox.showinfo("Success", f"✅ Added {count} room(s)")
                self.update_status(f"Added {count} room(s)", icon="🏠")
            else:
                messagebox.showwarning("Warning", "No valid rooms!\n\nMake sure you select:\n- Closed POLYLINES\n- HATCHES\n- REGIONS")
                self.update_status("No valid rooms detected", icon="⚠️")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
        finally:
            self.root.deiconify()
    
    def pick_doors(self):
        """Count doors and add with batch settings"""
        self.update_status("Counting doors from AutoCAD...", icon="🚪")
        self.root.withdraw()
        try:
            self._delete_all_selections()
            
            print("\n=== Counting DOORS ===")
            self.acad.prompt("Select DOORS (any blocks):")
            
            ss = self.doc.SelectionSets.Add(f"BILIND_DOORS_{int(time.time() * 1000) % 100000}")
            ss.SelectOnScreen()
            
            count = ss.Count
            ss.Delete()
            
            self.root.deiconify()
            
            if count > 0:
                # Ask how many to actually add
                result = messagebox.askquestion(
                    "Doors Found", 
                    f"Found {count} door(s) in selection.\n\nAdd all {count} doors?",
                    icon='question'
                )
                
                if result == 'yes':
                    actual_count = count
                else:
                    actual_count = simpledialog.askinteger(
                        "How Many?",
                        f"Found {count} door(s).\nHow many do you want to add?",
                        initialvalue=count,
                        minvalue=1,
                        maxvalue=count
                    )
                    if not actual_count:
                        return
                
                # Get batch settings
                self.add_openings_batch('DOOR', actual_count)
            else:
                messagebox.showwarning("Warning", "No doors selected!")
                self.update_status("No doors selected", icon="⚠️")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.root.deiconify()
    
    def pick_windows(self):
        """Count windows and add with batch settings"""
        self.update_status("Counting windows from AutoCAD...", icon="🪟")
        self.root.withdraw()
        try:
            self._delete_all_selections()
            
            print("\n=== Counting WINDOWS ===")
            self.acad.prompt("Select WINDOWS (any blocks):")
            
            ss = self.doc.SelectionSets.Add(f"BILIND_WINDOWS_{int(time.time() * 1000) % 100000}")
            ss.SelectOnScreen()
            
            count = ss.Count
            ss.Delete()
            
            self.root.deiconify()
            
            if count > 0:
                # Ask how many to actually add
                result = messagebox.askquestion(
                    "Windows Found", 
                    f"Found {count} window(s) in selection.\n\nAdd all {count} windows?",
                    icon='question'
                )
                
                if result == 'yes':
                    actual_count = count
                else:
                    actual_count = simpledialog.askinteger(
                        "How Many?",
                        f"Found {count} window(s).\nHow many do you want to add?",
                        initialvalue=count,
                        minvalue=1,
                        maxvalue=count
                    )
                    if not actual_count:
                        return
                
                # Get batch settings
                self.add_openings_batch('WINDOW', actual_count)
            else:
                messagebox.showwarning("Warning", "No windows selected!")
                self.update_status("No windows selected", icon="⚠️")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.root.deiconify()
    
    def add_openings_batch(self, opening_type, count):
        """Add multiple doors/windows with shared settings and preview."""
        type_catalog = self.door_types if opening_type == 'DOOR' else self.window_types
        prefix_default = 'D' if opening_type == 'DOOR' else 'W'

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Add {count} {opening_type.title()}(s)")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        header = ttk.Frame(dialog, padding=(18, 16), style='Main.TFrame')
        header.pack(fill=tk.X)
        ttk.Label(header,
                  text=f"📦 Batch add {count} {opening_type.lower()}(s)",
                  font=('Segoe UI Semibold', 14),
                  foreground=self.colors['accent']).pack(anchor=tk.W)

        body = ttk.Frame(dialog, padding=(18, 10), style='Main.TFrame')
        body.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(body, text="Name prefix", foreground=self.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=(0, 6))
        name_var = tk.StringVar(value=prefix_default)
        ttk.Entry(body, textvariable=name_var, width=18).grid(row=row, column=1, sticky='w', pady=(0, 6))
        row += 1

        ttk.Label(body, text="Layer", foreground=self.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        layer_default = 'Door' if opening_type == 'DOOR' else 'Window'
        layer_var = tk.StringVar(value=layer_default)
        ttk.Entry(body, textvariable=layer_var, width=18).grid(row=row, column=1, sticky='w', pady=6)
        row += 1

        ttk.Label(body, text="Type", foreground=self.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        type_var = tk.StringVar(value=list(type_catalog.keys())[0])
        type_combo = ttk.Combobox(body, textvariable=type_var, values=list(type_catalog.keys()), state='readonly', width=20)
        type_combo.grid(row=row, column=1, sticky='w', pady=6)
        info_var = tk.StringVar()
        info_label = ttk.Label(body, textvariable=info_var, wraplength=260, foreground=self.colors['text_secondary'])
        info_label.grid(row=row, column=2, sticky='w', padx=12, pady=6)
        row += 1

        ttk.Label(body, text="Width (m)", foreground=self.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        w_var = tk.StringVar(value="0.9" if opening_type == 'DOOR' else "1.2")
        ttk.Entry(body, textvariable=w_var, width=12).grid(row=row, column=1, sticky='w', pady=6)
        row += 1

        ttk.Label(body, text="Height (m)", foreground=self.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        h_var = tk.StringVar(value="2.1" if opening_type == 'DOOR' else "1.5")
        ttk.Entry(body, textvariable=h_var, width=12).grid(row=row, column=1, sticky='w', pady=6)
        row += 1

        ttk.Label(body, text="Qty (per item)", foreground=self.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        qty_var = tk.StringVar(value="1")
        ttk.Entry(body, textvariable=qty_var, width=12).grid(row=row, column=1, sticky='w', pady=6)
        row += 1

        weight_var = tk.StringVar(value=str(self.door_types.get(type_var.get(), {}).get('weight', 0))) if opening_type == 'DOOR' else None
        weight_entry = None
        weight_hint = None
        if opening_type == 'DOOR':
            ttk.Label(body, text="Weight (kg each)", foreground=self.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
            weight_entry = ttk.Entry(body, textvariable=weight_var, width=12)
            weight_entry.grid(row=row, column=1, sticky='w', pady=6)
            weight_hint = ttk.Label(body, text="", foreground=self.colors['warning'])
            weight_hint.grid(row=row, column=2, sticky='w', padx=12)
            row += 1

        preview_var = tk.StringVar(value="Preview: enter width, height, qty")
        preview_label = ttk.Label(body, textvariable=preview_var, foreground=self.colors['accent'], font=('Segoe UI', 10, 'italic'))
        preview_label.grid(row=row, column=0, columnspan=3, sticky='w', pady=(10, 4))
        row += 1

        ttk.Separator(body, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
        row += 1

        apply_var = tk.StringVar(value='all')
        ttk.Label(body, text="Apply mode", foreground=self.colors['text_secondary']).grid(row=row, column=0, sticky='w')
        row += 1

        ttk.Radiobutton(body, text=f"Apply to all {count} items", variable=apply_var, value='all').grid(row=row, column=0, columnspan=2, sticky='w', pady=3)
        row += 1
        ttk.Radiobutton(body, text="Customize each item", variable=apply_var, value='individual').grid(row=row, column=0, columnspan=2, sticky='w', pady=3)
        row += 1

        def update_type_details(*_):
            info = type_catalog.get(type_var.get(), {})
            info_var.set(info.get('description', ''))
            if opening_type == 'DOOR' and weight_var is not None:
                default_weight = info.get('weight', 0)
                if default_weight > 0:
                    weight_var.set(str(default_weight))
                    if weight_hint:
                        weight_hint.config(text="")
                else:
                    if weight_hint:
                        if info.get('material', '').lower() in ('steel', 'metal'):
                            weight_hint.config(text="⚠️ Enter actual steel weight")
                        else:
                            weight_hint.config(text="")

        def update_preview(*_):
            try:
                w_val = float(w_var.get())
                h_val = float(h_var.get())
                qty_val = max(1, int(qty_var.get()))
                perim_each = 2 * (w_val + h_val)
                area_each = w_val * h_val
                stone_total = perim_each * qty_val
                glass_total = area_each * 0.85 * qty_val if opening_type == 'WINDOW' else None
                preview = f"Perim each: {perim_each:.2f} m • Total stone: {stone_total:.2f} lm • Area total: {area_each * qty_val:.2f} m²"
                if glass_total is not None:
                    preview += f" • Glass total: {glass_total:.2f} m²"
                preview_var.set(preview)
            except Exception:
                preview_var.set("Preview: enter valid numbers for width, height, qty")

        type_combo.bind('<<ComboboxSelected>>', update_type_details)
        for var in (w_var, h_var, qty_var):
            var.trace_add('write', update_preview)
        update_type_details()
        update_preview()

        def save():
            try:
                prefix = name_var.get().strip() or prefix_default
                type_name = type_var.get()
                width = float(w_var.get())
                height = float(h_var.get())
                qty = max(1, int(qty_var.get()))
                weight = float(weight_var.get()) if weight_var is not None else 0.0
                layer = layer_var.get().strip() or ("Door" if opening_type == 'DOOR' else "Window")

                if width <= 0 or height <= 0:
                    raise ValueError("Width and height must be positive")

                storage = self._opening_storage(opening_type)

                if apply_var.get() == 'all':
                    base_len = len(storage)
                    for idx in range(count):
                        base_name = f"{prefix}{base_len + idx + 1}"
                        name = self._make_unique_name(opening_type, base_name)
                        record = self._build_opening_record(opening_type, name, type_name, width, height, qty, weight, layer=layer)
                        storage.append(record)

                    self.refresh_openings()
                    dialog.destroy()
                    messagebox.showinfo("Success", f"✅ Added {count} {opening_type.lower()}(s)")
                    icon = "🚪" if opening_type == 'DOOR' else "🪟"
                    self.update_status(f"Added {count} {opening_type.lower()}(s)", icon=icon)
                else:
                    dialog.destroy()
                    for idx in range(count):
                        defaults = {
                            'from_batch': True,
                            'name_prefix': prefix,
                            'type': type_name,
                            'width': width,
                            'height': height,
                            'qty': qty,
                            'weight': weight,
                            'layer': layer
                        }
                        self.add_opening_manual(opening_type, defaults=defaults)
                    icon = "🚪" if opening_type == 'DOOR' else "🪟"
                    self.update_status(f"Batch customization complete ({count} items)", icon=icon)

            except ValueError as exc:
                messagebox.showerror("Error", f"Invalid input: {exc}")

        btn_bar = ttk.Frame(dialog, padding=(18, 14), style='Main.TFrame')
        btn_bar.pack(fill=tk.X)
        ttk.Button(btn_bar, text="✓ Apply", command=save, style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(btn_bar, text="Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)

        dialog.wait_window()
    
    def add_opening_manual(self, opening_type, number=None, defaults=None):
        """Add a single door/window with full customization."""
        type_catalog = self.door_types if opening_type == 'DOOR' else self.window_types
        storage = self._opening_storage(opening_type)

        defaults = defaults or {}
        prefix = defaults.get('name_prefix') or ('D' if opening_type == 'DOOR' else 'W')
        suggested_name = defaults.get('name') or self._make_unique_name(opening_type, f"{prefix}{len(storage)+1}")
        type_default = defaults.get('type') or list(type_catalog.keys())[0]
        layer_default = defaults.get('layer') or ('Door' if opening_type == 'DOOR' else 'Window')
        width_default = defaults.get('width') or (0.9 if opening_type == 'DOOR' else 1.2)
        height_default = defaults.get('height') or (2.1 if opening_type == 'DOOR' else 1.5)
        qty_default = defaults.get('qty') or 1
        if opening_type == 'DOOR':
            weight_default = defaults.get('weight') if defaults.get('weight') is not None else type_catalog.get(type_default, {}).get('weight', 0)
        else:
            weight_default = 0
        title = f"Customize {opening_type.title()}" if number is None else f"Customize {opening_type.title()} #{number}"

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=(18, 14), style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Name", foreground=self.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=(0, 6))
        name_var = tk.StringVar(value=suggested_name)
        ttk.Entry(frame, textvariable=name_var, width=20).grid(row=0, column=1, sticky='w', pady=(0, 6))

        ttk.Label(frame, text="Layer", foreground=self.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=6)
        layer_var = tk.StringVar(value=layer_default)
        ttk.Entry(frame, textvariable=layer_var, width=20).grid(row=1, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Type", foreground=self.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=6)
        type_var = tk.StringVar(value=type_default)
        type_combo = ttk.Combobox(frame, textvariable=type_var, values=list(type_catalog.keys()), state='readonly', width=22)
        type_combo.grid(row=2, column=1, sticky='w', pady=6)

        info_var = tk.StringVar(value=type_catalog.get(type_var.get(), {}).get('description', ''))
        info_label = ttk.Label(frame, textvariable=info_var, wraplength=240, foreground=self.colors['text_secondary'])
        info_label.grid(row=2, column=2, sticky='w', padx=12, pady=6)

        ttk.Label(frame, text="Width (m)", foreground=self.colors['text_secondary']).grid(row=3, column=0, sticky='w', pady=6)
        w_var = tk.StringVar(value=f"{width_default}")
        ttk.Entry(frame, textvariable=w_var, width=12).grid(row=3, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Height (m)", foreground=self.colors['text_secondary']).grid(row=4, column=0, sticky='w', pady=6)
        h_var = tk.StringVar(value=f"{height_default}")
        ttk.Entry(frame, textvariable=h_var, width=12).grid(row=4, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Quantity", foreground=self.colors['text_secondary']).grid(row=5, column=0, sticky='w', pady=6)
        qty_var = tk.StringVar(value=str(qty_default))
        ttk.Entry(frame, textvariable=qty_var, width=12).grid(row=5, column=1, sticky='w', pady=6)

        weight_var = tk.StringVar(value=f"{weight_default}") if opening_type == 'DOOR' else None
        weight_hint = None
        if opening_type == 'DOOR':
            ttk.Label(frame, text="Weight (kg each)", foreground=self.colors['text_secondary']).grid(row=6, column=0, sticky='w', pady=6)
            weight_entry = ttk.Entry(frame, textvariable=weight_var, width=12)
            weight_entry.grid(row=6, column=1, sticky='w', pady=6)
            weight_hint = ttk.Label(frame, text="", foreground=self.colors['warning'])
            weight_hint.grid(row=6, column=2, sticky='w', padx=12)
            row_preview = 7
        else:
            row_preview = 6

        preview_var = tk.StringVar(value="Preview: adjust values")
        preview_label = ttk.Label(frame, textvariable=preview_var, foreground=self.colors['accent'], font=('Segoe UI', 10, 'italic'))
        preview_label.grid(row=row_preview, column=0, columnspan=3, sticky='w', pady=(10, 4))

        def update_type_info(*_):
            info = type_catalog.get(type_var.get(), {})
            info_var.set(info.get('description', ''))
            if opening_type == 'DOOR' and weight_var is not None:
                default_weight = info.get('weight', 0)
                if default_weight > 0 and not defaults.get('from_batch'):
                    weight_var.set(str(default_weight))
                if weight_hint:
                    if default_weight == 0 and info.get('material', '').lower() in ('steel', 'metal'):
                        weight_hint.config(text="⚠️ Enter actual steel weight")
                    else:
                        weight_hint.config(text="")

        def update_preview(*_):
            try:
                width = float(w_var.get())
                height = float(h_var.get())
                qty = max(1, int(qty_var.get()))
                perim_each = 2 * (width + height)
                area_each = width * height
                stone_total = perim_each * qty
                preview = f"Perim each: {perim_each:.2f} m • Stone total: {stone_total:.2f} lm"
                if opening_type == 'WINDOW':
                    glass_total = area_each * qty * 0.85
                    preview += f" • Glass total: {glass_total:.2f} m²"
                preview_var.set(preview)
            except Exception:
                preview_var.set("Preview: enter valid numeric values")

        type_combo.bind('<<ComboboxSelected>>', update_type_info)
        for var in (w_var, h_var, qty_var):
            var.trace_add('write', update_preview)
        update_type_info()
        update_preview()

        def save():
            try:
                name = name_var.get().strip() or suggested_name
                name = self._make_unique_name(opening_type, name)
                layer = layer_var.get().strip() or layer_default
                width = float(w_var.get())
                height = float(h_var.get())
                qty = max(1, int(qty_var.get()))
                weight = float(weight_var.get()) if weight_var is not None else 0.0

                if width <= 0 or height <= 0:
                    raise ValueError("Width and height must be positive")

                record = self._build_opening_record(opening_type, name, type_var.get(), width, height, qty, weight, layer=layer)
                storage.append(record)
                self.refresh_openings()
                dialog.destroy()
                icon = "🚪" if opening_type == 'DOOR' else "🪟"
                self.update_status(f"Added {opening_type.lower()} '{record.get('name', '-')}'", icon=icon)

            except ValueError as exc:
                messagebox.showerror("Error", f"Invalid input: {exc}")

        button_bar = ttk.Frame(dialog, padding=(18, 10), style='Main.TFrame')
        button_bar.pack(fill=tk.X)
        ttk.Button(button_bar, text="Save", command=save, style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)

        dialog.wait_window()
    
    def _pick_openings(self, name, storage, icon):
        """Generic opening picker"""
        opening_type = 'DOOR' if storage is self.doors else 'WINDOW'
        self.update_scale()
        self.root.withdraw()
        
        try:
            self._delete_all_selections()
            
            print(f"\n=== Selecting {name} ===")
            self.acad.prompt(f"Select {name} (BLOCKS only):")
            
            ss = self.doc.SelectionSets.Add(f"BILIND_{name}")
            ss.SelectOnScreen()
            
            count = 0
            print(f"Processing {ss.Count} objects...")
            
            for i in range(ss.Count):
                try:
                    block = ss.Item(i)
                    
                    # Check if it's a block reference
                    try:
                        obj_type = str(block.ObjectName)
                        if "BlockReference" not in obj_type:
                            print(f"Object {i}: Not a block ({obj_type})")
                            continue
                    except:
                        print(f"Object {i}: Can't get ObjectName")
                        continue
                    
                    # Get dimensions
                    w, h = None, None
                    
                    # PRIORITY 1: Try Dynamic Block Properties (most accurate)
                    try:
                        if hasattr(block, 'IsDynamicBlock') and block.IsDynamicBlock:
                            props = block.GetDynamicBlockProperties()
                            print(f"Object {i}: Found {len(props)} dynamic properties")
                            for prop in props:
                                try:
                                    prop_name = str(prop.PropertyName).upper()
                                    prop_value = prop.Value
                                    print(f"Object {i}: Property '{prop_name}' = {prop_value}")
                                    
                                    # قائمة موسّعة من الأسماء المحتملة
                                    if prop_name in ['WIDTH', 'W', 'DOOR WIDTH', 'WINDOW WIDTH', 'DOOR_WIDTH', 'WINDOW_WIDTH', 'DOORWIDTH', 'WINDOWWIDTH']:
                                        try:
                                            w = abs(float(prop_value))
                                            print(f"Object {i}: ✅ Got width from dynamic property: {w}")
                                        except:
                                            pass
                                    elif prop_name in ['HEIGHT', 'H', 'DOOR HEIGHT', 'WINDOW HEIGHT', 'DOOR_HEIGHT', 'WINDOW_HEIGHT', 'DOORHEIGHT', 'WINDOWHEIGHT']:
                                        try:
                                            h = abs(float(prop_value))
                                            print(f"Object {i}: ✅ Got height from dynamic property: {h}")
                                        except:
                                            pass
                                except Exception as e:
                                    print(f"Object {i}: Error reading property: {e}")
                                    continue
                        else:
                            print(f"Object {i}: Not a dynamic block")
                    except Exception as e:
                        print(f"Object {i}: No dynamic properties: {e}")
                    
                    # PRIORITY 2: Try attributes
                    if w is None or h is None:
                        try:
                            if block.HasAttributes:
                                attrs = block.GetAttributes()
                                for att in attrs:
                                    try:
                                        tag = str(att.TagString).upper()
                                        val = str(att.TextString)
                                        print(f"Object {i}: Attribute {tag}={val}")
                                        
                                        if (w is None or w <= 0.001) and tag in ['WIDTH', 'W']:
                                            try:
                                                w = abs(float(val))
                                                print(f"Object {i}: Got width from attribute: {w}")
                                            except:
                                                pass
                                        elif (h is None or h <= 0.001) and tag in ['HEIGHT', 'H']:
                                            try:
                                                h = abs(float(val))
                                                print(f"Object {i}: Got height from attribute: {h}")
                                            except:
                                                pass
                                    except:
                                        continue
                        except Exception as e:
                            print(f"Object {i}: No attributes: {e}")
                    
                    # PRIORITY 3: Get BoundingBox (fallback) - طريقة بسيطة بدون VARIANT
                    if w is None or h is None or w <= 0.001 or h <= 0.001:
                        bbox_w = bbox_h = None
                        try:
                            # استخدام الطريقة القديمة الموثوقة
                            minPt = [0.0, 0.0, 0.0]
                            maxPt = [0.0, 0.0, 0.0]
                            block.GetBoundingBox(minPt, maxPt)
                            
                            bbox_w = abs(maxPt[0] - minPt[0])
                            bbox_h = abs(maxPt[1] - minPt[1])
                            print(f"Object {i}: BBox W={bbox_w:.4f}, H={bbox_h:.4f}")
                            
                            if (w is None or w <= 0.001) and bbox_w and bbox_w > 0.001:
                                w = bbox_w
                                print(f"Object {i}: ✅ Using BBox width: {w}")
                            if (h is None or h <= 0.001) and bbox_h and bbox_h > 0.001:
                                h = bbox_h
                                print(f"Object {i}: ✅ Using BBox height: {h}")
                        except Exception as e:
                            print(f"Object {i}: BBox error: {e}")
                    
                    # PRIORITY 4: إذا فشل كل شيء، اقرأ من Block Definition مباشرة
                    if (w is None or w < 0.001) or (h is None or h < 0.001):
                        try:
                            # الحصول على اسم البلوك
                            if hasattr(block, 'EffectiveName'):
                                block_name = block.EffectiveName
                            elif hasattr(block, 'Name'):
                                block_name = block.Name
                            else:
                                block_name = "Unknown"
                            
                            print(f"Object {i}: Block name = '{block_name}', trying to read definition...")
                            
                            # قراءة Block Definition
                            try:
                                blocks = self.doc.Blocks
                                blk_def = None
                                
                                # البحث عن Block Definition
                                for j in range(blocks.Count):
                                    try:
                                        temp_blk = blocks.Item(j)
                                        if temp_blk.Name == block_name:
                                            blk_def = temp_blk
                                            break
                                    except:
                                        continue
                                
                                if blk_def and blk_def.Count > 0:
                                    print(f"Object {i}: Found block definition with {blk_def.Count} entities")
                                    
                                    # جمع أبعاد كل العناصر داخل البلوك
                                    min_x = min_y = float('inf')
                                    max_x = max_y = float('-inf')
                                    found_any = False
                                    
                                    for ent_idx in range(blk_def.Count):
                                        try:
                                            entity = blk_def.Item(ent_idx)
                                            if hasattr(entity, 'GetBoundingBox'):
                                                e_min = [0.0, 0.0, 0.0]
                                                e_max = [0.0, 0.0, 0.0]
                                                entity.GetBoundingBox(e_min, e_max)
                                                
                                                min_x = min(min_x, e_min[0])
                                                min_y = min(min_y, e_min[1])
                                                max_x = max(max_x, e_max[0])
                                                max_y = max(max_y, e_max[1])
                                                found_any = True
                                        except:
                                            continue
                                    
                                    if found_any:
                                        def_w = abs(max_x - min_x)
                                        def_h = abs(max_y - min_y)
                                        
                                        if def_w > 0.001 and def_h > 0.001:
                                            # تطبيق Scale من النسخة الفعلية
                                            x_scale = abs(float(block.XScaleFactor)) if hasattr(block, 'XScaleFactor') else 1.0
                                            y_scale = abs(float(block.YScaleFactor)) if hasattr(block, 'YScaleFactor') else 1.0
                                            
                                            w = def_w * x_scale
                                            h = def_h * y_scale
                                            print(f"Object {i}: ✅ Block def: {def_w:.4f}×{def_h:.4f} × scale({x_scale:.2f},{y_scale:.2f}) = {w:.4f}×{h:.4f}")
                                    else:
                                        print(f"Object {i}: No entities with BoundingBox in block definition")
                                else:
                                    print(f"Object {i}: Block definition '{block_name}' not found or empty")
                                    
                            except Exception as e:
                                print(f"Object {i}: Block definition read error: {e}")
                                    
                        except Exception as e:
                            print(f"Object {i}: Block processing error: {e}")
                    
                    # Validate dimensions
                    if w and h and w > 0.001 and h > 0.001:
                        try:
                            layer = str(block.Layer)
                        except:
                            layer = "Unknown"
                        
                        # Apply scale
                        w_scaled = w * self.scale
                        h_scaled = h * self.scale
                        
                        prefix = 'D' if opening_type == 'DOOR' else 'W'
                        base_name = f"{prefix}{len(storage)+1}"
                        type_label = None
                        try:
                            type_label = str(getattr(block, 'EffectiveName', '') or getattr(block, 'Name', '') or '')
                        except:
                            type_label = None
                        if not type_label:
                            type_label = 'AutoCAD Block'

                        record = self._build_opening_record(opening_type,
                                                            self._make_unique_name(opening_type, base_name),
                                                            type_label,
                                                            w_scaled,
                                                            h_scaled,
                                                            1,
                                                            0.0,
                                                            layer=layer)
                        storage.append(record)
                        count += 1
                        print(f"Object {i}: ✅ Added {w_scaled:.2f} x {h_scaled:.2f} m (Area={w_scaled * h_scaled:.2f} m²)")
                    else:
                        print(f"Object {i}: ❌ Invalid dimensions w={w}, h={h}")
                    
                except Exception as e:
                    print(f"Object {i}: Error: {e}")
                    continue
            
            ss.Delete()
            self.refresh_openings()
            
            if count > 0:
                messagebox.showinfo("Success", f"✅ Added {count} {name.lower()}")
            else:
                messagebox.showwarning("Warning", f"No valid {name.lower()}!\n\nMake sure you select:\n- BLOCK REFERENCES (INSERT)\n- Not lines or polylines!")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.root.deiconify()
    
    def pick_walls(self):
        """Pick walls - can add multiple times with different heights"""
        self.update_status("Picking walls from AutoCAD...", icon="🧱")
        self.root.deiconify()
        height = simpledialog.askfloat("Wall Height", "Enter wall height (m):", initialvalue=3.0)
        if not height or height <= 0:
            return
        
        self.update_scale()
        self.root.withdraw()
        
        try:
            self._delete_all_selections()
            
            print(f"\n=== Selecting WALLS (Height: {height}m) ===")
            self.acad.prompt(f"Select WALLS (lines/polylines) - Height: {height}m:")
            
            # Use timestamp for unique name
            sel_name = f"BILIND_WALL_{int(time.time() * 1000) % 100000}"
            ss = self.doc.SelectionSets.Add(sel_name)
            ss.SelectOnScreen()
            
            count = 0
            num_objects = ss.Count
            print(f"Processing {num_objects} objects...")
            
            # Use direct iteration instead of Item()
            for i, obj in enumerate(ss):
                try:
                    # Get Length - REQUIRED
                    try:
                        length_du = float(obj.Length)
                    except Exception as e:
                        print(f"Object {i}: No Length property - {e}")
                        continue
                    
                    if length_du <= 0.001:
                        print(f"Object {i}: Length too small: {length_du}")
                        continue
                    
                    length = length_du * self.scale
                    area = length * height
                    
                    try:
                        layer = str(obj.Layer)
                    except:
                        layer = "Unknown"
                    
                    self.walls.append({
                        'layer': layer,
                        'length': length,
                        'height': height,
                        'gross': area,
                        'deduct': 0,
                        'net': area
                    })
                    count += 1
                    print(f"Wall {i+1}/{num_objects}: L={length:.2f}m, H={height:.2f}m, Area={area:.2f}m²")
                    
                except Exception as e:
                    print(f"Object {i}: Error: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            ss.Delete()
            self.refresh_walls()
            
            if count > 0:
                messagebox.showinfo("Success", f"✅ Added {count} wall(s) @ {height}m height")
                self.update_status(f"Added {count} wall(s) @ {height}m", icon="🧱")
            else:
                messagebox.showwarning("Warning", "No valid walls!\n\nMake sure you select:\n- LINES\n- POLYLINES\n- ARCS\nwith Length property")
                self.update_status("No valid walls detected", icon="⚠️")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.root.deiconify()
    
    # === HELPER FUNCTIONS ===
    
    def _get_block_dims(self, block):
        """Get block W×H from attributes or bbox"""
        w, h = None, None
        
        # Try attributes first
        try:
            has_attrs = self._safe_get(block, 'HasAttributes', False)
            if has_attrs:
                attrs = block.GetAttributes()
                for att in attrs:
                    try:
                        tag = str(att.TagString).upper()
                        text = str(att.TextString)
                        
                        if tag in ['WIDTH', 'W'] and not w:
                            try:
                                w = abs(float(text))
                            except:
                                pass
                        elif tag in ['HEIGHT', 'H'] and not h:
                            try:
                                h = abs(float(text))
                            except:
                                pass
                    except:
                        continue
        except:
            pass
        
        # Always try bounding box (most reliable)
        try:
            bbox = block.GetBoundingBox()
            min_pt = bbox[0]
            max_pt = bbox[1]
            
            bbox_w = abs(max_pt[0] - min_pt[0])
            bbox_h = abs(max_pt[1] - min_pt[1])
            
            # Use bbox if no attributes or if bbox is bigger (safer)
            if not w or bbox_w > w:
                w = bbox_w
            if not h or bbox_h > h:
                h = bbox_h
        except:
            pass
        
        # Return if valid
        if w and h and w > 0.001 and h > 0.001:
            return w, h
        
        return None, None
    
    def _delete_all_selections(self):
        """Delete all selection sets to avoid conflicts"""
        try:
            ss_count = self.doc.SelectionSets.Count
            # Delete from end to beginning
            for i in range(ss_count - 1, -1, -1):
                try:
                    self.doc.SelectionSets.Item(i).Delete()
                except:
                    pass
        except:
            pass
    
    def update_scale(self):
        """Update scale from entry"""
        try:
            self.scale = float(self.scale_var.get())
            if self.scale <= 0:
                raise ValueError
        except:
            self.scale = 1.0
            self.scale_var.set("1.0")
    
    # === FINISHES FUNCTIONS ===
    
    def add_finish_from_source(self, finish_type, source):
        """Add finish from rooms/walls with selection"""
        if source == 'rooms':
            if not self.rooms:
                messagebox.showwarning("Warning", "No rooms available!")
                return
            self._select_and_add_finish(finish_type, self.rooms, "Rooms")
        else:  # walls
            if not self.walls:
                messagebox.showwarning("Warning", "No walls available!")
                return
            self._select_and_add_finish(finish_type, self.walls, "Walls")
    
    def add_walls_from_rooms(self, finish_type):
        """Add wall areas calculated from room perimeters × height"""
        if not self.rooms:
            messagebox.showwarning("Warning", "No rooms available!")
            return
        
        # Ask for height
        height = simpledialog.askfloat(
            "Wall Height",
            "Enter wall height (m):",
            initialvalue=3.0,
            minvalue=0.1,
            maxvalue=10.0
        )
        if not height:
            return
        
        # Select rooms
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Select Rooms for {finish_type.upper()} (Walls)")
        dialog.geometry("520x420")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, 
                 text=f"Select rooms to calculate wall area (Perimeter × {height}m):",
                 foreground=self.colors['text_primary'],
                 background=self.colors['bg_secondary'],
                 font=('Segoe UI', 11, 'bold')).pack(pady=12)
        
        frame = ttk.Frame(dialog, style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, 
                            bg=self.colors['bg_card'], 
                            fg=self.colors['text_primary'],
                            font=('Segoe UI', 10), 
                            height=12)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        for i, room in enumerate(self.rooms):
            perim = room.get('perim', 0)
            area_wall = perim * height
            listbox.insert(tk.END, f"{room.get('name', f'Room{i+1}')} - Perim: {perim:.2f}m → Wall: {area_wall:.2f} m²")
        
        btn_frame = ttk.Frame(dialog, style='Main.TFrame')
        btn_frame.pack(pady=10)
        
        def select_all():
            listbox.select_set(0, tk.END)
        
        def deselect_all():
            listbox.select_clear(0, tk.END)
        
        ttk.Button(btn_frame, text="Select All", command=select_all, style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Deselect All", command=deselect_all, style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
        
        def add_selected():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("Warning", "Select at least one room!")
                return
            
            storage = self._get_finish_storage(finish_type)
            total_added = 0
            
            for idx in selected_indices:
                room = self.rooms[idx]
                perim = room.get('perim', 0)
                area = perim * height
                desc = f"Walls: {room.get('name', f'Room{idx+1}')} ({perim:.2f}m × {height}m)"
                storage.append({'desc': desc, 'area': area})
                total_added += area
            
            self._refresh_finish(finish_type)
            dialog.destroy()
            messagebox.showinfo("Success", f"✅ Added {total_added:.2f} m² wall area to {finish_type}")
            self.update_status(f"Added {total_added:.2f} m² to {finish_type}", icon="🎨")
        
        action_frame = ttk.Frame(dialog, style='Main.TFrame')
        action_frame.pack(pady=12)
        
        ttk.Button(action_frame, text="✓ Add Selected", command=add_selected, style='Accent.TButton').pack(side=tk.LEFT, padx=6)
        ttk.Button(action_frame, text="✗ Cancel", command=dialog.destroy, style='Danger.TButton').pack(side=tk.LEFT, padx=6)
    
    def deduct_ceramic_from_finish(self, finish_type):
        """Deduct ceramic zone areas from finish totals"""
        if not self.ceramic_zones:
            messagebox.showinfo("Info", "No ceramic zones defined. Add ceramic zones in the Materials tab first.")
            return
        
        total_ceramic = sum(zone.get('area', 0) for zone in self.ceramic_zones)
        
        result = messagebox.askyesno(
            "Deduct Ceramic",
            f"Deduct {total_ceramic:.2f} m² of ceramic wall zones from {finish_type}?\n\n"
            f"This will subtract the ceramic-tiled areas from your {finish_type} calculation."
        )
        
        if result:
            storage = self._get_finish_storage(finish_type)
            storage.append({
                'desc': f"Deduction: Ceramic zones",
                'area': -total_ceramic
            })
            self._refresh_finish(finish_type)
            messagebox.showinfo("Success", f"✅ Deducted {total_ceramic:.2f} m² from {finish_type}")
    
    def calculate_room_finishes(self):
        """Open Room Finishes Calculator for selected room"""
        if not hasattr(self, 'rooms_tree'):
            return
        
        selection = self.rooms_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a room first")
            return
        
        room_idx = self.rooms_tree.index(selection[0])
        room = self.rooms[room_idx]
        
        # Open calculator dialog
        self._room_finishes_calculator_dialog(room, room_idx)
    
    def _room_finishes_calculator_dialog(self, room, room_idx):
        """Room-based finishes calculator with opening deductions"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"🧮 Calculate Finishes - {room.get('name', f'Room{room_idx+1}')}")
        dialog.geometry("700x750")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = ttk.Frame(dialog, style='Hero.TFrame', padding=(18, 16))
        header.pack(fill=tk.X)
        
        room_name = room.get('name', f'Room{room_idx+1}')
        room_dims = f"{self._fmt(room.get('w'))} × {self._fmt(room.get('l'))} m"
        room_perim = room.get('perim', 0)
        
        ttk.Label(header, text=f"🏠 {room_name}", 
                 style='HeroHeading.TLabel').pack(anchor=tk.W)
        ttk.Label(header, text=f"Dimensions: {room_dims} • Perimeter: {room_perim:.2f} m",
                 style='HeroSubheading.TLabel').pack(anchor=tk.W, pady=(4, 0))
        
        # Main content
        content = ttk.Frame(dialog, style='Main.TFrame', padding=(18, 12))
        content.pack(fill=tk.BOTH, expand=True)
        
        # Wall height input
        height_frame = ttk.Frame(content, style='Main.TFrame')
        height_frame.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(height_frame, text="Wall Height (m):",
                 foreground=self.colors['text_secondary']).pack(side=tk.LEFT, padx=(0, 8))
        height_var = tk.StringVar(value="3.0")
        height_entry = ttk.Entry(height_frame, textvariable=height_var, width=10)
        height_entry.pack(side=tk.LEFT)
        
        gross_area_var = tk.StringVar(value="0.00")
        ttk.Label(height_frame, text="→ Gross Wall Area:",
                 foreground=self.colors['text_secondary']).pack(side=tk.LEFT, padx=(20, 8))
        ttk.Label(height_frame, textvariable=gross_area_var,
                 foreground=self.colors['accent'],
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        
        # Openings selection
        openings_label = ttk.Label(content, text="Select Openings in This Room:",
                                   foreground=self.colors['text_primary'],
                                   font=('Segoe UI', 11, 'bold'))
        openings_label.pack(anchor=tk.W, pady=(8, 4))
        
        # Scrollable frame for openings
        canvas = tk.Canvas(content, bg=self.colors['bg_card'], height=300, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Main.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add all doors and windows
        opening_vars = []
        
        if self.doors:
            ttk.Label(scrollable_frame, text="🚪 Doors:",
                     foreground=self.colors['accent'],
                     font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(8, 4))
            
            for door in self.doors:
                frame = ttk.Frame(scrollable_frame, style='Main.TFrame')
                frame.pack(fill=tk.X, padx=10, pady=2)
                
                check_var = tk.BooleanVar(value=False)
                qty_var = tk.StringVar(value="1")
                
                door_info = f"{door.get('name', '-')} ({self._fmt(door.get('w'))}×{self._fmt(door.get('h'))}m) = {self._fmt(door.get('area_each'))} m² each"
                
                cb = tk.Checkbutton(frame, text=door_info,
                                   variable=check_var,
                                   bg=self.colors['bg_secondary'],
                                   fg=self.colors['text_primary'],
                                   selectcolor=self.colors['bg_card'],
                                   activebackground=self.colors['bg_secondary'],
                                   activeforeground=self.colors['accent'])
                cb.pack(side=tk.LEFT)
                
                ttk.Label(frame, text="Qty:", foreground=self.colors['text_secondary']).pack(side=tk.LEFT, padx=(10, 4))
                ttk.Entry(frame, textvariable=qty_var, width=5).pack(side=tk.LEFT)
                
                opening_vars.append({
                    'type': 'door',
                    'data': door,
                    'checked': check_var,
                    'qty': qty_var
                })
        
        if self.windows:
            ttk.Label(scrollable_frame, text="🪟 Windows:",
                     foreground=self.colors['accent'],
                     font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(8, 4))
            
            for window in self.windows:
                frame = ttk.Frame(scrollable_frame, style='Main.TFrame')
                frame.pack(fill=tk.X, padx=10, pady=2)
                
                check_var = tk.BooleanVar(value=False)
                qty_var = tk.StringVar(value="1")
                
                window_info = f"{window.get('name', '-')} ({self._fmt(window.get('w'))}×{self._fmt(window.get('h'))}m) = {self._fmt(window.get('area_each'))} m² each"
                
                cb = tk.Checkbutton(frame, text=window_info,
                                   variable=check_var,
                                   bg=self.colors['bg_secondary'],
                                   fg=self.colors['text_primary'],
                                   selectcolor=self.colors['bg_card'],
                                   activebackground=self.colors['bg_secondary'],
                                   activeforeground=self.colors['accent'])
                cb.pack(side=tk.LEFT)
                
                ttk.Label(frame, text="Qty:", foreground=self.colors['text_secondary']).pack(side=tk.LEFT, padx=(10, 4))
                ttk.Entry(frame, textvariable=qty_var, width=5).pack(side=tk.LEFT)
                
                opening_vars.append({
                    'type': 'window',
                    'data': window,
                    'checked': check_var,
                    'qty': qty_var
                })
        
        # Calculation summary
        summary_frame = ttk.Frame(content, style='Main.TFrame', padding=(10, 12))
        summary_frame.pack(fill=tk.X, pady=(12, 0))
        
        deduct_var = tk.StringVar(value="0.00")
        net_var = tk.StringVar(value="0.00")
        
        ttk.Label(summary_frame, text="Total Deductions:",
                 foreground=self.colors['text_secondary']).grid(row=0, column=0, sticky='w', padx=(0, 8))
        ttk.Label(summary_frame, textvariable=deduct_var,
                 foreground=self.colors['warning'],
                 font=('Segoe UI', 10, 'bold')).grid(row=0, column=1, sticky='w')
        
        ttk.Label(summary_frame, text="NET WALL AREA:",
                 foreground=self.colors['text_primary'],
                 font=('Segoe UI', 11, 'bold')).grid(row=1, column=0, sticky='w', padx=(0, 8), pady=(8, 0))
        ttk.Label(summary_frame, textvariable=net_var,
                 foreground=self.colors['success'],
                 font=('Segoe UI', 12, 'bold')).grid(row=1, column=1, sticky='w', pady=(8, 0))
        
        # Apply to finishes
        apply_frame = ttk.Frame(content, style='Main.TFrame', padding=(10, 12))
        apply_frame.pack(fill=tk.X, pady=(8, 0))
        
        ttk.Label(apply_frame, text="Apply To:",
                 foreground=self.colors['text_primary'],
                 font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 6))
        
        apply_plaster = tk.BooleanVar(value=True)
        apply_paint = tk.BooleanVar(value=True)
        apply_tiles = tk.BooleanVar(value=False)
        
        tk.Checkbutton(apply_frame, text="🏗️ Plaster", variable=apply_plaster,
                      bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                      selectcolor=self.colors['bg_card']).pack(anchor=tk.W, pady=2)
        tk.Checkbutton(apply_frame, text="🎨 Paint", variable=apply_paint,
                      bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                      selectcolor=self.colors['bg_card']).pack(anchor=tk.W, pady=2)
        tk.Checkbutton(apply_frame, text="🟦 Tiles", variable=apply_tiles,
                      bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                      selectcolor=self.colors['bg_card']).pack(anchor=tk.W, pady=2)
        
        # Auto-calculate function
        def update_calculations(*args):
            try:
                height = float(height_var.get())
                gross = room_perim * height
                gross_area_var.set(f"{gross:.2f} m²")
                
                total_deduct = 0
                for item in opening_vars:
                    if item['checked'].get():
                        qty = int(item['qty'].get())
                        area_each = item['data'].get('area_each', 0)
                        total_deduct += area_each * qty
                
                deduct_var.set(f"{total_deduct:.2f} m²")
                net = max(0, gross - total_deduct)
                net_var.set(f"{net:.2f} m²")
            except:
                pass
        
        # Bind updates
        height_var.trace_add('write', update_calculations)
        for item in opening_vars:
            item['checked'].trace_add('write', update_calculations)
            item['qty'].trace_add('write', update_calculations)
        
        update_calculations()
        
        # Buttons
        btn_frame = ttk.Frame(dialog, style='Main.TFrame', padding=(18, 12))
        btn_frame.pack(fill=tk.X)
        
        def save_finishes():
            try:
                height = float(height_var.get())
                gross = room_perim * height
                
                total_deduct = 0
                opening_details = []
                for item in opening_vars:
                    if item['checked'].get():
                        qty = int(item['qty'].get())
                        name = item['data'].get('name', '-')
                        area_each = item['data'].get('area_each', 0)
                        area_total = area_each * qty
                        total_deduct += area_total
                        opening_details.append(f"{name}×{qty}")
                
                net = max(0, gross - total_deduct)
                
                if net <= 0:
                    messagebox.showwarning("Warning", "Net area is zero or negative!")
                    return
                
                # Build description
                openings_str = f" - {', '.join(opening_details)}" if opening_details else ""
                desc = f"{room_name} walls ({room_perim:.2f}m × {height}m{openings_str})"
                
                # Add to selected finishes
                added_to = []
                if apply_plaster.get():
                    self.plaster_items.append({'desc': desc, 'area': net})
                    added_to.append('Plaster')
                if apply_paint.get():
                    self.paint_items.append({'desc': desc, 'area': net})
                    added_to.append('Paint')
                if apply_tiles.get():
                    self.tiles_items.append({'desc': desc, 'area': net})
                    added_to.append('Tiles')
                
                if added_to:
                    self._refresh_finish('plaster')
                    self._refresh_finish('paint')
                    self._refresh_finish('tiles')
                    
                    dialog.destroy()
                    messagebox.showinfo("Success", 
                                      f"✅ Added {net:.2f} m² to:\n" + "\n".join(f"  • {f}" for f in added_to))
                    self.update_status(f"Applied {net:.2f} m² to {', '.join(added_to)}", icon="🎨")
                else:
                    messagebox.showwarning("Warning", "Please select at least one finish type!")
                    
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {e}")
        
        ttk.Button(btn_frame, text="✓ Save & Apply", command=save_finishes, style='Accent.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="✗ Cancel", command=dialog.destroy, style='Danger.TButton').pack(side=tk.RIGHT, padx=4)
    
    def _select_and_add_finish(self, finish_type, items, source_name):
        """Show dialog to select specific items"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Select {source_name} for {finish_type.upper()}")
        dialog.geometry("500x400")
        dialog.configure(bg='#2b2b2b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"Select {source_name} to add:", bg='#2b2b2b', fg='white', font=('Arial', 11, 'bold')).pack(pady=10)
        
        # Listbox with checkboxes
        frame = tk.Frame(dialog, bg='#2b2b2b')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, bg='#1e1e1e', fg='white', font=('Arial', 10), height=15)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate listbox
        if source_name == "Rooms":
            for i, room in enumerate(items):
                area = room['area']
                listbox.insert(tk.END, f"Room {i+1} - {room['layer']} - {area:.2f} m²")
        else:  # Walls
            for i, wall in enumerate(items):
                area = wall['net']
                listbox.insert(tk.END, f"Wall {i+1} - {wall['layer']} - L:{wall['length']:.2f}m H:{wall['height']:.2f}m = {area:.2f} m²")
        
        # Select all button
        btn_frame = tk.Frame(dialog, bg='#2b2b2b')
        btn_frame.pack(pady=5)
        
        def select_all():
            listbox.select_set(0, tk.END)
        
        def deselect_all():
            listbox.select_clear(0, tk.END)
        
        tk.Button(btn_frame, text="Select All", command=select_all, bg='#607D8B', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Deselect All", command=deselect_all, bg='#607D8B', fg='white').pack(side=tk.LEFT, padx=5)
        
        def add_selected():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("Warning", "Select at least one item!")
                return
            
            storage = self._get_finish_storage(finish_type)
            total_added = 0
            
            for idx in selected_indices:
                if source_name == "Rooms":
                    room = items[idx]
                    area = room['area']
                    desc = f"Room {idx+1} - {room['layer']}"
                else:
                    wall = items[idx]
                    area = wall['net']
                    desc = f"Wall {idx+1} - {wall['layer']}"
                
                storage.append({'desc': desc, 'area': area})
                total_added += area
            
            self._refresh_finish(finish_type)
            dialog.destroy()
            messagebox.showinfo("Success", f"✅ Added {total_added:.2f} m² to {finish_type}")
            self.update_status(f"Added {total_added:.2f} m² to {finish_type}", icon="🎨")
        
        # Action buttons
        action_frame = tk.Frame(dialog, bg='#2b2b2b')
        action_frame.pack(pady=10)
        
        tk.Button(action_frame, text="✓ Add Selected", command=add_selected, bg='#4CAF50', fg='white', width=15, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="✗ Cancel", command=dialog.destroy, bg='#f44336', fg='white', width=15, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
    
    def add_finish_manual(self, finish_type):
        """Add finish area manually"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Add {finish_type.upper()} Manually")
        dialog.geometry("400x180")
        dialog.configure(bg='#2b2b2b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Description:", bg='#2b2b2b', fg='white').grid(row=0, column=0, padx=10, pady=10, sticky='e')
        desc_var = tk.StringVar(value=f"Manual {finish_type}")
        tk.Entry(dialog, textvariable=desc_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(dialog, text="Area (m²):", bg='#2b2b2b', fg='white').grid(row=1, column=0, padx=10, pady=10, sticky='e')
        area_var = tk.StringVar(value="10.0")
        tk.Entry(dialog, textvariable=area_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        def save():
            try:
                area = float(area_var.get())
                desc = desc_var.get().strip()
                
                if not desc:
                    messagebox.showerror("Error", "Description cannot be empty!")
                    return
                
                storage = self._get_finish_storage(finish_type)
                storage.append({'desc': desc, 'area': area})
                self._refresh_finish(finish_type)
                dialog.destroy()
                messagebox.showinfo("Success", f"✅ Added {area:.2f} m² to {finish_type}")
                self.update_status(f"Manual entry: {area:.2f} m² to {finish_type}", icon="🎨")
            except ValueError:
                messagebox.showerror("Error", "Invalid area value!")
        
        btn_frame = tk.Frame(dialog, bg='#2b2b2b')
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        tk.Button(btn_frame, text="✓ Save", command=save, bg='#4CAF50', fg='white', width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✗ Cancel", command=dialog.destroy, bg='#f44336', fg='white', width=12).pack(side=tk.LEFT, padx=5)
    
    def edit_finish_item(self, finish_type):
        """Edit selected finish item"""
        tree = self._get_finish_tree(finish_type)
        storage = self._get_finish_storage(finish_type)
        
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", f"Select a {finish_type} item to edit!")
            return
        
        idx = tree.index(selection[0])
        item = storage[idx]
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {finish_type.upper()} Item")
        dialog.geometry("400x180")
        dialog.configure(bg='#2b2b2b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Description:", bg='#2b2b2b', fg='white').grid(row=0, column=0, padx=10, pady=10, sticky='e')
        desc_var = tk.StringVar(value=item['desc'])
        tk.Entry(dialog, textvariable=desc_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(dialog, text="Area (m²):", bg='#2b2b2b', fg='white').grid(row=1, column=0, padx=10, pady=10, sticky='e')
        area_var = tk.StringVar(value=str(item['area']))
        tk.Entry(dialog, textvariable=area_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        def save():
            try:
                area = float(area_var.get())
                desc = desc_var.get().strip()
                
                if not desc:
                    messagebox.showerror("Error", "Description cannot be empty!")
                    return
                
                storage[idx] = {'desc': desc, 'area': area}
                self._refresh_finish(finish_type)
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid area value!")
        
        btn_frame = tk.Frame(dialog, bg='#2b2b2b')
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        tk.Button(btn_frame, text="✓ Save", command=save, bg='#4CAF50', fg='white', width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✗ Cancel", command=dialog.destroy, bg='#f44336', fg='white', width=12).pack(side=tk.LEFT, padx=5)
    
    def delete_finish_item(self, finish_type):
        """Delete selected finish item"""
        tree = self._get_finish_tree(finish_type)
        storage = self._get_finish_storage(finish_type)
        
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", f"Select a {finish_type} item to delete!")
            return
        
        if messagebox.askyesno("Confirm", f"Delete selected {finish_type} item?"):
            idx = tree.index(selection[0])
            del storage[idx]
            self._refresh_finish(finish_type)
            self.update_status(f"Deleted {finish_type} item", icon="🗑️")
    
    def _get_finish_storage(self, finish_type):
        """Get the storage list for a finish type"""
        if finish_type == 'plaster':
            return self.plaster_items
        elif finish_type == 'paint':
            return self.paint_items
        else:
            return self.tiles_items
    
    def _get_finish_tree(self, finish_type):
        """Get the treeview for a finish type"""
        if finish_type == 'plaster':
            return self.plaster_tree
        elif finish_type == 'paint':
            return self.paint_tree
        else:
            return self.tiles_tree
    
    def _get_finish_label(self, finish_type):
        """Get the label for a finish type"""
        if finish_type == 'plaster':
            return self.plaster_label
        elif finish_type == 'paint':
            return self.paint_label
        else:
            return self.tiles_label
    
    def _refresh_finish(self, finish_type):
        """Refresh a finish treeview and total"""
        tree = self._get_finish_tree(finish_type)
        storage = self._get_finish_storage(finish_type)
        label = self._get_finish_label(finish_type)
        
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)
        
        # Repopulate
        total = 0
        for item in storage:
            tree.insert('', tk.END, values=(item['desc'], f"{item['area']:.2f}"))
            total += item['area']
        
        # Update label
        label.config(text=f"Total = {total:.2f} m²")
    
    # === WALLS & OLD FINISHES (kept for compatibility) ===
    
    def deduct_from_walls(self):
        """Deduct selected openings from walls with modern dialog"""
        if not self.walls:
            messagebox.showwarning("Warning", "No walls available!")
            return
        
        if not self.doors and not self.windows:
            messagebox.showwarning("Warning", "No doors or windows to deduct!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("➖ Deduct Openings from Walls")
        dialog.geometry("680x580")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = ttk.Frame(dialog, style='Hero.TFrame', padding=(18, 16))
        header.pack(fill=tk.X)
        ttk.Label(header, text="Deduct Openings from Walls",
                  style='HeroHeading.TLabel').pack(anchor=tk.W)
        ttk.Label(header, text="اختر الأبواب والشبابيك المراد خصمها من الجدران",
                  style='HeroSubheading.TLabel').pack(anchor=tk.W, pady=(4, 0))
        
        # Content
        content = ttk.Frame(dialog, style='Main.TFrame', padding=(18, 12))
        content.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(content,
                  text="✓ Check the openings you want to deduct",
                  foreground=self.colors['accent'],
                  font=('Segoe UI', 10, 'italic')).pack(anchor=tk.W, pady=(0, 8))
        
        # Scrollable selection area
        canvas = tk.Canvas(content, bg=self.colors['bg_card'], height=320, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Main.TFrame')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        opening_vars = []
        
        # Doors section
        if self.doors:
            ttk.Label(scrollable_frame, text="🚪 Doors:",
                      foreground=self.colors['accent'],
                      font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, padx=12, pady=(10, 6))
            
            for door in self.doors:
                item_frame = ttk.Frame(scrollable_frame, style='Main.TFrame')
                item_frame.pack(fill=tk.X, padx=12, pady=3)
                
                var = tk.BooleanVar(value=True)
                opening_vars.append({'type': 'door', 'data': door, 'var': var})
                
                area = door.get('area', 0)
                name = door.get('name', '-')
                dims = f"{self._fmt(door.get('w'))}×{self._fmt(door.get('h'))}m"
                qty = door.get('qty', 1)
                
                cb = tk.Checkbutton(item_frame,
                                    text=f"{name} ({dims}) × {qty} = {area:.2f} m²",
                                    variable=var,
                                    bg=self.colors['bg_secondary'],
                                    fg=self.colors['text_primary'],
                                    selectcolor=self.colors['bg_card'],
                                    activebackground=self.colors['bg_secondary'],
                                    activeforeground=self.colors['accent'],
                                    font=('Segoe UI', 10))
                cb.pack(side=tk.LEFT, anchor='w')
        
        # Windows section
        if self.windows:
            ttk.Label(scrollable_frame, text="🪟 Windows:",
                      foreground=self.colors['accent'],
                      font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, padx=12, pady=(12, 6))
            
            for window in self.windows:
                item_frame = ttk.Frame(scrollable_frame, style='Main.TFrame')
                item_frame.pack(fill=tk.X, padx=12, pady=3)
                
                var = tk.BooleanVar(value=True)
                opening_vars.append({'type': 'window', 'data': window, 'var': var})
                
                area = window.get('area', 0)
                name = window.get('name', '-')
                dims = f"{self._fmt(window.get('w'))}×{self._fmt(window.get('h'))}m"
                qty = window.get('qty', 1)
                
                cb = tk.Checkbutton(item_frame,
                                    text=f"{name} ({dims}) × {qty} = {area:.2f} m²",
                                    variable=var,
                                    bg=self.colors['bg_secondary'],
                                    fg=self.colors['text_primary'],
                                    selectcolor=self.colors['bg_card'],
                                    activebackground=self.colors['bg_secondary'],
                                    activeforeground=self.colors['accent'],
                                    font=('Segoe UI', 10))
                cb.pack(side=tk.LEFT, anchor='w')
        
        # Summary panel
        summary_frame = ttk.Frame(content, style='Main.TFrame', padding=(12, 10))
        summary_frame.pack(fill=tk.X, pady=(12, 0))
        
        total_var = tk.StringVar(value="0.00")
        ttk.Label(summary_frame, text="Total to deduct:",
                  foreground=self.colors['text_secondary']).pack(side=tk.LEFT)
        ttk.Label(summary_frame, textvariable=total_var,
                  foreground=self.colors['warning'],
                  font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT, padx=8)
        
        def update_total(*args):
            total = sum(item['data'].get('area', 0) for item in opening_vars if item['var'].get())
            total_var.set(f"{total:.2f} m²")
        
        for item in opening_vars:
            item['var'].trace_add('write', update_total)
        update_total()
        
        def apply_deduction():
            total_deduct = sum(item['data'].get('area', 0) for item in opening_vars if item['var'].get())
            
            if total_deduct <= 0:
                messagebox.showwarning("Warning", "Select at least one opening to deduct!")
                return
            
            total_walls = sum(w.get('gross', 0) for w in self.walls)
            if total_walls <= 0:
                messagebox.showerror("Error", "No wall area available!")
                return
            
            # Distribute deduction proportionally
            for wall in self.walls:
                ratio = wall.get('gross', 0) / total_walls
                wall['deduct'] = total_deduct * ratio
                wall['net'] = wall.get('gross', 0) - wall['deduct']
            
            self.refresh_walls()
            dialog.destroy()
            messagebox.showinfo("Success", f"✅ Deducted {total_deduct:.2f} m² from walls")
            self.update_status(f"Deducted {total_deduct:.2f} m² from walls", icon="➖")
        
        # Buttons
        btn_frame = ttk.Frame(dialog, padding=(18, 12), style='Main.TFrame')
        btn_frame.pack(fill=tk.X)
        
        def select_all():
            for item in opening_vars:
                item['var'].set(True)
        
        def deselect_all():
            for item in opening_vars:
                item['var'].set(False)
        
        ttk.Button(btn_frame, text="✓ Select All", command=select_all, style='Secondary.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="✗ Deselect All", command=deselect_all, style='Secondary.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="➖ Apply Deduction", command=apply_deduction, style='Accent.TButton').pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, style='Danger.TButton').pack(side=tk.RIGHT, padx=4)
    
    def update_finish_labels(self):
        """Update all finish labels (for backward compatibility)"""
        self._refresh_finish('plaster')
        self._refresh_finish('paint')
        self._refresh_finish('tiles')
    
    # === REFRESH TABLES ===
    
    def refresh_rooms(self):
        query = self.rooms_filter.get() if hasattr(self, 'rooms_filter') else ''
        self._filter_treeview(self.rooms_tree, query, 'rooms')
    
    def refresh_openings(self):
        """Refresh doors and windows tables"""
        door_query = self.doors_filter.get() if hasattr(self, 'doors_filter') else ''
        window_query = self.windows_filter.get() if hasattr(self, 'windows_filter') else ''
        self._filter_treeview(self.doors_tree, door_query, 'doors')
        self._filter_treeview(self.windows_tree, window_query, 'windows')
        self.refresh_materials_tab()
    
    def refresh_walls(self):
        query = self.walls_filter.get() if hasattr(self, 'walls_filter') else ''
        visible = self._filter_treeview(self.walls_tree, query, 'walls')
        total_net = sum(w.get('net', 0) for w in self.walls)
        visible_net = sum(w.get('net', 0) for w in visible)
        if hasattr(self, 'wall_metrics_var'):
            total_count = len(self.walls)
            visible_count = len(visible)
            if query and visible_count != total_count:
                self.wall_metrics_var.set(
                    f"Net wall area: {visible_net:.2f} m² (showing {visible_count}/{total_count})"
                )
            else:
                self.wall_metrics_var.set(f"Net wall area: {total_net:.2f} m²")
    
    # === SUMMARY & EXPORT ===
    
    def update_summary(self):
        """Generate summary"""
        sep = "=" * 90
        s = sep + "\n"
        s += "                BILIND ENHANCED - MATERIAL SUMMARY\n"
        s += sep + "\n\n"

        room_total = sum((r.get('area') or 0) for r in self.rooms)
        s += "📋 ROOMS / الغرف:\n" + "-"*90 + "\n"
        for i, r in enumerate(self.rooms, 1):
            s += (
                f"{i:>2}. {r.get('name', f'Room{i}'):<14} | Layer: {r.get('layer', '-'):<18}"
                f" | Size: {self._fmt(r.get('w'))}×{self._fmt(r.get('l'))} m"
                f" | Area: {self._fmt(r.get('area'))} m²\n"
            )
        s += f"→ Total Rooms Area: {room_total:.2f} m²\n\n"

        door_area = sum((d.get('area') or 0) for d in self.doors)
        door_stone = sum((d.get('stone') or 0) for d in self.doors)
        door_weight = sum((d.get('weight') or 0) for d in self.doors)
        s += "🚪 DOORS / الأبواب:\n" + "-"*90 + "\n"
        for i, d in enumerate(self.doors, 1):
            s += (
                f"{i:>2}. {d.get('name', f'D{i}'):<10} | Type: {d.get('type', '-'):<10}"
                f" | Qty: {d.get('qty', 1):>2}"
                f" | Size: {self._fmt(d.get('w'))}×{self._fmt(d.get('h'))} m"
                f" | Stone: {self._fmt(d.get('stone'))} lm"
                f" | Area: {self._fmt(d.get('area'))} m²"
                f" | Steel: {self._fmt(d.get('weight'), digits=1)} kg\n"
            )
        s += (
            f"→ Totals • Area: {door_area:.2f} m² • Stone: {door_stone:.2f} lm"
            f" • Steel: {door_weight:.1f} kg\n\n"
        )

        window_area = sum((w.get('area') or 0) for w in self.windows)
        window_stone = sum((w.get('stone') or 0) for w in self.windows)
        window_glass = sum((w.get('glass') or 0) for w in self.windows)
        s += "🪟 WINDOWS / الشبابيك:\n" + "-"*90 + "\n"
        for i, w in enumerate(self.windows, 1):
            s += (
                f"{i:>2}. {w.get('name', f'W{i}'):<10} | Type: {w.get('type', '-'):<12}"
                f" | Qty: {w.get('qty', 1):>2}"
                f" | Size: {self._fmt(w.get('w'))}×{self._fmt(w.get('h'))} m"
                f" | Stone: {self._fmt(w.get('stone'))} lm"
                f" | Area: {self._fmt(w.get('area'))} m²"
                f" | Glass: {self._fmt(w.get('glass'))} m²\n"
            )
        s += (
            f"→ Totals • Area: {window_area:.2f} m² • Stone: {window_stone:.2f} lm"
            f" • Glass: {window_glass:.2f} m²\n\n"
        )

        if self.walls:
            wall_net = sum((w.get('net') or 0) for w in self.walls)
            s += "🧱 WALLS / الجدران:\n" + "-"*90 + "\n"
            for i, w in enumerate(self.walls, 1):
                s += (
                    f"{i:>2}. {w.get('name', f'Wall{i}'):<12} | Layer: {w.get('layer', '-'):<15}"
                    f" | L×H: {w.get('length', 0):.2f}×{w.get('height', 0):.2f} m"
                    f" | Net: {w.get('net', 0):.2f} m² (Deduct {w.get('deduct', 0):.2f} m²)\n"
                )
            s += f"→ Total Net Walls: {wall_net:.2f} m²\n\n"

        s += "🪨 STONE & STEEL LEDGER:\n" + "-"*90 + "\n"
        s += (
            f"Doors stone: {door_stone:.2f} lm | Windows stone: {window_stone:.2f} lm"
            f" | Steel weight: {door_weight:.1f} kg | Glass: {window_glass:.2f} m²\n\n"
        )

        s += "🎨 FINISHES / التشطيبات:\n" + "-"*90 + "\n"
        plaster_total = sum(item['area'] for item in self.plaster_items)
        paint_total = sum(item['area'] for item in self.paint_items)
        tiles_total = sum(item['area'] for item in self.tiles_items)

        s += "🏗️ PLASTER:\n"
        for i, item in enumerate(self.plaster_items, 1):
            s += f"{i:>2}. {item['desc']:<45} {item['area']:>10.2f} m²\n"
        s += f"→ Total Plaster: {plaster_total:.2f} m²\n\n"

        s += "🎨 PAINT:\n"
        for i, item in enumerate(self.paint_items, 1):
            s += f"{i:>2}. {item['desc']:<45} {item['area']:>10.2f} m²\n"
        s += f"→ Total Paint: {paint_total:.2f} m²\n\n"

        s += "🟦 TILES:\n"
        for i, item in enumerate(self.tiles_items, 1):
            s += f"{i:>2}. {item['desc']:<45} {item['area']:>10.2f} m²\n"
        s += f"→ Total Tiles: {tiles_total:.2f} m²\n\n"

        if self.ceramic_zones:
            s += "🧼 CERAMIC WALLS / سيراميك الجدران:\n" + "-"*90 + "\n"
            ceramic_totals = {}
            for i, zone in enumerate(self.ceramic_zones, 1):
                area = zone.get('area', 0)
                category = zone.get('category', 'Other')
                ceramic_totals[category] = ceramic_totals.get(category, 0.0) + area
                s += (
                    f"{i:>2}. {zone.get('name', 'Zone'):<16} | {category:<10}"
                    f" | Perimeter: {zone.get('perimeter', 0):.2f} m | Height: {zone.get('height', 0):.2f} m"
                    f" | Area: {area:.2f} m²"
                    f"{f' | Notes: {zone.get('notes')}' if zone.get('notes') else ''}\n"
                )
            total_ceramic = sum(ceramic_totals.values())
            cat_summary = " • ".join(f"{cat}: {val:.2f} m²" for cat, val in ceramic_totals.items())
            s += f"→ Totals • {cat_summary} • Total: {total_ceramic:.2f} m²\n\n"

        s += sep + "\n"
        s += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        s += sep
        
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', s)
        self.update_status("Summary refreshed", icon="📊")
    
    def copy_summary(self):
        """Copy summary to clipboard"""
        self.update_summary()
        text = self.summary_text.get('1.0', tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Success", "✅ Copied!")
        self.update_status("Summary copied to clipboard", icon="📋")
    
    def export_csv(self):
        """Export to CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"bilind_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not filename:
            return
        
        door_stone = sum(d.get('stone', 0.0) for d in self.doors)
        door_weight = sum(d.get('weight', 0.0) for d in self.doors)
        window_stone = sum(w.get('stone', 0.0) for w in self.windows)
        window_glass = sum(w.get('glass', 0.0) for w in self.windows)

        plaster_total = sum(item.get('area', 0.0) for item in self.plaster_items)
        paint_total = sum(item.get('area', 0.0) for item in self.paint_items)
        tiles_total = sum(item.get('area', 0.0) for item in self.tiles_items)

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            writer.writerow(["ROOMS"])
            writer.writerow(["Name", "Layer", "Width (m)", "Length (m)", "Perimeter (m)", "Area (m²)"])
            for r in self.rooms:
                writer.writerow([
                    r.get('name', ''),
                    r.get('layer', ''),
                    self._fmt(r.get('w')),
                    self._fmt(r.get('l')),
                    self._fmt(r.get('perim')),
                    self._fmt(r.get('area'))
                ])

            writer.writerow([])
            writer.writerow(["DOORS"])
            writer.writerow(["Name", "Layer", "Type", "Qty", "Width (m)", "Height (m)", "Stone (lm)", "Area (m²)", "Steel (kg)"])
            for d in self.doors:
                writer.writerow([
                    d.get('name', ''),
                    d.get('layer', ''),
                    d.get('type', ''),
                    d.get('qty', 1),
                    self._fmt(d.get('w')),
                    self._fmt(d.get('h')),
                    self._fmt(d.get('stone')),
                    self._fmt(d.get('area')),
                    self._fmt(d.get('weight'), digits=1)
                ])

            writer.writerow([])
            writer.writerow(["WINDOWS"])
            writer.writerow(["Name", "Layer", "Type", "Qty", "Width (m)", "Height (m)", "Stone (lm)", "Area (m²)", "Glass (m²)"])
            for w in self.windows:
                writer.writerow([
                    w.get('name', ''),
                    w.get('layer', ''),
                    w.get('type', ''),
                    w.get('qty', 1),
                    self._fmt(w.get('w')),
                    self._fmt(w.get('h')),
                    self._fmt(w.get('stone')),
                    self._fmt(w.get('area')),
                    self._fmt(w.get('glass'))
                ])

            if self.walls:
                writer.writerow([])
                writer.writerow(["WALLS"])
                writer.writerow(["Name", "Layer", "Length (m)", "Height (m)", "Gross (m²)", "Deduct (m²)", "Net (m²)"])
                for w in self.walls:
                    writer.writerow([
                        w.get('name', ''),
                        w.get('layer', ''),
                        self._fmt(w.get('length')),
                        self._fmt(w.get('height')),
                        self._fmt(w.get('gross')),
                        self._fmt(w.get('deduct')),
                        self._fmt(w.get('net'))
                    ])

            writer.writerow([])
            writer.writerow(["STONE & STEEL SUMMARY"])
            writer.writerow(["Doors stone (lm)", f"{door_stone:.2f}"])
            writer.writerow(["Windows stone (lm)", f"{window_stone:.2f}"])
            writer.writerow(["Steel weight (kg)", f"{door_weight:.1f}"])
            writer.writerow(["Window glass (m²)", f"{window_glass:.2f}"])

            writer.writerow([])
            writer.writerow(["FINISHES"])
            writer.writerow(["Type", "Area (m²)"])
            writer.writerow(["Plaster", f"{plaster_total:.2f}"])
            writer.writerow(["Paint", f"{paint_total:.2f}"])
            writer.writerow(["Tiles", f"{tiles_total:.2f}"])

            if self.ceramic_zones:
                writer.writerow([])
                writer.writerow(["CERAMIC WALL ZONES"])
                writer.writerow(["Name", "Category", "Perimeter (m)", "Height (m)", "Area (m²)", "Notes"])
                for zone in self.ceramic_zones:
                    writer.writerow([
                        zone.get('name', ''),
                        zone.get('category', ''),
                        f"{zone.get('perimeter', 0):.2f}",
                        f"{zone.get('height', 0):.2f}",
                        f"{zone.get('area', 0):.2f}",
                        zone.get('notes', '')
                    ])
        
        messagebox.showinfo("Success", f"✅ Saved:\n{filename}")
        self.update_status(f"CSV exported: {os.path.basename(filename)}", icon="💾")
    
    # === EDIT/DELETE FUNCTIONS ===
    
    def add_room_manual(self):
        """Add room manually with flexible input options"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🏠 Add Room - Flexible Input")
        dialog.geometry("550x550")
        dialog.configure(bg='#16213e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        title_frame = tk.Frame(dialog, bg='#1a1a2e')
        title_frame.pack(fill=tk.X, pady=10)
        tk.Label(
            title_frame, 
            text="🏠 Add New Room",
            bg='#1a1a2e',
            fg='#00d9ff',
            font=('Arial', 14, 'bold')
        ).pack(pady=10)
        
        # Input method selection
        method_frame = tk.Frame(dialog, bg='#16213e')
        method_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            method_frame,
            text="📝 Input Method:",
            bg='#16213e',
            fg='#ffffff',
            font=('Arial', 11, 'bold')
        ).pack(anchor='w', pady=5)
        
        input_method = tk.StringVar(value="dimensions")
        
        tk.Radiobutton(
            method_frame,
            text="📐 Enter Dimensions (Width × Length)",
            variable=input_method,
            value="dimensions",
            bg='#16213e',
            fg='#ffffff',
            selectcolor='#1a1a2e',
            activebackground='#16213e',
            activeforeground='#00d9ff',
            font=('Arial', 10)
        ).pack(anchor='w', padx=20)
        
        tk.Radiobutton(
            method_frame,
            text="📏 Enter Perimeter + Area Directly",
            variable=input_method,
            value="perim_area",
            bg='#16213e',
            fg='#ffffff',
            selectcolor='#1a1a2e',
            activebackground='#16213e',
            activeforeground='#00d9ff',
            font=('Arial', 10)
        ).pack(anchor='w', padx=20)
        
        # Input fields frame
        input_frame = tk.Frame(dialog, bg='#0f0f1e')
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Name field (always visible)
        tk.Label(input_frame, text="🏷️ Name:", bg='#0f0f1e', fg='#b0bec5', font=('Arial', 10)).grid(row=0, column=0, padx=10, pady=8, sticky='e')
        name_var = tk.StringVar(value=f"Room{len(self.rooms)+1}")
        tk.Entry(input_frame, textvariable=name_var, width=25, font=('Arial', 10), bg='#f0f0f0').grid(row=0, column=1, padx=10, pady=8, sticky='w')
        
        # Layer field
        tk.Label(input_frame, text="📁 Layer:", bg='#0f0f1e', fg='#b0bec5', font=('Arial', 10)).grid(row=1, column=0, padx=10, pady=8, sticky='e')
        layer_var = tk.StringVar(value="Room")
        tk.Entry(input_frame, textvariable=layer_var, width=25, font=('Arial', 10), bg='#f0f0f0').grid(row=1, column=1, padx=10, pady=8, sticky='w')
        
        # Conditional fields
        dim_frame = tk.Frame(input_frame, bg='#0f0f1e')
        dim_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Dimensions inputs
        tk.Label(dim_frame, text="📐 Width (m):", bg='#0f0f1e', fg='#b0bec5', font=('Arial', 10)).grid(row=0, column=0, padx=10, pady=8, sticky='e')
        w_var = tk.StringVar(value="4.0")
        w_entry = tk.Entry(dim_frame, textvariable=w_var, width=15, font=('Arial', 10), bg='#f0f0f0')
        w_entry.grid(row=0, column=1, padx=10, pady=8, sticky='w')
        
        tk.Label(dim_frame, text="📐 Length (m):", bg='#0f0f1e', fg='#b0bec5', font=('Arial', 10)).grid(row=1, column=0, padx=10, pady=8, sticky='e')
        l_var = tk.StringVar(value="5.0")
        l_entry = tk.Entry(dim_frame, textvariable=l_var, width=15, font=('Arial', 10), bg='#f0f0f0')
        l_entry.grid(row=1, column=1, padx=10, pady=8, sticky='w')
        
        # Perimeter + Area inputs
        perim_frame = tk.Frame(input_frame, bg='#0f0f1e')
        perim_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        tk.Label(perim_frame, text="📏 Perimeter (m):", bg='#0f0f1e', fg='#b0bec5', font=('Arial', 10)).grid(row=0, column=0, padx=10, pady=8, sticky='e')
        p_var = tk.StringVar(value="18.0")
        p_entry = tk.Entry(perim_frame, textvariable=p_var, width=15, font=('Arial', 10), bg='#f0f0f0')
        p_entry.grid(row=0, column=1, padx=10, pady=8, sticky='w')
        
        tk.Label(perim_frame, text="📐 Area (m²):", bg='#0f0f1e', fg='#b0bec5', font=('Arial', 10)).grid(row=1, column=0, padx=10, pady=8, sticky='e')
        a_var = tk.StringVar(value="20.0")
        a_entry = tk.Entry(perim_frame, textvariable=a_var, width=15, font=('Arial', 10), bg='#f0f0f0')
        a_entry.grid(row=1, column=1, padx=10, pady=8, sticky='w')
        
        # Initially hide perim_area frame
        perim_frame.grid_remove()
        
        def on_method_change(*args):
            if input_method.get() == "dimensions":
                perim_frame.grid_remove()
                dim_frame.grid()
            else:
                dim_frame.grid_remove()
                perim_frame.grid()
        
        input_method.trace('w', on_method_change)
        
        # Info label
        info_label = tk.Label(
            dialog,
            text="💡 Choose your preferred input method above",
            bg='#16213e',
            fg='#ffab00',
            font=('Arial', 9, 'italic')
        )
        info_label.pack(pady=5)
        
        def save():
            try:
                name = name_var.get().strip() or f"Room{len(self.rooms)+1}"
                layer = layer_var.get().strip() or "Room"
                
                if input_method.get() == "dimensions":
                    # Calculate from dimensions
                    w = float(w_var.get())
                    l = float(l_var.get())
                    
                    if w <= 0 or l <= 0:
                        messagebox.showerror("❌ Error", "Dimensions must be positive!")
                        return
                    
                    perim = 2 * (w + l)
                    area = w * l
                    
                else:
                    # Calculate from perimeter + area
                    perim = float(p_var.get())
                    area = float(a_var.get())
                    
                    if perim <= 0 or area <= 0:
                        messagebox.showerror("❌ Error", "Perimeter and Area must be positive!")
                        return
                    
                    # Estimate dimensions using quadratic formula
                    # P = 2(W+L) => W+L = P/2
                    # A = W*L
                    # L = P/2 - W
                    # A = W(P/2 - W) = WP/2 - W²
                    # W² - WP/2 + A = 0
                    # W = (P/2 ± √((P/2)² - 4A)) / 2
                    
                    half_p = perim / 2
                    discriminant = (half_p ** 2) - (4 * area)
                    
                    if discriminant < 0:
                        messagebox.showerror("❌ Error", "Invalid perimeter/area combination!")
                        return
                    
                    w = (half_p + (discriminant ** 0.5)) / 2
                    l = area / w if w > 0 else 0
                
                self.rooms.append({
                    'name': name,
                    'layer': layer,
                    'w': w,
                    'l': l,
                    'perim': perim,
                    'area': area
                })
                self.refresh_rooms()
                messagebox.showinfo("✓ Success", f"Room '{name}' added successfully!")
                dialog.destroy()
                self.update_status(f"Added room '{name}'", icon="🏠")
                
            except ValueError:
                messagebox.showerror("❌ Error", "Invalid number format!")
        
        # Button frame
        btn_frame = tk.Frame(dialog, bg='#16213e')
        btn_frame.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Button(
            btn_frame, 
            text="✓ Save Room", 
            command=save, 
            bg='#00e676', 
            fg='white', 
            font=('Arial', 11, 'bold'),
            width=15
        ).pack(side=tk.LEFT, padx=5, expand=True)
        
        tk.Button(
            btn_frame, 
            text="✗ Cancel", 
            command=dialog.destroy, 
            bg='#546e7a', 
            fg='white', 
            font=('Arial', 11),
            width=15
        ).pack(side=tk.LEFT, padx=5, expand=True)
    
    def edit_room(self):
        """Edit selected room with modern styling"""
        selection = self.rooms_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a room to edit!")
            return
        
        idx = self.rooms_tree.index(selection[0])
        room = self.rooms[idx]
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"✏️ Edit Room - {room.get('name', f'Room{idx+1}')}")
        dialog.geometry("420x340")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=(18, 14), style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Name", foreground=self.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=(0, 8))
        name_var = tk.StringVar(value=room.get('name', ''))
        ttk.Entry(frame, textvariable=name_var, width=26).grid(row=0, column=1, sticky='w', pady=(0, 8))
        
        ttk.Label(frame, text="Layer", foreground=self.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=8)
        layer_var = tk.StringVar(value=room.get('layer', ''))
        ttk.Entry(frame, textvariable=layer_var, width=26).grid(row=1, column=1, sticky='w', pady=8)
        
        ttk.Label(frame, text="Width (m)", foreground=self.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=8)
        w_var = tk.StringVar(value=str(room.get('w', '')))
        ttk.Entry(frame, textvariable=w_var, width=16).grid(row=2, column=1, sticky='w', pady=8)
        
        ttk.Label(frame, text="Length (m)", foreground=self.colors['text_secondary']).grid(row=3, column=0, sticky='w', pady=8)
        l_var = tk.StringVar(value=str(room.get('l', '')))
        ttk.Entry(frame, textvariable=l_var, width=16).grid(row=3, column=1, sticky='w', pady=8)
        
        ttk.Label(frame, text="Perimeter (m)", foreground=self.colors['text_secondary']).grid(row=4, column=0, sticky='w', pady=8)
        p_var = tk.StringVar(value=str(room.get('perim', '')))
        ttk.Entry(frame, textvariable=p_var, width=16).grid(row=4, column=1, sticky='w', pady=8)
        
        def save():
            try:
                name = name_var.get().strip() or room.get('name', f'Room{idx+1}')
                layer = layer_var.get().strip() or room.get('layer', 'Room')
                w_str = w_var.get().strip()
                l_str = l_var.get().strip()
                p = float(p_var.get())
                
                try:
                    w_f = float(w_str) if w_str else room.get('w')
                    l_f = float(l_str) if l_str else room.get('l')
                    area = w_f * l_f if (w_f and l_f) else room.get('area', 0)
                except:
                    w_f = room.get('w')
                    l_f = room.get('l')
                    area = room.get('area', 0)
                
                self.rooms[idx] = {
                    'name': name,
                    'layer': layer,
                    'w': w_f,
                    'l': l_f,
                    'perim': p,
                    'area': area
                }
                self.refresh_rooms()
                dialog.destroy()
                self.update_status(f"Updated room '{name}'", icon="🏠")
            except ValueError:
                messagebox.showerror("Error", "Invalid number format!")
        
        btn_frame = ttk.Frame(dialog, padding=(18, 10), style='Main.TFrame')
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="✓ Save", command=save, style='Accent.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="✗ Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT, padx=4)
    
    def delete_room(self):
        """Delete selected room"""
        selection = self.rooms_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a room to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected room?"):
            idx = self.rooms_tree.index(selection[0])
            del self.rooms[idx]
            self.refresh_rooms()
            self.update_status("Deleted room", icon="🏠")
    
    def edit_opening(self, opening_type):
        """Edit selected door/window with full metadata."""
        tree = self.doors_tree if opening_type == 'DOOR' else self.windows_tree
        storage = self._opening_storage(opening_type)
        type_catalog = self.door_types if opening_type == 'DOOR' else self.window_types

        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", f"Select a {opening_type.lower()} to edit!")
            return

        idx = tree.index(selection[0])
        item = storage[idx]

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {opening_type.title()} - {item.get('name', idx + 1)}")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=(18, 14), style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Name", foreground=self.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=(0, 6))
        name_var = tk.StringVar(value=item.get('name', ''))
        ttk.Entry(frame, textvariable=name_var, width=20).grid(row=0, column=1, sticky='w', pady=(0, 6))

        ttk.Label(frame, text="Layer", foreground=self.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=6)
        layer_var = tk.StringVar(value=item.get('layer', ''))
        ttk.Entry(frame, textvariable=layer_var, width=20).grid(row=1, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Type", foreground=self.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=6)
        type_var = tk.StringVar(value=item.get('type') or list(type_catalog.keys())[0])
        type_combo = ttk.Combobox(frame, textvariable=type_var, values=list(type_catalog.keys()), state='readonly', width=22)
        type_combo.grid(row=2, column=1, sticky='w', pady=6)

        info_var = tk.StringVar(value=type_catalog.get(type_var.get(), {}).get('description', ''))
        info_label = ttk.Label(frame, textvariable=info_var, wraplength=240, foreground=self.colors['text_secondary'])
        info_label.grid(row=2, column=2, sticky='w', padx=12, pady=6)

        ttk.Label(frame, text="Width (m)", foreground=self.colors['text_secondary']).grid(row=3, column=0, sticky='w', pady=6)
        w_var = tk.StringVar(value=f"{item.get('w', 0)}")
        ttk.Entry(frame, textvariable=w_var, width=12).grid(row=3, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Height (m)", foreground=self.colors['text_secondary']).grid(row=4, column=0, sticky='w', pady=6)
        h_var = tk.StringVar(value=f"{item.get('h', 0)}")
        ttk.Entry(frame, textvariable=h_var, width=12).grid(row=4, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Quantity", foreground=self.colors['text_secondary']).grid(row=5, column=0, sticky='w', pady=6)
        qty_var = tk.StringVar(value=str(item.get('qty', 1)))
        ttk.Entry(frame, textvariable=qty_var, width=12).grid(row=5, column=1, sticky='w', pady=6)

        weight_var = None
        weight_hint = None
        if opening_type == 'DOOR':
            default_weight_each = item.get('weight_each', item.get('weight', 0) / max(1, item.get('qty', 1)))
            ttk.Label(frame, text="Weight (kg each)", foreground=self.colors['text_secondary']).grid(row=6, column=0, sticky='w', pady=6)
            weight_var = tk.StringVar(value=f"{default_weight_each}")
            ttk.Entry(frame, textvariable=weight_var, width=12).grid(row=6, column=1, sticky='w', pady=6)
            weight_hint = ttk.Label(frame, text="", foreground=self.colors['warning'])
            weight_hint.grid(row=6, column=2, sticky='w', padx=12)
            preview_row = 7
        else:
            preview_row = 6

        preview_var = tk.StringVar(value="Preview: review values")
        preview_label = ttk.Label(frame, textvariable=preview_var, foreground=self.colors['accent'], font=('Segoe UI', 10, 'italic'))
        preview_label.grid(row=preview_row, column=0, columnspan=3, sticky='w', pady=(10, 4))

        def update_type_info(*_):
            info = type_catalog.get(type_var.get(), {})
            info_var.set(info.get('description', ''))
            if opening_type == 'DOOR' and weight_var is not None:
                default_weight = info.get('weight', 0)
                material = info.get('material', '').lower()
                if default_weight > 0 and material not in ('steel', 'metal'):
                    weight_var.set(str(default_weight))
                    if weight_hint:
                        weight_hint.config(text="")
                else:
                    if weight_hint:
                        if material in ('steel', 'metal'):
                            weight_hint.config(text="⚠️ Enter actual steel weight")
                        else:
                            weight_hint.config(text="")

        def update_preview(*_):
            try:
                width = float(w_var.get())
                height = float(h_var.get())
                qty = max(1, int(qty_var.get()))
                perim_each = 2 * (width + height)
                stone_total = perim_each * qty
                area_total = width * height * qty
                preview = f"Perim each: {perim_each:.2f} m • Stone total: {stone_total:.2f} lm"
                if opening_type == 'WINDOW':
                    glass_total = width * height * 0.85 * qty
                    preview += f" • Glass total: {glass_total:.2f} m²"
                preview += f" • Area total: {area_total:.2f} m²"
                preview_var.set(preview)
            except Exception:
                preview_var.set("Preview: enter valid values")

        type_combo.bind('<<ComboboxSelected>>', update_type_info)
        for var in (w_var, h_var, qty_var):
            var.trace_add('write', update_preview)
        update_type_info()
        update_preview()

        def save():
            try:
                desired_name = name_var.get().strip() or item.get('name') or (('D' if opening_type == 'DOOR' else 'W') + str(idx + 1))
                if desired_name != item.get('name') and any(other.get('name') == desired_name for j, other in enumerate(storage) if j != idx):
                    desired_name = self._make_unique_name(opening_type, desired_name)

                width = float(w_var.get())
                height = float(h_var.get())
                qty = max(1, int(qty_var.get()))
                weight_each = float(weight_var.get()) if weight_var is not None else 0.0

                if width <= 0 or height <= 0:
                    raise ValueError("Width and height must be positive")

                layer_value = layer_var.get().strip() or item.get('layer') or (type_var.get() or opening_type)

                updated = self._build_opening_record(opening_type,
                                                     desired_name,
                                                     type_var.get(),
                                                     width,
                                                     height,
                                                     qty,
                                                     weight_each,
                                                     layer=layer_value)
                storage[idx] = updated
                self.refresh_openings()
                dialog.destroy()
                icon = "🚪" if opening_type == 'DOOR' else "🪟"
                self.update_status(f"Updated {opening_type.lower()} '{updated.get('name', '-')}'", icon=icon)

            except ValueError as exc:
                messagebox.showerror("Error", f"Invalid input: {exc}")

        button_bar = ttk.Frame(dialog, padding=(18, 10), style='Main.TFrame')
        button_bar.pack(fill=tk.X)
        ttk.Button(button_bar, text="Save", command=save, style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)
    
    def delete_opening(self, opening_type):
        """Delete selected door/window"""
        tree = self.doors_tree if opening_type == 'DOOR' else self.windows_tree
        storage = self.doors if opening_type == 'DOOR' else self.windows
        
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", f"Select a {opening_type.lower()} to delete!")
            return
        
        if messagebox.askyesno("Confirm", f"Delete selected {opening_type.lower()}?"):
            idx = tree.index(selection[0])
            del storage[idx]
            self.refresh_openings()
            icon = "🚪" if opening_type == 'DOOR' else "🪟"
            self.update_status(f"Deleted {opening_type.lower()}", icon=icon)
    
    def edit_wall(self):
        """Edit selected wall with modern styling"""
        selection = self.walls_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a wall to edit!")
            return
        
        idx = self.walls_tree.index(selection[0])
        wall = self.walls[idx]
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"✏️ Edit Wall - {wall.get('name', f'Wall{idx+1}')}")
        dialog.geometry("400x280")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=(18, 14), style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Name", foreground=self.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=(0, 8))
        name_var = tk.StringVar(value=wall.get('name', ''))
        ttk.Entry(frame, textvariable=name_var, width=26).grid(row=0, column=1, sticky='w', pady=(0, 8))
        
        ttk.Label(frame, text="Layer", foreground=self.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=8)
        layer_var = tk.StringVar(value=wall.get('layer', ''))
        ttk.Entry(frame, textvariable=layer_var, width=26).grid(row=1, column=1, sticky='w', pady=8)
        
        ttk.Label(frame, text="Length (m)", foreground=self.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=8)
        l_var = tk.StringVar(value=str(wall.get('length', '')))
        ttk.Entry(frame, textvariable=l_var, width=16).grid(row=2, column=1, sticky='w', pady=8)
        
        ttk.Label(frame, text="Height (m)", foreground=self.colors['text_secondary']).grid(row=3, column=0, sticky='w', pady=8)
        h_var = tk.StringVar(value=str(wall.get('height', '')))
        ttk.Entry(frame, textvariable=h_var, width=16).grid(row=3, column=1, sticky='w', pady=8)
        
        def save():
            try:
                name = name_var.get().strip() or wall.get('name', f'Wall{idx+1}')
                layer = layer_var.get().strip() or wall.get('layer', 'Wall')
                length = float(l_var.get())
                height = float(h_var.get())
                
                if length <= 0 or height <= 0:
                    messagebox.showerror("Error", "Dimensions must be positive!")
                    return
                
                gross = length * height
                self.walls[idx] = {
                    'name': name,
                    'layer': layer,
                    'length': length,
                    'height': height,
                    'gross': gross,
                    'deduct': wall.get('deduct', 0),
                    'net': gross - wall.get('deduct', 0)
                }
                self.refresh_walls()
                dialog.destroy()
                self.update_status(f"Updated wall '{name}'", icon="🧱")
            except ValueError:
                messagebox.showerror("Error", "Invalid number format!")
        
        btn_frame = ttk.Frame(dialog, padding=(18, 10), style='Main.TFrame')
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="✓ Save", command=save, style='Accent.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="✗ Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT, padx=4)
    
    def delete_wall(self):
        """Delete selected wall"""
        selection = self.walls_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a wall to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected wall?"):
            idx = self.walls_tree.index(selection[0])
            del self.walls[idx]
            self.refresh_walls()
            self.update_status("Deleted wall", icon="🧱")
    
    def delete_multiple(self, data_type):
        """Delete multiple selected items with modern UI"""
        # Map data types to their storage and tree
        mappings = {
            'rooms': (self.rooms, self.rooms_tree, 'Rooms'),
            'doors': (self.doors, self.doors_tree, 'Doors'),
            'windows': (self.windows, self.windows_tree, 'Windows'),
            'walls': (self.walls, self.walls_tree, 'Walls')
        }
        
        if data_type not in mappings:
            return
        
        storage, tree, label = mappings[data_type]
        
        # Create modern selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"🗑️ Delete Multiple {label}")
        dialog.geometry("600x500")
        dialog.configure(bg='#16213e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        title_frame = tk.Frame(dialog, bg='#1a1a2e')
        title_frame.pack(fill=tk.X, pady=10)
        tk.Label(
            title_frame, 
            text=f"🗑️ Select {label} to Delete",
            bg='#1a1a2e',
            fg='#ff1744',
            font=('Arial', 14, 'bold')
        ).pack(pady=10)
        
        # Info label
        tk.Label(
            dialog,
            text=f"✓ Check items to delete • Total: {len(storage)} items",
            bg='#16213e',
            fg='#b0bec5',
            font=('Arial', 9)
        ).pack(pady=5)
        
        # Selection frame with scrollbar
        list_frame = tk.Frame(dialog, bg='#16213e')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Listbox with checkbuttons
        canvas = tk.Canvas(list_frame, bg='#0f0f1e', highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#0f0f1e')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create checkbuttons for each item
        check_vars = []
        for i, item in enumerate(storage):
            var = tk.BooleanVar()
            check_vars.append(var)
            
            # Create item display text
            if data_type == 'rooms':
                text = f"Room {i+1}: {item.get('name', 'N/A')} - {item.get('area', 0):.2f}m²"
            elif data_type == 'doors':
                text = f"Door {i+1}: {item.get('name', 'N/A')} - {item.get('type', 'N/A')} {item.get('w', 0)}×{item.get('h', 0)}m"
            elif data_type == 'windows':
                text = f"Window {i+1}: {item.get('name', 'N/A')} - {item.get('type', 'N/A')} {item.get('w', 0)}×{item.get('h', 0)}m"
            else:  # walls
                text = f"Wall {i+1}: {item.get('name', 'N/A')} - {item.get('length', 0):.2f}×{item.get('height', 0):.2f}m"
            
            cb = tk.Checkbutton(
                scrollable_frame,
                text=text,
                variable=var,
                bg='#0f0f1e',
                fg='#ffffff',
                selectcolor='#1a1a2e',
                activebackground='#16213e',
                activeforeground='#00d9ff',
                font=('Arial', 10),
                anchor='w'
            )
            cb.pack(fill=tk.X, padx=10, pady=2)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        btn_frame = tk.Frame(dialog, bg='#16213e')
        btn_frame.pack(fill=tk.X, padx=20, pady=15)
        
        def select_all():
            for var in check_vars:
                var.set(True)
        
        def deselect_all():
            for var in check_vars:
                var.set(False)
        
        def delete_selected():
            # Get indices to delete (in reverse order to avoid index issues)
            to_delete = [i for i, var in enumerate(check_vars) if var.get()]
            
            if not to_delete:
                messagebox.showwarning("⚠️ No Selection", "Please select at least one item to delete!")
                return
            
            # Confirm deletion
            count = len(to_delete)
            if not messagebox.askyesno("🗑️ Confirm Deletion", f"Delete {count} selected {label.lower()}?"):
                return
            
            # Delete in reverse order
            for i in reversed(to_delete):
                del storage[i]
            
            # Refresh appropriate view
            if data_type == 'rooms':
                self.refresh_rooms()
            elif data_type in ['doors', 'windows']:
                self.refresh_openings()
            elif data_type == 'walls':
                self.refresh_walls()
            
            messagebox.showinfo("✓ Success", f"Deleted {count} {label.lower()}!")
            dialog.destroy()
            icons = {
                'rooms': '🏠',
                'doors': '🚪',
                'windows': '🪟',
                'walls': '🧱'
            }
            self.update_status(f"Deleted {count} {label.lower()}", icon=icons.get(data_type, '🗑️'))
        
        tk.Button(
            btn_frame, 
            text="✓ Select All", 
            command=select_all, 
            bg='#00e676', 
            fg='white', 
            font=('Arial', 10, 'bold'),
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, 
            text="✗ Deselect All", 
            command=deselect_all, 
            bg='#ffab00', 
            fg='white', 
            font=('Arial', 10, 'bold'),
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, 
            text="🗑️ Delete Selected", 
            command=delete_selected, 
            bg='#ff1744', 
            fg='white', 
            font=('Arial', 10, 'bold'),
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, 
            text="Cancel", 
            command=dialog.destroy, 
            bg='#546e7a', 
            fg='white', 
            font=('Arial', 10),
            width=10
        ).pack(side=tk.LEFT, padx=5)
    
    def reset_all(self):
        """Reset all data"""
        if messagebox.askyesno("Reset", "Clear ALL data?"):
            self.rooms.clear()
            self.doors.clear()
            self.windows.clear()
            self.walls.clear()
            self.plaster_items.clear()
            self.paint_items.clear()
            self.tiles_items.clear()
            self.ceramic_zones.clear()
            
            self.refresh_rooms()
            self.refresh_openings()
            self.refresh_walls()
            self.update_finish_labels()
            self.refresh_materials_tab()
            self.update_summary()
            self.update_status("All data cleared", icon="🧹")

if __name__ == "__main__":
    root = tk.Tk()
    app = BilindEnhanced(root)
    root.mainloop()
