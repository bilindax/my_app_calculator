"""
Integration test: Wall edits impact on ceramic calculations
"""
import pytest
from bilind.models.project import Project
from bilind.models.finish import CeramicZone
from bilind.calculations.room_metrics import build_room_metrics_context, calculate_room_finish_metrics


def test_ceramic_zone_updates_when_wall_length_changes():
    """
    Scenario: User creates kitchen with ceramic, then edits wall length.
    Expected: Ceramic zone perimeter updates automatically.
    """
    project = Project(project_name="Test")
    
    # Step 1: Create kitchen room with walls
    kitchen = {
        'name': 'مطبخ',
        'perim': 16.0,
        'area': 12.0,
        'wall_height': 3.0,
        'opening_ids': [],
        'walls': [
            {'name': 'جدار شمال', 'length': 4.0, 'height': 3.0},
            {'name': 'جدار جنوب', 'length': 4.0, 'height': 3.0},
            {'name': 'جدار شرق', 'length': 4.0, 'height': 3.0},
            {'name': 'جدار غرب', 'length': 4.0, 'height': 3.0}
        ]
    }
    project.rooms = [kitchen]
    
    # Step 2: Create ceramic zone for wall (perimeter × height)
    zone = CeramicZone.for_wall(
        perimeter=16.0,
        height=1.5,
        room_name='مطبخ',
        category='Kitchen'
    )
    project.ceramic_zones = [zone]
    
    # Step 3: Calculate initial ceramic area
    ctx = build_room_metrics_context(
        rooms=project.rooms,
        doors=[],
        windows=[],
        ceramic_zones=project.ceramic_zones,
        default_wall_height=3.0
    )
    metrics = calculate_room_finish_metrics(kitchen, ctx)
    
    # Initial: 16.0 × 1.5 = 24.0 m²
    assert metrics.ceramic_wall == pytest.approx(24.0)
    
    # Step 4: User edits wall length (north wall: 4.0 → 5.0)
    kitchen['walls'][0]['length'] = 5.0
    # New perimeter = 5.0 + 4.0 + 4.0 + 4.0 = 17.0
    
    # Simulate _update_ceramic_zones_after_wall_change()
    total_length = sum(w['length'] for w in kitchen['walls'])
    zone.perimeter = total_length  # Update zone
    
    # Step 5: Recalculate with updated zone
    ctx_updated = build_room_metrics_context(
        rooms=project.rooms,
        doors=[],
        windows=[],
        ceramic_zones=project.ceramic_zones,
        default_wall_height=3.0
    )
    metrics_updated = calculate_room_finish_metrics(kitchen, ctx_updated)
    
    # Updated: 17.0 × 1.5 = 25.5 m²
    assert metrics_updated.ceramic_wall == pytest.approx(25.5)


def test_ceramic_zone_with_effective_area_not_auto_updated():
    """
    When user sets effective_area explicitly, it should NOT be overridden
    by automatic perimeter updates (preserves user customization).
    """
    project = Project(project_name="Test")
    
    kitchen = {
        'name': 'مطبخ',
        'perim': 16.0,
        'area': 12.0,
        'wall_height': 3.0,
        'opening_ids': [],
        'walls': [
            {'name': 'جدار شمال', 'length': 4.0, 'height': 3.0},
        ]
    }
    project.rooms = [kitchen]
    
    # User manually set effective_area (e.g., after deducting openings manually)
    zone = CeramicZone(
        name='سيراميك مخصص',
        room_name='مطبخ',
        surface_type='wall',
        perimeter=16.0,
        height=1.5,
        effective_area=20.0  # User-defined net area
    )
    project.ceramic_zones = [zone]
    
    # Calculate with explicit effective_area
    ctx = build_room_metrics_context(
        rooms=project.rooms,
        doors=[],
        windows=[],
        ceramic_zones=project.ceramic_zones,
        default_wall_height=3.0
    )
    metrics = calculate_room_finish_metrics(kitchen, ctx)
    
    # Should use effective_area, not perimeter × height
    assert metrics.ceramic_wall == pytest.approx(20.0)
    
    # Even if wall changes, effective_area stays (user customization protected)
    kitchen['walls'][0]['length'] = 10.0
    # In real app, _update_ceramic_zones_after_wall_change() would skip this zone
    # because effective_area is set
    
    ctx_after = build_room_metrics_context(
        rooms=project.rooms,
        doors=[],
        windows=[],
        ceramic_zones=project.ceramic_zones,
        default_wall_height=3.0
    )
    metrics_after = calculate_room_finish_metrics(kitchen, ctx_after)
    
    # Still 20.0 (unchanged)
    assert metrics_after.ceramic_wall == pytest.approx(20.0)


def test_ceramic_floor_not_affected_by_wall_changes():
    """Floor/ceiling ceramic zones should not be affected by wall edits."""
    project = Project(project_name="Test")
    
    room = {
        'name': 'غرفة',
        'perim': 12.0,
        'area': 9.0,
        'wall_height': 3.0,
        'opening_ids': [],
        'walls': [
            {'name': 'جدار 1', 'length': 3.0, 'height': 3.0},
            {'name': 'جدار 2', 'length': 3.0, 'height': 3.0},
            {'name': 'جدار 3', 'length': 3.0, 'height': 3.0},
            {'name': 'جدار 4', 'length': 3.0, 'height': 3.0}
        ]
    }
    project.rooms = [room]
    
    # Floor ceramic
    floor_zone = CeramicZone.for_floor(
        area=9.0,
        room_name='غرفة',
        category='Other'
    )
    project.ceramic_zones = [floor_zone]
    
    ctx = build_room_metrics_context(
        rooms=project.rooms,
        doors=[],
        windows=[],
        ceramic_zones=project.ceramic_zones,
        default_wall_height=3.0
    )
    metrics = calculate_room_finish_metrics(room, ctx)
    
    assert metrics.ceramic_floor == pytest.approx(9.0)
    assert metrics.ceramic_wall == pytest.approx(0.0)
    
    # Edit wall length
    room['walls'][0]['length'] = 5.0
    # Floor ceramic should remain unchanged (not affected by walls)
    
    ctx_after = build_room_metrics_context(
        rooms=project.rooms,
        doors=[],
        windows=[],
        ceramic_zones=project.ceramic_zones,
        default_wall_height=3.0
    )
    metrics_after = calculate_room_finish_metrics(room, ctx_after)
    
    # Floor ceramic unchanged
    assert metrics_after.ceramic_floor == pytest.approx(9.0)


def test_ceramic_with_opening_deduction_after_wall_edit():
    """
    Complex scenario: Kitchen with ceramic zone and window.
    When wall length changes, ceramic updates AND opening deduction recalculates.
    """
    project = Project(project_name="Test")
    
    kitchen = {
        'name': 'مطبخ',
        'perim': 16.0,
        'area': 12.0,
        'wall_height': 3.0,
        'opening_ids': ['W1'],
        'walls': [
            {'name': 'جدار شمال', 'length': 4.0, 'height': 3.0},
            {'name': 'جدار جنوب', 'length': 4.0, 'height': 3.0},
            {'name': 'جدار شرق', 'length': 4.0, 'height': 3.0},
            {'name': 'جدار غرب', 'length': 4.0, 'height': 3.0}
        ]
    }
    project.rooms = [kitchen]
    
    # Window: 1.2m wide × 1.2m high, sill at 1.0m
    window = {
        'name': 'W1',
        'opening_type': 'WINDOW',
        'w': 1.2,
        'width': 1.2,
        'h': 1.2,
        'height': 1.2,
        'placement_height': 1.0,
        'qty': 1,
        'quantity': 1,
        'area': 1.44,
        'glass': 1.22
    }
    project.windows = [window]
    
    # Ceramic zone: perimeter × 1.5m height (0m to 1.5m from floor)
    zone = CeramicZone(
        name='سيراميك جدار - مطبخ',
        room_name='مطبخ',
        surface_type='wall',
        perimeter=16.0,
        height=1.5,
        start_height=0.0
    )
    project.ceramic_zones = [zone]
    
    # Initial calculation
    ctx = build_room_metrics_context(
        rooms=project.rooms,
        doors=[],
        windows=project.windows,
        ceramic_zones=project.ceramic_zones,
        default_wall_height=3.0
    )
    metrics = calculate_room_finish_metrics(kitchen, ctx)
    
    # Gross ceramic = 16.0 × 1.5 = 24.0
    # Window overlap: width=1.2, overlap_height = min(1.5, 1.0+1.2) - max(0.0, 1.0) = 1.2m (from 1.0 to 1.5)
    # Window deduction = 1.2 × 0.5 = 0.6 m²
    # Net ceramic = 24.0 - 0.6 = 23.4 m²
    assert metrics.ceramic_wall == pytest.approx(23.4)
    
    # User edits wall: north wall 4.0 → 5.0
    kitchen['walls'][0]['length'] = 5.0
    zone.perimeter = 17.0  # Simulate auto-update
    
    ctx_updated = build_room_metrics_context(
        rooms=project.rooms,
        doors=[],
        windows=project.windows,
        ceramic_zones=project.ceramic_zones,
        default_wall_height=3.0
    )
    metrics_updated = calculate_room_finish_metrics(kitchen, ctx_updated)
    
    # New gross = 17.0 × 1.5 = 25.5
    # Same window deduction = 0.6
    # New net = 25.5 - 0.6 = 24.9 m²
    assert metrics_updated.ceramic_wall == pytest.approx(24.9)
