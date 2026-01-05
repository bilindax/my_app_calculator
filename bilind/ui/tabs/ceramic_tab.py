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
            # (Removed) Bathroom/Toilet/Kitchen/Balcony preset buttons per user request
            ("⚡ سيراميك سريع", self.quick_ceramic_wizard, 'Success.TButton'),
            ("➕ Add Zone", self.add_ceramic_zone, 'Accent.TButton'),
            ("✏️ Edit", self.edit_ceramic_zone, 'Secondary.TButton'),
            ("🗑️ Delete", self.delete_ceramic_zone, 'Danger.TButton')
        ]:
            self.create_button(btn_bar, text, command, style).pack(side=tk.LEFT, padx=4)

        for text, command, style in [
            ("🚫 حذف سيراميك الغرفة", self.delete_room_ceramic, 'Warning.TButton'),
            ("📉 خصومات الفتحات (سيراميك)", self.show_ceramic_openings_deductions_by_room, 'Secondary.TButton'),
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
        """Get wall height with improved priority: room.wall_height > derived > segments > project default."""
        from ...calculations.unified_calculator import UnifiedCalculator
        
        default_h = float(getattr(self.app.project, 'default_wall_height', 3.0) or 3.0)
        try:
            # Priority 1: Derive from walls_gross / perimeter (SSOT)
            calc = UnifiedCalculator(self.app.project)
            walls_gross = calc.calculate_walls_gross(room)
            
            if isinstance(room, dict):
                perim = float(room.get('perimeter', 0) or room.get('perim', 0) or 0)
            else:
                perim = float(getattr(room, 'perimeter', 0) or getattr(room, 'perim', 0) or 0)
            
            # If perimeter is 0, try summing wall lengths
            if perim <= 0.01:
                walls = room.get('walls', []) if isinstance(room, dict) else getattr(room, 'walls', [])
                if walls:
                    perim = sum(float((w.get('length', 0) if isinstance(w, dict) else getattr(w, 'length', 0)) or 0) for w in walls)
            
            if walls_gross > 0 and perim > 0:
                derived_h = walls_gross / perim
                if derived_h > 0.5:  # Sanity check
                    return derived_h
            
            # Priority 3: Max from wall_segments
            if isinstance(room, dict):
                segs = room.get('wall_segments', []) or []
                heights = [float(s.get('height', 0.0) or 0.0) for s in segs if isinstance(s, dict)]
            else:
                segs = getattr(room, 'wall_segments', []) or []
                heights = [float((s.get('height', 0.0) if isinstance(s, dict) else getattr(s, 'height', 0.0)) or 0.0) for s in segs]
            
            heights = [h for h in heights if h > 0.0]
            if heights:
                return max(heights)
            
            # Priority 4: Project default
            return default_h
        except Exception:
            return default_h

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

        def _get_zone_room_name(zone, known_room_names):
            """Best-effort: return room name for a ceramic zone.

            Some legacy zones may have empty room_name; try to infer from the zone name.
            """
            if isinstance(zone, dict):
                room_name = (zone.get('room_name') or '').strip()
                zone_name = (zone.get('name') or '').strip()
            else:
                room_name = (getattr(zone, 'room_name', '') or '').strip()
                zone_name = (getattr(zone, 'name', '') or '').strip()

            if room_name:
                return room_name

            if not zone_name:
                return None

            # Common pattern: "سيراميك - ROOM_NAME - جدار N" (or similar)
            try:
                parts = [p.strip() for p in zone_name.split('-')]
                if len(parts) >= 3 and 'سيراميك' in parts[0]:
                    candidate = parts[1].strip()
                    if candidate:
                        return candidate
            except Exception:
                pass

            # Fallback: find any known room name embedded in the zone name
            for rn in known_room_names:
                if rn and rn in zone_name:
                    return rn

            return None

        # Collect room names and total area per room
        known_room_names = set()
        for room in self.app.project.rooms or []:
            rn = room.get('name') if isinstance(room, dict) else getattr(room, 'name', None)
            if rn:
                known_room_names.add(str(rn))

        # Use the same area logic as the grid (handles effective_area safely)
        from ...calculations.helpers import safe_zone_area

        room_map = {}
        for z in zones:
            inferred_room = _get_zone_room_name(z, known_room_names)
            label = inferred_room or "(غير مرتبط بغرفة)"

            eff_area = float(safe_zone_area(z) or 0.0)
            room_map.setdefault(label, 0.0)
            room_map[label] += eff_area

        items = [{'name': name, 'area': val} for name, val in sorted(room_map.items())]
        dialog = ItemSelectorDialog(self.app.root, "اختر الغرف لحذف السيراميك", items, show_quantity=False, colors=self.app.colors)
        sel = dialog.show()
        if not sel:
            return
        selected_names = {s['item']['name'] for s in sel}

        before = len(zones)
        def _zone_selected(zone):
            inferred = _get_zone_room_name(zone, known_room_names)
            if inferred is None:
                return "(غير مرتبط بغرفة)" in selected_names
            return inferred in selected_names

        self.app.project.ceramic_zones = [z for z in zones if not _zone_selected(z)]
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

    def show_ceramic_openings_deductions_by_room(self):
        """Show per-room ceramic wall deductions caused by openings (doors/windows).

        Note: Deductions are computed in SSOT (UnifiedCalculator) using overlap with the zone band
        (start_height + height), so this is the reliable view.
        """
        zones = self.app.project.ceramic_zones or []
        if not zones:
            messagebox.showinfo("No Ceramic", "لا يوجد سيراميك لعرضه.")
            return

        from ...calculations.unified_calculator import UnifiedCalculator

        calc = UnifiedCalculator(self.app.project)
        by_room = {}
        room_order = []

        def _get_attr(obj, key, attr, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, attr, default)

        for z in zones:
            surface = str(_get_attr(z, 'surface_type', 'surface_type', 'wall') or 'wall').lower()
            if surface != 'wall':
                continue
            room_name = str(_get_attr(z, 'room_name', 'room_name', '') or '').strip() or '(غير مرتبط بغرفة)'

            m = calc.calculate_zone_metrics(z)
            if room_name not in by_room:
                by_room[room_name] = {
                    'zones': 0,
                    'gross': 0.0,
                    'deduct': 0.0,
                    'net': 0.0,
                    'details': [],
                }
                room_order.append(room_name)

            rec = by_room[room_name]
            rec['zones'] += 1
            rec['gross'] += float(m.gross_area or 0.0)
            rec['deduct'] += float(m.deduction_area or 0.0)
            rec['net'] += float(m.net_area or 0.0)
            det = str(m.deduction_details or '').strip()
            if det and det not in ('لا يوجد خصم', 'No deduction'):
                rec['details'].append(det)

        if not by_room:
            messagebox.showinfo("Info", "لا توجد مناطق سيراميك جدران (خصم الفتحات يكون على الجدران فقط).")
            return

        dlg = tk.Toplevel(self.app.root)
        dlg.title("📉 خصومات الفتحات للسيراميك (حسب الغرفة)")
        dlg.configure(bg=self.app.colors['bg_secondary'])
        dlg.transient(self.app.root)
        dlg.grab_set()
        dlg.geometry("820x520")

        container = ttk.Frame(dlg, padding=(14, 12), style='Main.TFrame')
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text="خصومات الفتحات (أبواب/شبابيك) تُحسب فقط على سيراميك الجدران حسب تداخل الفتحة مع شريط السيراميك.",
            style='Caption.TLabel',
        ).pack(anchor=tk.W, pady=(0, 10))

        cols = ('Room', 'Zones', 'Gross', 'Deduct', 'Net')
        tree = ttk.Treeview(container, columns=cols, show='headings', height=12)
        tree.heading('Room', text='Room')
        tree.heading('Zones', text='Zones')
        tree.heading('Gross', text='Gross (m²)')
        tree.heading('Deduct', text='Openings Deduct (m²)')
        tree.heading('Net', text='Net (m²)')
        tree.column('Room', width=260)
        tree.column('Zones', width=60, anchor=tk.CENTER)
        tree.column('Gross', width=120, anchor=tk.CENTER)
        tree.column('Deduct', width=160, anchor=tk.CENTER)
        tree.column('Net', width=120, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True)

        total_g = total_d = total_n = 0.0
        for rn in sorted(room_order):
            rec = by_room[rn]
            total_g += rec['gross']
            total_d += rec['deduct']
            total_n += rec['net']
            tree.insert('', tk.END, iid=rn, values=(
                rn,
                str(rec['zones']),
                f"{rec['gross']:.2f}",
                f"{rec['deduct']:.2f}",
                f"{rec['net']:.2f}",
            ))

        footer = ttk.Frame(container, style='Main.TFrame')
        footer.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(
            footer,
            text=f"الإجمالي: Gross {total_g:.2f} | Deduct {total_d:.2f} | Net {total_n:.2f} (m²)",
            style='Metrics.TLabel',
            foreground=self.app.colors.get('accent', '#00d4ff'),
        ).pack(side=tk.LEFT)

        def _show_details():
            sel = tree.selection()
            if not sel:
                return
            rn = sel[0]
            dets = by_room.get(rn, {}).get('details', [])
            if not dets:
                messagebox.showinfo("تفاصيل الخصم", "لا يوجد خصم فتحات على مناطق السيراميك لهذه الغرفة.", parent=dlg)
                return
            msg = "\n".join(dets)
            messagebox.showinfo(f"تفاصيل خصم الفتحات – {rn}", msg, parent=dlg)

        ttk.Button(footer, text="تفاصيل الغرفة المحددة", command=_show_details, style='Secondary.TButton').pack(side=tk.RIGHT, padx=6)
        ttk.Button(footer, text="إغلاق", command=dlg.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)

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
        
        NEW: Shows a dialog with computed heights BEFORE applying, allowing user override.
        """
        from ...calculations.unified_calculator import UnifiedCalculator

        def _resolve_room_wall_height(room) -> float:
            """
            Get wall height that matches how walls_gross is calculated.
            Priority: 
            1. Explicit room.wall_height (if set by user)
            2. Derived from walls_gross / perimeter (matches SSOT)
            3. Max height from wall_segments
            4. Project default_wall_height
            """
            default_h = float(getattr(self.app.project, 'default_wall_height', 3.0) or 3.0)
            try:
                # Priority 1: Derive from actual wall geometry (same as UnifiedCalculator)
                calc = UnifiedCalculator(self.app.project)
                walls_gross = calc.calculate_walls_gross(room)
                
                if isinstance(room, dict):
                    perim = float(room.get('perimeter', 0) or room.get('perim', 0) or 0)
                else:
                    perim = float(getattr(room, 'perimeter', 0) or getattr(room, 'perim', 0) or 0)
                
                # If perimeter is 0, try summing wall lengths
                if perim <= 0.01:
                    walls = room.get('walls', []) if isinstance(room, dict) else getattr(room, 'walls', [])
                    if walls:
                        perim = sum(float((w.get('length', 0) if isinstance(w, dict) else getattr(w, 'length', 0)) or 0) for w in walls)
                
                # Derive height from walls_gross / perimeter
                if walls_gross > 0 and perim > 0:
                    derived_h = walls_gross / perim
                    if derived_h > 0.5:  # Sanity check
                        return derived_h
                
                # Priority 3: If multi-segment heights exist, use the maximum
                if isinstance(room, dict):
                    segs = room.get('wall_segments', None) or []
                    heights = [float(s.get('height', 0.0) or 0.0) for s in segs if isinstance(s, dict)]
                    heights = [h for h in heights if h > 0.0]
                    if heights:
                        return max(heights)
                else:
                    segs = getattr(room, 'wall_segments', None) or []
                    heights = []
                    for s in segs:
                        if isinstance(s, dict):
                            heights.append(float(s.get('height', 0.0) or 0.0))
                        else:
                            heights.append(float(getattr(s, 'height', 0.0) or 0.0))
                    heights = [h for h in heights if h > 0.0]
                    if heights:
                        return max(heights)
                
                # Priority 4: Project default
                return default_h
            except Exception:
                return default_h

        # Find bathrooms, toilets, kitchens, balconies, and other rooms
        bathrooms = []
        toilets = []
        kitchens = []
        balconies = []
        others = []

        for r in self.app.project.rooms:
            if isinstance(r, dict):
                rtype = (r.get('room_type', '') or '').lower()
                name = r.get('name', '')
                area = float(r.get('area', 0) or 0)
                # IMPORTANT: some legacy flows store perimeter under 'perim'
                perim = float(r.get('perim', None) or r.get('perimeter', 0) or 0)
            else:
                rtype = (getattr(r, 'room_type', '') or '').lower()
                name = getattr(r, 'name', '')
                area = float(getattr(r, 'area', 0) or 0)
                # IMPORTANT: support both 'perim' and 'perimeter'
                perim = float(getattr(r, 'perim', None) or getattr(r, 'perimeter', 0) or 0)

            low_name = str(name or '').lower()
            is_toilet = any(k in rtype or k in low_name for k in ['تواليت', 'wc', 'toilet'])
            is_bath = any(k in rtype or k in low_name for k in ['حمام', 'bathroom', 'bath'])
            is_kitchen = any(k in rtype or k in low_name for k in ['مطبخ', 'kitchen'])
            is_balcony = any(k in rtype or k in low_name for k in ['بلكون', 'شرفة', 'balcony', 'terrace'])

            if is_toilet:
                toilets.append({'name': name, 'area': area, 'perimeter': perim, 'room_obj': r})
            elif is_bath:
                bathrooms.append({'name': name, 'area': area, 'perimeter': perim, 'room_obj': r})
            elif is_kitchen:
                kitchens.append({'name': name, 'area': area, 'perimeter': perim, 'room_obj': r})
            elif is_balcony:
                balconies.append({'name': name, 'area': area, 'perimeter': perim, 'room_obj': r})
            else:
                others.append({'name': name, 'area': area, 'perimeter': perim, 'room_obj': r})
        
        if not bathrooms and not toilets and not kitchens and not balconies and not others:
            messagebox.showinfo("لا توجد غرف", 
                "لم يتم العثور على حمامات أو مطابخ.\n"
                "تأكد من تحديد الغرف أولاً.")
            return
        
        # NEW: Show dialog for height adjustment
        self._show_quick_wizard_dialog(bathrooms, toilets, kitchens, balconies, others, _resolve_room_wall_height)
    
    def _show_quick_wizard_dialog(self, bathrooms, toilets, kitchens, balconies, others, resolve_height_func):
        """Show a structured dialog for quick ceramic generation (simpler + consistent)."""

        dialog = tk.Toplevel(self.app.root)
        dialog.title("⚡ السيراميك السريع")
        dialog.configure(bg=self.app.colors['bg_secondary'])
        dialog.transient(self.app.root)
        dialog.grab_set()
        dialog.geometry("760x640")

        # Header
        header = ttk.Frame(dialog, style='Main.TFrame', padding=12)
        header.pack(fill=tk.X)
        ttk.Label(
            header,
            text="⚡ السيراميك السريع",
            font=('Segoe UI Semibold', 14),
            foreground=self.app.colors['accent'],
        ).pack(anchor='w')
        ttk.Label(
            header,
            text="1) اختر الأسطح  2) اختر الغرف  3) عدّل الارتفاع إن لزم",
            foreground=self.app.colors['text_secondary'],
        ).pack(anchor='w')

        # Options (fixed, not inside a long scroll)
        opts = ttk.LabelFrame(dialog, text="⚙️ خيارات", style='Card.TLabelframe', padding=10)
        opts.pack(fill=tk.X, padx=12, pady=(0, 10))

        add_walls_var = tk.BooleanVar(value=True)
        add_floor_var = tk.BooleanVar(value=True)
        add_ceiling_var = tk.BooleanVar(value=False)  # default: NO ceiling (per user request)
        kitchen_mode_var = tk.StringVar(value='backsplash')  # 'backsplash' or 'full'

        # Surface presets
        preset_row = ttk.Frame(opts, style='Main.TFrame')
        preset_row.pack(fill=tk.X)
        ttk.Label(preset_row, text="اختيار سريع:", foreground=self.app.colors['text_secondary']).pack(side=tk.LEFT)

        def _set_surfaces(walls: bool, floor: bool, ceiling: bool):
            add_walls_var.set(bool(walls))
            add_floor_var.set(bool(floor))
            add_ceiling_var.set(bool(ceiling))

        self.create_button(preset_row, "جدران فقط", lambda: _set_surfaces(True, False, False), 'Secondary.TButton').pack(side=tk.LEFT, padx=(8, 4))
        self.create_button(preset_row, "جدران + أرضية", lambda: _set_surfaces(True, True, False), 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(preset_row, "كامل (مع سقف)", lambda: _set_surfaces(True, True, True), 'Secondary.TButton').pack(side=tk.LEFT, padx=4)

        # Surface toggles
        surf_row = ttk.Frame(opts, style='Main.TFrame')
        surf_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(surf_row, text="الأسطح:", foreground=self.app.colors['text_secondary']).pack(side=tk.LEFT)
        ttk.Checkbutton(surf_row, text="جدران", variable=add_walls_var).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Checkbutton(surf_row, text="أرضية", variable=add_floor_var).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Checkbutton(surf_row, text="سقف", variable=add_ceiling_var).pack(side=tk.LEFT, padx=(8, 0))

        # Kitchen mode
        kitchen_row = ttk.Frame(opts, style='Main.TFrame')
        kitchen_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(kitchen_row, text="المطبخ (للجدران فقط):", foreground=self.app.colors['text_secondary']).pack(side=tk.LEFT)
        ttk.Radiobutton(kitchen_row, text="باكسبلاش 0.60م @ 0.85م", value='backsplash', variable=kitchen_mode_var).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Radiobutton(kitchen_row, text="جدران كاملة", value='full', variable=kitchen_mode_var).pack(side=tk.LEFT, padx=(8, 0))

        # Room selection area (tabs)
        content = ttk.Frame(dialog, style='Main.TFrame', padding=(12, 0, 12, 0))
        content.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(content)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Store rows in a consistent structure
        room_rows = []  # [{type, data, include_var, height_var}]

        def _make_tab(title: str, rows: list, default_include: bool):
            tab = ttk.Frame(notebook, style='Main.TFrame')
            notebook.add(tab, text=title)

            top = ttk.Frame(tab, style='Main.TFrame', padding=(8, 8, 8, 6))
            top.pack(fill=tk.X)

            ttk.Label(top, text="تحديد:", foreground=self.app.colors['text_secondary']).pack(side=tk.LEFT)

            def _select_all(val: bool):
                for row in rows:
                    row['include_var'].set(bool(val))

            self.create_button(top, "الكل", lambda: _select_all(True), 'Secondary.TButton').pack(side=tk.LEFT, padx=(8, 4))
            self.create_button(top, "لا شيء", lambda: _select_all(False), 'Secondary.TButton').pack(side=tk.LEFT, padx=4)

            body = ttk.Frame(tab, style='Main.TFrame', padding=(8, 0, 8, 8))
            body.pack(fill=tk.BOTH, expand=True)

            # Scrollable list per tab
            canvas = tk.Canvas(body, bg=self.app.colors['bg_secondary'], highlightthickness=0)
            sb = ttk.Scrollbar(body, orient=tk.VERTICAL, command=canvas.yview)
            inner = ttk.Frame(canvas, style='Main.TFrame')
            inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.create_window((0, 0), window=inner, anchor='nw')
            canvas.configure(yscrollcommand=sb.set)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb.pack(side=tk.RIGHT, fill=tk.Y)

            for row in rows:
                d = row['data']
                computed_h = resolve_height_func(d['room_obj'])
                row['height_var'].set(f"{computed_h:.2f}")
                row['include_var'].set(bool(default_include))

                card = ttk.Frame(inner, style='Card.TFrame', padding=8)
                card.pack(fill=tk.X, pady=4)

                ttk.Checkbutton(card, text="تضمين", variable=row['include_var']).grid(row=0, column=3, padx=(10, 4), sticky='e')

                ttk.Label(card, text=f"{d['name']}", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=4)
                ttk.Label(
                    card,
                    text=f"محيط: {float(d.get('perimeter', 0) or 0):.2f}م  |  مساحة: {float(d.get('area', 0) or 0):.2f}م²",
                    foreground=self.app.colors['text_secondary'],
                ).grid(row=1, column=0, sticky='w', padx=4)

                ttk.Label(card, text="ارتفاع الجدران (م):", foreground=self.app.colors['text_secondary']).grid(row=0, column=1, padx=(20, 4), sticky='e')
                ttk.Entry(card, textvariable=row['height_var'], width=8, justify='center').grid(row=0, column=2, padx=4)

            return tab

        # Build room rows per group
        bath_rows = [{'type': 'bath', 'data': b, 'include_var': tk.BooleanVar(), 'height_var': tk.StringVar()} for b in bathrooms]
        toilet_rows = [{'type': 'toilet', 'data': t, 'include_var': tk.BooleanVar(), 'height_var': tk.StringVar()} for t in toilets]
        kitchen_rows = [{'type': 'kitchen', 'data': k, 'include_var': tk.BooleanVar(), 'height_var': tk.StringVar()} for k in kitchens]
        balcony_rows = [{'type': 'balcony', 'data': b, 'include_var': tk.BooleanVar(), 'height_var': tk.StringVar()} for b in balconies]
        other_rows = [{'type': 'other', 'data': o, 'include_var': tk.BooleanVar(), 'height_var': tk.StringVar()} for o in others]
        room_rows.extend(bath_rows + toilet_rows + kitchen_rows + balcony_rows + other_rows)

        if bath_rows:
            _make_tab("🚿 حمامات", bath_rows, default_include=True)
        if toilet_rows:
            _make_tab("🚽 تواليت", toilet_rows, default_include=True)
        if kitchen_rows:
            _make_tab("🍳 مطابخ", kitchen_rows, default_include=True)
        if balcony_rows:
            _make_tab("🪟 بلكون", balcony_rows, default_include=True)
        if other_rows:
            _make_tab("🏠 غرف أخرى", other_rows, default_include=False)

        # Quick selection buttons (which rooms)
        quick = ttk.Frame(dialog, style='Main.TFrame', padding=(12, 10))
        quick.pack(fill=tk.X)
        ttk.Label(quick, text="اختيار الغرف:", foreground=self.app.colors['text_secondary']).pack(side=tk.LEFT)

        def _select_rooms(types_to_keep: set | None):
            for r in room_rows:
                if types_to_keep is None:
                    r['include_var'].set(True)
                else:
                    r['include_var'].set(r['type'] in types_to_keep)

        self.create_button(quick, "الكل", lambda: _select_rooms(None), 'Secondary.TButton').pack(side=tk.LEFT, padx=(8, 4))
        self.create_button(quick, "لا شيء", lambda: _select_rooms(set()), 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(quick, "تواليت فقط", lambda: _select_rooms({'toilet'}), 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(quick, "حمامات فقط", lambda: _select_rooms({'bath'}), 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(quick, "مطبخ فقط", lambda: _select_rooms({'kitchen'}), 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(quick, "بلكون فقط", lambda: _select_rooms({'balcony'}), 'Secondary.TButton').pack(side=tk.LEFT, padx=4)

        # Summary + buttons
        bottom = ttk.Frame(dialog, style='Main.TFrame', padding=12)
        bottom.pack(fill=tk.X)

        summary_var = tk.StringVar(value="")
        ttk.Label(bottom, textvariable=summary_var, foreground=self.app.colors['accent']).pack(side=tk.LEFT)

        def _update_summary(*_):
            selected = [r for r in room_rows if bool(r['include_var'].get())]
            parts = []
            if add_walls_var.get():
                parts.append("جدران")
            if add_floor_var.get():
                parts.append("أرضية")
            if add_ceiling_var.get():
                parts.append("سقف")
            surf = " + ".join(parts) if parts else "(لا يوجد أسطح)"
            summary_var.set(f"المحدد: {len(selected)} غرفة | الأسطح: {surf}")

        _update_summary()
        add_walls_var.trace_add('write', _update_summary)
        add_floor_var.trace_add('write', _update_summary)
        add_ceiling_var.trace_add('write', _update_summary)
        for r in room_rows:
            r['include_var'].trace_add('write', _update_summary)

        def apply_zones():
            try:
                if not (add_walls_var.get() or add_floor_var.get() or add_ceiling_var.get()):
                    messagebox.showerror("خطأ", "اختر سطح واحد على الأقل (جدران/أرضية/سقف).")
                    return

                selected = [r for r in room_rows if bool(r['include_var'].get())]
                if not selected:
                    messagebox.showinfo("Info", "اختر غرفة واحدة على الأقل.")
                    return

                zones_to_add = []
                for r in selected:
                    info_type = r['type']
                    d = r['data']

                    try:
                        wall_height = float((r['height_var'].get() or '').strip())
                    except ValueError:
                        messagebox.showerror("خطأ", f"ارتفاع غير صحيح للغرفة '{d['name']}'")
                        return

                    room_name = d['name']
                    perim = float(d.get('perimeter', 0) or 0)
                    area = float(d.get('area', 0) or 0)

                    if info_type == 'kitchen':
                        # Walls for kitchen depend on mode; respect the global "walls" toggle
                        if add_walls_var.get():
                            if kitchen_mode_var.get() == 'full':
                                zones_to_add.append(
                                    CeramicZone.for_wall(
                                        perimeter=perim,
                                        height=wall_height,
                                        room_name=room_name,
                                        category='Kitchen',
                                        name=f"سيراميك حائط - {room_name}",
                                    )
                                )
                            else:
                                zones_to_add.append(
                                    CeramicZone.for_wall(
                                        perimeter=perim,
                                        height=0.6,
                                        start_height=0.85,
                                        room_name=room_name,
                                        category='Kitchen',
                                        name=f"باكسبلاش - {room_name}",
                                    )
                                )
                        # Floor/Ceiling use the global toggles
                        if add_floor_var.get() and area > 0:
                            zones_to_add.append(
                                CeramicZone.for_floor(
                                    area=area,
                                    room_name=room_name,
                                    category='Kitchen',
                                    name=f"سيراميك أرضية - {room_name}",
                                )
                            )
                        if add_ceiling_var.get() and area > 0:
                            cz = CeramicZone.for_floor(
                                area=area,
                                room_name=room_name,
                                category='Kitchen',
                                name=f"سيراميك سقف - {room_name}",
                            )
                            cz.surface_type = 'ceiling'
                            zones_to_add.append(cz)
                        continue

                    # Default for bath/toilet/balcony/other
                    category = {
                        'bath': 'Bathroom',
                        'toilet': 'Toilet',
                        'balcony': 'Balcony',
                        'other': 'Other',
                    }.get(info_type, 'Other')

                    if add_walls_var.get() and perim > 0:
                        zones_to_add.append(
                            CeramicZone.for_wall(
                                perimeter=perim,
                                height=wall_height,
                                room_name=room_name,
                                category=category,
                                name=f"سيراميك حائط - {room_name}",
                            )
                        )
                    if add_floor_var.get() and area > 0:
                        zones_to_add.append(
                            CeramicZone.for_floor(
                                area=area,
                                room_name=room_name,
                                category=category,
                                name=f"سيراميك أرضية - {room_name}",
                            )
                        )
                    if add_ceiling_var.get() and area > 0:
                        cz = CeramicZone.for_floor(
                            area=area,
                            room_name=room_name,
                            category=category,
                            name=f"سيراميك سقف - {room_name}",
                        )
                        cz.surface_type = 'ceiling'
                        zones_to_add.append(cz)

                if not zones_to_add:
                    messagebox.showinfo("Info", "لا توجد عناصر لإضافتها (تحقق من اختيار الغرف/الأسطح).")
                    return

                affected_rooms = {z.room_name for z in zones_to_add if getattr(z, 'room_name', None)}
                self.app.project.ceramic_zones = [
                    z for z in (self.app.project.ceramic_zones or [])
                    if (z.get('room_name') if isinstance(z, dict) else getattr(z, 'room_name', None)) not in affected_rooms
                ]

                self.app.project.ceramic_zones.extend(zones_to_add)
                self.refresh_data()
                if hasattr(self.app, 'coatings_tab'):
                    self.app.coatings_tab.refresh_data()

                dialog.destroy()
                messagebox.showinfo("تم", f"تمت إضافة {len(zones_to_add)} منطقة سيراميك.")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل التطبيق:\n{e}")

        self.create_button(bottom, "❌ إلغاء", dialog.destroy, 'Secondary.TButton').pack(side=tk.RIGHT, padx=4)
        self.create_button(bottom, "✅ تطبيق", apply_zones, 'Accent.TButton').pack(side=tk.RIGHT, padx=4)
