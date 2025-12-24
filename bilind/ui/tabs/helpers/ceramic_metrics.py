"""
Ceramic Metrics Helper
======================
Calculate accurate ceramic totals using UnifiedCalculator.
"""

from typing import Any, Dict
from bilind.calculations.unified_calculator import UnifiedCalculator


def calculate_ceramic_metrics(project: Any) -> Dict[str, float]:
    """
    Calculate accurate ceramic totals using UnifiedCalculator.
    
    This ensures the UI displays the SAME numbers as Excel export.
    
    Returns:
        Dict with keys: 'wall', 'floor', 'ceiling', 'total'
    """
    if not project or not hasattr(project, 'rooms'):
        return {'wall': 0.0, 'floor': 0.0, 'ceiling': 0.0, 'total': 0.0}
    
    calc = UnifiedCalculator(project)
    totals = calc.calculate_totals()
    
    return {
        'wall': totals['ceramic_wall'],
        'floor': totals['ceramic_floor'],
        'ceiling': totals['ceramic_ceiling'],
        'total': totals['ceramic_total']
    }
