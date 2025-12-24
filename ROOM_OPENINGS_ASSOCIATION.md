# Room-Openings Association System Design

## 🎯 Problem Statement

**Current Issue**: Openings (doors/windows) exist globally without room assignment:
- When calculating finishes, unclear which openings belong to which room
- Plaster calculations can duplicate or miss deductions
- No way to say "Living Room has D1, D2, and W1"

## ✅ Proposed Solution: Room-Opening Association

### Core Concept
```python
room = {
    'name': 'Living Room',
    'area': 25.5,
    'perimeter': 21.0,
    'opening_ids': ['D1', 'W1', 'W2'],  # ← NEW FIELD
    # ... other fields
}
```

---

## 📊 Data Structure Changes

### Before (Current):
```python
# Separate, unlinked data
self.rooms = [
    {'name': 'Living Room', 'area': 25.5, 'perim': 21.0},
    {'name': 'Bedroom', 'area': 18.0, 'perim': 17.0}
]

self.doors = [
    {'name': 'D1', 'area': 1.89},
    {'name': 'D2', 'area': 1.89}
]

self.windows = [
    {'name': 'W1', 'area': 1.80},
    {'name': 'W2', 'area': 1.50}
]
```

### After (Proposed):
```python
# Linked data with relationships
self.rooms = [
    {
        'name': 'Living Room',
        'area': 25.5,
        'perim': 21.0,
        'opening_ids': ['D1', 'W1'],  # This room has these openings
        'opening_total_area': 3.69     # Cached for performance
    },
    {
        'name': 'Bedroom',
        'area': 18.0,
        'perim': 17.0,
        'opening_ids': ['D2', 'W2'],   # Different openings
        'opening_total_area': 3.39
    }
]

# Openings stay the same
self.doors = [...]
self.windows = [...]
```

---

## 🎨 UI Changes

### 1. New Button in Main Tab
```python
┌─ Rooms Section ─────────────────────────────┐
│ [➕ Add] [✏️ Edit] [🗑️ Delete]              │
│ [🔗 Assign Openings] ← NEW BUTTON           │
│                                             │
│ Rooms Table:                                │
│ ┌───────────────────────────────────────┐  │
│ │ Name        │ Openings │ Area │ Perim │  │
│ │ Living Room │ D1,W1    │ 25.5 │ 21.0  │  │
│ │ Bedroom     │ D2,W2    │ 18.0 │ 17.0  │  │
│ └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 2. Assign Openings Dialog

**Triggered by**: Selecting a room + clicking "🔗 Assign Openings"

```python
┌─────────────────────────────────────────────┐
│ 🔗 Assign Openings to "Living Room"        │
├─────────────────────────────────────────────┤
│ Room: Living Room (25.5 m²)                │
│ Perimeter: 21.0 m                           │
├─────────────────────────────────────────────┤
│                                             │
│ 🚪 Available Doors:                         │
│ ┌─────────────────────────────────────┐    │
│ │ ☑ D1 - Wood 0.9×2.1 (1.89 m²)       │    │
│ │ ☐ D2 - Wood 0.9×2.1 (1.89 m²)       │    │
│ │ ☐ D3 - Steel 0.8×2.1 (1.68 m²)      │    │
│ └─────────────────────────────────────┘    │
│                                             │
│ 🪟 Available Windows:                       │
│ ┌─────────────────────────────────────┐    │
│ │ ☑ W1 - Aluminum 1.2×1.5 (1.80 m²)   │    │
│ │ ☐ W2 - Aluminum 1.0×1.5 (1.50 m²)   │    │
│ │ ☐ W3 - PVC 0.6×0.8 (0.48 m²)        │    │
│ └─────────────────────────────────────┘    │
│                                             │
│ ✓ Currently assigned: D1, W1               │
│ Total opening area: 3.69 m²                │
│                                             │
│ [✓ Save] [✗ Cancel] [Clear All]            │
└─────────────────────────────────────────────┘
```

### 3. Updated Rooms Treeview

Add an "Openings" column:
```python
self.rooms_tree = ttk.Treeview(
    columns=('Name', 'Layer', 'Openings', 'W', 'L', 'Perim', 'Area'),
    #                    ↑ NEW COLUMN
)
```

Display format:
- "D1,W1" if assigned
- "-" if no openings
- "D1,D2,W1,W2" if multiple

---

## 🔧 Implementation Details

### 1. New Helper Functions

```python
def get_opening_by_id(self, opening_id: str):
    """Get door or window by ID"""
    for door in self.doors:
        if door.get('name') == opening_id:
            return door
    for window in self.windows:
        if window.get('name') == opening_id:
            return window
    return None

def calculate_room_opening_area(self, room: dict) -> float:
    """Calculate total area of openings in a room"""
    total = 0.0
    for opening_id in room.get('opening_ids', []):
        opening = self.get_opening_by_id(opening_id)
        if opening:
            total += opening.get('area', 0.0)
    return total

def assign_openings_to_room(self):
    """UI handler for opening assignment"""
    selection = self.rooms_tree.selection()
    if not selection:
        messagebox.showwarning("Warning", "Select a room first")
        return
    
    room_idx = self.rooms_tree.index(selection[0])
    room = self.rooms[room_idx]
    
    # Open dialog (see below)
    result = self._opening_assignment_dialog(room)
    if result:
        room['opening_ids'] = result['selected_ids']
        room['opening_total_area'] = self.calculate_room_opening_area(room)
        self.refresh_rooms()
```

### 2. Assignment Dialog

```python
def _opening_assignment_dialog(self, room):
    """Dialog to assign doors/windows to a room"""
    dialog = tk.Toplevel(self.root)
    dialog.title(f"Assign Openings to {room['name']}")
    dialog.geometry("550x700")
    dialog.configure(bg=self.colors['bg_secondary'])
    
    # Header
    header = ttk.Frame(dialog, padding=(18, 16))
    header.pack(fill=tk.X)
    ttk.Label(header, 
              text=f"🔗 Assign Openings to \"{room['name']}\"",
              font=('Segoe UI Semibold', 14),
              foreground=self.colors['accent']).pack(anchor=tk.W)
    
    # Room info
    info_frame = ttk.Frame(dialog, padding=(18, 10))
    info_frame.pack(fill=tk.X)
    ttk.Label(info_frame,
              text=f"Room: {room['name']} ({room.get('area', 0):.2f} m²)",
              foreground=self.colors['text_secondary']).pack(anchor=tk.W)
    ttk.Label(info_frame,
              text=f"Perimeter: {room.get('perim', 0):.2f} m",
              foreground=self.colors['text_secondary']).pack(anchor=tk.W)
    
    # Currently assigned openings
    current_ids = room.get('opening_ids', [])
    
    # Doors section
    doors_frame = ttk.LabelFrame(dialog, text="🚪 Available Doors", padding=(12, 10))
    doors_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 4))
    
    doors_canvas = tk.Canvas(doors_frame, bg=self.colors['bg_card'], height=150)
    doors_scroll = ttk.Scrollbar(doors_frame, orient=tk.VERTICAL, command=doors_canvas.yview)
    doors_inner = ttk.Frame(doors_canvas)
    
    doors_canvas.create_window((0, 0), window=doors_inner, anchor='nw')
    doors_canvas.configure(yscrollcommand=doors_scroll.set)
    
    doors_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    doors_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    door_vars = {}
    for door in self.doors:
        var = tk.BooleanVar(value=door['name'] in current_ids)
        door_vars[door['name']] = var
        chk = ttk.Checkbutton(
            doors_inner,
            text=f"{door['name']} - {door.get('type', '-')} {door.get('w', 0):.2f}×{door.get('h', 0):.2f} ({door.get('area', 0):.2f} m²)",
            variable=var
        )
        chk.pack(anchor=tk.W, pady=2)
    
    doors_inner.bind("<Configure>", lambda e: doors_canvas.configure(scrollregion=doors_canvas.bbox("all")))
    
    # Windows section (similar to doors)
    windows_frame = ttk.LabelFrame(dialog, text="🪟 Available Windows", padding=(12, 10))
    windows_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
    
    windows_canvas = tk.Canvas(windows_frame, bg=self.colors['bg_card'], height=150)
    windows_scroll = ttk.Scrollbar(windows_frame, orient=tk.VERTICAL, command=windows_canvas.yview)
    windows_inner = ttk.Frame(windows_canvas)
    
    windows_canvas.create_window((0, 0), window=windows_inner, anchor='nw')
    windows_canvas.configure(yscrollcommand=windows_scroll.set)
    
    windows_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    windows_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    window_vars = {}
    for window in self.windows:
        var = tk.BooleanVar(value=window['name'] in current_ids)
        window_vars[window['name']] = var
        chk = ttk.Checkbutton(
            windows_inner,
            text=f"{window['name']} - {window.get('type', '-')} {window.get('w', 0):.2f}×{window.get('h', 0):.2f} ({window.get('area', 0):.2f} m²)",
            variable=var
        )
        chk.pack(anchor=tk.W, pady=2)
    
    windows_inner.bind("<Configure>", lambda e: windows_canvas.configure(scrollregion=windows_canvas.bbox("all")))
    
    # Summary
    summary_frame = ttk.Frame(dialog, padding=(18, 10))
    summary_frame.pack(fill=tk.X)
    
    summary_var = tk.StringVar()
    
    def update_summary():
        selected = []
        total_area = 0.0
        
        for door_id, var in door_vars.items():
            if var.get():
                selected.append(door_id)
                door = self.get_opening_by_id(door_id)
                if door:
                    total_area += door.get('area', 0.0)
        
        for window_id, var in window_vars.items():
            if var.get():
                selected.append(window_id)
                window = self.get_opening_by_id(window_id)
                if window:
                    total_area += window.get('area', 0.0)
        
        summary_var.set(f"✓ Currently assigned: {', '.join(selected) if selected else 'None'}\nTotal opening area: {total_area:.2f} m²")
    
    for var in list(door_vars.values()) + list(window_vars.values()):
        var.trace_add('write', lambda *_: update_summary())
    
    update_summary()
    
    ttk.Label(summary_frame,
              textvariable=summary_var,
              foreground=self.colors['accent'],
              font=('Segoe UI', 10, 'italic')).pack(anchor=tk.W)
    
    # Buttons
    result = {}
    
    def save():
        selected_ids = []
        for door_id, var in door_vars.items():
            if var.get():
                selected_ids.append(door_id)
        for window_id, var in window_vars.items():
            if var.get():
                selected_ids.append(window_id)
        
        result['selected_ids'] = selected_ids
        dialog.destroy()
    
    def clear_all():
        for var in list(door_vars.values()) + list(window_vars.values()):
            var.set(False)
    
    btn_frame = ttk.Frame(dialog, padding=(18, 14))
    btn_frame.pack(fill=tk.X)
    ttk.Button(btn_frame, text="✓ Save", command=save, style='Accent.TButton').pack(side=tk.LEFT, padx=4)
    ttk.Button(btn_frame, text="Clear All", command=clear_all, style='Warning.TButton').pack(side=tk.LEFT, padx=4)
    ttk.Button(btn_frame, text="✗ Cancel", command=dialog.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)
    
    dialog.wait_window()
    return result if result else None
```

---

## 🎨 Benefits

### 1. **Accurate Finish Calculations**
```python
def calculate_room_plaster_area(self, room: dict) -> float:
    """Calculate net plaster area for a room"""
    # Gross area: room perimeter × height
    gross = room.get('perim', 0) * 3.0  # 3m height
    
    # Deduct only THIS room's openings
    deduct = 0.0
    for opening_id in room.get('opening_ids', []):
        opening = self.get_opening_by_id(opening_id)
        if opening:
            deduct += opening.get('area', 0.0)
    
    net = gross - deduct
    return net
```

### 2. **Prevents Duplication**
- Each opening belongs to exactly one room
- When calculating finishes, only deduct assigned openings
- No risk of double-counting or missing openings

### 3. **Better Reporting**
```
Living Room (25.5 m²):
  - Openings: D1 (1.89 m²), W1 (1.80 m²)
  - Wall area: 63.0 m² (21.0m × 3.0m)
  - Deductions: 3.69 m²
  - Net plaster: 59.31 m²

Bedroom (18.0 m²):
  - Openings: D2 (1.89 m²), W2 (1.50 m²)
  - Wall area: 51.0 m² (17.0m × 3.0m)
  - Deductions: 3.39 m²
  - Net plaster: 47.61 m²
```

### 4. **Validation**
```python
def validate_opening_assignments(self):
    """Check for unassigned or duplicate openings"""
    assigned = set()
    for room in self.rooms:
        for opening_id in room.get('opening_ids', []):
            if opening_id in assigned:
                return f"Warning: {opening_id} assigned to multiple rooms"
            assigned.add(opening_id)
    
    all_openings = {d['name'] for d in self.doors} | {w['name'] for w in self.windows}
    unassigned = all_openings - assigned
    
    if unassigned:
        return f"Warning: Unassigned openings: {', '.join(unassigned)}"
    
    return "✓ All openings properly assigned"
```

---

## 🔄 Migration Strategy

### For Existing Projects
```python
def migrate_legacy_data(self):
    """Add opening_ids field to existing rooms"""
    for room in self.rooms:
        if 'opening_ids' not in room:
            room['opening_ids'] = []
            room['opening_total_area'] = 0.0
```

### Backward Compatibility
- Old code still works (empty `opening_ids` list)
- Gradual adoption - users can assign openings over time
- Export functions handle both old and new format

---

## 📅 Implementation Timeline

**Estimated: 6-8 hours**

1. **Data Structure** (1 hour)
   - Add `opening_ids` field to room dicts
   - Helper functions for association

2. **UI - Assign Button** (1 hour)
   - Add button to rooms section
   - Wire up event handler

3. **UI - Dialog** (3 hours)
   - Build assignment dialog
   - Checkboxes for doors/windows
   - Summary calculations

4. **Treeview Update** (1 hour)
   - Add "Openings" column
   - Format display string

5. **Finish Calculations** (2 hours)
   - Update plaster/paint/tiles logic
   - Use room-specific openings
   - Add validation

6. **Testing** (1 hour)
   - Test with sample project
   - Verify calculations
   - Export validation

---

## 🎯 Next Steps

**Option A: Implement Now (Before Refactoring)**
- Pro: Immediate value, solves real problem
- Con: More code in monolithic file

**Option B: After Phase 2 Refactoring**
- Pro: Work with clean dataclasses
- Con: Delayed benefit

**My Recommendation**: **Implement after Phase 2** 
- Phase 2 creates Room/Opening dataclasses
- Much cleaner to add `openings: List[Opening]` field
- Better type safety and validation

---

## 💡 Alternative: Quick Win Version

If you need this NOW, here's a simplified version:

```python
# Just add this to existing code
def quick_assign_openings(self):
    """Quick dialog: type opening IDs manually"""
    selection = self.rooms_tree.selection()
    if not selection:
        return
    
    room_idx = self.rooms_tree.index(selection[0])
    room = self.rooms[room_idx]
    
    current = ','.join(room.get('opening_ids', []))
    result = simpledialog.askstring(
        "Assign Openings",
        f"Enter opening IDs for {room['name']} (comma-separated):\nExample: D1,D2,W1",
        initialvalue=current
    )
    
    if result is not None:
        ids = [x.strip() for x in result.split(',') if x.strip()]
        room['opening_ids'] = ids
        self.refresh_rooms()
```

Takes 10 minutes to implement, gives 80% of the benefit!
