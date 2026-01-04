"""
Costs Tab Module - Material and labor cost estimation.

This module provides the UI for the Costs tab, allowing users to:
- Define unit costs for materials and labor
- Add, edit, and delete cost items
- View total estimated project cost
- Automatic cost calculation based on quantities
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import TYPE_CHECKING

from .base_tab import BaseTab

if TYPE_CHECKING:
    from ...bilind_main import BilindEnhanced


class CostsTab(BaseTab):
    """
    Costs tab for cost estimation and management.
    
    Features:
    - Material and labor cost tracking
    - Add/edit/delete cost items
    - Unit cost definition (m², lm, pcs, kg)
    - Total cost calculation
    """
    def __init__(self, parent: tk.Widget, app: 'BilindEnhanced'):
        super().__init__(parent, app)
        self.costs_tree = None
        self.total_cost_var = None

    def create(self) -> tk.Frame:
        """
        Create and return the costs tab frame.
        
        Returns:
            tk.Frame: Configured costs tab
        """
        container = tk.Frame(self.parent, bg=self.app.colors['bg_secondary'])
        
        # Header
        self._create_header(
            container,
            "Cost Estimation Module",
            "Define unit costs for materials and labor to automatically calculate project estimates."
        )
        
        # Toolbar
        self._create_toolbar(container)
        
        # Costs table
        self._create_costs_table(container)
        
        # Total cost display
        self._create_cost_metrics(container)

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
        """Create toolbar with cost management buttons."""
        toolbar = ttk.Frame(parent, style='Toolbar.TFrame', padding=(12, 10))
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        buttons = [
            ("➕ Add Cost Item", self.add_cost_item, 'Accent.TButton'),
            ("✏️ Edit Cost Item", self.edit_cost_item, 'Secondary.TButton'),
            ("🗑️ Delete Cost Item", self.delete_cost_item, 'Danger.TButton')
        ]
        
        for text, command, style in buttons:
            self.create_button(toolbar, text, command, style).pack(side=tk.LEFT, padx=4)
    
    def _create_costs_table(self, parent):
        """Create costs treeview table."""
        table_frame = ttk.Frame(parent, style='Main.TFrame', padding=(12, 10))
        table_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        
        columns = ('Item', 'Unit', 'Cost')
        
        self.costs_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        # Configure columns
        self.costs_tree.heading('Item', text='Material/Labor Item')
        self.costs_tree.heading('Unit', text='Unit')
        self.costs_tree.heading('Cost', text='Cost per Unit')
        
        self.costs_tree.column('Item', width=300, anchor=tk.W)
        self.costs_tree.column('Unit', width=100, anchor=tk.CENTER)
        self.costs_tree.column('Cost', width=150, anchor=tk.E)
        
        # Scrollbar
        costs_scroll = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self.costs_tree.yview
        )
        self.costs_tree.configure(yscrollcommand=costs_scroll.set)
        
        self.costs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        costs_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_cost_metrics(self, parent):
        """Create total cost display."""
        metrics_frame = ttk.Frame(parent, style='Main.TFrame', padding=(16, 8))
        metrics_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        self.total_cost_var = tk.StringVar(value="Total Estimated Cost: $0.00")
        
        ttk.Label(
            metrics_frame,
            textvariable=self.total_cost_var,
            style='Metrics.TLabel',
            font=('Segoe UI Semibold', 14)
        ).pack(anchor=tk.E)

    def refresh_data(self):
        """Refreshes the data in the costs tab and recalculates the total cost."""
        if not self.costs_tree:
            return

        for item in self.costs_tree.get_children():
            self.costs_tree.delete(item)

        # Use a predefined order for consistency
        cost_order = ['Plaster', 'Paint', 'Tiles', 'Doors', 'Windows', 'Stone', 'Steel', 'Glass']
        
        # Add existing costs
        for item_name in cost_order:
            if item_name in self.app.material_costs:
                cost_info = self.app.material_costs[item_name]
                self.costs_tree.insert('', tk.END, values=(item_name, cost_info['unit'], f"{cost_info['cost']:.2f}"))

        # Add any other costs not in the predefined order
        for item_name, cost_info in self.app.material_costs.items():
            if item_name not in cost_order:
                 self.costs_tree.insert('', tk.END, values=(item_name, cost_info['unit'], f"{cost_info['cost']:.2f}"))

        total_cost, _ = self._calculate_total_cost()
        self.total_cost_var.set(f"Total Estimated Cost: ${total_cost:,.2f}")
        if hasattr(self.app, 'summary_tab'):
            self.app.summary_tab.refresh_data()

    def calculate_total_cost(self):
        """Public wrapper used by exporters to obtain totals and breakdown."""
        return self._calculate_total_cost()

    def add_cost_item(self):
        """Adds a new cost item to the material_costs dictionary."""
        new_item = self._cost_item_dialog("Add New Cost Item")
        if new_item:
            self.app.material_costs[new_item['item']] = {'unit': new_item['unit'], 'cost': new_item['cost']}
            self.refresh_data()
            self.app.update_status(f"Added cost for {new_item['item']}", icon="💰")

    def edit_cost_item(self):
        """Edits an existing cost item."""
        selection = self.costs_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a cost item to edit.")
            return
        
        item_name = self.costs_tree.item(selection[0])['values'][0]
        current_cost = self.app.material_costs.get(item_name, {})
        
        updated_item = self._cost_item_dialog("Edit Cost Item", defaults={'item': item_name, 'unit': current_cost.get('unit'), 'cost': current_cost.get('cost')})
        
        if updated_item:
            self.app.material_costs[updated_item['item']] = {'unit': updated_item['unit'], 'cost': updated_item['cost']}
            self.refresh_data()
            self.app.update_status(f"Updated cost for {updated_item['item']}", icon="💰")

    def delete_cost_item(self):
        """Deletes a cost item."""
        selection = self.costs_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a cost item to delete.")
            return

        item_name = self.costs_tree.item(selection[0])['values'][0]
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the cost for '{item_name}'?"):
            if item_name in self.app.material_costs:
                del self.app.material_costs[item_name]
                self.refresh_data()
                self.app.update_status(f"Deleted cost for {item_name}", icon="🗑️")

    def _calculate_total_cost(self):
        """Calculates the total estimated cost using project data (supports dicts and dataclasses)."""
        total_cost = 0.0
        cost_details = []

        proj = self.app.project

        from .helpers.opening_adapter import OpeningAdapter

        def _sum_finish_area(items):
            total = 0.0
            for item in items:
                if hasattr(item, 'area'):
                    total += float(getattr(item, 'area', 0.0) or 0.0)
                elif isinstance(item, dict):
                    total += float(item.get('area', 0.0) or 0.0)
            return total

        def _sum_opening_attr(openings, dict_key, attr_name, fallback=None):
            total = 0.0
            for opening in openings:
                if isinstance(opening, dict):
                    total += float(opening.get(dict_key, 0.0) or 0.0)
                elif hasattr(opening, attr_name):
                    val = getattr(opening, attr_name)
                    if callable(val):
                        try:
                            total += float(val() or 0.0)
                        except TypeError:
                            if callable(fallback):
                                total += float(fallback(opening) or 0.0)
                            else:
                                total += 0.0
                    else:
                        total += float(val or 0.0)
                elif callable(fallback):
                    total += float(fallback(opening) or 0.0)
            return total

        def _steel_weight_total(door) -> float:
            """Total steel weight (kg) for a door opening (dict or dataclass)."""
            od = OpeningAdapter(door)
            if od.opening_type != 'DOOR':
                return 0.0

            mt = str(od.material_type or '')
            mt_low = mt.lower()
            is_steel = mt == 'Steel' or ('steel' in mt_low) or ('ستيل' in mt) or ('حديد' in mt)
            if not is_steel:
                return 0.0

            if od.weight_each > 0:
                return float(od.weight_total)

            try:
                from bilind.core.config import DOOR_TYPES
                per = float((DOOR_TYPES.get(mt, {}) or {}).get('weight', 0.0) or 0.0)
                return per * float(od.qty or 0)
            except Exception:
                return 0.0

        quantities = {
            'Plaster': _sum_finish_area(proj.plaster_items),
            'Paint': _sum_finish_area(proj.paint_items),
            'Tiles': _sum_finish_area(proj.tiles_items),
            'Doors': _sum_opening_attr(proj.doors, 'qty', 'quantity'),
            'Windows': _sum_opening_attr(proj.windows, 'qty', 'quantity'),
            'Stone': _sum_opening_attr(proj.doors, 'stone', 'stone_linear') + _sum_opening_attr(proj.windows, 'stone', 'stone_linear'),
            'Steel': sum(_steel_weight_total(d) for d in (proj.doors or [])),
            'Glass': _sum_opening_attr(proj.windows, 'glass', 'calculate_glass_area'),
        }

        for item, qty in quantities.items():
            if qty > 0 and item in self.app.material_costs:
                cost_info = self.app.material_costs[item]
                item_total = qty * cost_info['cost']
                total_cost += item_total
                cost_details.append({
                    'item': item,
                    'qty': qty,
                    'unit': cost_info['unit'],
                    'cost': cost_info['cost'],
                    'total': item_total
                })
        
        return total_cost, cost_details

    def _cost_item_dialog(self, title, defaults=None):
        """Dialog for adding or editing a cost item."""
        from tkinter import messagebox

        defaults = defaults or {}
        dialog = tk.Toplevel(self.app.root)
        dialog.title(title)
        dialog.geometry("550x350")
        dialog.resizable(True, True)
        dialog.minsize(500, 300)
        dialog.configure(bg=self.app.colors['bg_secondary'])
        dialog.transient(self.app.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=(18, 14), style='Main.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Item Name", foreground=self.app.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=8)
        item_name_var = tk.StringVar(value=defaults.get('item', ''))
        item_name_entry = ttk.Entry(frame, textvariable=item_name_var, width=30)
        item_name_entry.grid(row=0, column=1, sticky='w', pady=8)
        if 'item' in defaults:
            item_name_entry.config(state='readonly')

        ttk.Label(frame, text="Unit", foreground=self.app.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=8)
        unit_var = tk.StringVar(value=defaults.get('unit', 'm²'))
        unit_combo = ttk.Combobox(frame, textvariable=unit_var, values=['m²', 'lm', 'pcs', 'kg'], width=27)
        unit_combo.grid(row=1, column=1, sticky='w', pady=8)

        ttk.Label(frame, text="Cost per Unit", foreground=self.app.colors['text_secondary']).grid(row=2, column=0, sticky='w', pady=8)
        cost_var = tk.StringVar(value=str(defaults.get('cost', '0.0')))
        ttk.Entry(frame, textvariable=cost_var, width=30).grid(row=2, column=1, sticky='w', pady=8)

        result = {}
        def save():
            try:
                item_name = item_name_var.get().strip()
                unit = unit_var.get()
                cost = float(cost_var.get())
                if not item_name or cost < 0:
                    raise ValueError("Item name cannot be empty and cost must be non-negative.")
                result.update({'item': item_name, 'unit': unit, 'cost': cost})
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e))

        button_bar = ttk.Frame(dialog, padding=(18, 10), style='Main.TFrame')
        button_bar.pack(fill=tk.X)
        self.create_button(button_bar, "Save", save, 'Accent.TButton', width=120, height=40).pack(side=tk.LEFT)
        self.create_button(button_bar, "Cancel", dialog.destroy, 'Secondary.TButton', width=120, height=40).pack(side=tk.RIGHT)

        dialog.wait_window()
        return result
