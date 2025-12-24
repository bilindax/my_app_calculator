# Wall Picker in Room Configuration - Feature Complete

## Overview
The room picker now includes full wall picking and configuration capabilities directly within the room setup dialog.

## New Features

### 1. **Wall Picker Button**
- Each room card now has a "🧱 Add Walls" button
- Click to pick walls directly from AutoCAD for that specific room
- Button updates to show count: "🧱 Walls (3)" after picking

### 2. **Wall Configuration Dialog**
For each picked wall, you can configure:

#### Basic Properties
- **Wall Name**: Custom name (default: "Wall 1", "Wall 2", etc.)
- **Length**: Auto-filled from AutoCAD pick, editable
- **Height**: Wall height in meters (default: 3.0m)

#### Ceramic Coverage
- **Ceramic Height**: Height of ceramic tiles (0 = no ceramic)
  - Example: 1.5m for half-height bathroom tiles
  - 0 for walls without ceramic

#### Opening Assignment
- **Checkbox list** of all available doors and windows
- Select which openings belong to this specific wall
- Shows opening dimensions for easy identification
- Example: "🚪 Door1 (0.90m × 2.10m)"

### 3. **Workflow**

```
1. Pick Rooms (as usual)
2. Room Configuration Dialog appears
3. For each room:
   a. Set Room Type, Wall Height
   b. Click "🧱 Add Walls"
   c. Pick wall line in AutoCAD
   d. Configure wall (name, height, ceramic, openings)
   e. Repeat for more walls or click "No" when done
4. Save All
```

### 4. **Data Integration**
- Picked walls are automatically added to `self.project.walls`
- Wall objects include:
  - Name, layer, length, height
  - Gross area (auto-calculated)
  - Ceramic area (from ceramic_height)
  - Assigned opening IDs
  - Deduction & net areas (calculated)
  
### 5. **UI Updates**
- Wall count stored in room data
- Walls visible in Walls tab immediately after save
- Full wall metrics available for calculations

## Example Use Case

**Kitchen with 4 walls:**
1. Pick room polygon
2. In config dialog, set Type = "Kitchen"
3. Click "🧱 Add Walls"
4. Pick Wall 1 (sink wall):
   - Name: "Sink Wall"
   - Length: 3.5m (from AutoCAD)
   - Height: 3.0m
   - Ceramic Height: 1.5m (backsplash)
   - Openings: [Window1]
5. Pick Wall 2 (door wall):
   - Name: "Entry Wall"
   - Ceramic: 0 (no tiles)
   - Openings: [Door1]
6. Repeat for remaining walls
7. Save All

**Result:**
- Room created with type, dimensions
- 4 walls created with individual configurations
- Ceramic areas calculated per wall
- Openings deducted from correct walls

## Benefits
- **Accuracy**: Each wall independently configured
- **Ceramic Control**: Per-wall ceramic heights
- **Opening Assignment**: Explicit wall-opening relationships
- **Time Saving**: All done in one flow
- **Flexibility**: 0 to any number of walls per room

## Technical Notes
- Walls stored as `Wall` objects in `project.walls`
- Temporary storage in room dict during configuration
- Cleaned up after save to avoid memory bloat
- AutoCAD interaction handled via existing `picker.pick_walls()`
