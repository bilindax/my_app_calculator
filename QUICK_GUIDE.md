# 🚀 Quick Guide - New Features

## 📐 Calculate Wall Areas from Room Perimeters

### Step-by-Step:

```
1. Go to: Finishes Tab → Plaster/Paint/Tiles section

2. Click: "📐 Room Walls" button

3. Dialog appears:
   ┌────────────────────────────────┐
   │ Enter wall height (m):         │
   │ [3.0              ] meters     │
   │                                │
   │ [✓ OK]    [✗ Cancel]          │
   └────────────────────────────────┘

4. Select rooms:
   ┌────────────────────────────────────────────┐
   │ ☑ Living Room - Perim: 18.00m → 54.00 m²  │
   │ ☑ Bedroom    - Perim: 14.50m → 43.50 m²  │
   │ ☐ Kitchen    - Perim: 12.00m → 36.00 m²  │
   │                                            │
   │ [Select All] [Deselect All]               │
   │ [✓ Add Selected] [✗ Cancel]               │
   └────────────────────────────────────────────┘

5. Result added:
   "Walls: Living Room (18.00m × 3.00m)" → 54.00 m²
   "Walls: Bedroom (14.50m × 3.00m)" → 43.50 m²
```

### Common Heights:
- **3.0m** - Full walls (plaster/paint)
- **0.8m** - Kitchen backsplash
- **1.5m** - Bathroom wall tiles
- **1.2m** - Wainscoting

---

## ➖ Deduct Ceramic Zones

### Step-by-Step:

```
1. First, add ceramic zones in Materials tab:
   ┌────────────────────────────────────────┐
   │ Kitchen Backsplash                     │
   │ Perimeter: 8.0m × Height: 0.8m        │
   │ = 6.4 m²                               │
   └────────────────────────────────────────┘

2. Go to: Finishes Tab → Plaster section

3. Add wall plaster:
   "Walls: Kitchen (12.00m × 3.00m)" → 36.00 m²

4. Click: "➖ Deduct" button

5. Confirmation:
   ┌────────────────────────────────────────┐
   │ Deduct 6.40 m² of ceramic zones       │
   │ from plaster?                          │
   │                                        │
   │ [Yes]  [No]                            │
   └────────────────────────────────────────┘

6. Result:
   Walls: Kitchen (12.00m × 3.00m)     +36.00 m²
   Deduction: Ceramic zones             -6.40 m²
   ───────────────────────────────────────────────
   Total Plaster:                       29.60 m²
```

---

## 🎯 Complete Kitchen Example

### Scenario: Kitchen renovation with backsplash

```
📏 ROOM DATA:
Kitchen: 4.0m × 3.5m
Perimeter: 15.0m
Area: 14.0 m²

🎨 REQUIREMENTS:
- Floor tiles: 14.0 m²
- Wall plaster: 3.0m height
- Ceramic backsplash: 0.8m height (behind counters only, 8m perimeter)

📋 WORKFLOW:

1. FLOOR TILES
   Finishes → Tiles → "➕ Room Areas"
   Select Kitchen
   Result: Floor tiles = 14.00 m²

2. WALL PLASTER
   Finishes → Plaster → "📐 Room Walls"
   Height: 3.0m
   Select Kitchen
   Result: Walls = 15.0m × 3.0m = 45.00 m²

3. CERAMIC BACKSPLASH
   Materials → Ceramic → "➕ Add Zone"
   Name: Kitchen Backsplash
   Perimeter: 8.0m
   Height: 0.8m
   Result: Ceramic = 6.40 m²

4. DEDUCT CERAMIC
   Finishes → Plaster → "➖ Deduct"
   Confirm
   Result: Net plaster = 45.00 - 6.40 = 38.60 m²

✅ FINAL QUANTITIES:
- Floor tiles: 14.00 m²
- Wall plaster: 38.60 m²
- Ceramic backsplash: 6.40 m²
```

---

## 🖱️ Button Quick Reference

### Finishes Tab Buttons:

| Icon | Button | Function |
|------|--------|----------|
| ➕ | Room Areas | Add floor areas from rooms |
| 📐 | Room Walls | Calculate wall areas (Perim × Height) |
| 🧱 | Wall Net | Add net wall areas from Walls tab |
| ✍️ | Manual | Add custom entry |
| ➖ | Deduct | Deduct ceramic zones |
| ✏️ | Edit | Modify selected entry |
| 🗑️ | Del | Delete selected entry |

---

## 💡 Tips & Tricks

### Tip 1: Different Heights for Different Rooms
```
Living Room → 3.0m (full walls)
Kitchen    → 2.8m (above cabinets only)
Bathroom   → 2.2m (above tiles)
```

### Tip 2: Multiple Finish Types
```
Same walls can have:
- Plaster: 45 m²
- Paint: 45 m²
- Ceramic deduction: -6.4 m² (both)
```

### Tip 3: Manual Adjustments
```
Use "✍️ Manual" for:
- Corrections
- Waste factors (+10%)
- Special areas
```

### Tip 4: Excel Export
```
Summary tab → "📋 Copy"
Paste in Excel → Auto-formatted table
Or: "💾 CSV" for full report
```

---

## ❓ Troubleshooting

### Q: "No ceramic zones" error when deducting?
**A:** Add ceramic zones in Materials tab first

### Q: Wall calculation showing 0?
**A:** Check room perimeter is calculated (pick rooms from AutoCAD)

### Q: Height dialog not appearing?
**A:** Ensure rooms are loaded in Main tab

### Q: Totals not updating?
**A:** Click "🔄 Refresh" in Summary tab

---

## 🎓 Training Video (Coming Soon)

Watch a 5-minute tutorial:
1. Setting up rooms
2. Calculating walls
3. Adding ceramic zones
4. Deducting ceramics
5. Exporting to Excel

---

**Need Help?** Check `USAGE_GUIDE.md` for detailed instructions.

**Found a Bug?** Report in GitHub Issues.

**Have a Suggestion?** We're listening! 🎯
