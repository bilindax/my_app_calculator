"""
Sync Log Tab Module - Real-time AutoCAD event monitoring.

This module provides the UI for the Sync Log tab, allowing users to:
- Monitor real-time AutoCAD object changes
- View event log from sync feature
- Clear log history
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import TYPE_CHECKING

from .base_tab import BaseTab

if TYPE_CHECKING:
    from ...bilind_main import BilindEnhanced


class SyncLogTab(BaseTab):
    """
    Sync Log tab for AutoCAD event monitoring.
    
    Features:
    - Real-time event log display
    - Clear log button
    - Experimental AutoCAD sync monitoring
    """
    def __init__(self, parent: tk.Widget, app: 'BilindEnhanced'):
        super().__init__(parent, app)
        self.sync_log_text = None

    def create(self) -> tk.Frame:
        """
        Create and return the sync log tab frame.
        
        Returns:
            tk.Frame: Configured sync log tab
        """
        container = tk.Frame(self.parent, bg=self.app.colors['bg_secondary'])
        
        # Header
        self._create_header(
            container,
            "AutoCAD Real-time Event Log",
            "Experimental: Monitors AutoCAD for object changes when 'Sync' is active."
        )
        
        # Toolbar
        self._create_toolbar(container)
        
        # Log text area
        self._create_log_area(container)
        
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
        """Create toolbar with clear log button."""
        toolbar = ttk.Frame(parent, style='Toolbar.TFrame', padding=(12, 10))
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        self.create_button(toolbar, "Clear Log", self.clear_log, 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
    
    def _create_log_area(self, parent):
        """Create scrolled text widget for log display."""
        text_frame = ttk.Frame(parent, style='Main.TFrame', padding=(12, 10))
        text_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        
        self.sync_log_text = scrolledtext.ScrolledText(
            text_frame,
            width=92,
            height=28,
            font=('Consolas', 10),
            wrap=tk.WORD
        )
        self.sync_log_text.pack(fill=tk.BOTH, expand=True)
        
        # Apply dark theme styling
        self.sync_log_text.configure(
            bg=self.app.colors['bg_primary'],
            fg=self.app.colors['text_secondary'],
            insertbackground=self.app.colors['accent'],
            relief='flat',
            borderwidth=0,
            padx=10,
            pady=10,
            state='disabled'
        )

    def log_event(self, message: str):
        """Appends a message to the sync log text widget."""
        if not self.sync_log_text:
            return
        
        from datetime import datetime
        self.sync_log_text.config(state='normal')
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.sync_log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.sync_log_text.see(tk.END) # Scroll to the end
        self.sync_log_text.config(state='disabled')

    def clear_log(self):
        """Clears the sync log."""
        if not self.sync_log_text:
            return
            
        self.sync_log_text.config(state='normal')
        self.sync_log_text.delete('1.0', tk.END)
        self.sync_log_text.config(state='disabled')
        self.app.update_status("Sync log cleared", icon="🧹")
