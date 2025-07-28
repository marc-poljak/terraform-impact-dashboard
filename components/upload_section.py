"""
Upload Section Component for Terraform Plan Impact Dashboard

This component handles the file upload functionality, preserving the existing
upload styling with dashed border and help text.
"""

import streamlit as st
import json
from typing import Optional, Dict, Any, Tuple


class UploadComponent:
    """Component for handling Terraform plan file uploads"""
    
    def __init__(self):
        """Initialize the UploadComponent"""
        pass
    
    def render(self) -> Optional[Dict[str, Any]]:
        """
        Render the file upload section and return uploaded file data
        
        Returns:
            Optional[Dict[str, Any]]: The uploaded plan data as a dictionary,
                                    or None if no file is uploaded
        """
        # File upload section with preserved styling
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.markdown("### 📁 Upload Terraform Plan JSON")

        uploaded_file = st.file_uploader(
            "Choose a plan JSON file",
            type=['json'],
            help="Upload your Terraform plan JSON file. Generate it using: 'terraform plan -out=tfplan && terraform show -json tfplan > plan.json'. The file should contain a 'resource_changes' array with your planned infrastructure changes."
        )

        st.markdown('</div>', unsafe_allow_html=True)
        
        # Return the uploaded file data if available
        if uploaded_file is not None:
            return uploaded_file
        
        return None
    
    def validate_and_parse_file(self, uploaded_file, show_debug: bool = False) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate and parse the uploaded JSON file
        
        Args:
            uploaded_file: The uploaded file from Streamlit
            show_debug: Whether to show debug information on errors
            
        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[str]]: 
                (parsed_data, error_message) - parsed_data is None if error occurred
        """
        try:
            # Parse the uploaded file
            plan_data = json.load(uploaded_file)
            return plan_data, None
            
        except json.JSONDecodeError as e:
            error_msg = "❌ Invalid JSON file. Please upload a valid Terraform plan JSON file."
            if show_debug:
                st.error(error_msg)
                st.error(f"JSON Decode Error: {str(e)}")
            else:
                st.error(error_msg)
            return None, error_msg
            
        except Exception as e:
            error_msg = f"❌ Error processing file: {str(e)}"
            st.error(error_msg)
            st.info("Please ensure you're uploading a valid Terraform plan JSON file.")
            
            # Show error details in debug mode
            if show_debug:
                st.exception(e)
                
            return None, error_msg
    
    def render_instructions(self) -> None:
        """
        Render instructions when no file is uploaded
        """
        st.markdown("## 📖 Instructions")
        st.markdown("""
        1. **Upload your Terraform plan JSON file** using the file uploader above
        2. **View the change summary** with create/update/delete counts
        3. **Analyze risk levels** and resource type distributions
        4. **Explore interactive visualizations** to understand your infrastructure changes
        5. **Filter and export data** for further analysis
        """)