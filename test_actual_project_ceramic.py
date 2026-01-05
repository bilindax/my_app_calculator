"""
فحص مشروع فعلي: ليش خصم فتحات السيراميك = 0 بالإكسل؟
"""
import sys
import pickle

# محاولة تحميل آخر مشروع محفوظ
try:
    with open('last_project.pkl', 'rb') as f:
        project = pickle.load(f)
    print("✅ تم تحميل المشروع من last_project.pkl")
except Exception as e:
    print(f"❌ فشل تحميل المشروع: {e}")
    print("\nللتشخيص، شغّل البرنامج واحفظ المشروع أولاً.")
    sys.exit(1)

from bilind.calculations.unified_calculator import UnifiedCalculator

calc = UnifiedCalculator(project)

print("\n" + "="*80)
print("تشخيص خصومات السيراميك في المشروع الفعلي")
print("="*80)

# إحصائيات عامة
rooms = getattr(project, 'rooms', []) or []
zones = getattr(project, 'ceramic_zones', []) or []
doors = getattr(project, 'doors', []) or []
windows = getattr(project, 'windows', []) or []

print(f"\n📊 إحصائيات المشروع:")
print(f"   عدد الغرف: {len(rooms)}")
print(f"   عدد مناطق السيراميك: {len(zones)}")
print(f"   عدد الأبواب: {len(doors)}")
print(f"   عدد الشبابيك: {len(windows)}")

# فحص كل غرفة
print(f"\n" + "="*80)
print("فحص مفصل لكل غرفة:")
print("="*80)

for room in rooms:
    rname = getattr(room, 'name', 'غرفة بدون اسم')
    print(f"\n🏠 {rname}")
    print(f"   {'─'*60}")
    
    # Zones في هذه الغرفة
    room_zones = [z for z in zones if str(getattr(z, 'room_name', '') or '').strip().lower() == rname.lower()]
    wall_zones = [z for z in room_zones if str(getattr(z, 'surface_type', 'wall') or 'wall').strip().lower() == 'wall']
    
    print(f"   مناطق السيراميك: {len(room_zones)} (جدران: {len(wall_zones)})")
    
    if not wall_zones:
        print(f"   ⚠️  لا يوجد سيراميك جدران → الخصم = 0 (طبيعي)")
        continue
    
    # فحص الفتحات المربوطة
    merged_ids = calc._iter_room_opening_ids(room)
    print(f"   الفتحات المربوطة: {len(merged_ids)}")
    if merged_ids:
        print(f"      {', '.join(merged_ids[:5])}" + (" ..." if len(merged_ids) > 5 else ""))
    
    if not merged_ids:
        print(f"   ⚠️  لا يوجد فتحات → الخصم = 0 (طبيعي)")
        continue
    
    # حساب خصم كل zone
    total_gross = 0.0
    total_deduct = 0.0
    total_net = 0.0
    
    for z in wall_zones:
        zname = getattr(z, 'name', '-')
        m = calc.calculate_zone_metrics(z)
        total_gross += m.gross_area
        total_deduct += m.deduction_area
        total_net += m.net_area
        
        if m.deduction_area > 0.01:
            print(f"   ✅ {zname}:")
            print(f"      قائم: {m.gross_area:.2f}م² | خصم: {m.deduction_area:.2f}م² | صافي: {m.net_area:.2f}م²")
            print(f"      تفاصيل: {m.deduction_details}")
    
    print(f"\n   📈 الإجمالي:")
    print(f"      قائم: {total_gross:.2f}م²")
    print(f"      خصم: {total_deduct:.2f}م²")
    print(f"      صافي: {total_net:.2f}م²")
    
    if total_deduct < 0.01:
        print(f"   ⚠️  الخصم = 0 رغم وجود فتحات!")
        print(f"   🔍 أسباب محتملة:")
        print(f"      1. الفتحات فوق/تحت شريط السيراميك (لا تداخل)")
        print(f"      2. host_wall للفتحة مو مطابق لـwall_name في الـzone")
        print(f"      3. opening_type غلط (مو DOOR/WINDOW)")
        
        # فحص أعمق
        for oid in merged_ids[:3]:  # أول 3 فتحات
            o = calc.openings_map.get(oid)
            if not o:
                continue
            otype = str(getattr(o, 'opening_type', '?')).upper()
            place = float(getattr(o, 'placement_height', 0.0) or 0.0)
            oh = float(getattr(o, 'height', 0.0) or 0.0)
            host = str(getattr(o, 'host_wall', '-') or '-')
            print(f"\n      📌 {oid}:")
            print(f"         نوع: {otype}")
            print(f"         منسوب: {place}م - {place+oh}م")
            print(f"         host_wall: {host}")
            
            # فحص تداخل مع أول zone
            if wall_zones:
                z0 = wall_zones[0]
                z_start = float(getattr(z0, 'start_height', 0.0) or 0.0)
                z_height = float(getattr(z0, 'height', 0.0) or 0.0)
                z_end = z_start + z_height
                overlap = max(0.0, min(z_end, place+oh) - max(z_start, place))
                print(f"         تداخل مع zone[0] [{z_start}-{z_end}]: {overlap:.2f}م")

print("\n" + "="*80)
print("انتهى التشخيص")
print("="*80)
