# Door & Window Templates System - دليل النماذج الجاهزة

## 🎯 Overview

The new **Templates System** makes adding doors and windows **10x faster** by providing:

1. **📦 Predefined Templates** - Common industry-standard sizes
2. **📋 Reusable Templates** - Any door/window you add becomes available as a template
3. **⚡ Quick-Add Buttons** - One-click adding of most common types in Room Manager

---

## 🚀 How to Use

### Method 1: Template Dropdown (All Dialogs)

When adding a door or window (from **any tab**), you'll now see:

```
📦 Template: [-- Custom (manual entry) --]
             ▼
```

**Click the dropdown** to see all available templates:

#### Predefined Door Templates:
- `1.0×2.0 PVC` - Standard PVC door 1.0×2.0m (15kg)
- `0.9×2.0 PVC` - Common PVC door 0.9×2.0m (15kg)
- `1.0×2.0 Steel 120kg` - Heavy steel door 1.0×2.0m (120kg)
- `0.8×2.1 Wood` - Standard wooden door 0.8×2.1m (25kg)
- `0.9×2.1 Wood` - Wide wooden door 0.9×2.1m (25kg)

#### Predefined Window Templates:
- `0.5×1.5 PVC` - Small PVC window (sill height 1.0m)
- `1.0×1.5 Aluminum` - Standard aluminum window
- `1.0×2.0 Aluminum` - Tall aluminum window (sill height 0.5m)
- `1.1×1.3 PVC` - Medium PVC window
- `1.6×1.4 Aluminum` - Wide aluminum window
- `1.2×1.5 Steel` - Steel window

#### Your Existing Doors/Windows:
- `📋 D1` - From existing door 'D1'
- `📋 W1` - From existing window 'W1'
- ... (all your previously added doors/windows)

**Select a template** → All fields auto-fill:
- ✅ Type (PVC, Steel, Wood, Aluminum)
- ✅ Width & Height
- ✅ Weight (for doors)
- ✅ Placement Height (floor to sill)

You can **still customize** any field after selecting a template!

---

### Method 2: Quick-Add Buttons (Room Manager Only)

In **Room Manager** tab, select a room, then click:

#### Door Quick-Add Buttons:
```
Quick Add: [1×2 PVC] [0.9×2 PVC] [1×2 Steel 120kg]
```

#### Window Quick-Add Buttons:
```
Quick Add: [0.5×1.5 PVC] [1×1.5 Alu] [1.6×1.4 Alu]
```

**One click** → Door/window instantly added to the selected room!

No dialog, no typing - just **click and done**! ⚡

---

## 📝 Detailed Workflow Examples

### Example 1: Adding a Standard Door (Template Method)

1. **Go to Room Manager** tab
2. **Select a room** (e.g., "Living Room")
3. **Click "➕ Add Door"**
4. **Click template dropdown** → Select `1.0×2.0 PVC`
5. All fields auto-fill:
   - Type: PVC
   - Width: 1.0m
   - Height: 2.0m
   - Weight: 15kg
   - Placement Height: 0.0m
6. **Customize if needed** (e.g., change quantity to 2)
7. **Click Save**

**Result**: Door added to Living Room in ~5 seconds!

---

### Example 2: Quick-Add a Window (One-Click Method)

1. **Go to Room Manager** tab
2. **Select a room** (e.g., "Bedroom")
3. **Click `1×1.5 Alu`** button
4. **Done!** Window instantly added:
   - Name: W1 (auto-generated)
   - Type: Aluminum
   - Size: 1.0×1.5m
   - Sill Height: 1.0m
   - Assigned to: Bedroom

**Result**: Window added in **1 second**! ⚡

---

### Example 3: Reusing Your Own Doors/Windows

**Scenario**: You added a custom door `D1` (0.85×2.15m PVC with special weight 18kg).

Now you want to add the **same type** to another room:

1. **Click "➕ Add Door"** in Room Manager
2. **Template dropdown** → Select `📋 D1`
3. All D1's specs auto-fill:
   - Type: PVC
   - Width: 0.85m
   - Height: 2.15m
   - Weight: 18kg
4. **Name will be D2** (auto-generated)
5. **Click Save**

**Result**: Exact copy of D1 added as D2!

---

## 🎨 Template System Features

### ✅ Smart Auto-Fill

When you select a template, the system fills:

**For Doors**:
- Name (auto-generated unique name)
- Type (Wood/Steel/PVC)
- Width (meters)
- Height (meters)
- Weight (kg per door)
- Placement Height (floor level = 0.0m)
- Quantity (defaults to 1, customizable)

**For Windows**:
- Name (auto-generated unique name)
- Type (Aluminum/PVC/Wood/Steel)
- Width (meters)
- Height (meters)
- Placement Height (sill height from floor)
- Quantity (defaults to 1, customizable)

### ✅ Fully Customizable

**After selecting a template**, you can:
- Change the name
- Adjust width/height
- Modify weight (doors)
- Change placement height
- Update quantity
- Switch material type

Templates are just **starting points** - you have full control!

---

## 🛠️ Template Definitions (Technical)

### Door Templates (config.py)

```python
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
    # ... more templates
]
```

### Window Templates (config.py)

```python
DEFAULT_WINDOW_TEMPLATES = [
    {
        'name': '1.0×1.5 Aluminum',
        'type': 'Aluminum',
        'width': 1.0,
        'height': 1.5,
        'placement_height': 1.0,
        'description': 'Standard aluminum window 1.0×1.5m'
    },
    # ... more templates
]
```

---

## 🔧 Customizing Templates

### Adding Your Own Predefined Templates

**Edit**: `bilind/core/config.py`

**Add to DEFAULT_DOOR_TEMPLATES**:
```python
{
    'name': '0.7×2.0 Wood Bathroom',
    'type': 'Wood',
    'width': 0.7,
    'height': 2.0,
    'weight': 20,
    'placement_height': 0.0,
    'description': 'Small bathroom wooden door'
}
```

**Add to DEFAULT_WINDOW_TEMPLATES**:
```python
{
    'name': '2.0×1.8 Aluminum Panoramic',
    'type': 'Aluminum',
    'width': 2.0,
    'height': 1.8,
    'placement_height': 0.8,
    'description': 'Large panoramic window'
}
```

**Restart BILIND** → Your templates appear in dropdown!

---

## 📊 Template Categories

### **Common Door Sizes** (Predefined)

| Template | Material | Size | Weight | Use Case |
|----------|----------|------|--------|----------|
| 1.0×2.0 PVC | PVC | 1.0×2.0m | 15kg | Main entrance, bedrooms |
| 0.9×2.0 PVC | PVC | 0.9×2.0m | 15kg | Interior rooms, standard |
| 1.0×2.0 Steel 120kg | Steel | 1.0×2.0m | 120kg | Heavy security doors |
| 0.8×2.1 Wood | Wood | 0.8×2.1m | 25kg | Classic wooden doors |
| 0.9×2.1 Wood | Wood | 0.9×2.1m | 25kg | Wide wooden doors |

### **Common Window Sizes** (Predefined)

| Template | Material | Size | Sill Height | Use Case |
|----------|----------|------|-------------|----------|
| 0.5×1.5 PVC | PVC | 0.5×1.5m | 1.0m | Small bathrooms, kitchens |
| 1.0×1.5 Aluminum | Aluminum | 1.0×1.5m | 1.0m | Standard bedrooms |
| 1.0×2.0 Aluminum | Aluminum | 1.0×2.0m | 0.5m | Tall living room windows |
| 1.1×1.3 PVC | PVC | 1.1×1.3m | 1.0m | Medium rooms |
| 1.6×1.4 Aluminum | Aluminum | 1.6×1.4m | 1.0m | Wide panoramic |
| 1.2×1.5 Steel | Steel | 1.2×1.5m | 1.0m | Industrial/security |

---

## ⚡ Performance Benefits

### Before Templates:
1. Click "Add Door"
2. Type name: `D1`
3. Select type: `PVC`
4. Enter width: `1.0`
5. Enter height: `2.0`
6. Enter weight: `15`
7. Enter placement: `0.0`
8. Click Save

**Time**: ~30 seconds per door

### After Templates (Quick-Add):
1. Select room
2. Click `1×2 PVC` button

**Time**: ~2 seconds per door

### **Result**: 15x faster! ⚡

---

## 🎯 Best Practices

### 1. **Use Quick-Add for Standard Sizes**
If you're adding many standard doors/windows, use Quick-Add buttons in Room Manager.

### 2. **Use Templates for Similar Items**
Adding 10 identical windows? Select template once, adjust quantity, done.

### 3. **Create Reusable Custom Templates**
Add your first custom door carefully (with all specs) → it becomes a template for next ones!

### 4. **Still Use Manual for Unique Items**
For one-off special sizes, select "Custom (manual entry)" and type values.

---

## 🔍 Template Selection Logic

**Template dropdown shows** (in order):

1. ✅ **"-- Custom (manual entry) --"** (default)
2. ✅ **Predefined templates** (from config.py)
   - Sorted by most common first
3. ✅ **Your existing doors/windows** (marked with 📋)
   - Sorted by name

**Total available**: Predefined (5-6 each) + Your existing (unlimited)

---

## 🌍 Multi-Language Support

Templates work seamlessly with Arabic/English:
- Template names are in English (universal measurements)
- Dialog labels are bilingual
- Quick-add buttons use compact English labels
- Descriptions can be customized per template

---

## 🆘 Troubleshooting

### ❓ "Template dropdown is empty"
✅ Check `bilind/core/config.py` - DEFAULT_DOOR_TEMPLATES / DEFAULT_WINDOW_TEMPLATES should exist

### ❓ "Quick-Add buttons don't work"
✅ Make sure you **selected a room first** in Room Manager
✅ Check console for error messages

### ❓ "Can't find my custom door in templates"
✅ Templates update when dialog opens - add door first, then open "Add Door" dialog again

### ❓ "Template filled wrong values"
✅ You can manually edit any field after selecting template
✅ Check template definition in config.py

---

## 📈 Future Enhancements

Potential additions (not yet implemented):

- 🔄 **Export/Import Template Sets** - Share templates between projects
- 🎨 **Template Images** - Visual preview of door/window types
- 📐 **Unit Conversion** - Templates in cm, mm, inches
- 🏷️ **Template Categories** - Group by room type (bathroom, bedroom, etc.)
- 🔧 **Template Editor UI** - Manage templates without editing config.py
- 💾 **Project-Specific Templates** - Templates that save with project

---

## 🚀 Quick Reference Card

### Add Door/Window (Any Tab):
```
1. Click "Add Door/Window"
2. Select template from dropdown
3. (Optional) Customize fields
4. Click Save
```

### Quick-Add (Room Manager):
```
1. Select room
2. Click Quick-Add button
3. Done!
```

### Reuse Existing:
```
1. Add first door/window manually
2. It appears in template dropdown
3. Select it for next doors/windows
```

---

## 🎉 Summary

The **Templates System** transforms door/window management from a **tedious repetitive task** into a **lightning-fast workflow**!

**Choose your speed**:
- 🚀 **Quick-Add buttons** - Fastest (1-2 seconds)
- ⚡ **Template dropdown** - Fast (5-10 seconds)
- ✏️ **Manual entry** - Flexible (30+ seconds, full control)

**All methods coexist** - use what fits your workflow!

---

**Developed by BILIND Team** 🏗️  
**Version**: 2.0 - November 2025  
**Feature**: Door & Window Templates System
