"""
Modern Theme Manager for BILIND
--------------------------------
Provides multiple cohesive dark themes and design tokens (colors, radii,
spacing) and a helper to apply ttk styles consistently.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass
class ThemeTokens:
    name: str
    colors: Dict[str, str]
    radius: int = 8
    spacing: int = 10
    density: str = "comfortable"  # compact | comfortable
    font_family: str = "Segoe UI"


THEMES: Dict[str, ThemeTokens] = {
    # Electric cyan (current default)
    "neo": ThemeTokens(
        name="neo",
        colors={
            'bg_primary': '#0f1419',
            'bg_secondary': '#1a1f2e',
            'bg_card': '#252b3b',
            'bg_elevated': '#2d3548',
            'accent': '#00d9ff',
            'accent_light': '#5ce1ff',
            'accent_dark': '#00a3cc',
            'text_primary': '#e2e8f0',
            'text_secondary': '#94a3b8',
            'text_muted': '#64748b',
            'text_disabled': '#475569',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'info': '#3b82f6',
            'success_bg': '#064e3b',
            'warning_bg': '#78350f',
            'danger_bg': '#7f1d1d',
            'info_bg': '#1e3a8a',
            'border': '#334155',
            'border_light': '#475569',
            'hover': '#334155',
            'selected': '#1e293b',
            'focus': '#00d9ff',
            'primary': '#00d9ff',
            'secondary': '#8b5cf6',
            'tertiary': '#ec4899',
        },
    ),
    # Purple/Plum variant
    "plum": ThemeTokens(
        name="plum",
        colors={
            'bg_primary': '#0e0b14',
            'bg_secondary': '#171427',
            'bg_card': '#211a35',
            'bg_elevated': '#2a2145',
            'accent': '#8b5cf6',
            'accent_light': '#a78bfa',
            'accent_dark': '#6d28d9',
            'text_primary': '#ede9fe',
            'text_secondary': '#c4b5fd',
            'text_muted': '#a78bfa',
            'text_disabled': '#6b7280',
            'success': '#22c55e',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'info': '#60a5fa',
            'success_bg': '#064e3b',
            'warning_bg': '#78350f',
            'danger_bg': '#7f1d1d',
            'info_bg': '#1e3a8a',
            'border': '#3f3c57',
            'border_light': '#514a77',
            'hover': '#3a2f5f',
            'selected': '#2c2251',
            'focus': '#a78bfa',
            'primary': '#8b5cf6',
            'secondary': '#00d9ff',
            'tertiary': '#ec4899',
        },
    ),
    # Emerald/Teal variant
    "emerald": ThemeTokens(
        name="emerald",
        colors={
            'bg_primary': '#0a0f0f',
            'bg_secondary': '#111b1b',
            'bg_card': '#162222',
            'bg_elevated': '#1a2a2a',
            'accent': '#10b981',
            'accent_light': '#34d399',
            'accent_dark': '#059669',
            'text_primary': '#e5f2ee',
            'text_secondary': '#9fd8c7',
            'text_muted': '#7cc7b2',
            'text_disabled': '#3f4f4c',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'info': '#22d3ee',
            'success_bg': '#052e26',
            'warning_bg': '#3f2a09',
            'danger_bg': '#3b0a0a',
            'info_bg': '#08343b',
            'border': '#1f2d2d',
            'border_light': '#274040',
            'hover': '#1b2a2a',
            'selected': '#143232',
            'focus': '#34d399',
            'primary': '#10b981',
            'secondary': '#3b82f6',
            'tertiary': '#22d3ee',
        },
    ),
    # Light theme variant
    "light": ThemeTokens(
        name="light",
        colors={
            'bg_primary': '#ffffff',
            'bg_secondary': '#f8fafc',
            'bg_card': '#ffffff',
            'bg_elevated': '#f1f5f9',
            'accent': '#0ea5e9',
            'accent_light': '#38bdf8',
            'accent_dark': '#0284c7',
            'text_primary': '#0f172a',
            'text_secondary': '#475569',
            'text_muted': '#64748b',
            'text_disabled': '#cbd5e1',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'info': '#3b82f6',
            'success_bg': '#d1fae5',
            'warning_bg': '#fef3c7',
            'danger_bg': '#fee2e2',
            'info_bg': '#dbeafe',
            'border': '#e2e8f0',
            'border_light': '#cbd5e1',
            'hover': '#f1f5f9',
            'selected': '#e0f2fe',
            'focus': '#0ea5e9',
            'primary': '#0ea5e9',
            'secondary': '#8b5cf6',
            'tertiary': '#ec4899',
        },
    ),
}


class ThemeManager:
    def __init__(self, default: str = "neo"):
        self._current: ThemeTokens = THEMES.get(default, list(THEMES.values())[0])

    @property
    def name(self) -> str:
        return self._current.name

    @property
    def colors(self) -> Dict[str, str]:
        return self._current.colors

    def set_theme(self, name: str) -> ThemeTokens:
        if name in THEMES:
            self._current = THEMES[name]
        return self._current

    def available(self):
        return list(THEMES.keys())
