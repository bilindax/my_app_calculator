"""
Quick test to verify excel export still works after UnifiedCalculator integration
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from bilind.models.project import Project
from bilind.models.room import Room
from bilind.models.opening import Opening
from bilind.models.finish import CeramicZone
from bilind.export.excel_comprehensive_book import export_comprehensive_book

# Create test project
project = Project(project_name="Test Export")

# Add a simple room
room1 = Room(
    name="غرفة 1",
    layer="ROOMS",
    area=20.0,
    perimeter=18.0,
    wall_height=3.0,
    opening_ids=["باب 1"]
)

# Add a door
door1 = Opening(
    name="باب 1",
    opening_type="DOOR",
    width=1.0,
    height=2.1,
    room_quantities={"غرفة 1": 1}
)

# Add ceramic
ceramic1 = CeramicZone.for_wall(
    perimeter=18.0,
    height=1.5,
    room_name="غرفة 1",
    name="سيراميك غرفة 1"
)

project.rooms.append(room1)
project.doors.append(door1)
project.ceramic_zones.append(ceramic1)

# Try to export
print("🧪 Testing Excel export with UnifiedCalculator...")
try:
    success = export_comprehensive_book(
        project,
        "d:/vscode/test_export.xlsx",
        selected_sheets=['summary', 'rooms']
    )
    
    if success:
        print("✅ Export successful!")
        print("📊 Check file: d:/vscode/test_export.xlsx")
        
        # Check if file exists
        if os.path.exists("d:/vscode/test_export.xlsx"):
            size = os.path.getsize("d:/vscode/test_export.xlsx")
            print(f"✅ File created: {size} bytes")
        else:
            print("❌ File not created!")
    else:
        print("❌ Export returned False")
        
except Exception as e:
    print(f"❌ Error during export: {e}")
    import traceback
    traceback.print_exc()
