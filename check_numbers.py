from bilind.models.project import Project
from bilind.models.room import Room
from bilind.models.opening import Opening
from bilind.models.finish import CeramicZone
from bilind.calculations.unified_calculator import UnifiedCalculator

# Same test project
project = Project(project_name='Test')
room1 = Room(name='غرفة 1', layer='ROOMS', area=20.0, perimeter=18.0, wall_height=3.0, opening_ids=['باب 1'])
door1 = Opening(name='باب 1', opening_type='DOOR', width=1.0, height=2.1, room_quantities={'غرفة 1': 1})
ceramic1 = CeramicZone.for_wall(perimeter=18.0, height=1.5, room_name='غرفة 1', name='سيراميك')

project.rooms.append(room1)
project.doors.append(door1)
project.ceramic_zones.append(ceramic1)

# Calculate with UnifiedCalculator
calc = UnifiedCalculator(project)
room_calc = calc.calculate_room(room1)
totals = calc.calculate_totals()

print('Room Calculations:')
print(f'  Walls Gross: {room_calc.walls_gross:.2f} m²')
print(f'  Walls Net: {room_calc.walls_net:.2f} m²')
print(f'  Plaster Total: {room_calc.plaster_total:.2f} m²')
print(f'  Ceramic Wall: {room_calc.ceramic_wall:.2f} m²')
print(f'  Paint Total: {room_calc.paint_total:.2f} m²')
print()
print('Project Totals:')
print(f'  Plaster: {totals["plaster_total"]:.2f} m²')
print(f'  Paint: {totals["paint_total"]:.2f} m²')
print(f'  Ceramic: {totals["ceramic_total"]:.2f} m²')
