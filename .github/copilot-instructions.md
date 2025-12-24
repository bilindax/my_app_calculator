# BILIND AutoCAD Quantity Takeoff Tool - AI Agent Instructions

## Project Overview

**BILIND** is a Python/Tkinter desktop application that integrates with AutoCAD via COM interface (pyautocad) to calculate construction quantities (rooms, doors, windows, walls, finishes) from .dwg files.

**Current State**: **Modular Architecture (Enhanced)**. The application has moved away from a monolithic structure into a tab-based modular design with specialized UI components and a robust data model.

---

## Critical Architecture Knowledge

### 1. **Modular Tab Architecture**

**Orchestrator**: ilind_main.py (BilindEnhanced class)
- Initializes the main window and AutoCAD connection.
- Manages global state (self.project, self.scale).
- Instantiates tabs from ilind.ui.tabs.

**UI Components** (ilind/ui/):
- **Tabs**: Each functional area is a separate class in ilind/ui/tabs/ (e.g., RoomsTab, CeramicTab, CoatingsTab).
- **MiniPicker**: ilind/ui/mini_picker.py - A floating, always-on-top toolbar for continuous room picking without main window toggling.
- **Styles**: ilind/ui/modern_styles.py handles theming (Dark/Light/Cyborg) using 	tkbootstrap concepts.

**File Structure**:
`
bilind/
 ui/
    mini_picker.py       # Floating toolbar for picking
    modern_styles.py     # Theme manager
    tabs/
        rooms_tab.py     # Main room list
        room_manager_tab.py # Detailed room editor
        ceramic_tab.py   # Hard finishes (Tiles, Stone)
        coatings_tab.py  # Soft finishes (Plaster, Paint)
        quantities_tab.py # Consolidated ledger
        ...
 autocad/
    picker.py            # AutoCAD interaction logic
    ...
 models/
    project.py           # Root data object
    room.py
    finish.py            # CeramicZone, FinishItem
    ...
 ...
`

### 2. **AutoCAD COM Interface Constraints**

**Critical Limitation**: Uses pyautocad (COM wrapper).
- **Process**: Runs as a separate process.
- **Selection**: SelectOnScreen is modal and requires the Tkinter window to hide (or be unobtrusive).
- **MiniPicker Workflow**:
    1. Main window hides.
    2. MiniPicker (small floating bar) appears.
    3. User selects "Room Type" on MiniPicker.
    4. User clicks "Pick" -> MiniPicker hides -> AutoCAD selection active.
    5. Selection done -> MiniPicker reappears for next pick.
    6. "Finish" restores main window.

### 3. **Data Structure & Models**

**Hybrid Approach**:
- **Legacy**: Dictionaries are still heavily used for UI treeview population and some calculations.
- **Modern**: dataclasses (e.g., Room, CeramicZone) are used in ilind.models.
- **Project State**: self.project (instance of Project) holds all lists (ooms, doors, walls, etc.).
- **Sync**: ilind_main.py syncs self.project lists to local attributes (e.g., self.rooms = self.project.rooms) for backward compatibility.

### 4. **Trade-Specific Workflows**

**Hard Finishes (Ceramic & Stone)**:
- **Tab**: CeramicTab
- **Logic**: Manages "Ceramic Zones" (Kitchen, Bath).
- **Deductions**: Ceramic zones are automatically deducted from Plaster/Paint areas in the Coatings tab.

**Soft Finishes (Plaster & Paint)**:
- **Tab**: CoatingsTab
- **Logic**: Calculates wall areas based on Room Perimeter  Height.
- **Net Area**: Gross Wall Area - Openings - Ceramic Zones.

---

## Key Developer Workflows

### Running the Application
`powershell
python bilind_main.py
# OR
.\run.bat
`

### Adding a New Tab
1. Create ilind/ui/tabs/new_feature_tab.py.
2. Define class NewFeatureTab with a create(self) method returning a 	tk.Frame.
3. In ilind_main.py, import the class.
4. In BilindEnhanced.create_ui(), instantiate and add to self.notebook.

### Debugging
- **Console Output**: print() statements go to the VS Code terminal.
- **Status Bar**: Use self.main_app.update_status("Message", icon="?") from within tabs.

---

## Project-Specific Conventions

### Naming Patterns
- **Tabs**: self.rooms_tab, self.ceramic_tab, self.coatings_tab.
- **Treeviews**: self.rooms_tree, self.ceramic_tree.
- **Data**: self.project.rooms, self.project.ceramic_zones.

### UI Style System
- **Theme**: Managed by ModernStyleManager.
- **Colors**: Accessed via self.colors (e.g., self.colors['accent'], self.colors['bg_primary']).
- **Buttons**: Use self.create_button(...) factory method for consistent styling.

### Material Catalogs
- **Config**: ilind/core/config.py contains DOOR_TYPES, WINDOW_TYPES, COLOR_SCHEME.
- **Modifying**: Edit config.py to add new material types or change default weights.

---

## Integration Points

### 1. Room Picking (MiniPicker)
- **Source**: ilind_main.py -> pick_rooms_by_type()
- **Action**: Instantiates MiniPicker.
- **Callback**: _add_rooms_from_selection(rtype) handles the AutoCAD data extraction.

### 2. Ceramic Deductions
- **Source**: CoatingsTab
- **Logic**: When calculating plaster, it iterates through self.project.ceramic_zones.
- **Calculation**: Plaster Area = (Room Perim * Height) - Openings - Ceramic Zone Area.

### 3. Export
- **CSV/Excel/PDF**: Located in ilind/export/.
- **Data Source**: Exports read directly from self.project lists.

---

## Known Issues & Limitations

1. **COM Threading**: pyautocad calls must happen on the main thread. Background threads (like Sync) require careful pythoncom.CoInitialize() usage.
2. **Scale Factor**: self.scale is global. Changing it affects *future* picks, not existing data.
3. **Legacy References**: Some parts of ilind_main.py might still reference old tab names (inishes_tab) in comments or unused methods. Always check hasattr before accessing tabs.

---

## Useful Commands for AI Agents

`powershell
# Check syntax
python -m py_compile bilind_main.py

# Run tests
python -m pytest tests/ -v

# Find tab usage
grep_search "class .*Tab" bilind/ui/tabs/
`

**Last Updated**: 2025-11-19 (Reflecting Modular Architecture & MiniPicker)
