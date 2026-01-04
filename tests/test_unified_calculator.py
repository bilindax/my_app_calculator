"""
Tests for UnifiedCalculator
============================
اختبارات للتأكد من صحة الحسابات الموحدة.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bilind.calculations.unified_calculator import UnifiedCalculator, RoomCalculations
from bilind.models.project import Project
from bilind.models.room import Room
from bilind.models.opening import Opening
from bilind.models.finish import CeramicZone


def test_walls_gross_with_walls_objects():
    """Test: حساب مساحة الجدران من walls objects"""
    project = Project(project_name="Test")
    
    room = Room(
        name="غرفة 1",
        layer="ROOMS",
        area=20.0,
        perimeter=18.0,
        wall_height=3.0,
        walls=[
            type('Wall', (), {'length': 5.0, 'height': 3.0})(),
            type('Wall', (), {'length': 4.0, 'height': 3.0})(),
            type('Wall', (), {'length': 5.0, 'height': 3.0})(),
            type('Wall', (), {'length': 4.0, 'height': 3.0})(),
        ]
    )
    project.rooms.append(room)
    
    calc = UnifiedCalculator(project)
    walls_gross = calc.calculate_walls_gross(room)
    
    # Expected: (5+4+5+4) × 3 = 54
    assert walls_gross == 54.0, f"Expected 54.0, got {walls_gross}"
    print("✅ test_walls_gross_with_walls_objects passed")


def test_walls_gross_without_walls_objects():
    """Test: حساب مساحة الجدران من perimeter × height"""
    project = Project(project_name="Test")
    
    room = Room(name="غرفة 1", layer="ROOMS", area=20.0,
        perimeter=18.0,
        wall_height=3.0,
        walls=[]
    )
    project.rooms.append(room)
    
    calc = UnifiedCalculator(project)
    walls_gross = calc.calculate_walls_gross(room)
    
    # Expected: 18 × 3 = 54
    assert walls_gross == 54.0, f"Expected 54.0, got {walls_gross}"
    print("✅ test_walls_gross_without_walls_objects passed")


def test_openings_deduction():
    """Test: حساب خصومات الفتحات"""
    project = Project(project_name="Test")
    
    room = Room(name="غرفة 1", layer="ROOMS", area=20.0,
        perimeter=18.0,
        wall_height=3.0,
        opening_ids=["باب 1", "شباك 1"]
    )
    
    door = Opening(
        name="باب 1",
        opening_type="DOOR",
        width=1.0,
        height=2.1,
        room_quantities={"غرفة 1": 1}
    )
    
    window = Opening(
        name="شباك 1",
        opening_type="WINDOW",
        width=1.5,
        height=1.2,
        room_quantities={"غرفة 1": 2}
    )
    
    project.rooms.append(room)
    project.doors.append(door)
    project.windows.append(window)
    
    calc = UnifiedCalculator(project)
    openings = calc.calculate_openings_deduction(room)
    
    # Expected: (1.0 × 2.1 × 1) + (1.5 × 1.2 × 2) = 2.1 + 3.6 = 5.7
    assert abs(openings - 5.7) < 0.01, f"Expected 5.7, got {openings}"
    print("✅ test_openings_deduction passed")


def test_plaster_calculation():
    """Test: حساب المحارة (لا يُخصم السيراميك)"""
    project = Project(project_name="Test")
    
    room = Room(name="غرفة 1", layer="ROOMS", area=20.0,
        perimeter=18.0,
        wall_height=3.0,
        opening_ids=["باب 1"]
    )
    
    door = Opening(
        name="باب 1",
        opening_type="DOOR",
        width=1.0,
        height=2.0,
        room_quantities={"غرفة 1": 1}
    )
    
    project.rooms.append(room)
    project.doors.append(door)
    
    calc = UnifiedCalculator(project)
    plaster = calc.calculate_plaster(room)
    
    # Expected walls_net: (18 × 3) - (1 × 2) = 54 - 2 = 52
    # Expected ceiling: 20
    # Expected total: 52 + 20 = 72
    assert abs(plaster['walls_net'] - 52.0) < 0.01, f"Expected walls_net 52.0, got {plaster['walls_net']}"
    assert plaster['ceiling'] == 20.0, f"Expected ceiling 20.0, got {plaster['ceiling']}"
    assert abs(plaster['total'] - 72.0) < 0.01, f"Expected total 72.0, got {plaster['total']}"
    print("✅ test_plaster_calculation passed")


def test_paint_with_ceramic():
    """Test: حساب الدهان (يُخصم السيراميك من المحارة)"""
    project = Project(project_name="Test")
    
    room = Room(name="غرفة 1", layer="ROOMS", area=20.0,
        perimeter=18.0,
        wall_height=3.0,
        opening_ids=[]
    )
    
    # Ceramic zone on walls
    ceramic_wall = CeramicZone.for_wall(
        perimeter=18.0,
        height=1.5,
        room_name="غرفة 1",
        name="سيراميك جدران"
    )
    
    # Ceramic zone on ceiling
    ceramic_ceiling = CeramicZone.for_floor(
        area=5.0,
        room_name="غرفة 1",
        name="سيراميك سقف"
    )
    ceramic_ceiling.surface_type = 'ceiling'
    
    project.rooms.append(room)
    project.ceramic_zones.append(ceramic_wall)
    project.ceramic_zones.append(ceramic_ceiling)
    
    calc = UnifiedCalculator(project)
    paint = calc.calculate_paint(room)
    
    # Plaster: walls_net = 54, ceiling = 20
    # Ceramic: walls = 27, ceiling = 5
    # Paint: walls = 54 - 27 = 27, ceiling = 20 - 5 = 15, total = 42
    assert abs(paint['walls'] - 27.0) < 0.01, f"Expected walls 27.0, got {paint['walls']}"
    assert abs(paint['ceiling'] - 15.0) < 0.01, f"Expected ceiling 15.0, got {paint['ceiling']}"
    assert abs(paint['total'] - 42.0) < 0.01, f"Expected total 42.0, got {paint['total']}"
    print("✅ test_paint_with_ceramic passed")


def test_baseboard_calculation():
    """Test: حساب النعلات (perimeter - door widths)"""
    project = Project(project_name="Test")
    
    room = Room(name="غرفة 1", layer="ROOMS", area=20.0,
        perimeter=18.0,
        wall_height=3.0,
        opening_ids=["باب 1", "باب 2"]
    )
    
    door1 = Opening(
        name="باب 1",
        opening_type="DOOR",
        width=1.0,
        height=2.1,
        room_quantities={"غرفة 1": 1}
    )
    
    door2 = Opening(
        name="باب 2",
        opening_type="DOOR",
        width=0.9,
        height=2.1,
        room_quantities={"غرفة 1": 1}
    )
    
    project.rooms.append(room)
    project.doors.append(door1)
    project.doors.append(door2)
    
    calc = UnifiedCalculator(project)
    baseboard = calc.calculate_baseboard(room)
    
    # Expected: 18 - 1.0 - 0.9 = 16.1
    assert abs(baseboard - 16.1) < 0.01, f"Expected 16.1, got {baseboard}"
    print("✅ test_baseboard_calculation passed")


def test_calculate_room_full():
    """Test: حساب كامل لغرفة واحدة"""
    project = Project(project_name="Test")
    
    room = Room(name="غرفة 1", layer="ROOMS", area=20.0,
        perimeter=18.0,
        wall_height=3.0,
        opening_ids=["باب 1"]
    )
    
    door = Opening(
        name="باب 1",
        opening_type="DOOR",
        width=1.0,
        height=2.0,
        room_quantities={"غرفة 1": 1}
    )
    
    ceramic = CeramicZone.for_wall(
        perimeter=18.0,
        height=1.0,
        room_name="غرفة 1",
        name="سيراميك"
    )
    
    project.rooms.append(room)
    project.doors.append(door)
    project.ceramic_zones.append(ceramic)
    
    calc = UnifiedCalculator(project)
    result = calc.calculate_room(room)
    
    # Verify all fields exist
    assert result.room_name == "غرفة 1"
    assert result.walls_gross == 54.0
    assert result.walls_openings == 2.0
    assert result.walls_net == 52.0
    assert result.ceiling_area == 20.0
    
    # Ceramic: 18*1 - 1*1 (door overlap) = 17.0
    assert result.ceramic_wall == 17.0
    
    # Plaster: Net Walls (52) + Ceiling (20) = 72
    assert result.plaster_total == 72.0
    
    # Paint: (Net Walls - Ceramic) + Ceiling
    # (52 - 17) + 20 = 35 + 20 = 55
    assert abs(result.paint_total - 55.0) < 0.01
    
    # Stone: Door 1x2 -> 2h+w = 4+1 = 5
    assert result.stone_length == 5.0
    
    print("✅ test_calculate_room_full passed")


def test_calculate_totals():
    """Test: حساب إجماليات المشروع"""
    project = Project(project_name="Test")
    
    # Room 1
    room1 = Room(
        name="غرفة 1",
        layer="ROOMS",
        area=20.0,
        perimeter=18.0,
        wall_height=3.0,
        opening_ids=[]
    )
    
    # Room 2
    room2 = Room(
        name="غرفة 2",
        layer="ROOMS",
        area=15.0,
        perimeter=16.0,
        wall_height=3.0,
        opening_ids=[]
    )
    
    project.rooms.append(room1)
    project.rooms.append(room2)
    
    calc = UnifiedCalculator(project)
    totals = calc.calculate_totals()
    
    # Room1: plaster = 54 + 20 = 74
    # Room2: plaster = 48 + 15 = 63
    # Total: 137
    assert abs(totals['plaster_total'] - 137.0) < 0.01, f"Expected plaster 137.0, got {totals['plaster_total']}"
    
    print("✅ test_calculate_totals passed")


if __name__ == "__main__":
    print("🧪 Running UnifiedCalculator Tests...\n")
    
    try:
        test_walls_gross_with_walls_objects()
        test_walls_gross_without_walls_objects()
        test_openings_deduction()
        test_plaster_calculation()
        test_paint_with_ceramic()
        test_baseboard_calculation()
        test_calculate_room_full()
        test_calculate_totals()
        
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
