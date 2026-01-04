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
from pathlib import Path
from datetime import datetime
import time
import threading
from typing import List, Optional, Dict, Any, Set

# Import from modular structure
from bilind.core.config import DOOR_TYPES, WINDOW_TYPES, COLOR_SCHEME
from bilind.core.theme import ThemeManager
from bilind.ui.modern_styles import ModernStyleManager
from bilind.calculations.helpers import build_opening_record, format_number
from bilind.calculations.unified_calculator import UnifiedCalculator
from bilind.calculations.room_metrics import (
    RoomMetricsContext,
    RoomFinishMetrics,
    build_room_metrics_context,
    calculate_room_finish_metrics,
)
from bilind.models import Room, Opening, Wall, FinishItem
from bilind.models.project import Project
from bilind.models.finish import CeramicZone
from bilind.models.association import RoomOpeningAssociation
from bilind.autocad import AutoCADPicker
from bilind.ui.tabs.rooms_tab import RoomsTab
from bilind.ui.tabs.room_manager_tab import RoomManagerTab
from bilind.ui.tabs.floors_tab import FloorsTab
from bilind.ui.tabs.walls_tab import WallsTab
from bilind.ui.tabs.coatings_tab import CoatingsTab
from bilind.ui.tabs.ceramic_tab import CeramicTab
from bilind.ui.tabs.summary_tab import SummaryTab
from bilind.ui.tabs.dashboard_tab import DashboardTab
from bilind.ui.tabs.sync_log_tab import SyncLogTab
from bilind.ui.tabs.costs_tab import CostsTab
from bilind.ui.tabs.settings_tab import SettingsTab
from bilind.ui.tabs.material_estimator_tab import MaterialEstimatorTab
from bilind.ui.dialogs import OpeningAssignmentDialog
from bilind.ui.mini_picker import MiniPicker
from bilind.models.room import ROOM_TYPES
from bilind.export import export_to_csv, export_to_pdf, export_comprehensive_book, insert_table_to_autocad
from bilind.core.project_manager import save_project, load_project

HAS_AUTOCAD_DEPS = True
try:
    from pyautocad import Autocad
    import win32com.client
    import pythoncom
except ImportError:
    # Allow the app to run without AutoCAD dependencies.
    # AutoCAD-only features will prompt the user when used.
    HAS_AUTOCAD_DEPS = False
    Autocad = None
    win32com = None

    class _DummyPythoncom:
        class com_error(Exception):
            pass

    pythoncom = _DummyPythoncom()

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:
    messagebox.showerror("Missing Dependency", "Openpyxl is required for Excel export. Please run: pip install openpyxl")
    # Disable Excel export button if library is missing
    # This will be handled where the button is created.
    pass

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.units import inch
except ImportError:
    messagebox.showerror("Missing Dependency", "ReportLab is required for PDF export. Please run: pip install reportlab")
    pass

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    messagebox.showerror("Missing Dependency", "Matplotlib is required for the dashboard. Please run: pip install matplotlib")
    pass

class BilindEnhanced:
    """
    Main application class for the BILIND Enhanced AutoCAD Calculator.

    This class encapsulates the entire Tkinter application, including the UI,
    AutoCAD interaction, data management, and calculations.
    """
    def __init__(self, root):
        """
        Initializes the main application window, data structures, and UI.

        Args:
            root (tk.Tk): The root Tkinter window.
        """
        self.root = root
        self.root.title("BILIND Enhanced")
        self.root.geometry("1040x780")

        # App icon (works even without AutoCAD)
        self._icon_image = None
        self._set_app_icon()
        
        # Modern styling with ttkbootstrap
        self.modern_style = ModernStyleManager(root, theme_name='cyborg')
        
        # Theme manager: support multiple modern palettes
        self.theme = ThemeManager(default="neo")
        self.colors = dict(COLOR_SCHEME)
        # Allow theme override
        try:
            self.colors.update(self.theme.colors)
        except Exception:
            pass
        self.root.configure(bg=self.colors['bg_primary'])
        self.modern_style.set_palette(self.colors)

        # Use material catalogs from config module
        self.door_types = DOOR_TYPES
        self.window_types = WINDOW_TYPES
        
        # AutoCAD connection is optional (connect lazily, on-demand)
        self.acad = None
        self.doc = None
        self.picker = None
        self._autocad_connected_once = False
        self._connect_autocad(initial=True)

        # --- Data Storage ---
        self.project = Project()
        self.current_project_path: Optional[str] = None
        self.scale = float(self.project.scale or 1.0)
        self._sync_project_references()
        
        # UI widget references (will be set by tabs during create())
        self.walls_tree = None
        self.walls_filter = None
        self.wall_metrics_var = None
        self.scale_var = None
        
        self._status_after_id = None
        self._default_status = "Ready"

        self.sync_thread = None
        self.is_syncing = False
        
        # Room-Opening Association Manager (Phase 7)
        self._rebuild_association()
        
        self.create_ui()
        self.create_menu()
        self._install_global_mousewheel()

    def _app_root_dir(self) -> Path:
        return Path(__file__).resolve().parent

    def _set_app_icon(self) -> None:
        """Set a custom app icon (Windows/Linux). Safe to call repeatedly."""
        try:
            icon_path = self._app_root_dir() / 'bilind' / 'assets' / 'bilind_icon.ppm'
            if icon_path.exists():
                self._icon_image = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, self._icon_image)
        except Exception:
            # Non-fatal: icon is cosmetic.
            self._icon_image = None

    def _doc_display_name(self) -> str:
        try:
            if self.doc is not None and hasattr(self.doc, 'Name'):
                return str(self.doc.Name)
        except Exception:
            pass
        return "(AutoCAD not connected)"

    def _refresh_window_title(self) -> None:
        try:
            self.root.title(f"BILIND Enhanced - {self._doc_display_name()}")
        except Exception:
            pass

    def _connect_autocad(self, *, initial: bool = False, show_message: bool = False) -> bool:
        """Try connecting to a running AutoCAD instance. Returns True on success."""
        if not HAS_AUTOCAD_DEPS or Autocad is None:
            self.acad = None
            self.doc = None
            self.picker = None
            if show_message and not initial:
                messagebox.showwarning(
                    "AutoCAD Not Available",
                    "AutoCAD integration is not available because dependencies are missing.\n\n"
                    "Install: pip install pyautocad pywin32"
                )
            self.update_status("AutoCAD not available (dependencies missing)", icon="⚠️")
            self._refresh_window_title()
            return False

        try:
            if initial:
                self.update_status("AutoCAD: not connected (you can connect when needed)", icon="⚙️")

            acad = Autocad(create_if_not_exists=False)
            doc = acad.doc
            picker = AutoCADPicker(acad, doc)

            self.acad = acad
            self.doc = doc
            self.picker = picker
            self._autocad_connected_once = True

            self.update_status(f"Connected to {self._doc_display_name()}", icon="✅")
            self._refresh_window_title()
            return True
        except Exception as e:
            self.acad = None
            self.doc = None
            self.picker = None

            if show_message and not initial:
                messagebox.showwarning(
                    "AutoCAD Not Available",
                    "AutoCAD must be running with a drawing open for picking.\n\n"
                    f"Details: {e}"
                )
            if not initial:
                self.update_status("AutoCAD not connected", icon="⚠️")
            self._refresh_window_title()
            return False

    def ensure_autocad(self) -> bool:
        """Ensure AutoCAD is connected (connects on-demand)."""
        if self.acad is not None and self.doc is not None and self.picker is not None:
            return True
        return self._connect_autocad(initial=False, show_message=True)

    def apply_theme(self, name: str):
        """Apply a theme by name and refresh styles across the app."""
        self.theme.set_theme(name)
        self.colors = dict(COLOR_SCHEME)
        self.colors.update(self.theme.colors)
        self.root.configure(bg=self.colors['bg_primary'])
        self.modern_style.set_palette(self.colors)
        self._setup_styles()
        self.modern_style.refresh_custom_buttons()
        self.refresh_all_tabs()

    def create_button(self, parent, text, command, variant='accent', width=156, height=42):
        """Factory to create rounded buttons with palette awareness."""
        if hasattr(self, 'modern_style') and hasattr(self.modern_style, 'create_button'):
            return self.modern_style.create_button(
                parent,
                text,
                command,
                variant=variant,
                palette=self.colors,
                width=width,
                height=height
            )

        style_map = {
            'accent': 'Accent.TButton',
            'secondary': 'Secondary.TButton',
            'danger': 'Danger.TButton',
            'warning': 'Warning.TButton',
            'success': 'Accent.TButton',
            'info': 'Accent.TButton'
        }
        style = style_map.get(variant, 'Accent.TButton')
        return ttk.Button(parent, text=text, command=command, style=style)

    def _install_global_mousewheel(self):
        """Smooth, consistent scrolling for Treeview/Canvas across Windows."""
        def _on_mousewheel(event):
            widget = event.widget
            # Traverse up the widget hierarchy to find a scrollable widget
            current = widget
            while current:
                if hasattr(current, 'yview') and (isinstance(current, (tk.Canvas, ttk.Treeview, tk.Listbox, tk.Text))):
                    # Found a scrollable widget
                    try:
                        delta = int(-1 * (event.delta / 120))
                        current.yview_scroll(delta, 'units')
                        return 'break'  # Stop propagation
                    except Exception:
                        pass
                # Move to parent
                parent = getattr(current, 'master', None)
                if not parent or parent == current:
                    break
                current = parent
            return None

        # Bind to all widgets globally
        self.root.bind_all('<MouseWheel>', _on_mousewheel)

    # === INTERNAL STATE SYNC / SCALE ===
    def _sync_project_references(self):
        """Keep backward-compat variables pointing to Project lists."""
        # Back-compat aliases so legacy code (and some tabs) keep working
        self.plaster_items = self.project.plaster_items
        self.paint_items = self.project.paint_items
        self.tiles_items = self.project.tiles_items
        self.ceramic_zones = self.project.ceramic_zones
        self.material_costs = self.project.material_costs

    def _rebuild_association(self):
        """Recreate room-opening association with current project lists."""
        self.association = RoomOpeningAssociation(self.project.rooms, self.project.doors, self.project.windows)

    def update_scale(self):
        """Read UI scale, update self.scale and project.scale safely."""
        try:
            if isinstance(self.scale_var, tk.StringVar):
                val = float(self.scale_var.get().strip() or "1.0")
            else:
                val = float(self.scale or 1.0)
        except Exception:
            val = 1.0
        self.scale = max(0.0001, val)
        self.project.scale = self.scale

    def create_menu(self):
        """Creates the main application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project...", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_command(label="Save Project As...", command=self.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    # === PROJECT MANAGEMENT (SAVE/LOAD) =====================================

    def new_project(self):
        """Clears all data and starts a new project."""
        if messagebox.askyesno("New Project", "This will clear all current data. Are you sure you want to continue?"):
            self.project = Project()
            self.current_project_path = None
            self._sync_project_references()
            self._rebuild_association()
            self._refresh_window_title()
            self.refresh_all_tabs()
            self.update_status("✨ New project started.", icon="📄")

    def open_project(self):
        """Opens a project from a .bilind file."""
        loaded_project, filepath = load_project(status_callback=self.update_status)
        if not loaded_project:
            return

        try:
            self.project = loaded_project
            self.current_project_path = filepath
            self._sync_project_references()
            self._rebuild_association()
            
            # Normalize ceramic zones immediately after loading (fix legacy data)
            try:
                from bilind.calculations.ceramic_zone_normalizer import normalize_ceramic_wall_zones
                updated, skipped = normalize_ceramic_wall_zones(self.project)
                if updated > 0:
                    self.update_status(f"🔧 Normalized {updated} ceramic zones", icon="🔧")
            except Exception:
                pass
            
            self.root.title(f"BILIND Enhanced - {os.path.basename(filepath)}")
            
            self.refresh_all_tabs()
            
            self.update_status(f"✅ Project '{os.path.basename(filepath)}' loaded successfully.", icon="📂")
        except Exception as e:
            messagebox.showerror("Error Loading Project", f"Failed to load project file:\n{e}")
            self.update_status(f"❌ Error loading project: {e}", icon="❌")

    def save_project(self):
        """Saves the current project to its existing path, or prompts for a new one."""
        if not self.current_project_path:
            self.save_project_as()
        else:
            try:
                save_project(self.current_project_path, self.project)
                self.update_status(f"✅ Project saved to '{os.path.basename(self.current_project_path)}'.", icon="💾")
            except Exception as e:
                messagebox.showerror("Error Saving Project", f"Failed to save project file:\n{e}")
                self.update_status(f"❌ Error saving project: {e}", icon="❌")

    def save_project_as(self):
        """Saves the current project to a new .bilind file."""
        filepath = filedialog.asksaveasfilename(
            title="Save BILIND Project As",
            defaultextension=".bilind",
            filetypes=[("BILIND Project Files", "*.bilind"), ("All files", "*")]
        )
        if not filepath:
            return

        try:
            save_project(filepath, self.project)
            self.current_project_path = filepath
            self.root.title(f"BILIND Enhanced - {os.path.basename(filepath)}")
            self.update_status(f"✅ Project saved as '{os.path.basename(filepath)}'.", icon="💾")
        except Exception as e:
            messagebox.showerror("Error Saving Project", f"Failed to save project file:\n{e}")
            self.update_status(f"❌ Error saving project: {e}", icon="❌")

    def refresh_all_tabs(self):
        """Refreshes the data in all UI tabs - complete synchronization."""
        # Group 1: Data Input
        if hasattr(self, 'floors_tab'): self.floors_tab.refresh_data()
        if hasattr(self, 'room_manager_tab'): self.room_manager_tab.refresh_rooms_list()
        if hasattr(self, 'rooms_tab'): self.rooms_tab.refresh_data()
        
        # Group 2: Calculations
        if hasattr(self, 'walls_tab'): self.walls_tab.refresh_data()
        if hasattr(self, 'ceramic_tab'): self.ceramic_tab.refresh_data()
        if hasattr(self, 'coatings_tab'): self.coatings_tab.refresh_data()
        
        # Group 3: Output & Reports
        if hasattr(self, 'summary_tab'): self.summary_tab.refresh_data()
        if hasattr(self, 'quantities_tab'): self.quantities_tab.refresh_data()
        if hasattr(self, 'dashboard_tab'): self.dashboard_tab.refresh_data()
        if hasattr(self, 'costs_tab'): self.costs_tab.refresh_data()
        if hasattr(self, 'material_estimator_tab'): self.material_estimator_tab.refresh_data()
        
        # Legacy tabs (kept for compatibility)
        if hasattr(self, 'finishes_tab'): self.finishes_tab.refresh_data()
        if hasattr(self, 'materials_tab'): self.materials_tab.refresh_data()

    # === STYLE & HELPERS ================================================== #

    def _setup_styles(self):
        """Configure ttk styles for a modern dark UI with ttkbootstrap enhancements."""
        # Use ModernStyleManager's style instance (already configured with ttkbootstrap)
        style = self.modern_style.style if hasattr(self.modern_style, 'style') else ttk.Style()
        
        # If ttkbootstrap not available, fallback to clam
        if not self.modern_style.is_available():
            try:
                style.theme_use('clam')
            except tk.TclError:
                pass

        colors = self.colors
        style.configure('Main.TFrame', background=colors['bg_secondary'])
        style.configure('Card.TLabelframe',
            background=colors['bg_card'],
            foreground=colors['text_secondary'],
            relief='solid',
            borderwidth=1,
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

        # Modern scrollbars
        style.configure('Vertical.TScrollbar',
                        background=colors['bg_card'],
                        troughcolor=colors['bg_secondary'],
                        bordercolor=colors['border'],
                        lightcolor=colors['bg_card'],
                        darkcolor=colors['bg_card'])

    def _opening_storage(self, opening_type):
        return self.project.doors if opening_type == 'DOOR' else self.project.windows

    def _opening_to_dict(self, opening):
        """Return a dictionary representation of an opening (door/window)."""
        if isinstance(opening, dict):
            return opening
        if hasattr(opening, 'to_dict'):
            weight = 0.0
            if getattr(opening, 'opening_type', '').upper() == 'DOOR':
                weight = self.door_types.get(getattr(opening, 'material_type', ''), {}).get('weight', 0.0)
            data = opening.to_dict(weight=weight)
            # Ensure essential fields exist
            data.setdefault('name', getattr(opening, 'name', ''))
            data.setdefault('layer', getattr(opening, 'layer', ''))
            data.setdefault('type', getattr(opening, 'material_type', ''))
            data.setdefault('qty', getattr(opening, 'quantity', 1))
            return data
        return {
            'name': getattr(opening, 'name', ''),
            'layer': getattr(opening, 'layer', ''),
            'type': getattr(opening, 'material_type', ''),
            'w': getattr(opening, 'width', 0.0),
            'h': getattr(opening, 'height', 0.0),
            'qty': getattr(opening, 'quantity', 1),
            'perim': getattr(opening, 'perimeter', 0.0),
            'area': getattr(opening, 'area', 0.0),
            'stone': getattr(opening, 'stone_linear', 0.0),
            'weight': getattr(opening, 'weight', 0.0),
            'glass': getattr(opening, 'calculate_glass_area', lambda: 0.0)() if hasattr(opening, 'calculate_glass_area') else 0.0
        }
    
    # Helper methods for Room Manager tab
    def _room_name(self, room):
        """Get room name (works with dict or Room object)."""
        if isinstance(room, dict):
            return room.get('name', '-')
        return getattr(room, 'name', '-')
    
    def _room_attr(self, room, dict_key, obj_attr, default=None):
        """Get room attribute (works with dict or Room object)."""
        if isinstance(room, dict):
            return room.get(dict_key, default)
        return getattr(room, obj_attr, default)
    
    def _opening_name(self, opening):
        """Get opening name (works with dict or Opening object)."""
        if isinstance(opening, dict):
            return opening.get('name', '-')
        return getattr(opening, 'name', '-')
    
    def _opening_attr(self, opening, dict_key, obj_attr, default=None):
        """Get opening attribute (works with dict or Opening object)."""
        if isinstance(opening, dict):
            return opening.get(dict_key, default)
        return getattr(opening, obj_attr, default)

    def _zone_attr(self, zone, key, default=None):
        """Safely read ceramic zone attributes for dicts or objects."""
        if isinstance(zone, dict):
            return zone.get(key, default)
        return getattr(zone, key, default)

    def _get_opening_dict_by_name(self, opening_id: str):
        for collection in (self.project.doors, self.project.windows):
            for opening in collection:
                data = self._opening_to_dict(opening)
                if data.get('name') == opening_id:
                    return data
        return None

    def _ensure_room_names(self):
        for idx, room in enumerate(self.project.rooms, start=1):
            if isinstance(room, Room):
                # Room objects already have names, no need to update
                pass
            else:
                room.setdefault('name', f"Room{idx}")

    def _ensure_wall_names(self):
        for idx, wall in enumerate(self.project.walls, start=1):
            if isinstance(wall, Wall):
                # Wall objects already have names, no need to update
                pass
            else:
                wall.setdefault('name', f"Wall{idx}")

    def _ensure_opening_names(self, opening_type):
        storage = self._opening_storage(opening_type)
        prefix = 'D' if opening_type == 'DOOR' else 'W'
        for idx, item in enumerate(storage, start=1):
            if isinstance(item, Opening):
                # Opening objects already have names, no need to update
                pass
            else:
                item.setdefault('name', f"{prefix}{idx}")

    def _make_unique_name(self, opening_type, base_name):
        storage = self._opening_storage(opening_type)
        existing = set()
        for item in storage:
            if isinstance(item, Opening):
                existing.add(item.name)
            elif isinstance(item, dict):
                name = item.get('name')
                if name:
                    existing.add(name)
        
        if base_name not in existing:
            return base_name
        suffix = 2
        while f"{base_name}{suffix}" in existing:
            suffix += 1
        return f"{base_name}{suffix}"

    def _sync_project_references(self):
        """Mirror project collections onto legacy attributes used by the UI."""
        self.rooms = self.project.rooms
        self.doors = self.project.doors
        self.windows = self.project.windows
        self.walls = self.project.walls
        self.plaster_items = self.project.plaster_items
        self.paint_items = self.project.paint_items
        self.tiles_items = self.project.tiles_items
        self.ceramic_zones = self.project.ceramic_zones
        self.material_costs = self.project.material_costs

    def _rebuild_association(self):
        """Recreate the room-opening association helper to track current data."""
        self.association = RoomOpeningAssociation(self.project.rooms, self.project.doors, self.project.windows)

    def update_scale(self):
        """Read the UI scale entry and update internal/project scale values."""
        if not self.scale_var:
            return

        try:
            value = float(self.scale_var.get())
            if value <= 0:
                raise ValueError
        except (TypeError, ValueError):
            messagebox.showwarning("Invalid Scale", "Scale must be a positive number.")
            self.scale_var.set(f"{self.scale:.3f}")
            return

        self.scale = value
        self.project.scale = value

    def _build_opening_record(self, opening_type, name, type_label, width, height, qty, weight=0.0, layer=None, placement_height=None, total_count=None):
        """Create a normalized dictionary for doors/windows using imported helper."""
        return build_opening_record(opening_type, name, type_label, width, height, qty, weight, layer, placement_height, total_count)

    def _store_autocad_openings(self, opening_type: str, openings: List[Any]):
        """Normalize and append openings imported from AutoCAD selection."""
        storage = self._opening_storage(opening_type)
        prefix = 'D' if opening_type == 'DOOR' else 'W'
        added_names: List[str] = []
        skipped = 0

        for entry in openings:
            try:
                if isinstance(entry, Opening):
                    type_label = entry.material_type or 'AutoCAD Block'
                    width = float(entry.width)
                    height = float(entry.height)
                    qty = int(entry.quantity or 1)
                    placement = entry.placement_height
                    layer = entry.layer
                    base_name = entry.name or f"{prefix}{len(storage) + len(added_names) + 1}"
                elif isinstance(entry, dict):
                    type_label = entry.get('material_type') or entry.get('type') or 'AutoCAD Block'
                    width = float(entry.get('width', entry.get('w', 0.0)) or 0.0)
                    height = float(entry.get('height', entry.get('h', 0.0)) or 0.0)
                    qty = int(entry.get('quantity', entry.get('qty', 1)) or 1)
                    placement = entry.get('placement_height')
                    layer = entry.get('layer')
                    base_name = entry.get('name') or f"{prefix}{len(storage) + len(added_names) + 1}"
                else:
                    skipped += 1
                    continue

                if width <= 0 or height <= 0 or qty <= 0:
                    skipped += 1
                    continue

                unique_name = self._make_unique_name(opening_type, base_name)
                record = self._build_opening_record(
                    opening_type,
                    unique_name,
                    type_label,
                    width,
                    height,
                    qty,
                    0.0,
                    layer=layer,
                    placement_height=placement
                )
                storage.append(record)
                added_names.append(unique_name)
            except Exception:
                skipped += 1

        return added_names, skipped

    def _link_opening_to_room(self, opening_name: Optional[str], room_name: Optional[str]):
        """Assign a single opening to a specific room via association helper."""
        if not opening_name or not room_name or not hasattr(self, 'association') or not self.association:
            return 0
        try:
            return self.association.assign_opening_to_rooms(opening_name, [room_name], mode='add')
        except Exception:
            return 0

    def _unlink_opening_from_all_rooms(self, opening_name: Optional[str]):
        """Remove an opening reference from every room (used before deleting openings)."""
        if not opening_name or not hasattr(self, 'association') or not self.association:
            return 0
        removed = 0
        for room in self.project.rooms:
            ids = self.association.get_room_opening_ids(room) or []
            if opening_name in ids:
                new_ids = [oid for oid in ids if oid != opening_name]
                self.association.set_room_opening_ids(room, new_ids)
                removed += 1
        return removed

    def _remove_opening_from_walls(self, opening_name: str):
        """Remove an opening reference from all walls in all rooms."""
        if not opening_name:
            return
        for room in self.project.rooms:
            walls = room.get('walls') if isinstance(room, dict) else getattr(room, 'walls', None)
            if not walls:
                continue
            for wall in walls:
                wall_openings = wall.get('opening_ids') if isinstance(wall, dict) else getattr(wall, 'opening_ids', None)
                if wall_openings and opening_name in wall_openings:
                    if isinstance(wall, dict):
                        wall['opening_ids'] = [oid for oid in wall_openings if oid != opening_name]
                    else:
                        wall.opening_ids = [oid for oid in wall_openings if oid != opening_name]

    def _fmt(self, value, digits=2, default='-'):
        """Format numeric value for display using imported helper."""
        use_thousands = bool(getattr(self.project, 'use_thousands_separator', False))
        return format_number(value, digits, default, thousands=use_thousands)

    def _calc_costs(self):
        """Bridge to CostsTab calculation logic."""
        if hasattr(self, 'costs_tab'):
            return self.costs_tab.calculate_total_cost()
        return 0.0, []

    def update_status(self, message, icon=""):
        """Update the persistent status bar with an optional icon."""
        if not hasattr(self, 'status_var'):
            return

        display_text = f"{icon} {message}".strip() if icon else message
        self.status_var.set(display_text)

        if self._status_after_id:
            self.root.after_cancel(self._status_after_id)
        self._status_after_id = self.root.after(4500, lambda: self.status_var.set(self._default_status))

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        current = self.current_theme_name.get()
        
        # Cycle: neo (dark) -> light -> neo
        if current in ['neo', 'plum', 'emerald']:
            new_theme = 'light'
            btn_text = "🌙 Dark"
        else:
            new_theme = 'neo'
            btn_text = "☀️ Light"
        
        # Apply theme
        self.theme.set_theme(new_theme)
        self.current_theme_name.set(new_theme)
        
        # Update button text (find it in status_bar_frame)
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Frame):
                        for btn in subchild.winfo_children():
                            if isinstance(btn, ttk.Button) and '☀️' in btn['text'] or '🌙' in btn['text']:
                                btn.config(text=btn_text)
        
        # Re-apply styles
        self._setup_styles()
        
        self.update_status(f"Theme switched to {new_theme.capitalize()}", icon="🎨")

    def get_room_opening_summary(self, room):
        """Get a summary of openings assigned to a room (returns dict)."""
        if not hasattr(self, 'association'):
            return {'door_ids': [], 'window_ids': [], 'door_count': 0, 'window_count': 0}
        return self.association.get_summary_dict_for_room(room)
    
    def get_room_opening_summary_text(self, room):
        """Get a text summary of openings assigned to a room (returns string)."""
        if not hasattr(self, 'association'):
            return "N/A"
        return self.association.get_summary_for_room(room)
    
    def get_opening_counts(self):
        """
        Get actual vs appearance counts for doors/windows.
        
        Returns dict with:
        - actual_doors/windows: Physical count (unique items)
        - total_door/window_qty: Sum of quantities
        - appearance_doors/windows: Count across all rooms (may double-count shared)
        - shared_doors/windows: Count of shared openings
        - door/window_details: Detailed breakdown
        """
        if not hasattr(self, 'association'):
            return {
                'actual_doors': len(self.project.doors),
                'actual_windows': len(self.project.windows),
                'total_door_qty': sum(int(d.get('qty', 1) or d.get('quantity', 1) or 1) if isinstance(d, dict) else int(getattr(d, 'qty', 1) or getattr(d, 'quantity', 1) or 1) for d in self.project.doors),
                'total_window_qty': sum(int(w.get('qty', 1) or w.get('quantity', 1) or 1) if isinstance(w, dict) else int(getattr(w, 'qty', 1) or getattr(w, 'quantity', 1) or 1) for w in self.project.windows),
                'appearance_doors': 0,
                'appearance_windows': 0,
                'shared_doors': 0,
                'shared_windows': 0,
                'door_details': [],
                'window_details': []
            }
        return self.association.get_opening_counts()

    def refresh_rooms(self):
        """Delegates refreshing rooms to all room-dependent tabs."""
        # Input tabs
        if hasattr(self, 'rooms_tab'):
            self.rooms_tab.refresh_data()
        if hasattr(self, 'room_manager_tab'):
            self.room_manager_tab.refresh_rooms_list()
        if hasattr(self, 'floors_tab'):
            self.floors_tab.refresh_data()
        
        # Calculation tabs (rooms affect ceramic zones and coatings)
        if hasattr(self, 'ceramic_tab'):
            self.ceramic_tab.refresh_data()
        if hasattr(self, 'coatings_tab'):
            self.coatings_tab.refresh_data()
        
        # Output tabs
        if hasattr(self, 'summary_tab'):
            self.summary_tab.refresh_data()
        if hasattr(self, 'quantities_tab'):
            self.quantities_tab.refresh_data()

    def refresh_openings(self):
        """Delegates refreshing openings to all opening-dependent tabs."""
        # Input tabs
        if hasattr(self, 'rooms_tab'):
            self.rooms_tab.refresh_data()
        # Refresh Room Manager openings if a room is selected
        if hasattr(self, 'room_manager_tab') and self.room_manager_tab.selected_room:
            self.room_manager_tab._refresh_openings_trees()
        
        # Calculation tabs (openings affect coatings deductions)
        if hasattr(self, 'ceramic_tab'):
            self.ceramic_tab.refresh_data()
        if hasattr(self, 'coatings_tab'):
            self.coatings_tab.refresh_data()
        
        # Output tabs
        if hasattr(self, 'summary_tab'):
            self.summary_tab.refresh_data()
        if hasattr(self, 'quantities_tab'):
            self.quantities_tab.refresh_data()

    def refresh_walls(self):
        """Delegates refreshing walls to all wall-dependent tabs."""
        if hasattr(self, 'walls_tab'):
            self.walls_tab.refresh_data()
        # Refresh Room Manager walls if a room is selected
        if hasattr(self, 'room_manager_tab') and self.room_manager_tab.selected_room:
            if hasattr(self.room_manager_tab, '_refresh_walls_tree'):
                self.room_manager_tab._refresh_walls_tree()
        
        # CRITICAL: Update ceramic zones when walls change (perimeter affects ceramic calculations)
        self._update_ceramic_zones_after_wall_change()
        if hasattr(self, 'ceramic_tab'):
            self.ceramic_tab.refresh_data()
        
        # Output tabs
        if hasattr(self, 'summary_tab'):
            self.summary_tab.refresh_data()
        if hasattr(self, 'quantities_tab'):
            self.quantities_tab.refresh_data()
    
    def refresh_finishes_tab(self):
        """Delegates refreshing finishes to the finishes_tab."""
        if hasattr(self, 'finishes_tab'):
            self.finishes_tab.refresh_data()
    
    def enhance_treeview(self, treeview):
        """Apply modern styling enhancements to a treeview widget."""
        if hasattr(self, 'modern_style'):
            self.modern_style.enhance_treeview(treeview)
    
    def create_ui(self):
        """
        Creates the main user interface, including the notebook with all functional tabs.
        Organized logically: Input → Calculations → Output
        """
        self.status_var = tk.StringVar(value="Ready")
        self._setup_styles()
        notebook = ttk.Notebook(self.root)
        notebook.configure(style='Accent.TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 0))
        tab_bg = self.colors['bg_secondary']
        
        # ═══════════════════════════════════════════════════════════════
        # GROUP 1: DATA INPUT (الإدخال)
        # ═══════════════════════════════════════════════════════════════
        
        # Tab 1: Floors & Rooms Overview
        self.floors_tab = FloorsTab(notebook, self)
        tab_floors = self.floors_tab.create()
        notebook.add(tab_floors, text="🏢 الأدوار")
        
        # Tab 2: Room Manager (Main editing interface)
        self.room_manager_tab = RoomManagerTab(notebook, self)
        
        # Tab 3: Main Data (rooms/doors/windows picking)
        self.rooms_tab = RoomsTab(notebook, self)
        tab1 = self.rooms_tab.create()
        notebook.add(tab1, text="📐 البيانات")
        
        # ═══════════════════════════════════════════════════════════════
        # GROUP 2: CALCULATIONS (الحسابات)
        # ═══════════════════════════════════════════════════════════════
        
        # Tab 4: Walls/Masonry
        self.walls_tab = WallsTab(notebook, self)
        tab2 = self.walls_tab.create()
        notebook.add(tab2, text="🧱 البناء")
        
        # Tab 5: Ceramic & Stone
        self.ceramic_tab = CeramicTab(notebook, self)
        tab3 = self.ceramic_tab.create()
        notebook.add(tab3, text="🚿 السيراميك")

        # Tab 6: Plaster & Paint
        self.coatings_tab = CoatingsTab(notebook, self)
        tab4 = self.coatings_tab.create()
        notebook.add(tab4, text="🎨 الدهانات")
        
        # ═══════════════════════════════════════════════════════════════
        # GROUP 3: OUTPUT & REPORTS (المخرجات)
        # ═══════════════════════════════════════════════════════════════
        
        # Tab 7: Summary
        self.summary_tab = SummaryTab(notebook, self)
        tab5 = self.summary_tab.create()
        notebook.add(tab5, text="📊 الملخص")

        # Tab 8: Quantities (consolidated ledger)
        try:
            from bilind.ui.tabs import QuantitiesTab
            self.quantities_tab = QuantitiesTab(notebook, self)
            tab6 = self.quantities_tab.create()
            notebook.add(tab6, text="📏 الكميات")
        except Exception as e:
            print(f"Quantities tab failed to load: {e}")

        # Tab 9: Dashboard (charts)
        self.dashboard_tab = DashboardTab(notebook, self)
        tab7_dashboard = self.dashboard_tab.create()
        notebook.add(tab7_dashboard, text="📈 لوحة التحكم")

        # Tab 10: Costs
        self.costs_tab = CostsTab(notebook, self)
        tab8_costs = self.costs_tab.create()
        notebook.add(tab8_costs, text="💰 التكاليف")

        # Tab 11: Material Estimator
        self.material_estimator_tab = MaterialEstimatorTab(notebook, self)
        tab9_mat = self.material_estimator_tab.frame
        notebook.add(tab9_mat, text="🔧 حاسبة المواد")

        # Tab 12: Settings
        self.settings_tab = SettingsTab(notebook, self)
        tab10_settings = self.settings_tab.create()
        notebook.add(tab10_settings, text="⚙️ الإعدادات")

        # Tab 13: Sync Log
        self.sync_log_tab = SyncLogTab(notebook, self)
        tab11_sync = self.sync_log_tab.create()
        notebook.add(tab11_sync, text="📡 المزامنة")

        # Store reference and bind events
        self.notebook = notebook
        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Status Bar with Theme Toggle
        status_bar_frame = ttk.Frame(self.root, style='Status.TFrame', height=25)
        status_bar_frame.pack(side='bottom', fill='x', padx=1, pady=1)
        
        # Theme toggle button (left side)
        theme_btn_frame = ttk.Frame(status_bar_frame, style='Status.TFrame')
        theme_btn_frame.pack(side='left', padx=5)
        
        self.current_theme_name = tk.StringVar(value='neo')  # Default dark theme
        theme_toggle_btn = ttk.Button(
            theme_btn_frame,
            text="☀️ Light",
            command=self.toggle_theme,
            style='Secondary.TButton',
            width=10
        )
        theme_toggle_btn.pack(side='left', padx=2)
        
        status_bar = ttk.Label(
            status_bar_frame, 
            textvariable=self.status_var, 
            anchor='w', 
            style='Status.TLabel'
        )
        status_bar.pack(side='left', fill='x', expand=True, padx=10)

        self.update_status(self._default_status) # Initial status
    
    # === TAB EVENT HANDLERS ===
    
    def on_tab_changed(self, event):
        """Handle tab changes to refresh data - supports Arabic tab names."""
        notebook = event.widget
        tab_name = notebook.tab(notebook.select(), "text")
        
        # Input Tabs
        if "الأدوار" in tab_name:  # Floors
            if hasattr(self, 'floors_tab'):
                self.floors_tab.refresh_data()
        elif "مدير الغرف" in tab_name:  # Room Manager
            if hasattr(self, 'room_manager_tab'):
                self.room_manager_tab.refresh_rooms_list()
        elif "البيانات" in tab_name or "Main" in tab_name:  # Main Data
            if hasattr(self, 'rooms_tab'):
                self.rooms_tab.refresh_data()
        
        # Calculation Tabs
        elif "البناء" in tab_name:  # Masonry
            if hasattr(self, 'walls_tab'):
                self.walls_tab.refresh_data()
        elif "السيراميك" in tab_name or "Ceramic" in tab_name:  # Ceramic
            if hasattr(self, 'ceramic_tab'):
                self.ceramic_tab.refresh_data()
        elif "الدهانات" in tab_name or "Plaster" in tab_name:  # Coatings
            if hasattr(self, 'coatings_tab'):
                self.coatings_tab.refresh_data()
        
        # Output Tabs
        elif "الملخص" in tab_name or "Summary" in tab_name:  # Summary
            if hasattr(self, 'summary_tab'):
                self.summary_tab.refresh_data()
        elif "الكميات" in tab_name:  # Quantities
            if hasattr(self, 'quantities_tab'):
                self.quantities_tab.refresh_data()
        elif "لوحة التحكم" in tab_name or "Dashboard" in tab_name:  # Dashboard
            if hasattr(self, 'dashboard_tab'):
                self.dashboard_tab.refresh_data()
        elif "التكاليف" in tab_name or "Costs" in tab_name:  # Costs
            if hasattr(self, 'costs_tab'):
                self.costs_tab.refresh_data()
        elif "حاسبة المواد" in tab_name or "Material Estimator" in tab_name:  # Materials
            if hasattr(self, 'material_estimator_tab'):
                self.material_estimator_tab.refresh_data()
        elif "المزامنة" in tab_name or "Sync Log" in tab_name:  # Sync
            self.update_status("سجل المزامنة نشط. يمكنك تفعيل المزامنة من تبويب البيانات.", icon="📡")
    
    def refresh_materials_tab(self):
        """Delegates refreshing materials to the ceramic_tab."""
        if hasattr(self, 'ceramic_tab'):
            self.ceramic_tab.refresh_data()
    
    # === CROSS-TAB REFRESH METHODS ===
    
    def refresh_finishes(self):
        """Refresh all finish-related tabs (ceramic + coatings)."""
        if hasattr(self, 'ceramic_tab'):
            self.ceramic_tab.refresh_data()
        if hasattr(self, 'coatings_tab'):
            self.coatings_tab.refresh_data()
    
    def refresh_output_tabs(self):
        """Refresh all output/report tabs when data changes."""
        if hasattr(self, 'summary_tab'):
            self.summary_tab.refresh_data()
        if hasattr(self, 'quantities_tab'):
            self.quantities_tab.refresh_data()
        if hasattr(self, 'dashboard_tab'):
            self.dashboard_tab.refresh_data()
        if hasattr(self, 'costs_tab'):
            self.costs_tab.refresh_data()
    
    def refresh_after_room_change(self):
        """Refresh all tabs that depend on room data."""
        # Refresh input tabs
        if hasattr(self, 'rooms_tab'):
            self.rooms_tab.refresh_data()
        if hasattr(self, 'room_manager_tab'):
            self.room_manager_tab.refresh_rooms_list()
        if hasattr(self, 'floors_tab'):
            self.floors_tab.refresh_data()
        
        # Refresh calculation tabs
        if hasattr(self, 'ceramic_tab'):
            self.ceramic_tab.refresh_data()
        if hasattr(self, 'coatings_tab'):
            self.coatings_tab.refresh_data()
        
        # Refresh output tabs
        self.refresh_output_tabs()
    
    def refresh_after_opening_change(self):
        """Refresh tabs when doors/windows change."""
        # Room views need updating for opening counts
        if hasattr(self, 'rooms_tab'):
            self.rooms_tab.refresh_data()
        if hasattr(self, 'room_manager_tab'):
            if hasattr(self.room_manager_tab, '_refresh_openings_trees'):
                self.room_manager_tab._refresh_openings_trees()
        
        # Coatings/Paint needs recalculating for deductions
        if hasattr(self, 'coatings_tab'):
            self.coatings_tab.refresh_data()
        
        # Output tabs need updating
        self.refresh_output_tabs()
    
    def refresh_after_wall_change(self):
        """Refresh tabs when wall data changes."""
        # CRITICAL: Update ceramic zones to sync with modified walls
        # This ensures perimeter/area values match current wall lengths
        # and removes orphan zones for deleted walls
        self._update_ceramic_zones_after_wall_change()
        
        if hasattr(self, 'walls_tab'):
            self.walls_tab.refresh_data()
        if hasattr(self, 'room_manager_tab'):
            if hasattr(self.room_manager_tab, '_refresh_walls_tree'):
                self.room_manager_tab._refresh_walls_tree()
        
        # CRITICAL: Refresh ceramic tab to show updated data
        if hasattr(self, 'ceramic_tab'):
            self.ceramic_tab.refresh_data()
        
        # Coatings depends on ceramic zones
        if hasattr(self, 'coatings_tab'):
            self.coatings_tab.refresh_data()
        
        # Output tabs need updating
        self.refresh_output_tabs()
    
    def _update_ceramic_zones_after_wall_change(self):
        """Update ceramic zone perimeters when room walls are modified."""
        if not hasattr(self, 'project') or not self.project.ceramic_zones:
            return

        # Root fix: do NOT overwrite per-wall zones with full-room perimeter.
        # Normalize zones by linking them back to the correct wall lengths.
        try:
            from bilind.calculations.ceramic_zone_normalizer import normalize_ceramic_wall_zones

            normalize_ceramic_wall_zones(self.project)
        except Exception:
            # Never break wall refresh because of normalization.
            return
    
    def refresh_after_ceramic_change(self):
        """Refresh tabs when ceramic zones change."""
        if hasattr(self, 'ceramic_tab'):
            self.ceramic_tab.refresh_data()
        # Coatings deducts ceramic zones, so refresh it too
        if hasattr(self, 'coatings_tab'):
            self.coatings_tab.refresh_data()
        
        # Output tabs need updating
        self.refresh_output_tabs()

    # === CORE ACTIONS (RESET/PICK/DEDUCT) ===
    def reset_all(self):
        """Clear all project data and refresh UI."""
        if not messagebox.askyesno("Reset All", "This will remove all rooms, walls, doors, windows and finishes. Continue?"):
            return
        self.project.rooms.clear()
        self.project.doors.clear()
        self.project.windows.clear()
        self.project.walls.clear()
        self.project.plaster_items.clear()
        self.project.paint_items.clear()
        self.project.tiles_items.clear()
        self.project.ceramic_zones.clear()
        self._rebuild_association()
        self.refresh_all_tabs()
        self.update_status("All data cleared", icon="🧹")
    
    def refresh_ceramic_zones(self):
        """Refresh ceramic planner table."""
        if not hasattr(self, 'ceramic_tree'):
            return

        zones = self._normalize_ceramic_zones()

        for item in self.ceramic_tree.get_children():
            self.ceramic_tree.delete(item)

        totals = {'Kitchen': 0.0, 'Bathroom': 0.0, 'Other': 0.0}
        for zone in zones:
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
        self.ceramic_totals_label.config(text=summary if zones else "No ceramic zones yet")

    def _validated_ceramic_zone_dict(self, zone_data: Any) -> Dict[str, Any]:
        """Validate and normalize ceramic zone payload into dictionary form."""
        if isinstance(zone_data, CeramicZone):
            zone_obj = zone_data
        elif isinstance(zone_data, dict):
            zone_obj = CeramicZone.from_dict(zone_data)
        else:
            raise TypeError(f"Unsupported ceramic zone type: {type(zone_data)}")
        return zone_obj.to_dict()

    def _normalize_ceramic_zones(self) -> List[Dict[str, Any]]:
        """Ensure ceramic zones remain validated dictionaries."""
        normalized: List[Dict[str, Any]] = []
        for zone in self.ceramic_zones:
            try:
                normalized.append(self._validated_ceramic_zone_dict(zone))
            except (ValueError, TypeError) as exc:
                print(f"[WARN] Skipping invalid ceramic zone: {exc}")
        self.ceramic_zones = normalized
        return normalized

    def _parse_ceramic_dialog_result(self, payload):
        """Normalize dialog payload into (zones, room_name, wall_updates)."""
        if not payload:
            return [], None, []
        if isinstance(payload, dict) and 'wall_updates' in payload:
            return payload.get('zones', []), payload.get('room_name'), payload.get('wall_updates', [])
        if isinstance(payload, list):
            room_name = self._zone_attr(payload[0], 'room_name', None) if payload else None
            return payload, room_name, []
        return [payload], self._zone_attr(payload, 'room_name', None), []

    def _remove_room_wall_zones(self, room_name: Optional[str], wall_names: Set[str]):
        """Remove existing wall zones for specific walls before re-adding."""
        if not room_name or not wall_names:
            return
        targets = {name for name in wall_names if name}
        if not targets:
            return
        filtered = []
        removed = False
        for zone in self.project.ceramic_zones:
            zone_room = self._zone_attr(zone, 'room_name', None)
            zone_surface = self._zone_attr(zone, 'surface_type', 'wall')
            zone_wall = self._zone_attr(zone, 'wall_name', None)
            if zone_surface == 'wall' and zone_room == room_name and zone_wall in targets:
                removed = True
                continue
            filtered.append(zone)
        if removed:
            self.project.ceramic_zones = filtered
            self.ceramic_zones = self.project.ceramic_zones

    def _apply_ceramic_wall_updates(self, room_name: Optional[str], updates: List[Dict[str, Any]]):
        """Apply ceramic height updates to walls for the given room name."""
        if not room_name or not updates:
            return
        room = next((r for r in self.project.rooms if self._room_name(r) == room_name), None)
        if not room:
            return
        walls = room.get('walls') if isinstance(room, dict) else getattr(room, 'walls', None)
        if not walls:
            return
        for update in updates:
            wall_name = update.get('wall_name')
            if not wall_name:
                continue
            height = float(update.get('ceramic_height', 0.0) or 0.0)
            for wall in walls:
                current_name = wall.get('name') if isinstance(wall, dict) else getattr(wall, 'name', None)
                if current_name != wall_name:
                    continue
                if isinstance(wall, dict):
                    wall['ceramic_height'] = height
                    if height > 0:
                        wall['ceramic_surface'] = 'سيراميك'
                    else:
                        wall.pop('ceramic_surface', None)
                    length_val = float(wall.get('length', 0.0) or 0.0)
                    wall['ceramic_area'] = max(0.0, length_val * height)
                else:
                    wall.ceramic_height = height
                    if height > 0:
                        wall.ceramic_surface = getattr(wall, 'ceramic_surface', 'سيراميك') or 'سيراميك'
                    else:
                        if hasattr(wall, 'ceramic_surface'):
                            wall.ceramic_surface = ''
                    if hasattr(wall, '_normalize_ceramic_segment'):
                        wall._normalize_ceramic_segment()
                    else:
                        length_val = float(getattr(wall, 'length', 0.0) or 0.0)
                        wall.ceramic_area = max(0.0, length_val * height)
                break

    def _apply_ceramic_zone_changes(self, zones, room_name=None, wall_updates=None):
        """Central handler for adding zones and syncing wall level data."""
        zones = zones or []
        wall_updates = wall_updates or []
        affected_rooms: Set[str] = set()

        updates_by_room: Dict[str, List[Dict[str, Any]]] = {}
        for update in wall_updates:
            target_room = update.get('room_name') or room_name
            wall_name = update.get('wall_name')
            if not target_room or not wall_name:
                continue
            updates_by_room.setdefault(target_room, []).append({
                'wall_name': wall_name,
                'ceramic_height': float(update.get('ceramic_height', 0.0) or 0.0)
            })
            affected_rooms.add(target_room)

        for target_room, updates in updates_by_room.items():
            names = {u['wall_name'] for u in updates if u.get('wall_name')}
            if names:
                self._remove_room_wall_zones(target_room, names)
            self._apply_ceramic_wall_updates(target_room, updates)

        zone_wall_groups: Dict[str, Set[str]] = {}
        for zone in zones:
            z_room = self._zone_attr(zone, 'room_name', None)
            if z_room:
                affected_rooms.add(z_room)
            z_wall = self._zone_attr(zone, 'wall_name', None)
            if z_room and z_wall:
                zone_wall_groups.setdefault(z_room, set()).add(z_wall)

        for target_room, names in zone_wall_groups.items():
            self._remove_room_wall_zones(target_room, names)

        added = 0
        for zone in zones:
            height = float(self._zone_attr(zone, 'height', 0.0) or 0.0)
            eff_area = self._zone_attr(zone, 'effective_area', None)
            perimeter = float(self._zone_attr(zone, 'perimeter', 0.0) or 0.0)
            preset_area = self._zone_attr(zone, 'area', None)
            computed_area = preset_area if preset_area is not None else perimeter * height
            if height <= 0 and (eff_area in (None, 0.0)) and (computed_area in (None, 0.0)):
                continue
            self.project.ceramic_zones.append(zone)
            added += 1

        if added or updates_by_room or zone_wall_groups:
            self.ceramic_zones = self.project.ceramic_zones

        return added, affected_rooms
    
    # === CERAMIC ZONE MANAGEMENT ===
    
    def _ceramic_zone_dialog(self, title, initial_values=None):
        """Dialog for adding/editing ceramic zones with per-wall customization."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("560x650")
        dialog.configure(bg=self.colors['bg_primary'])
        dialog.transient(self.root)
        dialog.grab_set()

        entries = {}
        # Allow room mode if rooms exist and we're not editing (perimeter/height not preset)
        is_editing = initial_values and ('perimeter' in initial_values or 'height' in initial_values)
        allow_room_mode = bool(self.project.rooms) and not is_editing

        frame = ttk.Frame(dialog, padding=10, style='Card.TFrame')
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        def _safe_float(value, default=0.0):
            try:
                return float(value)
            except (TypeError, ValueError):
                return float(default)

        def _set_entry(entry_widget, value, readonly=False):
            entry_widget.state(['!readonly'])
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, value)
            if readonly:
                entry_widget.state(['readonly'])

        # Name
        ttk.Label(frame, text="Zone Name:").grid(row=0, column=0, sticky='w', pady=4)
        entries['name'] = ttk.Entry(frame, width=40)
        entries['name'].grid(row=0, column=1, pady=4, columnspan=2)

        # Category
        ttk.Label(frame, text="Category:").grid(row=1, column=0, sticky='w', pady=4)
        entries['category'] = ttk.Combobox(frame, width=20, state='readonly', values=('Kitchen', 'Bathroom', 'Other'))
        entries['category'].current(0)
        entries['category'].grid(row=1, column=1, sticky='w', pady=4)

        # Surface Type
        ttk.Label(frame, text="Surface Type:").grid(row=2, column=0, sticky='w', pady=4)
        surface_var = tk.StringVar(value='wall')
        entries['surface_type'] = surface_var
        surface_frame = ttk.Frame(frame)
        surface_frame.grid(row=2, column=1, sticky='w', pady=4, columnspan=2)
        ttk.Radiobutton(surface_frame, text="🧱 Wall", variable=surface_var, value='wall').pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(surface_frame, text="🟫 Floor", variable=surface_var, value='floor').pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(surface_frame, text="⬛ Ceiling", variable=surface_var, value='ceiling').pack(side=tk.LEFT, padx=4)

        # Mode
        ttk.Label(frame, text="Mode:").grid(row=3, column=0, sticky='w', pady=4)
        mode_var = tk.StringVar(value='room' if allow_room_mode else 'manual')
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=3, column=1, sticky='w', pady=4, columnspan=2)
        rb_manual = ttk.Radiobutton(mode_frame, text="Manual Input", variable=mode_var, value='manual')
        rb_manual.pack(side=tk.LEFT, padx=4)
        rb_room = ttk.Radiobutton(mode_frame, text="From Room Walls", variable=mode_var, value='room')
        rb_room.pack(side=tk.LEFT, padx=4)
        if not allow_room_mode:
            rb_room.state(['disabled'])

        # Room selection
        ttk.Label(frame, text="Room:").grid(row=4, column=0, sticky='w', pady=4)
        room_names = [r.name if hasattr(r, 'name') else r.get('name', '-') for r in self.project.rooms]
        room_state = 'readonly' if allow_room_mode else 'disabled'
        entries['room_name'] = ttk.Combobox(frame, width=26, values=room_names, state=room_state)
        entries['room_name'].grid(row=4, column=1, sticky='w', pady=4)

        # Perimeter / Height inputs
        ttk.Label(frame, text="Perimeter (m):").grid(row=5, column=0, sticky='w', pady=4)
        entries['perimeter'] = ttk.Entry(frame, width=20)
        entries['perimeter'].grid(row=5, column=1, sticky='w', pady=4)

        ttk.Label(frame, text="Height (m):").grid(row=6, column=0, sticky='w', pady=4)
        entries['height'] = ttk.Entry(frame, width=20)
        entries['height'].insert(0, "1.20")
        entries['height'].grid(row=6, column=1, sticky='w', pady=4)

        ttk.Label(frame, text="Notes:").grid(row=7, column=0, sticky='w', pady=4)
        entries['notes'] = ttk.Entry(frame, width=40)
        entries['notes'].grid(row=7, column=1, pady=4, columnspan=2)

        # Per-wall controls (room mode)
        walls_frame = ttk.LabelFrame(frame, text="Select Walls for Zone", padding=6)
        walls_frame.grid(row=8, column=0, columnspan=3, sticky='nsew', pady=6)
        walls_frame.grid_remove()

        columns = ('name', 'length', 'wall_height', 'ceramic_height')
        walls_tree = ttk.Treeview(
            walls_frame,
            columns=columns,
            show='headings',
            selectmode='extended',
            height=7
        )
        walls_tree.heading('name', text='Wall')
        walls_tree.heading('length', text='Length (m)')
        walls_tree.heading('wall_height', text='Wall H (m)')
        walls_tree.heading('ceramic_height', text='Ceramic H (m)')
        walls_tree.column('name', width=150)
        walls_tree.column('length', width=80, anchor='center')
        walls_tree.column('wall_height', width=90, anchor='center')
        walls_tree.column('ceramic_height', width=100, anchor='center')
        walls_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(walls_frame, orient=tk.VERTICAL, command=walls_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        walls_tree.configure(yscrollcommand=scrollbar.set)

        wall_rows = {}
        clone_counters = {}
        preview_var = tk.StringVar(value="Selected Walls Area: 0.00 m²")
        height_editor_var = tk.StringVar(value="")

        controls_row = ttk.Frame(walls_frame)
        controls_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(controls_row, text="Set ceramic height (m):").pack(side=tk.LEFT)
        height_editor_entry = ttk.Entry(controls_row, width=8, textvariable=height_editor_var)
        height_editor_entry.pack(side=tk.LEFT, padx=4)

        def _update_preview():
            selected = walls_tree.selection()
            total_len = 0.0
            total_area = 0.0
            for iid in selected:
                row = wall_rows.get(iid)
                if not row:
                    continue
                total_len += row['length']
                total_area += row['length'] * max(0.0, row.get('ceramic_height', 0.0))
            _set_entry(entries['perimeter'], f"{total_len:.2f}", readonly=True)
            preview_var.set(f"Selected Walls Area: {total_area:.2f} m²")

        def apply_height_to_selection():
            try:
                value = _safe_float(height_editor_var.get(), default=0.0)
            except Exception:
                value = 0.0
            if value < 0:
                messagebox.showerror("Invalid Height", "Height cannot be negative.", parent=dialog)
                return
            changed = False
            for iid in walls_tree.selection():
                row = wall_rows.get(iid)
                if not row:
                    continue
                max_h = row.get('wall_height') or value
                row['ceramic_height'] = min(value, max_h) if max_h > 0 else value
                walls_tree.set(iid, 'ceramic_height', f"{row['ceramic_height']:.2f}")
                changed = True
            if changed:
                _update_preview()

        def duplicate_selected_walls():
            selected = walls_tree.selection()
            if not selected:
                messagebox.showinfo("No Selection", "Select at least one wall to duplicate.", parent=dialog)
                return
            new_ids = []
            for iid in selected:
                row = wall_rows.get(iid)
                if not row:
                    continue
                base_key = row.get('base_key') or row['name']
                clone_counters[base_key] = clone_counters.get(base_key, 1) + 1
                clone_label = f"{row['display_name']} • h{clone_counters[base_key]}"
                new_row = row.copy()
                new_row['display_name'] = clone_label
                new_row['base_key'] = base_key
                new_id = walls_tree.insert('', tk.END, values=(
                    clone_label,
                    f"{new_row['length']:.2f}",
                    f"{new_row['wall_height']:.2f}",
                    f"{new_row.get('ceramic_height', 0.0):.2f}"
                ))
                wall_rows[new_id] = new_row
                new_ids.append(new_id)
            if new_ids:
                walls_tree.selection_set(new_ids[-1])
                _update_preview()

        ttk.Button(controls_row, text="Apply Height", command=apply_height_to_selection, style='Secondary.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(controls_row, text="➕ Duplicate Wall", command=duplicate_selected_walls, style='Secondary.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Label(controls_row, textvariable=preview_var, foreground=self.colors.get('accent', '#0ea5e9')).pack(side=tk.RIGHT)

        def update_from_room(event=None):
            if mode_var.get() != 'room':
                walls_frame.grid_remove()
                wall_rows.clear()
                return
            room_name = entries['room_name'].get()
            if not room_name:
                return
            room = next((r for r in self.project.rooms if (r.name if hasattr(r, 'name') else r.get('name')) == room_name), None)
            if not room:
                return
            walls_frame.grid()
            for item in walls_tree.get_children():
                walls_tree.delete(item)
            wall_rows.clear()
            clone_counters.clear()
            walls = getattr(room, 'walls', []) if not isinstance(room, dict) else room.get('walls', [])
            total_len = 0.0
            default_height = _safe_float(entries['height'].get(), 0.0)
            if walls:
                for w in walls:
                    w_name = w.get('name') if isinstance(w, dict) else getattr(w, 'name', 'Wall')
                    w_len = _safe_float(w.get('length') if isinstance(w, dict) else getattr(w, 'length', 0.0))
                    w_h = _safe_float(w.get('height') if isinstance(w, dict) else getattr(w, 'height', 0.0))
                    existing_h = _safe_float(w.get('ceramic_height') if isinstance(w, dict) else getattr(w, 'ceramic_height', 0.0))
                    ceramic_h = existing_h if existing_h > 0 else (default_height if default_height > 0 else (w_h if w_h > 0 else 0.0))
                    iid = walls_tree.insert('', tk.END, values=(
                        w_name,
                        f"{w_len:.2f}",
                        f"{w_h:.2f}",
                        f"{ceramic_h:.2f}"
                    ))
                    wall_rows[iid] = {
                        'name': w_name,
                        'display_name': w_name,
                        'length': w_len,
                        'wall_height': w_h,
                        'ceramic_height': ceramic_h,
                        'base_key': w_name
                    }
                    total_len += w_len
                    walls_tree.selection_add(iid)
            else:
                if isinstance(room, dict):
                    perim = _safe_float(room.get('perim', 0.0))
                    wall_h = _safe_float(room.get('wall_height', 0.0))
                else:
                    perim = _safe_float(getattr(room, 'perimeter', 0.0))
                    wall_h = _safe_float(getattr(room, 'wall_height', 0.0))
                ceramic_h = default_height if default_height > 0 else wall_h
                iid = walls_tree.insert('', tk.END, values=(
                    'Room Perimeter',
                    f"{perim:.2f}",
                    f"{wall_h:.2f}",
                    f"{ceramic_h:.2f}"
                ))
                wall_rows[iid] = {
                    'name': 'Room Perimeter',
                    'display_name': 'Room Perimeter',
                    'length': perim,
                    'wall_height': wall_h,
                    'ceramic_height': ceramic_h,
                    'base_key': 'Room Perimeter'
                }
                walls_tree.selection_add(iid)
                total_len = perim
            _set_entry(entries['perimeter'], f"{total_len:.2f}", readonly=True)
            if default_height <= 0:
                height_editor_var.set(f"{_safe_float(entries['height'].get(), wall_rows[next(iter(wall_rows))]['ceramic_height'] if wall_rows else 0.0):.2f}")
            _update_preview()

        def on_wall_select(event=None):
            if mode_var.get() == 'room':
                _update_preview()

        def toggle_mode():
            if mode_var.get() == 'room' and allow_room_mode:
                entries['perimeter'].state(['readonly'])
                walls_frame.grid()
                update_from_room()
            else:
                entries['perimeter'].state(['!readonly'])
                walls_frame.grid_remove()
                preview_var.set("Selected Walls Area: 0.00 m²")

        walls_tree.bind('<<TreeviewSelect>>', on_wall_select)
        rb_manual.configure(command=toggle_mode)
        rb_room.configure(command=toggle_mode)
        entries['room_name'].bind('<<ComboboxSelected>>', update_from_room)

        if initial_values:
            entries['name'].insert(0, initial_values.get('name', ''))
            category = initial_values.get('category', 'Other')
            if category in ('Kitchen', 'Bathroom', 'Other'):
                entries['category'].set(category)
            surface_var.set(initial_values.get('surface_type', 'wall'))
            
            # Only populate perimeter/height if editing an existing zone
            if is_editing:
                _set_entry(entries['perimeter'], str(initial_values.get('perimeter', '')))
                entries['height'].delete(0, tk.END)
                entries['height'].insert(0, str(initial_values.get('height', '')))
                mode_var.set('manual')
                walls_frame.grid_remove()
                entries['room_name'].state(['disabled'])
                rb_room.state(['disabled'])
            
            # Pre-select room if provided (but still allow room mode)
            rn = initial_values.get('room_name') if isinstance(initial_values, dict) else None
            if rn and allow_room_mode:
                try:
                    entries['room_name'].set(rn)
                except Exception:
                    pass
            
            entries['notes'].insert(0, initial_values.get('notes', ''))

        toggle_mode()

        result = {}

        def on_ok():
            try:
                name = entries['name'].get().strip()
                if not name:
                    messagebox.showerror("Error", "Zone Name cannot be empty.", parent=dialog)
                    return
                category = entries['category'].get()
                surface_type = entries['surface_type'].get()
                notes = entries['notes'].get().strip()
                perimeter_val = _safe_float(entries['perimeter'].get(), 0.0)
                height_val = _safe_float(entries['height'].get(), 0.0)
                room_name = entries['room_name'].get().strip() if entries['room_name'].get() else None

                from bilind.models.finish import CeramicZone

                if mode_var.get() == 'room' and allow_room_mode:
                    if not room_name:
                        messagebox.showerror("Error", "Select a room to pull walls from.", parent=dialog)
                        return
                    selected = walls_tree.selection()
                    if not selected:
                        messagebox.showerror("Error", "Select at least one wall.", parent=dialog)
                        return
                    zones_created = []
                    wall_updates = []  # Track which walls to update
                    for idx, iid in enumerate(selected, start=1):
                        row = wall_rows.get(iid)
                        if not row:
                            continue
                        ceramic_height = max(0.0, row.get('ceramic_height', height_val))
                        wall_updates.append({
                            'room_name': room_name,
                            'wall_name': row['name'],
                            'ceramic_height': ceramic_height
                        })
                        if ceramic_height <= 0:
                            continue
                        zone_name = name if len(selected) == 1 else f"{name} - {row['display_name']}"
                        zone = CeramicZone(
                            name=zone_name,
                            category=category,
                            perimeter=row['length'],
                            height=ceramic_height,
                            surface_type='wall',
                            room_name=room_name,
                            wall_name=row['name'],
                            notes=notes
                        )
                        zones_created.append(zone)
                    if not zones_created and not wall_updates:
                        messagebox.showerror("Error", "No valid wall selections to create zones.", parent=dialog)
                        return
                    result['zones'] = zones_created
                    result['wall_updates'] = wall_updates
                    result['room_name'] = room_name
                else:
                    if perimeter_val <= 0 or height_val <= 0:
                        messagebox.showerror("Error", "Perimeter and height must be positive numbers.", parent=dialog)
                        return
                    result['zone'] = CeramicZone(
                        name=name,
                        category=category,
                        perimeter=perimeter_val,
                        height=height_val,
                        surface_type=surface_type,
                        room_name=room_name,
                        notes=notes
                    )
                dialog.destroy()
            except Exception as exc:
                messagebox.showerror("Error", f"Invalid input: {exc}", parent=dialog)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=9, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="OK", command=on_ok, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side='left', padx=5)

        self.root.wait_window(dialog)
        # Return the entire result dict if it has wall_updates, otherwise just zones/zone
        if 'wall_updates' in result:
            return result
        if 'zones' in result:
            return result['zones']
        return result.get('zone')

    def add_ceramic_zone(self):
        """Add a new ceramic zone."""
        payload = self._ceramic_zone_dialog("Add Ceramic Zone")
        zones, room_name, wall_updates = self._parse_ceramic_dialog_result(payload)
        if not zones and not wall_updates:
            return
        added, affected_rooms = self._apply_ceramic_zone_changes(zones, room_name, wall_updates)
        self.refresh_after_ceramic_change()
        if added:
            first_label = self._zone_attr(zones[0], 'name', '') if zones else ''
            msg = "ceramic zone" if added == 1 else f"{added} ceramic zones"
            self.update_status(f"✅ Added {msg}: {first_label}", icon="➕")
        else:
            self.update_status("Updated ceramic wall heights", icon="🧱")

    def edit_ceramic_zone(self):
        """Edit the selected ceramic zone."""
        if not hasattr(self, 'ceramic_tab') or not self.ceramic_tab.ceramic_tree:
            return
        selection = self.ceramic_tab.ceramic_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "⚠️ Select a ceramic zone to edit.")
            return
        
        # Assuming IID is index is risky if sorting is enabled, but standard for now
        # Better: find by ID if we had one. For now, rely on list order.
        try:
            # Treeview items are usually I001 etc unless explicitly set.
            # In refresh_ceramic_zones we didn't set explicit IIDs matching index.
            # Let's fix refresh_ceramic_zones in CeramicTab to use index as IID or handle this better.
            # Actually, CeramicTab.refresh_ceramic_zones doesn't set IID.
            # So we rely on index in children list.
            idx = self.ceramic_tab.ceramic_tree.index(selection[0])
            original_data = self.ceramic_zones[idx]
            
            # Convert to dict for dialog if needed
            initial_values = original_data.to_dict() if hasattr(original_data, 'to_dict') else original_data
            
            new_zone = self._ceramic_zone_dialog("Edit Ceramic Zone", initial_values=initial_values)
            
            if new_zone:
                self.ceramic_zones[idx] = new_zone
                self.ceramic_tab.refresh_data()
                self.update_status(f"✅ Edited ceramic zone: {new_zone.name}", icon="✏️")
        except (ValueError, IndexError):
             messagebox.showerror("Error", "Could not find the selected ceramic zone to edit.")


    def delete_ceramic_zone(self):
        """Delete the selected ceramic zone."""
        if not hasattr(self, 'ceramic_tab') or not self.ceramic_tab.ceramic_tree:
            return
        selection = self.ceramic_tab.ceramic_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "⚠️ Select a ceramic zone to delete.")
            return

        if not messagebox.askyesno("Confirm", "Are you sure you want to delete the selected ceramic zone?"):
            return
            
        # Get indices from treeview items
        indices_to_delete = sorted([self.ceramic_tab.ceramic_tree.index(item) for item in selection], reverse=True)

        for idx in indices_to_delete:
            if 0 <= idx < len(self.ceramic_zones):
                del self.ceramic_zones[idx]
        
        self.ceramic_tab.refresh_data()
        self.update_status(f"🗑️ Deleted {len(indices_to_delete)} ceramic zone(s).", icon="🗑️")
    
    def _finish_item_dialog(self, title, defaults=None):
        """Dialog for adding/editing a finish item."""
        defaults = defaults or {}
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=(18, 14), style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Description", foreground=self.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=8)
        desc_var = tk.StringVar(value=defaults.get('desc', ''))
        ttk.Entry(frame, textvariable=desc_var, width=35).grid(row=0, column=1, sticky='w', pady=8)

        ttk.Label(frame, text="Area (m²)", foreground=self.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=8)
        area_var = tk.StringVar(value=str(defaults.get('area', '')))
        ttk.Entry(frame, textvariable=area_var, width=20).grid(row=1, column=1, sticky='w', pady=8)

        result = {}
        def save():
            try:
                desc = desc_var.get().strip()
                area = float(area_var.get())
                if not desc:
                    raise ValueError("Description cannot be empty.")
                result.update({'desc': desc, 'area': area})
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e))

        button_bar = ttk.Frame(dialog, padding=(18, 10), style='Main.TFrame')
        button_bar.pack(fill=tk.X)
        ttk.Button(button_bar, text="Save", command=save, style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)

        dialog.wait_window()
        return result
    
    def calculate_room_finishes(self):
        """Calculate finishes for a selected room using associations."""
        selection = self.rooms_tab.rooms_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "⚠️ Select a room first")
            return
        
        room_idx = self.rooms_tab.rooms_tree.index(selection[0])
        room = self.project.rooms[room_idx]
        room_dict = room.to_dict() if hasattr(room, 'to_dict') else room
        
        try:
            wall_height_str = simpledialog.askstring(
                "Wall Height",
                f"Enter wall height for '{room_dict.get('name', 'Room')}' (meters):",
                initialvalue="3.0"
            )
            if not wall_height_str:
                return
            
            wall_height = float(wall_height_str)
            if wall_height <= 0:
                raise ValueError("Height must be positive")
            
            # Use association manager for accurate calculations
            net_wall_area = self.association.get_room_net_wall_area(room_dict, wall_height)

            room_name = room_dict.get('name', 'Room')
            perimeter_value = float(room_dict.get('perim', 0.0) or 0.0)

            # Create finish items (store as simple dictionaries for compatibility)
            self.plaster_items.append({'desc': f"Walls: {room_name}", 'area': net_wall_area})
            self.paint_items.append({'desc': f"Walls: {room_name}", 'area': net_wall_area})
            self.tiles_items.append({'desc': f"Skirting: {room_name}", 'area': perimeter_value})

            # Persist on room object for direct extraction
            if hasattr(room, 'wall_height'):
                setattr(room, 'wall_height', wall_height)
                setattr(room, 'wall_finish_area', net_wall_area)
                setattr(room, 'ceiling_finish_area', float(room_dict.get('area', 0.0) or 0.0))
            else:
                room['wall_height'] = wall_height
                room['wall_finish_area'] = net_wall_area
                room['ceiling_finish_area'] = float(room_dict.get('area', 0.0) or 0.0)
            self.refresh_rooms()
            
            self.refresh_finishes_tab()
            self.update_status(f"✅ Calculated finishes for {room_name}", icon="🧮")
            
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Invalid wall height. Please enter a positive number.")

    def set_room_ceramic(self):
        """Set ceramic area (deduction) for selected room."""
        sel = self.rooms_tab.rooms_tree.selection() if hasattr(self, 'rooms_tab') else []
        if not sel:
            messagebox.showwarning("Warning", "Select a room first")
            return
        idx = self.rooms_tab.rooms_tree.index(sel[0])
        if idx >= len(self.project.rooms):
            return
        room = self.project.rooms[idx]
        room_dict = room.to_dict() if hasattr(room, 'to_dict') else room
        from tkinter import simpledialog
        val = simpledialog.askstring("Ceramic Area", f"Enter ceramic area for {room_dict.get('name','Room')} (m²):", initialvalue=f"{room_dict.get('ceramic_area', 0.0) or 0.0}")
        if val is None:
            return
        try:
            ceramic_area = float(val)
            if ceramic_area < 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Invalid ceramic area.")
            return
        if hasattr(room, 'ceramic_area'):
            room.ceramic_area = ceramic_area
        else:
            room['ceramic_area'] = ceramic_area
        self._recompute_room_finish(room)
        self.refresh_rooms()
        self.update_status(f"Set ceramic area for {room_dict.get('name','Room')} = {ceramic_area:.2f} m²", icon="🧱")

    def _build_room_metrics_context(self) -> RoomMetricsContext:
        """Construct a reusable metrics context from current project data."""
        return build_room_metrics_context(
            self.project.rooms,
            self.project.doors,
            self.project.windows,
            getattr(self.project, 'ceramic_zones', []),
            getattr(self.project, 'default_wall_height', 3.0),
        )

    def _apply_room_metrics(self, room, metrics: RoomFinishMetrics) -> None:
        """Persist calculated metrics back onto the room record."""
        breakdown = {
            'wall': metrics.ceramic_wall,
            'ceiling': metrics.ceramic_ceiling,
            'floor': metrics.ceramic_floor,
        }
        if isinstance(room, dict):
            room['wall_finish_area'] = metrics.wall_finish_net
            room['ceiling_finish_area'] = metrics.area
            room['plaster_area'] = metrics.plaster_total
            room['paint_area'] = metrics.paint_total
            room['ceramic_area'] = metrics.ceramic_total
            room['ceramic_breakdown'] = breakdown
        else:
            room.wall_finish_area = metrics.wall_finish_net
            room.ceiling_finish_area = metrics.area
            room.plaster_area = metrics.plaster_total
            room.paint_area = metrics.paint_total
            room.ceramic_area = metrics.ceramic_total
            room.ceramic_breakdown = breakdown

    def _recompute_room_finish(self, room, context: Optional[RoomMetricsContext] = None) -> RoomFinishMetrics:
        """Recalculate wall, plaster, paint, and ceramic totals for a single room."""
        ctx = context or self._build_room_metrics_context()
        metrics = calculate_room_finish_metrics(room, ctx)
        self._apply_room_metrics(room, metrics)
        return metrics

    def auto_calculate_room(self):
        """Automatically compute wall finish (net), plaster, and paint for selected room using current assignments and optional ceramic area."""
        sel = self.rooms_tab.rooms_tree.selection() if hasattr(self, 'rooms_tab') else []
        if not sel:
            messagebox.showwarning("Warning", "Select a room to auto-calc")
            return
        idx = self.rooms_tab.rooms_tree.index(sel[0])
        if idx >= len(self.project.rooms):
            return
        room = self.project.rooms[idx]
        ctx = self._build_room_metrics_context()
        metrics = self._recompute_room_finish(room, context=ctx)
        self.refresh_rooms()
        self.update_status(
            f"Auto calc: {self._room_name(room)} wall={metrics.wall_finish_net:.2f} m²",
            icon="⚡",
        )
    
    def auto_calculate_all_rooms(self):
        """Automatically calculate finishes for ALL rooms using UnifiedCalculator."""
        if not self.project.rooms:
            messagebox.showwarning("Warning", "No rooms to calculate.")
            return
        
        # Ask for confirmation
        result = messagebox.askyesno(
            "Auto Calculate All",
            f"This will calculate finishes for {len(self.project.rooms)} room(s) using Unified Calculator.\\n\\n"
            "Continue?"
        )
        if not result:
            return
        
        # Use UnifiedCalculator
        calc = UnifiedCalculator(self.project)
        results = calc.calculate_all_rooms()
        
        calculated = 0
        
        for i, room in enumerate(self.project.rooms):
            # Find result for this room
            room_name = self._room_name(room)
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
            
            calculated += 1
        
        self.refresh_rooms()
        
        msg = f"✅ Calculated finishes for {calculated} room(s) using Unified Calculator"
        
        messagebox.showinfo("Auto Calculate All - Complete", msg)
        self.update_status(f"Auto-calculated {calculated} rooms", icon="⚡⚡")

    # === NEW: ROOM DETAIL PROMPT AFTER PICK ===
    def _prompt_room_details(self, new_rooms: list):
        """Prompt user to set room type, wall height, balcony flag, and optionally pick walls for newly picked rooms."""
        from bilind.models.room import ROOM_TYPES
        if not new_rooms:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Configure Room Properties")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Make resizable and calculate initial size
        dialog.resizable(True, True)
        max_h = int(self.root.winfo_screenheight() * 0.8)
        initial_h = min(max_h, 220 + len(new_rooms) * 150) # Increased header space for bulk actions
        dialog.geometry(f"950x{initial_h}") # Wider for bulk actions
        dialog.minsize(850, 500)

        # Main frame
        main_frame = ttk.Frame(dialog, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Frame(main_frame, style='Main.TFrame', padding=(16, 14, 16, 6))
        header.pack(fill=tk.X)
        ttk.Label(header, text="Configure Room Properties", font=('Segoe UI Semibold', 14)).pack(anchor='w')
        ttk.Label(header, text="Set type, wall height, and balcony walls for each room", 
                  foreground=self.colors['text_secondary'], font=('Segoe UI', 9)).pack(anchor='w', pady=(2, 0))

        # --- Bulk Actions Frame ---
        bulk_frame = ttk.LabelFrame(main_frame, text="Bulk Actions (Apply to Selected)", padding=10, style='Card.TLabelframe')
        bulk_frame.pack(fill=tk.X, padx=16, pady=(10, 10))
        
        # Bulk Type
        ttk.Label(bulk_frame, text="Type:").pack(side=tk.LEFT, padx=(0, 4))
        bulk_type_var = tk.StringVar()
        bulk_type_combo = ttk.Combobox(bulk_frame, textvariable=bulk_type_var, values=ROOM_TYPES, width=15, state='readonly')
        bulk_type_combo.pack(side=tk.LEFT, padx=4)
        
        def apply_bulk_type():
            val = bulk_type_var.get()
            if not val: return
            count = 0
            for i, (r, t_var, h_var, b_var, idx, sel_var, _, _, _) in enumerate(entries):
                if sel_var.get():
                    t_var.set(val)
                    count += 1
            self.update_status(f"Applied type '{val}' to {count} rooms", icon="✅")

        ttk.Button(bulk_frame, text="Apply", command=apply_bulk_type, style='Secondary.TButton', width=6).pack(side=tk.LEFT, padx=(0, 12))

        # Bulk Height
        ttk.Label(bulk_frame, text="Height:").pack(side=tk.LEFT, padx=(0, 4))
        bulk_h_var = tk.StringVar()
        ttk.Entry(bulk_frame, textvariable=bulk_h_var, width=6).pack(side=tk.LEFT, padx=4)
        
        def apply_bulk_height():
            val = bulk_h_var.get()
            if not val: return
            count = 0
            for i, (r, t_var, h_var, b_var, idx, sel_var, _, _, _) in enumerate(entries):
                if sel_var.get():
                    h_var.set(val)
                    count += 1
            self.update_status(f"Applied height '{val}' to {count} rooms", icon="✅")

        ttk.Button(bulk_frame, text="Apply", command=apply_bulk_height, style='Secondary.TButton', width=6).pack(side=tk.LEFT, padx=(0, 12))

        # Bulk Balcony
        def apply_bulk_balcony(state):
            count = 0
            for i, (r, t_var, h_var, b_var, idx, sel_var, toggle_func, _, _) in enumerate(entries):
                if sel_var.get():
                    b_var.set(state)
                    if toggle_func: toggle_func()
                    count += 1
            self.update_status(f"Set balcony={state} for {count} rooms", icon="✅")

        ttk.Button(bulk_frame, text="Mark Balcony", command=lambda: apply_bulk_balcony(True), style='Secondary.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(bulk_frame, text="Unmark", command=lambda: apply_bulk_balcony(False), style='Secondary.TButton').pack(side=tk.LEFT, padx=(2, 12))

        # Bulk Pick Walls
        def pick_walls_bulk():
            selected_indices = [i for i, entry in enumerate(entries) if entry[5].get()]
            if not selected_indices:
                messagebox.showinfo("Info", "Select rooms first.")
                return
            
            dialog.withdraw()
            try:
                for i in selected_indices:
                    r, t_var, h_var, b_var, idx, sel_var, toggle_func, walls_storage, update_btn_func = entries[i]
                    room_name = r.get('name') or f"Room{idx+1}"
                    
                    # Pick walls for this room
                    picked_walls = self._pick_walls_for_room_dialog(r, room_name)
                    if picked_walls:
                        current = walls_storage.get() or []
                        if isinstance(current, tuple): current = list(current)
                        updated = current + picked_walls
                        walls_storage.set(updated)
                        r['_picked_walls'] = updated
                        update_btn_func(len(updated))
            finally:
                dialog.deiconify()

        ttk.Button(bulk_frame, text="🧱 Pick Walls for Selected", command=pick_walls_bulk, style='Accent.TButton').pack(side=tk.LEFT, padx=(12, 0))

        # Select All Checkbox
        select_all_var = tk.BooleanVar(value=False)
        def toggle_select_all():
            val = select_all_var.get()
            for entry in entries:
                entry[5].set(val)
        
        chk_frame = ttk.Frame(main_frame, style='Main.TFrame', padding=(16, 0))
        chk_frame.pack(fill=tk.X)
        ttk.Checkbutton(chk_frame, text="Select All", variable=select_all_var, command=toggle_select_all).pack(anchor='w')

        # --- Bottom button bar ---
        btns = ttk.Frame(main_frame, padding=(16, 12), style='Main.TFrame')
        btns.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Scrollable content
        canvas_frame = ttk.Frame(main_frame, style='Main.TFrame')
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(16,0), pady=4)

        canvas = tk.Canvas(canvas_frame, bg=self.colors['bg_secondary'], highlightthickness=0)
        frame = ttk.Frame(canvas, style='Main.TFrame')
        scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.create_window((0, 0), window=frame, anchor='nw')
        
        def _cfg_scroll(e):
            canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.itemconfig(canvas.create_window((0,0), window=frame, anchor='nw'), width=e.width)
        canvas.bind('<Configure>', _cfg_scroll)
        
        entries = []
        balcony_segment_frames = {}
        
        for idx, r in enumerate(new_rooms):
            # Main room card
            card = ttk.Frame(frame, style='Card.TLabelframe', padding=(12, 10))
            card.grid(row=idx, column=0, sticky='ew', pady=6, padx=8)
            frame.columnconfigure(0, weight=1)
            
            # Selection Checkbox
            sel_var = tk.BooleanVar(value=False)
            sel_chk = ttk.Checkbutton(card, variable=sel_var)
            sel_chk.grid(row=0, column=0, sticky='nw', padx=(0, 8), pady=4)
            
            # Content Frame (to the right of checkbox)
            content_frame = ttk.Frame(card, style='Main.TFrame')
            content_frame.grid(row=0, column=1, sticky='ew')
            card.columnconfigure(1, weight=1)

            # Room header with dimensions
            header_frame = ttk.Frame(content_frame, style='Main.TFrame')
            header_frame.pack(fill=tk.X, pady=(0, 8))
            
            name = r.get('name') or f"Room{idx+1}"
            area = r.get('area', 0.0)
            perim = r.get('perim', 0.0)
            width = r.get('w')
            length = r.get('l')
            
            # Room name and dimensions
            name_label = ttk.Label(header_frame, text=f"🏠 {name}", font=('Segoe UI Semibold', 11))
            name_label.pack(side=tk.LEFT)
            
            dims_text = f"Area: {area:.2f} m² | Perimeter: {perim:.2f} m"
            if width and length:
                dims_text += f" | Dimensions: {width:.2f} × {length:.2f} m"
            
            dims_label = ttk.Label(header_frame, text=dims_text, 
                                   foreground=self.colors['text_secondary'], font=('Segoe UI', 9))
            dims_label.pack(side=tk.LEFT, padx=(12, 0))
            
            # Input row
            input_frame = ttk.Frame(content_frame, style='Main.TFrame')
            input_frame.pack(fill=tk.X, pady=4)
            
            ttk.Label(input_frame, text="Type:", width=8).pack(side=tk.LEFT, padx=(0, 4))
            type_var = tk.StringVar(value=r.get('room_type', '[Not Set]'))
            type_combo = ttk.Combobox(input_frame, textvariable=type_var, values=ROOM_TYPES, width=18, state='readonly')
            type_combo.pack(side=tk.LEFT, padx=4)
            
            ttk.Label(input_frame, text="Wall Height (m):").pack(side=tk.LEFT, padx=(12, 4))
            h_var = tk.StringVar(value="3.0")
            ttk.Entry(input_frame, textvariable=h_var, width=8).pack(side=tk.LEFT, padx=4)
            
            balcony_var = tk.BooleanVar(value=r.get('is_balcony', False) or (type_var.get() == 'Balcony'))
            balcony_check = ttk.Checkbutton(input_frame, text='🏗️ Balcony', variable=balcony_var)
            balcony_check.pack(side=tk.LEFT, padx=(12, 0))
            
            # Add wall picker button
            walls_var = tk.Variable(value=[])  # Store picked walls
            r['_temp_walls'] = walls_var  # Temporary storage
            
            # Helper to update button text
            def update_wall_btn_text(count):
                for widget in input_frame.winfo_children():
                    if isinstance(widget, ttk.Button) and ('🧱' in widget['text'] or 'Walls' in widget['text']):
                        widget.config(text=f'🧱 Walls ({count})')
                        break

            def pick_walls_for_room(room_data=r, room_name=name, walls_storage=walls_var, update_func=update_wall_btn_text):
                """Pick walls for this specific room."""
                dialog.withdraw()
                try:
                    picked_walls = self._pick_walls_for_room_dialog(room_data, room_name)
                    if picked_walls:
                        current = walls_storage.get() or []
                        if isinstance(current, tuple): current = list(current)
                        updated = current + picked_walls
                        walls_storage.set(updated)
                        room_data['_picked_walls'] = updated
                        update_func(len(updated))
                finally:
                    dialog.deiconify()
            
            wall_btn = ttk.Button(input_frame, text='🧱 Add Walls', 
                                 command=pick_walls_for_room, style='Secondary.TButton')
            wall_btn.pack(side=tk.LEFT, padx=(12, 0))
            
            # Balcony segments frame (initially hidden)
            segments_frame = ttk.Frame(content_frame, style='Main.TFrame')
            balcony_segment_frames[idx] = segments_frame
            
            # Function to toggle balcony segments UI
            def toggle_balcony_ui(room_idx=idx, b_var=balcony_var, seg_frame=segments_frame, room_data=r):
                if b_var.get():
                    seg_frame.pack(fill=tk.X, pady=(8, 0))
                    # Initialize 4 segments using actual room dimensions
                    room_width = room_data.get('w', 0.0)
                    room_length = room_data.get('l', 0.0)
                    
                    # If we have actual dimensions, use them (2 walls of width, 2 walls of length)
                    # Otherwise fall back to perimeter/4
                    if room_width > 0 and room_length > 0:
                        wall_lengths = [room_length, room_width, room_length, room_width]
                    else:
                        perim_val = room_data.get('perim', 0.0)
                        fallback = perim_val / 4 if perim_val > 0 else 0
                        wall_lengths = [fallback, fallback, fallback, fallback]
                    
                    default_h = h_var.get()
                    
                    # Clear existing
                    for widget in seg_frame.winfo_children():
                        widget.destroy()
                    
                    ttk.Label(seg_frame, text="Wall Segments (Length × Height):", 
                             font=('Segoe UI Semibold', 9)).pack(anchor='w', pady=(4, 6))
                    
                    seg_vars = []
                    for i in range(4):
                        seg_row = ttk.Frame(seg_frame, style='Main.TFrame')
                        seg_row.pack(fill=tk.X, pady=2)
                        
                        ttk.Label(seg_row, text=f"  Wall {i+1}:", width=10).pack(side=tk.LEFT)
                        len_var = tk.StringVar(value=f"{wall_lengths[i]:.2f}")
                        h_var_seg = tk.StringVar(value=default_h)
                        
                        ttk.Entry(seg_row, textvariable=len_var, width=10).pack(side=tk.LEFT, padx=2)
                        ttk.Label(seg_row, text="m ×").pack(side=tk.LEFT, padx=2)
                        ttk.Entry(seg_row, textvariable=h_var_seg, width=10).pack(side=tk.LEFT, padx=2)
                        ttk.Label(seg_row, text="m").pack(side=tk.LEFT, padx=2)
                        
                        seg_vars.append((len_var, h_var_seg))
                    
                    # Store segment vars for later retrieval
                    balcony_segment_frames[f'{room_idx}_vars'] = seg_vars
                else:
                    seg_frame.pack_forget()
                    
            balcony_check.configure(command=toggle_balcony_ui)
            
            # Auto-check balcony if type is Balcony
            def on_type_change(*args):
                if type_var.get() == 'Balcony':
                    balcony_var.set(True)
                    toggle_balcony_ui()
            type_var.trace_add('write', lambda *args: on_type_change())
            
            # Initialize balcony UI if already marked
            if balcony_var.get():
                toggle_balcony_ui()
            
            entries.append((r, type_var, h_var, balcony_var, idx, sel_var, toggle_balcony_ui, walls_var, update_wall_btn_text))
        
        def save():
            for r, type_var, h_var, b_var, room_idx, sel_var, toggle_func, walls_storage, update_func in entries:
                r['room_type'] = type_var.get()
                try:
                    h_val = float(h_var.get())
                except Exception:
                    h_val = 0.0
                r['wall_height'] = h_val if h_val > 0 else None
                r['is_balcony'] = bool(b_var.get())
                
                # Save picked walls if any
                if '_picked_walls' in r:
                    picked_walls = r.pop('_picked_walls')
                    if picked_walls:
                        # Convert wall dicts to Wall objects and add to project
                        from bilind.models.wall import Wall
                        room_name = r.get('name', 'Room')
                        for wall_data in picked_walls:
                            wall_obj = Wall(
                                name=wall_data.get('name', 'Wall'),
                                layer=wall_data.get('layer', r.get('layer', '')),
                                length=wall_data.get('length', 0.0),
                                height=wall_data.get('height', 3.0),
                                gross_area=wall_data.get('gross_area'),
                                deduction_area=wall_data.get('deduction_area', 0.0),
                                net_area=wall_data.get('net_area')
                            )
                            # Set ceramic and openings if provided
                            if 'ceramic_height' in wall_data:
                                wall_obj.ceramic_height = wall_data['ceramic_height']
                            if 'opening_ids' in wall_data:
                                wall_obj.opening_ids = wall_data['opening_ids']
                            
                            self.project.walls.append(wall_obj)
                        
                        # Store wall references in room if needed
                        r['wall_count'] = len(picked_walls)
                
                # Clean up temp storage
                r.pop('_temp_walls', None)
                
                # Save balcony segments if applicable
                if r['is_balcony'] and f'{room_idx}_vars' in balcony_segment_frames:
                    seg_vars = balcony_segment_frames[f'{room_idx}_vars']
                    segments = []
                    for len_var, h_var_seg in seg_vars:
                        try:
                            ln = float(len_var.get())
                            ht = float(h_var_seg.get())
                            if ln > 0 and ht > 0:
                                segments.append({'length': ln, 'height': ht})
                        except:
                            pass
                    r['wall_segments'] = segments if segments else []
                else:
                    if 'wall_segments' not in r:
                        r['wall_segments'] = []
                    
            dialog.destroy()
        
        ttk.Button(btns, text='✅ Save All', command=save, style='Accent.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text='❌ Cancel', command=lambda: dialog.destroy(), style='Secondary.TButton').pack(side=tk.RIGHT, padx=4)
        
        dialog.wait_window()

    def _pick_walls_for_room_dialog(self, room_data: dict, room_name: str) -> list:
        """
        Interactive dialog to pick walls for a specific room with full customization.
        Returns list of wall dictionaries with name, height, ceramic_height, and opening assignments.
        """
        walls = []
        
        while True:
            # Ask if user wants to add another wall
            if walls:
                add_more = messagebox.askyesno(
                    "Add More Walls?",
                    f"Room '{room_name}' currently has {len(walls)} wall(s).\n\nPick more walls from AutoCAD?",
                    icon='question'
                )
                if not add_more:
                    break
            
            # Pick wall from AutoCAD
            self.update_status(f"Pick wall(s) for {room_name}...", icon="🧱")

            if not self.ensure_autocad():
                if not walls:
                    return []
                break
            
            try:
                picked_lines = self.picker.pick_walls(scale=self.scale, height=3.0)  # Temp height
                if not picked_lines:
                    if not walls:  # No walls picked at all
                        return []
                    break  # Cancel adding more
                
                # Process all picked walls
                for wall_raw in picked_lines:
                    wall_length = float(wall_raw.length if hasattr(wall_raw, 'length') else wall_raw.get('length', 0.0))
                    wall_layer = wall_raw.layer if hasattr(wall_raw, 'layer') else wall_raw.get('layer', '')
                    
                    # Now show configuration dialog for this wall
                    wall_config = self._configure_wall_dialog(
                        room_name=room_name,
                        wall_number=len(walls) + 1,
                        default_length=wall_length,
                        default_layer=wall_layer
                    )
                    
                    if wall_config:
                        walls.append(wall_config)
                    else:
                        # User cancelled this specific wall, continue to next if any
                        pass
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to pick wall: {e}")
                if not walls:
                    return []
                break
        
        return walls
    
    def _configure_wall_dialog(self, room_name: str, wall_number: int, default_length: float, default_layer: str) -> dict:
        """
        Dialog to configure a single wall with name, height, ceramic height, and openings.
        Returns wall configuration dict or None if cancelled.
        """
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Configure Wall {wall_number} - {room_name}")
        dialog.geometry("600x500")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Main frame
        main_frame = ttk.Frame(dialog, style='Main.TFrame', padding=16)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(main_frame, text=f"Wall Configuration", 
                 font=('Segoe UI Semibold', 14)).pack(anchor='w', pady=(0, 4))
        ttk.Label(main_frame, text=f"Room: {room_name} | Wall #{wall_number}", 
                 foreground=self.colors['text_secondary']).pack(anchor='w', pady=(0, 12))
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=8)
        
        # Input fields frame
        inputs = ttk.Frame(main_frame, style='Main.TFrame')
        inputs.pack(fill=tk.X, pady=8)
        
        # Wall Name
        row = 0
        ttk.Label(inputs, text="Wall Name:", width=18).grid(row=row, column=0, sticky='w', pady=6)
        name_var = tk.StringVar(value=f"Wall {wall_number}")
        ttk.Entry(inputs, textvariable=name_var, width=30).grid(row=row, column=1, sticky='ew', pady=6, padx=(8, 0))
        
        # Length (from AutoCAD pick)
        row += 1
        ttk.Label(inputs, text="Length (m):", width=18).grid(row=row, column=0, sticky='w', pady=6)
        length_var = tk.StringVar(value=f"{default_length:.2f}")
        ttk.Entry(inputs, textvariable=length_var, width=30).grid(row=row, column=1, sticky='ew', pady=6, padx=(8, 0))
        
        # Height
        row += 1
        ttk.Label(inputs, text="Wall Height (m):", width=18).grid(row=row, column=0, sticky='w', pady=6)
        height_var = tk.StringVar(value="3.0")
        ttk.Entry(inputs, textvariable=height_var, width=30).grid(row=row, column=1, sticky='ew', pady=6, padx=(8, 0))
        
        # Ceramic Height (0 = no ceramic)
        row += 1
        ttk.Label(inputs, text="Ceramic Height (m):", width=18).grid(row=row, column=0, sticky='w', pady=6)
        ceramic_var = tk.StringVar(value="0")
        ceramic_entry = ttk.Entry(inputs, textvariable=ceramic_var, width=30)
        ceramic_entry.grid(row=row, column=1, sticky='ew', pady=6, padx=(8, 0))
        ttk.Label(inputs, text="(0 = no ceramic)", foreground=self.colors['text_secondary'], 
                 font=('Segoe UI', 8)).grid(row=row, column=2, sticky='w', padx=4)
        
        inputs.columnconfigure(1, weight=1)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=12)
        
        # Openings assignment section
        ttk.Label(main_frame, text="Assign Openings (Doors/Windows):", 
                 font=('Segoe UI Semibold', 10)).pack(anchor='w', pady=(0, 8))
        
        # Openings list with checkboxes
        openings_frame = ttk.Frame(main_frame, style='Card.TLabelframe', padding=8)
        openings_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        
        # Create scrollable list
        canvas = tk.Canvas(openings_frame, bg=self.colors['bg_card'], highlightthickness=0, height=150)
        scrollbar = ttk.Scrollbar(openings_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Main.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Populate with all available openings
        opening_vars = {}
        all_openings = list(self.project.doors) + list(self.project.windows)
        
        if all_openings:
            for idx, opening in enumerate(all_openings):
                o_name = self._opening_name(opening)
                o_type = "Door" if opening in self.project.doors else "Window"
                icon = "🚪" if o_type == "Door" else "🪟"
                w = self._opening_attr(opening, 'w', 'width', 0.0) or 0.0
                h = self._opening_attr(opening, 'h', 'height', 0.0) or 0.0
                
                var = tk.BooleanVar(value=False)
                check = ttk.Checkbutton(
                    scrollable_frame,
                    text=f"{icon} {o_name} ({w:.2f}m × {h:.2f}m)",
                    variable=var
                )
                check.pack(anchor='w', pady=2)
                opening_vars[o_name] = var
        else:
            ttk.Label(scrollable_frame, text="No openings available. Add doors/windows first.",
                     foreground=self.colors['text_secondary']).pack(pady=20)
        
        # Result storage
        result = {}
        
        def save():
            try:
                # Validate inputs
                name = name_var.get().strip()
                if not name:
                    raise ValueError("Wall name cannot be empty")
                
                length = float(length_var.get())
                height = float(height_var.get())
                ceramic_h = float(ceramic_var.get())
                
                if length <= 0 or height <= 0:
                    raise ValueError("Length and height must be positive")
                if ceramic_h < 0 or ceramic_h > height:
                    raise ValueError("Ceramic height must be between 0 and wall height")
                
                # Collect selected openings
                selected_openings = [name for name, var in opening_vars.items() if var.get()]
                
                # Calculate areas
                gross_area = length * height
                ceramic_area = length * ceramic_h if ceramic_h > 0 else 0.0
                
                # Store result
                result['name'] = name
                result['layer'] = default_layer
                result['length'] = length
                result['height'] = height
                result['ceramic_height'] = ceramic_h
                result['gross_area'] = gross_area
                result['ceramic_area'] = ceramic_area
                result['opening_ids'] = selected_openings
                result['deduction_area'] = 0.0  # Will be calculated when openings are assigned
                result['net_area'] = gross_area  # Will be updated after deductions
                
                dialog.destroy()
                
            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e), parent=dialog)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame, style='Main.TFrame')
        btn_frame.pack(fill='x', pady=(8, 0))
        
        ttk.Button(btn_frame, text="✅ Save Wall", command=save, 
                  style='Accent.TButton').pack(side='left', padx=4)
        ttk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy, 
                  style='Secondary.TButton').pack(side='right', padx=4)
        
        dialog.wait_window()
        return result if result else None

    def edit_balcony_heights(self):
        """Edit per-wall heights for a selected balcony room (multi-height handling)."""
        sel = self.rooms_tab.rooms_tree.selection() if hasattr(self, 'rooms_tab') else []
        if not sel:
            messagebox.showwarning("Warning", "Select a balcony room first")
            return
        idx = self.rooms_tab.rooms_tree.index(sel[0])
        if idx >= len(self.project.rooms):
            return
        room = self.project.rooms[idx]
        # Resolve dict form
        if hasattr(room, 'to_dict'):
            room_dict = room.to_dict()
        else:
            room_dict = room
        if room_dict.get('room_type') != 'Balcony' and not room_dict.get('is_balcony'):
            messagebox.showinfo("Not Balcony", "Selected room is not marked as Balcony.")
            return
        perim = float(room_dict.get('perim') or getattr(room, 'perimeter', 0.0) or 0.0)
        segments = room_dict.get('wall_segments') or []
        if not segments:
            # Initialize 4 segments using actual room dimensions if available
            room_width = room_dict.get('w', 0.0) or getattr(room, 'width', 0.0)
            room_length = room_dict.get('l', 0.0) or getattr(room, 'length', 0.0)
            default_height = float(room_dict.get('wall_height') or 3.0)
            
            if room_width > 0 and room_length > 0:
                # Use actual dimensions: 2 walls of length, 2 walls of width
                wall_lengths = [room_length, room_width, room_length, room_width]
            else:
                # Fall back to equal segments
                base_len = perim / 4 if perim > 0 else 0
                wall_lengths = [base_len, base_len, base_len, base_len]
            
            segments = [{'length': length, 'height': default_height} for length in wall_lengths]
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Balcony Wall Heights - {room_dict.get('name','Room')}")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text="Adjust segment lengths & heights", font=('Segoe UI Semibold', 12)).pack(padx=12, pady=(10,6))
        container = ttk.Frame(dialog, padding=(8,4), style='Main.TFrame')
        container.pack(fill=tk.BOTH, expand=True)
        row_vars = []
        for i, seg in enumerate(segments):
            frm = ttk.Frame(container, padding=(4,2), style='Main.TFrame')
            frm.grid(row=i, column=0, sticky='w')
            ttk.Label(frm, text=f"Seg {i+1}", width=8).pack(side=tk.LEFT)
            l_var = tk.StringVar(value=f"{seg.get('length',0):.3f}")
            h_var = tk.StringVar(value=f"{seg.get('height',0):.3f}")
            ttk.Entry(frm, textvariable=l_var, width=8).pack(side=tk.LEFT, padx=4)
            ttk.Entry(frm, textvariable=h_var, width=8).pack(side=tk.LEFT, padx=4)
            row_vars.append((l_var, h_var))
        def save():
            new_segments = []
            for l_var, h_var in row_vars:
                try:
                    ln = float(l_var.get())
                    ht = float(h_var.get())
                except Exception:
                    continue
                if ln > 0 and ht > 0:
                    new_segments.append({'length': ln, 'height': ht})
            if not new_segments:
                messagebox.showerror("Error", "Provide valid segment values.")
                return
            gross = sum(s['length'] * s['height'] for s in new_segments)
            # Deduct openings if possible
            opening_area = 0.0
            try:
                opening_area = self.association.calculate_room_opening_area(room)
            except Exception:
                pass
            wall_finish_area = max(0.0, gross - opening_area)
            if hasattr(room, 'wall_segments'):
                room.wall_segments = new_segments
                room.is_balcony = True
                room.wall_finish_area = wall_finish_area
                room.wall_height = None
            else:
                room['wall_segments'] = new_segments
                room['is_balcony'] = True
                room['wall_finish_area'] = wall_finish_area
                room['wall_height'] = None
            self.refresh_rooms()
            dialog.destroy()
            self.update_status(f"Updated balcony segments for {room_dict.get('name','Room')}", icon="🏗️")
        btns = ttk.Frame(dialog, padding=(8,6), style='Main.TFrame')
        btns.pack(fill=tk.X)
        ttk.Button(btns, text='Save', command=save, style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(btns, text='Cancel', command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)
    
    # === PICKING FUNCTIONS ===
    
    def calibrate_scale(self):
        """
        Calibrate the drawing scale by picking 2 points in AutoCAD and entering the known distance.
        This is essential for PDF/scanned drawings where the scale is not 1:1.
        
        Workflow:
        1. User picks 2 points in AutoCAD (e.g., along a known dimension line)
        2. System measures the distance in drawing units
        3. User enters the known real-world distance
        4. Scale is calculated as: known_distance / measured_distance
        5. Scale is applied to project and UI
        """
        from tkinter import simpledialog

        if not self.ensure_autocad():
            return
        
        self.update_status("📏 Calibration: Pick first point in AutoCAD...", icon="📏")
        self.root.withdraw()
        
        try:
            # Prompt for first point
            try:
                pt1 = self.acad.prompt("Pick first calibration point:")
                if not pt1:
                    raise ValueError("No point selected")
            except Exception as e:
                self.root.deiconify()
                messagebox.showwarning("Cancelled", "Calibration cancelled - no first point selected.")
                self.update_status("Calibration cancelled", icon="⚠️")
                return
            
            self.update_status("📏 Calibration: Pick second point...", icon="📏")
            
            # Prompt for second point
            try:
                pt2 = self.acad.prompt("Pick second calibration point:")
                if not pt2:
                    raise ValueError("No point selected")
            except Exception as e:
                self.root.deiconify()
                messagebox.showwarning("Cancelled", "Calibration cancelled - no second point selected.")
                self.update_status("Calibration cancelled", icon="⚠️")
                return
            
            # Calculate measured distance in drawing units
            import math
            dx = pt2[0] - pt1[0]
            dy = pt2[1] - pt1[1]
            dz = pt2[2] - pt1[2] if len(pt1) > 2 and len(pt2) > 2 else 0
            measured_distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            self.root.deiconify()
            
            if measured_distance < 0.0001:
                messagebox.showerror("Error", "The two points are too close together. Please pick points farther apart.")
                self.update_status("Calibration failed - points too close", icon="❌")
                return
            
            # Prompt for known real-world distance
            known_distance_str = simpledialog.askstring(
                "Known Distance",
                f"Measured distance in drawing: {measured_distance:.4f} units\n\n"
                "Enter the known REAL distance between these points (in meters):",
                initialvalue="1.0"
            )
            
            if not known_distance_str:
                self.update_status("Calibration cancelled", icon="⚠️")
                return
            
            try:
                known_distance = float(known_distance_str)
                if known_distance <= 0:
                    raise ValueError("Distance must be positive")
            except (ValueError, TypeError):
                messagebox.showerror("Error", "Invalid distance. Please enter a positive number.")
                self.update_status("Calibration failed - invalid distance", icon="❌")
                return
            
            # Calculate scale factor
            new_scale = known_distance / measured_distance
            
            # Confirm with user
            result = messagebox.askyesno(
                "Confirm Calibration",
                f"Calibration Results:\n\n"
                f"• Measured in drawing: {measured_distance:.4f} units\n"
                f"• Known real distance: {known_distance} m\n"
                f"• Calculated scale factor: {new_scale:.6f}\n\n"
                f"Current scale: {self.scale:.6f}\n"
                f"New scale: {new_scale:.6f}\n\n"
                "Apply this calibration?",
                icon='question'
            )
            
            if result:
                # Update scale
                self.scale = new_scale
                self.project.scale = new_scale
                if hasattr(self, 'scale_var') and self.scale_var:
                    self.scale_var.set(f"{new_scale:.6f}")
                
                messagebox.showinfo(
                    "Success",
                    f"✅ Scale calibrated successfully!\n\n"
                    f"New scale factor: {new_scale:.6f}\n\n"
                    "Note: This scale will be applied to all future measurements.\n"
                    "Existing rooms/walls/openings are NOT retroactively updated."
                )
                self.update_status(f"✅ Scale calibrated: {new_scale:.6f}", icon="📏")
            else:
                self.update_status("Calibration cancelled by user", icon="⚠️")
                
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Error", f"Calibration error: {str(e)}")
            self.update_status(f"❌ Calibration error: {e}", icon="❌")
        finally:
            if not self.root.winfo_ismapped():
                self.root.deiconify()
    
    def pick_rooms(self):
        """
        Initiates the process of selecting room objects (closed polylines, hatches)
        from the active AutoCAD drawing. It calculates area, perimeter, and attempts
        to determine width and length from the bounding box.
        """
        self.update_scale()

        if not self.ensure_autocad():
            return
        self.update_status("Picking rooms from AutoCAD... Please select objects.", icon="🏠")
        self.root.withdraw()
        
        try:
            # Use AutoCADPicker to get rooms
            default_h = float(getattr(self.project, 'default_wall_height', 3.0) or 3.0)
            rooms = self.picker.pick_rooms(scale=self.scale, default_wall_height=default_h)

            normalized_rooms = []
            for room in rooms:
                if hasattr(room, "to_dict"):
                    normalized_rooms.append(room.to_dict())
                elif isinstance(room, dict):
                    normalized_rooms.append(room)

            if normalized_rooms:
                # Restore window BEFORE showing dialog (critical - dialog is transient to root)
                self.root.deiconify()
                
                # Prompt for details (type, wall height, balcony flag)
                self._prompt_room_details(normalized_rooms)
                self.project.rooms.extend(normalized_rooms)
                # Update finish fields for each new room (simple pass, openings may be assigned later)
                for r in normalized_rooms:
                    try:
                        perim = float(r.get('perim', 0.0) or 0.0)
                        area = float(r.get('area', 0.0) or 0.0)
                        wall_h = float(r.get('wall_height') or 0.0)

                        gross = 0.0
                        walls_data = r.get('walls', []) or []
                        if walls_data:
                            for wall in walls_data:
                                length = float(wall.get('length', 0.0) or 0.0)
                                height = float(wall.get('height', wall_h) or wall_h or 0.0)
                                if length > 0 and height > 0:
                                    gross += length * height
                        elif r.get('is_balcony') and r.get('wall_segments'):
                            for seg in r['wall_segments']:
                                length = float(seg.get('length', 0.0) or 0.0)
                                height = float(seg.get('height', 0.0) or 0.0)
                                if length > 0 and height > 0:
                                    gross += length * height
                        else:
                            gross = perim * wall_h if wall_h > 0 else 0.0

                        r['ceiling_finish_area'] = area
                        r['wall_finish_area'] = gross  # openings deducted later when assigned
                    except Exception:
                        pass
                self.refresh_rooms()
                messagebox.showinfo("Success", f"✅ Added {len(normalized_rooms)} room(s).")
                self.update_status(f"Added {len(normalized_rooms)} room(s)", icon="🏠")
            else:
                self.root.deiconify()
                self.update_status("No rooms selected.", icon="⚠️")
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Error Picking Rooms", f"Failed to pick rooms:\n{e}")
            self.update_status(f"Error: {e}", icon="❌")

    def pick_rooms_by_type(self):
        """
        Pick rooms from AutoCAD using a continuous Mini Picker toolbar.
        Allows picking multiple batches of different room types without closing the tool.
        """
        self.update_scale()

        if not self.ensure_autocad():
            return
        
        # Hide main window
        self.root.withdraw()
        
        def on_pick(room_type):
            """Callback for MiniPicker to pick a batch."""
            try:
                # Use AutoCADPicker with room_type parameter
                default_h = float(getattr(self.project, 'default_wall_height', 3.0) or 3.0)
                rooms = self.picker.pick_rooms(
                    scale=self.scale,
                    room_type=room_type,
                    default_wall_height=default_h,
                    existing_rooms=self.project.rooms
                )
                
                normalized_rooms = []
                for room in rooms:
                    if hasattr(room, "to_dict"):
                        normalized_rooms.append(room.to_dict())
                    elif isinstance(room, dict):
                        normalized_rooms.append(room)
                
                if normalized_rooms:
                    # Auto-calculate finish fields with defaults
                    default_h = float(self.project.default_wall_height or 3.0)
                    
                    for r in normalized_rooms:
                        try:
                            perim = float(r.get('perim', 0.0) or 0.0)
                            area = float(r.get('area', 0.0) or 0.0)
                            
                            # Set default wall height if not present
                            if not r.get('wall_height'):
                                r['wall_height'] = default_h
                                
                            wall_h = float(r.get('wall_height') or default_h)
                            
                            # Prefer explicit wall data when available
                            gross = 0.0
                            walls_data = r.get('walls', []) or []
                            if walls_data:
                                for wall in walls_data:
                                    length = float(wall.get('length', 0.0) or 0.0)
                                    height = float(wall.get('height', wall_h) or wall_h or 0.0)
                                    if length > 0 and height > 0:
                                        gross += length * height
                            else:
                                gross = perim * wall_h
                            r['ceiling_finish_area'] = area
                            r['wall_finish_area'] = gross
                            
                            # Set balcony flag if type implies it
                            if room_type in ['Balcony', 'Terrace']:
                                r['is_balcony'] = True
                                
                        except Exception:
                            pass
                    
                    self.project.rooms.extend(normalized_rooms)
                    return len(normalized_rooms)
                return 0
            except pythoncom.com_error as e:
                # Extract hresult from various formats
                hresult = getattr(e, 'hresult', None)
                if hresult is None and hasattr(e, 'args') and e.args:
                    hresult = e.args[0] if isinstance(e.args[0], int) else None
                
                if hresult == AutoCADPicker.RPC_E_CALL_REJECTED or hresult == -2147418111:
                    messagebox.showwarning(
                        "AutoCAD Busy",
                        "AutoCAD rejected the pick request.\n\n"
                        "Possible causes:\n"
                        "• AutoCAD is running another command\n"
                        "• A dialog is open in AutoCAD\n"
                        "• AutoCAD is processing something\n\n"
                        "Solution: Press ESC in AutoCAD to cancel any active commands, then try again."
                    )
                    self.update_status("AutoCAD was busy during pick", icon="⚠️")
                    return 0
                # Show generic error for other COM errors
                messagebox.showerror("AutoCAD Error", f"Pick failed: {e}")
                return 0
            except Exception as e:
                messagebox.showerror("Error", f"Pick failed: {e}")
                return 0

        def on_finish():
            """Callback when user is done."""
            self.root.deiconify()
            self.refresh_rooms()
            self.update_status("Continuous picking finished.", icon="✅")

        # Launch MiniPicker
        MiniPicker(self.root, on_pick, on_finish, sorted(list(ROOM_TYPES)), colors=self.colors)
    
    def pick_doors(self):
        """Initiates the process of selecting and counting door blocks in AutoCAD."""
        self._pick_and_count_openings('DOOR')

    def pick_windows(self):
        """Initiates the process of selecting and counting window blocks in AutoCAD."""
        self._pick_and_count_openings('WINDOW')

    def _pick_and_count_openings(self, opening_type):
        """
        Generic function to select and count opening blocks (doors/windows) in AutoCAD,
        then initiate a batch-add process with improved user guidance.
        """
        is_door = opening_type == 'DOOR'
        name = "doors" if is_door else "windows"
        icon = "🚪" if is_door else "🪟"
        
        self.update_scale()

        if not self.ensure_autocad():
            return
        self.update_status(f"Picking {name} from AutoCAD...", icon=icon)
        self.root.withdraw()

        openings = []
        try:
            openings = self.picker.pick_openings(opening_type, scale=self.scale)
        except pythoncom.com_error as e:
            hresult = getattr(e, 'hresult', None)
            if hresult == AutoCADPicker.RPC_E_CALL_REJECTED:
                messagebox.showwarning(
                    "AutoCAD Busy",
                    "AutoCAD is busy with another command. Finish it in AutoCAD and try again."
                )
                self.update_status("AutoCAD was busy during pick", icon="⚠️")
            else:
                messagebox.showerror("Error", f"Failed to pick {name}: {e}")
                self.update_status(f"Error picking {name}", icon="❌")
            openings = []
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while picking {name}: {str(e)}")
            self.update_status(f"Error picking {name}", icon="❌")
            openings = []
        finally:
            try:
                if not self.root.winfo_viewable():
                    self.root.deiconify()
            except Exception:
                self.root.deiconify()

        if not openings:
            messagebox.showwarning("Warning", f"No {name} were detected in the selection.")
            self.update_status(f"No {name} detected", icon="⚠️")
            return

        count = len(openings)
        if not messagebox.askyesno(
            f"Import {opening_type.title()}s",
            f"Detected {count} {name} from AutoCAD.\n\nAdd them to the project?"
        ):
            self.update_status("Import cancelled.", icon="🚫")
            return

        added_names, skipped = self._store_autocad_openings(opening_type, openings)
        if not added_names:
            messagebox.showwarning(
                "Warning",
                f"No valid {name} were added. Ensure the selected blocks expose width/height."
            )
            self.update_status(f"No valid {name} added", icon="⚠️")
            return

        self.refresh_openings()

        preview = ', '.join(added_names[:4])
        if len(added_names) > 4:
            preview += f" ... +{len(added_names)-4}"
        summary = f"✅ Added {len(added_names)} {name}."
        if preview:
            summary += f"\n{preview}"
        if skipped:
            summary += f"\n⚠️ Skipped {skipped} block(s) missing geometry."
        summary += "\n\nUse 'Assign Openings' to link them to rooms."
        messagebox.showinfo("Success", summary)
        self.update_status(f"Added {len(added_names)} {name}", icon=icon)

    def pick_walls(self):
        """Pick walls from AutoCAD and add to project using current scale."""
        self.update_scale()

        if not self.ensure_autocad():
            return
        try:
            default_height = getattr(self, 'last_wall_height', 3.0)
            height_str = simpledialog.askstring("Wall Height", "Enter wall height (meters):", initialvalue=f"{default_height}")
            if not height_str:
                return
            height = float(height_str)
            if height <= 0:
                raise ValueError("Height must be positive")
            # remember last value for next time
            self.last_wall_height = height
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Input", "Please enter a valid positive wall height.")
            return

        self.update_status("Picking walls from AutoCAD...", icon="🧱")
        self.root.withdraw()
        try:
            walls = self.picker.pick_walls(scale=self.scale, height=height)
            if walls:
                self.project.walls.extend(walls)
                self.refresh_walls()
                messagebox.showinfo("Success", f"✅ Added {len(walls)} wall(s).")
                self.update_status(f"Added {len(walls)} wall(s)", icon="🧱")
            else:
                messagebox.showwarning("Warning", "No valid walls found in selection.")
                self.update_status("No walls detected", icon="⚠️")
        except pythoncom.com_error as e:
            hresult = getattr(e, 'hresult', None)
            if hresult == AutoCADPicker.RPC_E_CALL_REJECTED:
                messagebox.showwarning(
                    "AutoCAD Busy",
                    "AutoCAD is temporarily busy processing another command.\n\n"
                    "Please click back into AutoCAD, finish the current command, and try again."
                )
                self.update_status("AutoCAD was busy during wall pick", icon="⚠️")
            else:
                messagebox.showerror("Error", f"Error picking walls: {e}")
                self.update_status("Error picking walls", icon="❌")
        except Exception as e:
            messagebox.showerror("Error", f"Error picking walls: {e}")
            self.update_status("Error picking walls", icon="❌")
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
        ttk.Label(
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

        # Placement height
        placement_default = 1.0 if opening_type == 'WINDOW' else 0.0
        ttk.Label(body, text="Placement Height (m)", foreground=self.colors['text_secondary']).grid(row=row, column=0, sticky='w', pady=6)
        placement_var = tk.StringVar(value=str(placement_default))
        ttk.Entry(body, textvariable=placement_var, width=12).grid(row=row, column=1, sticky='w', pady=6)
        placement_hint = ttk.Label(body, text="Height from floor to sill" if opening_type == 'WINDOW' else "Floor level", 
                                   foreground=self.colors['text_secondary'], font=('Segoe UI', 8))
        placement_hint.grid(row=row, column=2, sticky='w', padx=12, pady=6)
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
                placement_height = float(placement_var.get())
                weight = float(weight_var.get()) if weight_var is not None else 0.0
                layer = layer_var.get().strip() or ("Door" if opening_type == 'DOOR' else "Window")

                if width <= 0 or height <= 0:
                    raise ValueError("Width and height must be positive")
                if placement_height < 0:
                    raise ValueError("Placement height cannot be negative")

                storage = self._opening_storage(opening_type)

                if apply_var.get() == 'all':
                    base_len = len(storage)
                    for idx in range(count):
                        base_name = f"{prefix}{base_len + idx + 1}"
                        name = self._make_unique_name(opening_type, base_name)

                        record = self._build_opening_record(
                            opening_type,
                            name,
                            type_name,
                            width,
                            height,
                            qty,
                            weight,
                            layer=layer,
                            placement_height=placement_height
                        )
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
                            'layer': layer,
                            'placement_height': placement_height
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
    
    def get_opening_templates(self, opening_type):
        """Get all available templates: predefined + existing user openings.
        
        Returns list of dicts with keys: name, type, width, height, weight (doors), placement_height, description
        """
        from bilind.core.config import DEFAULT_DOOR_TEMPLATES, DEFAULT_WINDOW_TEMPLATES
        
        templates = []
        
        # Add predefined templates
        if opening_type == 'DOOR':
            templates.extend(DEFAULT_DOOR_TEMPLATES)
        else:
            templates.extend(DEFAULT_WINDOW_TEMPLATES)
        
        # Add existing user openings as templates
        storage = self._opening_storage(opening_type)
        for opening in storage:
            name = self._opening_name(opening)
            template = {
                'name': f"📋 {name}",  # Mark as existing
                'type': self._opening_attr(opening, 'type', 'material_type', '-'),
                'width': float(self._opening_attr(opening, 'w', 'width', 0.0) or 0.0),
                'height': float(self._opening_attr(opening, 'h', 'height', 0.0) or 0.0),
                'placement_height': float(self._opening_attr(opening, 'placement_height', 'placement_height', (1.0 if opening_type == 'WINDOW' else 0.0)) or (1.0 if opening_type == 'WINDOW' else 0.0)),
                'description': f"From existing {opening_type.lower()} '{name}'"
            }
            if opening_type == 'DOOR':
                # Prefer per-door weight if available, else total weight divided by qty
                weight_each = self._opening_attr(opening, 'weight_each', 'weight_each', None)
                if weight_each is None:
                    total_weight = self._opening_attr(opening, 'weight', 'weight', 0.0) or 0.0
                    qty = self._opening_attr(opening, 'qty', 'quantity', 1) or 1
                    try:
                        weight_each = float(total_weight) / max(1, int(qty))
                    except Exception:
                        weight_each = 0.0
                template['weight'] = float(weight_each or 0.0)
            templates.append(template)
        
        return templates
    
    def add_opening_manual(self, opening_type, number=None, defaults=None, assign_to_room=None):
        """Add a single door/window with full customization.
        
        Args:
            opening_type: 'DOOR' or 'WINDOW'
            number: Optional number suffix for name
            defaults: Optional dict of default values
            assign_to_room: Optional room name to auto-assign opening to
        """
        type_catalog = self.door_types if opening_type == 'DOOR' else self.window_types
        storage = self._opening_storage(opening_type)

        defaults = defaults or {}
        prefix = defaults.get('name_prefix') or ('D' if opening_type == 'DOOR' else 'W')
        suggested_name = defaults.get('name') or self._make_unique_name(opening_type, f"{prefix}{len(storage)+1}")
        # Default to PVC (most common in Middle East construction)
        type_default = defaults.get('type') or 'PVC'
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

        # Template selection dropdown
        ttk.Label(frame, text="📦 Template", foreground=self.colors['accent'], font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 8))
        
        templates = self.get_opening_templates(opening_type)
        template_names = ['-- Custom (manual entry) --'] + [t['name'] for t in templates]
        template_var = tk.StringVar(value=template_names[0])
        template_combo = ttk.Combobox(frame, textvariable=template_var, values=template_names, state='readonly', width=35)
        template_combo.grid(row=0, column=1, columnspan=2, sticky='ew', pady=(0, 8))
        
        def apply_template(*_):
            selected = template_var.get()
            if selected == template_names[0]:  # Custom
                return
            
            # Find selected template
            for tmpl in templates:
                if tmpl['name'] == selected:
                    type_var.set(tmpl['type'])
                    w_var.set(str(tmpl['width']))
                    h_var.set(str(tmpl['height']))
                    placement_var.set(str(tmpl['placement_height']))
                    if opening_type == 'DOOR' and weight_var:
                        weight_var.set(str(tmpl.get('weight', 0)))
                    update_type_info()
                    update_preview()
                    break
        
        template_combo.bind('<<ComboboxSelected>>', apply_template)
        
        ttk.Separator(frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew', pady=(0, 12))

        ttk.Label(frame, text="Name", foreground=self.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=(0, 6))
        name_var = tk.StringVar(value=suggested_name)
        ttk.Entry(frame, textvariable=name_var, width=20).grid(row=2, column=1, sticky='w', pady=(0, 6))

        ttk.Label(frame, text="Layer", foreground=self.colors['text_secondary']).grid(row=3, column=0, sticky='w', pady=6)
        layer_var = tk.StringVar(value=layer_default)
        ttk.Entry(frame, textvariable=layer_var, width=20).grid(row=3, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Type", foreground=self.colors['text_secondary']).grid(row=4, column=0, sticky='w', pady=6)
        type_var = tk.StringVar(value=type_default)
        type_combo = ttk.Combobox(frame, textvariable=type_var, values=list(type_catalog.keys()), state='readonly', width=22)
        type_combo.grid(row=4, column=1, sticky='w', pady=6)

        info_var = tk.StringVar(value=type_catalog.get(type_var.get(), {}).get('description', ''))
        info_label = ttk.Label(frame, textvariable=info_var, wraplength=240, foreground=self.colors['text_secondary'])
        info_label.grid(row=4, column=2, sticky='w', padx=12, pady=6)

        ttk.Label(frame, text="Width (m)", foreground=self.colors['text_secondary']).grid(row=5, column=0, sticky='w', pady=6)
        w_var = tk.StringVar(value=f"{width_default}")
        ttk.Entry(frame, textvariable=w_var, width=12).grid(row=5, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Height (m)", foreground=self.colors['text_secondary']).grid(row=6, column=0, sticky='w', pady=6)
        h_var = tk.StringVar(value=f"{height_default}")
        ttk.Entry(frame, textvariable=h_var, width=12).grid(row=6, column=1, sticky='w', pady=6)

        # Quantity (Hidden/Removed as per user request to simplify)
        # We keep the variable for compatibility but hide the UI controls
        qty_var = tk.StringVar(value=str(qty_default))
        # ttk.Label(frame, text="Quantity", foreground=self.colors['text_secondary']).grid(row=7, column=0, sticky='w', pady=6)
        # ttk.Entry(frame, textvariable=qty_var, width=12).grid(row=7, column=1, sticky='w', pady=6)
        # qty_hint = ttk.Label(frame, text="For this room", foreground=self.colors['text_secondary'], font=('Segoe UI', 8))
        # qty_hint.grid(row=7, column=2, sticky='w', padx=12)
        
        # Total Count - total across all rooms/walls
        total_count_default = defaults.get('total_count', qty_default)
        ttk.Label(frame, text="Total Quantity", foreground=self.colors['accent'], font=('Segoe UI', 9, 'bold')).grid(row=8, column=0, sticky='w', pady=6)
        total_count_var = tk.StringVar(value=str(total_count_default))
        ttk.Entry(frame, textvariable=total_count_var, width=12).grid(row=8, column=1, sticky='w', pady=6)
        total_count_hint = ttk.Label(frame, text="الكمية الكلية", foreground=self.colors['accent'], font=('Segoe UI', 8))
        total_count_hint.grid(row=8, column=2, sticky='w', padx=12)
        
        # Sync qty with total_count since we are in global edit mode
        def sync_qty(*_):
            try:
                qty_var.set(total_count_var.get())
            except:
                pass
        total_count_var.trace_add('write', sync_qty)
        
        # Placement height (height from floor to sill)
        placement_default = defaults.get('placement_height', 1.0 if opening_type == 'WINDOW' else 0.0)
        ttk.Label(frame, text="Placement Height (m)", foreground=self.colors['text_secondary']).grid(row=9, column=0, sticky='w', pady=6)
        placement_var = tk.StringVar(value=f"{placement_default}")
        ttk.Entry(frame, textvariable=placement_var, width=12).grid(row=9, column=1, sticky='w', pady=6)
        placement_hint = ttk.Label(frame, text="Height from floor to sill" if opening_type == 'WINDOW' else "Floor level", 
                                   foreground=self.colors['text_secondary'], font=('Segoe UI', 8))
        placement_hint.grid(row=9, column=2, sticky='w', padx=12)

        weight_var = tk.StringVar(value=f"{weight_default}") if opening_type == 'DOOR' else None
        weight_hint = None
        if opening_type == 'DOOR':
            ttk.Label(frame, text="Weight (kg each)", foreground=self.colors['text_secondary']).grid(row=10, column=0, sticky='w', pady=6)
            weight_entry = ttk.Entry(frame, textvariable=weight_var, width=12)
            weight_entry.grid(row=10, column=1, sticky='w', pady=6)
            weight_hint = ttk.Label(frame, text="", foreground=self.colors['warning'])
            weight_hint.grid(row=10, column=2, sticky='w', padx=12)
            row_preview = 11
        else:
            row_preview = 10

        preview_var = tk.StringVar(value="Preview: adjust values")
        preview_label = ttk.Label(frame, textvariable=preview_var, foreground=self.colors['accent'], font=('Segoe UI', 10, 'italic'))
        preview_label.grid(row=row_preview, column=0, columnspan=3, sticky='w', pady=(10, 4))

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
                total_count = max(1, int(total_count_var.get()))
                perim_each = 2 * (width + height)
                stone_total = perim_each * total_count  # Use total_count for stone
                area_total = width * height * total_count  # Use total_count for total area
                preview = f"Perim each: {perim_each:.2f} m • Stone total: {stone_total:.2f} lm (×{total_count})"
                if opening_type == 'WINDOW':
                    glass_total = width * height * 0.85 * total_count
                    preview += f" • Glass: {glass_total:.2f} m²"
                preview += f" • Area: {area_total:.2f} m²"
                preview_var.set(preview)
            except Exception:
                preview_var.set("Preview: enter valid values")

        type_combo.bind('<<ComboboxSelected>>', update_type_info)
        for var in (w_var, h_var, qty_var, total_count_var):
            var.trace_add('write', update_preview)
        update_type_info()
        update_preview()

        def save():
            try:
                desired_name = name_var.get().strip() or suggested_name
                # Ensure unique across dicts and model objects
                existing_names = {self._opening_name(o) for o in storage}
                if desired_name in existing_names:
                    desired_name = self._make_unique_name(opening_type, desired_name)

                width = float(w_var.get())
                height = float(h_var.get())
                qty = max(1, int(qty_var.get()))
                total_count = max(1, int(total_count_var.get()))
                weight_each = float(weight_var.get()) if weight_var is not None else 0.0
                placement_height = float(placement_var.get())

                if width <= 0 or height <= 0:
                    raise ValueError("Width and height must be positive")
                if placement_height < 0:
                    raise ValueError("Placement height cannot be negative")

                layer_value = layer_var.get().strip() or layer_default

                new_record = self._build_opening_record(opening_type,
                                                       desired_name,
                                                       type_var.get(),
                                                       width,
                                                       height,
                                                       qty,
                                                       weight_each,
                                                       layer=layer_value,
                                                       placement_height=placement_height,
                                                       total_count=total_count)
                storage.append(new_record)

                if assign_to_room:
                    self._link_opening_to_room(self._opening_name(new_record), assign_to_room)
                self.refresh_openings()
                
                # Refresh room manager if it exists
                if hasattr(self, 'room_manager_tab'):
                    self.room_manager_tab.refresh_rooms_list()
                    if self.room_manager_tab.selected_room:
                        self.room_manager_tab._refresh_openings_trees()
                
                dialog.destroy()
                icon = "🚪" if opening_type == 'DOOR' else "🪟"
                self.update_status(f"Added {opening_type.lower()} '{new_record.get('name', '-')}'", icon=icon)

            except ValueError as exc:
                messagebox.showerror("Error", f"Invalid input: {exc}")

        button_bar = ttk.Frame(dialog, padding=(18, 10), style='Main.TFrame')
        button_bar.pack(fill=tk.X)
        ttk.Button(button_bar, text="Save", command=save, style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)
    
    def delete_opening(self, opening_type):
        """Delete selected door/window"""
        tree = self.rooms_tab.doors_tree if opening_type == 'DOOR' else self.rooms_tab.windows_tree
        storage = self.project.doors if opening_type == 'DOOR' else self.project.windows
        
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", f"Select a {opening_type.lower()} to delete!")
            return
        
        # Get the name from the selected row (column 0 is Name)
        values = tree.item(selection[0])['values']
        if not values:
            messagebox.showerror("Error", "Could not read selected item.")
            return
        
        selected_name = values[0]
        
        # Find the opening in storage by name
        opening_idx = None
        opening = None
        for i, o in enumerate(storage):
            o_name = o.get('name') if isinstance(o, dict) else getattr(o, 'name', None)
            if o_name == selected_name:
                opening_idx = i
                opening = o
                break
        
        if opening_idx is None:
            messagebox.showerror("Error", f"Could not find {opening_type.lower()} '{selected_name}' in storage.")
            return
        
        if messagebox.askyesno("Confirm", f"Delete {opening_type.lower()} '{selected_name}'?"):
            opening_name = self._opening_name(opening)
            removed_links = self._unlink_opening_from_all_rooms(opening_name)
            # Also remove from walls
            self._remove_opening_from_walls(opening_name)
            del storage[opening_idx]
            self.refresh_openings()
            # Refresh rooms tab to update opening counts
            if hasattr(self, 'rooms_tab'):
                self.rooms_tab.refresh_data()
            icon = "🚪" if opening_type == 'DOOR' else "🪟"
            extra = f" and cleared {removed_links} room link(s)" if removed_links else ""
            self.update_status(f"Deleted {opening_type.lower()} '{selected_name}'{extra}", icon=icon)

    def edit_opening(self, opening_type):
        """Edit selected door/window in the rooms tab."""
        tree = self.rooms_tab.doors_tree if opening_type == 'DOOR' else self.rooms_tab.windows_tree
        storage = self.project.doors if opening_type == 'DOOR' else self.project.windows

        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", f"Select a {opening_type.lower()} to edit!")
            return

        # Get the name from the selected row (column 0 is Name)
        values = tree.item(selection[0])['values']
        if not values:
            messagebox.showerror("Error", "Could not read selected item.")
            return
        
        selected_name = values[0]
        
        # Find the opening in storage by name
        idx = None
        for i, o in enumerate(storage):
            o_name = o.get('name') if isinstance(o, dict) else getattr(o, 'name', None)
            if o_name == selected_name:
                idx = i
                break
        
        if idx is None:
            messagebox.showerror("Error", f"Could not find {opening_type.lower()} '{selected_name}' in storage.")
            return

        opening_dict = self._opening_to_dict(storage[idx])
        type_catalog = self.door_types if opening_type == 'DOOR' else self.window_types

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {opening_type.title()} - {opening_dict.get('name', '')}")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=(18, 14), style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        name_var = tk.StringVar(value=opening_dict.get('name', ''))
        layer_var = tk.StringVar(value=opening_dict.get('layer', ''))
        type_var = tk.StringVar(value=opening_dict.get('type', list(type_catalog.keys())[0]))
        width_var = tk.StringVar(value=str(opening_dict.get('w', opening_dict.get('width', 0.0))))
        height_var = tk.StringVar(value=str(opening_dict.get('h', opening_dict.get('height', 0.0))))
        qty_var = tk.StringVar(value=str(opening_dict.get('qty', opening_dict.get('quantity', 1))))
        total_count_var = tk.StringVar(value=str(opening_dict.get('total_count', opening_dict.get('qty', 1))))
        weight_each = opening_dict.get('weight_each', opening_dict.get('weight', 0.0))
        weight_var = tk.StringVar(value=str(weight_each)) if opening_type == 'DOOR' else None

        ttk.Label(frame, text="Name", foreground=self.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=name_var, width=22).grid(row=0, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Layer", foreground=self.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=layer_var, width=22).grid(row=1, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Type", foreground=self.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=6)
        type_combo = ttk.Combobox(frame, textvariable=type_var, values=list(type_catalog.keys()), state='readonly', width=24)
        type_combo.grid(row=2, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Width (m)", foreground=self.colors['text_secondary']).grid(row=3, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=width_var, width=12).grid(row=3, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Height (m)", foreground=self.colors['text_secondary']).grid(row=4, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=height_var, width=12).grid(row=4, column=1, sticky='w', pady=6)

        # Quantity (Hidden/Removed as per user request to simplify)
        # ttk.Label(frame, text="Quantity", foreground=self.colors['text_secondary']).grid(row=5, column=0, sticky='w', pady=6)
        # ttk.Entry(frame, textvariable=qty_var, width=12).grid(row=5, column=1, sticky='w', pady=6)
        # ttk.Label(frame, text="For this room", foreground=self.colors['text_secondary'], font=('Segoe UI', 8)).grid(row=5, column=2, sticky='w', padx=8)

        # Total Count field
        ttk.Label(frame, text="Total Quantity", foreground=self.colors['accent'], font=('Segoe UI', 9, 'bold')).grid(row=6, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=total_count_var, width=12).grid(row=6, column=1, sticky='w', pady=6)
        ttk.Label(frame, text="الكمية الكلية", foreground=self.colors['accent'], font=('Segoe UI', 8)).grid(row=6, column=2, sticky='w', padx=8)
        
        # Sync qty with total_count since we are in global edit mode
        def sync_qty(*_):
            try:
                qty_var.set(total_count_var.get())
            except:
                pass
        total_count_var.trace_add('write', sync_qty)

        # Placement height
        placement_height = opening_dict.get('placement_height', 1.0 if opening_type == 'WINDOW' else 0.0)
        placement_var = tk.StringVar(value=str(placement_height))
        ttk.Label(frame, text="Placement Height (m)", foreground=self.colors['text_secondary']).grid(row=7, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=placement_var, width=12).grid(row=7, column=1, sticky='w', pady=6)

        if opening_type == 'DOOR' and weight_var is not None:
            ttk.Label(frame, text="Weight (kg each)", foreground=self.colors['text_secondary']).grid(row=8, column=0, sticky='w', pady=6)
            ttk.Entry(frame, textvariable=weight_var, width=12).grid(row=8, column=1, sticky='w', pady=6)
            info_row = 9
        else:
            info_row = 8

        preview_var = tk.StringVar(value="Preview: adjust values")
        ttk.Label(frame, textvariable=preview_var, foreground=self.colors['accent'], font=('Segoe UI', 10, 'italic')).grid(row=info_row, column=0, columnspan=3, sticky='w', pady=(10, 4))

        def update_preview(*_):
            try:
                w = float(width_var.get())
                h = float(height_var.get())
                qty = max(1, int(qty_var.get()))
                total_count = max(1, int(total_count_var.get()))
                perim_each = 2 * (w + h)
                stone_total = perim_each * total_count
                area_total = w * h * total_count
                text = f"Perim each: {perim_each:.2f} m • Stone total: {stone_total:.2f} lm (×{total_count})"
                if opening_type == 'WINDOW':
                    glass_total = w * h * 0.85 * total_count
                    text += f" • Glass: {glass_total:.2f} m²"
                text += f" • Area: {area_total:.2f} m²"
                preview_var.set(text)
            except Exception:
                preview_var.set("Preview: enter valid values")

        for var in (width_var, height_var, qty_var, total_count_var):
            var.trace_add('write', update_preview)
        update_preview()

        def save():
            try:
                name = name_var.get().strip() or opening_dict.get('name', '')
                layer = layer_var.get().strip() or opening_dict.get('layer', '')
                width = float(width_var.get())
                height = float(height_var.get())
                qty = max(1, int(qty_var.get()))
                total_count = max(1, int(total_count_var.get()))
                placement_height = float(placement_var.get())
                if width <= 0 or height <= 0:
                    raise ValueError("Width and height must be positive")
                if placement_height < 0:
                    raise ValueError("Placement height cannot be negative")
                weight = float(weight_var.get()) if weight_var is not None else 0.0
                # Enforce unique name among other openings of same type
                existing_names = {self._opening_name(o) for i, o in enumerate(storage) if i != idx}
                if name in existing_names:
                    name = self._make_unique_name(opening_type, name)
                new_record = self._build_opening_record(opening_type, name, type_var.get(), width, height, qty, weight, layer=layer, placement_height=placement_height, total_count=total_count)
                storage[idx] = new_record
                self.refresh_openings()
                dialog.destroy()
                icon = "🚪" if opening_type == 'DOOR' else "🪟"
                self.update_status(f"Updated {opening_type.lower()} '{name}'", icon=icon)
            except ValueError as exc:
                messagebox.showerror("Invalid Input", f"Error: {exc}")
            except Exception:
                messagebox.showerror("Invalid Input", "Please enter valid numeric values for width, height, and quantity.")

        button_bar = ttk.Frame(dialog, padding=(18, 10), style='Main.TFrame')
        button_bar.pack(fill=tk.X)
        ttk.Button(button_bar, text="Save", command=save, style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)

    # === WALL DEDUCTIONS ===
    def deduct_from_walls(self):
        """Interactive wall deduction with selection, scope, and smarter distribution."""
        if not self.project.walls:
            messagebox.showwarning("No Walls", "Pick or add walls first.")
            return

        # Helpers for openings
        def _o_area(o):
            if o is None:
                return 0.0
            return float(o.get('area', 0.0)) if isinstance(o, dict) else float(getattr(o, 'area', 0.0))
        def _o_layer(o):
            return o.get('layer', '') if isinstance(o, dict) else getattr(o, 'layer', '')
        def _o_name(o):
            return o.get('name', 'Opening') if isinstance(o, dict) else getattr(o, 'name', 'Opening')
        def _o_icon(o):
            if isinstance(o, dict):
                t = o.get('type', '').upper()
            else:
                t = getattr(o, 'opening_type', '').upper()
            return '🚪' if t == 'DOOR' else '🪟'

        openings_all = list(self.project.doors) + list(self.project.windows)
        if not openings_all:
            messagebox.showwarning("No Openings", "No doors or windows to deduct. Pick or add some first.")
            return

        # Determine walls scope (selected vs all)
        walls_scope = []
        selected_names = set()
        tree = getattr(self, 'walls_tree', None)
        if tree is not None and tree.selection():
            for iid in tree.selection():
                vals = tree.item(iid, 'values')
                if vals:
                    selected_names.add(str(vals[0]))
        for w in self.project.walls:
            if hasattr(w, 'name'):
                name = w.name
            else:
                name = w.get('name', '')
            if not selected_names or name in selected_names:
                walls_scope.append(w)
        if not walls_scope:
            messagebox.showwarning("No Selection", "Select one or more walls, or clear selection to apply to all walls.")
            return

        # Ask user if they want to choose openings interactively
        choose_specific = messagebox.askyesno(
            "Deduct Openings",
            "Do you want to choose specific doors/windows to deduct?\nYes = choose list, No = auto by layer.",
            default=messagebox.YES
        )

        total_deductions = 0
        skipped_small = 0
        warnings = []
        min_area = max(0.0, float(getattr(self.project, 'min_opening_deduction_area', 0.0)))

        if choose_specific:
            # Build items for selector
            items = []
            for op in openings_all:
                a = _o_area(op)
                if a <= 0:
                    continue
                label = f"{_o_icon(op)} {_o_name(op)} • {_o_layer(op)}"
                items.append({'name': label, 'area': a, 'layer': _o_layer(op), 'raw': op})

            from bilind.ui.dialogs.item_selector_dialog import ItemSelectorDialog
            dialog = ItemSelectorDialog(self.root, "Select Openings to Deduct", items, show_quantity=True, colors=self.colors)
            selected = dialog.show()
            if not selected:
                return

            # Build selected openings list (expanded by qty)
            selected_openings = []
            for s in selected:
                item = s['item']
                qty = max(1, int(s.get('qty', 1)))
                a = float(item.get('area', 0.0))
                if a < min_area:
                    skipped_small += 1
                    continue
                for _ in range(qty):
                    selected_openings.append(item)

            if not selected_openings:
                messagebox.showinfo("No Openings Selected", "Nothing to deduct.")
                return

            ignore_layer = messagebox.askyesno(
                "Apply Mode",
                "Ignore layers and split selected openings equally across the chosen walls?\nYes = split equally, No = match by layer.",
                default=messagebox.NO
            )

            # Pre-compute gross areas for distribution
            def _gross(w):
                if hasattr(w, 'gross_area'):
                    return float(getattr(w, 'gross_area'))
                if isinstance(w, dict):
                    g = w.get('gross')
                    if g is None:
                        g = float(w.get('length', 0.0)) * float(w.get('height', 0.0))
                    return float(g or 0.0)
                return float(getattr(w, 'length', 0.0)) * float(getattr(w, 'height', 0.0))

            if ignore_layer:
                total_area = sum(float(it.get('area', 0.0)) for it in selected_openings)
                if total_area <= 0:
                    messagebox.showinfo("No Area", "Selected openings have zero total area.")
                    return
                # Choose distribution: proportional vs equal
                proportional = messagebox.askyesno(
                    "Distribution",
                    "Distribute proportionally by wall gross area?\nYes = proportional, No = equal share.",
                    default=messagebox.YES
                )
                total_gross = sum(_gross(w) for w in walls_scope) or 1.0
                for idx, w in enumerate(walls_scope):
                    gross = _gross(w)
                    if proportional:
                        share = (gross / total_gross) * total_area
                    else:
                        share = total_area / max(1, len(walls_scope))
                    deduct_total = min(share, gross)
                    total_deductions += 1
                    if hasattr(w, 'add_deduction'):
                        w.reset_deductions()
                        w.add_deduction(deduct_total)
                    else:
                        w['deduct'] = deduct_total
                        w['net'] = max(0.0, float(gross) - deduct_total)
            else:
                # Group selection by layer
                area_by_layer = {}
                for it in selected_openings:
                    lyr = it.get('layer', '')
                    area_by_layer[lyr] = area_by_layer.get(lyr, 0.0) + float(it.get('area', 0.0))

                proportional = messagebox.askyesno(
                    "Distribution",
                    "For matching layers, distribute proportionally by wall gross area?\nYes = proportional, No = equal share per layer.",
                    default=messagebox.YES
                )

                # Build walls grouped by layer
                walls_by_layer = {}
                for w in walls_scope:
                    lyr = w.layer if hasattr(w, 'layer') else w.get('layer', '')
                    walls_by_layer.setdefault(lyr, []).append(w)

                # Apply deduction per layer by distributing the layer total across its walls
                for lyr, total_area in area_by_layer.items():
                    group = walls_by_layer.get(lyr, [])
                    if not group:
                        continue
                    total_gross = sum(_gross(w) for w in group) or 1.0
                    for idx, w in enumerate(group):
                        gross = _gross(w)
                        if proportional:
                            share = (gross / total_gross) * total_area
                        else:
                            share = total_area / len(group)
                        deduct_total = min(share, gross)
                        if gross > 0 and deduct_total > (gross * 0.8):
                            name = w.name if hasattr(w, 'name') else w.get('name', f'Wall{idx+1}')
                            warnings.append(f"⚠️ {name}: Deduction ({deduct_total:.2f} m²) is {(deduct_total/gross)*100:.0f}% of gross area")
                        if hasattr(w, 'add_deduction'):
                            w.reset_deductions()
                            w.add_deduction(deduct_total)
                        else:
                            w['deduct'] = deduct_total
                            w['net'] = max(0.0, float(gross) - deduct_total)
                        total_deductions += 1
        else:
            # Auto by layer (previous behavior), limited to scope
            def _gross(w):
                if hasattr(w, 'gross_area'):
                    return float(getattr(w, 'gross_area'))
                if isinstance(w, dict):
                    g = w.get('gross')
                    if g is None:
                        g = float(w.get('length', 0.0)) * float(w.get('height', 0.0))
                    return float(g or 0.0)
                return float(getattr(w, 'length', 0.0)) * float(getattr(w, 'height', 0.0))

            # Compute area by layer from all openings
            area_by_layer = {}
            for op in openings_all:
                try:
                    a = float(_o_area(op) or 0.0)
                    if a < min_area:
                        skipped_small += 1
                        continue
                    lyr = _o_layer(op)
                    area_by_layer[lyr] = area_by_layer.get(lyr, 0.0) + a
                except Exception:
                    continue

            # Group walls by layer for scoped walls only
            walls_by_layer = {}
            for w in walls_scope:
                lyr = w.layer if hasattr(w, 'layer') else w.get('layer', '')
                walls_by_layer.setdefault(lyr, []).append(w)

            # Ask distribution mode
            proportional = messagebox.askyesno(
                "Distribution",
                "Auto mode: distribute per layer proportionally by wall gross area?\nYes = proportional, No = equal share.",
                default=messagebox.YES
            )

            for lyr, total_area in area_by_layer.items():
                group = walls_by_layer.get(lyr, [])
                if not group:
                    continue
                total_gross = sum(_gross(w) for w in group) or 1.0
                for idx, w in enumerate(group):
                    gross = _gross(w)
                    if proportional:
                        share = (gross / total_gross) * total_area
                    else:
                        share = total_area / len(group)
                    deduct_total = min(share, gross)
                    if gross > 0 and deduct_total > (gross * 0.8):
                        name = w.name if hasattr(w, 'name') else w.get('name', f'Wall{idx+1}')
                        warnings.append(f"⚠️ {name}: Deduction ({deduct_total:.2f} m²) is {(deduct_total/gross)*100:.0f}% of gross area")
                    if hasattr(w, 'add_deduction'):
                        w.reset_deductions()
                        w.add_deduction(deduct_total)
                    else:
                        w['deduct'] = deduct_total
                        w['net'] = max(0.0, float(gross) - deduct_total)
                    total_deductions += 1

        # Refresh UI
        self.refresh_walls()
        if hasattr(self, 'rooms_tab'):
            self.rooms_tab.refresh_data()

        summary_parts = [
            f"✅ Deductions updated for {len(walls_scope)} wall(s)"
        ]
        if skipped_small > 0:
            summary_parts.append(f"ℹ️ Skipped {skipped_small} small openings (< {min_area} m²)")
        summary = "\n".join(summary_parts)
        self.update_status(summary.replace('\n', ' • '), icon="➖")
        messagebox.showinfo("Deductions Applied", summary)

    # === FINISHES WRAPPERS (called by Finishes tab buttons) ===
    def add_finish_from_source(self, key: str, source: str):
        if hasattr(self, 'finishes_tab'):
            return self.finishes_tab.add_finish_from_source(key, source)

    def add_walls_from_rooms(self, key: str):
        if hasattr(self, 'finishes_tab'):
            return self.finishes_tab.add_walls_from_rooms(key)

    def delete_finish_item(self, key: str):
        if hasattr(self, 'finishes_tab'):
            return self.finishes_tab.delete_finish_item(key)

    def deduct_ceramic_from_finish(self, key: str):
        if hasattr(self, 'finishes_tab'):
            return self.finishes_tab.deduct_ceramic_from_finish(key)

    # === ROOMS CRUD ===
    def add_room_manual(self):
        """Minimal dialog to add a room manually."""
        from bilind.models.room import ROOM_TYPES, FLOOR_PROFILES
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Room")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=(16, 12), style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Name", foreground=self.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=6)
        name_var = tk.StringVar(value=f"Room{len(self.project.rooms)+1}")
        ttk.Entry(frame, textvariable=name_var, width=24).grid(row=0, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Room Type", foreground=self.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=6)
        type_var = tk.StringVar(value="[Not Set]")
        type_combo = ttk.Combobox(frame, textvariable=type_var, values=ROOM_TYPES, width=22, state='readonly')
        type_combo.grid(row=1, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Layer", foreground=self.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=6)
        layer_var = tk.StringVar(value="A-ROOM")
        ttk.Entry(frame, textvariable=layer_var, width=24).grid(row=2, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Width (m)", foreground=self.colors['text_secondary']).grid(row=3, column=0, sticky='w', pady=6)
        w_var = tk.StringVar(value="4.0")
        ttk.Entry(frame, textvariable=w_var, width=12).grid(row=3, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Length (m)", foreground=self.colors['text_secondary']).grid(row=4, column=0, sticky='w', pady=6)
        l_var = tk.StringVar(value="5.0")
        ttk.Entry(frame, textvariable=l_var, width=12).grid(row=4, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Floor #", foreground=self.colors['text_secondary']).grid(row=5, column=0, sticky='w', pady=6)
        floor_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=floor_var, width=12).grid(row=5, column=1, sticky='w', pady=6)

        ttk.Label(frame, text="Floor Profile", foreground=self.colors['text_secondary']).grid(row=6, column=0, sticky='w', pady=6)
        floor_profile_var = tk.StringVar(value="Ground")
        ttk.Combobox(
            frame,
            textvariable=floor_profile_var,
            values=FLOOR_PROFILES,
            width=22,
            state='readonly'
        ).grid(row=6, column=1, sticky='w', pady=6)

        # --- Quick Assign Existing Openings Section ---
        assign_label = ttk.Label(frame, text="Assign Existing Openings", foreground=self.colors['accent'], font=('Segoe UI Semibold', 10))
        assign_label.grid(row=7, column=0, columnspan=2, sticky='w', pady=(14,4))

        doors_windows_container = ttk.Frame(frame, style='Main.TFrame')
        doors_windows_container.grid(row=8, column=0, columnspan=3, sticky='ew')
        doors_windows_container.columnconfigure(0, weight=1)

        door_vars = {}
        window_vars = {}

        def _make_scrollable(parent, title_text):
            outer = ttk.Labelframe(parent, text=title_text, style='Card.TLabelframe')
            outer.pack(fill='x', pady=6)
            canvas = tk.Canvas(outer, height=110, bg=self.colors['bg_card'], highlightthickness=0)
            vsb = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
            inner = ttk.Frame(canvas, style='Main.TFrame')
            canvas.create_window((0,0), window=inner, anchor='nw')
            canvas.configure(yscrollcommand=vsb.set)
            canvas.pack(side='left', fill='both', expand=True)
            vsb.pack(side='right', fill='y')
            inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            return inner

        # Doors list
        if self.project.doors:
            inner_doors = _make_scrollable(doors_windows_container, '🚪 Doors')
            for d in self.project.doors:
                d_dict = self._opening_to_dict(d)
                dname = d_dict.get('name','')
                if not dname:
                    continue
                var = tk.BooleanVar(value=False)
                door_vars[dname] = var
                txt = f"{dname}  {d_dict.get('w',0):.2f}×{d_dict.get('h',0):.2f} m  ({d_dict.get('area',0):.2f} m²)"
                chk = tk.Checkbutton(inner_doors, text=txt, variable=var,
                                     bg=self.colors['bg_card'], fg=self.colors['text_primary'],
                                     activebackground=self.colors['bg_card'], activeforeground=self.colors['accent'],
                                     anchor='w', padx=6)
                chk.pack(fill='x', pady=2)
        else:
            inner_doors = _make_scrollable(doors_windows_container, '🚪 Doors')
            tk.Label(inner_doors, text='No doors yet', bg=self.colors['bg_card'], fg=self.colors['text_secondary'], font=('Segoe UI',9,'italic')).pack(pady=4, anchor='w')

        # Windows list
        if self.project.windows:
            inner_windows = _make_scrollable(doors_windows_container, '🪟 Windows')
            for w in self.project.windows:
                w_dict = self._opening_to_dict(w)
                wname = w_dict.get('name','')
                if not wname:
                    continue
                var = tk.BooleanVar(value=False)
                window_vars[wname] = var
                txt = f"{wname}  {w_dict.get('w',0):.2f}×{w_dict.get('h',0):.2f} m  ({w_dict.get('area',0):.2f} m²)"
                chk = tk.Checkbutton(inner_windows, text=txt, variable=var,
                                     bg=self.colors['bg_card'], fg=self.colors['text_primary'],
                                     activebackground=self.colors['bg_card'], activeforeground=self.colors['accent'],
                                     anchor='w', padx=6)
                chk.pack(fill='x', pady=2)
        else:
            inner_windows = _make_scrollable(doors_windows_container, '🪟 Windows')
            tk.Label(inner_windows, text='No windows yet', bg=self.colors['bg_card'], fg=self.colors['text_secondary'], font=('Segoe UI',9,'italic')).pack(pady=4, anchor='w')

        # Quick summary label updates as user toggles
        summary_var = tk.StringVar(value='No openings selected')
        summary_lbl = ttk.Label(frame, textvariable=summary_var, foreground=self.colors['text_secondary'])
        summary_lbl.grid(row=9, column=0, columnspan=3, sticky='w', pady=(6,4))

        def _refresh_summary(*_):
            sel_doors = [n for n,v in door_vars.items() if v.get()]
            sel_windows = [n for n,v in window_vars.items() if v.get()]
            total = len(sel_doors) + len(sel_windows)
            if total == 0:
                summary_var.set('No openings selected')
            else:
                summary_var.set(f"Selected: {len(sel_doors)} door(s), {len(sel_windows)} window(s)")
        for v in list(door_vars.values()) + list(window_vars.values()):
            v.trace_add('write', _refresh_summary)
        _refresh_summary()

        def save():
            try:
                name = name_var.get().strip() or f"Room{len(self.project.rooms)+1}"
                # Ensure unique room name to keep assignments reliable
                existing_names = {self._room_name(r) for r in self.project.rooms}
                if name in existing_names:
                    base = name
                    suffix = 2
                    while f"{base}{suffix}" in existing_names:
                        suffix += 1
                    name = f"{base}{suffix}"
                room_type = type_var.get()
                layer = layer_var.get().strip() or "A-ROOM"
                w = float(w_var.get())
                l = float(l_var.get())
                if w <= 0 or l <= 0:
                    raise ValueError
                perim = 2 * (w + l)
                area = w * l
                try:
                    floor_no = int(float(floor_var.get() or 0))
                except ValueError:
                    floor_no = 0
                floor_profile = floor_profile_var.get() or "[Not Set]"
                if floor_profile not in FLOOR_PROFILES:
                    floor_profile = "[Not Set]"
                room = Room(
                    name=name,
                    layer=layer,
                    area=area,
                    perimeter=perim,
                    width=w,
                    length=l,
                    room_type=room_type,
                    floor=floor_no,
                    floor_profile=floor_profile,
                )
                # Assign selected openings immediately
                opening_ids = []
                for dname,var in door_vars.items():
                    if var.get():
                        opening_ids.append(dname)
                for wname,var in window_vars.items():
                    if var.get():
                        opening_ids.append(wname)
                if opening_ids:
                    # Persist opening ids on room (dataclass supports dynamic attr assignment)
                    try:
                        setattr(room, 'opening_ids', opening_ids)
                    except Exception:
                        pass
                    # Update each opening's assigned_rooms list
                    for collection in (self.project.doors, self.project.windows):
                        for o in collection:
                            o_dict = self._opening_to_dict(o)
                            oname = o_dict.get('name')
                            if oname in opening_ids:
                                # Support dict or dataclass
                                if isinstance(o, dict):
                                    rooms_list = o.get('assigned_rooms', []) or []
                                    if name not in rooms_list:
                                        rooms_list.append(name)
                                    o['assigned_rooms'] = rooms_list
                                else:
                                    try:
                                        rooms_list = getattr(o, 'assigned_rooms', []) or []
                                        if name not in rooms_list:
                                            rooms_list.append(name)
                                        setattr(o, 'assigned_rooms', rooms_list)
                                    except Exception:
                                        pass
                self.project.rooms.append(room)
                # Rebuild association to capture new assignments
                self._rebuild_association()
                self.refresh_rooms()
                dialog.destroy()
                assigned_msg = ''
                if opening_ids:
                    d_ct = sum(1 for oid in opening_ids if oid in door_vars)
                    w_ct = sum(1 for oid in opening_ids if oid in window_vars)
                    assigned_msg = f" • Assigned {d_ct} door(s), {w_ct} window(s)"
                self.update_status(f"Added room '{name}' ({room_type}){assigned_msg}", icon="🏠")
            except Exception:
                messagebox.showerror("Invalid Input", "Enter valid positive numbers for width and length.")

        btn = ttk.Frame(dialog, padding=(16, 8), style='Main.TFrame')
        btn.pack(fill=tk.X)
        ttk.Button(btn, text="Save", command=save, style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(btn, text="Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)
    
    def import_rooms_from_csv(self):
        """
        Import rooms from a CSV file.
        
        Expected CSV format (with header row):
        Name,Layer,Width,Length,Perimeter,Area
        
        Minimal requirements: Name and Area columns
        Width, Length, Perimeter are calculated if missing
        """
        from tkinter import filedialog
        import csv
        
        # Prompt for CSV file
        filepath = filedialog.askopenfilename(
            title="Import Rooms from CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            imported_rooms = []
            errors = []
            
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                
                # Detect delimiter (comma or semicolon)
                delimiter = ',' if sample.count(',') > sample.count(';') else ';'
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                    try:
                        # Required field: Name
                        name = row.get('Name', '').strip() or row.get('name', '').strip()
                        if not name:
                            name = f"Imported_Room_{len(imported_rooms)+1}"
                        
                        # Get layer (optional)
                        layer = row.get('Layer', '').strip() or row.get('layer', '').strip() or 'IMPORTED'
                        
                        # Try to get dimensions
                        width_str = row.get('Width', '') or row.get('W', '') or row.get('width', '') or row.get('w', '')
                        length_str = row.get('Length', '') or row.get('L', '') or row.get('length', '') or row.get('l', '')
                        perim_str = row.get('Perimeter', '') or row.get('perim', '') or row.get('Perim', '')
                        area_str = row.get('Area', '') or row.get('area', '')
                        
                        # Parse numbers
                        width = float(width_str) if width_str else None
                        length = float(length_str) if length_str else None
                        perimeter = float(perim_str) if perim_str else None
                        area = float(area_str) if area_str else None
                        
                        # Validate and calculate missing values
                        if area is None:
                            if width and length:
                                area = width * length
                            else:
                                raise ValueError(f"Row {row_num}: Missing area or width/length")
                        
                        if width is None or length is None:
                            # Assume square if only area is given
                            if area:
                                width = length = area ** 0.5
                            else:
                                raise ValueError(f"Row {row_num}: Cannot determine dimensions")
                        
                        if perimeter is None:
                            perimeter = 2 * (width + length)
                        
                        # Validate positive values
                        if area <= 0 or width <= 0 or length <= 0:
                            raise ValueError(f"Row {row_num}: Dimensions must be positive")
                        
                        # Create room object
                        room = Room(
                            name=name,
                            layer=layer,
                            area=area,
                            perimeter=perimeter,
                            width=width,
                            length=length
                        )
                        
                        imported_rooms.append(room)
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        continue
            
            # Show import results
            if imported_rooms:
                self.project.rooms.extend(imported_rooms)
                self._rebuild_association()  # Rebuild associations with new rooms
                self.refresh_rooms()
                
                result_msg = f"✅ Successfully imported {len(imported_rooms)} room(s)"
                if errors:
                    result_msg += f"\n\n⚠️ {len(errors)} error(s):\n" + "\n".join(errors[:5])
                    if len(errors) > 5:
                        result_msg += f"\n... and {len(errors)-5} more"
                
                messagebox.showinfo("Import Complete", result_msg)
                self.update_status(f"Imported {len(imported_rooms)} rooms from CSV", icon="📥")
            else:
                error_msg = "No valid rooms found in CSV file."
                if errors:
                    error_msg += "\n\nErrors:\n" + "\n".join(errors[:10])
                messagebox.showerror("Import Failed", error_msg)
                self.update_status("CSV import failed", icon="❌")
                
        except Exception as e:
            messagebox.showerror(
                "Import Error",
                f"Failed to read CSV file:\n{str(e)}\n\n"
                "Expected format:\n"
                "Name,Layer,Width,Length,Perimeter,Area\n"
                "Room1,A-ROOM,4.0,5.0,18.0,20.0"
            )
            self.update_status(f"CSV import error: {e}", icon="❌")

    def edit_room(self):
        from bilind.models.room import ROOM_TYPES
        
        sel = self.rooms_tab.rooms_tree.selection() if hasattr(self, 'rooms_tab') else []
        if not sel:
            messagebox.showwarning("Warning", "Select a room to edit!")
            return
        idx = self.rooms_tab.rooms_tree.index(sel[0])
        room = self.project.rooms[idx]
        # Prepare current values
        if isinstance(room, dict):
            name_cur = room.get('name', f'Room{idx+1}')
            type_cur = room.get('room_type', '[Not Set]')
            layer_cur = room.get('layer', 'A-ROOM')
            w_cur = room.get('w') or 0.0
            l_cur = room.get('l') or 0.0
        else:
            name_cur = getattr(room, 'name', f'Room{idx+1}')
            type_cur = getattr(room, 'room_type', '[Not Set]')
            layer_cur = getattr(room, 'layer', 'A-ROOM')
            w_cur = getattr(room, 'width', None) or 0.0
            l_cur = getattr(room, 'length', None) or 0.0

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Room - {name_cur}")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=(16, 12), style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        name_var = tk.StringVar(value=name_cur)
        type_var = tk.StringVar(value=type_cur)
        layer_var = tk.StringVar(value=layer_cur)
        w_var = tk.StringVar(value=f"{w_cur}")
        l_var = tk.StringVar(value=f"{l_cur}")
        
        ttk.Label(frame, text="Name").grid(row=0, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=name_var, width=24).grid(row=0, column=1, sticky='w', pady=6)
        
        ttk.Label(frame, text="Room Type").grid(row=1, column=0, sticky='w', pady=6)
        ttk.Combobox(frame, textvariable=type_var, values=ROOM_TYPES, width=22, state='readonly').grid(row=1, column=1, sticky='w', pady=6)
        
        ttk.Label(frame, text="Layer").grid(row=2, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=layer_var, width=24).grid(row=2, column=1, sticky='w', pady=6)
        
        ttk.Label(frame, text="Width (m)").grid(row=3, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=w_var, width=12).grid(row=3, column=1, sticky='w', pady=6)
        
        ttk.Label(frame, text="Length (m)").grid(row=4, column=0, sticky='w', pady=6)
        ttk.Entry(frame, textvariable=l_var, width=12).grid(row=4, column=1, sticky='w', pady=6)

        def save():
            try:
                name = name_var.get().strip() or name_cur
                room_type = type_var.get()
                layer = layer_var.get().strip() or layer_cur
                w = float(w_var.get())
                l = float(l_var.get())
                perim = 2 * (w + l)
                area = w * l
                # Ensure unique name among other rooms
                existing = {self._room_name(r) for i, r in enumerate(self.project.rooms) if i != idx}
                if name in existing:
                    base = name
                    suffix = 2
                    while f"{base}{suffix}" in existing:
                        suffix += 1
                    name = f"{base}{suffix}"
                if hasattr(room, 'name'):
                    room.name = name
                    room.room_type = room_type
                    room.layer = layer
                    room.width = w
                    room.length = l
                    room.perimeter = perim
                    room.area = area
                else:
                    room.update({'name': name, 'room_type': room_type, 'layer': layer, 'w': w, 'l': l, 'perim': perim, 'area': area})
                # Recompute finish areas if wall height stored
                wall_h = getattr(room, 'wall_height', None) if hasattr(room, 'wall_height') else room.get('wall_height')
                if wall_h:
                    try:
                        h_val = float(wall_h)
                        if hasattr(room, 'wall_finish_area'):
                            room.wall_finish_area = perim * h_val
                            room.ceiling_finish_area = area
                        else:
                            room['wall_finish_area'] = perim * h_val
                            room['ceiling_finish_area'] = area
                    except Exception:
                        pass
                self.refresh_rooms()
                dialog.destroy()
                self.update_status(f"Updated room '{name}' ({room_type})", icon="✏️")
            except Exception:
                messagebox.showerror("Invalid Input", "Enter valid room dimensions.")

        btn = ttk.Frame(dialog, padding=(16, 8), style='Main.TFrame')
        btn.pack(fill=tk.X)
        ttk.Button(btn, text="Save", command=save, style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(btn, text="Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)

    def delete_room(self):
        sel = self.rooms_tab.rooms_tree.selection() if hasattr(self, 'rooms_tab') else []
        if not sel:
            messagebox.showwarning("Warning", "Select a room to delete!")
            return
        if not messagebox.askyesno("Confirm", "Delete selected room?"):
            return
        idx = self.rooms_tab.rooms_tree.index(sel[0])
        del self.project.rooms[idx]
        self.refresh_rooms()
        self.update_status("Deleted room", icon="🗑️")

    def assign_openings_to_room(self):
        """Open assignment dialog and persist selected openings for chosen room."""
        if not hasattr(self, 'rooms_tab'):
            messagebox.showerror("Error", "Rooms tab is not available.")
            return

        selection = self.rooms_tab.rooms_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a room first!")
            return

        idx = self.rooms_tab.rooms_tree.index(selection[0])
        if idx >= len(self.project.rooms):
            messagebox.showerror("Error", "Selected room index is out of range.")
            return

        room_obj = self.project.rooms[idx]
        room_payload = room_obj.to_dict() if hasattr(room_obj, 'to_dict') else dict(room_obj)
        room_payload.setdefault('opening_ids', self.association.get_room_opening_ids(room_obj))

        door_dicts = [self._opening_to_dict(o) for o in self.project.doors]
        window_dicts = [self._opening_to_dict(o) for o in self.project.windows]

        dialog = OpeningAssignmentDialog(
            parent=self.root,
            room=room_payload,
            doors=door_dicts,
            windows=window_dicts,
            get_opening_func=self._get_opening_dict_by_name,
            colors=self.colors
        )

        result = dialog.show()
        if result is None:
            self.update_status("Opening assignment cancelled", icon="🚫")
            return

        self.association.set_room_opening_ids(room_obj, result)
        self.refresh_rooms()
        room_name = room_payload.get('name', f"Room {idx+1}")
        self.update_status(f"Assigned {len(result)} opening(s) to {room_name}", icon="🔗")
    
    def edit_wall(self):
        """Edit selected wall with modern styling"""
        selection = self.walls_tab.walls_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a wall to edit!")
            return
        
        idx = self.walls_tab.walls_tree.index(selection[0])
        wall = self.project.walls[idx]
        
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
                self.project.walls[idx] = {
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
        selection = self.walls_tab.walls_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a wall to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected wall?"):
            idx = self.walls_tab.walls_tree.index(selection[0])
            del self.project.walls[idx]
            self.refresh_walls()
            self.update_status("Deleted wall", icon="🧱")
    
    def delete_multiple(self, data_type):
        """Delete multiple selected items with modern UI"""
        # Map data types to their storage and tree
        mappings = {
            'rooms': (self.project.rooms, self.rooms_tab.rooms_tree, 'Rooms'),
            'doors': (self.project.doors, self.rooms_tab.doors_tree, 'Doors'),
            'windows': (self.project.windows, self.rooms_tab.windows_tree, 'Windows'),
            'walls': (self.project.walls, self.walls_tab.walls_tree, 'Walls')
        }
        
        if data_type not in mappings:
            return
        
        storage, tree, label = mappings[data_type]
        
        if not storage:
            messagebox.showinfo("Empty", f"No {label.lower()} to delete!")
            return
        
        # Create modern selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"🗑️ Delete Multiple {label}")
        dialog.geometry("750x600")
        dialog.minsize(600, 450)  # Allow resize
        dialog.configure(bg=self.colors['bg_primary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        title_frame = tk.Frame(dialog, bg=self.colors['bg_card'], pady=16)
        title_frame.pack(fill=tk.X)
        tk.Label(
            title_frame, 
            text=f"🗑️ Select {label} to Delete",
            bg=self.colors['bg_card'],
            fg=self.colors['danger'],
            font=('Segoe UI', 14, 'bold')
        ).pack()
        
        # Info label
        tk.Label(
            dialog,
            text=f"✓ Check items below to delete • Total available: {len(storage)} items",
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 10, 'bold')
        ).pack(pady=8)
        
        # Selection frame with scrollbar
        list_frame = tk.Frame(dialog, bg=self.colors['bg_primary'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=12)
        
        # Canvas for scrollable checkboxes
        canvas = tk.Canvas(list_frame, bg=self.colors['bg_secondary'], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_secondary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=690)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create checkbuttons for each item with stronger colors
        check_vars = []
        for i, item in enumerate(storage):
            var = tk.BooleanVar(value=False)
            check_vars.append(var)
            
            # Helper to get values from dict or dataclass
            def gv(obj, dk, attr, default='N/A'):
                if isinstance(obj, dict):
                    return obj.get(dk, default)
                return getattr(obj, attr, default)
            
            # Create item display text
            if data_type == 'rooms':
                name = gv(item, 'name', 'name')
                area = gv(item, 'area', 'area', 0.0)
                text = f"[{i+1}] {name} • {area:.2f} m²"
            elif data_type == 'doors':
                name = gv(item, 'name', 'name')
                typ = gv(item, 'type', 'material_type')
                w = gv(item, 'w', 'width', 0.0)
                h = gv(item, 'h', 'height', 0.0)
                text = f"[{i+1}] {name} • {typ} • {w:.2f}×{h:.2f} m"
            elif data_type == 'windows':
                name = gv(item, 'name', 'name')
                typ = gv(item, 'type', 'material_type')
                w = gv(item, 'w', 'width', 0.0)
                h = gv(item, 'h', 'height', 0.0)
                text = f"[{i+1}] {name} • {typ} • {w:.2f}×{h:.2f} m"
            else:  # walls
                name = gv(item, 'name', 'name')
                length = gv(item, 'length', 'length', 0.0)
                height = gv(item, 'height', 'height', 0.0)
                text = f"[{i+1}] {name} • {length:.2f}×{height:.2f} m"
            
            # Create row frame for better layout
            row = tk.Frame(scrollable_frame, bg=self.colors['bg_card'], pady=6, padx=12)
            row.pack(fill=tk.X, padx=8, pady=3)
            
            cb = tk.Checkbutton(
                row,
                text=text,
                variable=var,
                bg=self.colors['bg_card'],
                fg=self.colors['text_primary'],
                selectcolor=self.colors['bg_secondary'],
                activebackground=self.colors['bg_card'],
                activeforeground=self.colors['accent'],
                font=('Segoe UI', 10, 'bold'),
                anchor='w',
                relief=tk.FLAT
            )
            cb.pack(fill=tk.X, expand=True)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        # Mouse wheel for canvas with cleanup
        def on_wheel(e):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(e.delta/120)), "units")
            except:
                pass
        canvas.bind_all("<MouseWheel>", on_wheel)
        
        # Button frame
        btn_frame = tk.Frame(dialog, bg=self.colors['bg_primary'], pady=12)
        btn_frame.pack(fill=tk.X, padx=24)
        
        # Count label
        count_var = tk.StringVar(value="Selected: 0 items")
        count_label = tk.Label(
            btn_frame,
            textvariable=count_var,
            bg=self.colors['bg_primary'],
            fg=self.colors['accent'],
            font=('Segoe UI', 11, 'bold')
        )
        count_label.pack(side=tk.LEFT, padx=8)
        
        def update_count():
            selected = sum(1 for v in check_vars if v.get())
            count_var.set(f"Selected: {selected} items")
        
        def select_all():
            for var in check_vars:
                var.set(True)
            update_count()
        
        def deselect_all():
            for var in check_vars:
                var.set(False)
            update_count()
        
        def delete_selected():
            to_delete = [i for i, var in enumerate(check_vars) if var.get()]
            
            if not to_delete:
                messagebox.showwarning("⚠️ No Selection", "Please select at least one item to delete!")
                return
            
            count = len(to_delete)
            if not messagebox.askyesno("🗑️ Confirm Deletion", f"Permanently delete {count} selected {label.lower()}?"):
                return
            
            for i in reversed(to_delete):
                if data_type in ['doors', 'windows']:
                    opening_name = self._opening_name(storage[i])
                    self._unlink_opening_from_all_rooms(opening_name)
                del storage[i]
            
            if data_type == 'rooms':
                self.refresh_rooms()
            elif data_type in ['doors', 'windows']:
                self.refresh_openings()
            elif data_type == 'walls':
                self.refresh_walls()
            
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()
            
            icons = {'rooms': '🏠', 'doors': '🚪', 'windows': '🪟', 'walls': '🧱'}
            self.update_status(f"Deleted {count} {label.lower()}", icon=icons.get(data_type, '🗑️'))
            messagebox.showinfo("✓ Success", f"Successfully deleted {count} {label.lower()}!")
        
        def cancel():
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()
        
        # Update count when checkboxes change
        for var in check_vars:
            var.trace_add('write', lambda *args: update_count())
        
        # Action buttons
        btn_container = tk.Frame(btn_frame, bg=self.colors['bg_primary'])
        btn_container.pack(side=tk.RIGHT)
        
        tk.Button(
            btn_container, text="✓ Select All", command=select_all,
            bg=self.colors['accent'], fg=self.colors['bg_primary'],
            font=('Segoe UI', 10, 'bold'), relief=tk.FLAT, padx=16, pady=8
        ).pack(side=tk.LEFT, padx=4)
        
        tk.Button(
            btn_container, text="✗ Deselect All", command=deselect_all,
            bg=self.colors['text_secondary'], fg=self.colors['text_primary'],
            font=('Segoe UI', 10), relief=tk.FLAT, padx=16, pady=8
        ).pack(side=tk.LEFT, padx=4)
        
        tk.Button(
            btn_container, text="🗑️ Delete Selected", command=delete_selected,
            bg=self.colors['danger'], fg='#ffffff',
            font=('Segoe UI', 10, 'bold'), relief=tk.FLAT, padx=16, pady=8
        ).pack(side=tk.LEFT, padx=4)
        
        tk.Button(
            btn_container, text="Cancel", command=cancel,
            bg=self.colors['bg_card'], fg=self.colors['text_primary'],
            font=('Segoe UI', 10), relief=tk.FLAT, padx=16, pady=8
        ).pack(side=tk.LEFT, padx=4)
    
    def reset_all(self):
        """Reset all data"""
        if messagebox.askyesno("Reset", "Clear ALL data?"):
            self.project = Project() # Reset with a new Project instance
            self._sync_project_references()
            self._rebuild_association()
            
            self.refresh_rooms()
            self.refresh_openings()
            self.refresh_walls()
            self.refresh_finishes_tab()
            self.refresh_materials_tab()
            if hasattr(self, 'summary_tab'):
                self.summary_tab.refresh_data()
            self.update_status("All data cleared", icon="🧹")
            self.material_costs.clear()
            if hasattr(self, 'costs_tab'):
                self.costs_tab.refresh_data()

    # === EXPORT FUNCTIONS ===================================================

    def _ask_save_path(self, default_name, file_type):
        """Helper to ask for save path."""
        from tkinter import filedialog
        import os
        
        filetypes = []
        if file_type == 'excel':
            filetypes = [("Excel files", "*.xlsx"), ("All files", "*.*")]
            ext = ".xlsx"
        elif file_type == 'pdf':
            filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
            ext = ".pdf"
        elif file_type == 'csv':
            filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
            ext = ".csv"
        else:
            filetypes = [("All files", "*.*")]
            ext = ""
            
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=filetypes,
            initialfile=default_name,
            title=f"Save {file_type.upper()} Report"
        )
        return path

    def export_csv(self):
        """Wrapper to call the CSV export function."""
        export_to_csv(
            project=self.project,
            fmt_func=self._fmt,
            status_callback=self.update_status
        )

    def export_excel(self):
        """Export comprehensive quantity book."""
        if not self.project.rooms:
            messagebox.showinfo("لا توجد غرف", "أضف الغرف أولاً قبل التصدير.")
            return
        
        # Use the comprehensive book export
        export_comprehensive_book(
            project=self.project,
            filepath=None,  # Will prompt for file path inside function
            app=self,
            status_cb=self.update_status
        )

    def export_pdf(self):
        """Wrapper to call the PDF export function."""
        if not hasattr(self, 'costs_tab'):
            messagebox.showerror("Error", "Costs tab is not available.")
            return

        export_to_pdf(
            project=self.project,
            fmt_func=self._fmt,
            calculate_cost_func=self.costs_tab.calculate_total_cost,
            colors_dict=self.colors,
            status_callback=self.update_status
        )

    def insert_table_to_autocad(self):
        """Wrapper to call the AutoCAD table insertion function."""
        if not self.ensure_autocad():
            return
        insert_table_to_autocad(
            project=self.project,
            acad=self.acad,
            doc=self.doc,
            scale=self.scale,
            root_window=self.root,
            status_callback=self.update_status
        )

    def toggle_sync(self):
        """Toggle AutoCAD sync feature (placeholder for future implementation)."""
        messagebox.showinfo(
            "Sync Feature",
            "AutoCAD sync feature is currently under development.\n\n"
            "This will allow real-time synchronization with AutoCAD changes."
        )
        self.update_status("Sync feature coming soon", icon="📡")

if __name__ == "__main__":
    print("Starting BILIND Enhanced...")
    try:
        root = tk.Tk()
        app = BilindEnhanced(root)
        root.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")
