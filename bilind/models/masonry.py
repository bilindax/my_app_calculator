"""
Masonry Block Calculator Model
===============================
Calculate block quantities and mortar for masonry walls.
"""

from dataclasses import dataclass
from typing import Dict, Any, Literal


@dataclass
class MasonryBlock:
    """
    Calculate masonry block quantities and mortar requirements.
    
    Common block sizes in Middle East construction:
    - 20cm (20×20×40cm): Standard block, 12.5 blocks/m²
    - 15cm (15×20×40cm): Partition walls, 12.5 blocks/m²
    - 10cm (10×20×40cm): Light partitions, 12.5 blocks/m²
    
    Attributes:
        name: Wall/area name
        net_area: Net wall area after openings deducted (m²)
        block_size: Block thickness ('20cm', '15cm', '10cm')
        mortar_joint_thickness: Joint thickness in mm (typically 10mm)
    """
    name: str
    net_area: float
    block_size: Literal['20cm', '15cm', '10cm'] = '20cm'
    mortar_joint_thickness: float = 10.0  # mm
    
    # Blocks per m² for standard 20×20×40cm blocks with 10mm joints
    BLOCKS_PER_M2 = {
        '20cm': 12.5,
        '15cm': 12.5,
        '10cm': 12.5
    }
    
    # Mortar volume per m² (m³) - approximate for 10mm joints
    MORTAR_M3_PER_M2 = {
        '20cm': 0.022,  # ~22 liters per m²
        '15cm': 0.018,  # ~18 liters per m²
        '10cm': 0.015   # ~15 liters per m²
    }
    
    # Mortar mix ratio for block laying (typically 1:6 cement:sand)
    MORTAR_MIX_RATIO = {'cement': 1, 'sand': 6}
    
    # Material densities
    CEMENT_DENSITY = 1440  # kg/m³
    SAND_DENSITY = 1600    # kg/m³
    CEMENT_BAG_WEIGHT = 50 # kg
    
    def __post_init__(self):
        """Validate inputs."""
        if self.net_area <= 0:
            raise ValueError(f"Net area must be positive: {self.net_area}")
        if self.block_size not in self.BLOCKS_PER_M2:
            raise ValueError(f"Invalid block size: {self.block_size}")
        if self.mortar_joint_thickness <= 0 or self.mortar_joint_thickness > 30:
            raise ValueError(f"Joint thickness must be 1-30mm: {self.mortar_joint_thickness}")
    
    @property
    def block_quantity(self) -> int:
        """Calculate number of blocks needed (rounded up)."""
        blocks_per_m2 = self.BLOCKS_PER_M2[self.block_size]
        total_blocks = self.net_area * blocks_per_m2
        return int(total_blocks) + (1 if total_blocks % 1 > 0 else 0)
    
    @property
    def mortar_volume_m3(self) -> float:
        """Calculate total mortar volume needed (m³)."""
        mortar_per_m2 = self.MORTAR_M3_PER_M2[self.block_size]
        # Adjust for joint thickness variation
        thickness_factor = self.mortar_joint_thickness / 10.0
        return self.net_area * mortar_per_m2 * thickness_factor
    
    def calculate_mortar_materials(self) -> Dict[str, float]:
        """
        Calculate mortar materials (cement and sand).
        
        Returns:
            Dictionary with sand_m3, cement_kg, cement_bags
        """
        total_parts = self.MORTAR_MIX_RATIO['cement'] + self.MORTAR_MIX_RATIO['sand']
        cement_volume = self.mortar_volume_m3 * (self.MORTAR_MIX_RATIO['cement'] / total_parts)
        sand_volume = self.mortar_volume_m3 * (self.MORTAR_MIX_RATIO['sand'] / total_parts)
        
        cement_kg = cement_volume * self.CEMENT_DENSITY
        cement_bags = int(cement_kg / self.CEMENT_BAG_WEIGHT) + (1 if cement_kg % self.CEMENT_BAG_WEIGHT > 0 else 0)
        
        return {
            'sand_m3': sand_volume,
            'sand_kg': sand_volume * self.SAND_DENSITY,
            'cement_kg': cement_kg,
            'cement_bags': cement_bags,
            'mortar_m3': self.mortar_volume_m3
        }
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        materials = self.calculate_mortar_materials()
        return (
            f"Blocks: {self.block_quantity} pcs • "
            f"Mortar: {materials['mortar_m3']:.3f} m³ • "
            f"Sand: {materials['sand_m3']:.2f} m³ • "
            f"Cement: {materials['cement_bags']} bags"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        materials = self.calculate_mortar_materials()
        return {
            'name': self.name,
            'net_area': self.net_area,
            'block_size': self.block_size,
            'mortar_joint_thickness': self.mortar_joint_thickness,
            'block_quantity': self.block_quantity,
            **materials
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MasonryBlock':
        """Create MasonryBlock from dictionary."""
        return cls(
            name=data.get('name', ''),
            net_area=data.get('net_area', 0.0),
            block_size=data.get('block_size', '20cm'),
            mortar_joint_thickness=data.get('mortar_joint_thickness', 10.0)
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"MasonryBlock('{self.name}', {self.net_area:.2f}m², {self.block_size}, {self.block_quantity} blocks)"
