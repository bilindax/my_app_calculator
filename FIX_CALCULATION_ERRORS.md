# Fix: Calculation Errors & Opening Deductions

## Problem
Users reported errors in calculations, specifically that **openings were not being deducted** from Plaster areas.
- **Live Metrics:** Showed Plaster area as `Gross Walls + Ceiling`, ignoring the 8.00m² of openings.
- **Summary Table:** Showed "Net Plaster" with the same incorrect value.

## Root Cause Analysis
1. **Live Metrics (`room_manager_tab.py`):** The code was using `room.plaster_area` directly. This value was stale or incorrect because the `Room` object didn't know about the openings.
2. **Room Model (`room.py`):** The `get_opening_total_area` method only looked at `room.opening_ids`. However, the application often links openings to rooms via `opening.assigned_rooms` without updating the room's ID list. This caused `room.plaster_area` to be calculated as if there were 0 openings.

## The Fix
1. **Updated `RoomManagerTab`:**
   - Modified `_compute_room_finish_metrics` to calculate Plaster area locally: `plaster = walls_net + area`.
   - `walls_net` is already correctly calculated (Gross - Openings), so this guarantees the Plaster value in the UI is correct.

2. **Updated `Room` Model:**
   - Rewrote `get_opening_total_area` to check **both** `room.opening_ids` AND `opening.assigned_rooms`.
   - This ensures that whenever `room.update_finish_areas()` is called, it correctly finds all openings associated with the room, regardless of which side the association is stored on.

## Verification
- **Live Metrics:** Will now show `Plaster = (Gross Walls - Openings) + Ceiling`.
  - Example from user: `(58.50 - 8.00) + 18.51 = 69.01` (Correct) instead of `77.01` (Incorrect).
- **Exports/Tables:** Since `Room.plaster_area` will now be calculated correctly, all downstream reports will be accurate.

---
*Fixed by AI Assistant*
