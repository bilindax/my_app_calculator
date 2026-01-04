# Master Sheet Export Feature (دفتر المساحة الموحد)

## Overview
A new export feature has been added to generate a **comprehensive, centralized Excel report** that allows for easy verification of quantities and detection of contradictions.

## Key Features
- **Single Sheet View**: All data is in one wide table, row by row per room.
- **Logical Flow**: Follows the construction sequence:
  1. **Dimensions** (الأبعاد)
  2. **Gross Area** (المساحة القائمة)
  3. **Openings Deduction** (خصم الفتحات)
  4. **Plaster** (الزريقة/اللياسة)
  5. **Ceramic** (السيراميك)
  6. **Paint** (الدهان)
- **Centralized Calculation**: Uses the `UnifiedCalculator` engine to ensure numbers match exactly with other reports.

## Column Structure
| Section | Columns | Description |
|---------|---------|-------------|
| **Info** | 1-3 | Sequence, Room Name, Type |
| **Dimensions** | 4-8 | Length, Width, Height, Perimeter, Floor Area |
| **Gross** | 9-11 | Gross Wall Area, Ceiling Area, **Total Gross** |
| **Openings** | 12 | **Total Openings Deduction** |
| **Plaster** | 13-15 | Net Wall Plaster, Ceiling Plaster, **Total Plaster** |
| **Ceramic** | 16-19 | Wall Ceramic, Floor Ceramic, Ceiling Ceramic, **Total Ceramic** |
| **Paint** | 20-22 | Wall Paint, Ceiling Paint, **Total Paint** |
| **Notes** | 23 | Warnings or special notes |

## How to Use
1. Go to the **Quantities Tab** (الكميات).
2. Click the new button: **📑 دفتر المساحة الموحد**.
3. Save the Excel file.

## Verification Logic
This sheet helps you spot errors like:
- **Plaster > Gross**: Impossible (unless added manually).
- **Paint > Plaster**: Impossible (Paint is usually <= Plaster).
- **Ceramic + Paint != Plaster**: Checks if surfaces are accounted for.
