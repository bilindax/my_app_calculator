"""
Walls Tab Module - Wall ledger, deductions, and net area calculations.

This module provides the UI for the Walls tab, allowing users to:
- Pick walls from AutoCAD
- Edit and delete wall records
- Deduct door/window openings from walls
- View gross, deduction, and net wall areas
- Calculate block quantities and mortar materials
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING
from ...models.wall import Wall
from ...models.masonry import MasonryBlock

from .base_tab import BaseTab

if TYPE_CHECKING:
    from ...bilind_main import BilindEnhanced


class WallsTab(BaseTab):
    """
    Walls tab for wall ledger and deduction tracking.
    
    Features:
    - Pick walls from AutoCAD (length × height)
    - Deduct openings (doors/windows) from walls
    - Edit/delete wall records
    - Display gross, deduct, and net areas
    - Filter and search capabilities
    """
    
    
    def _add_wall(self):
        """Manually add a wall without picking from AutoCAD."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Wall Manually")
        dialog.geometry("400x320")
        dialog.transient(self.parent)
        dialog.grab_set()
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Center dialog
        dialog.update_idletasks()
        try:
            x = self.parent.winfo_rootx() + (self.parent.winfo_width() - 400) // 2
            y = self.parent.winfo_rooty() + (self.parent.winfo_height() - 320) // 2
            dialog.geometry(f"+{x}+{y}")
        except:
            pass

        # Header
        header = ttk.Frame(dialog, style='Header.TFrame', padding=(20, 15))
        header.pack(fill=tk.X)
        ttk.Label(header, text="🧱 Add New Wall", style='Header.TLabel').pack(anchor=tk.W)
        ttk.Label(header, text="Enter wall dimensions manually", style='Subheader.TLabel').pack(anchor=tk.W)

        # Content
        content = ttk.Frame(dialog, style='Main.TFrame', padding=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Input Grid
        grid = ttk.Frame(content, style='Main.TFrame')
        grid.pack(fill=tk.X)
        grid.columnconfigure(1, weight=1)

        # Name
        ttk.Label(grid, text="Name:", foreground=self.colors['text_secondary']).grid(row=0, column=0, sticky='w', pady=8)
        name_var = tk.StringVar(value=f"Wall {len(self.app.project.walls) + 1}")
        ttk.Entry(grid, textvariable=name_var).grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=8)
        
        # Layer
        ttk.Label(grid, text="Layer:", foreground=self.colors['text_secondary']).grid(row=1, column=0, sticky='w', pady=8)
        layer_var = tk.StringVar(value="Manual")
        ttk.Entry(grid, textvariable=layer_var).grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=8)
        
        # Dimensions Frame
        dims_frame = ttk.LabelFrame(content, text="Dimensions", padding=15, style='Card.TLabelframe')
        dims_frame.pack(fill=tk.X, pady=(15, 0))
        dims_frame.columnconfigure(1, weight=1)
        dims_frame.columnconfigure(3, weight=1)

        # Length
        ttk.Label(dims_frame, text="Length (m):").grid(row=0, column=0, sticky='w')
        length_var = tk.StringVar()
        ttk.Entry(dims_frame, textvariable=length_var, width=10).grid(row=0, column=1, sticky='w', padx=(5, 15))
        
        # Height
        ttk.Label(dims_frame, text="Height (m):").grid(row=0, column=2, sticky='w')
        height_var = tk.StringVar(value=str(self.app.project.default_wall_height))
        ttk.Entry(dims_frame, textvariable=height_var, width=10).grid(row=0, column=3, sticky='w', padx=(5, 0))
        
        def save():
            try:
                name = name_var.get().strip()
                if not name:
                    tk.messagebox.showerror("Error", "Name is required", parent=dialog)
                    return
                    
                length = float(length_var.get())
                height = float(height_var.get())
                
                if length <= 0 or height <= 0:
                    tk.messagebox.showerror("Error", "Dimensions must be positive", parent=dialog)
                    return
                
                # Create new wall
                new_wall = Wall(
                    name=name,
                    layer=layer_var.get(),
                    length=length,
                    height=height
                )
                
                self.app.project.walls.append(new_wall)
                self.refresh_data()
                
                if hasattr(self.app, 'update_status'):
                    self.app.update_status(f"Added wall '{name}'", icon="🧱")
                
                dialog.destroy()
                
            except ValueError:
                tk.messagebox.showerror("Error", "Invalid number format", parent=dialog)
        
        # Buttons
        btn_frame = ttk.Frame(dialog, style='Main.TFrame', padding=(0, 20))
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.app.create_button(btn_frame, "Save Wall", save, variant='accent', width=120).pack(side=tk.RIGHT, padx=20)
        self.app.create_button(btn_frame, "Cancel", dialog.destroy, variant='secondary', width=100).pack(side=tk.RIGHT)

    def _create_metrics_footer(self, parent):
        """Create metrics display at bottom of tab - ENHANCED with Block Calculator."""
        # === Block/Masonry Calculator Section ===
        block_card = ttk.LabelFrame(
            parent,
            text="🧱 Block/Masonry Calculator (حاسبة البلوك)",
            padding=(16, 12),
            style='Card.TLabelframe'
        )
        block_card.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        # Block calculator toolbar
        block_toolbar = ttk.Frame(block_card)
        block_toolbar.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(
            block_toolbar,
            text="Block Size:",
            font=('Segoe UI', 9, 'bold'),
            foreground=self.colors.get('text_secondary', '#94a3b8')
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        self.block_size_var = tk.StringVar(value='20cm')
        block_sizes = [
            ('20cm (Standard)', '20cm'),
            ('15cm (Partition)', '15cm'),
            ('10cm (Light)', '10cm')
        ]
        
        for label, value in block_sizes:
            ttk.Radiobutton(
                block_toolbar,
                text=label,
                variable=self.block_size_var,
                value=value,
                command=self._update_block_calculation
            ).pack(side=tk.LEFT, padx=4)
        
        self.create_button(
            block_toolbar,
            "🔄 Calculate",
            self._update_block_calculation,
            'Accent.TButton'
        ).pack(side=tk.RIGHT, padx=4)
        
        # Block calculation display (3 columns)
        calc_frame = ttk.Frame(block_card)
        calc_frame.pack(fill=tk.X, pady=4)
        calc_frame.columnconfigure([0, 1, 2], weight=1)
        
        # Column 1: Wall Areas
        col1 = ttk.Frame(calc_frame, style='Card.TFrame', padding=12)
        col1.grid(row=0, column=0, sticky='nsew', padx=6)
        
        ttk.Label(
            col1,
            text="📏 Wall Areas",
            font=('Segoe UI', 10, 'bold'),
            foreground=self.colors.get('accent', '#00d9ff')
        ).pack(anchor=tk.W, pady=(0, 8))
        
        self.block_area_label = ttk.Label(
            col1,
            text="Gross: 0.00 m²\nDeduct: 0.00 m²\nNet: 0.00 m²",
            font=('Segoe UI', 9),
            foreground=self.colors.get('text_secondary', '#94a3b8'),
            justify=tk.LEFT
        )
        self.block_area_label.pack(anchor=tk.W)
        
        # Column 2: Block Quantities
        col2 = ttk.Frame(calc_frame, style='Card.TFrame', padding=12)
        col2.grid(row=0, column=1, sticky='nsew', padx=6)
        
        ttk.Label(
            col2,
            text="🧱 Blocks & Mortar",
            font=('Segoe UI', 10, 'bold'),
            foreground=self.colors.get('accent', '#00d9ff')
        ).pack(anchor=tk.W, pady=(0, 8))
        
        self.block_qty_label = ttk.Label(
            col2,
            text="Blocks: 0 pcs\nMortar: 0.000 m³\nJoint: 10mm",
            font=('Segoe UI', 9),
            foreground=self.colors.get('text_secondary', '#94a3b8'),
            justify=tk.LEFT
        )
        self.block_qty_label.pack(anchor=tk.W)
        
        # Column 3: Materials
        col3 = ttk.Frame(calc_frame, style='Card.TFrame', padding=12)
        col3.grid(row=0, column=2, sticky='nsew', padx=6)
        
        ttk.Label(
            col3,
            text="📦 Materials Needed",
            font=('Segoe UI', 10, 'bold'),
            foreground=self.colors.get('accent', '#00d9ff')
        ).pack(anchor=tk.W, pady=(0, 8))
        
        self.block_materials_label = ttk.Label(
            col3,
            text="Sand: 0.00 m³\nCement: 0 bags\nRatio: 1:6",
            font=('Segoe UI', 9),
            foreground=self.colors.get('text_secondary', '#94a3b8'),
            justify=tk.LEFT
        )
        self.block_materials_label.pack(anchor=tk.W)
        
        # === Original Metrics Footer ===
        metrics_frame = ttk.Frame(parent, style='Main.TFrame', padding=(16, 8))
        metrics_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        self.app.wall_metrics_var = tk.StringVar(value="Net wall area: 0.00 m²")
        
        ttk.Label(
            metrics_frame,
            textvariable=self.app.wall_metrics_var,
            style='Metrics.TLabel'
        ).pack(anchor=tk.W)
    
    def _update_block_calculation(self):
        """Calculate and display block quantities and mortar materials."""
        # Gather ALL walls (Global + Room-specific)
        all_walls = list(self.app.project.walls)
        
        # Add room walls
        for room in self.app.project.rooms:
            if hasattr(room, 'walls') and room.walls:
                all_walls.extend(room.walls)
        
        # Calculate totals
        total_gross = sum(
            wall.gross_area if hasattr(wall, 'gross_area') else wall.get('gross', 0.0)
            for wall in all_walls
        )
        
        total_deduct = sum(
            wall.deduction_area if hasattr(wall, 'deduction_area') else wall.get('deduct', 0.0)
            for wall in all_walls
        )
        
        total_net = total_gross - total_deduct
        
        if total_net <= 0:
            # No walls or all deducted
            if hasattr(self, 'block_area_label'):
                self.block_area_label.config(
                    text=f"Gross: {total_gross:.2f} m²\nDeduct: {total_deduct:.2f} m²\nNet: {total_net:.2f} m²"
                )
            if hasattr(self, 'block_qty_label'):
                self.block_qty_label.config(text="Blocks: 0 pcs\nMortar: 0.000 m³\nJoint: 10mm")
            if hasattr(self, 'block_materials_label'):
                self.block_materials_label.config(text="Sand: 0.00 m³\nCement: 0 bags\nRatio: 1:6")
            return
        
        # Calculate blocks and mortar
        block_size = self.block_size_var.get() if hasattr(self, 'block_size_var') else '20cm'
        
        try:
            masonry = MasonryBlock(
                name="Total Walls",
                net_area=total_net,
                block_size=block_size,
                mortar_joint_thickness=10.0
            )
            
            materials = masonry.calculate_mortar_materials()
            
            # Update displays
            if hasattr(self, 'block_area_label'):
                self.block_area_label.config(
                    text=f"Gross: {total_gross:.2f} m²\nDeduct: {total_deduct:.2f} m²\nNet: {total_net:.2f} m²"
                )
            
            if hasattr(self, 'block_qty_label'):
                self.block_qty_label.config(
                    text=(
                        f"Blocks: {masonry.block_quantity} pcs\n"
                        f"Mortar: {materials['mortar_m3']:.3f} m³\n"
                        f"Joint: 10mm (1:6 mix)"
                    )
                )
            
            if hasattr(self, 'block_materials_label'):
                self.block_materials_label.config(
                    text=(
                        f"Sand: {materials['sand_m3']:.2f} m³ ({materials['sand_kg']:.0f} kg)\n"
                        f"Cement: {materials['cement_bags']} bags ({materials['cement_kg']:.1f} kg)\n"
                        f"Ratio: 1 cement : 6 sand"
                    )
                )
            
        except Exception as e:
            print(f"Block calculation error: {e}")
            if hasattr(self, 'block_qty_label'):
                self.block_qty_label.config(text=f"Error: {str(e)}")

    def refresh_data(self, query=None):
        """Refreshes the wall data in the treeview, applying an optional filter."""
        tree = getattr(self, 'tree', None)
        if tree is None:
            return
        # Keep shared reference for legacy callers
        self.app.walls_tree = tree

        if query is None:
            query = self.filter_var.get() if hasattr(self, 'filter_var') else ""

        tree.delete(*tree.get_children())
        
        self.app._ensure_wall_names()
        
        total_net_area = 0.0
        total_gross_area = 0.0
        
        search_term = query.strip().lower()

        for wall in self.app.project.walls:
            row_values = self._format_wall_row(wall)
            row_string = " ".join(map(str, row_values)).lower()

            if not search_term or search_term in row_string:
                tree.insert("", tk.END, values=row_values)
                # Use the 'net' value from the formatted tuple
                try:
                    total_net_area += float(row_values[6])
                    total_gross_area += float(row_values[4])
                except (ValueError, IndexError):
                    pass # Ignore if conversion fails

        # Update metrics
        metrics_text = (
            f"Total Walls: {len(self.app.project.walls)} • "
            f"Gross Area: {total_gross_area:.2f} m² • "
            f"Net Area: {total_net_area:.2f} m²"
        )
        # New metrics label (via wall_metrics_var)
        if hasattr(self.app, 'wall_metrics_var') and self.app.wall_metrics_var:
            try:
                self.app.wall_metrics_var.set(metrics_text)
            except Exception:
                pass
        # Legacy metrics label support
        if hasattr(self, 'metrics_label') and getattr(self, 'metrics_label', None):
            self.metrics_label.configure(text=metrics_text)

        # Keep block calculator in sync
        try:
            self._update_block_calculation()
        except Exception:
            pass

    def _format_wall_row(self, wall_record):
        """Formats a wall record (dict or object) for treeview display."""
        if isinstance(wall_record, Wall):
            return (
                wall_record.name,
                wall_record.layer,
                f"{wall_record.length:.2f}",
                f"{wall_record.height:.2f}",
                f"{wall_record.gross_area:.2f}",
                f"{wall_record.deduction_area:.2f}",
                f"{wall_record.net_area:.2f}"
            )
        else: # Legacy dict support
            return (
                wall_record.get('name', '-'),
                wall_record.get('layer', '-'),
                f"{wall_record.get('length', 0):.2f}",
                f"{wall_record.get('height', 0):.2f}",
                f"{wall_record.get('gross', 0):.2f}",
                f"{wall_record.get('deduct', 0):.2f}",
                f"{wall_record.get('net', 0):.2f}"
            )

    def _clear_filter(self):
        """Clears the filter entry and refreshes the tree."""
        self.filter_var.set("")
        self.refresh_data()

    def create(self):
        frame = ttk.Frame(self.parent, style='Main.TFrame', padding=(10, 12))
        frame.pack(fill=tk.BOTH, expand=True)

        # --- Header ---
        header = ttk.Frame(frame, style='Header.TFrame')
        header.pack(fill=tk.X, padx=10, pady=(10, 4))

        ttk.Label(header, text="Wall Ledger & Deductions", style='Header.TLabel').pack(anchor=tk.W)
        ttk.Label(header, text="Manage walls, openings, and view net areas.", style='Subheader.TLabel').pack(anchor='w')

        # --- Toolbar ---
        toolbar = ttk.Frame(frame, style='Toolbar.TFrame')
        toolbar.pack(fill=tk.X, padx=10, pady=(4, 10))

        # Filter
        self.filter_var = tk.StringVar()
        filter_entry = ttk.Entry(toolbar, textvariable=self.filter_var, width=30)
        filter_entry.pack(side=tk.LEFT, padx=(0, 8))
        filter_entry.bind('<KeyRelease>', lambda e: self.refresh_data())

        self.create_button(toolbar, "Clear Filter", self._clear_filter, 'Danger.TButton').pack(side=tk.LEFT)

        # Actions
        action_frame = ttk.Frame(toolbar)
        action_frame.pack(side=tk.RIGHT)

        self.create_button(action_frame, "➕ Add Wall", self._add_wall, 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(action_frame, "🧱 Pick Walls", self.app.pick_walls, 'Accent.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(action_frame, "➖ Deduct Openings", self.app.deduct_from_walls, 'Warning.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(action_frame, "✏️ Edit", self.app.edit_wall, 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(action_frame, "🗑️ Delete", self.app.delete_wall, 'Danger.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(action_frame, "🗑️ Delete Multiple", lambda: self.app.delete_multiple('walls'), 'Danger.TButton').pack(side=tk.LEFT, padx=4)

        # --- Treeview ---
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 10))

        columns = ('Name', 'Layer', 'Length', 'Height', 'Gross Area', 'Deduct Area', 'Net Area')
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            style='Walls.Treeview'
        )
        for col in columns:
            self.tree.heading(col, text=col)
        
        self.tree.column('Length', width=100, anchor='e')
        self.tree.column('Height', width=100, anchor='e')
        self.tree.column('Gross Area', width=100, anchor='e')
        self.tree.column('Deduct Area', width=100, anchor='e')
        self.tree.column('Net Area', width=100, anchor='e')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Block/Masonry Calculator + Metrics Footer ---
        # Place the calculator visibly under the table
        self._create_metrics_footer(frame)

        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_selection)
        
        # Initial data load
        # Ensure shared reference is set so other modules update properly
        # Keep shared references in sync for legacy code paths
        self.walls_tree = self.tree
        self.app.walls_tree = self.tree
        self.refresh_data()
        # Also compute initial block quantities display
        try:
            self._update_block_calculation()
        except Exception:
            pass

        return frame

    def on_selection(self, event):
        """Placeholder for selection-based actions."""
        tree = getattr(self, 'tree', None)
        if tree is None:
            return

        selection = tree.selection()
        if not selection:
            return

        values = tree.item(selection[0], 'values')
        try:
            name = values[0]
            gross = float(values[4])
            deduct = float(values[5])
            net = float(values[6])
        except (IndexError, ValueError, TypeError):
            return

        if hasattr(self.app, 'update_status'):
            self.app.update_status(
                f"Wall {name}: gross {gross:.2f} m² • deduct {deduct:.2f} m² • net {net:.2f} m²",
                icon="🧱"
            )
