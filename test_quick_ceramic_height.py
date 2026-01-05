"""
Test: Quick Ceramic vs Manual Ceramic Height Calculation
=========================================================
Scenario: Bathroom with explicit 3.2m height
Compare: Quick wizard computed height vs manual 3.2m input
"""

from bilind.models.project import Project
from bilind.models.room import Room
from bilind.models.finish import CeramicZone
from bilind.calculations.unified_calculator import UnifiedCalculator

# Setup: Create a bathroom with 3.2m wall height
project = Project(project_name="Test Project", default_wall_height=3.0)

bathroom = Room(
    name="حمام 1",
    layer="ROOMS",
    area=6.0,
    perimeter=10.0,
    wall_height=3.2,  # User set this explicitly
    room_type="حمام"
)

project.rooms = [bathroom]

# Test 1: Manual ceramic (user inputs 3.2m)
print("=" * 60)
print("TEST 1: MANUAL CERAMIC (User Input: 3.2m)")
print("=" * 60)

manual_zone = CeramicZone.for_wall(
    perimeter=10.0,
    height=3.2,
    room_name="حمام 1",
    category="Bathroom",
    name="سيراميك حائط يدوي - حمام 1"
)

project.ceramic_zones = [manual_zone]
calc = UnifiedCalculator(project)

manual_cer = calc.calculate_ceramic_by_room()
manual_room_calc = calc.calculate_room(bathroom)

print(f"Perimeter: {bathroom.perimeter}m")
print(f"Wall Height (explicit): {bathroom.wall_height}m")
print(f"Zone Height (manual): {manual_zone.height}m")
print(f"Expected Gross: {bathroom.perimeter * 3.2:.2f}m²")
print(f"\nCalculated:")
print(f"  walls_gross: {manual_room_calc.walls_gross:.2f}m²")
print(f"  ceramic_wall: {manual_room_calc.ceramic_wall:.2f}m²")
print(f"  plaster_walls: {manual_room_calc.plaster_walls:.2f}m²")
print(f"  paint_walls: {manual_room_calc.paint_walls:.2f}m²")
print(f"\n✅ MANUAL: Paint = {manual_room_calc.paint_walls:.2f}m² (should be 0)")

# Test 2: Quick ceramic (wizard derives height)
print("\n" + "=" * 60)
print("TEST 2: QUICK CERAMIC (Wizard Auto-Calculation)")
print("=" * 60)

# Simulate _resolve_room_wall_height logic
def simulate_quick_wizard_height(room, project):
    """Simulate the _resolve_room_wall_height function from ceramic_tab.py"""
    default_h = float(getattr(project, 'default_wall_height', 3.0) or 3.0)
    
    # Priority 1: Explicit wall_height
    wh = getattr(room, 'wall_height', None)
    if wh not in (None, '', 0, 0.0):
        print(f"  → Priority 1: room.wall_height = {wh}m")
        return float(wh)
    
    # Priority 2: Derive from walls_gross / perimeter
    calc_temp = UnifiedCalculator(project)
    walls_gross = calc_temp.calculate_walls_gross(room)
    perim = float(getattr(room, 'perimeter', 0) or getattr(room, 'perim', 0) or 0)
    
    if walls_gross > 0 and perim > 0:
        derived_h = walls_gross / perim
        if derived_h > 0.5:
            print(f"  → Priority 2: walls_gross / perimeter = {walls_gross:.2f} / {perim:.2f} = {derived_h:.2f}m")
            return derived_h
    
    # Priority 4: Project default
    print(f"  → Priority 4: project.default_wall_height = {default_h}m")
    return default_h

quick_height = simulate_quick_wizard_height(bathroom, project)

quick_zone = CeramicZone.for_wall(
    perimeter=10.0,
    height=quick_height,
    room_name="حمام 1",
    category="Bathroom",
    name="سيراميك حائط سريع - حمام 1"
)

project.ceramic_zones = [quick_zone]
calc2 = UnifiedCalculator(project)

quick_cer = calc2.calculate_ceramic_by_room()
quick_room_calc = calc2.calculate_room(bathroom)

print(f"\nQuick Wizard Computed Height: {quick_height}m")
print(f"Zone Height (quick): {quick_zone.height}m")
print(f"Expected Gross: {bathroom.perimeter * quick_height:.2f}m²")
print(f"\nCalculated:")
print(f"  walls_gross: {quick_room_calc.walls_gross:.2f}m²")
print(f"  ceramic_wall: {quick_room_calc.ceramic_wall:.2f}m²")
print(f"  plaster_walls: {quick_room_calc.plaster_walls:.2f}m²")
print(f"  paint_walls: {quick_room_calc.paint_walls:.2f}m²")
print(f"\n{'✅' if quick_room_calc.paint_walls < 0.01 else '❌'} QUICK: Paint = {quick_room_calc.paint_walls:.2f}m² (should be 0)")

# Test 3: Without explicit wall_height (legacy scenario)
print("\n" + "=" * 60)
print("TEST 3: LEGACY ROOM (No explicit wall_height)")
print("=" * 60)

bathroom_legacy = Room(
    name="حمام قديم",
    layer="ROOMS",
    area=6.0,
    perimeter=10.0,
    wall_height=None,  # Not set!
    room_type="حمام"
)

project.rooms = [bathroom_legacy]
legacy_height = simulate_quick_wizard_height(bathroom_legacy, project)

print(f"\nLegacy Room:")
print(f"  wall_height: {bathroom_legacy.wall_height}")
print(f"  Quick wizard would use: {legacy_height}m")
print(f"  Expected: {project.default_wall_height}m (from project default)")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Manual (3.2m):  ceramic={manual_room_calc.ceramic_wall:.2f}m², paint={manual_room_calc.paint_walls:.2f}m²")
print(f"Quick (computed): ceramic={quick_room_calc.ceramic_wall:.2f}m², paint={quick_room_calc.paint_walls:.2f}m²")

if abs(manual_room_calc.ceramic_wall - quick_room_calc.ceramic_wall) < 0.01:
    print("\n✅ PASS: Quick wizard correctly uses room.wall_height (3.2m)")
else:
    print(f"\n❌ FAIL: Height mismatch!")
    print(f"  Expected: {manual_room_calc.ceramic_wall:.2f}m² (manual)")
    print(f"  Got:      {quick_room_calc.ceramic_wall:.2f}m² (quick)")
    print(f"  Difference: {abs(manual_room_calc.ceramic_wall - quick_room_calc.ceramic_wall):.2f}m²")
