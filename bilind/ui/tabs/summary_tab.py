"""
Summary Tab Module - Project summary and export functionality.

This module provides the UI for the Summary tab, allowing users to:
- View comprehensive project summary
- Refresh summary with latest data
- Copy summary to clipboard
- Export to CSV, Excel, PDF
- Insert table into AutoCAD
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import TYPE_CHECKING

from .base_tab import BaseTab

if TYPE_CHECKING:
    from ...bilind_main import BilindEnhanced


class SummaryTab(BaseTab):
    """
    Summary tab for project overview and exports.
    
    Features:
    - Text-based project summary
    - Refresh button to update data
    - Copy to clipboard
    - Export to multiple formats (CSV, Excel, PDF)
    - Insert table into AutoCAD
    """
    def __init__(self, parent: tk.Widget, app: 'BilindEnhanced'):
        super().__init__(parent, app)
        self.summary_text = None

    def create(self) -> tk.Frame:
        """
        Create and return the summary tab frame.
        
        Returns:
            tk.Frame: Configured summary tab
        """
        container = tk.Frame(self.parent, bg=self.app.colors['bg_secondary'])
        
        # Header
        self._create_header(
            container,
            "Project Summary & Exports",
            "Create a detailed material summary, copy or export it with one click."
        )
        
        # Toolbar with export buttons - MOVED TO TOP for visibility
        self._create_toolbar(container)
        
        # Room type statistics panel
        self._create_room_type_stats(container)
        
        # Summary text area
        self._create_summary_text(container)
        
        # Footer hint
        self._create_footer_hint(container)

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
    
    def _create_room_type_stats(self, parent):
        """Create room type statistics panel."""
        stats_frame = ttk.LabelFrame(
            parent,
            text="🏠 إحصائيات الغرف",
            style='Card.TLabelframe',
            padding=(12, 10)
        )
        stats_frame.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        # Create container for dynamic stats labels
        self.stats_container = ttk.Frame(stats_frame, style='Main.TFrame')
        self.stats_container.pack(fill=tk.X)
        
        # Initial placeholder
        self.stats_labels = []
        placeholder = ttk.Label(
            self.stats_container,
            text="لا توجد غرف. اختر غرف من AutoCAD أو أضفها يدوياً.",
            foreground=self.app.colors['text_muted'],
            style='Caption.TLabel'
        )
        placeholder.pack(pady=10)
        self.stats_labels.append(placeholder)
        
        # Opening Statistics Panel
        openings_frame = ttk.LabelFrame(
            parent,
            text="🚪🪟 إحصائيات الأبواب والنوافذ",
            style='Card.TLabelframe',
            padding=(12, 10)
        )
        openings_frame.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        self.openings_stats_container = ttk.Frame(openings_frame, style='Main.TFrame')
        self.openings_stats_container.pack(fill=tk.X)
        
        self.openings_labels = []
    
    def _update_opening_stats(self):
        """Update door/window statistics display with actual vs appearance counts."""
        if not hasattr(self, 'openings_stats_container'):
            return
        
        # Clear existing labels
        for label in self.openings_labels:
            try:
                label.destroy()
            except:
                pass
        self.openings_labels.clear()
        
        # Get opening counts from app
        try:
            counts = self.app.get_opening_counts()
        except Exception as e:
            print(f"Error getting opening counts: {e}")
            counts = {
                'actual_doors': len(self.app.project.doors),
                'actual_windows': len(self.app.project.windows),
                'total_door_qty': len(self.app.project.doors),
                'total_window_qty': len(self.app.project.windows),
                'appearance_doors': 0,
                'appearance_windows': 0,
                'shared_doors': 0,
                'shared_windows': 0,
            }
        
        if counts['actual_doors'] == 0 and counts['actual_windows'] == 0:
            placeholder = ttk.Label(
                self.openings_stats_container,
                text="لا توجد أبواب أو نوافذ. اختر من AutoCAD أو أضفها يدوياً.",
                foreground=self.app.colors['text_muted'],
                style='Caption.TLabel'
            )
            placeholder.pack(pady=10)
            self.openings_labels.append(placeholder)
            return
        
        # Main stats row
        main_row = ttk.Frame(self.openings_stats_container, style='Main.TFrame')
        main_row.pack(fill=tk.X, pady=(0, 8))
        self.openings_labels.append(main_row)  # Track frame to destroy later
        
        # Doors Card
        doors_card = ttk.Frame(main_row, style='Main.TFrame')
        doors_card.pack(side=tk.LEFT, padx=16, pady=4)
        
        door_title = ttk.Label(
            doors_card,
            text="🚪 الأبواب",
            style='Metrics.TLabel',
            font=('Segoe UI Semibold', 11)
        )
        door_title.pack(anchor=tk.W)
        
        door_actual = ttk.Label(
            doors_card,
            text=f"العدد الفعلي: {counts['total_door_qty']} باب",
            foreground=self.app.colors['accent'],
            style='Caption.TLabel',
            font=('Segoe UI Semibold', 10)
        )
        door_actual.pack(anchor=tk.W)
        
        if counts['appearance_doors'] != counts['total_door_qty']:
            door_appearance = ttk.Label(
                doors_card,
                text=f"الظهور في الغرف: {counts['appearance_doors']} (مشترك: {counts['shared_doors']})",
                foreground=self.app.colors['text_secondary'],
                style='Caption.TLabel',
                font=('Segoe UI', 9)
            )
            door_appearance.pack(anchor=tk.W)
        
        # Windows Card
        windows_card = ttk.Frame(main_row, style='Main.TFrame')
        windows_card.pack(side=tk.LEFT, padx=16, pady=4)
        
        window_title = ttk.Label(
            windows_card,
            text="🪟 النوافذ",
            style='Metrics.TLabel',
            font=('Segoe UI Semibold', 11)
        )
        window_title.pack(anchor=tk.W)
        
        window_actual = ttk.Label(
            windows_card,
            text=f"العدد الفعلي: {counts['total_window_qty']} نافذة",
            foreground=self.app.colors['accent'],
            style='Caption.TLabel',
            font=('Segoe UI Semibold', 10)
        )
        window_actual.pack(anchor=tk.W)
        
        if counts['appearance_windows'] != counts['total_window_qty']:
            window_appearance = ttk.Label(
                windows_card,
                text=f"الظهور في الغرف: {counts['appearance_windows']} (مشترك: {counts['shared_windows']})",
                foreground=self.app.colors['text_secondary'],
                style='Caption.TLabel',
                font=('Segoe UI', 9)
            )
            window_appearance.pack(anchor=tk.W)
            window_appearance.pack(anchor=tk.W)
        
        # Shared openings note
        if counts['shared_doors'] > 0 or counts['shared_windows'] > 0:
            note_frame = ttk.Frame(self.openings_stats_container, style='Main.TFrame')
            note_frame.pack(fill=tk.X, pady=(4, 0))
            self.openings_labels.append(note_frame)
            
            note = ttk.Label(
                note_frame,
                text="⚠️ ملاحظة: الأبواب/النوافذ المشتركة تظهر في أكثر من غرفة لكن تُحسب مرة واحدة للكميات",
                foreground=self.app.colors['warning'],
                style='Caption.TLabel',
                font=('Segoe UI', 9)
            )
            note.pack(anchor=tk.W, padx=8)
    
    def _update_room_type_stats(self):
        """Update room type statistics display."""
        if not hasattr(self, 'stats_container'):
            return
        
        # Clear existing labels
        for label in self.stats_labels:
            label.destroy()
        self.stats_labels.clear()
        
        # Calculate room type statistics
        room_types_data = {}
        total_rooms = 0
        total_area = 0.0
        
        for room in self.app.project.rooms:
            room_type = room.get('room_type', '[Not Set]') if isinstance(room, dict) else getattr(room, 'room_type', '[Not Set]')
            area = float(room.get('area', 0.0) if isinstance(room, dict) else getattr(room, 'area', 0.0) or 0.0)
            
            if room_type not in room_types_data:
                room_types_data[room_type] = {'count': 0, 'area': 0.0}
            room_types_data[room_type]['count'] += 1
            room_types_data[room_type]['area'] += area
            total_rooms += 1
            total_area += area
        
        if not room_types_data:
            placeholder = ttk.Label(
                self.stats_container,
                text="No rooms yet. Pick rooms from AutoCAD or add manually.",
                foreground=self.app.colors['text_muted'],
                style='Caption.TLabel'
            )
            placeholder.pack(pady=10)
            self.stats_labels.append(placeholder)
            return
        
        # Create grid layout for stats
        row = 0
        col = 0
        max_cols = 4
        
        # Sort by area (largest first)
        sorted_types = sorted(room_types_data.items(), key=lambda x: x[1]['area'], reverse=True)
        
        for room_type, data in sorted_types:
            count = data['count']
            area = data['area']
            percentage = (area / total_area * 100) if total_area > 0 else 0
            
            # Create card for each type
            card = ttk.Frame(self.stats_container, style='Main.TFrame')
            card.grid(row=row, column=col, padx=8, pady=6, sticky='ew')
            
            # Type name (bold, colored)
            type_label = ttk.Label(
                card,
                text=room_type,
                style='Metrics.TLabel',
                font=('Segoe UI Semibold', 10)
            )
            type_label.pack(anchor=tk.W)
            
            # Count and area
            stats_text = f"{count} room(s) • {area:.1f} m² ({percentage:.1f}%)"
            stats_label = ttk.Label(
                card,
                text=stats_text,
                foreground=self.app.colors['text_secondary'],
                style='Caption.TLabel',
                font=('Segoe UI', 9)
            )
            stats_label.pack(anchor=tk.W)
            
            self.stats_labels.extend([card, type_label, stats_label])
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Configure grid weights for equal distribution
        for i in range(max_cols):
            self.stats_container.columnconfigure(i, weight=1, uniform='stats')
    
    def _create_toolbar(self, parent):
        """Create toolbar with action buttons."""
        toolbar = ttk.Frame(parent, style='Toolbar.TFrame', padding=(12, 10))
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        # Core buttons
        self.create_button(toolbar, "🔄 تحديث", self.refresh_data, 'Accent.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(toolbar, "📋 نسخ", self.copy_summary, 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
        self.create_button(toolbar, "💾 تصدير CSV", self.app.export_csv, 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
        
        # Excel export button (always show - library is installed)
        self.create_button(toolbar, "📄 تصدير Excel", self.app.export_excel, 'Accent.TButton').pack(side=tk.LEFT, padx=4)
        
        # PDF export button (always show - library is installed)
        self.create_button(toolbar, "📕 تصدير PDF", self.app.export_pdf, 'Secondary.TButton').pack(side=tk.LEFT, padx=4)
        
        self.create_button(toolbar, "📊 إدراج جدول في AutoCAD", self.app.insert_table_to_autocad, 'Warning.TButton').pack(side=tk.LEFT, padx=4)
    
    def _create_summary_text(self, parent):
        """Create scrolled text widget for summary display."""
        text_frame = ttk.Frame(parent, style='Main.TFrame', padding=(12, 10))
        text_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        
        self.summary_text = scrolledtext.ScrolledText(
            text_frame,
            width=92,
            height=28,
            font=('Consolas', 10),
            wrap=tk.WORD
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Apply dark theme styling
        self.summary_text.configure(
            bg=self.app.colors['bg_primary'],
            fg=self.app.colors['accent_light'],
            insertbackground=self.app.colors['accent'],
            relief='flat',
            borderwidth=0,
            padx=10,
            pady=10
        )
    
    def _create_footer_hint(self, parent):
        """Create footer with usage hint."""
        ttk.Label(
            parent,
            text="💡 Use Refresh to update the numbers immediately after any modification.",
            style='Caption.TLabel'
        ).pack(anchor=tk.W, padx=18, pady=(0, 18))

    def refresh_data(self):
        """Generates and displays the project summary."""
        # Update room type statistics panel
        self._update_room_type_stats()
        
        # Update opening statistics panel
        self._update_opening_stats()
        
        # Update text summary
        if not self.summary_text:
            return

        summary = self._generate_summary_content()
        self.summary_text.config(state='normal')
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', summary)
        self.summary_text.config(state='disabled')
        self.app.update_status("Summary refreshed", icon="📊")

    def copy_summary(self):
        """Copies the summary text to the clipboard."""
        if not self.summary_text:
            return
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(self.summary_text.get('1.0', tk.END))
        self.app.update_status("Summary copied to clipboard", icon="📋")

    def _generate_summary_content(self) -> str:
        """Compiles all project data into a formatted string."""
        from datetime import datetime
        
        # Safely resolve current drawing name (AutoCAD doc may disconnect)
        doc_name = getattr(self.app, 'drawing_name', '')
        doc = getattr(self.app, 'doc', None)
        if doc is not None:
            try:
                doc_name = getattr(doc, 'Name', doc_name)
            except Exception as exc:
                # Silent fallback; summary will still render using cached name
                if hasattr(self.app, 'update_status'):
                    self.app.update_status(
                        "AutoCAD document unavailable; showing cached drawing name",
                        icon="⚠️"
                    )
        summary_lines = [
            f"BILIND Project Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Drawing: {doc_name or 'Unknown'}",
            "="*60,
            "\n"
        ]

        # Helpers to support both dicts and dataclass models
        def room_fields(room):
            if isinstance(room, dict):
                return (
                    room.get('name', 'Unknown'),
                    float(room.get('area', 0.0) or 0.0),
                    float(room.get('perim', 0.0) or 0.0),
                )
            return (
                getattr(room, 'name', 'Unknown'),
                float(getattr(room, 'area', 0.0) or 0.0),
                float(getattr(room, 'perimeter', 0.0) or 0.0),
            )

        def opening_type(op):
            if isinstance(op, dict):
                return op.get('type', 'Unknown')
            return getattr(op, 'material_type', 'Unknown')

        def opening_dims(op):
            if isinstance(op, dict):
                return float(op.get('w', 0.0) or 0.0), float(op.get('h', 0.0) or 0.0)
            return float(getattr(op, 'width', 0.0) or 0.0), float(getattr(op, 'height', 0.0) or 0.0)

        def opening_qty(op):
            if isinstance(op, dict):
                return int(op.get('qty', 0) or 0)
            return int(getattr(op, 'quantity', 0) or 0)

        def opening_stone(op):
            if isinstance(op, dict):
                return float(op.get('stone', 0.0) or 0.0)
            # Opening model exposes stone_linear
            return float(getattr(op, 'stone_linear', 0.0) or 0.0)

        def opening_weight(op):
            if isinstance(op, dict):
                return float(op.get('weight', 0.0) or 0.0)
            # Estimate from app.door_types when possible
            mat = getattr(op, 'material_type', '')
            qty = opening_qty(op)
            if getattr(op, 'opening_type', 'DOOR') == 'DOOR':
                per = self.app.door_types.get(mat, {}).get('weight', 0.0)
                return float(per * qty)
            return 0.0

        def opening_glass(op):
            if isinstance(op, dict):
                return float(op.get('glass', 0.0) or 0.0)
            if getattr(op, 'opening_type', 'DOOR') == 'WINDOW':
                try:
                    return float(op.calculate_glass_area())
                except Exception:
                    return 0.0
            return 0.0

        def wall_fields(wall):
            if isinstance(wall, dict):
                return (
                    wall.get('name', 'Wall'),
                    float(wall.get('gross', 0.0) or 0.0),
                    float(wall.get('deduct', 0.0) or 0.0),
                    float(wall.get('net', 0.0) or 0.0)
                )
            return (
                getattr(wall, 'name', 'Wall'),
                float(getattr(wall, 'gross_area', 0.0) or 0.0),
                float(getattr(wall, 'deduction_area', 0.0) or 0.0),
                float(getattr(wall, 'net_area', 0.0) or 0.0)
            )

        def finish_area(item):
            return float(getattr(item, 'area', item.get('area', 0.0) if isinstance(item, dict) else 0.0) or 0.0)

        def ceramic_area(z):
            if isinstance(z, dict):
                return float(z.get('area', 0.0) or 0.0)
            return float(getattr(z, 'area', 0.0) or 0.0)

        # --- Rooms ---
        summary_lines.append(f"Rooms ({len(self.app.project.rooms)} items)")
        summary_lines.append("-"*20)
        total_room_area = 0
        for room in self.app.project.rooms:
            name, area, perim = room_fields(room)
            summary_lines.append(f"- {name}: {area:.2f} m² (Perim: {perim:.2f} m)")
            total_room_area += area
        summary_lines.append(f"Total Room Area: {total_room_area:.2f} m²\n")
        
        # --- Room Type Breakdown ---
        room_types_summary = {}
        for room in self.app.project.rooms:
            room_type = room.get('room_type', '[Not Set]') if isinstance(room, dict) else getattr(room, 'room_type', '[Not Set]')
            area = float(room.get('area', 0.0) if isinstance(room, dict) else getattr(room, 'area', 0.0) or 0.0)
            
            if room_type not in room_types_summary:
                room_types_summary[room_type] = {'count': 0, 'total_area': 0.0}
            room_types_summary[room_type]['count'] += 1
            room_types_summary[room_type]['total_area'] += area
        
        if room_types_summary:
            summary_lines.append("Rooms by Type")
            summary_lines.append("-"*20)
            # Sort by total area (largest first)
            sorted_types = sorted(room_types_summary.items(), key=lambda x: x[1]['total_area'], reverse=True)
            for room_type, data in sorted_types:
                count = data['count']
                total = data['total_area']
                avg = total / count if count > 0 else 0.0
                summary_lines.append(f"- {room_type}: {count} room(s), {total:.2f} m² (avg {avg:.2f} m²/room)")
            summary_lines.append("")

        # --- Openings ---
        # Get actual vs appearance counts
        opening_counts = self.app.get_opening_counts()
        
        def summarize_openings(title, openings, opening_type_key):
            # Keys use plural: actual_doors, actual_windows, etc.
            actual = opening_counts[f'actual_{opening_type_key}s']
            total_qty = opening_counts[f'total_{opening_type_key}_qty']
            appearance = opening_counts[f'appearance_{opening_type_key}s']
            shared = opening_counts[f'shared_{opening_type_key}s']
            
            summary_lines.append(f"{title} ({total_qty} actual items)")
            summary_lines.append("-"*20)
            if not openings:
                summary_lines.append("  None\n")
                return
            
            # Show actual vs appearance if different
            if appearance != total_qty:
                summary_lines.append(f"  ⚠️ Appears {appearance}x across rooms (shared: {shared})")
                summary_lines.append(f"  ✓ Actual count for quantities: {total_qty}")
            
            by_type = {}
            for op in openings:
                mat = opening_type(op)
                w, h = opening_dims(op)
                qty = opening_qty(op)
                key = f"{mat} ({w:.2f}x{h:.2f}m)"
                by_type.setdefault(key, 0)
                by_type[key] += qty
            
            for type_key, qty in by_type.items():
                summary_lines.append(f"- {type_key}: {qty} pcs")
            summary_lines.append("\n")

        summarize_openings("Doors", self.app.project.doors, 'door')
        summarize_openings("Windows", self.app.project.windows, 'window')

        # --- Walls ---
        summary_lines.append(f"Walls ({len(self.app.project.walls)} items)")
        summary_lines.append("-"*20)
        total_net_wall = 0
        for wall in self.app.project.walls:
            name, gross, deduct, net = wall_fields(wall)
            summary_lines.append(f"- {name}: Net {net:.2f} m² (Gross: {gross:.2f}, Deduct: {deduct:.2f})")
            total_net_wall += net
        summary_lines.append(f"Total Net Wall Area: {total_net_wall:.2f} m²\n")

        # --- Finishes (using UnifiedCalculator for consistency) ---
        from bilind.calculations.unified_calculator import UnifiedCalculator
        calc = UnifiedCalculator(self.app.project)
        totals = calc.calculate_totals()
        
        summary_lines.append(f"Plaster Area: {totals['plaster_total']:.2f} m²")
        summary_lines.append(f"Paint Area: {totals['paint_total']:.2f} m²")
        summary_lines.append(f"Ceramic Area: {totals['ceramic_total']:.2f} m²")
        summary_lines.append("\n")

        # --- Materials ---
        summary_lines.append("Material Take-off")
        summary_lines.append("-"*20)
        total_stone = sum(opening_stone(d) for d in self.app.project.doors) + \
                  sum(opening_stone(w) for w in self.app.project.windows)
        total_steel = sum(opening_weight(d) for d in self.app.project.doors)
        total_glass = sum(opening_glass(w) for w in self.app.project.windows)
        # Use UnifiedCalculator ceramic total (already calculated above)
        total_ceramic = totals['ceramic_total']

        summary_lines.append(f"- Stone (lm): {total_stone:.2f}")
        summary_lines.append(f"- Steel (kg): {total_steel:.1f}")
        summary_lines.append(f"- Glass (m²): {total_glass:.2f}")
        summary_lines.append(f"- Ceramic (m²): {total_ceramic:.2f}")

        return "\n".join(summary_lines)
