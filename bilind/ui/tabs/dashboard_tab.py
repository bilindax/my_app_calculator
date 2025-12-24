"""
Dashboard Tab Module - Data visualization and charts.

This module provides the UI for the Dashboard tab, allowing users to:
- View interactive charts and visualizations
- Refresh dashboard to update with latest data
- Visualize room area distribution
- Compare wall gross vs net areas
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from .base_tab import BaseTab

if TYPE_CHECKING:
    from ...bilind_main import BilindEnhanced


class DashboardTab(BaseTab):
    """
    Dashboard tab for project visualization.
    
    Features:
    - Interactive charts using matplotlib
    - Room area distribution pie chart
    - Wall gross vs net area bar chart
    - Refresh button to update visualizations
    """
    def __init__(self, parent: tk.Widget, app: 'BilindEnhanced'):
        super().__init__(parent, app)
        self.dashboard_frame = None
        self.dashboard_canvas = None

    def create(self) -> tk.Frame:
        """
        Create and return the dashboard tab frame.
        
        Returns:
            tk.Frame: Configured dashboard tab
        """
        container = tk.Frame(self.parent, bg=self.app.colors['bg_secondary'])
        
        # Header
        self._create_header(
            container,
            "Project Dashboard",
            "Visualize your project's quantities with interactive charts."
        )
        
        # Toolbar
        self._create_toolbar(container)
        
        # Dashboard content area
        self._create_dashboard_area(container)

        self.refresh_data()
        return container
    
    def _create_header(self, parent, title: str, subtitle: str):
        """Create styled header section."""
        hero = ttk.Frame(parent, style='Hero.TFrame', padding=(18, 20))
        hero.pack(fill=tk.X, padx=16, pady=(16, 12))
        
        ttk.Label(
            hero,
            text=title,
            style='HeroHeading.TLabel'
        ).pack(anchor=tk.W)
        
        ttk.Label(
            hero,
            text=subtitle,
            style='HeroSubheading.TLabel'
        ).pack(anchor=tk.W, pady=(6, 0))
    
    def _create_toolbar(self, parent):
        """Create toolbar with refresh button."""
        toolbar = ttk.Frame(parent, style='Toolbar.TFrame', padding=(12, 10))
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        self.create_button(toolbar, "🔄 Refresh Dashboard", self.refresh_data, 'Accent.TButton').pack(side=tk.LEFT, padx=4)
    
    def _create_dashboard_area(self, parent):
        """Create frame for dashboard charts."""
        self.dashboard_frame = ttk.Frame(
            parent,
            style='Main.TFrame',
            padding=(12, 10)
        )
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        
        # Initialize canvas placeholder
        self.dashboard_canvas = None

    def refresh_data(self):
        """Refreshes the charts on the dashboard tab."""
        if not self.dashboard_frame:
            return

        # Clear previous charts
        if self.dashboard_canvas:
            self.dashboard_canvas.get_tk_widget().destroy()

        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            ttk.Label(self.dashboard_frame, text="Matplotlib not installed. Please run 'pip install matplotlib'.", style='Caption.TLabel').pack()
            return

        if not self.app.project.rooms:
            # Clear any existing message and show the new one
            for widget in self.dashboard_frame.winfo_children():
                widget.destroy()
            ttk.Label(self.dashboard_frame, text="No room data to display. Pick some rooms first.", style='Caption.TLabel').pack()
            return

        fig = Figure(figsize=(10, 6), dpi=100, facecolor=self.app.colors['bg_secondary'])
        fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.3, hspace=0.4)

        # Chart 1: Room Area Distribution
        ax1 = fig.add_subplot(1, 2, 1)
        def _rname(r):
            return r.get('name', 'Room') if isinstance(r, dict) else getattr(r, 'name', 'Room')
        def _rarea(r):
            return float(r.get('area', 0.0) or 0.0) if isinstance(r, dict) else float(getattr(r, 'area', 0.0) or 0.0)
        room_names = [_rname(r) for r in self.app.project.rooms]
        room_areas = [_rarea(r) for r in self.app.project.rooms]
        # Filter out zero-area entries to avoid matplotlib warnings
        filtered = [(n, a) for n, a in zip(room_names, room_areas) if a > 0]
        if not filtered:
            filtered = [("No room data", 1.0)]
        room_names, room_areas = zip(*filtered)
        
        ax1.pie(room_areas, labels=room_names, autopct='%1.1f%%', startangle=90,
                textprops={'color': self.app.colors['text_primary']})
        ax1.set_title("Room Area Distribution", color=self.app.colors['accent'])
        ax1.axis('equal')

        # Chart 2: Wall Area Analysis
        ax2 = fig.add_subplot(1, 2, 2)
        if self.app.project.walls:
            def _wname(w):
                return w.get('name', 'Wall') if isinstance(w, dict) else getattr(w, 'name', 'Wall')
            def _wgross(w):
                return float(w.get('gross', 0.0) or 0.0) if isinstance(w, dict) else float(getattr(w, 'gross_area', 0.0) or 0.0)
            def _wnet(w):
                return float(w.get('net', 0.0) or 0.0) if isinstance(w, dict) else float(getattr(w, 'net_area', 0.0) or 0.0)
            wall_names = [_wname(w) for w in self.app.project.walls]
            gross_areas = [_wgross(w) for w in self.app.project.walls]
            net_areas = [_wnet(w) for w in self.app.project.walls]
            
            x = range(len(wall_names))
            ax2.bar(x, gross_areas, width=0.4, label='Gross Area', color=self.app.colors['secondary'])
            ax2.bar(x, net_areas, width=0.4, label='Net Area', color=self.app.colors['success'])
            ax2.set_xticks(x)
            ax2.set_xticklabels(wall_names, rotation=45, ha="right", color=self.app.colors['text_secondary'])
            ax2.set_ylabel("Area (m²)", color=self.app.colors['text_secondary'])
            ax2.set_title("Wall Gross vs. Net Area", color=self.app.colors['accent'])
            ax2.legend()
            ax2.tick_params(axis='y', colors=self.app.colors['text_secondary'])
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['bottom'].set_color(self.app.colors['border'])
            ax2.spines['left'].set_color(self.app.colors['border'])
            ax2.set_facecolor(self.app.colors['bg_card'])
        else:
            ax2.text(0.5, 0.5, "No wall data available.", ha='center', va='center', color=self.app.colors['text_muted'])
            ax2.set_xticks([])
            ax2.set_yticks([])
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['bottom'].set_visible(False)
            ax2.spines['left'].set_visible(False)
            ax2.set_facecolor(self.app.colors['bg_card'])

        self.dashboard_canvas = FigureCanvasTkAgg(fig, master=self.dashboard_frame)
        self.dashboard_canvas.draw()
        self.dashboard_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.app.update_status("Dashboard refreshed", icon="📈")
