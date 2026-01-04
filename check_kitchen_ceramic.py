"""
Kitchen Ceramic Debug - فحص سيراميك المطبخ
==========================================
"""
import sys
import pickle
from pathlib import Path

def check_kitchen():
    # Find project file
    project_files = list(Path('.').glob('*.pkl'))
    if not project_files:
        print("❌ لا يوجد ملف مشروع (.pkl)")
        return
    
    project_file = project_files[0]
    print(f"📂 فتح الملف: {project_file}")
    
    with open(project_file, 'rb') as f:
        project = pickle.load(f)
    
    # Find kitchen room
    kitchen = None
    for room in project.rooms:
        name = room.name if hasattr(room, 'name') else room.get('name', '')
        if 'مطبخ' in name.lower() or 'kitchen' in name.lower():
            kitchen = room
            break
    
    if not kitchen:
        print("❌ لم يتم العثور على غرفة المطبخ")
        return
    
    room_name = kitchen.name if hasattr(kitchen, 'name') else kitchen.get('name', '')
    perim = kitchen.perimeter if hasattr(kitchen, 'perimeter') else kitchen.get('perimeter', 0)
    
    print(f"\n🏠 الغرفة: {room_name}")
    print(f"📏 المحيط: {perim:.2f} م")
    
    # Check walls
    walls = kitchen.walls if hasattr(kitchen, 'walls') else kitchen.get('walls', [])
    print(f"\n🧱 الجدران ({len(walls)}):")
    for i, wall in enumerate(walls, 1):
        w_len = wall.length if hasattr(wall, 'length') else wall.get('length', 0)
        w_h = wall.height if hasattr(wall, 'height') else wall.get('height', 0)
        w_name = wall.name if hasattr(wall, 'name') else wall.get('name', f'Wall {i}')
        print(f"  {i}. {w_name}: طول={w_len:.2f}م، ارتفاع={w_h:.2f}م")
    
    # Check ceramic zones for this room
    print(f"\n🧱 مناطق السيراميك:")
    total_ceramic = 0
    found_zones = 0
    
    for zone in project.ceramic_zones:
        z_room = zone.room_name if hasattr(zone, 'room_name') else zone.get('room_name', '')
        if z_room == room_name:
            found_zones += 1
            z_name = zone.name if hasattr(zone, 'name') else zone.get('name', '')
            z_perim = zone.perimeter if hasattr(zone, 'perimeter') else zone.get('perimeter', 0)
            z_height = zone.height if hasattr(zone, 'height') else zone.get('height', 0)
            z_area = z_perim * z_height
            total_ceramic += z_area
            
            print(f"  ✓ {z_name}")
            print(f"    محيط: {z_perim:.2f}م، ارتفاع: {z_height:.2f}م")
            print(f"    المساحة: {z_area:.2f} م²")
            
            if z_height < 1.4:
                print(f"    ⚠️  الارتفاع منخفض جداً!")
    
    if found_zones == 0:
        print("  ❌ لا توجد مناطق سيراميك لهذه الغرفة!")
        print("\n💡 الحل: افتح نافذة 'سيراميك الجدران' واضغط 'تطبيق'")
    else:
        print(f"\n📊 إجمالي السيراميك: {total_ceramic:.2f} م²")
        avg_height = total_ceramic / perim if perim > 0 else 0
        print(f"📐 الارتفاع الفعلي المحسوب: {avg_height:.2f} م")
        
        if avg_height < 1.4:
            print("\n❌ المشكلة مؤكدة: الارتفاع المحفوظ أقل من 1.5 متر!")
            print("\n🔧 الحل:")
            print("  1. افتح نافذة 'سيراميك جدران (مطبخ/حمام...)'")
            print("  2. اختر المطبخ من القائمة")
            print("  3. تأكد أن كل جدار له ارتفاع 1.50")
            print("  4. اضغط زر '✅ تطبيق'")
            print("  5. أعد التصدير")
        else:
            print("\n✅ الارتفاع صحيح!")

if __name__ == '__main__':
    check_kitchen()
