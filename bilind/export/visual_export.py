"""
Visual Export Module
===================
Generates charts and graphs for project data using Matplotlib.
Used for inserting visual reports into AutoCAD or PDF exports.
"""

import matplotlib.pyplot as plt
import tempfile
import os
from typing import List, Dict, Any, Optional
from bilind.models.project import Project

def create_room_area_chart(project: Project) -> Optional[str]:
    """
    Create a pie chart of room areas.
    
    Args:
        project: Project data
        
    Returns:
        Path to temporary image file, or None if no data
    """
    if not project.rooms:
        return None
        
    # Aggregate data (group small rooms or by name)
    labels = []
    sizes = []
    
    # Sort by area
    sorted_rooms = sorted(project.rooms, key=lambda r: r.area, reverse=True)
    
    # Take top 10, group rest
    for room in sorted_rooms[:10]:
        labels.append(f"{room.name}\n({room.area:.1f}m²)")
        sizes.append(room.area)
        
    if len(sorted_rooms) > 10:
        others_area = sum(r.area for r in sorted_rooms[10:])
        labels.append(f"Others\n({others_area:.1f}m²)")
        sizes.append(others_area)
        
    if not sizes:
        return None

    # Create plot
    plt.figure(figsize=(10, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Pastel1.colors)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title(f"Room Areas Distribution (Total: {sum(r.area for r in project.rooms):.1f}m²)")
    
    # Save to temp file
    fd, path = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    plt.savefig(path, bbox_inches='tight', dpi=150)
    plt.close()
    
    return path

def create_finishes_chart(project: Project) -> Optional[str]:
    """
    Create a bar chart of finish quantities.
    
    Args:
        project: Project data
        
    Returns:
        Path to temporary image file, or None if no data
    """
    categories = []
    values = []
    colors = []
    
    # Plaster
    plaster_total = sum(item.quantity for item in project.plaster_items)
    if plaster_total > 0:
        categories.append("Plaster")
        values.append(plaster_total)
        colors.append('#ff9999') # Light red
        
    # Paint
    paint_total = sum(item.quantity for item in project.paint_items)
    if paint_total > 0:
        categories.append("Paint")
        values.append(paint_total)
        colors.append('#66b3ff') # Light blue
        
    # Tiles
    tiles_total = sum(item.quantity for item in project.tiles_items)
    if tiles_total > 0:
        categories.append("Floor Tiles")
        values.append(tiles_total)
        colors.append('#99ff99') # Light green
        
    # Ceramic Walls
    ceramic_total = sum(z.area for z in project.ceramic_zones)
    if ceramic_total > 0:
        categories.append("Wall Ceramic")
        values.append(ceramic_total)
        colors.append('#ffcc99') # Light orange
        
    if not values:
        return None
        
    # Create plot
    plt.figure(figsize=(10, 6))
    bars = plt.bar(categories, values, color=colors)
    
    # Add value labels on top
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}m²',
                ha='center', va='bottom')
                
    plt.title("Finish Quantities Summary")
    plt.ylabel("Area (m²)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save to temp file
    fd, path = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    plt.savefig(path, bbox_inches='tight', dpi=150)
    plt.close()
    
    return path

def create_project_charts(project: Project) -> Dict[str, str]:
    """
    Generate all available charts for the project.
    
    Args:
        project: Project data
        
    Returns:
        Dictionary mapping chart name to file path
    """
    charts = {}
    
    p1 = create_room_area_chart(project)
    if p1:
        charts['room_areas'] = p1
        
    p2 = create_finishes_chart(project)
    if p2:
        charts['finishes'] = p2
        
    return charts
