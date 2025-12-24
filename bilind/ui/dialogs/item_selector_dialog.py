"""
Item Selector Dialog - Multi-selection dialog for rooms, doors, windows, etc.

Allows users to select specific items from a list with checkboxes and quantity multipliers.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Tuple


class ItemSelectorDialog:
    """
    Dialog for selecting multiple items with optional quantity multipliers.
    
    Features:
    - Checkbox list for item selection
    - Quantity multiplier per item
    - Select All / Deselect All buttons
    - Preview of total area/count
    """
    
    def __init__(self, parent, title: str, items: List[Dict[str, Any]], 
                 show_quantity: bool = False, colors: dict = None):
        """
        Create item selector dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            items: List of dicts with 'name', 'area' or 'value', and optional 'qty'
            show_quantity: Whether to show quantity multiplier column
            colors: Color scheme dict
        """
        self.result = None
        self.items = items
        self.show_quantity = show_quantity
        self.colors = colors or {}
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("750x650")
        self.dialog.resizable(True, True)
        self.dialog.minsize(700, 600)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        if colors:
            self.dialog.configure(bg=colors.get('bg_secondary', '#1e2139'))
        
        # Variables for each item
        self.vars = []  # [(BooleanVar, IntVar), ...]
        
        self._create_ui()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_ui(self):
        """Create dialog UI."""
        # Header
        header = ttk.Frame(self.dialog, padding=(16, 12))
        header.pack(fill=tk.X)
        
        ttk.Label(
            header,
            text=f"Select items to include ({len(self.items)} available)",
            font=('Segoe UI', 12, 'bold'),
            foreground=self.colors.get('text_primary', '#ffffff')
        ).pack(anchor=tk.W)
        
        # Toolbar with Select All / Deselect All
        toolbar = ttk.Frame(self.dialog, padding=(16, 8))
        toolbar.pack(fill=tk.X)
        
        ttk.Button(
            toolbar,
            text="✓ Select All",
            command=self._select_all
        ).pack(side=tk.LEFT, padx=4)
        
        ttk.Button(
            toolbar,
            text="✗ Deselect All",
            command=self._deselect_all
        ).pack(side=tk.LEFT, padx=4)
        
        # Items list with scrollbar
        list_frame = ttk.Frame(self.dialog, padding=(16, 0))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(
            list_frame,
            bg=self.colors.get('bg_primary', '#0a0e1a'),
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Populate items
        for idx, item in enumerate(self.items):
            self._create_item_row(scrollable_frame, item, idx)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel scrolling with safe cleanup
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass  # Canvas destroyed, ignore
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self._canvas = canvas
        self._mousewheel_handler = _on_mousewheel
        
        # Summary and buttons
        bottom = ttk.Frame(self.dialog, padding=(16, 12))
        bottom.pack(fill=tk.X)
        
        self.summary_var = tk.StringVar(value="Total: 0 items, 0.00 m²")
        ttk.Label(
            bottom,
            textvariable=self.summary_var,
            font=('Segoe UI', 10, 'bold'),
            foreground=self.colors.get('accent', '#00d4ff')
        ).pack(anchor=tk.W, pady=(0, 12))
        
        btn_frame = ttk.Frame(bottom)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(
            btn_frame,
            text="✓ OK",
            command=self._ok,
            style='Accent.TButton' if hasattr(ttk, 'Accent.TButton') else None
        ).pack(side=tk.RIGHT, padx=4)
        
        ttk.Button(
            btn_frame,
            text="✗ Cancel",
            command=self._cancel
        ).pack(side=tk.RIGHT, padx=4)
        
        # Update summary initially
        self._update_summary()
    
    def _create_item_row(self, parent, item: Dict[str, Any], idx: int):
        """Create a row for one item."""
        row = ttk.Frame(parent, padding=(8, 4))
        row.pack(fill=tk.X)
        
        # Checkbox
        check_var = tk.BooleanVar(value=True)  # Default: selected
        check = ttk.Checkbutton(
            row,
            variable=check_var,
            command=self._update_summary
        )
        check.pack(side=tk.LEFT, padx=(0, 8))
        
        # Item name
        name = item.get('name', f'Item {idx+1}')
        ttk.Label(
            row,
            text=name,
            width=30,
            font=('Segoe UI', 9, 'bold'),
            foreground=self.colors.get('text_primary', '#e2e8f0')
        ).pack(side=tk.LEFT, padx=(0, 12))
        
        # Area/value display
        area = item.get('area', item.get('value', 0.0))
        ttk.Label(
            row,
            text=f"{area:.2f} m²",
            width=12,
            font=('Segoe UI', 9),
            foreground=self.colors.get('accent', '#00d4ff')
        ).pack(side=tk.LEFT, padx=(0, 12))
        
        # Quantity multiplier (if enabled)
        qty_var = tk.IntVar(value=item.get('qty', 1))
        if self.show_quantity:
            ttk.Label(row, text="Qty:").pack(side=tk.LEFT, padx=(0, 4))
            qty_spin = ttk.Spinbox(
                row,
                from_=1,
                to=10,
                width=5,
                textvariable=qty_var,
                command=self._update_summary
            )
            qty_spin.pack(side=tk.LEFT)
        
        self.vars.append((check_var, qty_var, area))
    
    def _select_all(self):
        """Select all items."""
        for check_var, _, _ in self.vars:
            check_var.set(True)
        self._update_summary()
    
    def _deselect_all(self):
        """Deselect all items."""
        for check_var, _, _ in self.vars:
            check_var.set(False)
        self._update_summary()
    
    def _update_summary(self):
        """Update summary label."""
        count = 0
        total_area = 0.0
        
        for (check_var, qty_var, area), item in zip(self.vars, self.items):
            if check_var.get():
                qty = qty_var.get() if self.show_quantity else 1
                count += 1
                total_area += area * qty
        
        self.summary_var.set(f"Selected: {count} items • Total: {total_area:.2f} m²")
    
    def _cleanup(self):
        """Cleanup event bindings before destroy."""
        try:
            if hasattr(self, '_mousewheel_handler'):
                self._canvas.unbind_all("<MouseWheel>")
        except:
            pass
    
    def _ok(self):
        """Collect selected items and close."""
        self.result = []
        for idx, ((check_var, qty_var, area), item) in enumerate(zip(self.vars, self.items)):
            if check_var.get():
                qty = qty_var.get() if self.show_quantity else 1
                self.result.append({
                    'index': idx,
                    'item': item,
                    'qty': qty,
                    'total_area': area * qty
                })
        self._cleanup()
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel and close."""
        self.result = None
        self._cleanup()
        self.dialog.destroy()
    
    def show(self) -> List[Dict[str, Any]]:
        """Show dialog and return selected items."""
        self.dialog.wait_window()
        return self.result
