"""Material Estimator Tab Module
================================
UI for calculating construction materials: plaster/mortar, ceramic adhesive, baseboards.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import TYPE_CHECKING

from .base_tab import BaseTab
from ...models.mortar import MortarLayer
from ...models.baseboard import Baseboard
from ..dialogs.item_selector_dialog import ItemSelectorDialog

if TYPE_CHECKING:
    from bilind_main import BilindEnhanced


class MaterialEstimatorTab(BaseTab):
    """Tab for advanced material calculations and estimates."""

    def __init__(self, parent: tk.Widget, app: 'BilindEnhanced'):
        super().__init__(parent, app)
        self.mortar_tree = None
        self.baseboard_tree = None
        self.mortar_summary_label = None
        self.baseboard_summary_label = None
        self.ceramic_adhesive_label = None
        self.create_ui()

    def create_ui(self):
        """Create the Material Estimator tab UI."""
        # Main container with scrollbar
        main_canvas = tk.Canvas(self.frame, bg=self.colors['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # === SECTION 1: Plaster/Mortar Calculator ===
        self._create_mortar_section(scrollable_frame)

        # === SECTION 2: Ceramic Adhesive Summary ===
        self._create_ceramic_adhesive_section(scrollable_frame)

        # === SECTION 3: Baseboards/Skirting ===
        self._create_baseboard_section(scrollable_frame)

        # === SECTION 4: Total Materials Summary ===
        self._create_totals_section(scrollable_frame)

    def _create_mortar_section(self, parent):
        """Create plaster/mortar calculator section."""
        card = ttk.LabelFrame(
            parent,
            text="🏗️ Plaster/Mortar Calculator (حاسبة الزريقة والملاط)",
            padding=(12, 8),
            style='Card.TLabelframe'
        )
        card.pack(fill=tk.X, padx=16, pady=(16, 8))

        # Toolbar
        toolbar = ttk.Frame(card)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        self.create_button(
            toolbar,
            "➕ From Plaster Areas",
            self.add_mortar_from_plaster,
            'Accent.TButton'
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.create_button(
            toolbar,
            "➕ From Wall Net",
            self.add_mortar_from_walls,
            'Accent.TButton'
        ).pack(side=tk.LEFT, padx=4)

        self.create_button(
            toolbar,
            "✍️ Manual Entry",
            self.add_mortar_manual,
            'Secondary.TButton'
        ).pack(side=tk.LEFT, padx=4)

        self.create_button(
            toolbar,
            "🗑️ Delete",
            self.delete_mortar,
            'Danger.TButton'
        ).pack(side=tk.RIGHT)

        # Mortar table
        columns = ('Name', 'Area (m²)', 'Type', 'Thick (mm)', 'Vol (m³)', 'Sand (m³)', 'Cement (bags)')
        self.mortar_tree = ttk.Treeview(card, columns=columns, show='headings', height=6)

        for col in columns:
            self.mortar_tree.heading(col, text=col)
        
        widths = [180, 80, 80, 80, 80, 90, 100]
        for col, width in zip(columns, widths):
            self.mortar_tree.column(col, width=width)

        self.mortar_tree.pack(fill=tk.BOTH, expand=True)

        # Summary
        self.mortar_summary_label = ttk.Label(
            card,
            text="Total: 0 layers • 0.00 m³ • Sand: 0.00 m³ • Cement: 0 bags",
            font=('Segoe UI', 9),
            foreground=self.colors.get('text_secondary', '#94a3b8')
        )
        self.mortar_summary_label.pack(anchor=tk.W, pady=(4, 0))

    def _create_ceramic_adhesive_section(self, parent):
        """Create ceramic adhesive auto-calculation section."""
        card = ttk.LabelFrame(
            parent,
            text="🏺 Ceramic Adhesive & Grout (لاصق السيراميك)",
            padding=(12, 8),
            style='Card.TLabelframe'
        )
        card.pack(fill=tk.X, padx=16, pady=8)

        info_text = (
            "Auto-calculated from Ceramic Zones:\n"
            "• Floor tiles: 5 kg/m² adhesive (8mm trowel)\n"
            "• Wall tiles: 3 kg/m² adhesive (6mm trowel)\n"
            "• Grout: 0.5 kg/m² (2-3mm joints)"
        )
        
        ttk.Label(
            card,
            text=info_text,
            font=('Segoe UI', 9),
            foreground=self.colors.get('text_secondary', '#94a3b8'),
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 8))

        self.ceramic_adhesive_label = ttk.Label(
            card,
            text="No ceramic zones defined",
            font=('Segoe UI', 10, 'bold'),
            foreground=self.colors.get('accent', '#00d4ff')
        )
        self.ceramic_adhesive_label.pack(anchor=tk.W)

    def _create_baseboard_section(self, parent):
        """Create baseboard/skirting section."""
        card = ttk.LabelFrame(
            parent,
            text="📏 Baseboards/Skirting (النعلات)",
            padding=(12, 8),
            style='Card.TLabelframe'
        )
        card.pack(fill=tk.X, padx=16, pady=8)

        # Toolbar
        toolbar = ttk.Frame(card)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        self.create_button(
            toolbar,
            "➕ From Rooms",
            self.add_baseboard_from_rooms,
            'Accent.TButton'
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.create_button(
            toolbar,
            "✍️ Manual Entry",
            self.add_baseboard_manual,
            'Secondary.TButton'
        ).pack(side=tk.LEFT, padx=4)

        self.create_button(
            toolbar,
            "🗑️ Delete",
            self.delete_baseboard,
            'Danger.TButton'
        ).pack(side=tk.RIGHT)

        # Baseboard table
        columns = ('Name', 'Perimeter', 'Door Deduct', 'Net Length', 'Material', 'Height (cm)', 'Area (m²)')
        self.baseboard_tree = ttk.Treeview(card, columns=columns, show='headings', height=6)

        for col in columns:
            self.baseboard_tree.heading(col, text=col)
        
        widths = [180, 80, 90, 80, 80, 80, 80]
        for col, width in zip(columns, widths):
            self.baseboard_tree.column(col, width=width)

        self.baseboard_tree.pack(fill=tk.BOTH, expand=True)

        # Summary
        self.baseboard_summary_label = ttk.Label(
            card,
            text="Total: 0 items • 0.00 linear meters",
            font=('Segoe UI', 9),
            foreground=self.colors.get('text_secondary', '#94a3b8')
        )
        self.baseboard_summary_label.pack(anchor=tk.W, pady=(4, 0))

    def _create_totals_section(self, parent):
        """Create overall materials summary."""
        card = ttk.LabelFrame(
            parent,
            text="📊 Total Materials Summary (ملخص المواد)",
            padding=(12, 8),
            style='Card.TLabelframe'
        )
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 16))

        self.totals_text = tk.Text(
            card,
            height=12,
            wrap=tk.WORD,
            bg=self.colors.get('bg_secondary', '#0f1419'),
            fg=self.colors.get('text_primary', '#e2e8f0'),
            font=('Consolas', 10),
            relief=tk.FLAT,
            padx=12,
            pady=8
        )
        self.totals_text.pack(fill=tk.BOTH, expand=True)

    def refresh_data(self):
        """Refresh all sections."""
        self._refresh_mortar()
        self._refresh_ceramic_adhesive()
        self._refresh_baseboards()
        self._refresh_totals()

    def _refresh_mortar(self):
        """Refresh mortar/plaster table."""
        if not self.mortar_tree:
            return

        self.mortar_tree.delete(*self.mortar_tree.get_children())

        total_volume = 0.0
        total_sand = 0.0
        total_cement_bags = 0

        for layer in self.app.project.mortar_layers:
            if hasattr(layer, 'calculate_materials'):
                materials = layer.calculate_materials()
            else:
                # Dict compatibility
                materials = {
                    'total_volume_m3': layer.get('volume_m3', 0.0),
                    'sand_m3': layer.get('sand_m3', 0.0),
                    'cement_bags': layer.get('cement_bags', 0)
                }

            name = layer.name if hasattr(layer, 'name') else layer.get('name', '-')
            area = layer.area if hasattr(layer, 'area') else layer.get('area', 0.0)
            mortar_type = layer.mortar_type if hasattr(layer, 'mortar_type') else layer.get('mortar_type', '-')
            thickness = layer.thickness_mm if hasattr(layer, 'thickness_mm') else layer.get('thickness_mm', 0.0)

            self.mortar_tree.insert('', tk.END, values=(
                name,
                f"{area:.2f}",
                mortar_type.capitalize(),
                f"{thickness:.0f}",
                f"{materials['total_volume_m3']:.3f}",
                f"{materials['sand_m3']:.3f}",
                materials['cement_bags']
            ))

            total_volume += materials['total_volume_m3']
            total_sand += materials['sand_m3']
            total_cement_bags += materials['cement_bags']

        summary = (
            f"Total: {len(self.app.project.mortar_layers)} layers • "
            f"{total_volume:.3f} m³ • Sand: {total_sand:.2f} m³ • "
            f"Cement: {total_cement_bags} bags"
        )
        self.mortar_summary_label.config(text=summary)

    def _refresh_ceramic_adhesive(self):
        """Refresh ceramic adhesive summary."""
        if not self.ceramic_adhesive_label:
            return

        zones = self.app.project.ceramic_zones
        if not zones:
            self.ceramic_adhesive_label.config(text="No ceramic zones defined")
            return

        total_area = 0.0
        total_adhesive = 0.0
        total_grout = 0.0
        floor_area = 0.0
        wall_area = 0.0

        for zone in zones:
            area = zone.area if hasattr(zone, 'area') else float(zone.get('area', 0.0) or 0.0)
            adhesive = zone.adhesive_kg if hasattr(zone, 'adhesive_kg') else 0.0
            grout = zone.grout_kg if hasattr(zone, 'grout_kg') else 0.0
            surface_type = zone.surface_type if hasattr(zone, 'surface_type') else zone.get('surface_type', 'wall')

            total_area += area
            total_adhesive += adhesive
            total_grout += grout

            if surface_type == 'floor':
                floor_area += area
            else:
                wall_area += area

        summary = (
            f"Total ceramic: {total_area:.2f} m² "
            f"(Floor: {floor_area:.2f} m², Wall: {wall_area:.2f} m²)\n"
            f"Adhesive needed: {total_adhesive:.1f} kg • "
            f"Grout needed: {total_grout:.1f} kg"
        )
        self.ceramic_adhesive_label.config(text=summary)

    def _refresh_baseboards(self):
        """Refresh baseboard table."""
        if not self.baseboard_tree:
            return

        self.baseboard_tree.delete(*self.baseboard_tree.get_children())

        total_length = 0.0

        for item in self.app.project.baseboards:
            name = item.name if hasattr(item, 'name') else item.get('name', '-')
            perim = item.perimeter if hasattr(item, 'perimeter') else item.get('perimeter', 0.0)
            door_ded = item.door_width_deduction if hasattr(item, 'door_width_deduction') else item.get('door_width_deduction', 0.0)
            net = item.net_length_m if hasattr(item, 'net_length_m') else item.get('net_length_m', 0.0)
            mat = item.material_type if hasattr(item, 'material_type') else item.get('material_type', '-')
            height = item.height_cm if hasattr(item, 'height_cm') else item.get('height_cm', 0.0)
            area = item.area_m2 if hasattr(item, 'area_m2') else item.get('area_m2', 0.0)

            self.baseboard_tree.insert('', tk.END, values=(
                name,
                f"{perim:.2f}",
                f"{door_ded:.2f}",
                f"{net:.2f}",
                mat.capitalize(),
                f"{height:.1f}",
                f"{area:.2f}"
            ))

            total_length += net

        summary = f"Total: {len(self.app.project.baseboards)} items • {total_length:.2f} linear meters"
        self.baseboard_summary_label.config(text=summary)

    def _refresh_totals(self):
        """Refresh overall materials summary."""
        if not self.totals_text:
            return

        self.totals_text.delete('1.0', tk.END)

        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║         TOTAL CONSTRUCTION MATERIALS SUMMARY              ║",
            "╚═══════════════════════════════════════════════════════════╝",
            ""
        ]

        # Mortar/Plaster
        total_sand = sum(
            (layer.calculate_materials()['sand_m3'] if hasattr(layer, 'calculate_materials') 
             else layer.get('sand_m3', 0.0))
            for layer in self.app.project.mortar_layers
        )
        total_cement_bags = sum(
            (layer.calculate_materials()['cement_bags'] if hasattr(layer, 'calculate_materials')
             else layer.get('cement_bags', 0))
            for layer in self.app.project.mortar_layers
        )

        lines.append("📦 PLASTER/MORTAR MATERIALS:")
        lines.append(f"   • Sand: {total_sand:.2f} m³")
        lines.append(f"   • Cement: {total_cement_bags} bags (50kg each)")
        lines.append("")

        # Ceramic
        zones = self.app.project.ceramic_zones
        total_adhesive = sum(
            (zone.adhesive_kg if hasattr(zone, 'adhesive_kg') else 0.0)
            for zone in zones
        )
        total_grout = sum(
            (zone.grout_kg if hasattr(zone, 'grout_kg') else 0.0)
            for zone in zones
        )

        lines.append("🏺 CERAMIC MATERIALS:")
        lines.append(f"   • Tile Adhesive: {total_adhesive:.1f} kg")
        lines.append(f"   • Grout: {total_grout:.1f} kg")
        lines.append("")

        # Baseboards
        total_baseboard_length = sum(
            (item.net_length_m if hasattr(item, 'net_length_m') else item.get('net_length_m', 0.0))
            for item in self.app.project.baseboards
        )
        total_baseboard_adhesive = sum(
            (item.calculate_adhesive_kg() if hasattr(item, 'calculate_adhesive_kg') 
             else item.get('adhesive_kg', 0.0))
            for item in self.app.project.baseboards
        )

        lines.append("📏 BASEBOARD MATERIALS:")
        lines.append(f"   • Total length: {total_baseboard_length:.2f} linear meters")
        lines.append(f"   • Adhesive/Glue: {total_baseboard_adhesive:.1f} kg")
        lines.append("")

        lines.append("─" * 60)
        lines.append("")
        lines.append("💡 TIP: These are base quantities. Add 10-15% for waste/spillage.")
        
        self.totals_text.insert('1.0', '\n'.join(lines))

    # === MORTAR ACTIONS ===
    
    def add_mortar_from_plaster(self):
        """Add mortar layers from plaster areas."""
        if not self.app.project.plaster_items:
            messagebox.showwarning("No Data", "No plaster items available. Add plaster areas first.")
            return

        # Show selector dialog
        items = []
        for item in self.app.project.plaster_items:
            desc = item.description if hasattr(item, 'description') else item.get('desc', '-')
            area = item.area if hasattr(item, 'area') else item.get('area', 0.0)
            if area > 0:  # Only positive areas
                items.append({'name': desc, 'area': area})

        if not items:
            messagebox.showinfo("No Data", "No valid plaster areas with positive area.")
            return

        dialog = ItemSelectorDialog(
            self.frame,
            "Select Plaster Areas for Mortar Calculation",
            items,
            show_quantity=False,
            colors=self.colors
        )
        
        selected_indices = dialog.show()
        if selected_indices is None:
            return

        # Ask for mortar type and thickness
        mortar_type = self._ask_mortar_type()
        if not mortar_type:
            return

        default_thickness = MortarLayer.DEFAULT_THICKNESS[mortar_type]
        thickness = simpledialog.askfloat(
            "Mortar Thickness",
            f"Enter thickness in mm (typical for {mortar_type}: {default_thickness}mm):",
            initialvalue=default_thickness,
            minvalue=1.0,
            maxvalue=100.0
        )
        
        if not thickness:
            return

        # Create mortar layers
        added = 0
        for idx in selected_indices:
            item = items[idx]
            layer = MortarLayer(
                name=f"Mortar: {item['name']}",
                area=item['area'],
                thickness_mm=thickness,
                mortar_type=mortar_type
            )
            self.app.project.mortar_layers.append(layer)
            added += 1

        self.refresh_data()
        self.app.update_status(f"Added {added} mortar layer(s)", icon="✅")

    def add_mortar_from_walls(self):
        """Add mortar layers from wall net areas."""
        if not self.app.project.walls:
            messagebox.showwarning("No Data", "No walls available. Pick walls first.")
            return

        # Show selector dialog
        items = []
        for wall in self.app.project.walls:
            name = wall.name if hasattr(wall, 'name') else wall.get('name', '-')
            net_area = wall.net_area if hasattr(wall, 'net_area') else wall.get('net', 0.0)
            if net_area and net_area > 0:
                items.append({'name': f"Wall: {name}", 'area': net_area})

        if not items:
            messagebox.showinfo("No Data", "No walls with net area. Deduct openings from walls first.")
            return

        dialog = ItemSelectorDialog(
            self.frame,
            "Select Walls for Mortar Calculation",
            items,
            show_quantity=False,
            colors=self.colors
        )
        
        selected_indices = dialog.show()
        if selected_indices is None:
            return

        # Ask for mortar type and thickness
        mortar_type = self._ask_mortar_type()
        if not mortar_type:
            return

        default_thickness = MortarLayer.DEFAULT_THICKNESS[mortar_type]
        thickness = simpledialog.askfloat(
            "Mortar Thickness",
            f"Enter thickness in mm (typical for {mortar_type}: {default_thickness}mm):",
            initialvalue=default_thickness,
            minvalue=1.0,
            maxvalue=100.0
        )
        
        if not thickness:
            return

        # Create mortar layers
        added = 0
        for idx in selected_indices:
            item = items[idx]
            layer = MortarLayer(
                name=item['name'],
                area=item['area'],
                thickness_mm=thickness,
                mortar_type=mortar_type
            )
            self.app.project.mortar_layers.append(layer)
            added += 1

        self.refresh_data()
        self.app.update_status(f"Added {added} mortar layer(s)", icon="✅")

    def add_mortar_manual(self):
        """Manual mortar layer entry."""
        # Ask for details
        name = simpledialog.askstring("Name", "Enter layer name:")
        if not name:
            return

        area = simpledialog.askfloat("Area", "Enter area (m²):", minvalue=0.01)
        if not area:
            return

        mortar_type = self._ask_mortar_type()
        if not mortar_type:
            return

        default_thickness = MortarLayer.DEFAULT_THICKNESS[mortar_type]
        thickness = simpledialog.askfloat(
            "Thickness",
            f"Enter thickness in mm (typical: {default_thickness}mm):",
            initialvalue=default_thickness,
            minvalue=1.0,
            maxvalue=100.0
        )
        
        if not thickness:
            return

        try:
            layer = MortarLayer(
                name=name,
                area=area,
                thickness_mm=thickness,
                mortar_type=mortar_type
            )
            self.app.project.mortar_layers.append(layer)
            self.refresh_data()
            self.app.update_status(f"Added mortar layer: {name}", icon="✅")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create mortar layer: {str(e)}")

    def delete_mortar(self):
        """Delete selected mortar layer."""
        selection = self.mortar_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select a mortar layer to delete.")
            return

        if messagebox.askyesno("Confirm", "Delete selected mortar layer(s)?"):
            indices = sorted([self.mortar_tree.index(i) for i in selection], reverse=True)
            for idx in indices:
                del self.app.project.mortar_layers[idx]
            self.refresh_data()
            self.app.update_status(f"Deleted {len(indices)} mortar layer(s)", icon="🗑️")

    def _ask_mortar_type(self):
        """Show dialog to select mortar type."""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Select Mortar Type")
        dialog.geometry("400x250")
        dialog.transient(self.frame)
        dialog.grab_set()

        result = {'type': None}

        ttk.Label(
            dialog,
            text="Select mortar/plaster type:",
            font=('Segoe UI', 11, 'bold')
        ).pack(pady=(16, 12))

        var = tk.StringVar(value='rough')

        types = [
            ('rough', 'خشنة (Rough)', '20-30mm, 1:4 mix'),
            ('fine', 'ناعمة (Fine)', '2-5mm, 1:3 mix'),
            ('screeding', 'مسمار (Screeding)', '10-20mm, 1:5 mix')
        ]

        for value, label, desc in types:
            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.X, padx=24, pady=4)
            
            ttk.Radiobutton(
                frame,
                text=f"{label} - {desc}",
                variable=var,
                value=value
            ).pack(anchor=tk.W)

        def ok():
            result['type'] = var.get()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=16)
        
        self.create_button(btn_frame, "OK", ok, 'Accent.TButton', width=120, height=40).pack(side=tk.LEFT, padx=4)
        self.create_button(btn_frame, "Cancel", cancel, 'Secondary.TButton', width=120, height=40).pack(side=tk.LEFT, padx=4)

        dialog.wait_window()
        return result['type']

    # === BASEBOARD ACTIONS ===

    def add_baseboard_from_rooms(self):
        """Add baseboards from room perimeters."""
        if not self.app.project.rooms:
            messagebox.showwarning("No Data", "No rooms available. Pick rooms first.")
            return

        # Show selector dialog
        items = []
        for room in self.app.project.rooms:
            name = room.name if hasattr(room, 'name') else room.get('name', '-')
            perim = room.perimeter if hasattr(room, 'perimeter') else room.get('perim', 0.0)
            if perim > 0:
                items.append({'name': name, 'perimeter': perim})

        if not items:
            messagebox.showinfo("No Data", "No rooms with perimeter data.")
            return

        dialog = ItemSelectorDialog(
            self.frame,
            "Select Rooms for Baseboards",
            items,
            show_quantity=False,
            colors=self.colors
        )
        
        selected_indices = dialog.show()
        if selected_indices is None:
            return

        # Ask for material type
        material = self._ask_baseboard_material()
        if not material:
            return

        # Ask for height
        height = simpledialog.askfloat(
            "Baseboard Height",
            "Enter baseboard height (cm):",
            initialvalue=10.0,
            minvalue=5.0,
            maxvalue=30.0
        )
        if not height:
            return

        # Calculate door deductions from doors in each room
        added = 0
        for idx in selected_indices:
            room_item = items[idx]
            
            # Find doors in this room (by layer matching or association)
            door_deduction = 0.0
            for door in self.app.project.doors:
                door_width = door.width if hasattr(door, 'width') else door.get('w', 0.0)
                door_deduction += door_width

            try:
                baseboard = Baseboard(
                    name=f"Baseboard: {room_item['name']}",
                    perimeter=room_item['perimeter'],
                    door_width_deduction=door_deduction,
                    material_type=material,
                    height_cm=height
                )
                self.app.project.baseboards.append(baseboard)
                added += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create baseboard: {str(e)}")
                continue

        self.refresh_data()
        self.app.update_status(f"Added {added} baseboard(s)", icon="✅")

    def add_baseboard_manual(self):
        """Manual baseboard entry."""
        name = simpledialog.askstring("Name", "Enter baseboard name:")
        if not name:
            return

        perimeter = simpledialog.askfloat("Perimeter", "Enter perimeter (m):", minvalue=0.01)
        if not perimeter:
            return

        door_deduction = simpledialog.askfloat(
            "Door Deduction",
            "Enter total door widths to deduct (m):",
            initialvalue=0.0,
            minvalue=0.0
        )
        if door_deduction is None:
            return

        material = self._ask_baseboard_material()
        if not material:
            return

        height = simpledialog.askfloat(
            "Height",
            "Enter baseboard height (cm):",
            initialvalue=10.0,
            minvalue=5.0,
            maxvalue=30.0
        )
        if not height:
            return

        try:
            baseboard = Baseboard(
                name=name,
                perimeter=perimeter,
                door_width_deduction=door_deduction,
                material_type=material,
                height_cm=height
            )
            self.app.project.baseboards.append(baseboard)
            self.refresh_data()
            self.app.update_status(f"Added baseboard: {name}", icon="✅")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create baseboard: {str(e)}")

    def delete_baseboard(self):
        """Delete selected baseboard."""
        selection = self.baseboard_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select a baseboard to delete.")
            return

        if messagebox.askyesno("Confirm", "Delete selected baseboard(s)?"):
            indices = sorted([self.baseboard_tree.index(i) for i in selection], reverse=True)
            for idx in indices:
                del self.app.project.baseboards[idx]
            self.refresh_data()
            self.app.update_status(f"Deleted {len(indices)} baseboard(s)", icon="🗑️")

    def _ask_baseboard_material(self):
        """Show dialog to select baseboard material."""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Select Baseboard Material")
        dialog.geometry("350x220")
        dialog.transient(self.frame)
        dialog.grab_set()

        result = {'material': None}

        ttk.Label(
            dialog,
            text="Select baseboard material:",
            font=('Segoe UI', 11, 'bold')
        ).pack(pady=(16, 12))

        var = tk.StringVar(value='wood')

        materials = [
            ('wood', 'خشب (Wood)'),
            ('marble', 'رخام (Marble)'),
            ('mdf', 'MDF'),
            ('pvc', 'PVC')
        ]

        for value, label in materials:
            ttk.Radiobutton(
                dialog,
                text=label,
                variable=var,
                value=value
            ).pack(anchor=tk.W, padx=24, pady=4)

        def ok():
            result['material'] = var.get()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=16)
        
        self.create_button(btn_frame, "OK", ok, 'Accent.TButton', width=120, height=40).pack(side=tk.LEFT, padx=4)
        self.create_button(btn_frame, "Cancel", cancel, 'Secondary.TButton', width=120, height=40).pack(side=tk.LEFT, padx=4)

        dialog.wait_window()
        return result['material']
