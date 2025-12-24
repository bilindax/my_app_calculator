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
        
        ttk.Label(
            row1,
            text="  (Used when picking walls from AutoCAD)",
            foreground=self.app.colors['text_muted'],
            style='Caption.TLabel'
        ).pack(side=tk.LEFT)

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
            min_opening = self.min_opening_var.get()
            plaster_waste = self.plaster_waste_var.get()
            paint_waste = self.paint_waste_var.get()
            tiles_waste = self.tiles_waste_var.get()
            precision = self.precision_var.get()
            precision_area = self.precision_area_var.get()
            precision_length = self.precision_length_var.get()
            precision_weight = self.precision_weight_var.get()
            precision_cost = self.precision_cost_var.get()
            
            # Apply to project
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
            
            self._save_settings()
    
    def refresh_data(self):
        """Refresh settings from project (called when tab is shown)."""
        if hasattr(self, 'wall_height_var'):
            self.wall_height_var.set(self.app.project.default_wall_height)
            self.min_opening_var.set(self.app.project.min_opening_deduction_area)
            self.plaster_waste_var.set(self.app.project.plaster_waste_percentage)
            self.paint_waste_var.set(self.app.project.paint_waste_percentage)
            self.tiles_waste_var.set(self.app.project.tiles_waste_percentage)
            self.precision_var.set(self.app.project.decimal_precision)
            self.precision_area_var.set(self.app.project.decimal_precision_area)
            self.precision_length_var.set(self.app.project.decimal_precision_length)
            self.precision_weight_var.set(self.app.project.decimal_precision_weight)
            self.precision_cost_var.set(self.app.project.decimal_precision_cost)
