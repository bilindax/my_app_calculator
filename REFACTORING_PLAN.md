pip install -r requirements.txt
# BILIND Refactoring Plan - Modular Architecture

## 🎯 Goal
Transform the monolithic 4,710-line `bilind_main.py` into a maintainable, modular architecture without breaking existing functionality.

## 📊 Current State Analysis

### Problems with Current Architecture
1. **Single File Complexity**: 4,710 lines in one file
2. **Testing Difficulty**: Only 3 unit tests possible (calculation helpers)
3. **Merge Conflicts**: Multiple developers can't work simultaneously
4. **Code Navigation**: Hard to find specific functionality
5. **Reusability**: Can't reuse components in other projects
6. **IDE Performance**: Large files slow down intellisense

### What Works Well (Keep This!)
- ✅ AutoCAD COM integration is stable
- ✅ UI is polished and user-friendly
- ✅ Data flow is logical (pick → calculate → export)
- ✅ Export functionality works reliably

---

## 🏗️ Proposed Architecture

```
bilind/
├── __init__.py                 # Package initialization
├── main.py                     # Entry point (launches app)
│
├── core/
│   ├── __init__.py
│   ├── app.py                  # Main BilindApp class (orchestrator)
│   └── config.py               # Color schemes, constants, catalogs
│
├── models/                     # Data structures
│   ├── __init__.py
│   ├── room.py                 # Room dataclass
│   ├── opening.py              # Door/Window dataclass
│   ├── wall.py                 # Wall dataclass
│   └── finish.py               # Finish item dataclass
│
├── autocad/                    # AutoCAD COM integration
│   ├── __init__.py
│   ├── connection.py           # AutoCAD connection manager
│   ├── picker.py               # Object selection logic
│   ├── extractor.py            # Dimension/attribute extraction
│   └── inserter.py             # Insert table to AutoCAD
│
├── calculations/               # Business logic
│   ├── __init__.py
│   ├── room_calc.py            # Room area/perimeter
│   ├── opening_calc.py         # Door/window calculations
│   ├── wall_calc.py            # Wall deductions
│   └── finish_calc.py          # Plaster/paint/tiles
│
├── ui/                         # User interface
│   ├── __init__.py
│   ├── main_window.py          # Root Tk window
│   ├── styles.py               # ttk styles setup
│   ├── status_bar.py           # Status bar widget
│   │
│   └── tabs/
│       ├── __init__.py
│       ├── base_tab.py         # Shared tab functionality
│       ├── rooms_tab.py        # Rooms tab
│       ├── walls_tab.py        # Walls tab
│       ├── finishes_tab.py     # Finishes tab
│       ├── materials_tab.py    # Materials tab
│       ├── summary_tab.py      # Summary tab
│       ├── dashboard_tab.py    # Dashboard tab
│       ├── costs_tab.py        # Costs tab
│       └── sync_tab.py         # Sync log tab
│
└── export/                     # Export functionality
    ├── __init__.py
    ├── csv_export.py           # CSV exporter
    ├── excel_export.py         # Excel exporter
    └── pdf_export.py           # PDF exporter
```

---

## 📋 Phase-by-Phase Implementation

### Phase 1: Foundation (Low Risk) ⭐ START HERE
**Goal**: Extract standalone functions without breaking current code

**Steps**:
1. Create `bilind/` package directory
2. Move material catalogs to `bilind/core/config.py`:
   ```python
   DOOR_TYPES = {
       'Wood': {'weight': 25, 'material': 'Wood', 'description': '...'},
       # ...
   }
   WINDOW_TYPES = { ... }
   COLOR_SCHEME = { ... }
   ```

3. Extract calculation helpers to `bilind/calculations/helpers.py`:
   - `_build_opening_record()`
   - `_fmt()`
   - Move existing tests to test these

4. Update `bilind_main.py` to import from new modules:
   ```python
   from bilind.core.config import DOOR_TYPES, COLOR_SCHEME
   from bilind.calculations.helpers import build_opening_record, format_number
   ```

**Success Criteria**:
- All tests still pass
- Application runs without changes
- New modules are importable

---

### Phase 2: Models (Medium Risk)
**Goal**: Replace dictionaries with typed dataclasses

**Steps**:
1. Create `bilind/models/room.py`:
   ```python
   from dataclasses import dataclass
   from typing import Optional
   
   @dataclass
   class Room:
       name: str
       layer: str
       width: Optional[float] = None
       length: Optional[float] = None
       perimeter: float = 0.0
       area: float = 0.0
       
       def to_dict(self) -> dict:
           """For backward compatibility with export"""
           return {
               'name': self.name,
               'layer': self.layer,
               'w': self.width,
               'l': self.length,
               'perim': self.perimeter,
               'area': self.area
           }
   ```

2. Gradually replace `self.rooms = []` with typed lists:
   ```python
   self.rooms: List[Room] = []
   ```

3. Update UI refresh methods to use `room.to_dict()`

**Success Criteria**:
- Type safety in IDE
- Export still works (uses `to_dict()`)
- Can validate data (e.g., `area > 0`)

---

### Phase 3: AutoCAD Layer (Medium-High Risk)
**Goal**: Isolate COM interface code

**Steps**:
1. Create `bilind/autocad/picker.py`:
   ```python
   class AutoCADPicker:
       def __init__(self, acad_app, doc):
           self.acad = acad_app
           self.doc = doc
       
       def pick_rooms(self, scale: float) -> List[Room]:
           """Pick rooms from AutoCAD drawing"""
           # Move logic from pick_rooms() method
           pass
   ```

2. Update `bilind_main.py`:
   ```python
   from bilind.autocad.picker import AutoCADPicker
   
   self.picker = AutoCADPicker(self.acad, self.doc)
   
   def pick_rooms(self):
       rooms = self.picker.pick_rooms(self.scale)
       self.rooms.extend(rooms)
       self.refresh_rooms()
   ```

**Success Criteria**:
- Can mock `AutoCADPicker` in tests
- AutoCAD integration still works
- Easier to test without AutoCAD running

---

### Phase 4: UI Tabs (High Risk)
**Goal**: Each tab is a separate module

**Steps**:
1. Create base class `bilind/ui/tabs/base_tab.py`:
   ```python
   class BaseTab(ttk.Frame):
       def __init__(self, parent, app_ref):
           super().__init__(parent)
           self.app = app_ref  # Access to main app
           self.colors = app_ref.colors
           self.create_widgets()
       
       def create_widgets(self):
           """Override in subclasses"""
           raise NotImplementedError
   ```

2. Extract each tab to its own file:
   ```python
   # bilind/ui/tabs/rooms_tab.py
   from .base_tab import BaseTab
   
   class RoomsTab(BaseTab):
       def create_widgets(self):
           # Build UI for rooms tab
           # Reference self.app.rooms for data
           pass
   ```

3. Main window assembles tabs:
   ```python
   from bilind.ui.tabs import RoomsTab, WallsTab, FinishesTab
   
   notebook = ttk.Notebook(root)
   notebook.add(RoomsTab(notebook, self), text="📐 Main")
   notebook.add(WallsTab(notebook, self), text="🧱 Walls")
   # ...
   ```

**Success Criteria**:
- Each tab is ~200-400 lines (manageable)
- Can work on tabs independently
- UI still looks/works the same

---

### Phase 5: Export Layer (Low Risk)
**Goal**: Separate export logic

**Steps**:
1. Create `bilind/export/csv_export.py`:
   ```python
   def export_to_csv(data: dict, filename: str):
       """Export project data to CSV"""
       # Move logic from export_csv() method
       pass
   ```

2. Similar for Excel and PDF exporters

**Success Criteria**:
- Can test export without UI
- Easier to add new export formats
- Export logic reusable

---

## 🧪 Testing Strategy

### Current Tests (Keep These!)
```python
tests/test_calculations.py
  ✓ test_build_opening_record_door
  ✓ test_build_opening_record_window
  ✓ test_fmt_helper
```

### New Tests to Add

#### Phase 1 Tests
```python
tests/test_config.py
  - test_door_types_structure
  - test_color_scheme_keys

tests/test_helpers.py
  - test_format_number_edge_cases
  - test_build_opening_record_validation
```

#### Phase 2 Tests
```python
tests/test_models.py
  - test_room_creation
  - test_room_to_dict
  - test_opening_validation
  - test_wall_deduction_calc
```

#### Phase 3 Tests
```python
tests/test_autocad_picker.py (with mocks)
  - test_pick_rooms_with_mock
  - test_dimension_extraction
  - test_bounding_box_fallback
```

---

## 🚨 Risks & Mitigation

### Risk 1: Breaking AutoCAD Integration
**Mitigation**:
- Test with real AutoCAD after each phase
- Keep `bilind_main.py` working until Phase 4 complete
- Use feature flags to toggle new vs. old code

### Risk 2: Data Migration Issues
**Mitigation**:
- Implement `to_dict()` methods for backward compatibility
- Test export after switching to dataclasses
- Keep sample project files for testing

### Risk 3: UI Performance Degradation
**Mitigation**:
- Profile UI refresh times before/after
- Use lazy loading for tabs
- Cache frequently accessed data

---

## 📅 Timeline Estimate

| Phase | Effort | Duration | Risk |
|-------|--------|----------|------|
| Phase 1: Foundation | 4 hours | 1 day | Low ⭐ |
| Phase 2: Models | 6 hours | 2 days | Medium |
| Phase 3: AutoCAD | 8 hours | 3 days | Medium-High |
| Phase 4: UI Tabs | 12 hours | 5 days | High |
| Phase 5: Export | 4 hours | 2 days | Low |
| **Testing/Bug fixes** | 6 hours | 2 days | - |
| **TOTAL** | ~40 hours | 2-3 weeks | - |

---

## ✅ Success Metrics

After refactoring, we should achieve:
- ✅ **Code Organization**: No file > 500 lines
- ✅ **Test Coverage**: >50% (up from ~5%)
- ✅ **IDE Performance**: Instant intellisense
- ✅ **Team Collaboration**: Multiple people can work simultaneously
- ✅ **Maintainability**: New features take 50% less time
- ✅ **Documentation**: Each module has clear docstrings

---

## 🔄 Rollback Plan

If refactoring fails:
1. Git revert to last working commit
2. Keep `bilind_main.py` in `_legacy/` as backup
3. Document lessons learned

---

## 🎓 Learning Resources

For developers new to the codebase:
1. Read `.github/copilot-instructions.md` first
2. Run tests: `python -m pytest tests/ -v`
3. Review data flows in documentation
4. Start with Phase 1 (lowest risk)

---

**Created**: 2025-10-22  
**Status**: Proposal (Not Started)  
**Priority**: HIGH - Current architecture is blocking scalability
**Next Step**: Get team approval, then start Phase 1
