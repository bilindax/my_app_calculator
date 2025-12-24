"""
BILIND UI Tabs Package
=====================
Modular tab components for the main application window.
"""

from .base_tab import BaseTab
from .rooms_tab import RoomsTab
from .walls_tab import WallsTab
from .finishes_tab import FinishesTab
from .materials_tab import MaterialsTab
from .summary_tab import SummaryTab
from .dashboard_tab import DashboardTab
from .sync_log_tab import SyncLogTab
from .costs_tab import CostsTab
from .settings_tab import SettingsTab
from .material_estimator_tab import MaterialEstimatorTab
from .quantities_tab import QuantitiesTab

__all__ = [
    'BaseTab', 'RoomsTab', 'WallsTab', 'FinishesTab',
    'MaterialsTab', 'SummaryTab', 'DashboardTab', 'SyncLogTab', 'CostsTab',
    'SettingsTab', 'MaterialEstimatorTab', 'QuantitiesTab'
]
