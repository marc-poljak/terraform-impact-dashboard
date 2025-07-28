"""
Header component for the Terraform Plan Impact Dashboard.

This component handles the main header display and CSS styling management.
"""

import streamlit as st


class HeaderComponent:
    """Component responsible for rendering the main dashboard header."""
    
    def __init__(self):
        """Initialize the HeaderComponent."""
        pass
    
    def render(self):
        """
        Render the main header with the dashboard title.
        
        This method outputs the existing header styling and preserves
        the current "🚀 Terraform Plan Impact Dashboard" header.
        """
        st.markdown(
            '<div class="main-header">🚀 Terraform Plan Impact Dashboard</div>', 
            unsafe_allow_html=True
        )
    
    def render_css(self):
        """
        Render all CSS styling for the dashboard.
        
        This method contains all the CSS styles extracted from app.py,
        including multi-cloud styling classes (.provider-aws, .provider-azure, etc.)
        """
        css_styles = """
        <style>
            .main-header {
                font-size: 2.5rem;
                font-weight: bold;
                color: #1f77b4;
                text-align: center;
                margin-bottom: 2rem;
            }

            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem;
                border-radius: 10px;
                color: white;
                text-align: center;
                margin: 0.5rem;
            }

            .risk-low {
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            }

            .risk-medium {
                background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
            }

            .risk-high {
                background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);
            }

            .provider-aws {
                background: linear-gradient(135deg, #FF9900 0%, #CC7A00 100%);
            }

            .provider-azure {
                background: linear-gradient(135deg, #0078D4 0%, #005A9F 100%);
            }

            .provider-google {
                background: linear-gradient(135deg, #4285F4 0%, #3367D6 100%);
            }

            .upload-section {
                border: 2px dashed #1f77b4;
                border-radius: 10px;
                padding: 2rem;
                text-align: center;
                background-color: #f8f9fa;
                margin-bottom: 2rem;
            }

            .debug-info {
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 5px;
                border-left: 4px solid #17a2b8;
                margin: 1rem 0;
            }

            .multi-cloud-alert {
                background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                color: white;
                padding: 1rem;
                border-radius: 10px;
                margin: 1rem 0;
                text-align: center;
            }

            .feature-unavailable {
                background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
                color: white;
                padding: 0.5rem;
                border-radius: 5px;
                margin: 0.5rem 0;
                text-align: center;
                font-size: 0.9rem;
            }
        </style>
        """
        
        st.markdown(css_styles, unsafe_allow_html=True)