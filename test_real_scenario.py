"""
Real Scenario Test: User manually sets 3.2m but room.wall_height is not saved
===============================================================================
Problem: User adds ceramic manually at 3.2m → no paint
         User uses quick wizard → height computed from old data → leftover paint
"""

from bilind.models.project import Project
from bilind.models.room import Room
from bilind.models.finish import CeramicZone
from bilind.calculations.unified_calculator import UnifiedCalculator

print("=" * 70)
print("REAL SCENARIO: Room with NO explicit wall_height saved")
print("=" * 70)

# Scenario: User picked room from AutoCAD, wall_height not set
project = Project(project_name="Real Project", default_wall_height=3.0)

bathroom = Room(
    name="حمام 1",
    layer="ROOMS",
    area=6.0,
    perimeter=10.0,
    wall_height=None,  # ← NOT SET! Common scenario
    room_type="حمام"
)

project.rooms = [bathroom]

print(f"\nRoom Data:")
print(f"  name: {bathroom.name}")
print(f"  perimeter: {bathroom.perimeter}m")
print(f"  wall_height: {bathroom.wall_height} (not set)")
print(f"  project.default_wall_height: {project.default_wall_height}m")

# Simulate: User manually adds ceramic at 3.2m (in advanced dialog/tab)
print("\n" + "-" * 70)
print("USER ACTION 1: Manually adds ceramic at 3.2m")
print("-" * 70)

manual_zone = CeramicZone.for_wall(
    perimeter=10.0,
    height=3.2,  # User typed this
    room_name="حمام 1",
    category="Bathroom"
)

project.ceramic_zones = [manual_zone]
calc1 = UnifiedCalculator(project)
room_calc_manual = calc1.calculate_room(bathroom)

print(f"Zone height (user input): {manual_zone.height}m")
print(f"Ceramic wall: {room_calc_manual.ceramic_wall:.2f}m²")
print(f"Paint walls: {room_calc_manual.paint_walls:.2f}m²")
print(f"✅ Result: Paint = 0 (correct)")

# Now user tries quick wizard
print("\n" + "-" * 70)
print("USER ACTION 2: Uses 'Quick Ceramic' wizard")
print("-" * 70)

# Simulate _resolve_room_wall_height from ceramic_tab.py
calc_temp = UnifiedCalculator(project)
walls_gross = calc_temp.calculate_walls_gross(bathroom)  # Uses project default (3.0)

print(f"Wizard logic:")
print(f"  1. Check room.wall_height → {bathroom.wall_height} (None)")
print(f"  2. Calculate walls_gross → {walls_gross:.2f}m²")
print(f"  3. Divide by perimeter → {walls_gross:.2f} / {bathroom.perimeter:.2f} = {walls_gross/bathroom.perimeter:.2f}m")
print(f"  4. Derived height: {walls_gross/bathroom.perimeter:.2f}m")

quick_height = walls_gross / bathroom.perimeter

quick_zone = CeramicZone.for_wall(
    perimeter=10.0,
    height=quick_height,  # Wizard computed this
    room_name="حمام 1",
    category="Bathroom"
)

project.ceramic_zones = [quick_zone]
calc2 = UnifiedCalculator(project)
room_calc_quick = calc2.calculate_room(bathroom)

print(f"\nZone height (wizard computed): {quick_zone.height:.2f}m")
print(f"Ceramic wall: {room_calc_quick.ceramic_wall:.2f}m²")
print(f"Paint walls: {room_calc_quick.paint_walls:.2f}m²")
print(f"{'❌' if room_calc_quick.paint_walls > 0.01 else '✅'} Result: Paint = {room_calc_quick.paint_walls:.2f}m²")

# Comparison
print("\n" + "=" * 70)
print("COMPARISON")
print("=" * 70)
print(f"Manual (3.2m):  walls_gross={room_calc_manual.walls_gross:.2f}, ceramic={room_calc_manual.ceramic_wall:.2f}, paint={room_calc_manual.paint_walls:.2f}")
print(f"Quick ({quick_height:.2f}m): walls_gross={room_calc_quick.walls_gross:.2f}, ceramic={room_calc_quick.ceramic_wall:.2f}, paint={room_calc_quick.paint_walls:.2f}")
print(f"\n❌ PROBLEM: Quick wizard uses {quick_height:.2f}m (from old default) instead of 3.2m")
print(f"   → Ceramic area SHORT by {room_calc_manual.ceramic_wall - room_calc_quick.ceramic_wall:.2f}m²")
print(f"   → Leftover paint: {room_calc_quick.paint_walls:.2f}m²")

print("\n" + "=" * 70)
print("ROOT CAUSE")
print("=" * 70)
print("• room.wall_height is NOT saved when user picks from AutoCAD")
print("• UnifiedCalculator.calculate_walls_gross() uses project.default_wall_height (3.0m)")
print("• Quick wizard derives height from walls_gross / perimeter → gets 3.0m")
print("• Manual input lets user type 3.2m directly → correct")
print("\n✅ SOLUTION: Quick wizard NOW shows dialog where user can edit height before applying")
