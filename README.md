# 🚀 BILIND - Advanced AutoCAD Quantity Takeoff Tool

**BILIND** is a powerful, standalone quantity takeoff application for AutoCAD, built with Python and Tkinter. It streamlines the process of calculating areas, dimensions, and material quantities directly from your `.dwg` files, providing a feature-rich interface to manage and export your data.


*(Note: Replace with an actual screenshot of the bilind_main.py interface)*

## ✨ Core Features

- **Multi-Tab Interface:** Organize your workflow with dedicated tabs for Rooms, Openings, Walls, Finishes, and a comprehensive Summary.
- **AutoCAD Integration:**
    - Pick Rooms (Closed Polylines), Openings (Blocks), and Walls directly from your drawing.
    - Smart scaling for drawings in meters, centimeters, or millimeters.
- **Advanced Calculations:**
    - **Rooms:** Calculates Area, Perimeter, and optional Length/Width for regular shapes.
    - **Openings:** Extracts dimensions for Doors & Windows from block attributes or bounding boxes. Includes detailed material calculations (e.g., glass area, steel weight).
    - **Walls:** Calculates gross/net wall areas and volumes.
    - **Finishes:** Comprehensive calculation for paint, plaster, skirting, and flooring.
- **Material & Ceramic Planner:**
    - A dedicated module for planning ceramic tile layouts in kitchens and bathrooms.
    - Material catalogs for doors and windows (e.g., Wood, Steel, PVC).
- **Data Management:**
    - Manually add, edit, or delete entries in any category.
    - Instant summary tables with aggregated totals.
- **Exporting:**
    - **Copy to Clipboard:** Instantly paste data into Excel.
    - **Export to CSV:** Generate detailed CSV reports.
    - **(Coming Soon) Insert Table to AutoCAD:** A planned feature to write the summary table back to your drawing.

## 🔧 Installation & Usage

### 1. Prerequisites
- Windows 10/11
- AutoCAD 2018+
- Python 3.8+

### 2. Setup
1.  **Install Python:** If you haven't already, download and install Python from [python.org](https://www.python.org/).
2.  **Install Dependencies:** Open a terminal or PowerShell in the project directory and run:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Running the Application
1.  Ensure **AutoCAD is running** and your desired drawing file is open.
2.  Run the main script from your terminal:
    ```bash
    python bilind_main.py
    ```

## 📖 Workflow Guide

1.  **Launch the App:** Run `bilind_main.py`.
2.  **Set the Scale:** Adjust the scale factor based on your drawing's units (e.g., `1` for meters, `1000` for millimeters).
3.  **Pick from AutoCAD:** Use the "Pick" buttons in each tab to select objects from your drawing. The application will automatically populate the tables.
4.  **Manual Adjustments:** Manually edit or add data as needed using the entry fields and buttons in each tab.
5.  **Review Summary:** Check the "Summary" tab for aggregated totals of all quantities.
6.  **Export Data:** Use the "Copy" or "CSV" buttons to export your results.

## ⚙️ Technical Details

### Block Attribute Recognition
The application automatically reads the following attributes from blocks for dimensions:
- `WIDTH` or `W`
- `HEIGHT` or `H`
- `LENGTH` or `L`

If these attributes are not found, it falls back to using the block's **BoundingBox** dimensions.

### COM Interface Limitation
This application uses the `pyautocad` library, which relies on the AutoCAD COM interface. This means the application window runs as a separate, floating process and **cannot be docked** into the AutoCAD user interface like a native palette. For a fully integrated, dockable UI, a C#/.NET implementation would be required.

## 🎨 Phase 10: Modern UI (NEW - October 2025)

**Visual Transformation Complete!** ✨

BILIND now features a modern, professional dark theme powered by **ttkbootstrap**:

### What's New:
- ✅ **5 Modern Dark Themes:** Cyborg (cyan), Darkly (blue), Superhero (orange), Solar (yellow), Vapor (purple)
- ✅ **Alternating Row Colors:** All tables now have zebra striping for better readability
- ✅ **Enhanced Buttons:** Smooth hover effects, increased padding, Material Design
- ✅ **Theme Selector:** Settings → Appearance → Choose your favorite theme
- ✅ **Improved Readability:** 30px row height, minimal scrollbars, professional spacing

### Visual Improvement:
- **Before:** Windows 95-style grey interface
- **After:** Modern Material Design dark theme (+250% visual quality)

### Try It:
1. Go to **⚙️ Settings** tab
2. Under **Appearance**, select **Modern Theme**
3. Choose a theme (e.g., "cyborg" or "vapor")
4. Click **✨ Apply** and watch the magic happen!

---

## 🚀 Future Enhancements (Roadmap)

- **Implement "Insert Table to AutoCAD":** The highest priority feature to complete the workflow loop.
- **Advanced Reporting:** Generate formatted Excel (`.xlsx`) and PDF reports.
- **Data Visualization:** A dashboard with charts (e.g., area distribution) to visualize quantities.
- **Cost Estimation:** A module to assign unit costs to materials and calculate total project costs.
- **Localization:** Support for multiple languages, including Arabic.
- **Custom Canvas Widgets:** Optional Phase 11 - Rounded buttons with shadows (2-3 days effort)

---

**Made with ❤️ for architects, engineers, and designers.**

**Latest Update:** Phase 10 - Modern UI Complete (Oct 2025) 🎉
