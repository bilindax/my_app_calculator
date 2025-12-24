using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Windows.Forms;
using Autodesk.AutoCAD.ApplicationServices;

namespace Bilind.AutoCAD.Addin.Runtime
{
    internal class MeasurementPaletteControl : UserControl
    {
        private readonly Document _doc;
        private readonly DataGridView _grid;
        private readonly Button _refreshButton;
        private readonly Button _clearButton;
        private readonly Label _statusLabel;
        private readonly BindingSource _bindingSource = new();

        public MeasurementPaletteControl(Document document)
        {
            _doc = document;
            Dock = DockStyle.Fill;
            BackColor = Color.FromArgb(20, 24, 34);
            ForeColor = Color.WhiteSmoke;

            var header = new Label
            {
                Text = "BILIND Quantities Assistant",
                Dock = DockStyle.Top,
                Height = 36,
                TextAlign = ContentAlignment.MiddleLeft,
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                Padding = new Padding(12, 0, 0, 0)
            };
            Controls.Add(header);

            var toolbar = new FlowLayoutPanel
            {
                Dock = DockStyle.Top,
                Height = 42,
                FlowDirection = FlowDirection.LeftToRight,
                Padding = new Padding(10, 6, 0, 6)
            };
            Controls.Add(toolbar);

            _refreshButton = new Button
            {
                Text = "Measure Selection",
                AutoSize = true,
                BackColor = Color.FromArgb(0, 180, 220),
                ForeColor = Color.Black,
                FlatStyle = FlatStyle.Flat
            };
            _refreshButton.Click += (_, _) => MeasureSelection();
            toolbar.Controls.Add(_refreshButton);

            _clearButton = new Button
            {
                Text = "Clear",
                AutoSize = true,
                Margin = new Padding(12, 0, 0, 0),
                BackColor = Color.FromArgb(55, 65, 81),
                ForeColor = Color.WhiteSmoke,
                FlatStyle = FlatStyle.Flat
            };
            _clearButton.Click += (_, _) => ClearMeasurements();
            toolbar.Controls.Add(_clearButton);

            _grid = new DataGridView
            {
                Dock = DockStyle.Fill,
                AutoGenerateColumns = false,
                BackgroundColor = Color.FromArgb(20, 24, 34),
                BorderStyle = BorderStyle.None,
                EnableHeadersVisualStyles = false,
                ColumnHeadersDefaultCellStyle = new DataGridViewCellStyle
                {
                    BackColor = Color.FromArgb(31, 41, 55),
                    ForeColor = Color.White,
                    Font = new Font("Segoe UI", 9, FontStyle.Bold)
                },
                DefaultCellStyle = new DataGridViewCellStyle
                {
                    BackColor = Color.FromArgb(17, 24, 39),
                    ForeColor = Color.WhiteSmoke,
                    SelectionBackColor = Color.FromArgb(59, 130, 246),
                    SelectionForeColor = Color.White
                }
            };
            _grid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = nameof(MeasurementResult.Category), HeaderText = "Category", Width = 110 });
            _grid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = nameof(MeasurementResult.Name), HeaderText = "Name", Width = 160 });
            _grid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = nameof(MeasurementResult.Layer), HeaderText = "Layer", Width = 120 });
            _grid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = nameof(MeasurementResult.Length), HeaderText = "Length (m)", Width = 110, DefaultCellStyle = new DataGridViewCellStyle { Format = "N3" } });
            _grid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = nameof(MeasurementResult.Area), HeaderText = "Area (m²)", Width = 110, DefaultCellStyle = new DataGridViewCellStyle { Format = "N3" } });
            _grid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = nameof(MeasurementResult.Timestamp), HeaderText = "Time", Width = 140, DefaultCellStyle = new DataGridViewCellStyle { Format = "HH:mm:ss" } });
            _grid.DataSource = _bindingSource;
            Controls.Add(_grid);

            _statusLabel = new Label
            {
                Dock = DockStyle.Bottom,
                Height = 28,
                TextAlign = ContentAlignment.MiddleRight,
                Padding = new Padding(0, 0, 12, 0)
            };
            Controls.Add(_statusLabel);
        }

        private void MeasureSelection()
        {
            var editor = _doc.Editor;
            editor.WriteMessage("\n[BILIND] Select objects to measure, then press Enter...");

            try
            {
                var service = new SelectionMeasurementService(_doc);
                var results = service.CollectMeasurements();
                BindMeasurements(results);
                editor.WriteMessage("\n[BILIND] Measurement complete.");
            }
            catch (System.Exception ex)
            {
                editor.WriteMessage($"\n[BILIND] Measurement failed: {ex.Message}");
            }
        }

        private void ClearMeasurements()
        {
            _bindingSource.DataSource = Array.Empty<MeasurementResult>();
            _statusLabel.Text = "Ready";
        }

        private void BindMeasurements(IReadOnlyList<MeasurementResult> results)
        {
            if (results == null || results.Count == 0)
            {
                _bindingSource.DataSource = Array.Empty<MeasurementResult>();
                _statusLabel.Text = "No entities measured";
                return;
            }

            _bindingSource.DataSource = results.ToList();
            double lengthSum = results.Where(r => r.Category != "Total").Sum(r => r.Length);
            double areaSum = results.Where(r => r.Category != "Total").Sum(r => r.Area);
            _statusLabel.Text = $"Σ Length = {lengthSum:N3} m • Σ Area = {areaSum:N3} m²";
        }
    }
}
