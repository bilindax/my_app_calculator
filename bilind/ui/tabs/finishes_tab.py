"""Finishes Tab Module
=====================
UI components for managing plaster, paint, and tile finish areas.
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING
from typing import Iterable, Tuple
from tkinter import messagebox, simpledialog

from .base_tab import BaseTab
from ...models.finish import FinishItem, CeramicZone
from ..dialogs.item_selector_dialog import ItemSelectorDialog

if TYPE_CHECKING:
    from bilind_main import BilindEnhanced


class FinishesTab(BaseTab):
    """Tab UI for finish calculations and tracking."""

    def __init__(self, parent: tk.Widget, app: 'BilindEnhanced'):
        super().__init__(parent, app)
        self.plaster_tree = None
        self.paint_tree = None
        self.tiles_tree = None
        self.plaster_label = None
        self.paint_label = None
        self.tiles_label = None
        self.ceramic_summary_label = None

    def refresh_data(self):
        """Refreshes all finish sections."""
        for finish_key in ('plaster', 'paint', 'tiles'):
            self._normalize_finish_storage(finish_key)
        self._refresh_ceramic_summary()
        self._refresh_section('plaster', self.plaster_tree, self.plaster_label)
        self._refresh_section('paint', self.paint_tree, self.paint_label)
        self._refresh_section('tiles', self.tiles_tree, self.tiles_label)

    def _refresh_ceramic_summary(self):
        """Update ceramic zones summary line for quick reference."""
        if not self.ceramic_summary_label:
            return

        zones = self.app.project.ceramic_zones
        if not zones:
            self.ceramic_summary_label.config(text="Ceramic zones: none defined yet")
            return

        totals = {}
        total_area = 0.0
        for zone in zones:
            if hasattr(zone, 'area'):
                area = float(zone.area)
                category = getattr(zone, 'category', 'Other')
            else:
                area = float(zone.get('area', 0.0) or 0.0)
                category = zone.get('category', 'Other')
            totals[category] = totals.get(category, 0.0) + area
            total_area += area

        ordered_categories = ['Kitchen', 'Bathroom', 'Other']
        breakdown_parts = []
        for cat in ordered_categories:
            area = totals.get(cat, 0.0)
            if area > 0:
                breakdown_parts.append(f"{cat}: {area:.2f} m²")
        for cat, area in totals.items():
            if cat not in ordered_categories and area > 0:
                breakdown_parts.append(f"{cat}: {area:.2f} m²")
        breakdown = " • ".join(breakdown_parts)
        summary_text = f"Ceramic zones total: {total_area:.2f} m²"
        if breakdown:
            summary_text += f" ({breakdown})"
        self.ceramic_summary_label.config(text=summary_text)

    def _refresh_section(self, key: str, tree: ttk.Treeview, label: ttk.Label):
        """Refreshes a single finish treeview and its total label."""
        if not tree or not label:
            return

        storage = getattr(self.app.project, f"{key}_items", [])
        tree.delete(*tree.get_children())
        
        # Get default waste percentage for this finish type
        waste_attr = f"{key}_waste_percentage"
        default_waste = getattr(self.app.project, waste_attr, 0.0)
        
        total_area = 0.0
        total_with_waste = 0.0
        
        for item in storage:
            area = item.area if hasattr(item, 'area') else item.get('area', 0.0)
            desc = item.description if hasattr(item, 'description') else item.get('desc', '-')
            
            # Calculate area with waste
            if hasattr(item, 'calculate_area_with_waste'):
                area_with_waste = item.calculate_area_with_waste(default_waste)
            else:
                # Fallback for legacy dicts
                area_with_waste = area * (1.0 + default_waste / 100.0)
            
            # Format negative deductions with a different color
            tags = ()
            if area < 0:
                tags = ('deduction',)
                tree.tag_configure('deduction', foreground=self.app.colors['danger'])

            tree.insert("", "end", values=(desc, f"{area:.2f}", f"{area_with_waste:.2f}"), tags=tags)
            total_area += area
            total_with_waste += area_with_waste
            
        waste_pct_text = f" (+{default_waste}% waste)" if default_waste > 0 else ""
        label.config(text=f"Net = {total_area:.2f} m² • With Waste = {total_with_waste:.2f} m²{waste_pct_text}")

    def create(self) -> tk.Frame:
        """Create and return the finishes tab frame."""
        container = tk.Frame(self.parent, bg=self.app.colors['bg_secondary'])

        self._create_header(
            container,
            "Wall Finishes Calculator",
            "Calculate plaster, paint, and tiles from room areas or wall perimeters."
        )

        self.ceramic_summary_label = ttk.Label(
            container,
            text="Ceramic zones: none defined yet",
            style='Metrics.TLabel'
        )
        self.ceramic_summary_label.pack(anchor=tk.W, padx=16, pady=(0, 8))

        # Scrollable content container so the Tiles section is always accessible
        scroll_container = tk.Frame(container, bg=self.app.colors['bg_secondary'])
        scroll_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(
            scroll_container,
            bg=self.app.colors['bg_secondary'],
            highlightthickness=0
        )
        vbar = ttk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        content = tk.Frame(canvas, bg=self.app.colors['bg_secondary'])
        canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_content_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        content.bind("<Configure>", _on_content_configure)

        # Basic mouse wheel support (Windows)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        content.bind_all('<MouseWheel>', _on_mousewheel)

        sections = [
            {
                'key': 'plaster',
                'title': "🏗️ Plaster",
                'tree_attr': 'plaster_tree',
                'label_attr': 'plaster_label',
                'pad_y': (4, 8)
            },
            {
                'key': 'paint',
                'title': "🎨 Paint",
                'tree_attr': 'paint_tree',
                'label_attr': 'paint_label',
                'pad_y': 8
            },
            {
                'key': 'tiles',
                'title': "🟦 Tiles",
                'tree_attr': 'tiles_tree',
                'label_attr': 'tiles_label',
                'pad_y': 8
            }
        ]

        for section in sections:
            self._create_finish_section(content, **section)

        self.refresh_data()
        return container

    def _create_header(self, parent: tk.Widget, title: str, subtitle: str) -> None:
        """Render the tab header."""
        hero = ttk.Frame(parent, style='Hero.TFrame', padding=(18, 20))
        hero.pack(fill=tk.X, padx=16, pady=(16, 8))

        ttk.Label(hero, text=title, style='HeroHeading.TLabel').pack(anchor=tk.W)
        ttk.Label(hero, text=subtitle, style='HeroSubheading.TLabel').pack(anchor=tk.W, pady=(6, 0))

    def _create_finish_section(
        self,
        parent: tk.Widget,
        key: str,
        title: str,
        tree_attr: str,
        label_attr: str,
        pad_y
    ) -> None:
        """Create a finish category section with controls and treeview."""
        frame = ttk.LabelFrame(parent, text=title, style='Card.TLabelframe', padding=(12, 10))
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=pad_y)

        # Button bar - Main actions
        btns = ttk.Frame(frame, style='Main.TFrame')
        btns.pack(fill=tk.X, pady=(0, 8))

        for text, command, style in [
            ("➕ Room Areas", lambda k=key: self.add_finish_from_source(k, 'rooms'), 'Accent.TButton'),
            ("📐 Room Walls", lambda k=key: self.add_walls_from_rooms(k), 'Accent.TButton'),
            ("🧱 Wall Net", lambda k=key: self.add_finish_from_source(k, 'walls'), 'Secondary.TButton'),
            ("🚪 Deduct Doors", lambda k=key: self.deduct_openings_from_finish(k, 'doors'), 'Warning.TButton'),
            ("🪟 Deduct Windows", lambda k=key: self.deduct_openings_from_finish(k, 'windows'), 'Warning.TButton'),
            ("➖ Deduct Ceramic", lambda k=key: self.deduct_ceramic_from_finish(k), 'Warning.TButton'),
            ("✍️ Manual", lambda k=key: self.add_finish_manual(k), 'Secondary.TButton'),
            ("✏️ Edit", lambda k=key: self.edit_finish_item(k), 'Secondary.TButton'),
            ("🗑️ Del", lambda k=key: self.delete_finish_item(k), 'Danger.TButton')
        ]:
            self.create_button(btns, text, command, style).pack(side=tk.LEFT, padx=3)

        # Extra actions for Tiles section: create ceramic floor zones from rooms
        if key == 'tiles':
            btns_floor = ttk.Frame(frame, style='Main.TFrame')
            btns_floor.pack(fill=tk.X, pady=(0, 8))
            self.create_button(
                btns_floor,
                "🟫 Floors: All Rooms",
                self.add_ceramic_floors_all_rooms,
                'Secondary.TButton'
            ).pack(side=tk.LEFT, padx=3)
            self.create_button(
                btns_floor,
                "🟫 Floors: Select Rooms",
                self.add_ceramic_floors_select_rooms,
                'Secondary.TButton'
            ).pack(side=tk.LEFT, padx=3)

        # Quick filters by room type
        btns2 = ttk.Frame(frame, style='Main.TFrame')
        btns2.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(btns2, text="🏠 By Room Type:", style='Body.TLabel').pack(side=tk.LEFT, padx=(0, 6))
        
        for text, room_types, source in [
            ("🚿 Wet Areas", ['Bathroom', 'Toilet/WC', 'Kitchen', 'Laundry Room'], 'walls'),
            ("🏠 Living Spaces", ['Living Room', 'Bedroom', 'Master Bedroom', 'Dining Room', 'Office/Study'], 'walls'),
            ("🌳 Outdoor", ['Balcony', 'Terrace'], 'walls'),
            ("🚪 Service", ['Hallway/Corridor', 'Entrance/Foyer', 'Storage/Closet', 'Utility Room'], 'walls')
        ]:
            self.create_button(
                btns2, text, 
                lambda k=key, types=room_types, src=source: self._add_finish_by_room_types(k, src, types), 
                'Secondary.TButton'
            ).pack(side=tk.LEFT, padx=3)

        # Treeview
        tree = ttk.Treeview(frame, columns=('Description', 'Area', 'With Waste'), show='headings', height=4)
        tree.heading('Description', text='Description')
        tree.heading('Area', text='Net Area (m²)')
        tree.heading('With Waste', text='With Waste (m²)')
        tree.column('Description', width=350)
        tree.column('Area', width=120, anchor=tk.CENTER)
        tree.column('With Waste', width=130, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        setattr(self, tree_attr, tree) # Store on self, not app
        
        # Apply modern styling enhancements
        if hasattr(self.app, 'enhance_treeview'):
            self.app.enhance_treeview(tree)

        label = ttk.Label(frame, text="Total = 0.00 m²", style='Metrics.TLabel')
        label.pack(anchor=tk.W, pady=(8, 0))
        setattr(self, label_attr, label) # Store on self, not app

    # === Ceramic Floors helpers ===
    def _room_iter_with_meta(self):
        for room in self.app.project.rooms:
            if isinstance(room, dict):
                name = room.get('name', 'Room')
                area = float(room.get('area', 0.0) or 0.0)
                perim = float(room.get('perim', 0.0) or 0.0)
                rtype = room.get('room_type', '[Not Set]')
            else:
                name = getattr(room, 'name', 'Room')
                area = float(getattr(room, 'area', 0.0) or 0.0)
                perim = float(getattr(room, 'perimeter', 0.0) or 0.0)
                rtype = getattr(room, 'room_type', '[Not Set]')
            yield name, area, perim, rtype

    def _categorize_room(self, room_type: str) -> str:
        rt = (room_type or '').lower()
        if any(k in rt for k in ['bath', 'toilet', 'wc']):
            return 'Bathroom'
        if 'kitchen' in rt:
            return 'Kitchen'
        return 'Other'

    def _ensure_unique_floor_zone(self, room_name: str, area: float, category: str):
        # For floor zones, store as perimeter=area, height=1.0 so zone.area == area
        # Remove any existing floor ceramic for this room first
        self.app.project.ceramic_zones = [
            z for z in self.app.project.ceramic_zones
            if not (
                ((z.get('surface_type') if isinstance(z, dict) else getattr(z, 'surface_type', '')).lower() == 'floor') and
                ((z.get('room_name') if isinstance(z, dict) else getattr(z, 'room_name', None)) == room_name)
            )
        ]
        
        # Add new floor ceramic zone
        zone = CeramicZone(
            name=f"Floor - {room_name}",
            category=category,
            perimeter=area,
            height=1.0,
            surface_type='floor',
            room_name=room_name
        )
        self.app.project.ceramic_zones.append(zone)

    def add_ceramic_floors_all_rooms(self):
        if not self.app.project.rooms:
            messagebox.showwarning("No Data", "No rooms available. Please pick rooms first.")
            return
        added = 0
        for name, area, _perim, rtype in self._room_iter_with_meta():
            if area > 0:
                self._ensure_unique_floor_zone(name, area, self._categorize_room(rtype))
                added += 1
        self.refresh_data()
        self.app.update_status(f"Floor ceramic zones updated for {added} room(s)", icon="✅")

    def add_ceramic_floors_select_rooms(self):
        if not self.app.project.rooms:
            messagebox.showwarning("No Data", "No rooms available. Please pick rooms first.")
            return
        items = []
        for name, area, _perim, rtype in self._room_iter_with_meta():
            if area > 0:
                items.append({'name': f"{name} ({rtype})", 'area': area, 'room_name': name, 'room_type': rtype})
        if not items:
            messagebox.showwarning("No Data", "No rooms with valid floor areas found.")
            return
        dialog = ItemSelectorDialog(self.app.root, "Select Rooms for Floor Ceramic", items, show_quantity=False, colors=self.app.colors)
        selected = dialog.show()
        if not selected:
            return
        for s in selected:
            rm = s['item']
            self._ensure_unique_floor_zone(rm['room_name'], rm['area'], self._categorize_room(rm.get('room_type')))
        self.refresh_data()
        self.app.update_status(f"Floor ceramic zones updated for {len(selected)} room(s)", icon="✅")

    def add_finish_from_source(self, key: str, source: str, room_type_filter: str = None):
        """Adds finish items from either room floor areas or net wall areas.
        
        Args:
            key: Finish type ('plaster', 'paint', 'tiles')
            source: Data source ('rooms' or 'walls')
            room_type_filter: Optional room type to filter by (e.g., 'Bathroom', 'Kitchen')
        """
        if source == 'rooms':
            if not self.app.project.rooms:
                messagebox.showwarning("No Data", "No rooms available. Please pick rooms first.")
                return
            
            # Prepare items for selector dialog with room types
            all_items = []
            for room in self.app.project.rooms:
                name = room.get('name') if isinstance(room, dict) else getattr(room, 'name', 'Room')
                area = float(room.get('area', 0.0) if isinstance(room, dict) else getattr(room, 'area', 0.0) or 0.0)
                room_type = room.get('room_type', '[Not Set]') if isinstance(room, dict) else getattr(room, 'room_type', '[Not Set]')
                
                # Apply room type filter if specified
                if room_type_filter and room_type != room_type_filter:
                    continue
                
                all_items.append({
                    'name': f"{name} ({room_type})",
                    'area': area,
                    'room_type': room_type
                })
            
            if not all_items:
                filter_msg = f" of type '{room_type_filter}'" if room_type_filter else ""
                messagebox.showwarning("No Data", f"No rooms{filter_msg} available.")
                return
            
            # Show selection dialog
            title = f"Select Rooms to Add ({len(all_items)} available)"
            if room_type_filter:
                title = f"Select {room_type_filter} Rooms ({len(all_items)} available)"
            
            dialog = ItemSelectorDialog(
                self.app.root,
                title,
                all_items,
                show_quantity=False,
                colors=self.app.colors
            )
            selected = dialog.show()
            
            if not selected:
                return
            
            items = [
                {'desc': s['item']['name'], 'area': s['total_area']}
                for s in selected
            ]
        elif source == 'walls':
            if not self.app.project.walls:
                messagebox.showwarning("No Data", "No walls available. Please pick walls first.")
                return
            items = []
            for wall in self.app.project.walls:
                net_area = getattr(wall, 'net_area', None)
                if net_area is None:
                    net_area = float(wall.get('net', 0.0) or 0.0) if isinstance(wall, dict) else 0.0
                try:
                    net_area = float(net_area)
                except (TypeError, ValueError):
                    net_area = 0.0
                if net_area > 0:
                    if isinstance(wall, dict):
                        name = wall.get('name', 'Wall')
                    else:
                        name = getattr(wall, 'name', 'Wall')
                    items.append({'desc': name, 'area': net_area})
        else:
            return

        storage = self._normalize_finish_storage(key)
        for item_data in items:
            self._append_finish_item(storage, key, item_data['desc'], item_data['area'])
        
        self.refresh_data()
        self.app.update_status(f"Added {len(items)} items from {source} to {key}", icon="✅")

    def add_walls_from_rooms(self, key: str, room_type_filter: str = None):
        """Calculates wall area from room perimeters and adds to a finish list.
        
        Args:
            key: Finish type ('plaster', 'paint', 'tiles')
            room_type_filter: Optional room type to filter by
        """
        if not self.app.project.rooms:
            messagebox.showwarning("No Data", "No rooms available to calculate wall areas from.")
            return

        try:
            height_str = simpledialog.askstring("Wall Height", "Enter wall height for all selected rooms (meters):", initialvalue="3.0")
            if not height_str:
                return
            height = float(height_str)
            if height <= 0:
                raise ValueError("Height must be positive.")
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Input", "Please enter a valid positive number for the height.")
            return

        # Prepare items for selector dialog with room types
        all_items = []
        for room in self.app.project.rooms:
            name = room.get('name') if isinstance(room, dict) else getattr(room, 'name', 'Room')
            perimeter = float(room.get('perim', 0.0) if isinstance(room, dict) else getattr(room, 'perimeter', 0.0) or 0.0)
            room_type = room.get('room_type', '[Not Set]') if isinstance(room, dict) else getattr(room, 'room_type', '[Not Set]')
            
            # Apply room type filter if specified
            if room_type_filter and room_type != room_type_filter:
                continue
            
            if perimeter > 0:
                all_items.append({
                    'name': f"{name} ({room_type})",
                    'area': perimeter * height,
                    'perimeter': perimeter,
                    'room_type': room_type
                })
        
        if not all_items:
            filter_msg = f" of type '{room_type_filter}'" if room_type_filter else ""
            messagebox.showwarning("No Data", f"No rooms{filter_msg} with valid perimeters found.")
            return
        
        # Show selection dialog
        title = f"Select Rooms for Wall Calculation ({len(all_items)} available)"
        if room_type_filter:
            title = f"Select {room_type_filter} Rooms for Walls ({len(all_items)} available)"
        
        dialog = ItemSelectorDialog(
            self.app.root,
            title,
            all_items,
            show_quantity=False,
            colors=self.app.colors
        )
        selected = dialog.show()
        
        if not selected:
            return
        
        storage = self._normalize_finish_storage(key)
        for s in selected:
            item = s['item']
            desc = f"Walls: {item['name']} ({item['perimeter']:.2f}m × {height:.2f}m)"
            self._append_finish_item(storage, key, desc, s['total_area'])
        
        self.refresh_data()
        self.app.update_status(f"Added wall areas from {len(selected)} rooms to {key}", icon="✅")

    def _add_finish_by_room_types(self, key: str, source: str, room_types: list):
        """Add finishes by iterating through multiple room types.
        
        This is a convenience method for quick-action buttons that target
        common room groupings (wet areas, living spaces, outdoor, etc.).
        
        Args:
            key: Finish type ('plaster', 'paint', 'tiles')
            source: Data source ('rooms' or 'walls')
            room_types: List of room types to include (e.g., ['Bathroom', 'Kitchen'])
        """
        added_count = 0
        
        for room_type in room_types:
            # Check if any rooms of this type exist
            matching_rooms = [
                r for r in self.app.project.rooms
                if (r.get('room_type') if isinstance(r, dict) else getattr(r, 'room_type', '[Not Set]')) == room_type
            ]
            
            if not matching_rooms:
                continue  # Skip if no rooms of this type
            
            # Add based on source
            if source == 'rooms':
                self.add_finish_from_source(key, 'rooms', room_type_filter=room_type)
                added_count += len(matching_rooms)
            elif source == 'walls':
                self.add_walls_from_rooms(key, room_type_filter=room_type)
                added_count += len(matching_rooms)
        
        if added_count == 0:
            room_types_str = ', '.join(room_types)
            messagebox.showinfo("No Matches", f"No rooms found matching types: {room_types_str}")
        else:
            self.app.update_status(f"Added {added_count} room(s) from selected types to {key}", icon="✅")

    def add_finish_manual(self, key: str):
        """Manually add a finish item."""
        dialog = self.app._finish_item_dialog("Add Manual Finish Item")
        if dialog:
            storage = self._normalize_finish_storage(key)
            self._append_finish_item(storage, key, dialog['desc'], dialog['area'])
            self.refresh_data()
            self.app.update_status(f"Added manual item to {key}", icon="✍️")

    def edit_finish_item(self, key: str):
        """Edit a selected finish item."""
        tree = getattr(self, f"{key}_tree")
        storage = self._normalize_finish_storage(key)
        
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to edit.")
            return
            
        idx = tree.index(selection[0])
        item = storage[idx]
        
        desc_default = item.description if hasattr(item, 'description') else item.get('desc', '')
        area_default = item.area if hasattr(item, 'area') else item.get('area', 0.0)
        dialog = self.app._finish_item_dialog("Edit Finish Item", defaults={'desc': desc_default, 'area': area_default})
        if dialog:
            if hasattr(item, 'description'):
                item.description = dialog['desc']
                item.area = dialog['area']
            else:
                item['desc'] = dialog['desc']
                item['area'] = dialog['area']
            self.refresh_data()
            self.app.update_status(f"Edited item in {key}", icon="✏️")

    def delete_finish_item(self, key: str):
        """Delete a selected finish item."""
        tree = getattr(self, f"{key}_tree")
        storage = self._normalize_finish_storage(key)

        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to delete.")
            return

        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected item?"):
            indices = sorted([tree.index(i) for i in selection], reverse=True)
            for idx in indices:
                del storage[idx]
            self.refresh_data()
            self.app.update_status(f"Deleted {len(selection)} item(s) from {key}", icon="🗑️")

    def deduct_ceramic_from_finish(self, key: str):
        """Deducts the total area of all ceramic zones from a finish list."""
        if not self.app.project.ceramic_zones:
            messagebox.showinfo("No Data", "No ceramic zones have been defined to deduct.\n\nGo to Materials tab → Ceramic Planner to add ceramic zones first.")
            return

        """Deduct ceramic area from a finish list, respecting wall/ceiling/floor types.

        Logic:
        - Plaster/Paint: deduct only *wall + ceiling* ceramic (لا نطرح سيراميك الأرضية من الدهان).
        - Tiles: deduct only *floor* ceramic (سيراميك الأرضية) من بند البلاط إذا لزم.
        """
        zones = self.app.project.ceramic_zones
        if not zones:
            messagebox.showinfo(
                "No Data",
                "No ceramic zones have been defined to deduct.\n\nGo to Materials tab → Ceramic Planner to add ceramic zones first."
            )
            return

        wall_ceiling_total = 0.0
        floor_total = 0.0

        for zone in zones:
            if hasattr(zone, 'surface_type'):
                surface = getattr(zone, 'surface_type', 'wall') or 'wall'
                area_val = getattr(zone, 'area', None)
                if area_val is None:
                    # Fallback when zone stores perimeter/height only
                    perim = getattr(zone, 'perimeter', 0.0) or 0.0
                    height = getattr(zone, 'height', 0.0) or 0.0
                    area_val = perim * height
            else:
                surface = (zone.get('surface_type') or 'wall') if isinstance(zone, dict) else 'wall'
                if isinstance(zone, dict):
                    if 'area' in zone:
                        area_val = zone.get('area', 0.0) or 0.0
                    else:
                        perim = zone.get('perimeter', 0.0) or 0.0
                        height = zone.get('height', 0.0) or 0.0
                        area_val = perim * height
                else:
                    area_val = 0.0

            try:
                area = float(area_val or 0.0)
            except (TypeError, ValueError):
                area = 0.0

            surface_key = str(surface).lower()
            if surface_key.startswith('floor'):
                floor_total += area
            elif surface_key.startswith('ceil'):
                wall_ceiling_total += area
            else:
                wall_ceiling_total += area

        if key in ('plaster', 'paint'):
            deduct_area = wall_ceiling_total
        elif key == 'tiles':
            deduct_area = floor_total
        else:
            deduct_area = wall_ceiling_total + floor_total

        if deduct_area <= 0:
            messagebox.showinfo("No Area", "Ceramic area for this finish type is zero. Nothing to deduct.")
            return

        storage = self._normalize_finish_storage(key)
        label = "Deduction: Ceramic wall/ceiling" if key in ('plaster', 'paint') else "Deduction: Ceramic floor"
        self._append_finish_item(storage, key, label, -deduct_area)
        self.refresh_data()

        if hasattr(self.app, 'material_estimator_tab'):
            self.app.material_estimator_tab.refresh_data()

        self.app.update_status(f"Deducted {deduct_area:.2f} m² from {key}", icon="➖")
    
    def deduct_openings_from_finish(self, key: str, opening_type: str):
        """
        Deduct door or window areas from a finish list with selection and quantity multiplier.
        
        Args:
            key: Finish type ('plaster', 'paint', 'tiles')
            opening_type: 'doors' or 'windows'
        """
        # Get openings list
        openings = self.app.project.doors if opening_type == 'doors' else self.app.project.windows
        
        if not openings:
            type_name = "Doors" if opening_type == 'doors' else "Windows"
            messagebox.showwarning("No Data", f"No {type_name.lower()} available. Please pick {type_name.lower()} first.")
            return
        
        # Prepare items for selector dialog
        all_items = []
        for opening in openings:
            if hasattr(opening, 'name'):
                name = opening.name
                area = opening.area
                qty = opening.quantity
            else:
                name = opening.get('name', 'Opening')
                area = opening.get('area', 0.0)
                qty = opening.get('qty', 1)
            
            all_items.append({
                'name': name,
                'area': area,
                'qty': qty
            })
        
        # Show selection dialog with quantity multipliers
        type_name = "Doors" if opening_type == 'doors' else "Windows"
        dialog = ItemSelectorDialog(
            self.app.root,
            f"Select {type_name} to Deduct",
            all_items,
            show_quantity=True,  # Enable quantity multipliers
            colors=self.app.colors
        )
        selected = dialog.show()
        
        if not selected:
            return
        
        # Add deductions
        storage = self._normalize_finish_storage(key)
        total_deducted = 0.0
        
        for s in selected:
            item = s['item']
            qty = s['qty']
            area = s['total_area']
            
            # Create descriptive text
            if qty > 1:
                desc = f"Deduction: {item['name']} (×{qty})"
            else:
                desc = f"Deduction: {item['name']}"
            
            self._append_finish_item(storage, key, desc, -area)
            total_deducted += area
        
        self.refresh_data()
        self.app.update_status(
            f"Deducted {len(selected)} {type_name.lower()} ({total_deducted:.2f} m²) from {key}",
            icon="➖"
        )

    # === Helpers ===

    def _normalize_finish_storage(self, key: str) -> list[FinishItem]:
        """Ensure finish collections contain FinishItem objects."""
        storage = getattr(self.app.project, f"{key}_items")
        if all(isinstance(item, FinishItem) for item in storage):
            return storage

        normalized: list[FinishItem] = []
        for item in storage:
            if isinstance(item, FinishItem):
                normalized.append(item)
            elif isinstance(item, dict):
                desc = item.get('desc', '')
                try:
                    area = float(item.get('area', 0.0) or 0.0)
                except (TypeError, ValueError):
                    area = 0.0
                try:
                    normalized.append(FinishItem(description=desc, area=area, finish_type=key))
                except ValueError:
                    continue
            else:
                # Unsupported type; skip but log for debugging
                print(f"[WARN] Skipping unsupported finish item type: {type(item)}")
        storage.clear()
        storage.extend(normalized)
        return storage

    def _append_finish_item(self, storage, key: str, description: str, area: float) -> None:
        """Append a FinishItem to storage, coercing to float and handling errors."""
        try:
            area_value = float(area)
        except (TypeError, ValueError):
            area_value = 0.0
        try:
            storage.append(FinishItem(description=description, area=area_value, finish_type=key))
        except ValueError:
            # Invalid finish type fallback to dict to avoid crash
            storage.append({'desc': description, 'area': area_value})

    def _iter_room_metrics(self) -> Iterable[Tuple[str, float, float]]:
        """Yield room name, area, and perimeter regardless of legacy format."""
        for room in self.app.project.rooms:
            if hasattr(room, 'name'):
                name = getattr(room, 'name', 'Room')
                area = getattr(room, 'area', 0.0) or 0.0
                perimeter = getattr(room, 'perimeter', 0.0) or 0.0
            elif isinstance(room, dict):
                name = room.get('name', 'Room')
                area = room.get('area', room.get('Area', 0.0)) or 0.0
                perimeter = room.get('perim', room.get('perimeter', 0.0)) or 0.0
            else:
                continue
            try:
                area_value = float(area)
            except (TypeError, ValueError):
                area_value = 0.0
            try:
                perim_value = float(perimeter)
            except (TypeError, ValueError):
                perim_value = 0.0
            yield name, area_value, perim_value
