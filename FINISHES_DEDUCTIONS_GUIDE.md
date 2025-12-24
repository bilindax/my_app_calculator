# Phase 8.1: Dynamic Finishes Deductions - Quick Guide

## ✅ New Features Implemented

### 1. **🚪 Deduct Doors Button**
- Deduct door areas from any finish (Plaster/Paint/Tiles)
- Select specific doors to deduct
- Set quantity multiplier per door (if duplicated)
- Example: "D1 ×2" deducts the same door twice

### 2. **🪟 Deduct Windows Button**  
- Deduct window areas from any finish
- Select specific windows to deduct
- Set quantity multiplier per window
- Example: "W3 ×3" deducts window area 3 times

### 3. **📋 Enhanced Room Selection**
- Modern dialog with checkboxes for each room
- "Select All" / "Deselect All" buttons
- Real-time preview: "Selected: 5 items • Total: 125.50 m²"
- Apply only to selected rooms

### 4. **🔢 Quantity Multipliers**
- For doors/windows: multiply deduction by N times
- Useful when same opening appears multiple times
- No need to add duplicate entries manually

---

## 🎯 How to Use

### **Deducting Doors from Finishes:**

1. Go to **Finishes** tab
2. Choose section (Plaster/Paint/Tiles)
3. Click **"🚪 Deduct Doors"**
4. Dialog appears with all doors:
   ```
   ☑ D1 - Wood       1.89 m²    Qty: [2]
   ☑ D2 - Steel      2.20 m²    Qty: [1]
   ☐ D3 - PVC        1.50 m²    Qty: [1]
   ```
5. Uncheck doors you DON'T want to deduct
6. Adjust quantity if door is duplicated
7. Click **"✓ OK"**
8. Result in table:
   ```
   | Description         | Net Area | With Waste |
   |---------------------|----------|------------|
   | Deduction: D1 (×2)  | -3.78    | -3.97      |
   | Deduction: D2       | -2.20    | -2.31      |
   ```

### **Deducting Windows:**

Same process, but click **"🪟 Deduct Windows"** instead.

---

## 💡 Use Cases

### **Case 1: Standard Deduction**
```
Scenario: Plaster walls, deduct all doors
Action: Click "🚪 Deduct Doors" → Select All → OK
Result: All door areas deducted once
```

### **Case 2: Duplicate Openings**
```
Scenario: Main door D1 appears twice in plan
Action: Click "🚪 Deduct Doors" → Select D1 → Set Qty to 2 → OK
Result: D1 area deducted twice (×2)
```

### **Case 3: Selective Deduction**
```
Scenario: Don't deduct bathroom doors (too small)
Action: Click "🚪 Deduct Doors" → Uncheck DB1, DB2 → OK
Result: Only main doors deducted
```

### **Case 4: Multiple Deductions**
```
Scenario: Deduct doors, then windows, then ceramic
Actions:
1. "🚪 Deduct Doors" → Select all → OK
2. "🪟 Deduct Windows" → Select all → OK  
3. "➖ Deduct Ceramic" → OK

Result:
| Description              | Net Area |
|--------------------------|----------|
| Room1                    | 25.00    |
| Deduction: D1            | -1.89    |
| Deduction: W1 (×2)       | -3.06    |
| Deduction: Ceramic zones | -5.50    |
| **Total**                | **14.55**|
```

---

## 🔧 Technical Details

### **ItemSelectorDialog Component**
- Location: `bilind/ui/dialogs/item_selector_dialog.py`
- Features:
  - Checkbox list with scrollable area
  - Quantity spinbox per item (1-10)
  - Real-time summary calculation
  - Mouse wheel scrolling support
  - Color-coded with app theme

### **Finishes Tab Updates**
- Added `deduct_openings_from_finish(key, type)` method
- Updated toolbar with 2 new buttons per section (×3 sections = 6 buttons)
- Integrated with ItemSelectorDialog for UX
- Supports both dataclass and dict-based openings

### **Button Layout (per section):**
```
Before:
[➕ Room Areas] [📐 Room Walls] [🧱 Wall Net] [✍️ Manual] 
[➖ Deduct] [✏️ Edit] [🗑️ Del]

After:
[➕ Room Areas] [📐 Room Walls] [🧱 Wall Net]
[🚪 Deduct Doors] [🪟 Deduct Windows] [➖ Deduct Ceramic]
[✍️ Manual] [✏️ Edit] [🗑️ Del]
```

---

## ✅ Benefits

| Before | After |
|--------|-------|
| ❌ No door/window deduction | ✅ Dedicated buttons |
| ❌ Manual calculation needed | ✅ Automatic area calculation |
| ❌ Can't handle duplicates | ✅ Quantity multiplier |
| ❌ All-or-nothing selection | ✅ Choose specific items |
| ❌ No preview | ✅ Real-time total preview |

---

## 📝 Example Workflow

**Project: 3-bedroom apartment**

**Plaster Section:**
1. Click "➕ Room Areas" → Select Living, Kitchen, Bedroom1, Bedroom2, Bedroom3 → OK
   - Net: 125.50 m²
2. Click "🚪 Deduct Doors" → Select D1 (×2), D2, D3, D4 → OK
   - Deduction: -8.50 m²
3. Click "🪟 Deduct Windows" → Select W1, W2, W3, W4 (×2) → OK
   - Deduction: -12.80 m²
4. Click "➖ Deduct Ceramic" → OK (bathrooms/kitchen)
   - Deduction: -15.20 m²

**Result:**
```
Net Area: 125.50 m²
Total Deductions: -36.50 m²
Final Net: 89.00 m²
With Waste (+5%): 93.45 m²
```

---

## 🚀 What's Next?

This feature enables:
- ✅ Accurate finish calculations
- ✅ Flexible deduction strategies
- ✅ Easy handling of duplicate elements
- ✅ Better user control and transparency

**Suggested improvements for Phase 9:**
- [ ] Bulk edit quantity for multiple items
- [ ] Save/load deduction presets
- [ ] Auto-suggest duplicates based on layer/name matching
- [ ] Visual preview of what's being deducted (highlight in plan)

---

**Date**: October 28, 2025  
**Status**: ✅ Completed & Tested  
**Files Modified**:
- `bilind/ui/tabs/finishes_tab.py`
- `bilind/ui/dialogs/item_selector_dialog.py` (new)
