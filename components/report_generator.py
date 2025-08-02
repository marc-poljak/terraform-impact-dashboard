"""
Report Generator Component

Handles the generation of comprehensive reports for Terraform Plan Impact Dashboard.
Implements enhanced reporting capabilities as specified in requirements 5.1, 5.2, and 5.3.
"""

from typing import Dict, Any, Optional, List
import streamlit as st
from datetime import datetime
import json
import base64
import tempfile
import os
from io import BytesIO
from jinja2 import Template
from .base_component import BaseComponent

# Import enhanced PDF generator
try:
    from .enhanced_pdf_generator import EnhancedPDFGenerator
    PDF_GENERATOR_AVAILABLE = True
except ImportError as e:
    PDF_GENERATOR_AVAILABLE = False
    PDF_GENERATOR_ERROR = str(e)


class ReportGeneratorComponent(BaseComponent):
    """Component for generating comprehensive reports with executive summary, risk analysis, and detailed changes"""
    
    def __init__(self, session_manager: Optional[Any] = None):
        """
        Initialize the ReportGeneratorComponent
        
        Args:
            session_manager: Optional session state manager
        """
        super().__init__(session_manager)
        self.session_manager = session_manager
        self.report_sections = {
            'executive_summary': True,
            'risk_analysis': True,
            'detailed_changes': True,
            'visualizations': True,
            'resource_breakdown': True,
            'recommendations': True
        }
        
        # Initialize enhanced PDF generator
        if PDF_GENERATOR_AVAILABLE:
            self.pdf_generator = EnhancedPDFGenerator()
        else:
            self.pdf_generator = None
    
    def generate_executive_summary(self, 
                                 summary: Dict[str, int], 
                                 risk_summary: Dict[str, Any],
                                 plan_data: Dict[str, Any]) -> str:
        """
        Generate executive summary section for the report
        
        Args:
            summary: Change summary with create/update/delete counts
            risk_summary: Risk assessment results
            plan_data: Original plan data
            
        Returns:
            HTML string containing the executive summary
        """
        # Calculate total if not present
        if 'total' not in summary:
            summary['total'] = summary.get('create', 0) + summary.get('update', 0) + summary.get('delete', 0) + summary.get('no-op', 0)
        
        # Extract risk information
        if isinstance(risk_summary, dict) and 'overall_risk' in risk_summary:
            risk_level = risk_summary['overall_risk'].get('level', 'Unknown')
            risk_score = risk_summary['overall_risk'].get('score', 0)
            estimated_time = risk_summary['overall_risk'].get('estimated_time', 'Unknown')
            high_risk_count = risk_summary['overall_risk'].get('high_risk_count', 0)
        else:
            risk_level = risk_summary.get('level', 'Unknown')
            risk_score = risk_summary.get('score', 0)
            estimated_time = risk_summary.get('estimated_time', 'Unknown')
            high_risk_count = risk_summary.get('high_risk_count', 0)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine deployment recommendation
        if risk_level in ['Low', 'Medium']:
            recommendation = "✅ Recommended for deployment with standard review process"
            recommendation_class = "success"
        elif risk_level == 'High':
            recommendation = "⚠️ Requires careful review and testing before deployment"
            recommendation_class = "warning"
        else:
            recommendation = "🚨 High-risk deployment - requires thorough review and approval"
            recommendation_class = "danger"
        
        return f"""
        <div class="executive-summary">
            <h2>📋 Executive Summary</h2>
            <div class="summary-header">
                <p><strong>Report Generated:</strong> {timestamp}</p>
                <p><strong>Terraform Version:</strong> {plan_data.get('terraform_version', 'Unknown')}</p>
                {self._get_tfe_metadata_html()}
            </div>
            
            <div class="key-metrics">
                <h3>Key Metrics</h3>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{summary['total']}</div>
                        <div class="metric-label">Total Changes</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{risk_level}</div>
                        <div class="metric-label">Risk Level</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{risk_score}/100</div>
                        <div class="metric-label">Risk Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{estimated_time}</div>
                        <div class="metric-label">Est. Deployment Time</div>
                    </div>
                </div>
            </div>
            
            <div class="change-breakdown">
                <h3>Change Breakdown</h3>
                <ul>
                    <li><strong>Create:</strong> {summary['create']} new resources will be provisioned</li>
                    <li><strong>Update:</strong> {summary['update']} existing resources will be modified</li>
                    <li><strong>Delete:</strong> {summary['delete']} resources will be removed</li>
                </ul>
            </div>
            
            <div class="deployment-recommendation {recommendation_class}">
                <h3>Deployment Recommendation</h3>
                <p>{recommendation}</p>
                {f'<p><strong>High-risk resources identified:</strong> {high_risk_count}</p>' if high_risk_count > 0 else ''}
            </div>
        </div>
        """
    
    def _get_tfe_metadata_html(self) -> str:
        """
        Generate HTML for TFE metadata if plan comes from TFE integration
        
        Returns:
            HTML string with TFE metadata or empty string if not from TFE
        """
        if not self.session_manager:
            return ""
        
        try:
            plan_manager = self.session_manager.get_plan_manager()
            metadata = plan_manager.get_plan_metadata()
            
            if not metadata or metadata.source != "tfe_integration":
                return ""
            
            # Generate masked IDs for security
            masked_workspace = self._mask_id_for_report(metadata.workspace_id) if metadata.workspace_id else "N/A"
            masked_run = self._mask_id_for_report(metadata.run_id) if metadata.run_id else "N/A"
            
            return f"""
                <div class="tfe-metadata">
                    <h4>🔗 Terraform Cloud/Enterprise Information</h4>
                    <p><strong>Data Source:</strong> TFE Integration</p>
                    <p><strong>Workspace ID:</strong> {masked_workspace}</p>
                    <p><strong>Run ID:</strong> {masked_run}</p>
                    <p><em>Note: IDs are masked for security. Plan data retrieved via secure API connection.</em></p>
                </div>
            """
        except Exception:
            # Return empty string if any error occurs
            return ""
    
    def _mask_id_for_report(self, id_value: str) -> str:
        """
        Mask ID for safe display in reports (same logic as SecurePlanManager)
        
        Args:
            id_value: ID to mask
            
        Returns:
            Masked ID string
        """
        if not id_value or len(id_value) <= 8:
            return '*' * len(id_value) if id_value else ''
        
        # Show prefix and suffix, mask the middle
        return f"{id_value[:4]}{'*' * (len(id_value) - 8)}{id_value[-4:]}"

    def generate_risk_analysis(self, 
                             risk_summary: Dict[str, Any],
                             resource_changes: List[Dict],
                             enhanced_risk_assessor: Optional[Any] = None) -> str:
        """
        Generate detailed risk analysis section
        
        Args:
            risk_summary: Risk assessment results
            resource_changes: List of resource changes
            enhanced_risk_assessor: Enhanced risk assessor instance (optional)
            
        Returns:
            HTML string containing the risk analysis
        """
        # Extract risk information
        if isinstance(risk_summary, dict) and 'overall_risk' in risk_summary:
            risk_level = risk_summary['overall_risk'].get('level', 'Unknown')
            risk_score = risk_summary['overall_risk'].get('score', 0)
            risk_factors = risk_summary['overall_risk'].get('risk_factors', [])
        else:
            risk_level = risk_summary.get('level', 'Unknown')
            risk_score = risk_summary.get('score', 0)
            risk_factors = risk_summary.get('risk_factors', [])
        
        # Generate risk breakdown by resource type
        risk_by_type = {}
        for change in resource_changes:
            resource_type = change.get('type', 'unknown')
            action = change.get('change', {}).get('actions', ['unknown'])[0]
            
            if resource_type not in risk_by_type:
                risk_by_type[resource_type] = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            
            # Simple risk scoring based on action type
            if action == 'delete':
                risk_by_type[resource_type]['high'] += 1
            elif action == 'update':
                risk_by_type[resource_type]['medium'] += 1
            else:
                risk_by_type[resource_type]['low'] += 1
        
        # Generate risk factors list
        risk_factors_html = ""
        if risk_factors:
            risk_factors_html = "<ul>"
            for factor in risk_factors:
                risk_factors_html += f"<li>{factor}</li>"
            risk_factors_html += "</ul>"
        else:
            risk_factors_html = "<p>No specific risk factors identified.</p>"
        
        # Generate resource type risk table
        risk_table_html = "<table class='risk-table'><thead><tr><th>Resource Type</th><th>Low Risk</th><th>Medium Risk</th><th>High Risk</th><th>Critical Risk</th></tr></thead><tbody>"
        for rtype, risks in risk_by_type.items():
            risk_table_html += f"""
            <tr>
                <td>{rtype}</td>
                <td class="risk-low">{risks['low']}</td>
                <td class="risk-medium">{risks['medium']}</td>
                <td class="risk-high">{risks['high']}</td>
                <td class="risk-critical">{risks['critical']}</td>
            </tr>
            """
        risk_table_html += "</tbody></table>"
        
        return f"""
        <div class="risk-analysis">
            <h2>⚠️ Risk Analysis</h2>
            
            <div class="overall-risk">
                <h3>Overall Risk Assessment</h3>
                <div class="risk-score-display">
                    <div class="risk-level risk-{risk_level.lower()}">{risk_level}</div>
                    <div class="risk-score">{risk_score}/100</div>
                </div>
            </div>
            
            <div class="risk-factors">
                <h3>Risk Factors</h3>
                {risk_factors_html}
            </div>
            
            <div class="risk-breakdown">
                <h3>Risk Breakdown by Resource Type</h3>
                {risk_table_html}
            </div>
            
            <div class="mitigation-strategies">
                <h3>Risk Mitigation Strategies</h3>
                <ul>
                    <li><strong>Pre-deployment Testing:</strong> Test changes in a staging environment</li>
                    <li><strong>Backup Strategy:</strong> Ensure backups are current before deployment</li>
                    <li><strong>Rollback Plan:</strong> Have a rollback strategy ready</li>
                    <li><strong>Monitoring:</strong> Monitor resources closely after deployment</li>
                    {'<li><strong>Phased Deployment:</strong> Consider deploying high-risk changes separately</li>' if risk_level in ['High', 'Critical'] else ''}
                </ul>
            </div>
        </div>
        """
    
    def generate_detailed_changes(self, 
                                resource_changes: List[Dict],
                                resource_types: Dict[str, int]) -> str:
        """
        Generate detailed changes section
        
        Args:
            resource_changes: List of resource changes
            resource_types: Dictionary of resource types and counts
            
        Returns:
            HTML string containing detailed changes
        """
        # Group changes by action type
        changes_by_action = {'create': [], 'update': [], 'delete': []}
        
        for change in resource_changes:
            action = change.get('change', {}).get('actions', ['unknown'])[0]
            if action in changes_by_action:
                changes_by_action[action].append(change)
        
        # Generate changes tables
        changes_html = ""
        
        for action, changes in changes_by_action.items():
            if not changes:
                continue
                
            action_icon = {'create': '🟢', 'update': '🔵', 'delete': '🔴'}.get(action, '⚪')
            action_title = action.title()
            
            changes_html += f"""
            <div class="changes-section">
                <h3>{action_icon} {action_title} Operations ({len(changes)} resources)</h3>
                <table class="changes-table">
                    <thead>
                        <tr>
                            <th>Resource Address</th>
                            <th>Resource Type</th>
                            <th>Provider</th>
                            <th>Key Changes</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for change in changes[:50]:  # Limit to first 50 for readability
                address = change.get('address', 'Unknown')
                resource_type = change.get('type', 'Unknown')
                provider = change.get('provider_name', 'Unknown').split('/')[-1] if change.get('provider_name') else 'Unknown'
                
                # Extract key changes
                change_data = change.get('change', {})
                before = change_data.get('before')
                after = change_data.get('after')
                
                key_changes = []
                if action == 'create':
                    key_changes.append("New resource")
                elif action == 'delete':
                    key_changes.append("Resource removal")
                elif action == 'update' and before and after:
                    # Try to identify key changed fields
                    if isinstance(before, dict) and isinstance(after, dict):
                        for key in after.keys():
                            if key in before and before[key] != after[key]:
                                key_changes.append(f"{key} modified")
                        if not key_changes:
                            key_changes.append("Configuration updated")
                
                key_changes_str = ", ".join(key_changes[:3]) if key_changes else "No details available"
                
                changes_html += f"""
                <tr>
                    <td><code>{address}</code></td>
                    <td>{resource_type}</td>
                    <td>{provider}</td>
                    <td>{key_changes_str}</td>
                </tr>
                """
            
            if len(changes) > 50:
                changes_html += f"""
                <tr>
                    <td colspan="4" class="truncated-notice">
                        ... and {len(changes) - 50} more {action} operations
                    </td>
                </tr>
                """
            
            changes_html += "</tbody></table></div>"
        
        # Generate resource type summary
        resource_summary_html = """
        <div class="resource-summary">
            <h3>📊 Resource Type Summary</h3>
            <table class="resource-summary-table">
                <thead>
                    <tr><th>Resource Type</th><th>Count</th><th>Percentage</th></tr>
                </thead>
                <tbody>
        """
        
        total_resources = sum(resource_types.values())
        for rtype, count in sorted(resource_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_resources * 100) if total_resources > 0 else 0
            resource_summary_html += f"""
            <tr>
                <td>{rtype}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
            """
        
        resource_summary_html += "</tbody></table></div>"
        
        return f"""
        <div class="detailed-changes">
            <h2>📋 Detailed Changes</h2>
            {resource_summary_html}
            {changes_html}
        </div>
        """
    
    def generate_recommendations(self, 
                               summary: Dict[str, int],
                               risk_summary: Dict[str, Any],
                               resource_changes: List[Dict],
                               enhanced_risk_assessor: Optional[Any] = None) -> str:
        """
        Generate recommendations section
        
        Args:
            summary: Change summary
            risk_summary: Risk assessment results
            resource_changes: List of resource changes
            enhanced_risk_assessor: Enhanced risk assessor instance (optional)
            
        Returns:
            HTML string containing recommendations
        """
        # Calculate total if not present
        if 'total' not in summary:
            summary['total'] = summary.get('create', 0) + summary.get('update', 0) + summary.get('delete', 0) + summary.get('no-op', 0)
        
        recommendations = []
        
        # Generate recommendations based on risk level
        if isinstance(risk_summary, dict) and 'overall_risk' in risk_summary:
            risk_level = risk_summary['overall_risk'].get('level', 'Unknown')
        else:
            risk_level = risk_summary.get('level', 'Unknown')
        
        # Risk-based recommendations
        if risk_level == 'Critical':
            recommendations.extend([
                "🚨 **Critical Risk Deployment** - Requires senior approval and extensive testing",
                "🔄 Consider breaking this deployment into smaller, incremental changes",
                "🧪 Mandatory staging environment testing before production deployment",
                "📋 Prepare detailed rollback procedures and test them",
                "👥 Have multiple team members review the changes"
            ])
        elif risk_level == 'High':
            recommendations.extend([
                "⚠️ **High Risk Deployment** - Requires careful review and testing",
                "🧪 Test thoroughly in staging environment",
                "📋 Prepare rollback procedures",
                "📊 Monitor resources closely after deployment"
            ])
        elif risk_level == 'Medium':
            recommendations.extend([
                "🔍 **Medium Risk Deployment** - Standard review process recommended",
                "🧪 Test in staging environment if possible",
                "📊 Monitor key resources after deployment"
            ])
        else:
            recommendations.extend([
                "✅ **Low Risk Deployment** - Standard deployment process",
                "📊 Basic monitoring recommended after deployment"
            ])
        
        # Change-specific recommendations
        if summary['delete'] > 0:
            recommendations.append(f"🗑️ **Resource Deletion** - {summary['delete']} resources will be deleted. Ensure data backup if needed")
        
        if summary['create'] > summary['update'] + summary['delete']:
            recommendations.append("🆕 **Resource Creation Heavy** - Verify resource quotas and limits")
        
        if summary['total'] > 50:
            recommendations.append("📊 **Large Deployment** - Consider phased deployment approach")
        
        # Security recommendations
        security_resources = [change for change in resource_changes 
                            if any(sec_type in change.get('type', '').lower() 
                                  for sec_type in ['security_group', 'iam', 'policy', 'role', 'key'])]
        
        if security_resources:
            recommendations.append(f"🔒 **Security Resources** - {len(security_resources)} security-related resources detected. Review permissions carefully")
        
        # Generate HTML
        recommendations_html = "<ul>"
        for rec in recommendations:
            recommendations_html += f"<li>{rec}</li>"
        recommendations_html += "</ul>"
        
        return f"""
        <div class="recommendations">
            <h2>💡 Recommendations</h2>
            <div class="recommendations-content">
                {recommendations_html}
            </div>
            
            <div class="best-practices">
                <h3>🎯 Deployment Best Practices</h3>
                <ul>
                    <li><strong>Plan Review:</strong> Have team members review this plan before deployment</li>
                    <li><strong>Backup Strategy:</strong> Ensure current backups of critical resources</li>
                    <li><strong>Monitoring:</strong> Set up monitoring for new and modified resources</li>
                    <li><strong>Documentation:</strong> Document any manual steps required post-deployment</li>
                    <li><strong>Communication:</strong> Notify stakeholders of planned changes and timeline</li>
                </ul>
            </div>
        </div>
        """
    

    
    def generate_full_report(self,
                           summary: Dict[str, int],
                           risk_summary: Dict[str, Any],
                           resource_changes: List[Dict],
                           resource_types: Dict[str, int],
                           plan_data: Dict[str, Any],
                           enhanced_risk_assessor: Optional[Any] = None,
                           include_sections: Optional[Dict[str, bool]] = None) -> str:
        """
        Generate a complete HTML report
        
        Args:
            summary: Change summary
            risk_summary: Risk assessment results
            resource_changes: List of resource changes
            resource_types: Dictionary of resource types and counts
            plan_data: Original plan data
            enhanced_risk_assessor: Enhanced risk assessor instance (optional)
            include_sections: Dictionary specifying which sections to include
            
        Returns:
            Complete HTML report string
        """
        if include_sections is None:
            include_sections = self.report_sections
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate total if not present
        if 'total' not in summary:
            summary['total'] = summary.get('create', 0) + summary.get('update', 0) + summary.get('delete', 0) + summary.get('no-op', 0)
        
        # Start building the report
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Terraform Plan Impact Report - {timestamp}</title>
            <style>
            .report-container {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            .report-header {{
                text-align: center;
                border-bottom: 3px solid #0066cc;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            
            .report-title {{
                color: #0066cc;
                font-size: 2.5em;
                margin-bottom: 10px;
            }}
            
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            
            .metric-card {{
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
            }}
            
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                color: #0066cc;
            }}
            
            .metric-label {{
                color: #666;
                font-size: 0.9em;
                margin-top: 5px;
            }}
            
            .deployment-recommendation {{
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            
            .deployment-recommendation.success {{
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
            }}
            
            .deployment-recommendation.warning {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
            }}
            
            .deployment-recommendation.danger {{
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
            }}
            
            .risk-score-display {{
                display: flex;
                align-items: center;
                gap: 20px;
                margin: 15px 0;
            }}
            
            .risk-level {{
                padding: 10px 20px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 1.2em;
            }}
            
            .risk-level.risk-low {{
                background-color: #d4edda;
                color: #155724;
            }}
            
            .risk-level.risk-medium {{
                background-color: #fff3cd;
                color: #856404;
            }}
            
            .risk-level.risk-high {{
                background-color: #f8d7da;
                color: #721c24;
            }}
            
            .risk-level.risk-critical {{
                background-color: #d1ecf1;
                color: #0c5460;
            }}
            
            .risk-score {{
                font-size: 1.5em;
                font-weight: bold;
                color: #0066cc;
            }}
            
            .risk-table, .changes-table, .resource-summary-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            
            .risk-table th, .changes-table th, .resource-summary-table th {{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 12px;
                text-align: left;
                font-weight: bold;
            }}
            
            .risk-table td, .changes-table td, .resource-summary-table td {{
                border: 1px solid #dee2e6;
                padding: 10px;
            }}
            
            .risk-low {{ background-color: #d4edda; }}
            .risk-medium {{ background-color: #fff3cd; }}
            .risk-high {{ background-color: #f8d7da; }}
            .risk-critical {{ background-color: #d1ecf1; }}
            
            .changes-section {{
                margin: 30px 0;
            }}
            
            .truncated-notice {{
                font-style: italic;
                color: #666;
                text-align: center;
            }}
            
            .recommendations-content ul {{
                list-style-type: none;
                padding-left: 0;
            }}
            
            .recommendations-content li {{
                margin: 10px 0;
                padding: 10px;
                background-color: #f8f9fa;
                border-left: 4px solid #0066cc;
                border-radius: 4px;
            }}
            
            code {{
                background-color: #f1f3f4;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Monaco', 'Consolas', monospace;
            }}
            
            h2 {{
                color: #0066cc;
                border-bottom: 2px solid #e9ecef;
                padding-bottom: 10px;
                margin-top: 40px;
            }}
            
            h3 {{
                color: #495057;
                margin-top: 25px;
            }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <div class="report-header">
                    <h1 class="report-title">🚀 Terraform Plan Impact Report</h1>
                    <p><strong>Generated:</strong> {timestamp}</p>
                    <p><strong>Total Changes:</strong> {summary['total']} resources</p>
                </div>
        """
        
        # Add sections based on configuration
        if include_sections.get('executive_summary', True):
            report_html += self.generate_executive_summary(summary, risk_summary, plan_data)
        
        if include_sections.get('risk_analysis', True):
            report_html += self.generate_risk_analysis(risk_summary, resource_changes, enhanced_risk_assessor)
        
        if include_sections.get('detailed_changes', True):
            report_html += self.generate_detailed_changes(resource_changes, resource_types)
        
        if include_sections.get('recommendations', True):
            report_html += self.generate_recommendations(summary, risk_summary, resource_changes, enhanced_risk_assessor)
        
        # Close the report
        report_html += """
            </div>
        </body>
        </html>
        """
        
        return report_html
    
    def create_download_link(self, content: bytes, filename: str, mime_type: str, link_text: str) -> str:
        """
        Create a download link for the generated report
        
        Args:
            content: File content as bytes
            filename: Name of the file to download
            mime_type: MIME type of the file
            link_text: Text to display for the download link
            
        Returns:
            HTML string containing the download link
        """
        b64_content = base64.b64encode(content).decode()
        href = f'<a href="data:{mime_type};base64,{b64_content}" download="{filename}" style="text-decoration: none;">'
        href += f'<button style="background-color: #0066cc; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">'
        href += f'{link_text}</button></a>'
        return href
    
    def export_html_report(self,
                          summary: Dict[str, int],
                          risk_summary: Dict[str, Any],
                          resource_changes: List[Dict],
                          resource_types: Dict[str, int],
                          plan_data: Dict[str, Any],
                          enhanced_risk_assessor: Optional[Any] = None,
                          include_sections: Optional[Dict[str, bool]] = None,
                          template_name: str = "default") -> bytes:
        """
        Export report as HTML file
        
        Args:
            summary: Change summary
            risk_summary: Risk assessment results
            resource_changes: List of resource changes
            resource_types: Dictionary of resource types and counts
            plan_data: Original plan data
            enhanced_risk_assessor: Enhanced risk assessor instance (optional)
            include_sections: Dictionary specifying which sections to include
            template_name: Name of the template to use
            
        Returns:
            HTML content as bytes
        """
        # Generate the full report HTML
        report_html = self.generate_full_report(
            summary=summary,
            risk_summary=risk_summary,
            resource_changes=resource_changes,
            resource_types=resource_types,
            plan_data=plan_data,
            enhanced_risk_assessor=enhanced_risk_assessor,
            include_sections=include_sections
        )
        
        # Apply template customizations if needed
        if template_name != "default":
            report_html = self.apply_template_customizations(report_html, template_name)
        
        return report_html.encode('utf-8')
    
    def export_pdf_report(self,
                         summary: Dict[str, int],
                         risk_summary: Dict[str, Any],
                         resource_changes: List[Dict],
                         resource_types: Dict[str, int],
                         plan_data: Dict[str, Any],
                         enhanced_risk_assessor: Optional[Any] = None,
                         include_sections: Optional[Dict[str, bool]] = None,
                         template_name: str = "default",
                         show_progress: bool = True) -> Optional[bytes]:
        """
        Export report as PDF file using enhanced PDF generator with improved error handling
        
        Args:
            summary: Change summary
            risk_summary: Risk assessment results
            resource_changes: List of resource changes
            resource_types: Dictionary of resource types and counts
            plan_data: Original plan data
            enhanced_risk_assessor: Enhanced risk assessor instance (optional)
            include_sections: Dictionary specifying which sections to include
            template_name: Name of the template to use
            show_progress: Whether to show progress indicators
            
        Returns:
            PDF content as bytes, or None if PDF generation is not available
        """
        # Check PDF generator availability
        if not PDF_GENERATOR_AVAILABLE or not self.pdf_generator:
            st.error("❌ **PDF Generation Unavailable**")
            st.warning("🔧 **Issue:** Enhanced PDF generator is not available")
            
            with st.expander("💡 **Installation Instructions**", expanded=True):
                st.markdown("""
                **To enable PDF generation, install reportlab:**
                
                ```bash
                pip install reportlab
                ```
                
                **Or if using conda:**
                
                ```bash
                conda install reportlab
                ```
                
                **After installation:**
                1. Restart your application
                2. Refresh this page
                3. Try generating the PDF again
                """)
            
            # Offer fallback option
            if st.button("📄 Generate Text Report Instead", key="fallback_text_report"):
                return self._generate_fallback_report(summary, risk_summary, resource_changes, resource_types, plan_data)
            
            return None
        
        # Validate dependencies
        is_valid, validation_error = self.pdf_generator.validate_dependencies()
        if not is_valid:
            st.error(f"❌ **PDF Dependencies Missing:** {validation_error}")
            
            with st.expander("🔧 **Dependency Installation Guide**", expanded=True):
                st.markdown("""
                **Install missing dependencies:**
                
                ```bash
                pip install reportlab
                ```
                
                **If you're still getting errors:**
                ```bash
                pip install --upgrade reportlab pillow
                ```
                
                **After installation, restart the application.**
                """)
            
            return None
        
        # Progress tracking setup
        progress_container = None
        progress_bar = None
        status_text = None
        
        if show_progress:
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
        
        def progress_callback(progress: float, message: str):
            """Callback function for progress updates"""
            if progress_bar is not None:
                progress_bar.progress(progress)
            if status_text is not None:
                status_text.text(message)
        
        try:
            # Generate PDF using enhanced PDF generator with progress tracking
            pdf_bytes, error_message = self.pdf_generator.generate_comprehensive_report(
                summary=summary,
                risk_summary=risk_summary,
                resource_changes=resource_changes,
                resource_types=resource_types,
                plan_data=plan_data,
                template_name=template_name,
                include_sections=include_sections,
                progress_callback=progress_callback if show_progress else None
            )
            
            # Clear progress indicators
            if progress_container:
                progress_container.empty()
            
            if pdf_bytes and len(pdf_bytes) > 0:
                st.success("✅ PDF report generated successfully!")
                return pdf_bytes
            else:
                # Handle specific error cases
                self._handle_pdf_generation_error(error_message, summary, risk_summary, resource_changes, resource_types, plan_data)
                return None
            
        except Exception as e:
            # Clear progress indicators on error
            if progress_container:
                progress_container.empty()
            
            st.error("❌ **Unexpected Error During PDF Generation**")
            
            # Categorize error types for better user guidance
            error_str = str(e).lower()
            if "memory" in error_str:
                st.warning("🔧 **Issue:** Insufficient memory to generate PDF")
                with st.expander("💡 **Memory Issue Solutions**", expanded=True):
                    st.markdown("""
                    **Your plan may be too large for PDF generation:**
                    
                    **Immediate solutions:**
                    1. **Use compact template:** Reduces memory usage
                    2. **Disable sections:** Uncheck some sections below
                    3. **Filter your data:** Use sidebar filters to reduce dataset size
                    
                    **For very large plans:**
                    - Break Terraform into smaller modules
                    - Use targeted plans: `terraform plan -target=module.vpc`
                    - Generate separate reports for different resource types
                    """)
                    
                    # Offer compact template option
                    if st.button("🔄 Try Compact Template", key="retry_compact"):
                        return self.export_pdf_report(
                            summary, risk_summary, resource_changes, resource_types, plan_data,
                            enhanced_risk_assessor, include_sections, "compact", show_progress
                        )
                        
            elif "import" in error_str or "module" in error_str:
                st.warning("🔧 **Issue:** Missing required dependencies")
                with st.expander("💡 **Dependency Solutions**", expanded=True):
                    st.markdown("""
                    **Required dependencies may be missing or corrupted:**
                    
                    **Try these commands:**
                    ```bash
                    pip install --upgrade reportlab
                    pip install --upgrade pillow
                    ```
                    
                    **If using conda:**
                    ```bash
                    conda update reportlab
                    conda update pillow
                    ```
                    
                    **After updating:**
                    1. Restart your application
                    2. Refresh this page
                    3. Try generating the PDF again
                    """)
                    
            else:
                st.warning(f"🔧 **Technical Issue:** {str(e)}")
                with st.expander("🔧 **General Troubleshooting**", expanded=True):
                    st.markdown("""
                    **Try these steps:**
                    1. **Refresh the page** and try again
                    2. **Use a different template** (compact uses less resources)
                    3. **Reduce data size** using sidebar filters
                    4. **Check your internet connection**
                    5. **Try a different browser** if issues persist
                    """)
            
            # Always offer fallback options
            st.info("📄 **Alternative Options Available Below**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Generate Text Report", key="fallback_after_error"):
                    return self._generate_fallback_report(summary, risk_summary, resource_changes, resource_types, plan_data)
            
            with col2:
                if st.button("🔄 Retry PDF Generation", key="retry_pdf"):
                    return self.export_pdf_report(
                        summary, risk_summary, resource_changes, resource_types, plan_data,
                        enhanced_risk_assessor, include_sections, template_name, show_progress
                    )
            
            # Show detailed error for debugging if requested
            if st.checkbox("🔍 Show detailed error information", key="pdf_error_details"):
                st.exception(e)
                
            return None
    
    def _handle_pdf_generation_error(self, error_message: str, summary: Dict[str, int], 
                                   risk_summary: Dict[str, Any], resource_changes: List[Dict],
                                   resource_types: Dict[str, int], plan_data: Dict[str, Any]) -> None:
        """
        Handle specific PDF generation errors with targeted solutions
        
        Args:
            error_message: The error message from PDF generation
            summary: Change summary (for fallback options)
            risk_summary: Risk assessment results (for fallback options)
            resource_changes: List of resource changes (for fallback options)
            resource_types: Dictionary of resource types and counts (for fallback options)
            plan_data: Original plan data (for fallback options)
        """
        st.error("❌ **PDF Generation Failed**")
        
        if not error_message:
            error_message = "Unknown error occurred during PDF generation"
        
        # Categorize errors and provide specific guidance
        error_lower = error_message.lower()
        
        if "dependencies" in error_lower or "reportlab" in error_lower:
            st.warning("🔧 **Issue:** Missing or corrupted PDF generation dependencies")
            with st.expander("💡 **Dependency Installation Guide**", expanded=True):
                st.markdown("""
                **Install required dependencies:**
                
                ```bash
                # Using pip
                pip install reportlab
                
                # Or using conda
                conda install reportlab
                ```
                
                **If you're getting import errors:**
                ```bash
                # Reinstall reportlab
                pip uninstall reportlab
                pip install reportlab
                
                # Also install pillow for image support
                pip install pillow
                ```
                
                **After installation:**
                1. Restart your application
                2. Refresh this page
                3. Try generating the PDF again
                """)
                
        elif "memory" in error_lower or "size" in error_lower:
            st.warning("🔧 **Issue:** Plan data too large for PDF generation")
            with st.expander("💡 **Large Data Solutions**", expanded=True):
                st.markdown(f"""
                **Your plan contains {len(resource_changes)} resource changes, which may be too large.**
                
                **Immediate solutions:**
                1. **Use compact template** (reduces memory usage by ~40%)
                2. **Disable optional sections** (appendix, detailed analysis)
                3. **Filter data** using sidebar controls
                
                **For future large plans:**
                - Break Terraform into smaller modules
                - Use targeted plans: `terraform plan -target=specific.resource`
                - Consider workspace separation for different environments
                """)
                
        elif "validation" in error_lower or "input" in error_lower:
            st.warning("🔧 **Issue:** Invalid or corrupted plan data")
            with st.expander("💡 **Data Validation Solutions**", expanded=True):
                st.markdown("""
                **Your Terraform plan data may have formatting issues:**
                
                **Try these steps:**
                1. **Re-upload your plan file** - the upload may have been corrupted
                2. **Generate a fresh plan:**
                   ```bash
                   terraform plan -out=tfplan
                   terraform show -json tfplan > new-plan.json
                   ```
                3. **Validate your JSON:**
                   ```bash
                   python -m json.tool your-plan.json > /dev/null
                   ```
                
                **Common data issues:**
                - Missing required fields in plan JSON
                - Corrupted resource change data
                - Invalid risk assessment results
                """)
                
        else:
            st.warning(f"🔧 **Technical Issue:** {error_message}")
            with st.expander("🔧 **General Error Solutions**", expanded=True):
                st.markdown("""
                **General troubleshooting steps:**
                
                1. **Try again** - temporary issues sometimes resolve themselves
                2. **Use different template** - compact template is more reliable
                3. **Reduce data size** - use filters to limit the dataset
                4. **Check browser** - try a different browser if issues persist
                5. **Restart application** - refresh the page and try again
                """)
        
        # Always provide fallback options
        st.info("📄 **Alternative Report Options**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Text Report", key="text_fallback", help="Generate a simple text report"):
                return self._generate_fallback_report(summary, risk_summary, resource_changes, resource_types, plan_data)
        
        with col2:
            if st.button("📊 Data Export", key="data_export", help="Export raw data as JSON"):
                return self._export_raw_data(summary, risk_summary, resource_changes, resource_types, plan_data)
        
        with col3:
            if st.button("🔄 Retry PDF", key="retry_pdf_generation", help="Try PDF generation again"):
                return self.export_pdf_report(
                    summary, risk_summary, resource_changes, resource_types, plan_data,
                    show_progress=True
                )
    
    def _generate_fallback_report(self, summary: Dict[str, int], risk_summary: Dict[str, Any],
                                resource_changes: List[Dict], resource_types: Dict[str, int],
                                plan_data: Dict[str, Any]) -> bytes:
        """
        Generate a fallback text report when PDF generation fails
        
        Returns:
            Text report as bytes for download
        """
        try:
            if self.pdf_generator:
                report_content, filename = self.pdf_generator.generate_fallback_report(
                    summary, risk_summary, resource_changes, resource_types, plan_data
                )
            else:
                # Ultimate fallback if PDF generator is not available
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                report_content = f"""
TERRAFORM PLAN IMPACT REPORT (BASIC FALLBACK)
Generated: {timestamp}

SUMMARY:
- Create: {summary.get('create', 0)}
- Update: {summary.get('update', 0)}
- Delete: {summary.get('delete', 0)}
- Total: {len(resource_changes)}

RESOURCE TYPES:
{chr(10).join(f"- {rtype}: {count}" for rtype, count in sorted(resource_types.items()))}

Note: This is a basic fallback report. For full functionality, please install reportlab.
"""
                filename = f"terraform-plan-basic-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
            
            # Provide download
            st.success("✅ Text report generated successfully!")
            st.download_button(
                label="📄 Download Text Report",
                data=report_content.encode('utf-8'),
                file_name=filename,
                mime="text/plain",
                key="download_text_report"
            )
            
            # Show preview
            with st.expander("👀 Preview Text Report", expanded=False):
                st.text(report_content[:2000] + "..." if len(report_content) > 2000 else report_content)
            
            return report_content.encode('utf-8')
            
        except Exception as e:
            st.error(f"❌ Failed to generate fallback report: {str(e)}")
            return b"Error generating fallback report"
    
    def _export_raw_data(self, summary: Dict[str, int], risk_summary: Dict[str, Any],
                        resource_changes: List[Dict], resource_types: Dict[str, int],
                        plan_data: Dict[str, Any]) -> bytes:
        """
        Export raw data as JSON when other options fail
        
        Returns:
            JSON data as bytes for download
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "summary": summary,
                "risk_summary": risk_summary,
                "resource_changes": resource_changes[:100],  # Limit for size
                "resource_types": resource_types,
                "plan_metadata": {
                    "terraform_version": plan_data.get("terraform_version"),
                    "format_version": plan_data.get("format_version"),
                    "total_resources": len(resource_changes)
                }
            }
            
            json_content = json.dumps(export_data, indent=2, default=str)
            filename = f"terraform-plan-data-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            
            st.success("✅ Data export prepared successfully!")
            st.download_button(
                label="📊 Download Raw Data (JSON)",
                data=json_content.encode('utf-8'),
                file_name=filename,
                mime="application/json",
                key="download_raw_data"
            )
            
            st.info("💡 This JSON file contains your plan data and can be imported into other analysis tools.")
            
            return json_content.encode('utf-8')
            
        except Exception as e:
            st.error(f"❌ Failed to export raw data: {str(e)}")
            return b'{"error": "Failed to export data"}'

    
    def apply_template_customizations(self, html_content: str, template_name: str) -> str:
        """
        Apply template-specific customizations to the HTML content
        
        Args:
            html_content: Original HTML content
            template_name: Name of the template to apply
            
        Returns:
            Customized HTML content
        """
        templates = {
            "executive": {
                "title": "Executive Summary Report",
                "focus": "high-level",
                "color_scheme": "#1f4e79"
            },
            "technical": {
                "title": "Technical Analysis Report", 
                "focus": "detailed",
                "color_scheme": "#2d5016"
            },
            "security": {
                "title": "Security Assessment Report",
                "focus": "security",
                "color_scheme": "#8b0000"
            }
        }
        
        if template_name not in templates:
            return html_content
        
        template_config = templates[template_name]
        
        # Replace title
        html_content = html_content.replace(
            "🚀 Terraform Plan Impact Report",
            f"🚀 {template_config['title']}"
        )
        
        # Replace color scheme
        html_content = html_content.replace(
            "#0066cc",
            template_config['color_scheme']
        )
        
        return html_content
    
    def get_available_templates(self) -> Dict[str, str]:
        """
        Get available report templates
        
        Returns:
            Dictionary mapping template names to descriptions
        """
        return {
            "default": "Standard comprehensive report with all sections",
            "executive": "Executive-focused report emphasizing high-level insights",
            "technical": "Technical deep-dive report with detailed analysis",
            "security": "Security-focused report highlighting security considerations"
        }
    
    def render_report_generator(self,
                              summary: Dict[str, int],
                              risk_summary: Dict[str, Any],
                              resource_changes: List[Dict],
                              resource_types: Dict[str, int],
                              plan_data: Dict[str, Any],
                              enhanced_risk_assessor: Optional[Any] = None) -> None:
        """
        Render the report generator interface in Streamlit
        
        Args:
            summary: Change summary
            risk_summary: Risk assessment results
            resource_changes: List of resource changes
            resource_types: Dictionary of resource types and counts
            plan_data: Original plan data
            enhanced_risk_assessor: Enhanced risk assessor instance (optional)
        """
        st.markdown("---")
        st.markdown("## 📄 Generate Report")
        st.caption("Create comprehensive reports for stakeholders with executive summary, risk analysis, and detailed changes")
        
        # Report configuration
        with st.expander("📋 Report Configuration", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Include Sections:**")
                include_executive = st.checkbox("Executive Summary", value=True, help="High-level overview with key metrics and recommendations")
                include_risk = st.checkbox("Risk Analysis", value=True, help="Detailed risk assessment and mitigation strategies")
                include_changes = st.checkbox("Detailed Changes", value=True, help="Complete list of resource changes by action type")
            
            with col2:
                st.markdown("**Additional Options:**")
                include_recommendations = st.checkbox("Recommendations", value=True, help="Deployment recommendations and best practices")
                include_visualizations = st.checkbox("Include Chart References", value=True, help="References to charts and visualizations")
                
        # Template selection
        st.markdown("**Report Template:**")
        available_templates = self.get_available_templates()
        selected_template = st.selectbox(
            "Choose report template",
            options=list(available_templates.keys()),
            format_func=lambda x: f"{x.title()} - {available_templates[x]}",
            help="Select a template that best fits your audience and use case"
        )
        
        # Generate report button
        if st.button("📊 Generate Report", type="primary"):
            # Configure sections
            include_sections = {
                'executive_summary': include_executive,
                'risk_analysis': include_risk,
                'detailed_changes': include_changes,
                'recommendations': include_recommendations,
                'visualizations': include_visualizations
            }
            
            # Generate the report
            with st.spinner("Generating comprehensive report..."):
                try:
                    report_html = self.generate_full_report(
                        summary=summary,
                        risk_summary=risk_summary,
                        resource_changes=resource_changes,
                        resource_types=resource_types,
                        plan_data=plan_data,
                        enhanced_risk_assessor=enhanced_risk_assessor,
                        include_sections=include_sections
                    )
                    
                    # Show success message
                    st.success("✅ Report generated successfully!")
                    
                    # Provide download options
                    # Use stable timestamp for session state key
                    if 'report_timestamp' not in st.session_state:
                        st.session_state.report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    timestamp = st.session_state.report_timestamp
                    
                    st.markdown("### 📥 Export Options")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # HTML download
                        html_content = self.export_html_report(
                            summary=summary,
                            risk_summary=risk_summary,
                            resource_changes=resource_changes,
                            resource_types=resource_types,
                            plan_data=plan_data,
                            enhanced_risk_assessor=enhanced_risk_assessor,
                            include_sections=include_sections,
                            template_name=selected_template
                        )
                        
                        st.download_button(
                            label="📄 Download HTML",
                            data=html_content,
                            file_name=f"terraform_plan_report_{selected_template}_{timestamp}.html",
                            mime="text/html",
                            help="Download as HTML file for viewing in web browsers and sharing"
                        )
                    
                    with col2:
                        # PDF download using enhanced PDF generator - generate immediately like HTML
                        if PDF_GENERATOR_AVAILABLE and self.pdf_generator:
                            with st.spinner("✨ Creating your professional PDF report..."):
                                try:
                                    # Generate the PDF using the enhanced PDF generator (same data as HTML)
                                    pdf_content = self.export_pdf_report(
                                        summary=summary,
                                        risk_summary=risk_summary,
                                        resource_changes=resource_changes,
                                        resource_types=resource_types,
                                        plan_data=plan_data,
                                        enhanced_risk_assessor=enhanced_risk_assessor,
                                        include_sections=include_sections,
                                        template_name=selected_template,
                                        show_progress=False
                                    )
                                    
                                    if pdf_content:
                                        # Show download button immediately (like the working test)
                                        pdf_size_kb = len(pdf_content) / 1024
                                        if pdf_size_kb >= 1024:
                                            pdf_size_mb = pdf_size_kb / 1024
                                            st.success(f"✅ PDF generated successfully! ({pdf_size_mb:.1f} MB)")
                                        elif pdf_size_kb >= 1:
                                            st.success(f"✅ PDF generated successfully! ({pdf_size_kb:.0f} KB)")
                                        else:
                                            st.success("✅ PDF generated successfully!")
                                        
                                        st.download_button(
                                            label="📥 Download PDF",
                                            data=pdf_content,
                                            file_name=f"terraform_plan_report_{selected_template}_{timestamp}.pdf",
                                            mime="application/pdf",
                                            help="Download as PDF for formal reviews and printing"
                                        )
                                    else:
                                        st.error("❌ PDF generation failed")
                                        st.info("💡 Try the HTML version instead")
                                        
                                except Exception as e:
                                    st.error(f"❌ PDF Error: {str(e)}")
                                    st.info("💡 HTML download is still available")
                        else:
                            st.info("📑 PDF export requires reportlab installation")
                            st.code("pip install reportlab", language="bash")
                            st.info("After installation, refresh the page to enable PDF generation")
                    
                    with col3:
                        # Preview button
                        if st.button("👁️ Preview Report"):
                            st.markdown("### Report Preview")
                            st.components.v1.html(html_content.decode('utf-8'), height=600, scrolling=True)
                    
                    # Show report statistics
                    st.info(f"""
                    **Report Statistics:**
                    - Sections included: {sum(include_sections.values())}
                    - Resources analyzed: {len(resource_changes)}
                    - Resource types: {len(resource_types)}
                    - Report size: ~{len(report_html) // 1024}KB
                    """)
                    
                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)}")
                    if st.checkbox("Show error details"):
                        st.exception(e)
        
        # Show sample report information
        with st.expander("ℹ️ About Reports", expanded=False):
            st.markdown("""
            **Report Features:**
            - **Executive Summary:** High-level overview with key metrics and deployment recommendations
            - **Risk Analysis:** Detailed risk assessment with mitigation strategies and resource-level risk breakdown
            - **Detailed Changes:** Complete listing of all resource changes organized by action type
            - **Recommendations:** Deployment best practices and specific guidance based on your plan
            - **Charts & Visualizations:** References to interactive charts for stakeholder presentations
            
            **Report Formats:**
            - **HTML:** Interactive report viewable in any web browser, perfect for sharing with stakeholders
            - **PDF:** Professional document format for formal reviews, approvals, and printing
            
            **Report Templates:**
            - **Default:** Standard comprehensive report with all sections
            - **Executive:** Executive-focused report emphasizing high-level insights
            - **Technical:** Technical deep-dive report with detailed analysis  
            - **Security:** Security-focused report highlighting security considerations
            
            **Use Cases:**
            - Stakeholder reviews and approvals
            - Change management documentation
            - Deployment planning and risk assessment
            - Audit trails and compliance reporting
            """)
    
    def render(self, *args, **kwargs) -> None:
        """
        Render method required by BaseComponent
        Delegates to render_report_generator for backward compatibility
        """
        return self.render_report_generator(*args, **kwargs)