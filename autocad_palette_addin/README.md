# BILIND AutoCAD Palette Add-in

Modern AutoCAD .NET plug-in that hosts a floating palette inside AutoCAD to capture lengths and areas without leaving the drawing window. The palette mirrors the workflows from the Python BILIND desktop app but runs natively inside AutoCAD (`NETLOAD`).

> **Status:** Minimal working skeleton meant to get you started. You still need to compile against the AutoCAD managed assemblies installed on your machine (e.g., AutoCAD 2024). The palette already exposes selection measuring buttons; extend it as required.

---

## 1. Features

- Dockable palette (`PaletteSet`) that stays inside AutoCAD
- “Measure Selection” button prompts the user to select geometry and lists total lengths + areas
- Grid with running totals (per entity and whole selection)
- “Clear” button resets the session
- Light-weight, written in C#/.NET Framework 4.8

Planned enhancements:

1. Live event hooks (react to selection changes without clicking the button)
2. Bidirectional bridge with the Python BILIND app via Named Pipes/REST
3. Room/door/wall categorisation, filters, exports, etc.

---

## 2. Repository Layout

```plaintext
autocad_palette_addin/
├── PaletteAssistantAddin.sln            # Visual Studio solution
├── README.md                            # This file
└── src/
    ├── BilindPaletteAddin.csproj        # C# project
    ├── Properties/
    │   └── AssemblyInfo.cs
    └── Runtime/
        ├── MeasurementPaletteControl.cs # WinForms palette UI
        ├── MeasurementResult.cs         # Simple data record
        ├── PaletteCommands.cs           # Entry point + commands
        └── SelectionMeasurementService.cs
```

---

## 3. Build Prerequisites

- **AutoCAD** 2022 or later (adjust dll paths below) installed on the same machine
- **Visual Studio 2022** with ".NET desktop development" workload
- **.NET Framework 4.8 SDK**

The project expects an environment variable `ACAD_INSTALL` pointing at your AutoCAD install directory:

```powershell
# Example for AutoCAD 2024
setx ACAD_INSTALL "C:\Program Files\Autodesk\AutoCAD 2024"
```

Alternatively, edit `BilindPaletteAddin.csproj` and hard-code the paths to `acmgd.dll`, `acdbmgd.dll`, and `AdWindows.dll`.

---

## 4. Build & Deploy

1. Open `PaletteAssistantAddin.sln` in Visual Studio.
2. Restore references (Visual Studio will prompt if dlls are missing).
3. Build the project (`Build > Build Solution`).
4. Copy the output dll (`bin\Debug\BilindPaletteAddin.dll`) to a safe location.
5. Inside AutoCAD, run the command:

   ```plaintext
   NETLOAD
   ```

   Browse to the compiled dll and load it.

6. Launch the palette with the custom command:

   ```plaintext
   BILINDPALETTE
   ```

   The palette can be docked, auto-hidden, or floated like any native AutoCAD palette.

---

## 5. How It Works

- `PaletteCommands` implements `IExtensionApplication` and exposes the command `BILINDPALETTE`.
- On first run it creates a `PaletteSet` and hosts `MeasurementPaletteControl` (WinForms user control).
- `MeasurementPaletteControl` calls `SelectionMeasurementService` whenever “Measure Selection” is pressed.
- `SelectionMeasurementService` prompts the user to select polylines/lines/arcs/hatches, walks the selection set inside a transaction, and computes:
  - Length (m) for line/geodesic geometry
  - Area (m²) for closed polylines, hatches, regions, circles
  - Total aggregates appended as a final row

Extend `SelectionMeasurementService` to categorise results (e.g., detect layer names, room types) and push results into the Python app via a file drop or API.

---

## 6. Next Steps / Ideas

1. **Room Type Awareness**
   - Read entity layer names (e.g., `A-ROOM-KITCHEN`) and map them to BILIND room types
   - Display dedicated totals per type inside the palette
2. **Auto-Sync with BILIND Desktop**
   - Write JSON payloads to a hot folder; the Python app watches and imports automatically
   - Alternatively, expose a local REST endpoint inside the Python app and POST from the add-in
3. **Live Selection Hooks**
   - Subscribe to `SelectionAdded` and `SelectionRemoved` events so the palette updates without pressing the button
4. **Direct Commands**
   - Provide buttons to create BILIND-specific layers, block libraries, or highlight rooms missing data

---

## 7. Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `error CS0006: Metadata file 'acmgd.dll' could not be found` | AutoCAD dll paths not resolved | Set `ACAD_INSTALL` or edit csproj hint paths |
| Palette opens but buttons do nothing | NETLOAD succeeded but selection aborted | Ensure you press Enter after selecting objects |
| `System.Exception: eNotOpenForWrite` | Attempting to modify db without write access | Measurements open entities read-only; leave as-is or upgrade transaction mode |
| AutoCAD crashes on unload | Palette disposed while still visible | Avoid closing AutoCAD with palette command still active; Terminate handles this but test |

---

## 8. Integration Notes

- The palette currently only reports lengths/areas locally. To push the data into the Python app:
  1. Serialize `results` to JSON (`System.Text.Json`)
  2. Save to `%AppData%\BILIND\sync\measurements.json`
  3. Extend the Python app to watch this file and import into the Quantities tab automatically
- Reverse direction (Python → AutoCAD) can be done by letting the desktop app call a small local HTTP server hosted inside the add-in (e.g., `HttpListener`) that triggers commands.

---

## 9. Arabic Quick Guide (دليل سريع بالعربي)

1. افتح AutoCAD ثم حمل الإضافة عبر `NETLOAD`
2. اكتب الأمر `BILINDPALETTE` وستظهر نافذة داخل الأوتوكاد يمكن تثبيتها على الطرف
3. اضغط "Measure Selection" ثم عد إلى الرسم وحدد العناصر (خطوط، بولي لاين، هاتش)
4. اضغط Enter → يتم حساب الأطوال والمساحات وتظهر مباشرة في النافذة
5. استخدم زر "Clear" لتفريغ القائمة وابدأ قياسات جديدة

---

## 10. License / Credits

- © 2025 BILIND. Provided as a starting point for internal workflows.
- AutoCAD is a trademark of Autodesk, Inc.
