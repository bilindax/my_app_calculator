"""
Test Excel Export
=================
Tests for the Excel export functionality.
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bilind.export.excel_comprehensive_book import export_comprehensive_book
from bilind.models.project import Project
from bilind.models.room import Room
from bilind.models.opening import Opening
from bilind.models.finish import CeramicZone

def test_export_comprehensive_book():
    """Test: تصدير ملف Excel شامل"""
    project = Project(project_name="Test Project")
    
    # Create a room
    room = Room(name="غرفة 1", layer="ROOMS", area=20.0,
        perimeter=18.0,
        wall_height=3.0,
        opening_ids=["باب 1"]
    )
    
    # Create a door
    door = Opening(
        name="باب 1",
        opening_type="DOOR",
        width=1.0,
        height=2.0,
        room_quantities={"غرفة 1": 1}
    )
    
    # Create ceramic zone
    ceramic = CeramicZone.for_wall(
        perimeter=18.0,
        height=1.0,
        room_name="غرفة 1",
        name="سيراميك"
    )
    
    project.rooms.append(room)
    project.doors.append(door)
    project.ceramic_zones.append(ceramic)
    
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        filepath = tmp.name
    
    try:
        # Run export
        success = export_comprehensive_book(project, filepath)
        assert success, "Export failed"
        assert os.path.exists(filepath), "File not created"
        print(f"✅ Export successful: {filepath}")
        
    finally:
        # Cleanup
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass

if __name__ == "__main__":
    test_export_comprehensive_book()
