import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to the path to allow importing bilind_main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bilind_main import BilindEnhanced
from bilind.calculations.helpers import build_opening_record, format_number


def test_room_metrics_ceramic_cache_invalidation():
    """Editing a ceramic zone in-place should change computed ceramic totals."""
    from bilind.calculations.room_metrics import RoomMetrics
    from bilind.models.project import Project
    from bilind.models.finish import CeramicZone

    project = Project(project_name="P")
    project.rooms = [
        {
            'name': 'R1',
            'perim': 10.0,
            'area': 10.0,
            'wall_height': 3.0,
            'opening_ids': [],
        }
    ]

    zone = CeramicZone.for_wall(perimeter=10.0, height=1.0, room_name='R1')
    zone.effective_area = 9.0
    project.ceramic_zones = [zone]

    m1 = RoomMetrics(project.rooms[0], project).compute_metrics()
    assert m1['cer_wall'] == pytest.approx(9.0)

    # Edit in-place: same list length, different effective_area
    project.ceramic_zones[0].effective_area = 7.5
    m2 = RoomMetrics(project.rooms[0], project).compute_metrics()
    assert m2['cer_wall'] == pytest.approx(7.5)


def test_room_metrics_uses_wall_based_ceramic_when_no_zones():
    """If no ceramic zones exist, wall-level ceramic should still count."""
    from bilind.calculations.room_metrics import RoomMetrics
    from bilind.models.project import Project

    project = Project(project_name="P")
    project.ceramic_zones = []
    project.rooms = [
        {
            'name': 'R1',
            'perim': 10.0,
            'area': 10.0,
            'wall_height': 3.0,
            'opening_ids': [],
            'walls': [
                {'name': 'W1', 'length': 5.0, 'height': 3.0, 'ceramic_area': 2.0},
                {'name': 'W2', 'length': 5.0, 'height': 3.0, 'ceramic_area': 3.25},
            ],
        }
    ]

    metrics = RoomMetrics(project.rooms[0], project).compute_metrics()
    assert metrics['cer_wall'] == pytest.approx(5.25)

@pytest.fixture
def app_instance():
    """
    Provides a mocked instance of the BilindEnhanced app,
    bypassing the AutoCAD connection and UI initialization.
    """
    # Patch the AutoCAD connection and the UI creation to avoid side effects
    with patch('bilind_main.Autocad') as mock_autocad, \
         patch('bilind_main.BilindEnhanced.create_ui') as mock_create_ui, \
         patch('bilind_main.BilindEnhanced.create_menu') as mock_create_menu, \
         patch('tkinter.messagebox') as mock_messagebox:

        # Mock the root Tkinter window with required attributes
        root = MagicMock(spec=tk.Tk)
        root.tk = MagicMock()
        root.configure = MagicMock()
        root.title = MagicMock()
        root.geometry = MagicMock()

        # The __init__ will run, but Autocad() will be a mock, and create_ui will do nothing
        app = BilindEnhanced(root)        # Manually add attributes that would have been created in the real create_ui
        app.status_var = MagicMock()

        return app

def test_build_opening_record_door(app_instance):
    """
    Tests the calculation logic for a single door record.
    """
    record = app_instance._build_opening_record(
        opening_type='DOOR',
        name='D1',
        type_label='Wood',
        width=0.9,
        height=2.1,
        qty=2,
        weight=25.0,
        layer='A-DOOR'
    )

    assert record['name'] == 'D1'
    assert record['type'] == 'Wood'
    assert record['qty'] == 2
    assert record['layer'] == 'A-DOOR'
    assert record['w'] == 0.9
    assert record['h'] == 2.1
    
    # Test calculated fields
    assert pytest.approx(record['perim_each']) == 2 * (0.9 + 2.1)
    assert pytest.approx(record['area_each']) == 0.9 * 2.1
    assert pytest.approx(record['area']) == (0.9 * 2.1) * 2
    assert pytest.approx(record['stone']) == (2 * (0.9 + 2.1)) * 2
    assert pytest.approx(record['weight_each']) == 25.0
    assert pytest.approx(record['weight']) == 50.0
    assert record['glass'] == 0.0 # Doors should have no glass

def test_build_opening_record_window(app_instance):
    """
    Tests the calculation logic for a single window record.
    """
    record = app_instance._build_opening_record(
        opening_type='WINDOW',
        name='W1',
        type_label='Aluminum',
        width=1.5,
        height=1.2,
        qty=3,
        weight=0, # Weight is ignored for windows
        layer='A-WIND'
    )

    assert record['name'] == 'W1'
    assert record['type'] == 'Aluminum'
    assert record['qty'] == 3
    assert record['w'] == 1.5
    assert record['h'] == 1.2

    # Test calculated fields
    area_each = 1.5 * 1.2
    perim_each = 2 * (1.5 + 1.2)
    assert pytest.approx(record['area']) == area_each * 3
    assert pytest.approx(record['stone']) == perim_each * 3
    assert record['weight'] == 0.0 # Windows should have no weight
    assert pytest.approx(record['glass_each']) == area_each * 0.85
    assert pytest.approx(record['glass']) == (area_each * 0.85) * 3

def test_fmt_helper(app_instance):
    """
    Tests the _fmt helper function for correct formatting and defaults.
    """
    assert app_instance._fmt(123.456) == "123.46"
    assert app_instance._fmt(123.456, digits=3) == "123.456"
    assert app_instance._fmt(123) == "123.00"
    assert app_instance._fmt(None) == "-"
    assert app_instance._fmt("invalid") == "-"
    assert app_instance._fmt(0) == "0.00"


# ============================================================================
# NEW TESTS: Direct testing of imported helper functions (no mocking needed)
# ============================================================================

def test_format_number_standalone():
    """Test the standalone format_number function."""
    assert format_number(123.456) == "123.46"
    assert format_number(123.456, digits=3) == "123.456"
    assert format_number(123) == "123.00"
    assert format_number(None) == "-"
    assert format_number("invalid") == "-"
    assert format_number(0) == "0.00"
    assert format_number(0.001, digits=4) == "0.0010"


def test_build_opening_record_door_standalone():
    """Test door record creation with standalone function."""
    record = build_opening_record(
        opening_type='DOOR',
        name='D1',
        type_label='Wood',
        width=0.9,
        height=2.1,
        qty=2,
        weight=25.0,
        layer='A-DOOR'
    )
    
    assert record['name'] == 'D1'
    assert record['type'] == 'Wood'
    assert record['qty'] == 2
    assert record['layer'] == 'A-DOOR'
    assert record['w'] == 0.9
    assert record['h'] == 2.1
    
    # Calculated fields
    assert pytest.approx(record['perim_each']) == 6.0
    assert pytest.approx(record['area_each']) == 1.89
    assert pytest.approx(record['area']) == 3.78
    assert pytest.approx(record['stone']) == 12.0
    assert record['weight_each'] == 25.0
    assert record['weight'] == 50.0
    assert record['glass'] == 0.0


def test_build_opening_record_window_standalone():
    """Test window record creation with standalone function."""
    record = build_opening_record(
        opening_type='WINDOW',
        name='W1',
        type_label='Aluminum',
        width=1.5,
        height=1.2,
        qty=3,
        weight=0,
        layer='A-WIND'
    )
    
    assert record['name'] == 'W1'
    assert record['type'] == 'Aluminum'
    assert record['qty'] == 3
    
    # Calculated fields
    area_each = 1.5 * 1.2
    assert pytest.approx(record['area']) == area_each * 3
    assert record['weight'] == 0.0
    assert pytest.approx(record['glass_each']) == area_each * 0.85
    assert pytest.approx(record['glass']) == (area_each * 0.85) * 3


def test_build_opening_record_edge_cases():
    """Test edge cases for opening record creation."""
    # Quantity less than 1 should default to 1
    record = build_opening_record('DOOR', 'D1', 'Wood', 0.9, 2.1, 0)
    assert record['qty'] == 1
    
    # Negative quantity should default to 1
    record = build_opening_record('DOOR', 'D1', 'Wood', 0.9, 2.1, -5)
    assert record['qty'] == 1
    
    # No layer specified should use type_label
    record = build_opening_record('DOOR', 'D1', 'Wood', 0.9, 2.1, 1, layer=None)
    assert record['layer'] == 'Wood'