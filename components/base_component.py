"""
Base Component Class

Provides common functionality for all dashboard UI components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import streamlit as st


class BaseComponent(ABC):
    """Abstract base class for all dashboard components"""
    
    def __init__(self, session_manager: Optional[Any] = None):
        """
        Initialize the component
        
        Args:
            session_manager: Optional session state manager for component state
        """
        self.session_manager = session_manager
        
    @abstractmethod
    def render(self, *args, **kwargs) -> Any:
        """
        Render the component
        
        This method must be implemented by all component subclasses.
        
        Returns:
            Component-specific return value (data, state, etc.)
        """
        pass
        
    def _get_session_state(self, key: str, default: Any = None) -> Any:
        """
        Get a value from Streamlit session state
        
        Args:
            key: Session state key
            default: Default value if key doesn't exist
            
        Returns:
            Value from session state or default
        """
        return st.session_state.get(key, default)
        
    def _set_session_state(self, key: str, value: Any) -> None:
        """
        Set a value in Streamlit session state
        
        Args:
            key: Session state key
            value: Value to set
        """
        st.session_state[key] = value
        
    def _render_error(self, message: str, details: Optional[str] = None) -> None:
        """
        Render an error message with optional details
        
        Args:
            message: Main error message
            details: Optional detailed error information
        """
        st.error(f"❌ {message}")
        if details:
            with st.expander("Error Details"):
                st.text(details)
                
    def _render_warning(self, message: str) -> None:
        """
        Render a warning message
        
        Args:
            message: Warning message
        """
        st.warning(f"⚠️ {message}")
        
    def _render_info(self, message: str) -> None:
        """
        Render an info message
        
        Args:
            message: Info message
        """
        st.info(f"ℹ️ {message}")
        
    def _render_success(self, message: str) -> None:
        """
        Render a success message
        
        Args:
            message: Success message
        """
        st.success(f"✅ {message}")