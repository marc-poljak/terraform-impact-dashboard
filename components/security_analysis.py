"""
Security Analysis Component

Provides security-focused analysis and visualization for Terraform plan changes.
Integrates with the existing dashboard structure to highlight security resources,
assess security risks, and provide compliance checks.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
from utils.security_analyzer import SecurityAnalyzer
from .base_component import BaseComponent


class SecurityAnalysisComponent(BaseComponent):
    """Component for rendering security analysis sections"""
    
    def __init__(self, session_manager: Optional[Any] = None):
        """
        Initialize the SecurityAnalysisComponent
        
        Args:
            session_manager: Optional session state manager
        """
        super().__init__(session_manager)
        self.security_analyzer = SecurityAnalyzer()
    
    def render(self, resource_changes: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Main render method for the security analysis component
        
        Args:
            resource_changes: List of resource changes from Terraform plan
            **kwargs: Additional keyword arguments
            
        Returns:
            Dictionary containing security analysis results
        """
        # Render all security analysis sections
        self.render_security_highlighting(resource_changes)
        self.render_compliance_checks(resource_changes)
        dashboard_data = self.render_security_dashboard(resource_changes)
        
        return dashboard_data
    
    def render_security_highlighting(self, resource_changes: List[Dict[str, Any]]) -> None:
        """
        Render security-focused resource highlighting section
        
        Args:
            resource_changes: List of resource changes from Terraform plan
        """
        st.markdown("---")
        st.markdown("## 🔒 Security Analysis")
        st.caption("Comprehensive security analysis of your Terraform plan changes, highlighting security-critical resources and potential risks.")
        
        # Perform security analysis
        security_data = self.security_analyzer.analyze_security_resources(resource_changes)
        
        if security_data['total_security_resources'] == 0:
            st.success("✅ No security-critical resources detected in this plan")
            st.info("💡 This plan appears to contain only non-security infrastructure changes. While this reduces security risk, ensure that security best practices are still followed.")
            return
        
        # Security overview metrics
        self._render_security_overview(security_data, len(resource_changes))
        
        # Security resources breakdown
        self._render_security_resources_breakdown(security_data)
        
        # Security risks and recommendations
        self._render_security_risks(security_data)
    
    def render_compliance_checks(self, resource_changes: List[Dict[str, Any]], 
                                frameworks: Optional[List[str]] = None) -> None:
        """
        Render compliance checks section
        
        Args:
            resource_changes: List of resource changes from Terraform plan
            frameworks: List of compliance frameworks to check
        """
        st.markdown("---")
        st.markdown("## 📋 Compliance Framework Checks")
        st.caption("Automated checks against common security and compliance frameworks to ensure your infrastructure meets regulatory requirements.")
        
        # Allow user to select frameworks
        if frameworks is None:
            available_frameworks = list(self.security_analyzer.compliance_frameworks.keys())
            frameworks = st.multiselect(
                "Select Compliance Frameworks to Check",
                options=available_frameworks,
                default=['SOC2', 'PCI_DSS'],
                help="Choose which compliance frameworks to evaluate your Terraform plan against. Each framework has specific requirements for security controls."
            )
        
        if not frameworks:
            st.info("Select one or more compliance frameworks to perform checks.")
            return
        
        # Perform compliance checks
        compliance_results = self.security_analyzer.check_compliance(resource_changes, frameworks)
        
        # Render compliance results
        self._render_compliance_results(compliance_results)
    
    def render_security_dashboard(self, resource_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Render comprehensive security dashboard
        
        Args:
            resource_changes: List of resource changes from Terraform plan
            
        Returns:
            Dictionary containing security dashboard data
        """
        st.markdown("---")
        st.markdown("## 🛡️ Security Dashboard")
        st.caption("Comprehensive security posture analysis combining resource analysis, risk assessment, and compliance checks.")
        
        # Get comprehensive security data
        dashboard_data = self.security_analyzer.get_security_dashboard_data(resource_changes)
        
        # Render security score and level
        self._render_security_score(dashboard_data)
        
        # Render security trends and insights
        self._render_security_insights(dashboard_data, resource_changes)
        
        # Render security categories analysis
        self._render_security_categories(dashboard_data['security_analysis'])
        
        # Render security best practices recommendations
        self._render_security_best_practices(dashboard_data)
        
        # Render compliance summary
        if dashboard_data['compliance_results']:
            self._render_compliance_summary(dashboard_data['compliance_results'])
        
        return dashboard_data
    
    def _render_security_overview(self, security_data: Dict[str, Any], total_resources: int) -> None:
        """Render security overview metrics"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            security_percentage = round((security_data['total_security_resources'] / total_resources) * 100, 1)
            st.metric(
                label="🔒 Security Resources",
                value=security_data['total_security_resources'],
                delta=f"{security_percentage}% of total"
            )
        
        with col2:
            level_color = {
                'Low': '🟢',
                'Medium': '🟡', 
                'High': '🟠',
                'Critical': '🔴'
            }.get(security_data['security_level'], '⚪')
            
            st.metric(
                label=f"{level_color} Security Level",
                value=security_data['security_level'],
                delta=f"Score: {security_data['avg_security_score']}/10"
            )
        
        with col3:
            high_risk_resources = len([r for r in security_data['security_resources'] if r['risk_score'] >= 8])
            st.metric(
                label="⚠️ High Risk Resources",
                value=high_risk_resources,
                delta="Require attention" if high_risk_resources > 0 else "None detected"
            )
        
        with col4:
            categories_count = len(security_data['category_breakdown'])
            st.metric(
                label="📊 Security Categories",
                value=categories_count,
                delta="Areas affected"
            )
    
    def _render_security_resources_breakdown(self, security_data: Dict[str, Any]) -> None:
        """Render detailed breakdown of security resources"""
        st.markdown("### 🔍 Security Resources Breakdown")
        
        if not security_data['security_resources']:
            return
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 By Category", "📋 Detailed List", "📈 Risk Distribution"])
        
        with tab1:
            # Category breakdown chart
            if security_data['category_breakdown']:
                category_df = pd.DataFrame([
                    {'Category': cat.title(), 'Count': count}
                    for cat, count in security_data['category_breakdown'].items()
                ])
                
                fig = px.pie(
                    category_df, 
                    values='Count', 
                    names='Category',
                    title="Security Resources by Category",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                
                # Category descriptions
                st.markdown("**Category Descriptions:**")
                category_descriptions = {
                    'identity': '🔐 Identity & Access Management (IAM roles, policies, users)',
                    'network': '🌐 Network Security (Security groups, VPCs, ACLs)',
                    'encryption': '🔒 Encryption & Key Management (KMS keys, certificates)',
                    'storage': '💾 Storage Security (S3 policies, bucket configurations)',
                    'database': '🗄️ Database Security (RDS instances, parameter groups)',
                    'secrets': '🤐 Secrets Management (Secrets Manager, SSM parameters)',
                    'monitoring': '👁️ Security Monitoring (CloudTrail, GuardDuty, Config)',
                    'certificates': '📜 Certificate Management (ACM certificates)'
                }
                
                for category, count in security_data['category_breakdown'].items():
                    description = category_descriptions.get(category, f'{category.title()} resources')
                    st.write(f"• **{category.title()}** ({count} resources): {description}")
        
        with tab2:
            # Detailed resource list
            resources_df = pd.DataFrame([
                {
                    'Resource': r['address'],
                    'Type': r['type'],
                    'Category': r['category'].title(),
                    'Actions': ', '.join(r['actions']),
                    'Risk Score': r['risk_score'],
                    'Risk Level': 'Critical' if r['risk_score'] >= 8 else 'High' if r['risk_score'] >= 6 else 'Medium' if r['risk_score'] >= 4 else 'Low',
                    'Description': r['description']
                }
                for r in security_data['security_resources']
            ])
            
            # Sort by risk score descending
            resources_df = resources_df.sort_values('Risk Score', ascending=False)
            
            # Color-code risk levels
            def highlight_risk(row):
                if row['Risk Score'] >= 8:
                    return ['background-color: #ffebee'] * len(row)  # Light red
                elif row['Risk Score'] >= 6:
                    return ['background-color: #fff3e0'] * len(row)  # Light orange
                elif row['Risk Score'] >= 4:
                    return ['background-color: #fffde7'] * len(row)  # Light yellow
                else:
                    return ['background-color: #e8f5e8'] * len(row)  # Light green
            
            st.dataframe(
                resources_df.style.apply(highlight_risk, axis=1),
                use_container_width=True,
                column_config={
                    "Risk Score": st.column_config.ProgressColumn(
                        "Risk Score",
                        help="Security risk score (0-10)",
                        min_value=0,
                        max_value=10,
                    ),
                }
            )
        
        with tab3:
            # Risk distribution chart
            risk_levels = ['Low', 'Medium', 'High', 'Critical']
            risk_counts = {level: 0 for level in risk_levels}
            
            for resource in security_data['security_resources']:
                score = resource['risk_score']
                if score >= 8:
                    risk_counts['Critical'] += 1
                elif score >= 6:
                    risk_counts['High'] += 1
                elif score >= 4:
                    risk_counts['Medium'] += 1
                else:
                    risk_counts['Low'] += 1
            
            risk_df = pd.DataFrame([
                {'Risk Level': level, 'Count': count}
                for level, count in risk_counts.items()
                if count > 0
            ])
            
            if not risk_df.empty:
                colors = {'Low': '#4CAF50', 'Medium': '#FFC107', 'High': '#FF9800', 'Critical': '#F44336'}
                fig = px.bar(
                    risk_df,
                    x='Risk Level',
                    y='Count',
                    title="Security Resources by Risk Level",
                    color='Risk Level',
                    color_discrete_map=colors
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_security_risks(self, security_data: Dict[str, Any]) -> None:
        """Render security risks and recommendations"""
        st.markdown("### ⚠️ Security Risks & Recommendations")
        
        if security_data['security_risks']:
            st.markdown("**🔴 High-Risk Security Issues:**")
            for risk in security_data['security_risks']:
                with st.expander(f"⚠️ {risk['resource']} - {risk['risk']}", expanded=False):
                    st.write(f"**Resource Type:** {risk['type']}")
                    st.write(f"**Risk:** {risk['risk']}")
                    st.write(f"**Recommendation:** {risk['recommendation']}")
        
        if security_data['recommendations']:
            st.markdown("**💡 Security Recommendations:**")
            for i, recommendation in enumerate(security_data['recommendations'], 1):
                st.write(f"{i}. {recommendation}")
        else:
            st.success("✅ No specific security recommendations at this time")
    
    def _render_security_score(self, dashboard_data: Dict[str, Any]) -> None:
        """Render overall security score and level"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Security score gauge
            score = dashboard_data['overall_security_score']
            level = dashboard_data['overall_security_level']
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Overall Security Score"},
                delta = {'reference': 70, 'increasing': {'color': "RebeccaPurple"}},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 40], 'color': "lightgray"},
                        {'range': [40, 70], 'color': "yellow"},
                        {'range': [70, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.metric(
                label="🛡️ Security Level",
                value=level,
                delta=f"{score:.1f}/100"
            )
            
            st.metric(
                label="📊 Resources Analyzed",
                value=dashboard_data['total_resources_analyzed'],
                delta=f"{dashboard_data['security_resource_percentage']:.1f}% security-related"
            )
        
        with col3:
            # Security level interpretation
            level_info = {
                'Low': {'color': '🟢', 'desc': 'Minimal security risks detected'},
                'Medium': {'color': '🟡', 'desc': 'Some security considerations needed'},
                'High': {'color': '🟠', 'desc': 'Significant security risks present'},
                'Critical': {'color': '🔴', 'desc': 'Immediate security attention required'}
            }
            
            info = level_info.get(level, {'color': '⚪', 'desc': 'Security level unknown'})
            st.info(f"{info['color']} **{level} Risk Level**\n\n{info['desc']}")
    
    def _render_security_categories(self, security_analysis: Dict[str, Any]) -> None:
        """Render security categories analysis"""
        if not security_analysis['category_breakdown']:
            return
        
        st.markdown("### 📊 Security Categories Impact")
        
        # Create a horizontal bar chart for categories
        categories = list(security_analysis['category_breakdown'].keys())
        counts = list(security_analysis['category_breakdown'].values())
        
        fig = go.Figure(go.Bar(
            x=counts,
            y=[cat.title() for cat in categories],
            orientation='h',
            marker_color='lightblue'
        ))
        
        fig.update_layout(
            title="Security Resources by Category",
            xaxis_title="Number of Resources",
            yaxis_title="Security Category",
            height=max(300, len(categories) * 50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_compliance_results(self, compliance_results: Dict[str, Any]) -> None:
        """Render compliance check results"""
        for framework, results in compliance_results.items():
            with st.expander(f"📋 {results['name']} Compliance", expanded=True):
                # Framework score
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Score", f"{results['score']:.1f}%")
                with col2:
                    st.metric("Passed", results['passed'], delta="✅")
                with col3:
                    st.metric("Failed", results['failed'], delta="❌" if results['failed'] > 0 else None)
                with col4:
                    st.metric("Warnings", results['warnings'], delta="⚠️" if results['warnings'] > 0 else None)
                
                # Detailed checks
                if results['checks']:
                    st.markdown("**Detailed Checks:**")
                    for check in results['checks']:
                        status_icon = {
                            'pass': '✅',
                            'fail': '❌', 
                            'warning': '⚠️'
                        }.get(check['status'], '❓')
                        
                        st.write(f"{status_icon} **{check['requirement']}**: {check['description']}")
                        
                        if check.get('resources'):
                            with st.expander("View affected resources", expanded=False):
                                for resource in check['resources']:
                                    st.write(f"• {resource}")
    
    def _render_compliance_summary(self, compliance_results: Dict[str, Any]) -> None:
        """Render compliance summary chart"""
        st.markdown("### 📊 Compliance Summary")
        
        # Create compliance summary data
        framework_names = []
        scores = []
        
        for framework, results in compliance_results.items():
            framework_names.append(results['name'])
            scores.append(results['score'])
        
        if framework_names:
            fig = go.Figure(data=[
                go.Bar(
                    x=framework_names,
                    y=scores,
                    marker_color=['green' if score >= 80 else 'orange' if score >= 60 else 'red' for score in scores]
                )
            ])
            
            fig.update_layout(
                title="Compliance Framework Scores",
                xaxis_title="Framework",
                yaxis_title="Compliance Score (%)",
                yaxis=dict(range=[0, 100])
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_security_insights(self, dashboard_data: Dict[str, Any], resource_changes: List[Dict[str, Any]]) -> None:
        """Render security insights and trends"""
        st.markdown("### 🔍 Security Insights")
        
        security_analysis = dashboard_data['security_analysis']
        
        # Create insights based on the analysis
        insights = []
        
        # Resource distribution insights
        total_resources = len(resource_changes)
        security_resources = security_analysis['total_security_resources']
        security_percentage = (security_resources / total_resources) * 100 if total_resources > 0 else 0
        
        if security_percentage > 50:
            insights.append({
                'type': 'warning',
                'title': 'High Security Resource Density',
                'message': f'{security_percentage:.1f}% of resources are security-related. This indicates significant security impact.',
                'recommendation': 'Consider staging deployment and extra review for security changes.'
            })
        elif security_percentage > 20:
            insights.append({
                'type': 'info',
                'title': 'Moderate Security Impact',
                'message': f'{security_percentage:.1f}% of resources are security-related.',
                'recommendation': 'Review security changes carefully before deployment.'
            })
        else:
            insights.append({
                'type': 'success',
                'title': 'Low Security Impact',
                'message': f'Only {security_percentage:.1f}% of resources are security-related.',
                'recommendation': 'Standard deployment procedures should be sufficient.'
            })
        
        # Risk level insights
        high_risk_count = len([r for r in security_analysis['security_resources'] if r['risk_score'] >= 8])
        if high_risk_count > 0:
            insights.append({
                'type': 'error',
                'title': 'Critical Security Risks Detected',
                'message': f'{high_risk_count} resources have critical security risk scores (≥8/10).',
                'recommendation': 'These resources require immediate security review and approval before deployment.'
            })
        
        # Category insights
        categories = security_analysis['category_breakdown']
        if 'identity' in categories and categories['identity'] > 3:
            insights.append({
                'type': 'warning',
                'title': 'Significant IAM Changes',
                'message': f'{categories["identity"]} identity and access management resources are being modified.',
                'recommendation': 'Verify principle of least privilege and review all permission changes.'
            })
        
        if 'network' in categories and categories['network'] > 2:
            insights.append({
                'type': 'warning',
                'title': 'Network Security Changes',
                'message': f'{categories["network"]} network security resources are being modified.',
                'recommendation': 'Review firewall rules and ensure no unintended access is granted.'
            })
        
        # Render insights
        for insight in insights:
            if insight['type'] == 'error':
                st.error(f"🚨 **{insight['title']}**\n\n{insight['message']}\n\n💡 **Recommendation:** {insight['recommendation']}")
            elif insight['type'] == 'warning':
                st.warning(f"⚠️ **{insight['title']}**\n\n{insight['message']}\n\n💡 **Recommendation:** {insight['recommendation']}")
            elif insight['type'] == 'info':
                st.info(f"ℹ️ **{insight['title']}**\n\n{insight['message']}\n\n💡 **Recommendation:** {insight['recommendation']}")
            else:
                st.success(f"✅ **{insight['title']}**\n\n{insight['message']}\n\n💡 **Recommendation:** {insight['recommendation']}")
    
    def _render_security_best_practices(self, dashboard_data: Dict[str, Any]) -> None:
        """Render security best practices and recommendations"""
        st.markdown("### 📚 Security Best Practices")
        
        security_analysis = dashboard_data['security_analysis']
        categories = security_analysis['category_breakdown']
        
        # Create tabs for different security domains
        if categories:
            # Create tabs based on categories present
            tab_names = []
            tab_contents = {}
            
            if 'identity' in categories:
                tab_names.append("🔐 Identity & Access")
                tab_contents["🔐 Identity & Access"] = self._get_iam_best_practices()
            
            if 'network' in categories:
                tab_names.append("🌐 Network Security")
                tab_contents["🌐 Network Security"] = self._get_network_best_practices()
            
            if 'encryption' in categories:
                tab_names.append("🔒 Encryption")
                tab_contents["🔒 Encryption"] = self._get_encryption_best_practices()
            
            if 'storage' in categories:
                tab_names.append("💾 Storage Security")
                tab_contents["💾 Storage Security"] = self._get_storage_best_practices()
            
            # Add general best practices tab
            tab_names.append("📋 General")
            tab_contents["📋 General"] = self._get_general_best_practices()
            
            # Create tabs
            tabs = st.tabs(tab_names)
            
            for i, tab_name in enumerate(tab_names):
                with tabs[i]:
                    practices = tab_contents[tab_name]
                    for practice in practices:
                        st.markdown(f"• **{practice['title']}**: {practice['description']}")
                        if practice.get('example'):
                            with st.expander("View Example", expanded=False):
                                st.code(practice['example'], language='hcl')
        else:
            # Show general best practices if no specific categories
            practices = self._get_general_best_practices()
            for practice in practices:
                st.markdown(f"• **{practice['title']}**: {practice['description']}")
    
    def _get_iam_best_practices(self) -> List[Dict[str, str]]:
        """Get IAM security best practices"""
        return [
            {
                'title': 'Principle of Least Privilege',
                'description': 'Grant only the minimum permissions necessary for the task',
                'example': '''# Good: Specific permissions
resource "aws_iam_policy" "s3_read_only" {
  policy = jsonencode({
    Statement = [{
      Effect = "Allow"
      Action = ["s3:GetObject"]
      Resource = "arn:aws:s3:::my-bucket/*"
    }]
  })
}'''
            },
            {
                'title': 'Use IAM Roles Instead of Users',
                'description': 'Prefer IAM roles for applications and services over IAM users',
                'example': '''# Good: Use roles for EC2 instances
resource "aws_iam_role" "ec2_role" {
  assume_role_policy = jsonencode({
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}'''
            },
            {
                'title': 'Enable MFA for Sensitive Operations',
                'description': 'Require multi-factor authentication for privileged actions',
                'example': '''# Add MFA condition to policies
"Condition": {
  "Bool": {
    "aws:MultiFactorAuthPresent": "true"
  }
}'''
            },
            {
                'title': 'Regular Access Reviews',
                'description': 'Periodically review and remove unused permissions and roles'
            }
        ]
    
    def _get_network_best_practices(self) -> List[Dict[str, str]]:
        """Get network security best practices"""
        return [
            {
                'title': 'Restrict Inbound Access',
                'description': 'Avoid 0.0.0.0/0 in security group rules, use specific IP ranges',
                'example': '''# Good: Specific IP ranges
resource "aws_security_group_rule" "ssh" {
  type        = "ingress"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["10.0.0.0/8"]  # Internal network only
}'''
            },
            {
                'title': 'Use Private Subnets',
                'description': 'Place application servers in private subnets without direct internet access',
                'example': '''# Good: Private subnet configuration
resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = false
}'''
            },
            {
                'title': 'Implement Network Segmentation',
                'description': 'Use multiple subnets and security groups to segment network traffic'
            },
            {
                'title': 'Enable VPC Flow Logs',
                'description': 'Monitor network traffic with VPC Flow Logs for security analysis'
            }
        ]
    
    def _get_encryption_best_practices(self) -> List[Dict[str, str]]:
        """Get encryption security best practices"""
        return [
            {
                'title': 'Encrypt Data at Rest',
                'description': 'Enable encryption for all storage services (S3, EBS, RDS)',
                'example': '''# Good: Enable S3 encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "example" {
  bucket = aws_s3_bucket.example.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}'''
            },
            {
                'title': 'Use Customer-Managed KMS Keys',
                'description': 'Use customer-managed KMS keys for better control over encryption',
                'example': '''# Good: Customer-managed KMS key
resource "aws_kms_key" "example" {
  description             = "Example KMS key"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}'''
            },
            {
                'title': 'Enable Key Rotation',
                'description': 'Enable automatic key rotation for KMS keys'
            },
            {
                'title': 'Encrypt Data in Transit',
                'description': 'Use TLS/SSL for all data transmission'
            }
        ]
    
    def _get_storage_best_practices(self) -> List[Dict[str, str]]:
        """Get storage security best practices"""
        return [
            {
                'title': 'Block Public Access',
                'description': 'Use S3 bucket public access block to prevent accidental public exposure',
                'example': '''# Good: Block public access
resource "aws_s3_bucket_public_access_block" "example" {
  bucket = aws_s3_bucket.example.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}'''
            },
            {
                'title': 'Enable Versioning',
                'description': 'Enable versioning on S3 buckets to protect against accidental deletion'
            },
            {
                'title': 'Use Bucket Policies',
                'description': 'Implement restrictive bucket policies to control access'
            },
            {
                'title': 'Enable Access Logging',
                'description': 'Enable access logging for audit trails'
            }
        ]
    
    def _get_general_best_practices(self) -> List[Dict[str, str]]:
        """Get general security best practices"""
        return [
            {
                'title': 'Enable CloudTrail',
                'description': 'Enable AWS CloudTrail for comprehensive audit logging'
            },
            {
                'title': 'Use Infrastructure as Code',
                'description': 'Manage infrastructure through code for consistency and auditability'
            },
            {
                'title': 'Implement Monitoring',
                'description': 'Set up monitoring and alerting for security events'
            },
            {
                'title': 'Regular Security Reviews',
                'description': 'Conduct regular security reviews and penetration testing'
            },
            {
                'title': 'Keep Resources Updated',
                'description': 'Regularly update and patch all infrastructure components'
            },
            {
                'title': 'Use Secrets Management',
                'description': 'Store sensitive data in AWS Secrets Manager or Systems Manager Parameter Store'
            }
        ]