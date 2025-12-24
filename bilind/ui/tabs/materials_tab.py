"""
Materials Tab Module - Material tracking dashboard.

This module provides the UI for the Materials tab, allowing users to:
- View stone and steel quantities from doors/windows
- Track ceramic zones for kitchens and bathrooms
- Add, edit, and delete ceramic zones
- Calculate total ceramic areas for deductions
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from .base_tab import BaseTab

if TYPE_CHECKING:
    from ...bilind_main import BilindEnhanced


class MaterialsTab(BaseTab):
    """
    Materials tab for tracking stone, steel, and ceramic quantities.
    
    Features:
    - Stone & Steel Ledger (from doors/windows)
    - Kitchen & Bath Ceramic Planner
    - Add/edit/delete ceramic zones
    - Automatic area calculations
    """
    def __init__(self, parent: tk.Widget, app: 'BilindEnhanced'):
        super().__init__(parent, app)
        self.stone_tree = None
        self.stone_metrics_label = None
        self.ceramic_tree = None
        self.ceramic_totals_label = None

    def create(self) -> tk.Frame:
        """
        Create and return the materials tab frame.
        
        Returns:
            tk.Frame: Configured materials tab
        """
        container = tk.Frame(self.parent, bg=self.app.colors['bg_secondary'])
        
        # Header
        self._create_header(
            container,
            "Material Intelligence Dashboard",
            "Track stone quantities, steel door weights, and ceramic areas for kitchens and bathrooms in one place."
        )
        
        # Stone & Steel section
        self._create_stone_section(container)
        
        # Ceramic zones section
        self._create_ceramic_section(container)

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
    
    def _create_stone_section(self, parent):
        """Create stone & steel ledger section."""
        stone_frame = ttk.LabelFrame(
            parent,
            text="🪨 Stone & Steel Ledger",
            style='Card.TLabelframe',
            padding=(14, 12)
        )
        stone_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 10))
        
        # Treeview for stone/steel data
        columns = ('Name', 'Kind', 'Type', 'Qty', 'Stone', 'Area', 'Weight')
        
        self.stone_tree = ttk.Treeview(
            stone_frame,
            columns=columns,
            show='headings',
            height=7
        )
        
        # Configure columns
        column_config = [
            ('Name', 'Name', 110, tk.W),
            ('Kind', 'Kind', 90, tk.CENTER),
            ('Type', 'Type', 120, tk.W),
            ('Qty', 'Qty', 70, tk.CENTER),
            ('Stone', 'Stone (lm)', 110, tk.CENTER),
            ('Area', 'Area (m²)', 110, tk.CENTER),
            ('Weight', 'Steel (kg)', 110, tk.CENTER)
        ]
        
        for col, text, width, anchor in column_config:
            self.stone_tree.heading(col, text=text)
            self.stone_tree.column(col, width=width, anchor=anchor)
        
        # Scrollbar
        stone_scroll = ttk.Scrollbar(
            stone_frame,
            orient=tk.VERTICAL,
            command=self.stone_tree.yview
        )
        self.stone_tree.configure(yscrollcommand=stone_scroll.set)
        
        stone_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.stone_tree.pack(fill=tk.BOTH, expand=True)
        
        # Metrics label
        self.stone_metrics_label = ttk.Label(
            stone_frame,
            text="Stone totals ready",
            style='Metrics.TLabel'
        )
        self.stone_metrics_label.pack(anchor=tk.W, pady=(8, 0))
    
    def _create_ceramic_section(self, parent):
        """Create ceramic zones planning section."""
        ceramic_frame = ttk.LabelFrame(
            parent,
            text="🧼 Kitchen & Bath Ceramic Planner",
            style='Card.TLabelframe',
            padding=(14, 12)
        )
        ceramic_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        
        # Button toolbar
        btn_bar = ttk.Frame(ceramic_frame, style='Main.TFrame')
        btn_bar.pack(fill=tk.X, pady=(0, 10))
        
        buttons = [
            ("➕ Add Zone", self.add_ceramic_zone, 'Accent.TButton'),
            ("✏️ Edit", self.edit_ceramic_zone, 'Secondary.TButton'),
            ("🗑️ Delete", self.delete_ceramic_zone, 'Danger.TButton')
        ]
        
        for text, command, style in buttons:
            self.create_button(btn_bar, text, command, style).pack(side=tk.LEFT, padx=4)
        
        # Ceramic zones treeview
        columns = ('Name', 'Category', 'Type', 'Perimeter', 'Height', 'Area', 'Adhesive', 'Grout', 'Notes')
        
        self.ceramic_tree = ttk.Treeview(
            ceramic_frame,
            columns=columns,
            show='headings',
            height=6
        )
        
        # Configure columns
        column_config = [
            ('Name', 'Zone', 140, tk.W),
            ('Category', 'Category', 90, tk.CENTER),
            ('Type', 'Type', 60, tk.CENTER),
            ('Perimeter', 'Perim (m)', 90, tk.CENTER),
            ('Height', 'Height (m)', 90, tk.CENTER),
            ('Area', 'Area (m²)', 90, tk.CENTER),
            ('Adhesive', 'Adhesive (kg)', 100, tk.CENTER),
            ('Grout', 'Grout (kg)', 90, tk.CENTER),
            ('Notes', 'Notes', 150, tk.W)
        ]
        
        for col, text, width, anchor in column_config:
            self.ceramic_tree.heading(col, text=text)
            self.ceramic_tree.column(col, width=width, anchor=anchor)
        
        # Scrollbar
        ceramic_scroll = ttk.Scrollbar(
            ceramic_frame,
            orient=tk.VERTICAL,
            command=self.ceramic_tree.yview
        )
        self.ceramic_tree.configure(yscrollcommand=ceramic_scroll.set)
        
        ceramic_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.ceramic_tree.pack(fill=tk.BOTH, expand=True)
        
        # Apply modern styling enhancements
        if hasattr(self.app, 'enhance_treeview'):
            self.app.enhance_treeview(self.ceramic_tree)
        
        # Totals label
        self.ceramic_totals_label = ttk.Label(
            ceramic_frame,
            text="No ceramic zones yet",
            style='Metrics.TLabel'
        )
        self.ceramic_totals_label.pack(anchor=tk.W, pady=(8, 0))

    def refresh_data(self):
        """Refreshes both the stone ledger and ceramic zones."""
        self.refresh_stone_ledger()
        self.refresh_ceramic_zones()

    def refresh_stone_ledger(self):
        """Refresh stone/weight table."""
        if not self.stone_tree:
            return

        self.stone_tree.delete(*self.stone_tree.get_children())

        doors_stone = 0.0
        windows_stone = 0.0
        steel_weight = 0.0
        door_area = 0.0
        window_glass = 0.0

        for door in self.app.project.doors:
            # Handle both dict and dataclass
            name = door.name if hasattr(door, 'name') else door.get('name', 'Unknown')
            mat = door.material_type if hasattr(door, 'material_type') else door.get('type', 'Unknown')
            qty = door.quantity if hasattr(door, 'quantity') else door.get('qty', 0)
            stone = door.stone if hasattr(door, 'stone') else door.get('stone', 0)
            area = door.area if hasattr(door, 'area') else door.get('area', 0)
            weight = door.weight if hasattr(door, 'weight') else door.get('weight', 0)
            
            self.stone_tree.insert('', tk.END, values=(
                name, 'Door', mat, qty,
                self.app._fmt(stone), self.app._fmt(area),
                self.app._fmt(weight, digits=1)
            ))
            doors_stone += stone
            door_area += area
            steel_weight += weight

        for window in self.app.project.windows:
            # Handle both dict and dataclass
            name = window.name if hasattr(window, 'name') else window.get('name', 'Unknown')
            mat = window.material_type if hasattr(window, 'material_type') else window.get('type', 'Unknown')
            qty = window.quantity if hasattr(window, 'quantity') else window.get('qty', 0)
            stone = window.stone if hasattr(window, 'stone') else window.get('stone', 0)
            area = window.area if hasattr(window, 'area') else window.get('area', 0)
            glass = window.glass if hasattr(window, 'glass') else window.get('glass', 0)
            
            self.stone_tree.insert('', tk.END, values=(
                name, 'Window', mat, qty,
                self.app._fmt(stone), self.app._fmt(area), '-'
            ))
            windows_stone += stone
            window_glass += glass

        metrics = (
            f"Doors stone: {doors_stone:.2f} lm • Windows stone: {windows_stone:.2f} lm"
            f" • Steel weight: {steel_weight:.1f} kg • Door area: {door_area:.2f} m²"
        )
        if window_glass > 0:
            metrics += f" • Glass area: {window_glass:.2f} m²"
        self.stone_metrics_label.config(text=metrics)

    def refresh_ceramic_zones(self):
        """Refresh ceramic planner table."""
        if not self.ceramic_tree:
            return

        zones = self.app.project.ceramic_zones
        self.ceramic_tree.delete(*self.ceramic_tree.get_children())

        totals = {'Kitchen': 0.0, 'Bathroom': 0.0, 'Other': 0.0}
        for i, zone in enumerate(zones):
            # Handle both dict and dataclass
            if hasattr(zone, 'category'):
                category = zone.category
                name = zone.name
                perim = zone.perimeter
                height = zone.height
                area = zone.area
                surface_type = zone.surface_type
                adhesive = zone.adhesive_kg
                grout = zone.grout_kg
                notes = zone.notes
            else:
                category = zone.get('category', 'Other')
                name = zone.get('name', '-')
                perim = zone.get('perimeter', 0.0)
                height = zone.get('height', 0.0)
                area = zone.get('area', 0.0)
                surface_type = zone.get('surface_type', 'wall')
                adhesive = zone.get('adhesive_kg', 0.0)
                grout = zone.get('grout_kg', 0.0)
                notes = zone.get('notes', '')
            
            totals.setdefault(category, 0.0)
            totals[category] += area
            
            # Surface type emoji
            type_emoji = '🟫' if surface_type == 'floor' else '🧱'
            
            self.ceramic_tree.insert('', tk.END, iid=str(i), values=(
                name, category, type_emoji,
                self.app._fmt(perim), self.app._fmt(height),
                self.app._fmt(area),
                self.app._fmt(adhesive, digits=1),
                self.app._fmt(grout, digits=1),
                notes
            ))

        total_area = sum(totals.values())
        kitchen = totals.get('Kitchen', 0.0)
        bathroom = totals.get('Bathroom', 0.0)
        other = total_area - kitchen - bathroom
        summary = f"Kitchen: {kitchen:.2f} m² • Bathroom: {bathroom:.2f} m²"
        if other > 0:
            summary += f" • Other: {other:.2f} m²"
        summary += f" • Total ceramic: {total_area:.2f} m²"
        self.ceramic_totals_label.config(text=summary if zones else "No ceramic zones yet")

    def add_ceramic_zone(self):
        """Add a new ceramic zone."""
        payload = self.app._ceramic_zone_dialog("Add Ceramic Zone")
        zones, room_name, wall_updates = self.app._parse_ceramic_dialog_result(payload)
        if not zones and not wall_updates:
            return
        added, _ = self.app._apply_ceramic_zone_changes(zones, room_name, wall_updates)
        self.refresh_ceramic_zones()
        self.app.refresh_after_ceramic_change()
        if added:
            first_label = self.app._zone_attr(zones[0], 'name', '') if zones else ''
            msg = "ceramic zone" if added == 1 else f"{added} ceramic zones"
            self.app.update_status(f"✅ Added {msg}: {first_label}", icon="➕")
        else:
            self.app.update_status("Updated ceramic wall heights", icon="🧱")

    def edit_ceramic_zone(self):
        """Edit the selected ceramic zone."""
        selection = self.ceramic_tree.selection()
        if not selection:
            tk.messagebox.showwarning("Warning", "⚠️ Select a ceramic zone to edit.")
            return
        
        item_id = selection[0]
        try:
            idx = int(item_id)
            original_data = self.app.project.ceramic_zones[idx]
            
            new_data = self.app._ceramic_zone_dialog("Edit Ceramic Zone", initial_values=original_data)
            
            if new_data:
                self.app.project.ceramic_zones[idx] = new_data
                self.refresh_ceramic_zones()
                self.app.update_status(f"✅ Edited ceramic zone: {new_data.name}", icon="✏️")
        except (ValueError, IndexError):
             tk.messagebox.showerror("Error", "Could not find the selected ceramic zone to edit.")

    def delete_ceramic_zone(self):
        """Delete the selected ceramic zone."""
        selection = self.ceramic_tree.selection()
        if not selection:
            tk.messagebox.showwarning("Warning", "⚠️ Select a ceramic zone to delete.")
            return

        if not tk.messagebox.askyesno("Confirm", "Are you sure you want to delete the selected ceramic zone(s)?"):
            return
            
        indices_to_delete = sorted([int(item_id) for item_id in selection], reverse=True)

        for idx in indices_to_delete:
            if 0 <= idx < len(self.app.project.ceramic_zones):
                del self.app.project.ceramic_zones[idx]
        
        self.refresh_ceramic_zones()
        self.app.update_status(f"🗑️ Deleted {len(indices_to_delete)} ceramic zone(s).", icon="🗑️")
