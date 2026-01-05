"""
Test Case 3: Room with explicit walls at different heights
===========================================================
Scenario: User has walls with mixed heights (e.g., 3.2m and 3.0m)
"""

from bilind.models.project import Project
from bilind.models.room import Room
from bilind.models.wall import Wall
from bilind.models.finish import CeramicZone
from bilind.calculations.unified_calculator import UnifiedCalculator

print("=" * 70)
print("SCENARIO 3: Room with EXPLICIT WALLS (mixed heights)")
print("=" * 70)

project = Project(project_name="Test Project", default_wall_height=3.0)

# Create walls with different heights
wall1 = Wall(name="Wall 1", layer="WALLS", length=3.0, height=3.2)
wall2 = Wall(name="Wall 2", layer="WALLS", length=2.0, height=3.2)
wall3 = Wall(name="Wall 3", layer="WALLS", length=3.0, height=3.2)
wall4 = Wall(name="Wall 4", layer="WALLS", length=2.0, height=3.2)

bathroom = Room(
    name="حمام متقدم",
    layer="ROOMS",
    area=6.0,
    perimeter=10.0,
    wall_height=None,  # Not set at room level
    room_type="حمام",
    walls=[wall1, wall2, wall3, wall4]
)

project.rooms = [bathroom]

print(f"\nRoom: {bathroom.name}")
print(f"  perimeter (room level): {bathroom.perimeter}m")
print(f"  wall_height (room level): {bathroom.wall_height}")
print(f"  walls:")
for w in bathroom.walls:
    print(f"    - {w.name}: {w.length}m × {w.height}m = {w.gross_area}m²")

total_wall_length = sum(w.length for w in bathroom.walls)
total_walls_gross = sum(w.gross_area for w in bathroom.walls)
avg_height = total_walls_gross / total_wall_length if total_wall_length > 0 else 0

print(f"\n  Total wall length: {total_wall_length}m")
print(f"  Total walls_gross: {total_walls_gross}m²")
print(f"  Average height: {avg_height:.2f}m")

# Test: What does UnifiedCalculator.calculate_walls_gross return?
calc = UnifiedCalculator(project)
calc_walls_gross = calc.calculate_walls_gross(bathroom)

print(f"\n  UnifiedCalculator.calculate_walls_gross(): {calc_walls_gross:.2f}m²")
print(f"  {'✅' if abs(calc_walls_gross - total_walls_gross) < 0.01 else '❌'} Matches wall sum: {abs(calc_walls_gross - total_walls_gross) < 0.01}")

# What height would quick wizard derive?
perim = bathroom.perimeter
derived_height = calc_walls_gross / perim if perim > 0 else 0

print(f"\n  Quick wizard would derive:")
print(f"    walls_gross / perimeter = {calc_walls_gross:.2f} / {perim:.2f} = {derived_height:.2f}m")

# Manual vs Quick
print("\n" + "-" * 70)
print("MANUAL: User adds ceramic at 3.2m")
print("-" * 70)

manual_zone = CeramicZone.for_wall(
    perimeter=10.0,
    height=3.2,
    room_name=bathroom.name,
    category="Bathroom"
)

project.ceramic_zones = [manual_zone]
calc1 = UnifiedCalculator(project)
room_calc_manual = calc1.calculate_room(bathroom)

print(f"Ceramic: {room_calc_manual.ceramic_wall:.2f}m²")
print(f"Plaster: {room_calc_manual.plaster_walls:.2f}m²")
print(f"Paint: {room_calc_manual.paint_walls:.2f}m²")

print("\n" + "-" * 70)
print(f"QUICK: Wizard derives {derived_height:.2f}m")
print("-" * 70)

quick_zone = CeramicZone.for_wall(
    perimeter=10.0,
    height=derived_height,
    room_name=bathroom.name,
    category="Bathroom"
)

project.ceramic_zones = [quick_zone]
calc2 = UnifiedCalculator(project)
room_calc_quick = calc2.calculate_room(bathroom)

print(f"Ceramic: {room_calc_quick.ceramic_wall:.2f}m²")
print(f"Plaster: {room_calc_quick.plaster_walls:.2f}m²")
print(f"Paint: {room_calc_quick.paint_walls:.2f}m²")

print("\n" + "=" * 70)
print("RESULT")
print("=" * 70)
if abs(room_calc_manual.ceramic_wall - room_calc_quick.ceramic_wall) < 0.01:
    print("✅ Quick wizard correctly uses wall heights → No paint discrepancy")
else:
    print(f"❌ Discrepancy: {abs(room_calc_manual.ceramic_wall - room_calc_quick.ceramic_wall):.2f}m² difference")
    print(f"   Manual ceramic: {room_calc_manual.ceramic_wall:.2f}m²")
    print(f"   Quick ceramic:  {room_calc_quick.ceramic_wall:.2f}m²")
    print(f"   Paint diff: {abs(room_calc_manual.paint_walls - room_calc_quick.paint_walls):.2f}m²")
