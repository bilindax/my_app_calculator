"""
Configuration and Catalogs for BILIND Application
=================================================
This module contains material type catalogs, color schemes, and constants.
"""

# Material Type Catalogs
DOOR_TYPES = {
    'Wood': {
        'weight': 25,
        'material': 'Wood',
        'description': 'Wood door - default 25kg each'
    },
    'Steel': {
        'weight': 0,
        'material': 'Steel',
        'description': 'Steel door - enter actual weight'
    },
    'PVC': {
        'weight': 15,
        'material': 'PVC',
        'description': 'PVC door - default 15kg each'
    }
}

# Predefined Door Templates (Common Sizes)
DEFAULT_DOOR_TEMPLATES = [
    {
        'name': '1.0×2.0 PVC',
        'type': 'PVC',
        'width': 1.0,
        'height': 2.0,
        'weight': 15,
        'placement_height': 0.0,
        'description': 'Standard PVC door 1.0×2.0m'
    },
    {
        'name': '0.9×2.0 PVC',
        'type': 'PVC',
        'width': 0.9,
        'height': 2.0,
        'weight': 15,
        'placement_height': 0.0,
        'description': 'Common PVC door 0.9×2.0m'
    },
    {
        'name': '1.0×2.0 Steel 120kg',
        'type': 'Steel',
        'width': 1.0,
        'height': 2.0,
        'weight': 120,
        'placement_height': 0.0,
        'description': 'Heavy steel door 1.0×2.0m - 120kg'
    },
    {
        'name': '0.8×2.1 Wood',
        'type': 'Wood',
        'width': 0.8,
        'height': 2.1,
        'weight': 25,
        'placement_height': 0.0,
        'description': 'Standard wooden door 0.8×2.1m'
    },
    {
        'name': '0.9×2.1 Wood',
        'type': 'Wood',
        'width': 0.9,
        'height': 2.1,
        'weight': 25,
        'placement_height': 0.0,
        'description': 'Wide wooden door 0.9×2.1m'
    }
]

WINDOW_TYPES = {
    'Aluminum': {
        'material': 'Aluminum',
        'description': 'Aluminum frame with clear glass'
    },
    'PVC': {
        'material': 'PVC',
        'description': 'PVC frame with double glazing'
    },
    'Wood': {
        'material': 'Wood',
        'description': 'Traditional wooden sash or casement'
    },
    'Steel': {
        'material': 'Steel',
        'description': 'Steel/metal frame window'
    }
}

# Predefined Window Templates (Common Sizes)
DEFAULT_WINDOW_TEMPLATES = [
    {
        'name': '0.5×1.5 PVC',
        'type': 'PVC',
        'width': 0.5,
        'height': 1.5,
        'placement_height': 1.0,
        'description': 'Small PVC window 0.5×1.5m'
    },
    {
        'name': '1.0×1.5 Aluminum',
        'type': 'Aluminum',
        'width': 1.0,
        'height': 1.5,
        'placement_height': 1.0,
        'description': 'Standard aluminum window 1.0×1.5m'
    },
    {
        'name': '1.0×2.0 Aluminum',
        'type': 'Aluminum',
        'width': 1.0,
        'height': 2.0,
        'placement_height': 0.5,
        'description': 'Tall aluminum window 1.0×2.0m'
    },
    {
        'name': '1.1×1.3 PVC',
        'type': 'PVC',
        'width': 1.1,
        'height': 1.3,
        'placement_height': 1.0,
        'description': 'Medium PVC window 1.1×1.3m'
    },
    {
        'name': '1.6×1.4 Aluminum',
        'type': 'Aluminum',
        'width': 1.6,
        'height': 1.4,
        'placement_height': 1.0,
        'description': 'Wide aluminum window 1.6×1.4m'
    },
    {
        'name': '1.2×1.5 Steel',
        'type': 'Steel',
        'width': 1.2,
        'height': 1.5,
        'placement_height': 1.0,
        'description': 'Steel window 1.2×1.5m'
    }
]

# UI Color Scheme (Modern Dark Theme - Enhanced)
COLOR_SCHEME = {
    # Backgrounds - Deep, rich tones
    'bg_primary': '#0f1419',      # Deepest space - main background
    'bg_secondary': '#1a1f2e',    # Rich dark blue - secondary panels
    'bg_card': '#252b3b',         # Card/container background
    'bg_elevated': '#2d3548',     # Elevated elements (modals, tooltips)
    
    # Accents - Vibrant, modern
    'accent': '#00d9ff',          # Electric cyan - primary actions
    'accent_light': '#5ce1ff',    # Light cyan - highlights
    'accent_dark': '#00a3cc',     # Deep cyan - pressed states
    'accent_glow': 'rgba(0, 217, 255, 0.2)',  # Glow effect
    
    # Text - High contrast, readable
    'text_primary': '#e2e8f0',    # Off-white - main text
    'text_secondary': '#94a3b8',  # Cool gray - secondary text
    'text_muted': '#64748b',      # Muted gray - hints/placeholders
    'text_disabled': '#475569',   # Disabled text
    
    # Status colors - Clear, modern
    'success': '#10b981',         # Emerald green - success states
    'success_bg': '#064e3b',      # Dark green background
    'warning': '#f59e0b',         # Amber - warnings
    'warning_bg': '#78350f',      # Dark amber background
    'danger': '#ef4444',          # Red - errors/danger
    'danger_bg': '#7f1d1d',       # Dark red background
    'info': '#3b82f6',            # Blue - informational
    'info_bg': '#1e3a8a',         # Dark blue background
    
    # UI Elements
    'border': '#334155',          # Borders and dividers
    'border_light': '#475569',    # Lighter borders
    'hover': '#334155',           # Hover backgrounds
    'selected': '#1e293b',        # Selected items
    'focus': '#00d9ff',           # Focus rings
    
    # Semantic colors
    'primary': '#00d9ff',         # Primary actions
    'secondary': '#8b5cf6',       # Secondary actions (purple)
    'tertiary': '#ec4899',        # Tertiary actions (pink)
    
    # Gradients (for future use)
    'gradient_start': '#00d9ff',
    'gradient_end': '#8b5cf6'
}

# Application Constants
DEFAULT_SCALE = 1.0
DEFAULT_WALL_HEIGHT = 3.0
GLASS_PERCENTAGE = 0.85  # Windows: 85% glass, 15% frame

# =============================================================================
# أنواع الغرف بالعربي - Arabic Room Types
# =============================================================================
ROOM_TYPES_AR = [
    "[غير محدد]",
    "صالة",
    "غرفة نوم",
    "غرفة نوم رئيسية",
    "مطبخ",
    "حمام",
    "تواليت",
    "بلكون",
    "تراس",
    "ممر",
    "مخزن",
    "غسيل",
    "مكتب",
    "كراج",
    "مدخل",
    "غرفة خدمات",
    "غرفة ضيوف",
    "درج",
    "أخرى"
]

# أنواع أسطح الجدران (للبلكون والمساحات الخاصة)
WALL_SURFACE_TYPES = [
    "دهان",           # Paint
    "سيراميك",        # Ceramic tiles
    "حجر",            # Stone
    "بدون تشطيب",     # No finish (raw concrete)
    "شباك/فتحة",      # Window/Opening (no wall area)
    "زجاج",           # Glass
]

# =============================================================================
# إفتراضيات ذكية حسب نوع الغرفة - Smart Defaults by Room Type
# =============================================================================
ROOM_TYPE_DEFAULTS = {
    # الحمام - Bathroom: سيراميك حائط كامل 1.6م + أرضية
    "حمام": {
        "wall_height": 2.8,
        "has_ceiling_paint": True,
        "ceramic": {
            "wall_height": 1.6,      # ارتفاع السيراميك على الحائط
            "floor": True,           # سيراميك أرضية
            "category": "Bathroom"
        },
        "description": "حمام - سيراميك حائط 1.6م + أرضية كاملة"
    },
    
    # التواليت - Toilet/WC: مثل الحمام
    "تواليت": {
        "wall_height": 2.8,
        "has_ceiling_paint": True,
        "ceramic": {
            "wall_height": 1.6,
            "floor": True,
            "category": "Bathroom"
        },
        "description": "تواليت - سيراميك حائط 1.6م + أرضية كاملة"
    },
    
    # المطبخ - Kitchen: باكسبلاش 1.6م فوق الكاونتر
    "مطبخ": {
        "wall_height": 3.0,
        "has_ceiling_paint": True,
        "ceramic": {
            "wall_height": 1.6,      # ارتفاع الباكسبلاش
            "start_height": 0.0,     # يبدأ من الأرض (أو 0.85 للكاونتر فقط)
            "floor": True,           # سيراميك أرضية
            "category": "Kitchen"
        },
        "description": "مطبخ - سيراميك حائط 1.6م + أرضية"
    },
    
    # البلكون - Balcony: جدران متعددة بارتفاعات مختلفة
    "بلكون": {
        "wall_height": 1.2,          # ارتفاع الدرابزين الإفتراضي
        "is_balcony": True,          # علامة البلكون
        "has_ceiling_paint": False,  # بدون سقف عادة
        "ceramic": {
            "wall_height": 0,        # بدون سيراميك حائط إفتراضياً
            "floor": True,           # سيراميك أرضية
            "category": "Other"
        },
        "multi_wall": True,          # جدران متعددة
        "description": "بلكون - جدران متعددة بارتفاعات مختلفة"
    },
    
    # التراس - Terrace
    "تراس": {
        "wall_height": 1.0,
        "is_balcony": True,
        "has_ceiling_paint": False,
        "ceramic": {
            "wall_height": 0,
            "floor": True,
            "category": "Other"
        },
        "multi_wall": True,
        "description": "تراس - مساحة خارجية"
    },
    
    # الصالة - Living Room: دهان فقط
    "صالة": {
        "wall_height": 3.0,
        "has_ceiling_paint": True,
        "ceramic": None,             # بدون سيراميك
        "description": "صالة - دهان حوائط وسقف"
    },
    
    # غرفة النوم - Bedroom: دهان فقط
    "غرفة نوم": {
        "wall_height": 3.0,
        "has_ceiling_paint": True,
        "ceramic": None,
        "description": "غرفة نوم - دهان حوائط وسقف"
    },
    
    # غرفة النوم الرئيسية - Master Bedroom
    "غرفة نوم رئيسية": {
        "wall_height": 3.0,
        "has_ceiling_paint": True,
        "ceramic": None,
        "description": "غرفة نوم رئيسية - دهان حوائط وسقف"
    },
    
    # الممر - Hallway
    "ممر": {
        "wall_height": 3.0,
        "has_ceiling_paint": True,
        "ceramic": None,
        "description": "ممر - دهان حوائط وسقف"
    },
    
    # المدخل - Entrance
    "مدخل": {
        "wall_height": 3.0,
        "has_ceiling_paint": True,
        "ceramic": {
            "wall_height": 0,
            "floor": True,           # سيراميك أرضية فقط
            "category": "Other"
        },
        "description": "مدخل - دهان حوائط + سيراميك أرضية"
    },
    
    # الدرج - Stairs
    "درج": {
        "wall_height": 3.0,
        "has_ceiling_paint": True,
        "ceramic": None,
        "description": "درج - دهان حوائط"
    },
    
    # المخزن - Storage
    "مخزن": {
        "wall_height": 2.8,
        "has_ceiling_paint": False,  # بدون دهان سقف عادة
        "ceramic": None,
        "description": "مخزن - دهان حوائط فقط"
    },
    
    # غرفة الغسيل - Laundry
    "غسيل": {
        "wall_height": 2.8,
        "has_ceiling_paint": True,
        "ceramic": {
            "wall_height": 1.2,      # سيراميك جزئي
            "floor": True,
            "category": "Other"
        },
        "description": "غسيل - سيراميك حائط 1.2م + أرضية"
    },
    
    # الكراج - Garage
    "كراج": {
        "wall_height": 2.8,
        "has_ceiling_paint": False,
        "ceramic": None,
        "description": "كراج - بدون تشطيبات"
    },
    
    # الإفتراضي - Default
    "[غير محدد]": {
        "wall_height": 3.0,
        "has_ceiling_paint": True,
        "ceramic": None,
        "description": "غير محدد - إفتراضيات قياسية"
    },
    
    "أخرى": {
        "wall_height": 3.0,
        "has_ceiling_paint": True,
        "ceramic": None,
        "description": "أخرى - إفتراضيات قياسية"
    }
}

# دالة للحصول على الإفتراضيات حسب نوع الغرفة
def get_room_defaults(room_type: str) -> dict:
    """
    Get smart defaults for a room type.
    
    Args:
        room_type: Room type in Arabic (e.g., 'حمام', 'مطبخ')
        
    Returns:
        Dictionary with default values for that room type
    """
    # Try exact match first
    if room_type in ROOM_TYPE_DEFAULTS:
        return ROOM_TYPE_DEFAULTS[room_type].copy()
    
    # Try lowercase match
    room_type_lower = room_type.lower() if room_type else ""
    for key, value in ROOM_TYPE_DEFAULTS.items():
        if key.lower() == room_type_lower:
            return value.copy()
    
    # Return default
    return ROOM_TYPE_DEFAULTS.get("[غير محدد]", {
        "wall_height": 3.0,
        "has_ceiling_paint": True,
        "ceramic": None
    }).copy()
