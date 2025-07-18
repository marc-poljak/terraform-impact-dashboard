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

    .debug-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Header
    st.markdown('<div class="main-header">🚀 Terraform Plan Impact Dashboard</div>', unsafe_allow_html=True)

    # Sidebar
    st.sidebar.title("📊 Dashboard Controls")
    st.sidebar.markdown("---")

    # Debug toggle
    show_debug = st.sidebar.checkbox("🔍 Show Debug Information", value=False)

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

                # Get debug info
                debug_info = parser.get_debug_info()

                # Risk assessment
                risk_assessor = RiskAssessment()
                risk_summary = risk_assessor.assess_plan_risk(resource_changes)

                # Chart generator
                chart_gen = ChartGenerator()

            # Display success message
            st.success("✅ Plan processed successfully!")

            # Debug Information Section
            if show_debug:
                st.markdown("## 🔍 Debug Information")
                st.markdown('<div class="debug-info">', unsafe_allow_html=True)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**📊 Parsing Details:**")
                    st.write(f"Total resource_changes in JSON: {debug_info['total_resource_changes']}")
                    st.write(f"Filtered resource_changes: {len(resource_changes)}")
                    st.write(f"Summary total: {summary['total']}")

                    # Fixed manual calculation logic
                    manual_create = manual_update = manual_delete = manual_total = 0
                    for change in parser.resource_changes:
                        actions = change.get('change', {}).get('actions', [])
                        if not actions or actions == ['no-op']:
                            continue

                        manual_total += 1  # Count each resource only once

                        if actions == ['create']:
                            manual_create += 1
                        elif actions == ['delete']:
                            manual_delete += 1
                        elif actions == ['update']:
                            manual_update += 1
                        elif set(actions) == {'create', 'delete'}:
                            # Replacement: count as both create and delete for action totals
                            manual_create += 1
                            manual_delete += 1

                    st.write(
                        f"Manual calculation: C:{manual_create} U:{manual_update} D:{manual_delete} T:{manual_total}")
                    st.write(
                        f"Actions total: {manual_create + manual_update + manual_delete} (includes replacement double-count)")

                with col2:
                    st.markdown("**🎯 Action Patterns:**")
                    for pattern, count in debug_info['action_patterns'].items():
                        st.write(f"`{pattern}`: {count} resources")

                st.markdown("**📁 Plan Structure:**")
                st.write(f"Has planned_values: {debug_info['has_planned_values']}")
                st.write(f"Has configuration: {debug_info['has_configuration']}")
                st.write(f"Has prior_state: {debug_info['has_prior_state']}")
                st.write(f"Plan keys: {', '.join(debug_info['plan_keys'])}")

                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")

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
                st.write(f"**Total Changes:** {summary['total']}")
                st.write(f"**Total Resources in Plan:** {debug_info['total_resource_changes']}")
                st.write(f"**Terraform Version:** {plan_data.get('terraform_version', 'Unknown')}")
                st.write(f"**Plan Format:** {plan_data.get('format_version', 'Unknown')}")

            with col2:
                st.markdown("### ⚠️ Risk Analysis")
                st.write(f"**Risk Level:** {risk_summary['level']}")
                st.write(f"**Risk Score:** {risk_summary['score']}/100")
                st.write(f"**High Risk Resources:** {risk_summary['high_risk_count']}")
                st.write(f"**Estimated Time:** {risk_summary.get('estimated_time', 'Unknown')}")

            with col3:
                st.markdown("### 📋 Resource Types")
                st.write(f"**Unique Types:** {len(resource_types)}")
                if resource_types:
                    top_types = dict(sorted(resource_types.items(), key=lambda x: x[1], reverse=True)[:3])
                    for rtype, count in top_types.items():
                        st.write(f"**{rtype}:** {count}")
                else:
                    st.write("No resource types found")

            # Only show visualizations if we have data
            if summary['total'] > 0:
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
                    if risk_by_type:
                        fig_risk = chart_gen.create_risk_heatmap(risk_by_type)
                        st.plotly_chart(fig_risk, use_container_width=True)
                    else:
                        st.info("No risk data available")

                # Resource Details Table
                st.markdown("---")
                st.markdown("## 📋 Resource Change Details")

                # Filters in sidebar
                st.sidebar.markdown("### 🔍 Filters")

                # Action filter
                action_filter = st.sidebar.multiselect(
                    "Filter by Action",
                    options=['create', 'update', 'delete', 'replace'],
                    default=['create', 'update', 'delete', 'replace']
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
                    if not filtered_df.empty:
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
                    else:
                        st.info("No resources match the current filters.")
                else:
                    st.info("No resource changes found in the plan.")

            else:
                st.info("🎉 No changes detected in this plan! All resources are up to date.")

            # Footer
            st.markdown("---")
            st.markdown("### 📚 Summary")

            if summary['total'] > 0:
                recommendations = risk_assessor.generate_recommendations(resource_changes)

                st.info(f"""
                **Plan Summary:**
                - Total changes: {summary['total']} resources
                - Risk level: {risk_summary['level']} ({risk_summary['score']}/100)
                - Estimated deployment time: {risk_summary.get('estimated_time', 'Unknown')}
                - Recommended action: {'Proceed with caution' if risk_summary['level'] == 'High' else 'Safe to deploy'}
                """)

                if recommendations:
                    st.markdown("**🎯 Recommendations:**")
                    for rec in recommendations:
                        st.write(f"- {rec}")
            else:
                st.success("✅ No changes required - your infrastructure is up to date!")

        except json.JSONDecodeError:
            st.error("❌ Invalid JSON file. Please upload a valid Terraform plan JSON file.")
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please ensure you're uploading a valid Terraform plan JSON file.")

            # Show error details in debug mode
            if show_debug:
                st.exception(e)

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
        - **Debug Mode**: Toggle in sidebar to see parsing details
        """)

        # Sample data section
        st.markdown("### 🧪 Want to test with sample data?")
        if st.button("🔧 Generate Sample Plan Data"):
            sample_data = {
                "terraform_version": "1.3.0",
                "format_version": "1.0",
                "resource_changes": [
                    {
                        "address": "aws_instance.web[0]",
                        "type": "aws_instance",
                        "name": "web",
                        "change": {
                            "actions": ["create"],
                            "before": None,
                            "after": {"instance_type": "t3.micro"}
                        }
                    },
                    {
                        "address": "aws_instance.web[1]",
                        "type": "aws_instance",
                        "name": "web",
                        "change": {
                            "actions": ["create"],
                            "before": None,
                            "after": {"instance_type": "t3.micro"}
                        }
                    },
                    {
                        "address": "aws_security_group.web",
                        "type": "aws_security_group",
                        "name": "web",
                        "change": {
                            "actions": ["update"],
                            "before": {"ingress": []},
                            "after": {"ingress": [{"from_port": 80}]}
                        }
                    },
                    {
                        "address": "aws_s3_bucket.old_bucket",
                        "type": "aws_s3_bucket",
                        "name": "old_bucket",
                        "change": {
                            "actions": ["delete"],
                            "before": {"bucket": "my-old-bucket"},
                            "after": None
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