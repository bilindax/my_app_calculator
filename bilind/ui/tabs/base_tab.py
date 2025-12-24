"""
Base Tab Class
==============
Abstract base class for all UI tabs with shared functionality.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable, Optional


class BaseTab:
    """
    Base class for all application tabs.
    
    Provides common functionality:
    - Access to parent app instance
    - Color scheme and styling
    - Status update helpers
    - Common UI utilities
    """
    
    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the tab.
        
        Args:
            parent: Parent notebook widget
            app: Main application instance (BilindEnhanced)
        """
        self.parent = parent
        self.app = app
        self.colors = app.colors
        self.frame = ttk.Frame(parent, style='Main.TFrame')
        
    def create(self) -> tk.Frame:
        """
        Create and return the tab's frame with all widgets.
        
        Must be implemented by subclasses.
        
        Returns:
            The configured frame widget
        """
        raise NotImplementedError("Subclasses must implement create()")
    
    def update_status(self, message: str, icon: str = "ℹ️"):
        """Update the application status bar."""
        self.app.update_status(message, icon)
    
    def _fmt(self, value: Optional[float], digits: int = 2) -> str:
        """Format a number for display."""
        return self.app._fmt(value, digits)
    
    def create_header(self, title: str, subtitle: str = "") -> ttk.Frame:
        """
        Create a styled header frame for the tab.
        
        Args:
            title: Main title text
            subtitle: Optional subtitle text
            
        Returns:
            Configured header frame
        """
        header = ttk.Frame(self.frame, style='Hero.TFrame', padding=(20, 16))
        header.pack(fill=tk.X)
        
        ttk.Label(
            header,
            text=title,
            style='HeroHeading.TLabel'
        ).pack(anchor=tk.W)
        
        if subtitle:
            ttk.Label(
                header,
                text=subtitle,
                style='HeroSubheading.TLabel'
            ).pack(anchor=tk.W, pady=(4, 0))
        
        return header
    
    def create_button_row(self, buttons: list) -> ttk.Frame:
        """
        Create a row of buttons with consistent styling.
        
        Args:
            buttons: List of (text, command, style) tuples
            
        Returns:
            Frame containing the buttons
        """
        btn_frame = ttk.Frame(self.frame, style='Main.TFrame', padding=(20, 12))
        btn_frame.pack(fill=tk.X)
        
        for text, command, style in buttons:
            button = self.create_button(btn_frame, text, command, style)
            button.pack(side=tk.LEFT, padx=4)
        
        return btn_frame
    
    def create_search_bar(self, search_var: tk.StringVar, on_change: Callable) -> ttk.Frame:
        """
        Create a search bar with icon and entry.
        
        Args:
            search_var: StringVar to bind to entry
            on_change: Callback when search text changes
            
        Returns:
            Frame containing the search bar
        """
        search_frame = ttk.Frame(self.frame, style='Main.TFrame', padding=(20, 8))
        search_frame.pack(fill=tk.X)
        
        ttk.Label(
            search_frame,
            text="🔍 Search:",
            foreground=self.colors['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_var.trace_add('write', on_change)
        
        return search_frame
    
    def create_metrics_label(self, text_var: tk.StringVar) -> ttk.Label:
        """
        Create a metrics display label.
        
        Args:
            text_var: StringVar containing the metrics text
            
        Returns:
            Configured label widget
        """
        return ttk.Label(
            self.frame,
            textvariable=text_var,
            style='Metrics.TLabel',
            padding=(20, 8)
        )

    # --- Modern Button Helpers -----------------------------------------
    def create_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable,
        style: str = 'Accent.TButton',
        width: int = 156,
        height: int = 42
    ) -> tk.Widget:
        """Create a themed button (rounded when supported)."""
        variant = self._style_to_variant(style)
        if variant:
            return self.app.create_button(parent, text, command, variant=variant, width=width, height=height)
        return ttk.Button(parent, text=text, command=command, style=style)

    @staticmethod
    def _style_to_variant(style: str) -> Optional[str]:
        mapping = {
            'Accent.TButton': 'accent',
            'Secondary.TButton': 'secondary',
            'Danger.TButton': 'danger',
            'Warning.TButton': 'warning',
            'Success.TButton': 'success',
            'Info.TButton': 'info',
            'AccentOutline.TButton': 'accent',
            'Small.TButton': 'secondary'
        }
        return mapping.get(style)
