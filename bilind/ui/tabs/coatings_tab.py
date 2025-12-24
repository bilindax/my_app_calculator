"""
Coatings Tab Module
===================
Dedicated tab for Plaster and Paint calculations.
Separates wall/ceiling coatings from hard finishes.
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING
from tkinter import messagebox, simpledialog

from .base_tab import BaseTab
from ..dialogs.item_selector_dialog import ItemSelectorDialog
# Legacy room_metrics removed - uses UnifiedCalculator instead

if TYPE_CHECKING:
    from ...bilind_main import BilindEnhanced


class CoatingsTab(BaseTab):
    """
    Tab for Plaster and Paint.
    
    Features:
    - Plaster Calculator (Walls + Ceilings)
    - Paint Calculator
    - Auto-deductions for Openings and Ceramic Zones
    """
    
    def __init__(self, parent: tk.Widget, app: 'BilindEnhanced'):
        super().__init__(parent, app)
        self.plaster_tree = None
        self.plaster_label = None
        self.paint_tree = None
        self.paint_label = None

    def create(self) -> tk.Frame:
        container = tk.Frame(self.parent, bg=self.app.colors['bg_secondary'])
        
        self._create_header(
            container,
            "Plaster & Paint Works",
            "Calculate wall and ceiling coatings. Deduct openings and ceramic zones automatically."
        )
        
        # Global Toolbar
        toolbar = ttk.Frame(container, style='Main.TFrame', padding=(16, 0, 16, 8))
        toolbar.pack(fill=tk.X)
        self.create_button(toolbar, "🔄 Auto-Calc All Rooms", self.auto_calculate_all, 'Accent.TButton').pack(side=tk.LEFT)
        ttk.Label(toolbar, text=" (Replaces all items with auto-calculated values based on current Room/Ceramic data)", style='Caption.TLabel').pack(side=tk.LEFT, padx=8)
        
        # Scrollable area
        canvas = tk.Canvas(container, bg=self.app.colors['bg_secondary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.app.colors['bg_secondary'])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # 1. Plaster Section
        self._create_section(scrollable_frame, 'plaster', "🏗️ Plaster Works")
        
        # 2. Paint Section
        self._create_section(scrollable_frame, 'paint', "🎨 Paint Works")

        self.refresh_data()
        return container

    def _create_header(self, parent, title, subtitle):
        hero = ttk.Frame(parent, style='Hero.TFrame', padding=(18, 20))
        hero.pack(fill=tk.X, padx=16, pady=(16, 12))
        ttk.Label(hero, text=title, style='HeroHeading.TLabel').pack(anchor=tk.W)
        ttk.Label(hero, text=subtitle, style='HeroSubheading.TLabel').pack(anchor=tk.W, pady=(6, 0))

    def _create_section(self, parent, key, title):
        frame = ttk.LabelFrame(parent, text=title, style='Card.TLabelframe', padding=(12, 10))
        frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        # Toolbar
        btns = ttk.Frame(frame, style='Main.TFrame')
        btns.pack(fill=tk.X, pady=(0, 8))
        
        # Add Sources
        self.create_button(btns, "➕ Room Ceilings", lambda: self.add_ceilings(key), 'Accent.TButton').pack(side=tk.LEFT, padx=2)
        self.create_button(btns, "📐 Room Walls", lambda: self.add_walls(key), 'Accent.TButton').pack(side=tk.LEFT, padx=2)
        self.create_button(btns, "🧱 Net Walls", lambda: self.add_net_walls(key), 'Secondary.TButton').pack(side=tk.LEFT, padx=2)
        
        # Deductions
        self.create_button(btns, "🚪 Deduct Openings", lambda: self.deduct_openings(key), 'Warning.TButton').pack(side=tk.LEFT, padx=2)
        self.create_button(btns, "➖ Deduct Ceramic", lambda: self.deduct_ceramic(key), 'Warning.TButton').pack(side=tk.LEFT, padx=2)
        
        # Edit/Del
        self.create_button(btns, "🗑️ Clear", lambda: self.clear_items(key), 'Danger.TButton').pack(side=tk.RIGHT, padx=2)

        # Treeview
        tree = ttk.Treeview(frame, columns=('Desc', 'Area', 'Waste'), show='headings', height=5)
        tree.heading('Desc', text='Description')
        tree.heading('Area', text='Net Area (m²)')
        tree.heading('Waste', text='With Waste (m²)')
        tree.column('Desc', width=350)
        tree.column('Area', width=100, anchor=tk.CENTER)
        tree.column('Waste', width=100, anchor=tk.CENTER)
        tree.pack(fill=tk.X, expand=True)
        
        label = ttk.Label(frame, text="Total: 0.00 m²", style='Metrics.TLabel')
        label.pack(anchor=tk.W, pady=(8, 0))
        
        setattr(self, f"{key}_tree", tree)
        setattr(self, f"{key}_label", label)

    def refresh_data(self):
        self._refresh_list('plaster')
        self._refresh_list('paint')
    
    def notify_data_changed(self):
        """Notify that coating data has changed - refresh output tabs."""
        if hasattr(self.app, 'summary_tab'):
            self.app.summary_tab.refresh_data()
        if hasattr(self.app, 'quantities_tab'):
            self.app.quantities_tab.refresh_data()

    def _refresh_list(self, key):
        tree = getattr(self, f"{key}_tree")
        label = getattr(self, f"{key}_label")
        if not tree: return
        
        tree.delete(*tree.get_children())
        items = getattr(self.app.project, f"{key}_items")
        waste_pct = getattr(self.app.project, f"{key}_waste_percentage", 5.0)
        
        total = 0.0
        for item in items:
            if isinstance(item, dict):
                desc = item.get('desc') or item.get('description')
                area = float(item.get('area', 0.0) or 0.0)
            else:
                desc = getattr(item, 'description', '')
                area = float(getattr(item, 'area', 0.0) or 0.0)

            w_area = area * (1 + waste_pct/100)
            
            tags = ('deduction',) if area < 0 else ()
            tree.insert('', tk.END, values=(desc, f"{area:.2f}", f"{w_area:.2f}"), tags=tags)
            total += area
            
        tree.tag_configure('deduction', foreground='red')
        label.config(text=f"Net: {total:.2f} m² (Waste +{waste_pct}%)")

    # --- Actions ---

    def auto_calculate_all(self):
        if not self.app.project.rooms:
            messagebox.showwarning("No Rooms", "No rooms to calculate.")
            return
        
        if not messagebox.askyesno("Auto-Calc", "This will CLEAR current lists and regenerate them from room data.\nContinue?"):
            return

        # Clear
        self.app.project.plaster_items.clear()
        self.app.project.paint_items.clear()

        # Use UnifiedCalculator for consistent calculations
        from ...calculations.unified_calculator import UnifiedCalculator
        from ...models.finish import FinishItem
        
        calc = UnifiedCalculator(self.app.project)
        all_room_calcs = calc.calculate_all_rooms()
        
        for room_calc in all_room_calcs:
            room_name = room_calc.room_name
            
            # Plaster breakdown
            if room_calc.plaster_walls > 0:
                self.app.project.plaster_items.append(FinishItem(
                    description=f"Walls: {room_name}", 
                    area=room_calc.plaster_walls, 
                    finish_type='plaster'
                ))
            if room_calc.plaster_ceiling > 0:
                self.app.project.plaster_items.append(FinishItem(
                    description=f"Ceiling: {room_name}", 
                    area=room_calc.plaster_ceiling, 
                    finish_type='plaster'
                ))

            # Paint breakdown
            if room_calc.paint_walls > 0:
                self.app.project.paint_items.append(FinishItem(
                    description=f"Walls: {room_name}", 
                    area=room_calc.paint_walls, 
                    finish_type='paint'
                ))
            if room_calc.paint_ceiling > 0:
                self.app.project.paint_items.append(FinishItem(
                    description=f"Ceiling: {room_name}", 
                    area=room_calc.paint_ceiling, 
                    finish_type='paint'
                ))

        self.refresh_data()
        self.notify_data_changed()
        self.app.update_status("Auto-calculated coatings for all rooms using UnifiedCalculator.", icon="✅")

    def add_ceilings(self, key):
        # Add room areas (ceilings)
        if not self.app.project.rooms:
            messagebox.showwarning("No Rooms", "Pick rooms first.")
            return
        
        ctx = self._get_metrics_context()
        items = []
        for r in self.app.project.rooms:
            m = calculate_room_finish_metrics(r, ctx)
            if key == 'paint':
                area = m.ceiling_paint
                desc = f"Ceiling: {m.name} (Net Paint)"
            else:
                area = m.ceiling_plaster_net
                desc = f"Ceiling: {m.name}"
            
            if area > 0:
                items.append({'name': desc, 'area': area})
            
        dialog = ItemSelectorDialog(self.app.root, f"Select Ceilings for {key.title()}", items, show_quantity=False, colors=self.app.colors)
        sel = dialog.show()
        if sel:
            from ...models.finish import FinishItem
            for s in sel:
                getattr(self.app.project, f"{key}_items").append(FinishItem(
                    description=s['item']['name'], area=s['total_area'], finish_type=key
                ))
            self.refresh_data()

    def add_walls(self, key):
        # Add room walls (prioritizing explicit walls if present)
        if not self.app.project.rooms:
            messagebox.showwarning("No Rooms", "Pick rooms first.")
            return
            
        # Ask for default height for rooms without explicit walls
        h_str = simpledialog.askstring("Height", "Enter default wall height (m) for rooms without explicit walls:", initialvalue="3.0")
        default_h = 3.0
        if h_str:
            try:
                default_h = float(h_str)
            except: pass
        
        ctx = self._get_metrics_context(default_h)
        items = []
        for r in self.app.project.rooms:
            m = calculate_room_finish_metrics(r, ctx)
            if key == 'paint':
                area = m.walls_paint_net
                desc = f"Walls: {m.name} (Net Paint)"
            else:
                area = m.wall_plaster_net
                desc = f"Walls: {m.name} (Net Plaster)"
            
            if area > 0:
                items.append({'name': desc, 'area': area})
            
        dialog = ItemSelectorDialog(self.app.root, f"Select Walls for {key.title()}", items, show_quantity=False, colors=self.app.colors)
        sel = dialog.show()
        if sel:
            from ...models.finish import FinishItem
            for s in sel:
                getattr(self.app.project, f"{key}_items").append(FinishItem(
                    description=s['item']['name'], area=s['total_area'], finish_type=key
                ))
            self.refresh_data()

    def add_net_walls(self, key):
        # Add from Walls tab (net area)
        if not self.app.project.walls:
            messagebox.showwarning("No Walls", "Pick walls first.")
            return
            
        items = []
        for w in self.app.project.walls:
            if isinstance(w, dict):
                name = w.get('name')
                net = float(w.get('net_area', 0.0) or w.get('net', 0.0) or 0.0)
            else:
                name = getattr(w, 'name', '')
                net = float(getattr(w, 'net_area', 0.0) or getattr(w, 'net', 0.0) or 0.0)
            
            if net > 0:
                items.append({'name': name, 'area': net})
                
        dialog = ItemSelectorDialog(self.app.root, f"Select Net Walls for {key.title()}", items, show_quantity=False, colors=self.app.colors)
        sel = dialog.show()
        if sel:
            from ...models.finish import FinishItem
            for s in sel:
                getattr(self.app.project, f"{key}_items").append(FinishItem(
                    description=s['item']['name'], area=s['total_area'], finish_type=key
                ))
            self.refresh_data()

    def deduct_openings(self, key):
        # Deduct doors/windows
        # Simplified: just ask which type
        choice = messagebox.askyesno("Deduct Openings", "Yes for Doors, No for Windows (Cancel to abort)")
        if choice is None: return # Cancel doesn't work well with yesno, but let's assume user picks one
        
        # Actually let's use a custom dialog or just do both?
        # Let's do a simple approach: Deduct ALL doors and windows? No, user might want control.
        # Let's just launch the selector for Doors first.
        
        openings = self.app.project.doors
        items = []
        for o in openings:
            if isinstance(o, dict):
                name = o.get('name')
                area = float(o.get('area', 0.0) or 0.0)
            else:
                name = getattr(o, 'name', '')
                area = float(getattr(o, 'area', 0.0) or 0.0)
            items.append({'name': f"Door: {name}", 'area': area})
            
        dialog = ItemSelectorDialog(self.app.root, "Select Doors to Deduct", items, show_quantity=True, colors=self.app.colors)
        sel = dialog.show()
        if sel:
            from ...models.finish import FinishItem
            for s in sel:
                getattr(self.app.project, f"{key}_items").append(FinishItem(
                    description=f"Deduction: {s['item']['name']}", area=-s['total_area'], finish_type=key
                ))
            self.refresh_data()

    def deduct_ceramic(self, key):
        # Deduct Wall + Ceiling ceramic zones
        zones = self.app.project.ceramic_zones
        deduct_area = 0.0
        for z in zones:
            if isinstance(z, dict):
                stype = z.get('surface_type', 'wall')
                area = float(z.get('area', 0.0) or 0.0)
            else:
                stype = getattr(z, 'surface_type', 'wall')
                area = float(getattr(z, 'area', 0.0) or 0.0)
            
            if stype in ['wall', 'ceiling']:
                deduct_area += area
                
        if deduct_area > 0:
            from ...models.finish import FinishItem
            getattr(self.app.project, f"{key}_items").append(FinishItem(
                description="Deduction: Ceramic Zones (Wall/Ceil)", area=-deduct_area, finish_type=key
            ))
            self.refresh_data()
            messagebox.showinfo("Deducted", f"Deducted {deduct_area:.2f} m² from {key}.")
        else:
            messagebox.showinfo("Info", "No wall/ceiling ceramic zones found.")

    def clear_items(self, key):
        if messagebox.askyesno("Clear", f"Clear all {key} items?"):
            getattr(self.app.project, f"{key}_items").clear()
            self.refresh_data()
            self.notify_data_changed()
