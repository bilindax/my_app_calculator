"""
Unit tests for data models.
"""

import pytest
from bilind.models import Room, Opening, Wall, FinishItem
from bilind.models.finish import CeramicZone


class TestRoom:
    """Tests for Room data model."""
    
    def test_create_simple_room(self):
        """Test creating a simple room."""
        room = Room(
            name="Living Room",
            layer="A-ROOM",
            width=5.0,
            length=4.0,
            perimeter=18.0,
            area=20.0
        )
        assert room.name == "Living Room"
        assert room.area == 20.0
        assert room.perimeter == 18.0
        assert room.opening_ids == []
    
    def test_room_validation(self):
        """Test room validation."""
        with pytest.raises(ValueError, match="area cannot be negative"):
            Room(name="Bad", layer="A", area=-10, perimeter=10)
        
        with pytest.raises(ValueError, match="perimeter cannot be negative"):
            Room(name="Bad", layer="A", area=10, perimeter=-5)
    
    def test_room_to_dict(self):
        """Test room to dictionary conversion."""
        room = Room(
            name="Kitchen",
            layer="A-ROOM",
            width=4.5,
            length=3.5,
            perimeter=16.0,
            area=15.75
        )
        data = room.to_dict()
        assert data['name'] == "Kitchen"
        assert data['w'] == 4.5
        assert data['l'] == 3.5
        assert data['perim'] == 16.0
        assert data['area'] == 15.75
    
    def test_room_from_dict(self):
        """Test creating room from dictionary."""
        data = {
            'name': 'Bedroom',
            'layer': 'A-ROOM',
            'w': 4.0,
            'l': 3.5,
            'perim': 15.0,
            'area': 14.0
        }
        room = Room.from_dict(data)
        assert room.name == "Bedroom"
        assert room.width == 4.0
        assert room.length == 3.5
        assert room.area == 14.0
    
    def test_calculate_wall_area(self):
        """Test wall area calculation."""
        room = Room(name="Room1", layer="A", area=20, perimeter=18)
        wall_area = room.calculate_wall_area(height=3.0)
        assert wall_area == 54.0  # 18 * 3
    
    def test_room_with_openings(self):
        """Test room with assigned openings."""
        room = Room(
            name="Living",
            layer="A-ROOM",
            area=25.0,
            perimeter=20.0,
            opening_ids=["D1", "W1", "W2"]
        )
        assert len(room.opening_ids) == 3
        assert "D1" in room.opening_ids


class TestOpening:
    """Tests for Opening data model."""
    
    def test_create_door(self):
        """Test creating a door."""
        door = Opening(
            name="D1",
            opening_type="DOOR",
            material_type="Wood",
            layer="A-DOOR",
            width=0.9,
            height=2.1,
            quantity=2
        )
        assert door.name == "D1"
        assert door.opening_type == "DOOR"
        assert door.quantity == 2
        assert door.area_each == pytest.approx(1.89)
        assert door.area == pytest.approx(3.78)
    
    def test_create_window(self):
        """Test creating a window."""
        window = Opening(
            name="W1",
            opening_type="WINDOW",
            material_type="Aluminum",
            layer="A-WINDOW",
            width=1.5,
            height=1.2,
            quantity=3
        )
        assert window.name == "W1"
        assert window.opening_type == "WINDOW"
        assert window.area_each == pytest.approx(1.8)
        assert window.area == pytest.approx(5.4)
    
    def test_opening_validation(self):
        """Test opening validation."""
        with pytest.raises(ValueError, match="width must be positive"):
            Opening(name="Bad", opening_type="DOOR", material_type="Wood", 
                   layer="A", width=-1, height=2)
        
        with pytest.raises(ValueError, match="quantity must be at least 1"):
            Opening(name="Bad", opening_type="DOOR", material_type="Wood",
                   layer="A", width=1, height=2, quantity=0)
    
    def test_door_perimeter(self):
        """Test door perimeter calculation."""
        door = Opening(
            name="D1",
            opening_type="DOOR",
            material_type="Wood",
            layer="A-DOOR",
            width=0.9,
            height=2.1,
            quantity=2
        )
        # Perimeter each = 2 * (0.9 + 2.1) = 6.0
        assert door.perimeter_each == pytest.approx(6.0)
        # Total = 6.0 * 2 = 12.0
        assert door.perimeter == pytest.approx(12.0)
        assert door.stone_linear == pytest.approx(12.0)
    
    def test_window_glass_area(self):
        """Test window glass area calculation."""
        window = Opening(
            name="W1",
            opening_type="WINDOW",
            material_type="Aluminum",
            layer="A-WINDOW",
            width=1.5,
            height=1.2,
            quantity=2
        )
        # Area = 1.5 * 1.2 = 1.8, total = 3.6
        # Glass = 3.6 * 0.85 = 3.06
        glass = window.calculate_glass_area()
        assert glass == pytest.approx(3.06)
    
    def test_opening_to_dict_door(self):
        """Test door to dictionary conversion."""
        door = Opening(
            name="D1",
            opening_type="DOOR",
            material_type="Steel",
            layer="A-DOOR",
            width=1.0,
            height=2.2,
            quantity=1
        )
        data = door.to_dict(weight=50.0)
        assert data['name'] == "D1"
        assert data['type'] == "Steel"
        assert data['w'] == 1.0
        assert data['h'] == 2.2
        assert data['qty'] == 1
        assert data['weight_each'] == 50.0
        assert data['weight'] == 50.0
        assert data['glass'] == 0.0
    
    def test_opening_to_dict_window(self):
        """Test window to dictionary conversion."""
        window = Opening(
            name="W1",
            opening_type="WINDOW",
            material_type="PVC",
            layer="A-WINDOW",
            width=1.2,
            height=1.5,
            quantity=2
        )
        data = window.to_dict()
        assert data['name'] == "W1"
        assert data['glass'] > 0  # Should have glass area
        assert data['weight'] == 0.0  # Windows have no weight


class TestWall:
    """Tests for Wall data model."""
    
    def test_create_wall(self):
        """Test creating a wall."""
        wall = Wall(
            name="Wall1",
            layer="A-WALL",
            length=5.0,
            height=3.0
        )
        assert wall.name == "Wall1"
        assert wall.gross_area == 15.0
        assert wall.net_area == 15.0
        assert wall.deduction_area == 0.0
    
    def test_wall_validation(self):
        """Test wall validation."""
        with pytest.raises(ValueError, match="length must be positive"):
            Wall(name="Bad", layer="A", length=-5, height=3)
        
        with pytest.raises(ValueError, match="height must be positive"):
            Wall(name="Bad", layer="A", length=5, height=0)
    
    def test_wall_with_deduction(self):
        """Test wall with opening deduction."""
        wall = Wall(
            name="Wall1",
            layer="A-WALL",
            length=6.0,
            height=3.0
        )
        # Gross = 18.0
        assert wall.gross_area == 18.0
        
        # Add door deduction (0.9 × 2.1 = 1.89)
        wall.add_deduction(1.89)
        assert wall.deduction_area == pytest.approx(1.89)
        assert wall.net_area == pytest.approx(16.11)
        
        # Add window deduction
        wall.add_deduction(1.8)
        assert wall.deduction_area == pytest.approx(3.69)
        assert wall.net_area == pytest.approx(14.31)
    
    def test_wall_reset_deductions(self):
        """Test resetting wall deductions."""
        wall = Wall(name="Wall1", layer="A", length=5, height=3)
        wall.add_deduction(2.0)
        assert wall.net_area == 13.0
        
        wall.reset_deductions()
        assert wall.deduction_area == 0.0
        assert wall.net_area == 15.0
    
    def test_wall_calculate_volume(self):
        """Test wall volume calculation."""
        wall = Wall(name="Wall1", layer="A", length=5, height=3)
        volume = wall.calculate_volume(thickness=0.2)
        assert volume == pytest.approx(3.0)  # 15 * 0.2
    
    def test_wall_deduction_percentage(self):
        """Test deduction percentage calculation."""
        wall = Wall(name="Wall1", layer="A", length=10, height=3)
        # Gross = 30
        wall.add_deduction(6.0)
        assert wall.deduction_percentage == pytest.approx(20.0)
    
    def test_wall_to_dict(self):
        """Test wall to dictionary conversion."""
        wall = Wall(
            name="North Wall",
            layer="A-WALL",
            length=8.0,
            height=3.0
        )
        wall.add_deduction(3.5)
        
        data = wall.to_dict()
        assert data['name'] == "North Wall"
        assert data['length'] == 8.0
        assert data['height'] == 3.0
        assert data['gross'] == 24.0
        assert data['deduct'] == 3.5
        assert data['net'] == 20.5


class TestFinishItem:
    """Tests for FinishItem data model."""
    
    def test_create_finish_item(self):
        """Test creating a finish item."""
        item = FinishItem(
            description="Living Room Floor",
            area=25.5,
            finish_type="tiles"
        )
        assert item.description == "Living Room Floor"
        assert item.area == 25.5
        assert item.finish_type == "tiles"
        assert not item.is_deduction
    
    def test_finish_item_deduction(self):
        """Test finish item deduction."""
        item = FinishItem(
            description="Deduction: Ceramic zones",
            area=-5.5,
            finish_type="plaster"
        )
        assert item.is_deduction
        assert item.absolute_area == 5.5
    
    def test_finish_item_validation(self):
        """Test finish item validation."""
        with pytest.raises(ValueError, match="Invalid finish type"):
            FinishItem(description="Bad", area=10, finish_type="invalid")
    
    def test_finish_item_to_dict(self):
        """Test finish item to dictionary conversion."""
        item = FinishItem(
            description="Wall Plaster",
            area=48.5,
            finish_type="plaster"
        )
        data = item.to_dict()
        assert data['desc'] == "Wall Plaster"
        assert data['area'] == 48.5
    
    def test_finish_item_from_dict(self):
        """Test creating finish item from dictionary."""
        data = {'desc': 'Paint Area', 'area': 120.0}
        item = FinishItem.from_dict(data, finish_type="paint")
        assert item.description == "Paint Area"
        assert item.area == 120.0
        assert item.finish_type == "paint"


class TestCeramicZone:
    """Tests for CeramicZone data model."""
    
    def test_create_ceramic_zone(self):
        """Test creating a ceramic zone."""
        zone = CeramicZone(
            name="Kitchen Backsplash",
            category="Kitchen",
            perimeter=8.0,
            height=0.6,
            notes="Above counter"
        )
        assert zone.name == "Kitchen Backsplash"
        assert zone.category == "Kitchen"
        assert zone.area == pytest.approx(4.8)  # 8.0 * 0.6
    
    def test_ceramic_zone_validation(self):
        """Test ceramic zone validation."""
        with pytest.raises(ValueError, match="Perimeter must be positive"):
            CeramicZone(name="Bad", category="Kitchen", perimeter=-5, height=1)
        
        with pytest.raises(ValueError, match="Height must be positive"):
            CeramicZone(name="Bad", category="Bathroom", perimeter=5, height=0)
    
    def test_ceramic_zone_to_dict(self):
        """Test ceramic zone to dictionary conversion."""
        zone = CeramicZone(
            name="Bathroom Walls",
            category="Bathroom",
            perimeter=12.0,
            height=2.2
        )
        data = zone.to_dict()
        assert data['name'] == "Bathroom Walls"
        assert data['category'] == "Bathroom"
        assert data['perimeter'] == 12.0
        assert data['height'] == 2.2
        assert data['area'] == pytest.approx(26.4)


class TestRoundTripConversion:
    """Test round-trip conversions between models and dictionaries."""
    
    def test_room_round_trip(self):
        """Test room to_dict and from_dict."""
        original = Room(
            name="Test Room",
            layer="A-ROOM",
            width=4.0,
            length=5.0,
            perimeter=18.0,
            area=20.0,
            opening_ids=["D1", "W1"]
        )
        data = original.to_dict()
        restored = Room.from_dict(data)
        
        assert restored.name == original.name
        assert restored.width == original.width
        assert restored.area == original.area
        assert restored.opening_ids == original.opening_ids
    
    def test_wall_round_trip(self):
        """Test wall to_dict and from_dict."""
        original = Wall(
            name="Test Wall",
            layer="A-WALL",
            length=6.0,
            height=3.0
        )
        original.add_deduction(2.5)
        
        data = original.to_dict()
        restored = Wall.from_dict(data)
        
        assert restored.name == original.name
        assert restored.length == original.length
        assert restored.height == original.height
        assert restored.gross_area == pytest.approx(original.gross_area)
        assert restored.deduction_area == pytest.approx(original.deduction_area)
        assert restored.net_area == pytest.approx(original.net_area)
