"""
Dashboard UI Components

This package contains all the UI components extracted from the monolithic app.py
to create a more maintainable and modular architecture.
"""

from .base_component import BaseComponent
from .header import HeaderComponent
from .sidebar import SidebarComponent
from .upload_section import UploadComponent
from .summary_cards import SummaryCardsComponent
from .visualizations import VisualizationsComponent
from .data_table import DataTableComponent
from .enhanced_sections import EnhancedSectionsComponent

__all__ = [
    'BaseComponent',
    'HeaderComponent',
    'SidebarComponent', 
    'UploadComponent',
    'SummaryCardsComponent',
    'VisualizationsComponent',
    'DataTableComponent',
    'EnhancedSectionsComponent'
]