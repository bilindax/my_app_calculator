"""
تشخيص خصومات فتحات السيراميك - مثال عملي
========================================
هذا المثال يفحص بالضبط كيف يحسب المحرك خصم فتحة شباك
عندما تتداخل مع شريط سيراميك ارتفاعه 1.6م
"""

from bilind.calculations.unified_calculator import UnifiedCalculator

# مشروع مبسط للتجربة
class MockProject:
    default_wall_height = 3.2
    rooms = []
    doors = []
    windows = []
    ceramic_zones = []

# غرفة: مطبخ
class MockRoom:
    name = "مطبخ"
    area = 12.0
    perimeter = 14.0
    wall_height = 3.2
    walls = [
        type('Wall', (), {'name': 'جدار 1', 'length': 4.0, 'height': 3.2})(),
        type('Wall', (), {'name': 'جدار 2', 'length': 3.0, 'height': 3.2})(),
        type('Wall', (), {'name': 'جدار 3', 'length': 4.0, 'height': 3.2})(),
        type('Wall', (), {'name': 'جدار 4', 'length': 3.0, 'height': 3.2})(),
    ]
    opening_ids = ['W1']

# شباك: على ارتفاع 1م من الأرض، ارتفاع الشباك 1.2م
class MockWindow:
    name = "W1"
    opening_type = "WINDOW"
    width = 1.5
    height = 1.2
    placement_height = 1.0  # من الأرض
    host_wall = "جدار 1"
    quantity = 1
    room_quantities = {"مطبخ": 1}
    assigned_rooms = ["مطبخ"]

# منطقة سيراميك: ارتفاع 1.6م من الأرض (0-1.6)
class MockCeramicZone:
    name = "مطبخ - جدار 1"
    room_name = "مطبخ"
    surface_type = "wall"
    wall_name = "جدار 1"
    perimeter = 4.0  # طول الجدار
    height = 1.6     # ارتفاع السيراميك
    start_height = 0.0
    effective_area = 0.0  # ليس يدوي
    category = "KITCHEN"

# ربط البيانات
project = MockProject()
room = MockRoom()
window = MockWindow()
zone = MockCeramicZone()

project.rooms = [room]
project.windows = [window]
project.ceramic_zones = [zone]

# تشغيل المحرك
calc = UnifiedCalculator(project)

print("=" * 80)
print("تشخيص حساب خصم فتحات السيراميك")
print("=" * 80)
print(f"\n📐 معلومات الغرفة:")
print(f"   الاسم: {room.name}")
print(f"   المحيط: {room.perimeter}م")
print(f"   ارتفاع الجدار: {room.wall_height}م")

print(f"\n🪟 معلومات الشباك:")
print(f"   الاسم: {window.name}")
print(f"   العرض: {window.width}م")
print(f"   الارتفاع: {window.height}م")
print(f"   منسوب التركيب: {window.placement_height}م من الأرض")
print(f"   الشباك يمتد من {window.placement_height}م إلى {window.placement_height + window.height}م")

print(f"\n🟦 معلومات منطقة السيراميك:")
print(f"   الاسم: {zone.name}")
print(f"   الجدار: {zone.wall_name}")
print(f"   المحيط: {zone.perimeter}م")
print(f"   ارتفاع السيراميك: {zone.height}م")
print(f"   بداية: {zone.start_height}م")
print(f"   السيراميك يمتد من {zone.start_height}م إلى {zone.start_height + zone.height}م")

# حساب التداخل (Overlap)
z_start = zone.start_height
z_end = z_start + zone.height
w_start = window.placement_height
w_end = w_start + window.height

overlap_start = max(z_start, w_start)
overlap_end = min(z_end, w_end)
overlap_height = max(0.0, overlap_end - overlap_start)

print(f"\n🔍 حساب التداخل:")
print(f"   السيراميك: [{z_start}م - {z_end}م]")
print(f"   الشباك: [{w_start}م - {w_end}م]")
print(f"   التداخل: [{overlap_start}م - {overlap_end}م]")
print(f"   ارتفاع التداخل: {overlap_height}م")

expected_deduction = window.width * overlap_height
print(f"\n✅ الخصم المتوقع:")
print(f"   {window.width}م (عرض) × {overlap_height}م (تداخل) = {expected_deduction:.3f}م²")

# استدعاء SSOT
metrics = calc.calculate_zone_metrics(zone)

print(f"\n📊 نتيجة SSOT (calculate_zone_metrics):")
print(f"   المساحة القائمة: {metrics.gross_area:.3f}م²")
print(f"   خصم الفتحات: {metrics.deduction_area:.3f}م²")
print(f"   المساحة الصافية: {metrics.net_area:.3f}م²")
print(f"   تفاصيل الخصم: {metrics.deduction_details}")

# التحقق
print(f"\n🎯 التحقق:")
if abs(metrics.deduction_area - expected_deduction) < 0.01:
    print(f"   ✅ الخصم صحيح! ({metrics.deduction_area:.3f}م² ≈ {expected_deduction:.3f}م²)")
else:
    print(f"   ❌ الخصم غير صحيح!")
    print(f"      المتوقع: {expected_deduction:.3f}م²")
    print(f"      الفعلي: {metrics.deduction_area:.3f}م²")
    print(f"      الفرق: {abs(metrics.deduction_area - expected_deduction):.3f}م²")

# فحص ما إذا كانت الفتحة ظاهرة في opening_ids
print(f"\n🔗 فحص ربط الفتحة:")
merged_ids = calc._iter_room_opening_ids(room)
print(f"   opening_ids مدمجة: {merged_ids}")
if window.name in merged_ids:
    print(f"   ✅ الفتحة مربوطة بالغرفة")
else:
    print(f"   ❌ الفتحة غير مربوطة! (سبب محتمل للخصم = 0)")

print("\n" + "=" * 80)
