"""
Settings Tab Module - Project calculation settings and preferences.

This module provides the UI for the Settings tab, allowing users to:
- Configure default wall height
- Set minimum opening size for deductions
- Define waste percentages for different finishes
- Adjust decimal precision for display
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

from .base_tab import BaseTab

if TYPE_CHECKING:
    from bilind_main import BilindEnhanced


class SettingsTab(BaseTab):
    """
    Settings tab for project calculation preferences.
    
    Features:
    - Default wall height configuration
    - Minimum opening deduction threshold
    - Waste percentages for plaster/paint/tiles
    - Decimal precision settings
    """
    
    def create(self) -> tk.Frame:
        """
        Create and return the settings tab frame.
        
        Returns:
            tk.Frame: Configured settings tab
        """
        # Main container
        main_frame = tk.Frame(self.parent, bg=self.app.colors['bg_secondary'])
        
        # Scrollable canvas
        canvas = tk.Canvas(main_frame, bg=self.app.colors['bg_secondary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        
        # Inner scrollable frame
        container = ttk.Frame(canvas, style='Main.TFrame')
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create window item
        window_item = canvas.create_window((0, 0), window=container, anchor='nw')
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        def on_canvas_configure(event):
            # Adjust width to fit canvas (minus scrollbar width if needed, but usually full width works)
            canvas.itemconfig(window_item, width=event.width)
            
        container.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        # Header
        self._create_header(container)
        
        # Settings sections
        self._create_calculation_settings(container)
        self._create_waste_settings(container)
        self._create_display_settings(container)
        self._create_theme_settings(container)
        
        # Action buttons
        self._create_action_buttons(container)
        
        return main_frame
    
    def _create_header(self, parent):
        """Create styled header section."""
        hero = ttk.Frame(parent, style='Hero.TFrame', padding=(18, 20))
        hero.pack(fill=tk.X, padx=16, pady=(16, 12))
        
        ttk.Label(
            hero,
            text="⚙️ Project Settings",
            style='HeroHeading.TLabel'
        ).pack(anchor=tk.W)
        
        ttk.Label(
            hero,
            text="Configure calculation rules, waste factors, and display preferences for this project.",
            style='HeroSubheading.TLabel'
        ).pack(anchor=tk.W, pady=(6, 0))
    
    def _create_calculation_settings(self, parent):
        """Create calculation settings section."""
        section = ttk.LabelFrame(
            parent,
            text="Calculation Settings",
            style='Card.TLabelframe',
            padding=(16, 12)
        )
        section.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        # Default wall height
        row1 = ttk.Frame(section, style='Main.TFrame')
        row1.pack(fill=tk.X, pady=6)
        
        ttk.Label(
            row1,
            text="Default Wall Height (m):",
            style='Body.TLabel'
        ).pack(side=tk.LEFT, padx=(0, 12))
        
        self.wall_height_var = tk.DoubleVar(value=self.app.project.default_wall_height)
        height_spin = ttk.Spinbox(
            row1,
            from_=2.0,
            to=6.0,
            increment=0.1,
            textvariable=self.wall_height_var,
            width=10
        )
        height_spin.pack(side=tk.LEFT)

        def apply_default_height_to_all_rooms():
            try:
                h = float(self.wall_height_var.get())
            except Exception:
                messagebox.showerror("Invalid Input", "Please enter a valid wall height.")
                return
            if h <= 0:
                messagebox.showerror("Invalid Input", "Wall height must be positive.")
                return

            if not messagebox.askyesno(
                "Apply to All Rooms",
                f"Apply wall height = {h:.2f} m to ALL rooms in this project?\n\n"
                "This will update room wall height and any per-room wall objects, then recalculate."
            ):
                return

            updated = 0
            for room in (self.app.project.rooms or []):
                try:
                    if isinstance(room, dict):
                        room['wall_height'] = h
                        room['wall_segments'] = []
                        walls = room.get('walls') or []
                    else:
                        setattr(room, 'wall_height', h)
                        setattr(room, 'wall_segments', [])
                        walls = getattr(room, 'walls', []) or []

                    for w in walls:
                        try:
                            if isinstance(w, dict):
                                w['height'] = h
                            else:
                                setattr(w, 'height', h)
                        except Exception:
                            continue

                    updated += 1
                except Exception:
                    continue

            # Recalculate using the app if available
            try:
                if hasattr(self.app, 'auto_calculate_all_rooms'):
                    self.app.auto_calculate_all_rooms()
            except Exception:
                pass

            if hasattr(self.app, 'refresh_all_tabs'):
                self.app.refresh_all_tabs()

            self.app.update_status(f"Applied wall height to {updated} room(s)", icon="✅")

        self.create_button(
            row1,
            "Apply to All Rooms",
            apply_default_height_to_all_rooms,
            'Secondary.TButton'
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Label(
            row1,
            text="  (Used when picking walls from AutoCAD)",
            foreground=self.app.colors['text_muted'],
            style='Caption.TLabel'
        ).pack(side=tk.LEFT)

        # Drawing scale factor (AutoCAD units -> meters)
        row_scale = ttk.Frame(section, style='Main.TFrame')
        row_scale.pack(fill=tk.X, pady=(12, 6))

        ttk.Label(
            row_scale,
            text="Drawing Scale Factor:",
            style='Body.TLabel'
        ).pack(side=tk.LEFT, padx=(0, 12))

        # This is the factor used by pickers: meters = drawing_units * scale
        self.scale_var = tk.DoubleVar(value=float(getattr(self.app.project, 'scale', 1.0) or 1.0))
        scale_entry = ttk.Entry(row_scale, textvariable=self.scale_var, width=12)
        scale_entry.pack(side=tk.LEFT)

        ttk.Label(
            row_scale,
            text="(meters = AutoCAD units × factor)",
            foreground=self.app.colors['text_muted'],
            style='Caption.TLabel'
        ).pack(side=tk.LEFT, padx=(10, 0))

        row_scale2 = ttk.Frame(section, style='Main.TFrame')
        row_scale2.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(row_scale2, text="Quick preset:", style='Body.TLabel').pack(side=tk.LEFT, padx=(0, 12))
        presets = [
            ("Meters (m)", 1.0),
            ("Centimeters (cm)", 0.01),
            ("Millimeters (mm)", 0.001),
            ("1:50", 0.02),
            ("1:100", 0.01),
            ("1:200", 0.005),
        ]
        preset_map = {name: val for name, val in presets}
        self._scale_preset_var = tk.StringVar(value="Meters (m)")
        preset_combo = ttk.Combobox(
            row_scale2,
            textvariable=self._scale_preset_var,
            values=[name for name, _ in presets],
            width=18,
            state='readonly'
        )
        preset_combo.pack(side=tk.LEFT)

        def _apply_preset(event=None):
            try:
                name = self._scale_preset_var.get()
                val = float(preset_map.get(name, 1.0))
                self.scale_var.set(val)
            except Exception:
                pass

        preset_combo.bind('<<ComboboxSelected>>', _apply_preset)

        def apply_scale_only():
            try:
                new_scale = float(self.scale_var.get())
            except Exception:
                messagebox.showerror("Invalid Input", "Please enter a valid scale factor.")
                return
            if new_scale <= 0:
                messagebox.showerror("Invalid Input", "Scale factor must be positive.")
                return
            self.app.project.scale = new_scale
            self.app.scale = new_scale
            self.app.update_status(f"Scale factor set to {new_scale:g}", icon="📐")
            if hasattr(self.app, 'refresh_all_tabs'):
                self.app.refresh_all_tabs()

        def fix_existing_measurements():
            """Rescale already-imported geometry by asking user about source/target units."""
            # Create dialog to ask about source and target units
            fix_dialog = tk.Toplevel(self.parent)
            fix_dialog.title("Fix Scale - تصحيح المقياس")
            dialog_w, dialog_h = 650, 540
            fix_dialog.geometry(f"{dialog_w}x{dialog_h}")
            fix_dialog.configure(bg=self.app.colors['bg_secondary'])
            fix_dialog.transient(self.parent)
            fix_dialog.grab_set()
            fix_dialog.minsize(620, 500)
            fix_dialog.resizable(True, True)

            # Center dialog
            fix_dialog.update_idletasks()
            try:
                x = self.parent.winfo_rootx() + (self.parent.winfo_width() - dialog_w) // 2
                y = self.parent.winfo_rooty() + (self.parent.winfo_height() - dialog_h) // 2
                fix_dialog.geometry(f"+{x}+{y}")
            except:
                pass

            result = {'proceed': False, 'factor': 1.0}

            # Header
            header = ttk.Frame(fix_dialog, style='Main.TFrame', padding=(20, 15))
            header.pack(fill=tk.X)
            ttk.Label(
                header,
                text="🔧 Fix Existing Measurements",
                font=('Segoe UI Semibold', 14),
                foreground=self.app.colors['accent']
            ).pack(anchor=tk.W)
            ttk.Label(
                header,
                text="Convert imported data from one unit to another",
                foreground=self.app.colors['text_secondary']
            ).pack(anchor=tk.W, pady=(4, 0))

            # Buttons first (at bottom)
            btn_frame = ttk.Frame(fix_dialog, style='Main.TFrame', padding=(20, 15))
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            # Content
            content = ttk.Frame(fix_dialog, style='Main.TFrame', padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Example box
            example_frame = ttk.LabelFrame(content, text="مثال - Example", padding=12)
            example_frame.pack(fill=tk.X, pady=(0, 15))
            ttk.Label(
                example_frame,
                text="If 120cm shows as 120m, choose:\n"
                     "  Current data: Centimeters (cm)\n"
                     "  Convert to: Meters (m)",
                foreground=self.app.colors['text_secondary'],
                justify=tk.LEFT
            ).pack(anchor=tk.W)

            # Unit presets
            unit_presets = [
                ("Meters (m) - أمتار", 1.0),
                ("Centimeters (cm) - سنتيمتر", 0.01),
                ("Millimeters (mm) - ملليمتر", 0.001),
                ("Scale 1:50 - مقياس", 0.02),
                ("Scale 1:100 - مقياس", 0.01),
                ("Scale 1:200 - مقياس", 0.005),
            ]
            unit_map = {name: val for name, val in unit_presets}

            # Source units
            ttk.Label(
                content,
                text="Current data is in:",
                font=('Segoe UI', 10, 'bold'),
                foreground=self.app.colors['text_primary']
            ).pack(anchor=tk.W, pady=(5, 5))
            source_var = tk.StringVar(value="Meters (m) - أمتار")
            source_combo = ttk.Combobox(
                content,
                textvariable=source_var,
                values=[name for name, _ in unit_presets],
                width=35,
                state='readonly'
            )
            source_combo.pack(fill=tk.X, pady=(0, 15))

            # Target units
            ttk.Label(
                content,
                text="Convert to:",
                font=('Segoe UI', 10, 'bold'),
                foreground=self.app.colors['text_primary']
            ).pack(anchor=tk.W, pady=(5, 5))
            target_var = tk.StringVar(value="Centimeters (cm) - سنتيمتر")
            target_combo = ttk.Combobox(
                content,
                textvariable=target_var,
                values=[name for name, _ in unit_presets],
                width=35,
                state='readonly'
            )
            target_combo.pack(fill=tk.X, pady=(0, 15))

            # Preview frame
            preview_frame = ttk.LabelFrame(content, text="Preview - معاينة", padding=12)
            preview_frame.pack(fill=tk.X, pady=(0, 15))
            
            preview_label = ttk.Label(
                preview_frame,
                text="Factor: ×1.0\nExample: 120 → 120",
                foreground=self.app.colors['accent'],
                font=('Segoe UI', 9)
            )
            preview_label.pack(anchor=tk.W)

            def update_preview(*args):
                try:
                    source = unit_map.get(source_var.get(), 1.0)
                    target = unit_map.get(target_var.get(), 1.0)
                    factor = target / source
                    preview_label.config(
                        text=f"Factor: ×{factor:g}\n"
                             f"Example: 120 → {120 * factor:g}"
                    )
                except:
                    pass

            source_var.trace_add('write', update_preview)
            target_var.trace_add('write', update_preview)
            update_preview()

            # Define button actions before creating buttons
            def proceed():
                try:
                    source = float(unit_map.get(source_var.get(), 1.0))
                    target = float(unit_map.get(target_var.get(), 1.0))
                    factor = target / source
                    if abs(factor - 1.0) < 1e-9:
                        messagebox.showinfo("No Change", "Source and target are the same; nothing to convert.", parent=fix_dialog)
                        return
                    result['factor'] = factor
                    result['proceed'] = True
                    fix_dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Invalid conversion: {e}", parent=fix_dialog)

            # Create buttons in the frame we packed earlier
            self.create_button(btn_frame, "✅ Convert", proceed, 'Accent.TButton').pack(side=tk.RIGHT, padx=(10, 0))
            self.create_button(btn_frame, "❌ Cancel", fix_dialog.destroy, 'Secondary.TButton').pack(side=tk.RIGHT)

            fix_dialog.wait_window()

            if not result['proceed']:
                return

            factor = result['factor']

            def _scale_linear(val):
                try:
                    return float(val) * factor
                except Exception:
                    return val

            def _scale_area(val):
                try:
                    return float(val) * (factor * factor)
                except Exception:
                    return val

            # Rooms
            for room in (self.app.project.rooms or []):
                try:
                    if isinstance(room, dict):
                        for k in ('w', 'l', 'perim'):
                            if k in room and room[k] is not None:
                                room[k] = _scale_linear(room[k])
                        for k in ('area', 'ceiling_finish_area', 'wall_finish_area', 'ceramic_area'):
                            if k in room and room[k] is not None:
                                room[k] = _scale_area(room[k])

                        # Balcony segments: length is linear, height is meters (leave as-is)
                        segs = room.get('wall_segments') or []
                        for seg in segs:
                            if isinstance(seg, dict) and 'length' in seg and seg.get('length') is not None:
                                seg['length'] = _scale_linear(seg.get('length'))
                        # Explicit walls
                        walls = room.get('walls') or []
                        for w in walls:
                            if isinstance(w, dict) and 'length' in w and w.get('length') is not None:
                                w['length'] = _scale_linear(w.get('length'))
                    else:
                        for attr in ('width', 'length', 'perimeter'):
                            if hasattr(room, attr) and getattr(room, attr) is not None:
                                setattr(room, attr, _scale_linear(getattr(room, attr)))
                        for attr in ('area', 'ceiling_finish_area', 'wall_finish_area', 'ceramic_area'):
                            if hasattr(room, attr) and getattr(room, attr) is not None:
                                setattr(room, attr, _scale_area(getattr(room, attr)))

                        for seg in getattr(room, 'wall_segments', []) or []:
                            if isinstance(seg, dict) and seg.get('length') is not None:
                                seg['length'] = _scale_linear(seg.get('length'))

                        for w in getattr(room, 'walls', []) or []:
                            try:
                                if isinstance(w, dict):
                                    if w.get('length') is not None:
                                        w['length'] = _scale_linear(w.get('length'))
                                else:
                                    if getattr(w, 'length', None) is not None:
                                        w.length = _scale_linear(w.length)
                                        # Refresh areas
                                        if getattr(w, 'gross_area', None) is not None:
                                            w.gross_area = w.length * float(getattr(w, 'height', 0.0) or 0.0)
                                        if getattr(w, 'net_area', None) is not None:
                                            w.net_area = max(0.0, float(w.gross_area or 0.0) - float(getattr(w, 'deduction_area', 0.0) or 0.0))
                                        if hasattr(w, '_normalize_ceramic_segment'):
                                            w._normalize_ceramic_segment()
                            except Exception:
                                continue
                except Exception:
                    continue

            # Project walls list
            for wall in (self.app.project.walls or []):
                try:
                    if isinstance(wall, dict):
                        if wall.get('length') is not None:
                            wall['length'] = _scale_linear(wall.get('length'))
                        # Refresh areas if present
                        try:
                            h = float(wall.get('height', 0.0) or 0.0)
                            ln = float(wall.get('length', 0.0) or 0.0)
                            wall['gross_area'] = ln * h
                            ded = float(wall.get('deduction_area', 0.0) or 0.0)
                            wall['net_area'] = max(0.0, wall['gross_area'] - ded)
                        except Exception:
                            pass
                    else:
                        if getattr(wall, 'length', None) is not None:
                            wall.length = _scale_linear(wall.length)
                            wall.gross_area = wall.length * float(getattr(wall, 'height', 0.0) or 0.0)
                            wall.net_area = max(0.0, float(wall.gross_area or 0.0) - float(getattr(wall, 'deduction_area', 0.0) or 0.0))
                            if hasattr(wall, '_normalize_ceramic_segment'):
                                wall._normalize_ceramic_segment()
                except Exception:
                    continue

            # Openings (doors/windows)
            def _fix_openings(collection):
                for op in (collection or []):
                    try:
                        if isinstance(op, dict):
                            for k in ('w', 'h', 'width', 'height'):
                                if k in op and op[k] is not None:
                                    op[k] = _scale_linear(op[k])

                            # Placement height: only scale if it looks like it's in cm/mm (heuristic)
                            ph = op.get('placement_height', None)
                            try:
                                ph_f = float(ph) if ph is not None else None
                                if ph_f is not None and ph_f > 10:
                                    op['placement_height'] = _scale_linear(ph_f)
                            except Exception:
                                pass

                            qty = int(op.get('qty', op.get('quantity', 1)) or 1)
                            wv = float(op.get('w', op.get('width', 0.0)) or 0.0)
                            hv = float(op.get('h', op.get('height', 0.0)) or 0.0)
                            op['perim_each'] = 2 * (wv + hv)
                            op['perim'] = op['perim_each'] * qty
                            op['area_each'] = wv * hv
                            op['area'] = op['area_each'] * qty
                            op['stone'] = op['perim']
                            if str(op.get('opening_type', '')).upper() == 'WINDOW':
                                op['glass_each'] = op['area_each'] * 0.85
                                op['glass'] = op['glass_each'] * qty
                        else:
                            if getattr(op, 'width', None) is not None:
                                op.width = _scale_linear(op.width)
                            if getattr(op, 'height', None) is not None:
                                op.height = _scale_linear(op.height)
                            try:
                                ph = getattr(op, 'placement_height', None)
                                if ph is not None and float(ph) > 10:
                                    op.placement_height = _scale_linear(ph)
                            except Exception:
                                pass
                    except Exception:
                        continue

            _fix_openings(getattr(self.app.project, 'doors', []))
            _fix_openings(getattr(self.app.project, 'windows', []))

            # Update scale to target (from the conversion dialog)
            desired_scale = getattr(self.app.project, 'scale', getattr(self.app, 'scale', 1.0))
            try:
                source_scale = float(unit_map.get(source_var.get(), 1.0))
                target_scale = float(unit_map.get(target_var.get(), 1.0))
                self.app.project.scale = target_scale
                self.app.scale = target_scale
                self.scale_var.set(target_scale)
                desired_scale = target_scale
            except:
                pass

            # Recalculate finishes after geometry update
            try:
                if hasattr(self.app, 'auto_calculate_all_rooms'):
                    self.app.auto_calculate_all_rooms()
            except Exception:
                pass

            if hasattr(self.app, 'refresh_all_tabs'):
                self.app.refresh_all_tabs()
            self.app.update_status(f"Fixed measurements (×{factor:g}); scale={desired_scale:g}", icon="✅")

        self.create_button(row_scale2, "Apply", apply_scale_only, 'Secondary.TButton').pack(side=tk.LEFT, padx=8)
        self.create_button(row_scale2, "Fix Existing", fix_existing_measurements, 'Accent.TButton').pack(side=tk.LEFT, padx=4)

        ttk.Label(
            row_scale2,
            text="Tip: if 120cm appears as 120m, use 0.01",
            foreground=self.app.colors['text_muted'],
            style='Caption.TLabel'
        ).pack(side=tk.LEFT, padx=(12, 0))

    def _create_theme_settings(self, parent):
        """Create theme/density settings section with live apply."""
        section = ttk.LabelFrame(
            parent,
            text="Appearance",
            style='Card.TLabelframe',
            padding=(16, 12)
        )
        section.pack(fill=tk.X, padx=16, pady=(0, 12))

        # ttkbootstrap Theme selector (NEW)
        if hasattr(self.app, 'modern_style') and self.app.modern_style.is_available():
            row0 = ttk.Frame(section, style='Main.TFrame')
            row0.pack(fill=tk.X, pady=(0, 12))
            ttk.Label(row0, text="🎨 Modern Theme:", style='Body.TLabel', font=('Segoe UI Semibold', 10)).pack(side=tk.LEFT, padx=(0, 12))
            
            from bilind.ui.modern_styles import ModernStyleManager
            modern_themes = ModernStyleManager.get_available_themes()
            self._modern_theme_var = tk.StringVar(value=getattr(self.app.modern_style, 'theme_name', 'cyborg'))
            
            modern_combo = ttk.Combobox(row0, textvariable=self._modern_theme_var, values=modern_themes, width=16, state='readonly')
            modern_combo.pack(side=tk.LEFT)
            
            def apply_modern_theme():
                theme = self._modern_theme_var.get()
                self.app.modern_style.set_theme(theme)
                self.app._setup_styles()
                self.app.refresh_all_tabs()
                self.app.update_status(f"Applied modern theme: {theme}", icon="✨")
            
            self.create_button(row0, "✨ Apply", apply_modern_theme, 'Accent.TButton').pack(side=tk.LEFT, padx=8)
            
            # Separator
            ttk.Separator(section, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # Theme selector (existing color palettes)
        row1 = ttk.Frame(section, style='Main.TFrame')
        row1.pack(fill=tk.X, pady=6)
        ttk.Label(row1, text="Color Palette:", style='Body.TLabel').pack(side=tk.LEFT, padx=(0, 12))
        themes = getattr(self.app.theme, 'available', lambda: ['neo'])()
        self._theme_var = tk.StringVar(value=getattr(self.app.theme, 'name', 'neo'))
        theme_combo = ttk.Combobox(row1, textvariable=self._theme_var, values=themes, width=14, state='readonly')
        theme_combo.pack(side=tk.LEFT)
        self.create_button(row1, "Apply", lambda: self.app.apply_theme(self._theme_var.get()), 'Secondary.TButton').pack(side=tk.LEFT, padx=8)
        
        # Minimum opening size
        row2 = ttk.Frame(section, style='Main.TFrame')
        row2.pack(fill=tk.X, pady=6)
        
        ttk.Label(
            row2,
            text="Min Opening for Deduction (m²):",
            style='Body.TLabel'
        ).pack(side=tk.LEFT, padx=(0, 12))
        
        self.min_opening_var = tk.DoubleVar(value=self.app.project.min_opening_deduction_area)
        min_spin = ttk.Spinbox(
            row2,
            from_=0.0,
            to=2.0,
            increment=0.1,
            textvariable=self.min_opening_var,
            width=10
        )
        min_spin.pack(side=tk.LEFT)
        
        ttk.Label(
            row2,
            text="  (Don't deduct openings smaller than this)",
            foreground=self.app.colors['text_muted'],
            style='Caption.TLabel'
        ).pack(side=tk.LEFT)
    
    def _create_waste_settings(self, parent):
        """Create waste percentage settings section."""
        section = ttk.LabelFrame(
            parent,
            text="Waste Percentages",
            style='Card.TLabelframe',
            padding=(16, 12)
        )
        section.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        ttk.Label(
            section,
            text="Set waste factors for finish materials (added to net areas):",
            foreground=self.app.colors['text_secondary'],
            style='Caption.TLabel'
        ).pack(anchor=tk.W, pady=(0, 12))
        
        # Plaster waste
        row1 = ttk.Frame(section, style='Main.TFrame')
        row1.pack(fill=tk.X, pady=6)
        
        ttk.Label(row1, text="Plaster:", width=15, style='Body.TLabel').pack(side=tk.LEFT)
        self.plaster_waste_var = tk.DoubleVar(value=self.app.project.plaster_waste_percentage)
        ttk.Spinbox(
            row1,
            from_=0.0,
            to=30.0,
            increment=1.0,
            textvariable=self.plaster_waste_var,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(row1, text="%", style='Body.TLabel').pack(side=tk.LEFT)
        
        # Paint waste
        row2 = ttk.Frame(section, style='Main.TFrame')
        row2.pack(fill=tk.X, pady=6)
        
        ttk.Label(row2, text="Paint:", width=15, style='Body.TLabel').pack(side=tk.LEFT)
        self.paint_waste_var = tk.DoubleVar(value=self.app.project.paint_waste_percentage)
        ttk.Spinbox(
            row2,
            from_=0.0,
            to=30.0,
            increment=1.0,
            textvariable=self.paint_waste_var,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(row2, text="%", style='Body.TLabel').pack(side=tk.LEFT)
        
        # Tiles waste
        row3 = ttk.Frame(section, style='Main.TFrame')
        row3.pack(fill=tk.X, pady=6)
        
        ttk.Label(row3, text="Tiles:", width=15, style='Body.TLabel').pack(side=tk.LEFT)
        self.tiles_waste_var = tk.DoubleVar(value=self.app.project.tiles_waste_percentage)
        ttk.Spinbox(
            row3,
            from_=0.0,
            to=30.0,
            increment=1.0,
            textvariable=self.tiles_waste_var,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(row3, text="%", style='Body.TLabel').pack(side=tk.LEFT)
    
    def _create_display_settings(self, parent):
        """Create display settings section with granular precision controls."""
        section = ttk.LabelFrame(
            parent,
            text="Display Settings",
            style='Card.TLabelframe',
            padding=(16, 12)
        )
        section.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        ttk.Label(
            section,
            text="Configure decimal precision for different measurement types:",
            foreground=self.app.colors['text_secondary'],
            style='Caption.TLabel'
        ).pack(anchor=tk.W, pady=(0, 12))

        # Thousands separator toggle
        row_sep = ttk.Frame(section, style='Main.TFrame')
        row_sep.pack(fill=tk.X, pady=(0, 10))
        self.thousands_sep_var = tk.BooleanVar(value=bool(getattr(self.app.project, 'use_thousands_separator', False)))
        ttk.Checkbutton(
            row_sep,
            text="Use thousands separator (e.g., 1,234.56)",
            variable=self.thousands_sep_var,
            style='Switch.TCheckbutton'
        ).pack(side=tk.LEFT)
        
        # General/Legacy precision (kept for backward compatibility)
        row0 = ttk.Frame(section, style='Main.TFrame')
        row0.pack(fill=tk.X, pady=6)
        
        ttk.Label(row0, text="General:", width=15, style='Body.TLabel').pack(side=tk.LEFT)
        self.precision_var = tk.IntVar(value=self.app.project.decimal_precision)
        ttk.Spinbox(
            row0,
            from_=0,
            to=4,
            increment=1,
            textvariable=self.precision_var,
            width=6
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(
            row0,
            text="decimal places (legacy/general)",
            foreground=self.app.colors['text_muted'],
            style='Caption.TLabel'
        ).pack(side=tk.LEFT)
        
        # Area precision
        row1 = ttk.Frame(section, style='Main.TFrame')
        row1.pack(fill=tk.X, pady=6)
        
        ttk.Label(row1, text="Areas (m²):", width=15, style='Body.TLabel').pack(side=tk.LEFT)
        self.precision_area_var = tk.IntVar(value=self.app.project.decimal_precision_area)
        ttk.Spinbox(
            row1,
            from_=0,
            to=4,
            increment=1,
            textvariable=self.precision_area_var,
            width=6
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(
            row1,
            text="decimal places",
            foreground=self.app.colors['text_muted'],
            style='Caption.TLabel'
        ).pack(side=tk.LEFT)
        
        # Length precision
        row2 = ttk.Frame(section, style='Main.TFrame')
        row2.pack(fill=tk.X, pady=6)
        
        ttk.Label(row2, text="Lengths (m):", width=15, style='Body.TLabel').pack(side=tk.LEFT)
        self.precision_length_var = tk.IntVar(value=self.app.project.decimal_precision_length)
        ttk.Spinbox(
            row2,
            from_=0,
            to=4,
            increment=1,
            textvariable=self.precision_length_var,
            width=6
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(
            row2,
            text="decimal places",
            foreground=self.app.colors['text_muted'],
            style='Caption.TLabel'
        ).pack(side=tk.LEFT)
        
        # Weight precision
        row3 = ttk.Frame(section, style='Main.TFrame')
        row3.pack(fill=tk.X, pady=6)
        
        ttk.Label(row3, text="Weights (kg):", width=15, style='Body.TLabel').pack(side=tk.LEFT)
        self.precision_weight_var = tk.IntVar(value=self.app.project.decimal_precision_weight)
        ttk.Spinbox(
            row3,
            from_=0,
            to=4,
            increment=1,
            textvariable=self.precision_weight_var,
            width=6
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(
            row3,
            text="decimal places",
            foreground=self.app.colors['text_muted'],
            style='Caption.TLabel'
        ).pack(side=tk.LEFT)
        
        # Cost precision
        row4 = ttk.Frame(section, style='Main.TFrame')
        row4.pack(fill=tk.X, pady=6)
        
        ttk.Label(row4, text="Costs/Currency:", width=15, style='Body.TLabel').pack(side=tk.LEFT)
        self.precision_cost_var = tk.IntVar(value=self.app.project.decimal_precision_cost)
        ttk.Spinbox(
            row4,
            from_=0,
            to=4,
            increment=1,
            textvariable=self.precision_cost_var,
            width=6
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(
            row4,
            text="decimal places",
            foreground=self.app.colors['text_muted'],
            style='Caption.TLabel'
        ).pack(side=tk.LEFT)
    
    def _create_action_buttons(self, parent):
        """Create action buttons."""
        btn_frame = ttk.Frame(parent, style='Main.TFrame', padding=(16, 12))
        btn_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        self.create_button(btn_frame, "💾 Save Settings", self._save_settings, 'Accent.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(btn_frame, "↺ Reset to Defaults", self._reset_to_defaults, 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
    
    def _save_settings(self):
        """Save settings to project."""
        try:
            # Validate inputs
            wall_height = self.wall_height_var.get()
            scale_factor = self.scale_var.get() if hasattr(self, 'scale_var') else self.app.project.scale
            min_opening = self.min_opening_var.get()
            plaster_waste = self.plaster_waste_var.get()
            paint_waste = self.paint_waste_var.get()
            tiles_waste = self.tiles_waste_var.get()
            precision = self.precision_var.get()
            precision_area = self.precision_area_var.get()
            precision_length = self.precision_length_var.get()
            precision_weight = self.precision_weight_var.get()
            precision_cost = self.precision_cost_var.get()
            use_thousands = bool(self.thousands_sep_var.get()) if hasattr(self, 'thousands_sep_var') else False
            
            # Apply to project
            try:
                scale_factor = float(scale_factor)
                if scale_factor > 0:
                    self.app.project.scale = scale_factor
                    self.app.scale = scale_factor
            except Exception:
                pass
            self.app.project.default_wall_height = wall_height
            self.app.project.min_opening_deduction_area = min_opening
            self.app.project.plaster_waste_percentage = plaster_waste
            self.app.project.paint_waste_percentage = paint_waste
            self.app.project.tiles_waste_percentage = tiles_waste
            self.app.project.decimal_precision = precision
            self.app.project.decimal_precision_area = precision_area
            self.app.project.decimal_precision_length = precision_length
            self.app.project.decimal_precision_weight = precision_weight
            self.app.project.decimal_precision_cost = precision_cost
            self.app.project.use_thousands_separator = use_thousands
            
            # Refresh all tabs to apply new settings
            if hasattr(self.app, 'finishes_tab'):
                self.app.finishes_tab.refresh_data()
            if hasattr(self.app, 'walls_tab'):
                self.app.walls_tab.refresh_data()
            if hasattr(self.app, 'refresh_all_tabs'):
                self.app.refresh_all_tabs()
            
            self.app.update_status("Settings saved successfully", icon="✅")
            messagebox.showinfo(
                "Settings Saved",
                "Project settings have been updated.\n\n"
                "Note: Existing items won't change automatically.\n"
                "Re-pick or recalculate to apply new settings."
            )
            
        except tk.TclError as e:
            messagebox.showerror("Invalid Input", f"Please enter valid numbers: {e}")
    
    def _reset_to_defaults(self):
        """Reset all settings to default values."""
        if messagebox.askyesno(
            "Reset Settings",
            "Reset all settings to default values?\n\n"
            "This will:\n"
            "• Wall Height: 3.0 m\n"
            "• Min Opening: 0.5 m²\n"
            "• Plaster Waste: 5%\n"
            "• Paint Waste: 10%\n"
            "• Tiles Waste: 15%\n"
            "• General Precision: 2\n"
            "• Area Precision: 2\n"
            "• Length Precision: 2\n"
            "• Weight Precision: 1\n"
            "• Cost Precision: 2"
        ):
            self.wall_height_var.set(3.0)
            self.min_opening_var.set(0.5)
            self.plaster_waste_var.set(5.0)
            self.paint_waste_var.set(10.0)
            self.tiles_waste_var.set(15.0)
            self.precision_var.set(2)
            self.precision_area_var.set(2)
            self.precision_length_var.set(2)
            self.precision_weight_var.set(1)
            self.precision_cost_var.set(2)
            if hasattr(self, 'thousands_sep_var'):
                self.thousands_sep_var.set(False)
            
            self._save_settings()
    
    def refresh_data(self):
        """Refresh settings from project (called when tab is shown)."""
        if hasattr(self, 'wall_height_var'):
            self.wall_height_var.set(self.app.project.default_wall_height)
            if hasattr(self, 'scale_var'):
                try:
                    self.scale_var.set(float(getattr(self.app.project, 'scale', 1.0) or 1.0))
                except Exception:
                    self.scale_var.set(1.0)
            self.min_opening_var.set(self.app.project.min_opening_deduction_area)
            self.plaster_waste_var.set(self.app.project.plaster_waste_percentage)
            self.paint_waste_var.set(self.app.project.paint_waste_percentage)
            self.tiles_waste_var.set(self.app.project.tiles_waste_percentage)
            self.precision_var.set(self.app.project.decimal_precision)
            self.precision_area_var.set(self.app.project.decimal_precision_area)
            self.precision_length_var.set(self.app.project.decimal_precision_length)
            self.precision_weight_var.set(self.app.project.decimal_precision_weight)
            self.precision_cost_var.set(self.app.project.decimal_precision_cost)
            if hasattr(self, 'thousands_sep_var'):
                self.thousands_sep_var.set(bool(getattr(self.app.project, 'use_thousands_separator', False)))
