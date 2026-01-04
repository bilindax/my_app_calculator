"""
Ceramic Height Debugging Tool
==============================
يفحص ارتفاعات السيراميك المخزنة في المشروع الحالي
"""

def check_ceramic_zones_heights(project_file='project.pkl'):
    import pickle
    import os
    
    if not os.path.exists(project_file):
        print(f"❌ الملف {project_file} غير موجود")
        return
    
    with open(project_file, 'rb') as f:
        project = pickle.load(f)
    
    print("="*60)
    print("🔍 CERAMIC ZONES HEIGHT DEBUG REPORT")
    print("="*60)
    
    ceramic_zones = getattr(project, 'ceramic_zones', [])
    
    if not ceramic_zones:
        print("\n❌ لا توجد مناطق سيراميك في المشروع")
        return
    
    print(f"\n📊 عدد المناطق: {len(ceramic_zones)}")
    print("\n" + "="*60)
    
    # Group by room
    by_room = {}
    for zone in ceramic_zones:
        if isinstance(zone, dict):
            room = zone.get('room_name', 'Unknown')
            name = zone.get('name', 'Unnamed')
            perim = zone.get('perimeter', 0)
            height = zone.get('height', 0)
            stype = zone.get('surface_type', 'wall')
        else:
            room = getattr(zone, 'room_name', 'Unknown')
            name = getattr(zone, 'name', 'Unnamed')
            perim = getattr(zone, 'perimeter', 0)
            height = getattr(zone, 'height', 0)
            stype = getattr(zone, 'surface_type', 'wall')
        
        if room not in by_room:
            by_room[room] = []
        
        area = perim * height
        by_room[room].append({
            'name': name,
            'perimeter': perim,
            'height': height,
            'surface_type': stype,
            'area': area
        })
    
    # Print by room
    for room_name, zones in sorted(by_room.items()):
        print(f"\n🏠 {room_name}")
        print("-" * 60)
        
        total_wall = 0
        total_floor = 0
        
        for z in zones:
            area = z['area']
            if z['surface_type'] == 'wall':
                total_wall += area
                status = "✅" if z['height'] >= 1.4 else "⚠️" if z['height'] >= 0.9 else "❌"
            else:
                total_floor += area
                status = "✅"
            
            print(f"  {status} {z['name']}")
            print(f"      محيط: {z['perimeter']:.2f} م | ارتفاع: {z['height']:.2f} م | نوع: {z['surface_type']}")
            print(f"      المساحة: {area:.2f} م²")
        
        print(f"\n  📊 الإجمالي:")
        if total_wall > 0:
            print(f"      جدران: {total_wall:.2f} م²")
        if total_floor > 0:
            print(f"      أرضيات: {total_floor:.2f} م²")
    
    print("\n" + "="*60)
    print("🔑 مفتاح الحالات:")
    print("   ✅ ارتفاع صحيح (≥ 1.4م)")
    print("   ⚠️  ارتفاع منخفض (0.9-1.4م)")
    print("   ❌ ارتفاع خاطئ (< 0.9م)")
    print("="*60)

if __name__ == '__main__':
    import sys
    file = sys.argv[1] if len(sys.argv) > 1 else 'project.pkl'
    check_ceramic_zones_heights(file)
