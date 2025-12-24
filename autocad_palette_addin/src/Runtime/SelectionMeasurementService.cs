using System.Collections.Generic;
using System.Globalization;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Geometry;

namespace Bilind.AutoCAD.Addin.Runtime
{
    /// <summary>
    /// Utility service that extracts total lengths and areas from the active selection.
    /// </summary>
    internal class SelectionMeasurementService
    {
        private readonly Document _doc;

        public SelectionMeasurementService(Document document)
        {
            _doc = document;
        }

        public IReadOnlyList<MeasurementResult> CollectMeasurements()
        {
            var results = new List<MeasurementResult>();
            var editor = _doc.Editor;

            var prompt = new PromptSelectionOptions
            {
                MessageForAdding = "Select polylines, lines, arcs, or hatches to measure",
                AllowDuplicates = false
            };

            var selection = editor.GetSelection(prompt);
            if (selection.Status != PromptStatus.OK)
            {
                return results;
            }

            using (var transaction = _doc.Database.TransactionManager.StartTransaction())
            {
                double totalLength = 0.0;
                double totalArea = 0.0;
                int count = 0;

                foreach (SelectedObject selObj in selection.Value)
                {
                    if (selObj.ObjectId.IsNull)
                    {
                        continue;
                    }

                    var entity = transaction.GetObject(selObj.ObjectId, OpenMode.ForRead) as Entity;
                    if (entity == null)
                    {
                        continue;
                    }

                    count++;
                    string name = entity.GetType().Name;
                    string layer = entity.Layer;
                    double length = 0.0;
                    double area = 0.0;

                    switch (entity)
                    {
                        case Polyline poly:
                            length = poly.Length;
                            if (IsClosed(poly))
                            {
                                area = poly.Area;
                            }
                            break;
                        case Line line:
                            length = line.Length;
                            break;
                        case Arc arc:
                            length = arc.Length;
                            break;
                        case Circle circle:
                            length = circle.Circumference;
                            area = circle.Area;
                            break;
                        case Region region:
                            area = region.Area;
                            break;
                        case Hatch hatch:
                            area = hatch.Area;
                            break;
                    }

                    totalLength += length;
                    totalArea += area;
                    results.Add(new MeasurementResult(name, entity.Handle.ToString(), layer, length, area));
                }

                if (count > 1)
                {
                    results.Add(new MeasurementResult("Total", $"{count} entities", string.Empty, totalLength, totalArea));
                }

                transaction.Commit();
            }

            return results;
        }

        private static bool IsClosed(Polyline polyline)
        {
            if (polyline.Closed)
            {
                return true;
            }

            var start = polyline.GetPoint2dAt(0);
            var end = polyline.GetPoint2dAt(polyline.NumberOfVertices - 1);
            return start.IsEqualTo(end);
        }
    }
}
