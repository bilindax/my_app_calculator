"""
Ceramic & Stone Tab Module
==========================
Unified tab for all hard finishes: Ceramic (Floors/Walls), Stone, and Marble.
Merges functionality from the old Materials Tab and Tiles section.
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING
from tkinter import messagebox, simpledialog

from .base_tab import BaseTab
from ...models.finish import CeramicZone
from ..dialogs.item_selector_dialog import ItemSelectorDialog

if TYPE_CHECKING:
    from bilind_main import BilindEnhanced


class CeramicTab(BaseTab):
    """
    Unified tab for Ceramic, Stone, and Marble.
    
    Sections:
    1. Kitchen & Bath Planner (Ceramic Zones)
    2. Floor Tiling (General Rooms)
    3. Stone & Marble Ledger (Sills, Thresholds)
    """
    
    def __init__(self, parent: tk.Widget, app: 'BilindEnhanced'):
        super().__init__(parent, app)
        self.ceramic_tree = None
        self.ceramic_totals_label = None
        self.tiles_tree = None
        self.tiles_label = None
        self.stone_tree = None
        self.stone_metrics_label = None

    def create(self) -> tk.Frame:
        """Create and return the tab frame."""
        container = tk.Frame(self.parent, bg=self.app.colors['bg_secondary'])
        
        # Header
        self._create_header(
            container,
            "Ceramic & Stone Works",
            "Manage all hard finishes: Kitchen/Bath zones, Floor Tiling, and Stone works."
        )
        
        # Scrollable content area
        canvas = tk.Canvas(container, bg=self.app.colors['bg_secondary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.app.colors['bg_secondary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # 1. Ceramic Zones (Kitchen/Bath)
        self._create_ceramic_zones_section(scrollable_frame)
        
        # 2. Floor Tiling (General)
        self._create_floor_tiling_section(scrollable_frame)
        
        # 3. Stone Ledger
        self._create_stone_section(scrollable_frame)

        self.refresh_data()
        return container

    def _create_header(self, parent, title: str, subtitle: str):
        hero = ttk.Frame(parent, style='Hero.TFrame', padding=(18, 20))
        hero.pack(fill=tk.X, padx=16, pady=(16, 12))
        ttk.Label(hero, text=title, style='HeroHeading.TLabel').pack(anchor=tk.W)
        ttk.Label(hero, text=subtitle, style='HeroSubheading.TLabel').pack(anchor=tk.W, pady=(6, 0))

    # --- Section 1: Ceramic Zones ---
    def _create_ceramic_zones_section(self, parent):
        frame = ttk.LabelFrame(parent, text="🚿 Kitchen & Bath Zones", style='Card.TLabelframe', padding=(14, 12))
        frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        # Toolbar (split into two rows so actions are always visible)
        btn_bar = ttk.Frame(frame, style='Main.TFrame')
        btn_bar.pack(fill=tk.X, pady=(0, 6))

        btn_bar2 = ttk.Frame(frame, style='Main.TFrame')
        btn_bar2.pack(fill=tk.X, pady=(0, 10))

        for text, command, style in [
            ("🚿 حمام كامل", self.preset_bathroom_full, 'Accent.TButton'),
            ("🚽 تواليت...", self.preset_toilet, 'Secondary.TButton'),
            ("🍳 مطبخ...", self.preset_kitchen, 'Secondary.TButton'),
            ("🪟 بلكون...", self.preset_balcony, 'Secondary.TButton'),
            ("⚡ سيراميك سريع", self.quick_ceramic_wizard, 'Success.TButton'),
            ("➕ Add Zone", self.add_ceramic_zone, 'Accent.TButton'),
            ("✏️ Edit", self.edit_ceramic_zone, 'Secondary.TButton'),
            ("🗑️ Delete", self.delete_ceramic_zone, 'Danger.TButton')
        ]:
            self.create_button(btn_bar, text, command, style).pack(side=tk.LEFT, padx=4)

        for text, command, style in [
            ("🚫 حذف سيراميك الغرفة", self.delete_room_ceramic, 'Warning.TButton'),
            ("🧹 حذف كل السيراميك", self.delete_all_ceramic, 'Danger.TButton')
        ]:
            self.create_button(btn_bar2, text, command, style).pack(side=tk.LEFT, padx=4)
            
        # Treeview
        columns = ('Name', 'Category', 'Type', 'Perimeter', 'Height', 'Area', 'Adhesive', 'Grout')
        self.ceramic_tree = ttk.Treeview(frame, columns=columns, show='headings', height=5)
        
        col_conf = [
            ('Name', 'Zone Name', 140, tk.W),
            ('Category', 'Category', 90, tk.CENTER),
            ('Type', 'Type', 60, tk.CENTER),
            ('Perimeter', 'Perim (m)', 80, tk.CENTER),
            ('Height', 'H (m)', 60, tk.CENTER),
            ('Area', 'Area (m²)', 80, tk.CENTER),
            ('Adhesive', 'Adhesive', 80, tk.CENTER),
            ('Grout', 'Grout', 80, tk.CENTER)
        ]
        for col, txt, w, anchor in col_conf:
            self.ceramic_tree.heading(col, text=txt)
            self.ceramic_tree.column(col, width=w, anchor=anchor)
            
        self.ceramic_tree.pack(fill=tk.X, expand=True)
        
        self.ceramic_totals_label = ttk.Label(frame, text="No zones defined", style='Metrics.TLabel')
        self.ceramic_totals_label.pack(anchor=tk.W, pady=(8, 0))

    # --- Presets ---
    def _classify_rooms(self):
        """Return mapping of rtype -> list of rooms."""
        try:
            from bilind.ui.tabs.helpers.auto_presets import classify_room_type
        except Exception:
            classify_room_type = None

        by_type = {'kitchen': [], 'bath': [], 'toilet': [], 'balcony': []}
        for room in (self.app.project.rooms or []):
            rname = getattr(room, 'name', None) if not isinstance(room, dict) else room.get('name')
            rname = str(rname or '')
            if classify_room_type:
                rtype = classify_room_type(rname, room)
            else:
                low = rname.lower()
                if 'مطبخ' in rname or 'kitchen' in low:
                    rtype = 'kitchen'
                elif 'تواليت' in rname or 'wc' in low or 'toilet' in low:
                    rtype = 'toilet'
                elif 'حمام' in rname or 'bath' in low:
                    rtype = 'bath'
                elif 'بلكون' in rname or 'شرفة' in rname or 'balcony' in low:
                    rtype = 'balcony'
                else:
                    rtype = ''

            if rtype in by_type:
                by_type[rtype].append(room)
        return by_type

    def _room_name(self, room) -> str:
        return str(getattr(room, 'name', '') if not isinstance(room, dict) else room.get('name', '') or '')

    def _room_area(self, room) -> float:
        try:
            return float(getattr(room, 'area', 0.0) if not isinstance(room, dict) else room.get('area', 0.0) or 0.0)
        except Exception:
            return 0.0

    def _room_wall_height(self, room) -> float:
        try:
            h = getattr(room, 'wall_height', None) if not isinstance(room, dict) else room.get('wall_height', None)
            if h is None:
                h = getattr(self.app.project, 'default_wall_height', 3.0)
            return float(h or 3.0)
        except Exception:
            return float(getattr(self.app.project, 'default_wall_height', 3.0) or 3.0)

    def _iter_room_walls(self, room):
        walls = getattr(room, 'walls', None) if not isinstance(room, dict) else room.get('walls')
        return list(walls or [])

    def _wall_name(self, wall, idx: int) -> str:
        return str(getattr(wall, 'name', '') if not isinstance(wall, dict) else wall.get('name', '') or f"Wall {idx+1}")

    def _wall_length(self, wall) -> float:
        try:
            return float(getattr(wall, 'length', 0.0) if not isinstance(wall, dict) else wall.get('length', 0.0) or 0.0)
        except Exception:
            return 0.0

    def _delete_room_zones(self, room_name: str, surfaces: set[str]) -> None:
        zones = self.app.project.ceramic_zones or []
        kept = []
        for z in zones:
            z_room = z.get('room_name') if isinstance(z, dict) else getattr(z, 'room_name', '')
            z_surface = z.get('surface_type', 'wall') if isinstance(z, dict) else getattr(z, 'surface_type', 'wall')
            if str(z_room or '') == str(room_name) and str(z_surface or 'wall') in surfaces:
                continue
            kept.append(z)
        self.app.project.ceramic_zones = kept

    def _set_wall_ceramic_fields(self, room, height: float) -> None:
        walls = self._iter_room_walls(room)
        for w in walls:
            ln = self._wall_length(w)
            area = ln * height
            if isinstance(w, dict):
                w['ceramic_height'] = height
                w['ceramic_area'] = area
                w['ceramic_surface'] = 'سيراميك'
            else:
                setattr(w, 'ceramic_height', height)
                setattr(w, 'ceramic_area', area)
                setattr(w, 'ceramic_surface', 'سيراميك')

    def _add_wall_zones_for_room(self, room, height: float, category: str, label: str) -> int:
        from bilind.models.finish import CeramicZone
        room_name = self._room_name(room)
        walls = self._iter_room_walls(room)
        created = 0

        if walls:
            self._set_wall_ceramic_fields(room, height)
            for i, w in enumerate(walls):
                ln = self._wall_length(w)
                if ln <= 0:
                    continue
                wname = self._wall_name(w, i)
                self.app.project.ceramic_zones.append(
                    CeramicZone(
                        name=f"{label} - {room_name} - جدار {i+1}",
                        category=category,
                        perimeter=ln,
                        height=float(height),
                        surface_type='wall',
                        room_name=room_name,
                        wall_name=wname,
                    )
                )
                created += 1
            return created

        # Fallback: room has no explicit walls, create one whole-room wall zone
        perim = getattr(room, 'perimeter', None) if not isinstance(room, dict) else room.get('perimeter', None)
        if perim is None:
            perim = getattr(room, 'perim', 0.0) if not isinstance(room, dict) else room.get('perim', 0.0)
        try:
            perim = float(perim or 0.0)
        except Exception:
            perim = 0.0
        if perim > 0:
            self.app.project.ceramic_zones.append(
                CeramicZone.for_wall(
                    perimeter=perim,
                    height=float(height),
                    room_name=room_name,
                    category=category,
                    name=f"{label} - {room_name}",
                )
            )
            created += 1
        return created

    def _add_floor_and_ceiling_for_room(self, room, category: str, label: str) -> int:
        from bilind.models.finish import CeramicZone
        room_name = self._room_name(room)
        area = self._room_area(room)
        if area <= 0:
            return 0
        z_floor = CeramicZone.for_floor(area=area, room_name=room_name, category=category, name=f"{label} أرضية - {room_name}")
        z_ceil = CeramicZone.for_floor(area=area, room_name=room_name, category=category, name=f"{label} سقف - {room_name}")
        z_ceil.surface_type = 'ceiling'
        self.app.project.ceramic_zones.extend([z_floor, z_ceil])
        return 2

    def _finalize_preset(self, affected_rooms: list) -> None:
        for room in affected_rooms:
            try:
                if hasattr(self.app, '_recompute_room_finish'):
                    self.app._recompute_room_finish(room)
            except Exception:
                pass
        try:
            if hasattr(self.app, 'refresh_rooms'):
                self.app.refresh_rooms()
        except Exception:
            pass
        self.refresh_data()
        self.notify_data_changed()

    def preset_bathroom_full(self):
        """Bathrooms: walls full height + floor + ceiling."""
        by_type = self._classify_rooms()
        rooms = by_type.get('bath', [])
        if not rooms:
            messagebox.showinfo("Info", "لا يوجد حمامات.")
            return
        names = ', '.join(self._room_name(r) for r in rooms[:6])
        if len(rooms) > 6:
            names += f" ... (+{len(rooms)-6})"
        if not messagebox.askyesno("تأكيد", f"تطبيق حمام كامل (جدران+أرض+سقف) على {len(rooms)} حمام؟\n\n{names}"):
            return

        affected = []
        for room in rooms:
            rname = self._room_name(room)
            self._delete_room_zones(rname, {'wall', 'floor', 'ceiling'})
            h = self._room_wall_height(room)
            self._add_wall_zones_for_room(room, h, category='Bathroom', label='حمام')
            self._add_floor_and_ceiling_for_room(room, category='Bathroom', label='حمام')
            affected.append(room)

        self._finalize_preset(affected)
        self.app.update_status(f"✅ حمام كامل: تم تطبيقه على {len(affected)} حمام", icon="🚿")

    def preset_toilet(self):
        """Toilets: full (walls+floor+ceiling) OR walls-only with a chosen height."""
        by_type = self._classify_rooms()
        rooms = by_type.get('toilet', [])
        if not rooms:
            messagebox.showinfo("Info", "لا يوجد تواليت.")
            return

        full = messagebox.askyesno("تواليت", "هل تريد تواليت كامل (جدران + أرض + سقف)؟\n\nYES = كامل\nNO = جدران فقط")
        height = None
        if not full:
            height = simpledialog.askfloat("تواليت - ارتفاع الجدران", "أدخل ارتفاع سيراميك الجدران (م):", initialvalue=1.6, minvalue=0.1)
            if height is None:
                return

        names = ', '.join(self._room_name(r) for r in rooms[:6])
        if len(rooms) > 6:
            names += f" ... (+{len(rooms)-6})"
        title = "تواليت كامل" if full else f"تواليت جدران فقط ({height:.2f}م)"
        if not messagebox.askyesno("تأكيد", f"{title} على {len(rooms)} تواليت؟\n\n{names}"):
            return

        affected = []
        for room in rooms:
            rname = self._room_name(room)
            if full:
                self._delete_room_zones(rname, {'wall', 'floor', 'ceiling'})
                h = self._room_wall_height(room)
                self._add_wall_zones_for_room(room, h, category='Toilet', label='تواليت')
                self._add_floor_and_ceiling_for_room(room, category='Toilet', label='تواليت')
            else:
                self._delete_room_zones(rname, {'wall'})
                self._add_wall_zones_for_room(room, float(height), category='Toilet', label='تواليت')
            affected.append(room)

        self._finalize_preset(affected)
        self.app.update_status(f"✅ {title}: تم تطبيقه على {len(affected)} تواليت", icon="🚽")

    def preset_kitchen(self):
        """Kitchens: walls-only with a chosen height (default 1.6m)."""
        by_type = self._classify_rooms()
        rooms = by_type.get('kitchen', [])
        if not rooms:
            messagebox.showinfo("Info", "لا يوجد مطابخ.")
            return

        height = simpledialog.askfloat("مطبخ - ارتفاع الجدران", "أدخل ارتفاع سيراميك الجدران (م):", initialvalue=1.6, minvalue=0.1)
        if height is None:
            return

        names = ', '.join(self._room_name(r) for r in rooms[:6])
        if len(rooms) > 6:
            names += f" ... (+{len(rooms)-6})"
        if not messagebox.askyesno("تأكيد", f"تطبيق مطبخ (جدران فقط) بارتفاع {height:.2f}م على {len(rooms)} مطبخ؟\n\n{names}"):
            return

        affected = []
        for room in rooms:
            rname = self._room_name(room)
            self._delete_room_zones(rname, {'wall'})
            self._add_wall_zones_for_room(room, float(height), category='Kitchen', label='مطبخ')
            affected.append(room)

        self._finalize_preset(affected)
        self.app.update_status(f"✅ مطبخ جدران ({height:.2f}م): تم تطبيقه على {len(affected)} مطبخ", icon="🍳")

    def preset_balcony(self):
        """Balconies: walls-only with chosen height; optional floor."""
        by_type = self._classify_rooms()
        rooms = by_type.get('balcony', [])
        if not rooms:
            messagebox.showinfo("Info", "لا يوجد بلكونات/شرفات.")
            return

        height = simpledialog.askfloat(
            "بلكون - ارتفاع الجدران",
            "أدخل ارتفاع سيراميك جدران البلكون (م):",
            initialvalue=1.6,
            minvalue=0.1,
        )
        if height is None:
            return

        include_floor = messagebox.askyesno("بلكون", "هل تريد إضافة سيراميك أرضية للبلكون أيضاً؟")

        names = ', '.join(self._room_name(r) for r in rooms[:6])
        if len(rooms) > 6:
            names += f" ... (+{len(rooms)-6})"
        title = f"بلكون جدران ({height:.2f}م)" + (" + أرض" if include_floor else "")
        if not messagebox.askyesno("تأكيد", f"تطبيق {title} على {len(rooms)} بلكون؟\n\n{names}"):
            return

        affected = []
        for room in rooms:
            rname = self._room_name(room)
            surfaces = {'wall', 'floor'} if include_floor else {'wall'}
            self._delete_room_zones(rname, surfaces)
            self._add_wall_zones_for_room(room, float(height), category='Balcony', label='بلكون')

            if include_floor:
                area = self._room_area(room)
                if area > 0:
                    from bilind.models.finish import CeramicZone
                    self.app.project.ceramic_zones.append(
                        CeramicZone.for_floor(
                            area=area,
                            room_name=rname,
                            category='Balcony',
                            name=f"بلكون أرضية - {rname}",
                        )
                    )

            affected.append(room)

        self._finalize_preset(affected)
        self.app.update_status(f"✅ {title}: تم تطبيقه على {len(affected)} بلكون", icon="🪟")

    # --- Section 2: Floor Tiling ---
    def _create_floor_tiling_section(self, parent):
        frame = ttk.LabelFrame(parent, text="🟦 General Floor Tiling", style='Card.TLabelframe', padding=(14, 12))
        frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        # Toolbar
        btn_bar = ttk.Frame(frame, style='Main.TFrame')
        btn_bar.pack(fill=tk.X, pady=(0, 10))
        
        for text, command, style in [
            ("➕ From Rooms", self.add_tiles_from_rooms, 'Accent.TButton'),
            ("✍️ Manual", self.add_tiles_manual, 'Secondary.TButton'),
            ("➖ Deduct Ceramic", self.deduct_ceramic_from_tiles, 'Warning.TButton'),
            ("🗑️ Clear", self.clear_tiles, 'Danger.TButton')
        ]:
            self.create_button(btn_bar, text, command, style).pack(side=tk.LEFT, padx=4)

        # Treeview
        self.tiles_tree = ttk.Treeview(frame, columns=('Desc', 'Area', 'Waste'), show='headings', height=5)
        self.tiles_tree.heading('Desc', text='Description')
        self.tiles_tree.heading('Area', text='Net Area (m²)')
        self.tiles_tree.heading('Waste', text='With Waste (m²)')
        self.tiles_tree.column('Desc', width=300)
        self.tiles_tree.column('Area', width=100, anchor=tk.CENTER)
        self.tiles_tree.column('Waste', width=100, anchor=tk.CENTER)
        self.tiles_tree.pack(fill=tk.X, expand=True)
        
        self.tiles_label = ttk.Label(frame, text="Total: 0.00 m²", style='Metrics.TLabel')
        self.tiles_label.pack(anchor=tk.W, pady=(8, 0))

    # --- Section 3: Stone Ledger ---
    def _create_stone_section(self, parent):
        frame = ttk.LabelFrame(parent, text="🪨 Stone & Marble Ledger", style='Card.TLabelframe', padding=(14, 12))
        frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        columns = ('Name', 'Kind', 'Type', 'Qty', 'Stone', 'Area')
        self.stone_tree = ttk.Treeview(frame, columns=columns, show='headings', height=5)
        
        col_conf = [
            ('Name', 'Name', 110, tk.W),
            ('Kind', 'Kind', 80, tk.CENTER),
            ('Type', 'Material', 100, tk.W),
            ('Qty', 'Qty', 60, tk.CENTER),
            ('Stone', 'Length (lm)', 100, tk.CENTER),
            ('Area', 'Area (m²)', 100, tk.CENTER)
        ]
        for col, txt, w, anchor in col_conf:
            self.stone_tree.heading(col, text=txt)
            self.stone_tree.column(col, width=w, anchor=anchor)
            
        self.stone_tree.pack(fill=tk.X, expand=True)
        
        self.stone_metrics_label = ttk.Label(frame, text="No stone items", style='Metrics.TLabel')
        self.stone_metrics_label.pack(anchor=tk.W, pady=(8, 0))

    # --- Logic & Refresh ---
    def refresh_data(self):
        # CRITICAL: Normalize ceramic zones to sync with room walls BEFORE displaying
        # This ensures perimeter/area/adhesive values match current wall data
        self._sync_ceramic_with_walls()
        
        self._refresh_ceramic_zones()
        self._refresh_tiles()
        self._refresh_stone()
    
    def _sync_ceramic_with_walls(self):
        """
        Sync ceramic zones with room walls:
        1. Run normalizer to update perimeter from wall.length
        2. Remove orphan zones (zones referencing non-existent walls)
        3. Recalculate area = perimeter × height
        """
        try:
            from ...calculations.ceramic_zone_normalizer import normalize_ceramic_wall_zones
            
            # First, remove orphan ceramic zones (walls that no longer exist)
            self._remove_orphan_ceramic_zones()
            
            # Then normalize remaining zones to match wall lengths
            normalize_ceramic_wall_zones(self.app.project)
            
        except Exception as e:
            print(f"[CeramicTab] Sync error: {e}")
    
    def _remove_orphan_ceramic_zones(self):
        """Remove ceramic zones that reference walls that no longer exist."""
        zones = self.app.project.ceramic_zones
        if not zones:
            return
        
        import re
        
        # Build a map of room -> wall numbers
        room_wall_map = {}
        for room in self.app.project.rooms or []:
            if isinstance(room, dict):
                room_name = room.get('name', '')
                walls = room.get('walls', []) or []
            else:
                room_name = getattr(room, 'name', '')
                walls = getattr(room, 'walls', []) or []
            
            wall_nums = set()
            for w in walls:
                w_name = w.get('name', '') if isinstance(w, dict) else getattr(w, 'name', '')
                # Extract wall number from name like "جدار 1" or "Wall 1"
                m = re.search(r'(\d+)', str(w_name))
                if m:
                    wall_nums.add(int(m.group(1)))
            
            room_wall_map[room_name] = wall_nums
        
        # Filter out orphan zones
        valid_zones = []
        removed = 0
        
        for z in zones:
            if isinstance(z, dict):
                z_name = z.get('name', '')
                z_room = z.get('room_name', '')
                surface = z.get('surface_type', 'wall')
            else:
                z_name = getattr(z, 'name', '')
                z_room = getattr(z, 'room_name', '')
                surface = getattr(z, 'surface_type', 'wall')
            
            # Only check wall zones
            if surface != 'wall':
                valid_zones.append(z)
                continue
            
            # If room_name is empty, try to extract from zone name
            # Pattern: "سيراميك - ROOM_NAME - جدار N" or "[Type] Wall N - ROOM_NAME"
            if not z_room and z_name:
                parts = [p.strip() for p in z_name.split("-")]
                if len(parts) >= 3 and "سيراميك" in parts[0]:
                    z_room = parts[1].strip()
            
            # Extract wall number from zone name
            m = re.search(r'جدار\s*(\d+)|wall\s*(\d+)', z_name, re.IGNORECASE)
            if not m:
                # No wall number in name, keep it
                valid_zones.append(z)
                continue
            
            wall_num = int(m.group(1) or m.group(2))
            
            # Check if this wall exists in the room
            if z_room in room_wall_map:
                if wall_num in room_wall_map[z_room]:
                    valid_zones.append(z)
                else:
                    removed += 1
                    print(f"[CeramicTab] Removing orphan zone: {z_name} (wall {wall_num} not in {z_room})")
            else:
                # Room not found, keep zone for now
                valid_zones.append(z)
        
        if removed > 0:
            self.app.project.ceramic_zones = valid_zones
            print(f"[CeramicTab] Removed {removed} orphan ceramic zones")
    
    def notify_data_changed(self):
        """Notify that ceramic data has changed - refresh coatings and output tabs."""
        # Coatings deducts ceramic zones
        if hasattr(self.app, 'coatings_tab'):
            self.app.coatings_tab.refresh_data()
        # Output tabs
        if hasattr(self.app, 'summary_tab'):
            self.app.summary_tab.refresh_data()
        if hasattr(self.app, 'quantities_tab'):
            self.app.quantities_tab.refresh_data()

    def _refresh_ceramic_zones(self):
        if not self.ceramic_tree: return
        self.ceramic_tree.delete(*self.ceramic_tree.get_children())
        zones = self.app.project.ceramic_zones
        
        # Import safe helper for area calculation
        from ...calculations.helpers import safe_zone_area
        
        total_area = 0.0
        for i, z in enumerate(zones):
            # Handle object or dict safely
            if isinstance(z, dict):
                name = z.get('name')
                cat = z.get('category')
                stype = z.get('surface_type', 'wall')
                perim = float(z.get('perimeter', 0.0) or 0.0)
                h = float(z.get('height', 0.0) or 0.0)
                
                # Use safe helper to calculate area (handles effective_area and stale data)
                area = safe_zone_area(z)
                
                adh = float(z.get('adhesive_kg', 0.0) or 0.0)
                grout = float(z.get('grout_kg', 0.0) or 0.0)
            else:
                name = getattr(z, 'name', '')
                cat = getattr(z, 'category', '')
                stype = getattr(z, 'surface_type', 'wall')
                perim = float(getattr(z, 'perimeter', 0.0) or 0.0)
                h = float(getattr(z, 'height', 0.0) or 0.0)
                # For objects, use safe helper
                area = safe_zone_area(z)
                adh = float(getattr(z, 'adhesive_kg', 0.0) or 0.0)
                grout = float(getattr(z, 'grout_kg', 0.0) or 0.0)
            
            emoji = '🟫' if stype == 'floor' else '🧱'
            self.ceramic_tree.insert('', tk.END, iid=f"zone-{i}", values=(
                name, cat, emoji,
                f"{perim:.2f}", f"{h:.2f}", f"{area:.2f}",
                f"{adh:.1f}", f"{grout:.1f}"
            ))
            total_area += area
        
        # Use accurate RoomMetrics totals (accounts for opening deductions)
        try:
            from .helpers.ceramic_metrics import calculate_ceramic_metrics
            metrics = calculate_ceramic_metrics(self.app.project)
            actual_wall = metrics['wall']
            actual_floor = metrics['floor']
            actual_ceiling = metrics['ceiling']
            actual_total = metrics['total']
            
            summary = (
                f"Zones Gross: {total_area:.2f} m² | "
                f"Net: Wall {actual_wall:.2f} + Floor {actual_floor:.2f} + Ceiling {actual_ceiling:.2f} "
                f"= {actual_total:.2f} m²"
            )
            self.ceramic_totals_label.config(text=summary)
        except:
            # Fallback to simple sum if metrics unavailable
            self.ceramic_totals_label.config(text=f"Total Ceramic Zones: {total_area:.2f} m²")

    def _refresh_tiles(self):
        if not self.tiles_tree: return
        self.tiles_tree.delete(*self.tiles_tree.get_children())
        items = self.app.project.tiles_items
        
        total = 0.0
        waste_pct = getattr(self.app.project, 'tiles_waste_percentage', 10.0)
        
        for item in items:
            if isinstance(item, dict):
                desc = item.get('desc') or item.get('description')
                area = float(item.get('area', 0.0) or 0.0)
            else:
                desc = getattr(item, 'description', '')
                area = float(getattr(item, 'area', 0.0) or 0.0)

            w_area = area * (1 + waste_pct/100)
            
            tags = ('deduction',) if area < 0 else ()
            self.tiles_tree.insert('', tk.END, values=(desc, f"{area:.2f}", f"{w_area:.2f}"), tags=tags)
            total += area
            
        self.tiles_tree.tag_configure('deduction', foreground='red')
        self.tiles_label.config(text=f"Net Tiles: {total:.2f} m² (Waste +{waste_pct}%)")

    def _refresh_stone(self):
        if not self.stone_tree: return
        self.stone_tree.delete(*self.stone_tree.get_children())
        
        total_lm = 0.0
        
        # Helper for stone items
        def process_openings(openings, kind):
            nonlocal total_lm
            for o in openings:
                if isinstance(o, dict):
                    name = o.get('name')
                    mat = o.get('type') or o.get('material_type')
                    qty = o.get('qty') or o.get('quantity')
                    stone = float(o.get('stone', 0.0) or 0.0)
                    area = float(o.get('area', 0.0) or 0.0)
                else:
                    name = getattr(o, 'name', '')
                    mat = getattr(o, 'material_type', '')
                    qty = getattr(o, 'quantity', 0)
                    stone = float(getattr(o, 'stone', 0.0) or 0.0)
                    area = float(getattr(o, 'area', 0.0) or 0.0)
                
                self.stone_tree.insert('', tk.END, values=(name, kind, mat, qty, f"{stone:.2f}", f"{area:.2f}"))
                total_lm += stone

        process_openings(self.app.project.doors, 'Door')
        process_openings(self.app.project.windows, 'Window')
            
        self.stone_metrics_label.config(text=f"Total Stone Length: {total_lm:.2f} lm")

    # --- Actions ---
    def add_ceramic_zone(self):
        payload = self.app._ceramic_zone_dialog("Add Ceramic Zone")
        zones, room_name, wall_updates = self.app._parse_ceramic_dialog_result(payload)
        if not zones and not wall_updates:
            return
        added, _ = self.app._apply_ceramic_zone_changes(zones, room_name, wall_updates)
        self.refresh_data()
        self.notify_data_changed()
        self.app.refresh_after_ceramic_change()

        if added:
            first_label = self.app._zone_attr(zones[0], 'name', '') if zones else ''
            msg = "ceramic zone" if added == 1 else f"{added} ceramic zones"
            self.app.update_status(f"✅ Added {msg}: {first_label}", icon="➕")
        else:
            self.app.update_status("Updated ceramic wall heights", icon="🧱")

    def edit_ceramic_zone(self):
        sel = self.ceramic_tree.selection()
        if not sel: return
        # Find index by matching values is risky, better to track ID. 
        # For now, assuming order matches.
        idx = self.ceramic_tree.index(sel[0])
        orig = self.app.project.ceramic_zones[idx]
        new_data = self.app._ceramic_zone_dialog("Edit Zone", initial_values=orig)
        if new_data:
            self.app.project.ceramic_zones[idx] = new_data
            self.refresh_data()
            self.notify_data_changed()

    def delete_ceramic_zone(self):
        sel = self.ceramic_tree.selection()
        if not sel: return
        if messagebox.askyesno("Confirm", "Delete selected zone?"):
            iid = sel[0]
            try:
                idx = int(str(iid).split('-')[-1])
            except Exception:
                idx = self.ceramic_tree.index(sel[0])
            deleted_room_name = None
            deleted_surface = None
            if 0 <= idx < len(self.app.project.ceramic_zones):
                z = self.app.project.ceramic_zones[idx]
                if isinstance(z, dict):
                    deleted_room_name = z.get('room_name')
                    deleted_surface = z.get('surface_type', 'wall')
                else:
                    deleted_room_name = getattr(z, 'room_name', None)
                    deleted_surface = getattr(z, 'surface_type', 'wall')
                del self.app.project.ceramic_zones[idx]

            # Recompute affected room metrics so deletion reflects immediately.
            if deleted_room_name:
                for room in self.app.project.rooms or []:
                    rname = getattr(room, 'name', None) if not isinstance(room, dict) else room.get('name')
                    if rname != deleted_room_name:
                        continue
                    # If a wall zone was removed, clear wall-level ceramic flags to avoid stale UI state.
                    if str(deleted_surface or '').lower().startswith('wall'):
                        self._clear_room_wall_ceramic(room)
                    # Recompute using UnifiedCalculator
                    if hasattr(self.app, '_recompute_room_finish'):
                        self.app._recompute_room_finish(room)
                    break
            self.refresh_data()
            self.notify_data_changed()

    def _clear_room_wall_ceramic(self, room):
        walls = getattr(room, 'walls', None) if not isinstance(room, dict) else room.get('walls')
        walls = walls or []
        for wall in walls:
            if isinstance(wall, dict):
                wall['ceramic_height'] = 0.0
                wall['ceramic_area'] = 0.0
                wall['ceramic_surface'] = ''
            else:
                if hasattr(wall, 'ceramic_height'):
                    wall.ceramic_height = 0.0
                if hasattr(wall, 'ceramic_area'):
                    wall.ceramic_area = 0.0
                if hasattr(wall, 'ceramic_surface'):
                    wall.ceramic_surface = ''

    def delete_room_ceramic(self):
        zones = self.app.project.ceramic_zones
        if not zones:
            messagebox.showinfo("No Ceramic", "لا يوجد سيراميك لحذفه.")
            return

        # Collect room names and total area per room
        room_map = {}
        for z in zones:
            room_name = getattr(z, 'room_name', None) if not isinstance(z, dict) else z.get('room_name')
            label = room_name or getattr(z, 'name', None) or (z.get('name') if isinstance(z, dict) else "")
            if not label:
                label = "(غير مرتبط بغرفة)"
            area = float(getattr(z, 'effective_area', None) if not isinstance(z, dict) else z.get('effective_area', 0.0) or 0.0)
            perim = float(getattr(z, 'perimeter', 0.0) if not isinstance(z, dict) else z.get('perimeter', 0.0) or 0.0)
            height = float(getattr(z, 'height', 0.0) if not isinstance(z, dict) else z.get('height', 0.0) or 0.0)
            eff_area = area if area > 0 else perim * height
            room_map.setdefault(label, 0.0)
            room_map[label] += eff_area

        items = [{'name': name, 'area': val} for name, val in sorted(room_map.items())]
        dialog = ItemSelectorDialog(self.app.root, "اختر الغرف لحذف السيراميك", items, show_quantity=False, colors=self.app.colors)
        sel = dialog.show()
        if not sel:
            return
        selected_names = {s['item']['name'] for s in sel}

        before = len(zones)
        self.app.project.ceramic_zones = [z for z in zones if (getattr(z, 'room_name', None) if not isinstance(z, dict) else z.get('room_name')) not in selected_names]
        removed = before - len(self.app.project.ceramic_zones)

        # Clear wall ceramic fields + recompute affected rooms
        for room in self.app.project.rooms or []:
            rname = getattr(room, 'name', None) if not isinstance(room, dict) else room.get('name')
            if not rname or rname not in selected_names:
                continue
            self._clear_room_wall_ceramic(room)
            if hasattr(self.app, '_recompute_room_finish'):
                self.app._recompute_room_finish(room)

        if removed == 0:
            messagebox.showinfo("Info", "لم يتم العثور على سيراميك مرتبط بهذه الغرف.")
            return
        self.refresh_data()
        self.notify_data_changed()
        if hasattr(self.app, 'refresh_rooms'):
            self.app.refresh_rooms()
        self.app.update_status(f"🗑️ حذف {removed} عناصر سيراميك للغرف المحددة", icon="🗑️")

    def delete_all_ceramic(self):
        if not self.app.project.ceramic_zones:
            messagebox.showinfo("No Ceramic", "لا يوجد سيراميك للحذف.")
            return
        if messagebox.askyesno("Confirm", "حذف كل السيراميك؟"):
            count = len(self.app.project.ceramic_zones)
            self.app.project.ceramic_zones.clear()

            # Clear wall ceramic fields and recompute all rooms
            for room in self.app.project.rooms or []:
                self._clear_room_wall_ceramic(room)
                if hasattr(self.app, '_recompute_room_finish'):
                    self.app._recompute_room_finish(room)

            self.refresh_data()
            self.notify_data_changed()
            if hasattr(self.app, 'refresh_rooms'):
                self.app.refresh_rooms()
            self.app.update_status(f"🧹 تم حذف كل السيراميك ({count} عنصر)", icon="🧹")

    def add_tiles_from_rooms(self):
        # Reuse logic from old finishes tab, but simplified
        if not self.app.project.rooms:
            messagebox.showwarning("No Rooms", "Pick rooms first.")
            return
            
        items = []
        for r in self.app.project.rooms:
            name = getattr(r, 'name', r.get('name'))
            area = float(getattr(r, 'area', r.get('area', 0.0)) or 0.0)
            rtype = getattr(r, 'room_type', r.get('room_type'))
            items.append({'name': f"{name} ({rtype})", 'area': area})
            
        dialog = ItemSelectorDialog(self.app.root, "Select Rooms for Tiling", items, show_quantity=False, colors=self.app.colors)
        sel = dialog.show()
        if sel:
            from ...models.finish import FinishItem
            for s in sel:
                self.app.project.tiles_items.append(FinishItem(
                    description=s['item']['name'],
                    area=s['total_area'],
                    finish_type='tiles'
                ))
            self.refresh_data()

    def add_tiles_manual(self):
        d = self.app._finish_item_dialog("Add Manual Tile Area")
        if d:
            from ...models.finish import FinishItem
            self.app.project.tiles_items.append(FinishItem(
                description=d['desc'], area=d['area'], finish_type='tiles'
            ))
            self.refresh_data()

    def deduct_ceramic_from_tiles(self):
        # Deduct floor zones from general tiles
        floor_zones_area = sum(
            float(getattr(z, 'area', z.get('area', 0.0)) or 0.0)
            for z in self.app.project.ceramic_zones
            if getattr(z, 'surface_type', z.get('surface_type')) == 'floor'
        )
        
        if floor_zones_area > 0:
            from ...models.finish import FinishItem
            self.app.project.tiles_items.append(FinishItem(
                description="Deduction: Ceramic Floor Zones",
                area=-floor_zones_area,
                finish_type='tiles'
            ))
            self.refresh_data()
            messagebox.showinfo("Deducted", f"Deducted {floor_zones_area:.2f} m² from tiles.")
        else:
            messagebox.showinfo("Info", "No floor ceramic zones found to deduct.")

    def clear_tiles(self):
        if messagebox.askyesno("Clear", "Clear all tile items?"):
            self.app.project.tiles_items.clear()
            self.refresh_data()

    def quick_ceramic_wizard(self):
        """
        Auto-generate ceramic zones for bathrooms and kitchens based on room data.
        
        Rules:
        - Bathroom: Full wall ceramic (perimeter × wall_height) + floor ceramic (area)
        - Kitchen: Backsplash only (perimeter × 0.6m at height 0.85m) + optional floor
        """
        # Find bathrooms and kitchens
        bathrooms = []
        kitchens = []
        
        for r in self.app.project.rooms:
            if isinstance(r, dict):
                rtype = r.get('room_type', '').lower()
                name = r.get('name', '')
                area = float(r.get('area', 0) or 0)
                perim = float(r.get('perimeter', 0) or 0)
            else:
                rtype = getattr(r, 'room_type', '').lower()
                name = getattr(r, 'name', '')
                area = float(getattr(r, 'area', 0) or 0)
                perim = float(getattr(r, 'perimeter', 0) or 0)
            
            if 'حمام' in rtype or 'bathroom' in rtype or 'bath' in rtype or 'wc' in rtype:
                bathrooms.append({'name': name, 'area': area, 'perimeter': perim})
            elif 'مطبخ' in rtype or 'kitchen' in rtype:
                kitchens.append({'name': name, 'area': area, 'perimeter': perim})
        
        if not bathrooms and not kitchens:
            messagebox.showinfo("لا توجد غرف", 
                "لم يتم العثور على حمامات أو مطابخ.\n"
                "تأكد من تحديد الغرف أولاً مع نوع 'حمام' أو 'مطبخ'.")
            return
        
        # Show selection dialog
        wall_height = getattr(self.app.project, 'default_wall_height', 3.0)
        
        # Build message
        msg = "سيتم إنشاء السيراميك التالي:\n\n"
        zones_to_add = []
        
        for b in bathrooms:
            wall_area = b['perimeter'] * wall_height
            floor_area = b['area']
            msg += f"🚿 {b['name']}:\n"
            msg += f"   • حائط: {b['perimeter']:.1f}م × {wall_height:.1f}م = {wall_area:.1f} م²\n"
            msg += f"   • أرضية: {floor_area:.1f} م²\n\n"
            
            # Delete existing ceramics for this bathroom
            self.app.project.ceramic_zones = [
                z for z in self.app.project.ceramic_zones
                if (z.get('room_name') if isinstance(z, dict) else getattr(z, 'room_name', None)) != b['name']
            ]
            
            zones_to_add.append(CeramicZone.for_wall(
                perimeter=b['perimeter'],
                height=wall_height,
                room_name=b['name'],
                category='Bathroom',
                name=f"سيراميك حائط - {b['name']}"
            ))
            zones_to_add.append(CeramicZone.for_floor(
                area=floor_area,
                room_name=b['name'],
                category='Bathroom',
                name=f"سيراميك أرضية - {b['name']}"
            ))
        
        for k in kitchens:
            backsplash_height = 0.6  # 60cm backsplash
            backsplash_area = k['perimeter'] * backsplash_height
            msg += f"🍳 {k['name']}:\n"
            msg += f"   • باكسبلاش: {k['perimeter']:.1f}م × {backsplash_height:.1f}م = {backsplash_area:.1f} م²\n\n"
            
            zones_to_add.append(CeramicZone.for_wall(
                perimeter=k['perimeter'],
                height=backsplash_height,
                start_height=0.85,  # Counter height
                room_name=k['name'],
                category='Kitchen',
                name=f"باكسبلاش - {k['name']}"
            ))
        
        msg += "هل تريد إضافة هذه المناطق؟"
        
        if messagebox.askyesno("سيراميك سريع", msg):
            self.app.project.ceramic_zones.extend(zones_to_add)
            self.refresh_data()
            # Also refresh coatings tab if exists
            if hasattr(self.app, 'coatings_tab'):
                self.app.coatings_tab.refresh_data()
            messagebox.showinfo("تم", f"تمت إضافة {len(zones_to_add)} منطقة سيراميك.")
