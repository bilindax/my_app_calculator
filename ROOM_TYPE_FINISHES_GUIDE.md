# Room Type-Based Finish Calculations 🏠

## Overview

BILIND now supports **filtering finishes by room type categories**, allowing you to calculate quantities separately for different functional areas (wet areas, living spaces, outdoor, etc.).

---

## 🎯 Key Features

### 1. **Room Type Categories** (21 standard types)
- Living Room, Bedroom, Master Bedroom
- Kitchen, Dining Room
- Bathroom, Toilet/WC, Laundry Room
- Balcony, Terrace
- Hallway/Corridor, Entrance/Foyer
- Storage/Closet, Utility Room, Garage
- Office/Study, Guest Room, Library
- Gym/Fitness, Other, [Not Set]

### 2. **Triple Filtering in Main Tab**
- 🔍 **Text Search**: Filter by name
- 📐 **Layer Filter**: Filter by AutoCAD layer
- 🏠 **Room Type Filter**: Filter by room category

### 3. **Quick Action Buttons in Finishes Tab**
Four specialized button groups for common scenarios:

| Button | Room Types Included | Typical Use |
|--------|---------------------|-------------|
| 🚿 **Wet Areas** | Bathroom, Toilet/WC, Kitchen, Laundry Room | Ceramic tiles, waterproof finishes |
| 🏠 **Living Spaces** | Living Room, Bedroom, Master Bedroom, Dining Room, Office/Study | Paint, standard plaster |
| 🌳 **Outdoor** | Balcony, Terrace | Exterior tiles, weather-resistant finishes |
| 🚪 **Service** | Hallway/Corridor, Entrance/Foyer, Storage/Closet, Utility Room | Basic finishes |

---

## 📋 Workflow Example

### **Scenario**: Calculate ceramic tiles for wet areas only

#### **Step 1: Pick Rooms from AutoCAD**
```
Main Tab → Pick Rooms → Select all rooms in drawing
```

#### **Step 2: Assign Room Types**
```
Main Tab → Select each room → Edit → Choose room type from dropdown
Example:
  - "Master Bath" → Type: Bathroom
  - "Kitchen" → Type: Kitchen
  - "Living Room" → Type: Living Room
  - "Balcony" → Type: Balcony
```

#### **Step 3: Calculate Wet Area Finishes**
```
Finishes Tab → Tiles Section → 🚿 Wet Areas
```

**What happens:**
- System filters rooms by type: Bathroom, Toilet/WC, Kitchen, Laundry Room
- Shows selection dialog: "Select Bathroom Rooms (2 available)"
- User selects desired rooms
- System calculates wall areas for each wet area
- Adds items to tiles list with room type labels:
  ```
  Walls: Master Bath (Bathroom) - 63.0m × 3.0m = 189.0 m²
  Walls: Kitchen (Kitchen) - 21.0m × 2.8m = 58.8 m²
  Total Wet Area Tiles = 247.8 m²
  ```

#### **Step 4: Calculate Living Space Finishes**
```
Finishes Tab → Paint Section → 🏠 Living Spaces
```

**What happens:**
- System filters rooms: Living Room, Bedroom, Master Bedroom, Dining Room, Office/Study
- Shows only living space rooms in dialog
- User selects desired rooms
- Adds wall areas for paint calculation
- Items show room types:
  ```
  Walls: Living Room (Living Room) - 24.0m × 3.0m = 72.0 m²
  Walls: Master Bedroom (Master Bedroom) - 18.0m × 3.0m = 54.0 m²
  Total Living Space Paint = 126.0 m²
  ```

---

## 🔧 Advanced Usage

### **Manual Filtering** (for custom room combinations)

#### Method 1: Use Main Buttons with Built-in Filter
```python
# In Finishes tab, buttons now support room_type_filter:
➕ Room Areas → Select source → Filtered by room type
📐 Room Walls → Select source → Filtered by room type
```

#### Method 2: Use Room Type Filter in Main Tab
```
1. Main Tab → Room Type Filter (dropdown)
2. Select "Bathroom" → Only bathrooms shown
3. Note which bathrooms you want
4. Finishes Tab → Add manually or use quick buttons
```

---

## 📊 Room Type Statistics (Summary Tab)

The **Summary Tab** now includes visual statistics for room types:

```
┌─────────────────────────────────────────────────┐
│  🏠 Room Type Distribution                      │
├─────────────────────────────────────────────────┤
│  Bathroom       2 rooms    45.5 m²   (12.3%)   │
│  Kitchen        1 room     28.0 m²   (7.6%)    │
│  Living Room    1 room     35.0 m²   (9.5%)    │
│  Bedroom        3 rooms    72.0 m²   (19.5%)   │
│  Balcony        2 rooms    15.0 m²   (4.1%)    │
│  [Not Set]      5 rooms    174.5 m²  (47.0%)   │
├─────────────────────────────────────────────────┤
│  Total          14 rooms   370.0 m²             │
└─────────────────────────────────────────────────┘
```

---

## 💡 Tips & Best Practices

### 1. **Assign Room Types Early**
- Set room types immediately after picking from AutoCAD
- Easier to filter and calculate later
- Reduces errors in finish calculations

### 2. **Use Quick Buttons for Common Scenarios**
- 🚿 Wet Areas → Perfect for ceramic tile calculations
- 🏠 Living Spaces → Standard paint and plaster
- 🌳 Outdoor → Exterior finishes, weather-resistant materials
- 🚪 Service → Basic finishes for circulation spaces

### 3. **Combine Filters in Main Tab**
```
Text Filter: "Bath"
Layer Filter: "A-ROOM"
Type Filter: "Bathroom"
→ Shows only bathrooms on A-ROOM layer with "Bath" in name
```

### 4. **Deductions Still Work**
After adding wet area tiles:
```
Finishes Tab → Tiles Section
1. 🚿 Wet Areas (adds wall tiles)
2. 🚪 Deduct Doors (removes door areas)
3. 🪟 Deduct Windows (removes window areas)
→ Net tile area = Gross - Doors - Windows
```

### 5. **Multiple Iterations Allowed**
You can call quick buttons multiple times:
```
1. 🚿 Wet Areas → Add Master Bath and Bath 2
2. Later: 🚿 Wet Areas → Add Guest Bath (new room)
→ Both batches appear in finish list
```

---

## 🎨 Room Type-Specific Finish Recommendations

| Room Type | Typical Finishes |
|-----------|------------------|
| **Bathroom/Toilet** | Ceramic tiles (walls + floor), waterproof paint |
| **Kitchen** | Ceramic tiles (backsplash + floor), washable paint |
| **Living Room** | Paint, plaster, parquet/tiles (floor) |
| **Bedroom** | Paint, plaster, carpet/tiles (floor) |
| **Balcony/Terrace** | Exterior tiles, weather-resistant paint |
| **Hallway** | Standard paint, durable flooring |
| **Storage/Utility** | Basic paint, simple finishes |

---

## 🔍 Troubleshooting

### **Issue**: "No rooms found matching types"
**Solution**: 
- Check that rooms have been assigned the correct room type
- Go to Main Tab → Edit room → Set room type
- Room type must match exactly (case-sensitive)

### **Issue**: Quick buttons show empty dialogs
**Solution**:
- Ensure rooms are picked from AutoCAD first
- Verify room types are assigned (not "[Not Set]")
- Check that you have rooms of the selected category

### **Issue**: Wrong rooms included in calculation
**Solution**:
- Verify room types in Main Tab (Type column)
- Use Room Type Filter to check which rooms have which type
- Edit room to correct the type if needed

### **Issue**: Total doesn't match expected area
**Solution**:
- Check if multiple iterations were used (areas add up)
- Verify waste factor settings (Finishes tab top)
- Check for deductions (doors, windows, ceramic)

---

## 🚀 Future Enhancements

### Planned Features:
- **Export by Room Type**: Separate Excel sheets for each category
- **Room Type Presets**: Save custom room type groupings
- **AutoCAD Layer → Room Type Mapping**: Auto-assign types based on layer naming
- **Room Type Templates**: Pre-configured finish specifications per type

---

## 📝 Example: Complete Project Workflow

### **Project**: 3-Bedroom Apartment

#### **1. Pick Rooms** (Main Tab)
```
Pick Rooms → Select 10 polylines from AutoCAD
Result: 10 rooms added
```

#### **2. Assign Types**
```
Living Room → Type: Living Room
Master Bedroom → Type: Master Bedroom
Bedroom 2 → Type: Bedroom
Bedroom 3 → Type: Bedroom
Kitchen → Type: Kitchen
Master Bath → Type: Bathroom
Bath 2 → Type: Bathroom
Balcony → Type: Balcony
Hallway → Type: Hallway/Corridor
Storage → Type: Storage/Closet
```

#### **3. Calculate Wet Area Tiles** (Finishes Tab → Tiles)
```
🚿 Wet Areas → Select Kitchen, Master Bath, Bath 2
Dialog shows: "Select Bathroom Rooms (2 available)"
Select both → OK
Dialog shows: "Select Kitchen Rooms (1 available)"
Select Kitchen → OK
Enter wall height: 2.8m

Result:
  Walls: Master Bath (Bathroom) - 21.0m × 2.8m = 58.8 m²
  Walls: Bath 2 (Bathroom) - 15.0m × 2.8m = 42.0 m²
  Walls: Kitchen (Kitchen) - 18.0m × 2.8m = 50.4 m²
  Total = 151.2 m² (Net) → 166.3 m² (With 10% waste)
```

#### **4. Calculate Living Space Paint** (Finishes Tab → Paint)
```
🏠 Living Spaces → Select all bedrooms and living room
Enter wall height: 3.0m

Result:
  Walls: Living Room (Living Room) - 24.0m × 3.0m = 72.0 m²
  Walls: Master Bedroom (Master Bedroom) - 21.0m × 3.0m = 63.0 m²
  Walls: Bedroom 2 (Bedroom) - 15.0m × 3.0m = 45.0 m²
  Walls: Bedroom 3 (Bedroom) - 15.0m × 3.0m = 45.0 m²
  Total = 225.0 m² (Net) → 247.5 m² (With 10% waste)
```

#### **5. Deduct Openings**
```
Finishes Tab → Paint Section
🚪 Deduct Doors → Deduct all interior doors from paint
🪟 Deduct Windows → Deduct all windows from paint

Tiles Section
🚪 Deduct Doors → Deduct bathroom/kitchen doors from tiles
```

#### **6. Export**
```
Summary Tab → 📊 Export → Excel
Result: Comprehensive report with:
  - Room type breakdown
  - Wet area tiles separated
  - Living space paint separated
  - Outdoor finishes (balcony)
  - Service area finishes (hallway, storage)
```

---

## 📖 Related Documentation
- `QUICK_GUIDE.md` - Basic usage instructions
- `USAGE_GUIDE.md` - Detailed feature explanations
- `ROOM_CALCULATOR_GUIDE.md` - Room calculation workflows
- `ROOM_OPENINGS_ASSOCIATION.md` - Door/window assignment to rooms

---

**Last Updated**: 2025-01-XX  
**Feature Version**: 1.0.0  
**Status**: ✅ Production Ready
