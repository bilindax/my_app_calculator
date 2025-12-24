"""
Opening Assignment Dialog
=========================
Dialog for assigning doors and windows to a specific room.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, List, Callable


class OpeningAssignmentDialog:
    """
    Dialog window for assigning openings (doors/windows) to a room.
    
    Features:
    - Checkbox list of all available doors
    - Checkbox list of all available windows
    - Real-time summary of selected openings
    - Save/Cancel/Clear All buttons
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        room: Dict[str, Any],
        doors: List[Dict[str, Any]],
        windows: List[Dict[str, Any]],
        get_opening_func: Callable[[str], Optional[Dict]],
        colors: Dict[str, str]
    ):
        """
        Initialize the dialog.
        
        Args:
            parent: Parent window
            room: Room dictionary to assign openings to
            doors: List of all door dictionaries
            windows: List of all window dictionaries
            get_opening_func: Function to get opening by ID
            colors: Color scheme dictionary
        """
        self.parent = parent
        self.room = room
        self.doors = doors
        self.windows = windows
        self.get_opening_func = get_opening_func
        self.colors = colors
        
        self.result: Optional[List[str]] = None
        self.door_vars: Dict[str, tk.BooleanVar] = {}
        self.window_vars: Dict[str, tk.BooleanVar] = {}
        
        self.dialog = tk.Toplevel(parent)
        self._create_ui()
    
    def _create_ui(self):
        """Create the dialog UI."""
        self.dialog.title(f"Assign Openings to {self.room.get('name', 'Room')}")
        self.dialog.geometry("700x850")
        self.dialog.resizable(True, True)
        self.dialog.minsize(650, 750)
        self.dialog.configure(bg=self.colors.get('bg_secondary', '#1a1a2e'))
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Header
        self._create_header()
        
        # Room info
        self._create_room_info()
        
        # Doors section
        self._create_doors_section()
        
        # Windows section
        self._create_windows_section()
        
        # Summary
        self._create_summary()
        
        # Buttons
        self._create_buttons()
    
    def _create_header(self):
        """Create the dialog header."""
        header = tk.Frame(self.dialog, bg=self.colors.get('bg_card', '#0f0f1e'))
        header.pack(fill=tk.X, padx=0, pady=0)
        
        tk.Label(
            header,
            text=f"🔗 Assign Openings to \"{self.room.get('name', 'Room')}\"",
            bg=self.colors.get('bg_card', '#0f0f1e'),
            fg=self.colors.get('accent', '#00d4ff'),
            font=('Segoe UI Semibold', 14)
        ).pack(pady=16, padx=18, anchor='w')
    
    def _create_room_info(self):
        """Create room information display."""
        info_frame = tk.Frame(
            self.dialog,
            bg=self.colors.get('bg_secondary', '#1a1a2e')
        )
        info_frame.pack(fill=tk.X, padx=18, pady=(0, 12))
        
        tk.Label(
            info_frame,
            text=f"Room: {self.room.get('name', 'Unknown')} ({self.room.get('area', 0):.2f} m²)",
            bg=self.colors.get('bg_secondary', '#1a1a2e'),
            fg=self.colors.get('text_secondary', '#b0bec5'),
            font=('Segoe UI', 10)
        ).pack(anchor='w')
        
        tk.Label(
            info_frame,
            text=f"Perimeter: {self.room.get('perim', 0):.2f} m",
            bg=self.colors.get('bg_secondary', '#1a1a2e'),
            fg=self.colors.get('text_secondary', '#b0bec5'),
            font=('Segoe UI', 10)
        ).pack(anchor='w')
    
    def _create_doors_section(self):
        """Create the doors selection section."""
        current_ids = self.room.get('opening_ids', [])
        
        doors_frame = tk.LabelFrame(
            self.dialog,
            text="🚪 Available Doors",
            bg=self.colors.get('bg_secondary', '#1a1a2e'),
            fg=self.colors.get('text_primary', '#ffffff'),
            font=('Segoe UI Semibold', 11),
            padx=12,
            pady=10
        )
        doors_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 4))
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(
            doors_frame,
            bg=self.colors.get('bg_card', '#0f0f1e'),
            height=180,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(doors_frame, orient=tk.VERTICAL, command=canvas.yview)
        inner_frame = tk.Frame(canvas, bg=self.colors.get('bg_card', '#0f0f1e'))
        
        canvas.create_window((0, 0), window=inner_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add checkboxes for each door
        if not self.doors:
            tk.Label(
                inner_frame,
                text="No doors available",
                bg=self.colors.get('bg_card', '#0f0f1e'),
                fg=self.colors.get('text_secondary', '#b0bec5'),
                font=('Segoe UI', 10, 'italic')
            ).pack(pady=10)
        else:
            for door in self.doors:
                var = tk.BooleanVar(value=door['name'] in current_ids)
                self.door_vars[door['name']] = var
                
                text = f"{door['name']} - {door.get('type', '-')} {door.get('w', 0):.2f}×{door.get('h', 0):.2f} ({door.get('area', 0):.2f} m²)"
                
                chk = tk.Checkbutton(
                    inner_frame,
                    text=text,
                    variable=var,
                    bg=self.colors.get('bg_card', '#0f0f1e'),
                    fg=self.colors.get('text_primary', '#ffffff'),
                    selectcolor=self.colors.get('bg_secondary', '#1a1a2e'),
                    activebackground=self.colors.get('bg_card', '#0f0f1e'),
                    activeforeground=self.colors.get('accent', '#00d4ff'),
                    font=('Segoe UI', 10),
                    anchor='w'
                )
                chk.pack(anchor='w', pady=3, padx=8, fill=tk.X)
                
                var.trace_add('write', lambda *_: self._update_summary())
        
        inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
    
    def _create_windows_section(self):
        """Create the windows selection section."""
        current_ids = self.room.get('opening_ids', [])
        
        windows_frame = tk.LabelFrame(
            self.dialog,
            text="🪟 Available Windows",
            bg=self.colors.get('bg_secondary', '#1a1a2e'),
            fg=self.colors.get('text_primary', '#ffffff'),
            font=('Segoe UI Semibold', 11),
            padx=12,
            pady=10
        )
        windows_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(
            windows_frame,
            bg=self.colors.get('bg_card', '#0f0f1e'),
            height=180,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(windows_frame, orient=tk.VERTICAL, command=canvas.yview)
        inner_frame = tk.Frame(canvas, bg=self.colors.get('bg_card', '#0f0f1e'))
        
        canvas.create_window((0, 0), window=inner_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add checkboxes for each window
        if not self.windows:
            tk.Label(
                inner_frame,
                text="No windows available",
                bg=self.colors.get('bg_card', '#0f0f1e'),
                fg=self.colors.get('text_secondary', '#b0bec5'),
                font=('Segoe UI', 10, 'italic')
            ).pack(pady=10)
        else:
            for window in self.windows:
                var = tk.BooleanVar(value=window['name'] in current_ids)
                self.window_vars[window['name']] = var
                
                text = f"{window['name']} - {window.get('type', '-')} {window.get('w', 0):.2f}×{window.get('h', 0):.2f} ({window.get('area', 0):.2f} m²)"
                
                chk = tk.Checkbutton(
                    inner_frame,
                    text=text,
                    variable=var,
                    bg=self.colors.get('bg_card', '#0f0f1e'),
                    fg=self.colors.get('text_primary', '#ffffff'),
                    selectcolor=self.colors.get('bg_secondary', '#1a1a2e'),
                    activebackground=self.colors.get('bg_card', '#0f0f1e'),
                    activeforeground=self.colors.get('accent', '#00d4ff'),
                    font=('Segoe UI', 10),
                    anchor='w'
                )
                chk.pack(anchor='w', pady=3, padx=8, fill=tk.X)
                
                var.trace_add('write', lambda *_: self._update_summary())
        
        inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
    
    def _create_summary(self):
        """Create the summary display."""
        summary_frame = tk.Frame(
            self.dialog,
            bg=self.colors.get('bg_secondary', '#1a1a2e')
        )
        summary_frame.pack(fill=tk.X, padx=18, pady=(12, 0))
        
        self.summary_var = tk.StringVar()
        
        tk.Label(
            summary_frame,
            textvariable=self.summary_var,
            bg=self.colors.get('bg_secondary', '#1a1a2e'),
            fg=self.colors.get('accent', '#00d4ff'),
            font=('Segoe UI', 10, 'italic'),
            justify=tk.LEFT
        ).pack(anchor='w')
        
        self._update_summary()
    
    def _update_summary(self):
        """Update the summary text with current selections."""
        selected = []
        total_area = 0.0
        
        # Collect selected doors
        for door_id, var in self.door_vars.items():
            if var.get():
                selected.append(door_id)
                opening = self.get_opening_func(door_id)
                if opening:
                    total_area += opening.get('area', 0.0)
        
        # Collect selected windows
        for window_id, var in self.window_vars.items():
            if var.get():
                selected.append(window_id)
                opening = self.get_opening_func(window_id)
                if opening:
                    total_area += opening.get('area', 0.0)
        
        # Format summary
        if selected:
            summary = f"✓ Currently assigned: {', '.join(selected)}\nTotal opening area: {total_area:.2f} m²"
        else:
            summary = "No openings assigned"
        
        self.summary_var.set(summary)
    
    def _create_buttons(self):
        """Create action buttons."""
        btn_frame = tk.Frame(
            self.dialog,
            bg=self.colors.get('bg_secondary', '#1a1a2e')
        )
        btn_frame.pack(fill=tk.X, padx=18, pady=16)
        
        # Save button
        save_btn = tk.Button(
            btn_frame,
            text="✓ Save",
            command=self._save,
            bg=self.colors.get('accent', '#00d4ff'),
            fg='#ffffff',
            font=('Segoe UI Semibold', 10),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        save_btn.pack(side=tk.LEFT, padx=4)
        
        # Clear All button
        clear_btn = tk.Button(
            btn_frame,
            text="Clear All",
            command=self._clear_all,
            bg=self.colors.get('warning', '#f59e0b'),
            fg='#ffffff',
            font=('Segoe UI Semibold', 10),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        clear_btn.pack(side=tk.LEFT, padx=4)
        
        # Cancel button
        cancel_btn = tk.Button(
            btn_frame,
            text="✗ Cancel",
            command=self.dialog.destroy,
            bg=self.colors.get('bg_tertiary', '#2a2a3e'),
            fg=self.colors.get('text_primary', '#ffffff'),
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.RIGHT, padx=4)
    
    def _save(self):
        """Save the selected openings and close dialog."""
        selected_ids = []
        
        for door_id, var in self.door_vars.items():
            if var.get():
                selected_ids.append(door_id)
        
        for window_id, var in self.window_vars.items():
            if var.get():
                selected_ids.append(window_id)
        
        self.result = selected_ids
        self.dialog.destroy()
    
    def _clear_all(self):
        """Clear all selections."""
        for var in list(self.door_vars.values()) + list(self.window_vars.values()):
            var.set(False)
    
    def show(self) -> Optional[List[str]]:
        """
        Show the dialog and wait for user action.
        
        Returns:
            List of selected opening IDs, or None if cancelled
        """
        self.dialog.wait_window()
        return self.result
