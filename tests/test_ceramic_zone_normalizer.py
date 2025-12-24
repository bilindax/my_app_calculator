from bilind.calculations.ceramic_zone_normalizer import normalize_ceramic_wall_zones
from bilind.models.project import Project
from bilind.models.room import Room
from bilind.models.wall import Wall
from bilind.models.finish import CeramicZone


def test_normalize_per_wall_zone_perimeter_from_wall_name():
    project = Project()
    room = Room(name="بلكون 2", layer="", area=0.0, perimeter=15.7)
    room.walls = [
        Wall(name="Wall 1", layer="", length=6.6, height=3.0),
        Wall(name="Wall 3", layer="", length=7.6, height=0.8),
        Wall(name="Wall 4", layer="", length=1.5, height=1.5),
    ]
    project.rooms.append(room)

    # Buggy state: Wall 4 zone got overwritten with total length 15.7
    zone = CeramicZone(
        name="سيراميك - بلكون 2 - جدار 4",
        category="Other",
        perimeter=15.7,
        height=1.5,
        surface_type="wall",
        room_name="بلكون 2",
        wall_name="Wall 4",
    )
    project.ceramic_zones.append(zone)

    updated, skipped = normalize_ceramic_wall_zones(project)

    assert updated == 1
    assert skipped == 0
    assert abs(zone.perimeter - 1.5) < 1e-9
    assert abs(zone.area - (1.5 * 1.5)) < 1e-9


def test_normalize_dict_zone_updates_area_adhesive_grout_when_effective_area_missing():
    project = Project()
    room = Room(name="بلكون 2", layer="", area=0.0, perimeter=15.7)
    room.walls = [Wall(name="Wall 4", layer="", length=1.5, height=1.5)]
    project.rooms.append(room)

    zone_dict = {
        "name": "سيراميك - بلكون 2 - جدار 4",
        "category": "Other",
        "perimeter": 15.7,
        "height": 1.5,
        "surface_type": "wall",
        "room_name": "بلكون 2",
        "wall_name": "Wall 4",
        "effective_area": None,
        "area": 20.5,
        "adhesive_kg": 61.5,
        "grout_kg": 10.25,
    }
    project.ceramic_zones.append(zone_dict)

    updated, skipped = normalize_ceramic_wall_zones(project)

    assert updated == 1
    assert skipped == 0
    assert abs(zone_dict["perimeter"] - 1.5) < 1e-9
    assert abs(zone_dict["area"] - 2.25) < 1e-9
    assert abs(zone_dict["adhesive_kg"] - (2.25 * 3.0)) < 1e-9
    assert abs(zone_dict["grout_kg"] - (2.25 * 0.5)) < 1e-9
