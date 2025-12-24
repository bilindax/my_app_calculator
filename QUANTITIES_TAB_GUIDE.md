# Quantities Tab (Lengths & Areas)

The new "📏 Quantities" tab gives you a single place to see the lengths and areas for Rooms, Walls, Doors, and Windows — with fast totals, search/filter, edit/delete shortcuts, and an option to insert a table directly into AutoCAD.

---

## Features

- Unified table for Rooms, Walls, Doors, and Windows
- Columns: Category, Name, Layer, Length (m), Area (m²)
- Live totals (bottom bar)
- Filters: by category + text search
- Quick actions: Edit, Delete
- Insert a formatted table into the AutoCAD drawing

---

## How to use

1. Open the app and go to the "📏 Quantities" tab.
2. Use the Category dropdown or Search to filter items.
3. Double-click an item (or use ✏️ Edit) to modify it using the existing dialogs.
4. Use 🗑️ Delete to remove the selected item from the project.
5. Click "📊 Insert Table to AutoCAD" to place a quantities table in the drawing (you will be prompted for an insertion point).

---

## What shows in Length and Area?

- Rooms: Length = Perimeter, Area = Floor area
- Walls: Length = Wall length, Area = Net area (after deductions)
- Doors: Length = Total perimeter (all quantities), Area = Total area (all quantities)
- Windows: Length = Total perimeter (all quantities), Area = Total area (all quantities)

---

## Inside AutoCAD vs. Separate Window

This application is a standalone Tkinter app that connects to AutoCAD via COM (pyautocad). It cannot be docked as a native AutoCAD palette. However, you can push your data into AutoCAD by inserting a table in model space using the "📊 Insert Table to AutoCAD" button.

- Requirement: AutoCAD must be running with a drawing open.
- You will be prompted to pick an insertion point.
- The table contains: Category, Name, Layer, Length (m), Area (m²).

---

## Notes

- Edit and Delete act on the underlying data and refresh all tabs.
- For Doors/Windows, the totals use the combined quantities.
- If the table insertion fails, ensure AutoCAD is open and COM access is available.

---

## Arabic (العربية)

تبويب جديد "📏 الكميات" يظهر جميع العناصر في مكان واحد مع أطوالها ومساحاتها ومجاميعها.

- الغرف: الطول = المحيط، المساحة = مساحة الأرضية
- الجدران: الطول = طول الجدار، المساحة = الصافي بعد الحذف
- الأبواب والشبابيك: الطول = محيط إجمالي، المساحة = مساحة إجمالية
- يمكنك التعديل أو الحذف بسرعة، والبحث والتصفية حسب النوع
- ويمكنك إدراج جدول الكميات داخل الأوتوكاد عبر زر "📊 إدراج جدول في الأوتوكاد"

ملاحظة: التطبيق يعمل كنافذة منفصلة (Tkinter) ولا يمكن تثبيته كلوحة داخل أوتوكاد عبر COM، لكن يمكن إدراج الجداول داخل الرسم.
