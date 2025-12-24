using System;

namespace Bilind.AutoCAD.Addin.Runtime
{
    /// <summary>
    /// Simple record used to bind measurement values into the palette grid.
    /// </summary>
    public class MeasurementResult
    {
        public string Category { get; }
        public string Name { get; }
        public string Layer { get; }
        public double Length { get; }
        public double Area { get; }
        public DateTime Timestamp { get; }

        public MeasurementResult(string category, string name, string layer, double length, double area)
        {
            Category = category;
            Name = name;
            Layer = layer;
            Length = length;
            Area = area;
            Timestamp = DateTime.UtcNow;
        }
    }
}
