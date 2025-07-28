"""
Base Component Class

Provides common functionality for all dashboard UI components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
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
        
    def _render_error(self, message: str, details: Optional[str] = None, 
                     suggestions: Optional[List[str]] = None, context: str = "component") -> None:
        """
        Render an enhanced error message with actionable guidance
        
        Args:
            message: Main error message
            details: Optional detailed error information
            suggestions: Optional list of suggestions to fix the error
            context: Context where the error occurred
        """
        from ui.error_handler import ErrorHandler
        
        # Use enhanced error handler if available
        try:
            error_handler = ErrorHandler()
            if context == "visualization":
                error_handler.handle_visualization_error(Exception(details or message), message.lower())
            elif context == "processing":
                error_handler.handle_processing_error(Exception(details or message), message.lower())
            else:
                # Fallback to basic error display with enhancements
                st.error(f"❌ **{message}**")
                
                if details:
                    with st.expander("🔍 **Error Details**", expanded=False):
                        st.text(details)
                
                if suggestions:
                    with st.expander("💡 **Suggested Solutions**", expanded=True):
                        for suggestion in suggestions:
                            st.write(f"• {suggestion}")
                else:
                    st.info("💡 **Next Steps:** Try refreshing the page or using different settings. Other dashboard features remain available.")
        except ImportError:
            # Fallback to basic error display
            st.error(f"❌ {message}")
            if details:
                with st.expander("Error Details"):
                    st.text(details)
                
    def _render_warning(self, message: str, help_text: Optional[str] = None) -> None:
        """
        Render an enhanced warning message with optional help
        
        Args:
            message: Warning message
            help_text: Optional help text to show in expander
        """
        st.warning(f"⚠️ **{message}**")
        if help_text:
            with st.expander("💡 **More Information**", expanded=False):
                st.markdown(help_text)
        
    def _render_info(self, message: str, tooltip: Optional[str] = None) -> None:
        """
        Render an enhanced info message with optional tooltip
        
        Args:
            message: Info message
            tooltip: Optional tooltip text
        """
        if tooltip:
            st.info(f"ℹ️ **{message}**")
            st.caption(tooltip)
        else:
            st.info(f"ℹ️ {message}")
        
    def _render_success(self, message: str, details: Optional[str] = None) -> None:
        """
        Render an enhanced success message with optional details
        
        Args:
            message: Success message
            details: Optional additional details
        """
        st.success(f"✅ **{message}**")
        if details:
            st.caption(details)
    
    def _show_contextual_help(self, feature_name: str, help_content: dict) -> None:
        """
        Show contextual help for component features
        
        Args:
            feature_name: Name of the feature
            help_content: Dictionary with help information
        """
        try:
            from ui.error_handler import ErrorHandler
            error_handler = ErrorHandler()
            error_handler.show_contextual_help(feature_name, help_content)
        except ImportError:
            # Fallback help display
            if help_content.get('quick_tip'):
                st.info(f"💡 {help_content['quick_tip']}")
            if help_content.get('detailed_help'):
                with st.expander(f"❓ Learn more about {feature_name}"):
                    st.markdown(help_content['detailed_help'])
    
    def _show_feature_tooltip(self, feature_name: str, tooltip_text: str, tooltip_type: str = "info") -> None:
        """
        Show tooltip for component features
        
        Args:
            feature_name: Name of the feature
            tooltip_text: Tooltip content
            tooltip_type: Type of tooltip
        """
        try:
            from ui.error_handler import ErrorHandler
            error_handler = ErrorHandler()
            error_handler.show_feature_tooltip(feature_name, tooltip_text, tooltip_type)
        except ImportError:
            # Fallback tooltip display
            if tooltip_type == "warning":
                st.warning(f"⚠️ **{feature_name}:** {tooltip_text}")
            elif tooltip_type == "success":
                st.success(f"✅ **{feature_name}:** {tooltip_text}")
            else:
                st.info(f"💡 **{feature_name}:** {tooltip_text}")