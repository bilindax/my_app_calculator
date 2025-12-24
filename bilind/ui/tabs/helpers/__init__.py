"""
Room Manager Helpers
====================
Utility classes and adapters for Room Manager tab.
"""

from .room_adapter import RoomAdapter
from .opening_adapter import OpeningAdapter
from .ceramic_calculator import CeramicCalculatorDialog, show_ceramic_calculator
from .auto_presets import AutoPresetsCalculator, apply_auto_presets, classify_room_type

__all__ = [
    'RoomAdapter', 
    'OpeningAdapter',
    'CeramicCalculatorDialog',
    'show_ceramic_calculator',
    'AutoPresetsCalculator',
    'apply_auto_presets',
    'classify_room_type'
]
