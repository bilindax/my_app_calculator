"""Calculation helpers and business logic for BILIND."""

from .helpers import build_opening_record, format_number
# Legacy room_metrics removed - use UnifiedCalculator instead

__all__ = [
	'build_opening_record',
	'format_number',
]
