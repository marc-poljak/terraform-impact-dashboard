import streamlit as st
import pandas as pd
import json
import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parsers.plan_parser import PlanParser
from visualizers.charts import ChartGenerator
from utils.risk_assessment import RiskAssessment

# Page configuration
st.set_page_config(
    page_title="Terraform Plan Impact Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
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

    .upload-section {
        border: 2px dashed #1f77b4;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Header
    st.markdown('<div class="main-header">🚀 Terraform Plan Impact Dashboard</div>', unsafe_allow_html=True)

    # Sidebar
    st.sidebar.title("📊 Dashboard Controls")
    st.sidebar.markdown("---")

    # File upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("### 📁 Upload Terraform Plan JSON")

    uploaded_file = st.file_uploader(
        "Choose a plan JSON file",
        type=['json'],
        help="Upload your Terraform plan JSON file (plan-{id}-structured-output.json)"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        try:
            # Show loading spinner
            with st.spinner('🔄 Processing Terraform plan...'):
                # Parse the uploaded file
                plan_data = json.load(uploaded_file)
                parser = PlanParser(plan_data)

                # Extract metrics
                summary = parser.get_summary()
                resource_changes = parser.get_resource_changes()
                resource_types = parser.get_resource_types()

                # Risk assessment
                risk_assessor = RiskAssessment()
                risk_summary = risk_assessor.assess_plan_risk(resource_changes)

                # Chart generator
                chart_gen = ChartGenerator()

            # Display success message
            st.success("✅ Plan processed successfully!")

            # Summary Cards Section
            st.markdown("## 📊 Change Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="🟢 Create",
                    value=summary['create'],
                    delta=f"{summary['create']} resources"
                )

            with col2:
                st.metric(
                    label="🔵 Update",
                    value=summary['update'],
                    delta=f"{summary['update']} resources"
                )

            with col3:
                st.metric(
                    label="🔴 Delete",
                    value=summary['delete'],
                    delta=f"{summary['delete']} resources"
                )

            with col4:
                risk_color = "🟢" if risk_summary['level'] == "Low" else "🟡" if risk_summary[
                                                                                   'level'] == "Medium" else "🔴"
                st.metric(
                    label=f"{risk_color} Risk Level",
                    value=risk_summary['level'],
                    delta=f"Score: {risk_summary['score']}"
                )

            # Detailed metrics
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### 📈 Plan Details")
                st.write(f"**Total Resources:** {summary['total']}")
                st.write(f"**Terraform Version:** {plan_data.get('terraform_version', 'Unknown')}")
                st.write(f"**Plan Format:** {plan_data.get('format_version', 'Unknown')}")

            with col2:
                st.markdown("### ⚠️ Risk Analysis")
                st.write(f"**Risk Level:** {risk_summary['level']}")
                st.write(f"**Risk Score:** {risk_summary['score']}/100")
                st.write(f"**High Risk Resources:** {risk_summary['high_risk_count']}")

            with col3:
                st.markdown("### 📋 Resource Types")
                st.write(f"**Unique Types:** {len(resource_types)}")
                top_types = dict(sorted(resource_types.items(), key=lambda x: x[1], reverse=True)[:3])
                for rtype, count in top_types.items():
                    st.write(f"**{rtype}:** {count}")

            # Visualizations Section
            st.markdown("---")
            st.markdown("## 📈 Visualizations")

            # Two columns for charts
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🏷️ Resource Types Distribution")
                if resource_types:
                    fig_pie = chart_gen.create_resource_type_pie(resource_types)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No resource type data available")

            with col2:
                st.markdown("### 🔄 Change Actions")
                fig_bar = chart_gen.create_change_actions_bar(summary)
                st.plotly_chart(fig_bar, use_container_width=True)

            # Risk Assessment Chart
            st.markdown("### ⚠️ Risk Assessment by Resource Type")
            if resource_changes:
                risk_by_type = risk_assessor.get_risk_by_resource_type(resource_changes)
                fig_risk = chart_gen.create_risk_heatmap(risk_by_type)
                st.plotly_chart(fig_risk, use_container_width=True)

            # Resource Details Table
            st.markdown("---")
            st.markdown("## 📋 Resource Change Details")

            # Filters in sidebar
            st.sidebar.markdown("### 🔍 Filters")

            # Action filter
            action_filter = st.sidebar.multiselect(
                "Filter by Action",
                options=['create', 'update', 'delete'],
                default=['create', 'update', 'delete']
            )

            # Risk filter
            risk_filter = st.sidebar.multiselect(
                "Filter by Risk Level",
                options=['Low', 'Medium', 'High'],
                default=['Low', 'Medium', 'High']
            )

            # Create detailed dataframe
            if resource_changes:
                detailed_df = parser.create_detailed_dataframe(resource_changes)

                # Add risk assessment to dataframe
                detailed_df['risk_level'] = detailed_df.apply(
                    lambda row: risk_assessor.assess_resource_risk({
                        'type': row['resource_type'],
                        'change': {'actions': [row['action']]}
                    })['level'], axis=1
                )

                # Apply filters
                filtered_df = detailed_df[
                    (detailed_df['action'].isin(action_filter)) &
                    (detailed_df['risk_level'].isin(risk_filter))
                    ]

                # Display table
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    column_config={
                        "action": st.column_config.TextColumn(
                            "Action",
                            width="small"
                        ),
                        "resource_type": st.column_config.TextColumn(
                            "Resource Type",
                            width="medium"
                        ),
                        "resource_name": st.column_config.TextColumn(
                            "Resource Name",
                            width="large"
                        ),
                        "risk_level": st.column_config.TextColumn(
                            "Risk Level",
                            width="small"
                        )
                    }
                )

                # Download button for filtered data
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Data as CSV",
                    data=csv,
                    file_name="terraform_plan_changes.csv",
                    mime="text/csv"
                )

            # Footer
            st.markdown("---")
            st.markdown("### 📚 Summary")
            st.info(f"""
            **Plan Summary:**
            - Total changes: {summary['total']} resources
            - Risk level: {risk_summary['level']} ({risk_summary['score']}/100)
            - Estimated deployment time: {risk_summary.get('estimated_time', 'Unknown')}
            - Recommended action: {'Proceed with caution' if risk_summary['level'] == 'High' else 'Safe to deploy'}
            """)

        except json.JSONDecodeError:
            st.error("❌ Invalid JSON file. Please upload a valid Terraform plan JSON file.")
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please ensure you're uploading a valid Terraform plan JSON file.")

    else:
        # Show instructions when no file is uploaded
        st.markdown("## 📖 Instructions")
        st.markdown("""
        1. **Upload your Terraform plan JSON file** using the file uploader above
        2. **View the change summary** with create/update/delete counts
        3. **Analyze risk levels** and resource type distributions
        4. **Explore interactive visualizations** to understand your infrastructure changes
        5. **Filter and export** detailed resource change data

        ### 📁 Expected File Format
        Upload files with naming pattern: `plan-{id}-structured-output.json`

        ### 🎯 Dashboard Features
        - **Summary Cards**: Quick overview of planned changes
        - **Risk Assessment**: Automatic risk scoring based on resource types and actions
        - **Interactive Charts**: Visualize resource distributions and change patterns
        - **Detailed Tables**: Filterable list of all resource changes
        - **Data Export**: Download filtered results as CSV
        """)

        # Sample data section
        st.markdown("### 🧪 Want to test with sample data?")
        if st.button("🔧 Generate Sample Plan Data"):
            sample_data = {
                "terraform_version": "1.3.0",
                "format_version": "1.0",
                "resource_changes": [
                    {
                        "address": "aws_instance.web",
                        "type": "aws_instance",
                        "change": {
                            "actions": ["create"],
                            "before": None,
                            "after": {"instance_type": "t3.micro"}
                        }
                    },
                    {
                        "address": "aws_security_group.web",
                        "type": "aws_security_group",
                        "change": {
                            "actions": ["update"],
                            "before": {"ingress": []},
                            "after": {"ingress": [{"from_port": 80}]}
                        }
                    }
                ]
            }

            # Create downloadable sample file
            sample_json = json.dumps(sample_data, indent=2)
            st.download_button(
                label="📥 Download Sample Plan JSON",
                data=sample_json,
                file_name="sample-plan-structured-output.json",
                mime="application/json"
            )


if __name__ == "__main__":
    main()