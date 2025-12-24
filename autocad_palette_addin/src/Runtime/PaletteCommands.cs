using System;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.Windows;

namespace Bilind.AutoCAD.Addin.Runtime
{
    /// <summary>
    /// Entry point for the palette add-in. Registers commands and manages lifecycle.
    /// </summary>
    public class PaletteCommands : IExtensionApplication
    {
        private PaletteSet? _paletteSet;
        private MeasurementPaletteControl? _paletteControl;

        public void Initialize()
        {
            // Lazy creation; palette is created on first command run.
        }

        public void Terminate()
        {
            if (_paletteSet is { } palette)
            {
                palette.Visible = false;
                palette.Dispose();
                _paletteSet = null;
            }
        }

        [CommandMethod("BILIND", "BILINDPALETTE", CommandFlags.Modal)]
        public void ShowPalette()
        {
            var doc = Application.DocumentManager.MdiActiveDocument;
            if (doc is null)
            {
                Autodesk.AutoCAD.ApplicationServices.Application.ShowAlertDialog("Please open a drawing before launching the palette.");
                return;
            }

            if (_paletteSet == null)
            {
                _paletteSet = new PaletteSet("BILIND Quantities")
                {
                    Size = new System.Drawing.Size(420, 520),
                    MinimumSize = new System.Drawing.Size(360, 420)
                };

                _paletteControl = new MeasurementPaletteControl(doc);
                _paletteSet.Add("Quantities", _paletteControl);
                _paletteSet.Style |= PaletteSetStyles.ShowPropertiesMenu;
            }

            _paletteSet.Visible = true;
            _paletteSet.KeepFocus = true;
        }
    }
}
