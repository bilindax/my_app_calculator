"""
Modern UI Styling with ttkbootstrap Integration
================================================
Enhanced visual styling using ttkbootstrap themes and custom improvements.
"""

import tkinter as tk

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    import tkinter.ttk as ttk
    TTKBOOTSTRAP_AVAILABLE = False


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Convert a #RRGGBB color string to an RGB tuple."""
    color = color.lstrip('#')
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert an RGB tuple to a #RRGGBB color string."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def _blend(color: str, target: str, amount: float) -> str:
    """Blend two colors together by a given amount (0-1)."""
    r1, g1, b1 = _hex_to_rgb(color)
    r2, g2, b2 = _hex_to_rgb(target)
    r = int(r1 + (r2 - r1) * amount)
    g = int(g1 + (g2 - g1) * amount)
    b = int(b1 + (b2 - b1) * amount)
    return _rgb_to_hex((r, g, b))


def _lighten(color: str, amount: float = 0.18) -> str:
    """Lighten a color by blending it with white."""
    return _blend(color, '#ffffff', amount)


def _darken(color: str, amount: float = 0.22) -> str:
    """Darken a color by blending it with black."""
    return _blend(color, '#000000', amount)


def _luminance(color: str) -> float:
    """Compute perceived luminance for color contrast decisions."""
    r, g, b = _hex_to_rgb(color)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _get_widget_bg(widget: tk.Widget, fallback: str = '#0f172a') -> str:
    """Safely get a widget background color."""
    try:
        return widget.cget('background')
    except Exception:
        try:
            return widget.cget('bg')
        except Exception:
            return fallback


class RoundedButton(tk.Frame):
    """Custom Canvas-based rounded button for a modern appearance."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command,
        width: int = 156,
        height: int = 42,
        radius: int = 18,
        base_color: str = '#00d4ff',
        text_color: str = '#0a0e1a',
        hover_color: str | None = None,
        active_color: str | None = None,
        font: tuple = ('Segoe UI Semibold', 11)
    ) -> None:
        bg = _get_widget_bg(parent)
        super().__init__(parent, bg=bg, highlightthickness=0, bd=0)

        self._command = command
        self._text = text
        self._width = width
        self._height = height
        self._radius = radius
        self._base_color = base_color
        self._text_color = text_color
        self._hover_color = hover_color or _lighten(base_color, 0.22)
        self._active_color = active_color or _darken(base_color, 0.30)
        self._current_color = self._base_color
        self._font = font

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=bg,
            highlightthickness=0,
            bd=0,
            cursor='hand2'
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Accessibility & focus
        self.canvas.configure(takefocus=1)
        self._focused = False

        self.canvas.bind('<Enter>', self._on_enter)
        self.canvas.bind('<Leave>', self._on_leave)
        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.canvas.bind('<FocusIn>', self._on_focus_in)
        self.canvas.bind('<FocusOut>', self._on_focus_out)
        self.canvas.bind('<Key-Return>', lambda e: self._invoke())
        self.canvas.bind('<space>', lambda e: self._invoke())
        self.canvas.bind('<Configure>', lambda _: self._draw())

        self._draw()

    # --- Drawing --------------------------------------------------------
    def _draw(self) -> None:
        self.canvas.delete('all')
        w = self.canvas.winfo_width() or self._width
        h = self.canvas.winfo_height() or self._height
        r = min(self._radius, int(min(w, h) / 2))

        points = [
            r, 0,
            w - r, 0,
            w, 0,
            w, r,
            w, h - r,
            w, h,
            w - r, h,
            r, h,
            0, h,
            0, h - r,
            0, r,
            0, 0
        ]
        self.canvas.create_polygon(
            points,
            smooth=True,
            splinesteps=36,
            fill=self._current_color,
            outline=''
        )

        # Focus ring
        if self._focused:
            ring_color = _lighten(self._base_color, 0.35)
            self.canvas.create_polygon(
                points,
                smooth=True,
                splinesteps=36,
                fill='',
                outline=ring_color,
                width=2
            )

        self.canvas.create_text(
            w / 2,
            h / 2,
            text=self._text,
            font=self._font,
            fill=self._text_color
        )

    # --- Event Handlers -------------------------------------------------
    def _on_enter(self, _event=None) -> None:
        self._set_color(self._hover_color)

    def _on_leave(self, _event=None) -> None:
        self._set_color(self._base_color)

    def _on_press(self, _event=None) -> None:
        self._set_color(self._active_color)

    def _on_release(self, event) -> None:
        x, y = event.x, event.y
        if 0 <= x <= self.canvas.winfo_width() and 0 <= y <= self.canvas.winfo_height():
            self._set_color(self._hover_color)
            if callable(self._command):
                self.canvas.after(10, self._command)
        else:
            self._set_color(self._base_color)

    def _set_color(self, color: str) -> None:
        self._current_color = color
        self._draw()

    def _on_focus_in(self, _event=None) -> None:
        self._focused = True
        self._draw()

    def _on_focus_out(self, _event=None) -> None:
        self._focused = False
        self._draw()

    def _invoke(self) -> None:
        # Visual feedback for keyboard activation
        self._set_color(self._active_color)
        if callable(self._command):
            self.canvas.after(10, self._command)

    # --- Public API -----------------------------------------------------
    def update_palette(
        self,
        base_color: str,
        text_color: str,
        hover_color: str | None = None,
        active_color: str | None = None,
        container_bg: str | None = None
    ) -> None:
        """Update button palette when theme/colors change."""
        self._base_color = base_color
        self._text_color = text_color
        self._hover_color = hover_color or _lighten(base_color, 0.22)
        self._active_color = active_color or _darken(base_color, 0.30)
        self._current_color = self._base_color
        if container_bg:
            self.configure(bg=container_bg)
            self.canvas.configure(bg=container_bg)
        self._draw()

    def set_text(self, text: str) -> None:
        self._text = text
        self._draw()



class ModernStyleManager:
    """Manages modern styling with ttkbootstrap themes and enhancements."""
    
    # Available ttkbootstrap themes (dark modern themes)
    MODERN_THEMES = {
        'cyborg': 'Cyborg (Dark Cyan)',
        'darkly': 'Darkly (Dark Blue)', 
        'superhero': 'Superhero (Dark Orange)',
        'solar': 'Solar (Dark Yellow)',
        'vapor': 'Vapor (Dark Purple)',
    }
    
    def __init__(self, root, theme_name='cyborg'):
        """
        Initialize modern style manager.
        
        Args:
            root: Tkinter root window
            theme_name: ttkbootstrap theme name (default: cyborg)
        """
        self.root = root
        self.theme_name = theme_name
        self.style = None
        self.custom_buttons: list[tuple[RoundedButton, str]] = []
        self.last_palette: dict[str, str] = {}
        
        if TTKBOOTSTRAP_AVAILABLE:
            self._apply_ttkbootstrap_theme()
        else:
            # Fallback to standard ttk
            self.style = ttk.Style()
            self._apply_fallback_theme()
    
    def _apply_ttkbootstrap_theme(self):
        """Apply ttkbootstrap modern theme."""
        try:
            # ttkbootstrap handles style automatically when imported
            self.style = ttk.Style(theme=self.theme_name)
            self._add_custom_enhancements()
        except Exception as e:
            print(f"⚠️ ttkbootstrap theme failed: {e}, using fallback")
            self._apply_fallback_theme()
    
    def _apply_fallback_theme(self):
        """Fallback styling if ttkbootstrap unavailable."""
        if not self.style:
            self.style = ttk.Style()
        
        try:
            self.style.theme_use('clam')
        except:
            pass
        
        # Basic dark theme colors
        colors = {
            'bg': '#1a1d23',
            'fg': '#e0e0e0',
            'select_bg': '#00d4ff',
            'select_fg': '#000000',
        }
        
        self.style.configure('Treeview',
            background=colors['bg'],
            foreground=colors['fg'],
            fieldbackground=colors['bg'],
            rowheight=28)
        
        self.style.map('Treeview',
            background=[('selected', colors['select_bg'])],
            foreground=[('selected', colors['select_fg'])])
    
    def _add_custom_enhancements(self):
        """Add custom visual enhancements on top of ttkbootstrap."""
        
        # Enhanced Treeview with alternating row colors
        self.style.configure('Treeview',
            rowheight=30,
            borderwidth=0,
            relief='flat')
        
        # Smooth hover effects
        self.style.map('Treeview',
            background=[
                ('selected', 'focus', '#00d4ff'),
                ('selected', '!focus', '#007799'),
            ],
            foreground=[
                ('selected', 'focus', '#000000'),
                ('selected', '!focus', '#ffffff'),
            ])
        
        # Enhanced buttons with better padding
        for btn_type in ['TButton', 'Accent.TButton', 'Danger.TButton', 'Secondary.TButton']:
            self.style.configure(btn_type,
                padding=(12, 8),
                relief='flat',
                borderwidth=0)
        
        # Modern notebook tabs
        self.style.configure('TNotebook.Tab',
            padding=(20, 10),
            borderwidth=0)
        
        # Smooth scrollbars
        self.style.configure('Vertical.TScrollbar',
            width=12,
            borderwidth=0,
            relief='flat')
        
        self.style.configure('Horizontal.TScrollbar',
            height=12,
            borderwidth=0,
            relief='flat')
    
    def apply_alternating_rows(self, treeview, tag_odd='oddrow', tag_even='evenrow'):
        """
        Apply alternating row colors to a treeview.
        
        Args:
            treeview: ttk.Treeview widget
            tag_odd: Tag name for odd rows
            tag_even: Tag name for even rows
        """
        if TTKBOOTSTRAP_AVAILABLE:
            # Use theme-aware colors
            odd_bg = '#1a1d23'
            even_bg = '#24272f'
        else:
            odd_bg = '#1a1d23'
            even_bg = '#242830'
        
        treeview.tag_configure(tag_odd, background=odd_bg)
        treeview.tag_configure(tag_even, background=even_bg)
        
        # Apply tags to existing items (preserve existing tags)
        for idx, item in enumerate(treeview.get_children()):
            tag = tag_even if idx % 2 == 0 else tag_odd
            existing_tags = list(treeview.item(item, 'tags'))
            # Only add alternating tag if not already present
            if tag not in existing_tags:
                existing_tags.append(tag)
            treeview.item(item, tags=tuple(existing_tags))
    
    def add_focus_animation(self, widget):
        """
        Add subtle focus animation to a widget.
        
        Args:
            widget: tkinter widget to animate
        """
        def on_focus_in(event):
            try:
                widget.configure(relief='solid', borderwidth=1)
            except:
                pass
        
        def on_focus_out(event):
            try:
                widget.configure(relief='flat', borderwidth=0)
            except:
                pass
        
        widget.bind('<FocusIn>', on_focus_in)
        widget.bind('<FocusOut>', on_focus_out)
    
    def enhance_treeview(self, treeview):
        """
        Apply all modern enhancements to a treeview.
        
        Args:
            treeview: ttk.Treeview to enhance
        """
        self.apply_alternating_rows(treeview)
        
        # Smooth scrolling (already handled in bilind_main.py)
        # Add hover effect
        def on_motion(event):
            region = treeview.identify_region(event.x, event.y)
            if region == 'cell':
                treeview.configure(cursor='hand2')
            else:
                treeview.configure(cursor='')
        
        treeview.bind('<Motion>', on_motion)
    
    def set_theme(self, theme_name):
        """
        Change theme dynamically.
        
        Args:
            theme_name: ttkbootstrap theme name
        """
        if not TTKBOOTSTRAP_AVAILABLE:
            print("⚠️ ttkbootstrap not available, cannot change theme")
            return
        
        try:
            self.theme_name = theme_name
            self.style = ttk.Style(theme=theme_name)
            self._add_custom_enhancements()
            self.refresh_custom_buttons()
        except Exception as e:
            print(f"❌ Failed to set theme {theme_name}: {e}")
    
    @staticmethod
    def is_available():
        """Check if ttkbootstrap is available."""
        return TTKBOOTSTRAP_AVAILABLE
    
    @staticmethod
    def get_available_themes():
        """Get list of available modern themes."""
        return list(ModernStyleManager.MODERN_THEMES.keys())

    # --- Custom Controls -------------------------------------------------
    def set_palette(self, palette: dict[str, str]):
        """Record the latest color palette from the application."""
        if palette:
            self.last_palette = dict(palette)
            self.refresh_custom_buttons()

    def create_button(
        self,
        parent: tk.Widget,
        text: str,
        command,
        variant: str = 'accent',
        palette: dict[str, str] | None = None,
        width: int = 156,
        height: int = 42
    ) -> RoundedButton:
        """
        Create a rounded modern button.
        
        Args:
            parent: parent widget
            text: button label
            command: callback
            variant: accent/secondary/danger/warning/success/info
            palette: color dictionary from application
            width: pixel width
            height: pixel height
        """
        palette = palette or self.last_palette or {}
        base_color = self._variant_color(variant, palette)
        text_color = '#0a0e1a' if _luminance(base_color) > 155 else '#f8fafc'
        hover_color = _lighten(base_color, 0.18)
        active_color = _darken(base_color, 0.24)
        container_bg = palette.get('bg_secondary', _get_widget_bg(parent))

        button = RoundedButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            base_color=base_color,
            text_color=text_color,
            hover_color=hover_color,
            active_color=active_color
        )
        button.update_palette(
            base_color,
            text_color,
            hover_color,
            active_color,
            container_bg=container_bg
        )

        self.custom_buttons.append((button, variant))
        return button

    def refresh_custom_buttons(self, palette: dict[str, str] | None = None):
        """Update all custom buttons to match the current palette."""
        if palette is not None:
            self.last_palette = dict(palette)
        if not self.last_palette or not self.custom_buttons:
            return

        palette = self.last_palette
        container_bg = palette.get('bg_secondary', '#1a1d23')
        for button, variant in self.custom_buttons:
            base_color = self._variant_color(variant, palette)
            text_color = '#0a0e1a' if _luminance(base_color) > 155 else '#f8fafc'
            hover_color = _lighten(base_color, 0.18)
            active_color = _darken(base_color, 0.24)
            button.update_palette(base_color, text_color, hover_color, active_color, container_bg)

    def _variant_color(self, variant: str, palette: dict[str, str]) -> str:
        """Resolve a variant name to a palette color."""
        fallback = {
            'accent': '#00d4ff',
            'secondary': '#1f2937',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'success': '#10b981',
            'info': '#3b82f6'
        }
        key_map = {
            'accent': 'accent',
            'secondary': 'secondary',
            'danger': 'danger',
            'warning': 'warning',
            'success': 'success',
            'info': 'info'
        }
        key = key_map.get(variant, 'accent')
        return palette.get(key, fallback[key])


def create_gradient_frame(parent, color1='#00d4ff', color2='#0080ff', height=100):
    """
    Create a frame with gradient background using Canvas.
    
    Args:
        parent: Parent widget
        color1: Start color (hex)
        color2: End color (hex)
        height: Frame height
    
    Returns:
        Canvas widget with gradient
    """
    import tkinter as tk
    
    canvas = tk.Canvas(parent, height=height, highlightthickness=0)
    
    def draw_gradient():
        width = canvas.winfo_width()
        if width <= 1:
            width = 400  # Default width
        
        # Parse colors
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        # Draw gradient
        for i in range(height):
            ratio = i / height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            canvas.create_line(0, i, width, i, fill=color)
    
    canvas.bind('<Configure>', lambda e: draw_gradient())
    draw_gradient()
    
    return canvas
