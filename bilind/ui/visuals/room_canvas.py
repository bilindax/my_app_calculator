"""Room Visual Canvas
======================
Lightweight drawing surface that renders an unfolded elevation view
of all walls inside a room. Intended for quick visual validation of
finish heights (ceramic bands) and opening distribution without
leaving the Room Manager tab.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Iterable, List

from bilind.models.wall import Wall
from bilind.ui.tabs.helpers import RoomAdapter


class RoomCanvas(ttk.Frame):
    """Scrollable canvas that draws room walls side-by-side."""

    def __init__(self, parent: tk.Widget, app, *, height: int = 280) -> None:
        super().__init__(parent, style='Main.TFrame')
        self.app = app
        self._current_room = None
        self._height = max(height, 220)
        self._padding = 32
        self._min_width = 760
        self._gap_px = 12

        self._canvas = tk.Canvas(
            self,
            bg=self.app.colors.get('bg_secondary', '#1e1e1e'),
            highlightthickness=0,
            height=self._height,
        )
        self._h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self._canvas.xview)
        self._canvas.configure(xscrollcommand=self._h_scroll.set)

        self._canvas.grid(row=0, column=0, sticky='nsew')
        self._h_scroll.grid(row=1, column=0, sticky='ew')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._canvas.bind('<Configure>', self._on_resize)

        # Modern Professional Color Palette - Enhanced Visuals
        self._colors = {
            # Wall finishes - Vibrant but professional
            'paint': '#FFE082',           # Warm amber/gold for paint
            'paint_dark': '#FFB300',      # Darker accent for paint edges
            'ceramic': '#78909C',         # Blue-grey for ceramic tiles
            'ceramic_pattern': '#546E7A', # Darker pattern lines
            'ceramic_accent': '#90A4AE',  # Lighter ceramic highlights
            
            # Openings - Rich distinct colors
            'door': '#8D6E63',            # Warm wood brown
            'door_frame': '#5D4037',      # Dark brown frame
            'door_panel': '#A1887F',      # Inner door panel
            'door_handle': '#D7CCC8',     # Metallic handle
            'window': '#64B5F6',          # Sky blue glass
            'window_frame': '#1565C0',    # Dark blue frame
            'window_cross': '#42A5F5',    # Window grid lines
            
            # Structure
            'outline': '#455A64',         # Solid dark outline
            'outline_light': '#78909C',   # Lighter outline
            'text': '#ECEFF1',            # Near-white text
            'text_dark': '#263238',       # Dark text for light backgrounds
            'subtle': '#90A4AE',          # Muted text
            'grid': '#37474F',            # Subtle grid
            
            # Floors & Ceilings
            'floor': '#BCAAA4',           # Warm neutral floor
            'floor_pattern': '#A1887F',   # Floor pattern lines
            'ceiling': '#ECEFF1',         # Clean white ceiling
            'ceiling_pattern': '#CFD8DC', # Subtle ceiling pattern
            'floor_ceramic': '#607D8B',   # Slate grey for floor tiles
            'floor_ceramic_pattern': '#455A64',
            
            # Cards & UI Elements
            'card_bg': '#263238',         # Dark charcoal card
            'card_bg_gradient': '#37474F',# Slightly lighter for gradient effect
            'card_shadow': '#0D1B21',     # Deep shadow
            'card_border': '#455A64',     # Visible border
            'badge_bg': '#00695C',        # Teal badge background
            'badge_border': '#004D40',    # Darker badge border
            'badge_text': '#E0F2F1',      # Light badge text
            
            # Measurement & Scale
            'scale': '#80CBC4',           # Teal scale lines
            'scale_text': '#B2DFDB',      # Light teal scale text
            'dimension': '#FFB74D',       # Orange dimension lines
            'dimension_text': '#FFCC80',  # Light orange dimension text
            
            # Status & Warnings
            'warning': '#FF7043',         # Orange-red warning
            'warning_bg': '#3E2723',      # Dark warning background
            'success': '#66BB6A',         # Green success
            'info': '#42A5F5',            # Blue info
            
            # Legend
            'legend_bg': '#1C2529',       # Very dark legend background
            'legend_border': '#37474F',   # Legend border
        }

        self._legend_items = [
            ('🎨 دهان', self._colors['paint']),
            ('🧱 سيراميك جدران', self._colors['ceramic']),
            ('🟫 أرضية عادية', self._colors['floor']),
            ('⬜ أرضية سيراميك', self._colors['floor_ceramic']),
            ('☁️ سقف', self._colors['ceiling']),
            ('🚪 أبواب', self._colors['door']),
            ('🪟 نوافذ', self._colors['window']),
        ]

    # === Public API ===
    def render_room(self, room) -> None:
        """Assign room and trigger redraw."""
        self._current_room = room
        self._draw()

    # === Internal helpers ===
    def _on_resize(self, event) -> None:
        if event.width <= 1:
            return
        self._draw()

    def _draw(self) -> None:
        self._canvas.delete('all')
        self._draw_grid()

        room = self._current_room
        if not room:
            self._draw_message('لا توجد غرفة محددة')
            return

        adapter = RoomAdapter(room)
        walls = self._normalize_walls(adapter.walls)
        if not walls:
            self._draw_message('أضف الجدران أولاً لعرض المخطط')
            return

        total_length = sum(max(w.length, 0.01) for w in walls)
        max_height = max(w.height for w in walls)
        canvas_width = max(int(self._canvas.winfo_width()), self._min_width)
        canvas_height = max(int(self._canvas.winfo_height()), self._height)

        summary = None
        if hasattr(self.app, 'get_room_opening_summary'):
            try:
                summary = self.app.get_room_opening_summary(room)
            except Exception:
                summary = None
        self._draw_room_header(room, adapter, summary, canvas_width)
        
        # Layout calculations
        header_height = 90
        padding_top = header_height + 40  # Allow room for header + ceiling strip
        padding_bottom = 90  # Extra room for measurement scale
        usable_width = max(canvas_width - (self._padding * 2), 100)
        usable_height = max(canvas_height - (padding_top + padding_bottom), 100)
        
        scale_x = usable_width / total_length
        scale_y = usable_height / max_height
        
        baseline_y = padding_top + usable_height
        total_width_px = int(total_length * scale_x) + self._padding * 2
        
        # Extend scroll region
        self._canvas.configure(scrollregion=(0, 0, total_width_px, canvas_height))

        # Draw Ceiling Strip (Top)
        self._draw_ceiling_strip(room, self._padding, 20, total_width_px - self._padding * 2, 30)

        # Draw Floor Strip (Bottom)
        self._draw_floor_strip(room, self._padding, baseline_y + 20, total_width_px - self._padding * 2, 30)

        # Floor line
        self._canvas.create_line(
            self._padding,
            baseline_y,
            total_width_px - self._padding,
            baseline_y,
            fill=self._colors['outline'],
            width=2,
        )
        self._draw_measurement_scale(self._padding, baseline_y + 36, total_length, scale_x)

        cursor_x = self._padding
        for wall in walls:
            length_px = max(wall.length * scale_x, 24)
            height_px = max(wall.height * scale_y, 8)
            self._draw_wall(wall, cursor_x, baseline_y, length_px, height_px)
            cursor_x += length_px + self._gap_px

        self._draw_legend(canvas_width - self._padding - 220, self._padding)
        self._draw_unassigned_openings(room, walls, canvas_width - self._padding - 220, self._padding + 160)

    def _draw_ceiling_strip(self, room, x: float, y: float, width: float, height: float) -> None:
        """Draw ceiling finish strip with enhanced visuals."""
        adapter = RoomAdapter(room)
        breakdown = adapter.ceramic_breakdown or {}
        is_ceramic = float(breakdown.get('ceiling', 0.0) or 0.0) > 0
        
        if is_ceramic:
            fill = self._colors['ceramic']
            pattern_color = self._colors['ceramic_pattern']
            text_color = self._colors['text']
            icon = "🧱"
        else:
            fill = self._colors['ceiling']
            pattern_color = self._colors['ceiling_pattern']
            text_color = self._colors['text_dark']
            icon = "☁️"
        
        # Draw with rounded corners effect (using multiple rectangles)
        corner = 4
        self._canvas.create_rectangle(x + corner, y, x + width - corner, y + height, fill=fill, outline='')
        self._canvas.create_rectangle(x, y + corner, x + width, y + height - corner, fill=fill, outline='')
        self._canvas.create_oval(x, y, x + corner*2, y + corner*2, fill=fill, outline='')
        self._canvas.create_oval(x + width - corner*2, y, x + width, y + corner*2, fill=fill, outline='')
        self._canvas.create_oval(x, y + height - corner*2, x + corner*2, y + height, fill=fill, outline='')
        self._canvas.create_oval(x + width - corner*2, y + height - corner*2, x + width, y + height, fill=fill, outline='')
        
        # Border
        self._canvas.create_rectangle(x, y, x + width, y + height, fill='', outline=self._colors['outline_light'], width=1)
        
        label = f"{icon} سقف: {'سيراميك' if is_ceramic else 'دهان'}"
        self._canvas.create_text(x + width/2, y + height/2, text=label, fill=text_color, font=('Segoe UI', 9, 'bold'))
        
        if is_ceramic:
            self._draw_ceramic_pattern_enhanced(x, y, x + width, y + height, step=18, color=pattern_color)

    def _draw_floor_strip(self, room, x: float, y: float, width: float, height: float) -> None:
        """Draw floor finish strip with enhanced visuals."""
        adapter = RoomAdapter(room)
        breakdown = adapter.ceramic_breakdown or {}
        is_ceramic = float(breakdown.get('floor', 0.0) or 0.0) > 0
        
        if is_ceramic:
            fill = self._colors['floor_ceramic']
            pattern_color = self._colors['floor_ceramic_pattern']
            text_color = self._colors['text']
            icon = "⬜"
        else:
            fill = self._colors['floor']
            pattern_color = self._colors['floor_pattern']
            text_color = self._colors['text_dark']
            icon = "🟫"
        
        # Draw with rounded corners effect
        corner = 4
        self._canvas.create_rectangle(x + corner, y, x + width - corner, y + height, fill=fill, outline='')
        self._canvas.create_rectangle(x, y + corner, x + width, y + height - corner, fill=fill, outline='')
        self._canvas.create_oval(x, y, x + corner*2, y + corner*2, fill=fill, outline='')
        self._canvas.create_oval(x + width - corner*2, y, x + width, y + corner*2, fill=fill, outline='')
        self._canvas.create_oval(x, y + height - corner*2, x + corner*2, y + height, fill=fill, outline='')
        self._canvas.create_oval(x + width - corner*2, y + height - corner*2, x + width, y + height, fill=fill, outline='')
        
        # Border
        self._canvas.create_rectangle(x, y, x + width, y + height, fill='', outline=self._colors['outline_light'], width=1)
        
        label = f"{icon} أرضية: {'سيراميك' if is_ceramic else 'قياسي'}"
        self._canvas.create_text(x + width/2, y + height/2, text=label, fill=text_color, font=('Segoe UI', 9, 'bold'))
        
        if is_ceramic:
            self._draw_ceramic_pattern_enhanced(x, y, x + width, y + height, step=18, color=pattern_color)

    def _draw_room_header(self, room, adapter: RoomAdapter, summary: dict, canvas_width: int) -> None:
        """Draw enhanced descriptive room header card."""
        width = min(canvas_width - self._padding * 2, 480)
        height = 82
        x = self._padding
        y = 10
        
        # Multi-layer shadow for depth effect
        for offset in [4, 3, 2]:
            self._canvas.create_rectangle(
                x + offset, y + offset, x + width + offset, y + height + offset,
                fill=self._colors['card_shadow'], outline=''
            )
        
        # Main card
        self._canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=self._colors['card_bg'],
            outline=self._colors['card_border'], width=1
        )
        
        # Top accent line
        self._canvas.create_line(x, y + 1, x + width, y + 1, 
                                 fill=self._colors['info'], width=3)
        
        # Room name (large)
        title = adapter.name or 'غرفة بدون اسم'
        self._canvas.create_text(x + 18, y + 20, text=f"🏠 {title}", anchor='w',
                                  font=('Segoe UI Semibold', 13), fill=self._colors['text'])
        
        # Room type and dimensions
        subtitle = f"{adapter.room_type}  •  {adapter.area:.2f} م²  •  محيط {adapter.perimeter:.2f} م"
        self._canvas.create_text(x + 18, y + 42, text=subtitle, anchor='w',
                                  font=('Segoe UI', 9), fill=self._colors['subtle'])
        
        # Wall info
        metric = f"📐 ارتفاع {adapter.wall_height:.2f} م  |  عدد الجدران: {len(adapter.walls)}"
        self._canvas.create_text(x + 18, y + 60, text=metric, anchor='w',
                                  font=('Segoe UI', 9), fill=self._colors['subtle'])
        
        # Opening chips (right side)
        door_count = summary.get('door_count', 0) if summary else 0
        window_count = summary.get('window_count', 0) if summary else 0
        chip_y = y + 50
        chip_x = x + width - 16
        chip_font = ('Segoe UI', 9, 'bold')
        
        chips = [
            (f"🚪 {door_count}", self._colors['door'], door_count > 0),
            (f"🪟 {window_count}", self._colors['info'], window_count > 0),
        ]
        
        for text, color, show in reversed(chips):
            if not show:
                continue
            temp = self._canvas.create_text(0, 0, text=text, font=chip_font)
            bbox = self._canvas.bbox(temp)
            self._canvas.delete(temp)
            if not bbox:
                continue
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            padding = 8
            chip_x -= (tw + padding * 2 + 10)
            
            # Chip background
            self._canvas.create_rectangle(
                chip_x, chip_y - th/2 - padding,
                chip_x + tw + padding * 2, chip_y + th/2 + padding,
                fill=self._colors['badge_bg'], outline=color, width=1
            )
            # Chip text
            self._canvas.create_text(
                chip_x + tw/2 + padding, chip_y,
                text=text, font=chip_font, fill=self._colors['text']
            )

    def _draw_measurement_scale(self, x: float, y: float, total_length: float, scale_x: float) -> None:
        """Draw enhanced measurement scale with better visibility."""
        if total_length <= 0:
            return
        length_px = total_length * scale_x
        color = self._colors['scale']
        text_color = self._colors['scale_text']
        
        # Main scale line with thicker appearance
        self._canvas.create_line(x, y, x + length_px, y, fill=color, width=3)
        
        step = self._select_scale_step(total_length)
        tick = 8
        current = 0.0
        
        while current <= total_length + 0.001:
            px = x + current * scale_x
            # Tick marks
            self._canvas.create_line(px, y - tick, px, y + tick, fill=color, width=2)
            # Scale labels
            self._canvas.create_text(px, y + 16, text=f"{current:.0f}", 
                                     fill=text_color, font=('Segoe UI', 8, 'bold'))
            current += step
        
        # Unit label
        self._canvas.create_text(x + length_px / 2, y + 30, text="متر", 
                                 fill=self._colors['subtle'], font=('Segoe UI', 8))
        
        # Total length indicator with styled box
        total_text = f"📏 إجمالي: {total_length:.2f} م"
        temp = self._canvas.create_text(0, 0, text=total_text, font=('Segoe UI', 9, 'bold'))
        bbox = self._canvas.bbox(temp)
        self._canvas.delete(temp)
        if bbox:
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = x + length_px + 20
            ty = y
            pad = 6
            self._canvas.create_rectangle(tx - pad, ty - th/2 - pad, tx + tw + pad, ty + th/2 + pad,
                                          fill=self._colors['legend_bg'], outline=color, width=1)
            self._canvas.create_text(tx + tw/2, ty, text=total_text, 
                                     fill=text_color, font=('Segoe UI', 9, 'bold'))

    @staticmethod
    def _select_scale_step(total_length: float) -> float:
        if total_length <= 6:
            return 1
        if total_length <= 15:
            return 2
        if total_length <= 40:
            return 5
        return 10

    def _draw_unassigned_openings(self, room, walls: List[Wall], x: float, y: float) -> None:
        """Draw list of openings not assigned to any wall with enhanced warning styling."""
        # Gather all assigned openings from the walls we just drew
        assigned_ids = set()
        for wall in walls:
            assigned = getattr(wall, 'assigned_openings', []) or []
            assigned_ids.update(assigned)
            
        # Get all room openings
        summary = self.app.get_room_opening_summary(room)
        all_ids = set(summary.get('door_ids', []) + summary.get('window_ids', []))
        
        unassigned = all_ids - assigned_ids
        if not unassigned:
            return
            
        # Enhanced warning box
        width = 200
        item_height = 20
        height = len(unassigned) * item_height + 40
        bg = self._colors['warning_bg']
        text_color = self._colors['text']
        warning_color = self._colors['warning']
        
        # Shadow
        self._canvas.create_rectangle(x + 2, y + 2, x + width + 2, y + height + 2, 
                                       fill=self._colors['card_shadow'], outline='')
        
        # Warning box with red border
        self._canvas.create_rectangle(x, y, x + width, y + height, 
                                       fill=bg, outline=warning_color, width=2)
        
        # Warning header
        self._canvas.create_text(x + 10, y + 14, text='⚠️ فتحات غير مرتبطة', anchor='w', 
                                 fill=warning_color, font=('Segoe UI', 9, 'bold'))
        
        # Separator
        self._canvas.create_line(x + 8, y + 28, x + width - 8, y + 28, 
                                 fill=warning_color, width=1, dash=(3, 2))
        
        offset_y = y + 38
        for oid in unassigned:
            # Bullet point
            self._canvas.create_oval(x + 12, offset_y - 3, x + 18, offset_y + 3, 
                                     fill=warning_color, outline='')
            self._canvas.create_text(x + 24, offset_y, text=oid, anchor='w', 
                                     fill=text_color, font=('Segoe UI', 8))
            offset_y += item_height

    def _draw_grid(self) -> None:
        """Subtle background grid with enhanced styling."""
        w = max(self._canvas.winfo_width(), self._min_width)
        h = max(self._canvas.winfo_height(), self._height)
        step = 50
        grid_color = self._colors['grid']
        
        # Vertical lines
        for x in range(0, w, step):
            self._canvas.create_line(x, 0, x, h, fill=grid_color, width=1, dash=(2, 6))
        
        # Horizontal lines
        for y in range(0, h, step):
            self._canvas.create_line(0, y, w, y, fill=grid_color, width=1, dash=(2, 6))

    def _draw_wall(self, wall: Wall, x1: float, baseline: float, width_px: float, height_px: float) -> None:
        x2 = x1 + width_px
        y2 = baseline
        y1 = baseline - height_px
        outline = self._colors['outline']

        # Enhanced Wall card background with gradient-like effect and shadow
        card_pad = 14
        card_top = y1 - 30
        card_bottom = y2 + 26
        card_left = x1 - card_pad
        card_right = x2 + card_pad
        
        # Multi-layer shadow for depth
        for offset in [6, 4, 2]:
            alpha = 0.3 - (offset * 0.05)
            self._canvas.create_rectangle(
                card_left + offset,
                card_top + offset,
                card_right + offset,
                card_bottom + offset,
                fill=self._colors['card_shadow'],
                outline=''
            )
        
        # Main card with subtle gradient simulation (top lighter)
        self._canvas.create_rectangle(
            card_left,
            card_top,
            card_right,
            card_bottom,
            fill=self._colors['card_bg'],
            outline=self._colors['card_border'],
            width=1
        )
        # Top highlight line
        self._canvas.create_line(
            card_left + 1, card_top + 1, card_right - 1, card_top + 1,
            fill=self._colors['card_bg_gradient'], width=2
        )
        
        self._draw_wall_badge(wall, card_left + 14, card_top + 16)

        # Paint / ceramic logic with enhanced split band
        if wall.has_partial_ceramic and wall.height > 0:
            ratio = max(0.0, min(1.0, wall.ceramic_height / wall.height))
            band_h = max(height_px * ratio, 6)
            split_y = y2 - band_h

            # Top: paint with gradient effect
            self._draw_gradient_rect(x1, y1, x2, split_y, 
                                      self._colors['paint'], self._colors['paint_dark'], 
                                      direction='vertical')
            self._canvas.create_rectangle(x1, y1, x2, split_y, fill='', outline=outline, width=2)
            
            # Bottom: ceramic with enhanced tile pattern
            self._canvas.create_rectangle(x1, split_y, x2, y2, fill=self._colors['ceramic'], outline=outline, width=2)
            self._draw_ceramic_pattern_enhanced(x1, split_y, x2, y2, color=self._colors['ceramic_pattern'])
            
            # Decorative separator line
            self._canvas.create_line(x1 - 4, split_y, x2 + 4, split_y, 
                                     fill=self._colors['dimension'], width=2, dash=(6, 3))
            # Height indicator for ceramic
            mid_x = x2 + 8
            self._canvas.create_text(mid_x, split_y + band_h/2, 
                                     text=f"⬆ {wall.ceramic_height:.1f}م", 
                                     fill=self._colors['dimension_text'], 
                                     font=('Segoe UI', 7, 'bold'), angle=0)
            
        elif wall.surface_type == 'سيراميك':
            self._canvas.create_rectangle(x1, y1, x2, y2, fill=self._colors['ceramic'], outline=outline, width=2)
            self._draw_ceramic_pattern_enhanced(x1, y1, x2, y2, color=self._colors['ceramic_pattern'])
        elif wall.surface_type == 'دهان':
            self._draw_gradient_rect(x1, y1, x2, y2, 
                                      self._colors['paint'], self._colors['paint_dark'],
                                      direction='vertical')
            self._canvas.create_rectangle(x1, y1, x2, y2, fill='', outline=outline, width=2)
        else:
            fill = self.app.colors.get('bg_primary', '#2b2b2b')
            self._canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=2, dash=(4, 2))
            # "Undefined" pattern
            self._canvas.create_text((x1+x2)/2, (y1+y2)/2, text="؟", 
                                     fill=self._colors['subtle'], font=('Segoe UI', 16, 'bold'))

        self._draw_wall_labels(wall, x1, x2, y1, y2)
        self._draw_wall_dimensions(wall, x1, x2, y1, y2)
        self._draw_wall_openings(wall, x1, y2, width_px, height_px)

    def _draw_gradient_rect(self, x1: float, y1: float, x2: float, y2: float, 
                            color_top: str, color_bottom: str, direction: str = 'vertical') -> None:
        """Draw a simple gradient effect using multiple lines."""
        if direction == 'vertical':
            steps = min(int(y2 - y1), 20)
            if steps < 2:
                self._canvas.create_rectangle(x1, y1, x2, y2, fill=color_top, outline='')
                return
            step_h = (y2 - y1) / steps
            for i in range(steps):
                # Simple interpolation - just alternate between colors
                color = color_top if i < steps // 2 else color_bottom
                self._canvas.create_rectangle(x1, y1 + i*step_h, x2, y1 + (i+1)*step_h + 1, 
                                              fill=color, outline='')
        else:
            self._canvas.create_rectangle(x1, y1, x2, y2, fill=color_top, outline='')

    def _draw_ceramic_pattern(self, x1: float, y1: float, x2: float, y2: float, step: int = 14) -> None:
        """Legacy method - calls enhanced version."""
        self._draw_ceramic_pattern_enhanced(x1, y1, x2, y2, step, self._colors.get('ceramic_pattern', '#546E7A'))

    def _draw_ceramic_pattern_enhanced(self, x1: float, y1: float, x2: float, y2: float, 
                                        step: int = 16, color: str = None) -> None:
        """Draw realistic tile grid pattern with offset rows."""
        if color is None:
            color = self._colors.get('ceramic_pattern', '#546E7A')
        
        # Vertical lines
        for i, x in enumerate(range(int(x1), int(x2), step)):
            # Offset every other row for brick effect
            offset = (step // 2) if i % 2 else 0
            self._canvas.create_line(x, y1, x, y2, fill=color, width=1)
        
        # Horizontal lines  
        for y in range(int(y1), int(y2), step):
            self._canvas.create_line(x1, y, x2, y, fill=color, width=1)
        
        # Add subtle highlight on alternate tiles
        accent = self._colors.get('ceramic_accent', '#90A4AE')
        for i, x in enumerate(range(int(x1), int(x2) - step, step * 2)):
            for j, y in enumerate(range(int(y1), int(y2) - step, step * 2)):
                if (i + j) % 2 == 0:
                    self._canvas.create_rectangle(
                        x + 2, y + 2, x + step - 2, y + step - 2,
                        fill='', outline=accent, width=1
                    )

    def _draw_wall_labels(self, wall: Wall, x1: float, x2: float, y1: float, y2: float) -> None:
        center_x = (x1 + x2) / 2
        text_color = self._colors['text']
        subtle = self._colors['subtle']
        self._canvas.create_text(center_x, y1 - 12, text=wall.name, fill=text_color, font=('Segoe UI', 9, 'bold'))
        dims = f"{wall.length:.2f}م"
        self._canvas.create_text(center_x, y2 + 10, text=dims, fill=subtle, font=('Segoe UI', 8))

    def _draw_wall_openings(self, wall: Wall, x_start: float, base_y: float,
                             width_px: float, height_px: float) -> None:
        openings = getattr(wall, 'assigned_openings', []) or []
        if not openings:
            return

        margin = 8
        cursor_x = x_start + margin

        for oid in openings:
            data = self.app._get_opening_dict_by_name(oid)
            if not data:
                continue
            width_m = max(float(data.get('w', 0.9) or 0.9), 0.2)
            height_m = max(float(data.get('h', 2.1) or 2.1), 0.2)
            glass_area = float(data.get('glass', 0.0) or 0.0)
            is_window = glass_area > 0
            default_placement = 1.0 if is_window else 0.0
            placement = float(data.get('placement_height', default_placement) or default_placement)
            opening_width = max(width_m / max(wall.length, 0.01), 0.05) * width_px
            opening_height = max(height_m / max(wall.height, 0.01), 0.05) * height_px
            
            # Prevent overflow
            if cursor_x + opening_width > x_start + width_px:
                cursor_x = x_start + width_px - opening_width - margin
            x1 = cursor_x
            x2 = cursor_x + opening_width
            placement_ratio = min(max(placement / max(wall.height, 0.01), 0.0), 1.0)
            y2 = base_y - placement_ratio * height_px
            y1 = y2 - opening_height

            if is_window:
                self._draw_window_enhanced(x1, y1, x2, y2, width_m, height_m)
            else:
                self._draw_door_enhanced(x1, y1, x2, y2, width_m, height_m)

            cursor_x = x2 + margin

    def _draw_window_enhanced(self, x1: float, y1: float, x2: float, y2: float, 
                               width_m: float, height_m: float) -> None:
        """Draw a detailed window with frame, glass, and grid."""
        frame_color = self._colors['window_frame']
        glass_color = self._colors['window']
        cross_color = self._colors['window_cross']
        
        frame_width = 4
        
        # Outer frame shadow
        self._canvas.create_rectangle(x1 + 2, y1 + 2, x2 + 2, y2 + 2, 
                                       fill=self._colors['card_shadow'], outline='')
        
        # Outer frame
        self._canvas.create_rectangle(x1, y1, x2, y2, fill=frame_color, outline='#0D47A1', width=2)
        
        # Inner glass area
        inner_x1, inner_y1 = x1 + frame_width, y1 + frame_width
        inner_x2, inner_y2 = x2 - frame_width, y2 - frame_width
        
        # Glass with reflection effect
        self._canvas.create_rectangle(inner_x1, inner_y1, inner_x2, inner_y2, 
                                       fill=glass_color, outline=cross_color, width=1)
        
        # Glass highlight (reflection simulation)
        highlight_w = (inner_x2 - inner_x1) * 0.3
        self._canvas.create_polygon(
            inner_x1, inner_y1,
            inner_x1 + highlight_w, inner_y1,
            inner_x1, inner_y1 + highlight_w,
            fill='#BBDEFB', outline=''
        )
        
        # Window grid (cross pattern)
        mid_x = (inner_x1 + inner_x2) / 2
        mid_y = (inner_y1 + inner_y2) / 2
        self._canvas.create_line(mid_x, inner_y1, mid_x, inner_y2, fill=frame_color, width=3)
        self._canvas.create_line(inner_x1, mid_y, inner_x2, mid_y, fill=frame_color, width=3)
        
        # Dimension label
        label = f"{width_m:.2f}×{height_m:.2f}"
        self._canvas.create_text((x1 + x2) / 2, y1 - 10, text=label, 
                                 fill=self._colors['text'], font=('Segoe UI', 7, 'bold'))
        # Window icon
        self._canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text="🪟", 
                                 font=('Segoe UI', 10))

    def _draw_door_enhanced(self, x1: float, y1: float, x2: float, y2: float,
                            width_m: float, height_m: float) -> None:
        """Draw a detailed door with frame, panels, and handle."""
        door_color = self._colors['door']
        frame_color = self._colors['door_frame']
        panel_color = self._colors['door_panel']
        handle_color = self._colors['door_handle']
        
        frame_width = 4
        
        # Door frame shadow
        self._canvas.create_rectangle(x1 + 2, y1 + 2, x2 + 2, y2 + 2,
                                       fill=self._colors['card_shadow'], outline='')
        
        # Door frame
        self._canvas.create_rectangle(x1, y1, x2, y2, fill=frame_color, outline='#3E2723', width=2)
        
        # Door body
        inner_x1, inner_y1 = x1 + frame_width, y1 + frame_width
        inner_x2, inner_y2 = x2 - frame_width, y2 - frame_width
        self._canvas.create_rectangle(inner_x1, inner_y1, inner_x2, inner_y2,
                                       fill=door_color, outline=frame_color, width=1)
        
        # Door panels (two panels typical)
        panel_margin = 4
        panel_height = (inner_y2 - inner_y1 - panel_margin * 3) / 2
        
        if panel_height > 10:  # Only draw panels if door is large enough
            # Top panel
            self._canvas.create_rectangle(
                inner_x1 + panel_margin, inner_y1 + panel_margin,
                inner_x2 - panel_margin, inner_y1 + panel_margin + panel_height,
                fill=panel_color, outline=frame_color, width=1
            )
            # Bottom panel
            self._canvas.create_rectangle(
                inner_x1 + panel_margin, inner_y2 - panel_margin - panel_height,
                inner_x2 - panel_margin, inner_y2 - panel_margin,
                fill=panel_color, outline=frame_color, width=1
            )
        
        # Door handle (on the right side)
        handle_x = inner_x2 - 8
        handle_y = (inner_y1 + inner_y2) / 2
        handle_radius = 4
        self._canvas.create_oval(
            handle_x - handle_radius, handle_y - handle_radius,
            handle_x + handle_radius, handle_y + handle_radius,
            fill=handle_color, outline='#9E9E9E', width=1
        )
        # Handle plate
        self._canvas.create_rectangle(
            handle_x - 3, handle_y - 12,
            handle_x + 3, handle_y + 12,
            fill=handle_color, outline='#9E9E9E', width=1
        )
        
        # Dimension label
        label = f"{width_m:.2f}×{height_m:.2f}"
        self._canvas.create_text((x1 + x2) / 2, y1 - 10, text=label,
                                 fill=self._colors['text'], font=('Segoe UI', 7, 'bold'))

    def _draw_wall_badge(self, wall: Wall, x: float, y: float) -> None:
        """Draw compact badge showing openings count on a wall with enhanced styling."""
        counts = self._get_wall_opening_counts(wall)
        total = counts['door'] + counts['window'] + counts['other']
        if total == 0:
            return
        text = []
        if counts['door']:
            text.append(f"🚪 {counts['door']}")
        if counts['window']:
            text.append(f"🪟 {counts['window']}")
        if counts['other']:
            text.append(f"⚙️ {counts['other']}")
        label = "  ·  ".join(text)
        padding_x = 12
        padding_y = 6
        font = ('Segoe UI', 8, 'bold')
        width = self._canvas.create_text(0, 0, text=label, font=font)
        bbox = self._canvas.bbox(width)
        self._canvas.delete(width)
        if not bbox:
            return
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Enhanced badge with rounded appearance
        badge_x1 = x - padding_x
        badge_y1 = y - padding_y
        badge_x2 = x + text_width + padding_x
        badge_y2 = y + text_height + padding_y
        
        # Badge shadow
        self._canvas.create_rectangle(
            badge_x1 + 2, badge_y1 + 2, badge_x2 + 2, badge_y2 + 2,
            fill=self._colors['card_shadow'], outline=''
        )
        # Badge body with teal color
        self._canvas.create_rectangle(
            badge_x1, badge_y1, badge_x2, badge_y2,
            fill=self._colors['badge_bg'],
            outline=self._colors['badge_border'],
            width=1
        )
        self._canvas.create_text(
            x + text_width / 2, y + text_height / 2, 
            text=label, font=font, fill=self._colors['badge_text']
        )

    def _draw_wall_dimensions(self, wall: Wall, x1: float, x2: float, y1: float, y2: float) -> None:
        """Draw wall length/height dimension ticks around the card."""
        color = self._colors['scale']
        # Horizontal (length)
        mid_y = y1 - 18
        self._canvas.create_line(x1, mid_y, x2, mid_y, fill=color, dash=(3, 3))
        self._canvas.create_line(x1, mid_y - 4, x1, mid_y + 4, fill=color)
        self._canvas.create_line(x2, mid_y - 4, x2, mid_y + 4, fill=color)
        self._canvas.create_text((x1 + x2) / 2, mid_y - 8, text=f"{wall.length:.2f} م", fill=color, font=('Segoe UI', 8, 'italic'))
        # Vertical (height)
        side_x = x2 + 18
        self._canvas.create_line(side_x, y1, side_x, y2, fill=color, dash=(3, 3))
        self._canvas.create_line(side_x - 4, y1, side_x + 4, y1, fill=color)
        self._canvas.create_line(side_x - 4, y2, side_x + 4, y2, fill=color)
        self._canvas.create_text(side_x + 16, (y1 + y2) / 2, text=f"{wall.height:.2f} م", fill=color, font=('Segoe UI', 8, 'italic'), angle=90)

    def _get_wall_opening_counts(self, wall: Wall) -> dict:
        counts = {'door': 0, 'window': 0, 'other': 0}
        for oid in getattr(wall, 'assigned_openings', []) or []:
            category = self._guess_opening_category(oid)
            if category in counts:
                counts[category] += 1
            else:
                counts['other'] += 1
        return counts

    def _guess_opening_category(self, opening_id: str) -> str:
        """Best-effort guess of opening category."""
        if not opening_id:
            return 'other'
        oid = opening_id.upper()
        if oid.startswith('D'):
            return 'door'
        if oid.startswith('W'):
            return 'window'
        # Consult project for better accuracy
        if hasattr(self.app, 'project'):
            for door in getattr(self.app.project, 'doors', []) or []:
                name = door.get('name') if isinstance(door, dict) else getattr(door, 'name', '')
                if name == opening_id:
                    return 'door'
            for win in getattr(self.app.project, 'windows', []) or []:
                name = win.get('name') if isinstance(win, dict) else getattr(win, 'name', '')
                if name == opening_id:
                    return 'window'
        return 'other'

    def _draw_legend(self, x: float, y: float) -> None:
        """Draw enhanced color legend with better styling."""
        text_color = self._colors['text']
        background = self._colors['legend_bg']
        border_color = self._colors['legend_border']
        padding = 10
        width = 180
        item_height = 22
        height = len(self._legend_items) * item_height + padding * 2 + 24
        
        # Legend shadow
        self._canvas.create_rectangle(x + 3, y + 3, x + width + 3, y + height + 3, 
                                       fill=self._colors['card_shadow'], outline='')
        
        # Legend background
        self._canvas.create_rectangle(x, y, x + width, y + height, 
                                       fill=background, outline=border_color, width=1)
        
        # Title with icon
        self._canvas.create_text(x + padding, y + 14, text='🎨 دليل الألوان', anchor='w', 
                                 fill=text_color, font=('Segoe UI', 10, 'bold'))
        
        # Separator line
        self._canvas.create_line(x + padding, y + 26, x + width - padding, y + 26, 
                                 fill=border_color, width=1)
        
        offset_y = y + 36
        for label, color in self._legend_items:
            # Color swatch with border
            swatch_size = 16
            self._canvas.create_rectangle(
                x + padding, offset_y - swatch_size/2, 
                x + padding + swatch_size, offset_y + swatch_size/2, 
                fill=color, outline=self._colors['outline_light'], width=1
            )
            # Label
            self._canvas.create_text(x + padding + swatch_size + 8, offset_y, text=label, anchor='w', 
                                     fill=text_color, font=('Segoe UI', 9))
            offset_y += item_height

    def _draw_message(self, message: str) -> None:
        self._canvas.create_text(
            self._canvas.winfo_width() / 2,
            self._canvas.winfo_height() / 2,
            text=message,
            fill=self.app.colors.get('text_muted', '#9E9E9E'),
            font=('Segoe UI', 11, 'italic')
        )

    @staticmethod
    def _normalize_walls(walls: Iterable) -> List[Wall]:
        normalized: List[Wall] = []
        for wall in walls or []:
            if isinstance(wall, Wall):
                normalized.append(wall)
                continue
            try:
                normalized.append(Wall.from_dict(wall))
            except Exception:
                continue
        return [w for w in normalized if w.length > 0 and w.height > 0]
