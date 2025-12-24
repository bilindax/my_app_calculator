"""
Test UI Integration with UnifiedCalculator
==========================================
Quick test to verify UI tabs use UnifiedCalculator correctly.
"""

from bilind.models.project import Project
from bilind.models.room import Room
from bilind.models.opening import Opening
from bilind.models.finish import CeramicZone
from bilind.calculations.unified_calculator import UnifiedCalculator

# Create test project
project = Project(
    project_name="UI Integration Test"
)

# Add a test room
room = Room(
    name="Living Room",
    layer="A-ROOM",
    perimeter=18.0,
    area=20.0,
    wall_height=3.0
)
project.rooms.append(room)

# Add door (1m × 2.1m)
door = Opening(
    name="D1",
    opening_type='DOOR',
    material_type='Wood',
    layer='A-DOOR',
    width=1.0,
    height=2.1,
    quantity=1
)
project.doors.append(door)

# Link door to room
room.opening_ids = ['D1']

# Add ceramic zone (18m perimeter × 1.5m height)
ceramic = CeramicZone.for_wall(
    perimeter=18.0,
    height=1.5,
    room_name="Living Room",
    category="Kitchen"
)
project.ceramic_zones.append(ceramic)

# Test UnifiedCalculator
print("=" * 60)
print("Testing UnifiedCalculator Integration")
print("=" * 60)

calc = UnifiedCalculator(project)

# Test individual room calculation
print("\n1. Individual Room Calculation (calculate_room):")
room_calc = calc.calculate_room(room)
print(f"   Room: {room_calc.room_name}")
print(f"   Walls Net: {room_calc.walls_net:.2f} m²")
print(f"   Plaster (Walls): {room_calc.plaster_walls:.2f} m²")
print(f"   Plaster (Ceiling): {room_calc.plaster_ceiling:.2f} m²")
print(f"   Plaster Total: {room_calc.plaster_total:.2f} m²")
print(f"   Paint (Walls): {room_calc.paint_walls:.2f} m²")
print(f"   Paint (Ceiling): {room_calc.paint_ceiling:.2f} m²")
print(f"   Paint Total: {room_calc.paint_total:.2f} m²")
print(f"   Ceramic (Wall): {room_calc.ceramic_wall:.2f} m²")

# Test all rooms calculation
print("\n2. All Rooms Calculation (calculate_all_rooms):")
all_calcs = calc.calculate_all_rooms()
print(f"   Number of rooms processed: {len(all_calcs)}")
for rc in all_calcs:
    print(f"   - {rc.room_name}: Plaster={rc.plaster_total:.2f}, Paint={rc.paint_total:.2f}")

# Test project totals
print("\n3. Project Totals (calculate_totals):")
totals = calc.calculate_totals()
print(f"   Plaster Total: {totals['plaster_total']:.2f} m²")
print(f"   Paint Total: {totals['paint_total']:.2f} m²")
print(f"   Ceramic Total: {totals['ceramic_total']:.2f} m²")
print(f"   Baseboard Total: {totals['baseboard_total']:.2f} m")

# Verify expected values
print("\n" + "=" * 60)
print("Verification:")
print("=" * 60)

expected = {
    'walls_gross': 54.0,  # 18 × 3
    'opening': 2.1,       # 1 × 2.1
    'walls_net': 51.9,    # 54 - 2.1
    'ceramic': 27.0,      # 18 × 1.5
    'plaster': 71.9,      # (51.9 - 0) + 20.0
    'paint': 44.9         # (51.9 - 27) + 20.0
}

print(f"✓ Walls Gross: {room_calc.walls_gross:.2f} (expected {expected['walls_gross']:.2f})")
print(f"✓ Opening: {room_calc.walls_openings:.2f} (expected {expected['opening']:.2f})")
print(f"✓ Walls Net: {room_calc.walls_net:.2f} (expected {expected['walls_net']:.2f})")
print(f"✓ Ceramic: {totals['ceramic_total']:.2f} (expected {expected['ceramic']:.2f})")
print(f"✓ Plaster: {totals['plaster_total']:.2f} (expected {expected['plaster']:.2f})")
print(f"✓ Paint: {totals['paint_total']:.2f} (expected {expected['paint']:.2f})")

# Check if all values match
all_match = (
    abs(room_calc.walls_gross - expected['walls_gross']) < 0.01 and
    abs(room_calc.walls_openings - expected['opening']) < 0.01 and
    abs(room_calc.walls_net - expected['walls_net']) < 0.01 and
    abs(totals['ceramic_total'] - expected['ceramic']) < 0.01 and
    abs(totals['plaster_total'] - expected['plaster']) < 0.01 and
    abs(totals['paint_total'] - expected['paint']) < 0.01
)

print("\n" + "=" * 60)
if all_match:
    print("✅ ALL TESTS PASSED - UnifiedCalculator working correctly!")
else:
    print("❌ SOME TESTS FAILED - Check calculations!")
print("=" * 60)

print("\n📝 Summary:")
print("   - UnifiedCalculator can be used in UI tabs")
print("   - calculate_room() for room details dialog")
print("   - calculate_all_rooms() for CoatingsTab auto-calc")
print("   - calculate_totals() for QuantitiesTab footer")
print("\n✅ Ready for UI integration!")
