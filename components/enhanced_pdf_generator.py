"""
Enhanced PDF Generator

A comprehensive PDF generator using pure Python libraries (reportlab) to generate
PDFs directly from data structures. This eliminates all WeasyPrint dependencies
and system library requirements.

Requirements addressed: 1.1, 1.4, 2.1
"""

import io
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Dependency validation
def validate_dependencies() -> Tuple[bool, str]:
    """
    Validate that required dependencies are available
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        import reportlab
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        return True, ""
    except ImportError as e:
        return False, f"PDF generation requires reportlab. Install with: pip install reportlab. Error: {str(e)}"


# Import reportlab components with error handling
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class EnhancedPDFGenerator:
    """
    Enhanced PDF generator that creates comprehensive reports directly from data structures
    using reportlab. Eliminates all WeasyPrint dependencies and system requirements.
    """
    
    def __init__(self):
        """Initialize the enhanced PDF generator"""
        self.styles = None
        self.is_available = REPORTLAB_AVAILABLE
        
        if self.is_available:
            self._setup_styles()
        else:
            logger.warning("Reportlab not available - PDF generation will be disabled")
    
    def validate_dependencies(self) -> Tuple[bool, str]:
        """
        Validate that required dependencies are available
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        return validate_dependencies()
    
    def _setup_styles(self):
        """Setup comprehensive PDF styles and themes"""
        if not REPORTLAB_AVAILABLE:
            return
            
        self.styles = getSampleStyleSheet()
        
        # Main title style
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontSize=28,
            spaceAfter=30,
            spaceBefore=20,
            textColor=colors.HexColor('#1f77b4'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=15,
            spaceBefore=20,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.HexColor('#3498db'),
            borderPadding=8,
            backColor=colors.HexColor('#f8f9fa')
        ))
        
        # Subsection heading style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.HexColor('#34495e'),
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leftIndent=10,
            fontName='Helvetica'
        ))
        
        # Summary box style
        self.styles.add(ParagraphStyle(
            name='CustomSummaryBox',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=8,
            leftIndent=20,
            rightIndent=20,
            borderWidth=2,
            borderColor=colors.HexColor('#27ae60'),
            borderPadding=12,
            backColor=colors.HexColor('#f8f9fa'),
            fontName='Helvetica'
        ))
        
        # Risk box styles
        self.styles.add(ParagraphStyle(
            name='CustomRiskBoxLow',
            parent=self.styles['CustomSummaryBox'],
            borderColor=colors.HexColor('#27ae60'),
            backColor=colors.HexColor('#d4edda')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomRiskBoxMedium',
            parent=self.styles['CustomSummaryBox'],
            borderColor=colors.HexColor('#f39c12'),
            backColor=colors.HexColor('#fff3cd')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomRiskBoxHigh',
            parent=self.styles['CustomSummaryBox'],
            borderColor=colors.HexColor('#e74c3c'),
            backColor=colors.HexColor('#f8d7da')
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.HexColor('#6c757d'),
            fontName='Helvetica'
        ))
    
    def generate_comprehensive_report(self,
                                    summary: Dict[str, int],
                                    risk_summary: Dict[str, Any],
                                    resource_changes: List[Dict],
                                    resource_types: Dict[str, int],
                                    plan_data: Dict[str, Any],
                                    template_name: str = "default",
                                    include_sections: Optional[Dict[str, bool]] = None) -> Optional[bytes]:
        """
        Generate a comprehensive PDF report directly from data structures
        
        Args:
            summary: Change summary with create/update/delete counts
            risk_summary: Risk assessment results
            resource_changes: List of resource changes
            resource_types: Dictionary of resource types and counts
            plan_data: Original Terraform plan data
            template_name: Template to use (default, compact, detailed)
            include_sections: Dictionary specifying which sections to include
            
        Returns:
            PDF content as bytes, or None if generation fails
        """
        # Validate dependencies first
        is_valid, error_msg = self.validate_dependencies()
        if not is_valid:
            logger.error(f"PDF generation failed: {error_msg}")
            return None
        
        if not self.is_available:
            logger.error("Reportlab not available for PDF generation")
            return None
        
        try:
            # Create PDF in memory buffer
            buffer = io.BytesIO()
            
            # Configure document with proper page size and margins
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
                title="Terraform Plan Impact Report"
            )
            
            # Build the story (content elements)
            story = []
            
            # Default sections to include
            if include_sections is None:
                include_sections = {
                    'title_page': True,
                    'executive_summary': True,
                    'resource_analysis': True,
                    'risk_assessment': True,
                    'recommendations': True
                }
            
            # Generate sections based on configuration
            if include_sections.get('title_page', True):
                story.extend(self._create_title_page(plan_data, summary))
            
            if include_sections.get('executive_summary', True):
                story.extend(self._create_executive_summary(summary, risk_summary))
            
            if include_sections.get('resource_analysis', True):
                story.extend(self._create_resource_analysis(resource_changes, resource_types))
            
            if include_sections.get('risk_assessment', True):
                story.extend(self._create_risk_assessment(risk_summary))
            
            if include_sections.get('recommendations', True):
                story.extend(self._create_recommendations(summary, risk_summary, resource_changes))
            
            # Build the PDF document
            doc.build(story)
            
            # Get the PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            if pdf_bytes and len(pdf_bytes) > 0:
                logger.info(f"Successfully generated PDF report ({len(pdf_bytes)} bytes)")
                return pdf_bytes
            else:
                logger.error("PDF generation produced empty content")
                return None
                
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}", exc_info=True)
            return None
    
    def _create_title_page(self, plan_data: Dict[str, Any], summary: Dict[str, int]) -> List:
        """
        Create the title page with metadata and summary information
        
        Args:
            plan_data: Original Terraform plan data
            summary: Change summary
            
        Returns:
            List of reportlab elements for the title page
        """
        story = []
        
        # Main title
        story.append(Paragraph("🚀 Terraform Plan Impact Report", self.styles['MainTitle']))
        story.append(Spacer(1, 30))
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate total changes
        total_changes = summary.get('total', sum([
            summary.get('create', 0),
            summary.get('update', 0),
            summary.get('delete', 0),
            summary.get('no-op', 0)
        ]))
        
        # Metadata table
        metadata_data = [
            ['Report Generated:', timestamp],
            ['Terraform Version:', plan_data.get('terraform_version', 'Unknown')],
            ['Format Version:', plan_data.get('format_version', 'Unknown')],
            ['Total Resources:', str(len(plan_data.get('resource_changes', [])))],
            ['Total Changes:', str(total_changes)]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2.5*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 40))
        
        # Quick summary section
        story.append(Paragraph("📊 Quick Summary", self.styles['SubsectionHeading']))
        
        summary_text = f"""
        <b>Resources to Create:</b> {summary.get('create', 0)}<br/>
        <b>Resources to Update:</b> {summary.get('update', 0)}<br/>
        <b>Resources to Delete:</b> {summary.get('delete', 0)}<br/>
        <b>No Changes:</b> {summary.get('no-op', 0)}
        """
        
        story.append(Paragraph(summary_text, self.styles['CustomSummaryBox']))
        story.append(PageBreak())
        
        return story
    
    def _create_executive_summary(self, summary: Dict[str, int], risk_summary: Dict[str, Any]) -> List:
        """
        Create executive summary section with key metrics and risk assessment
        
        Args:
            summary: Change summary
            risk_summary: Risk assessment results
            
        Returns:
            List of reportlab elements for executive summary
        """
        story = []
        
        story.append(Paragraph("📋 Executive Summary", self.styles['SectionHeading']))
        story.append(Spacer(1, 15))
        
        # Calculate total changes
        total_changes = summary.get('total', sum([
            summary.get('create', 0),
            summary.get('update', 0),
            summary.get('delete', 0),
            summary.get('no-op', 0)
        ]))
        
        # Extract risk information
        if isinstance(risk_summary, dict) and 'overall_risk' in risk_summary:
            risk_level = risk_summary['overall_risk'].get('level', 'Unknown')
            risk_score = risk_summary['overall_risk'].get('score', 0)
        else:
            risk_level = risk_summary.get('level', 'Unknown')
            risk_score = risk_summary.get('score', 0)
        
        # Key metrics table
        metrics_data = [
            ['Metric', 'Value', 'Description'],
            ['Total Changes', str(total_changes), 'Total number of resource changes'],
            ['Risk Level', risk_level, 'Overall deployment risk assessment'],
            ['Risk Score', f'{risk_score}/100', 'Numerical risk assessment'],
            ['Create Operations', str(summary.get('create', 0)), 'New resources to be created'],
            ['Update Operations', str(summary.get('update', 0)), 'Existing resources to be modified'],
            ['Delete Operations', str(summary.get('delete', 0)), 'Resources to be removed']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[1.8*inch, 1.2*inch, 2.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        # Risk assessment summary
        risk_style = self._get_risk_style(risk_level)
        risk_text = f"""
        <b>Risk Assessment Summary:</b><br/>
        The deployment has been assessed as <b>{risk_level}</b> risk with a score of <b>{risk_score}/100</b>.<br/>
        {'This requires careful review and testing before deployment.' if risk_level in ['High', 'Critical'] else 'Standard deployment procedures can be followed.'}
        """
        
        story.append(Paragraph(risk_text, risk_style))
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_resource_analysis(self, resource_changes: List[Dict], resource_types: Dict[str, int]) -> List:
        """
        Create detailed resource analysis section
        
        Args:
            resource_changes: List of resource changes
            resource_types: Dictionary of resource types and counts
            
        Returns:
            List of reportlab elements for resource analysis
        """
        story = []
        
        story.append(Paragraph("🔧 Resource Analysis", self.styles['SectionHeading']))
        story.append(Spacer(1, 15))
        
        # Resource types summary
        if resource_types:
            story.append(Paragraph("Resource Types Summary", self.styles['SubsectionHeading']))
            
            # Sort resource types by count (descending)
            sorted_types = sorted(resource_types.items(), key=lambda x: x[1], reverse=True)
            
            type_data = [['Resource Type', 'Count', 'Percentage']]
            total_resources = sum(resource_types.values())
            
            for resource_type, count in sorted_types:
                percentage = (count / total_resources * 100) if total_resources > 0 else 0
                type_data.append([resource_type, str(count), f"{percentage:.1f}%"])
            
            type_table = Table(type_data, colWidths=[2.5*inch, 1*inch, 1*inch])
            type_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            
            story.append(type_table)
            story.append(Spacer(1, 20))
        
        # Detailed changes (limited to first 20 for readability)
        if resource_changes:
            story.append(Paragraph("Detailed Changes (Top 20)", self.styles['SubsectionHeading']))
            
            change_data = [['Resource Address', 'Action', 'Type', 'Provider']]
            
            for i, change in enumerate(resource_changes[:20]):
                address = change.get('address', 'Unknown')
                # Truncate long addresses for better formatting
                if len(address) > 40:
                    address = address[:37] + "..."
                
                actions = change.get('change', {}).get('actions', ['unknown'])
                action_str = ', '.join(actions)
                
                resource_type = change.get('type', 'Unknown')
                provider = change.get('provider_name', 'Unknown')
                if provider != 'Unknown':
                    provider = provider.split('/')[-1]  # Get just the provider name
                
                change_data.append([address, action_str, resource_type, provider])
            
            change_table = Table(change_data, colWidths=[2.2*inch, 0.8*inch, 1.2*inch, 0.8*inch])
            change_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            
            story.append(change_table)
            
            # Add note if there are more changes
            if len(resource_changes) > 20:
                story.append(Spacer(1, 10))
                story.append(Paragraph(
                    f"<i>... and {len(resource_changes) - 20} more resource changes</i>",
                    self.styles['Metadata']
                ))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_risk_assessment(self, risk_summary: Dict[str, Any]) -> List:
        """
        Create risk assessment section with detailed analysis
        
        Args:
            risk_summary: Risk assessment results
            
        Returns:
            List of reportlab elements for risk assessment
        """
        story = []
        
        story.append(Paragraph("⚠️ Risk Assessment", self.styles['SectionHeading']))
        story.append(Spacer(1, 15))
        
        # Extract risk information
        if isinstance(risk_summary, dict) and 'overall_risk' in risk_summary:
            risk_level = risk_summary['overall_risk'].get('level', 'Unknown')
            risk_score = risk_summary['overall_risk'].get('score', 0)
            risk_factors = risk_summary['overall_risk'].get('risk_factors', [])
        else:
            risk_level = risk_summary.get('level', 'Unknown')
            risk_score = risk_summary.get('score', 0)
            risk_factors = risk_summary.get('risk_factors', [])
        
        # Overall risk assessment
        risk_style = self._get_risk_style(risk_level)
        risk_text = f"""
        <b>Overall Risk Level:</b> {risk_level}<br/>
        <b>Risk Score:</b> {risk_score}/100<br/>
        <b>Assessment:</b> {self._get_risk_description(risk_level)}
        """
        
        story.append(Paragraph(risk_text, risk_style))
        story.append(Spacer(1, 15))
        
        # Risk factors
        if risk_factors:
            story.append(Paragraph("Identified Risk Factors", self.styles['SubsectionHeading']))
            
            for factor in risk_factors:
                story.append(Paragraph(f"• {factor}", self.styles['CustomBodyText']))
            
            story.append(Spacer(1, 15))
        
        # Risk mitigation strategies
        story.append(Paragraph("Risk Mitigation Strategies", self.styles['SubsectionHeading']))
        
        mitigation_strategies = [
            "Review all resource deletions carefully before deployment",
            "Test changes in a staging environment first",
            "Ensure proper backup procedures are in place",
            "Monitor resource quotas and limits",
            "Validate security group and network changes",
            "Have a rollback plan ready in case of issues"
        ]
        
        # Add risk-specific strategies
        if risk_level in ['High', 'Critical']:
            mitigation_strategies.extend([
                "Consider phased deployment approach",
                "Have senior team member review the changes",
                "Schedule deployment during low-traffic periods"
            ])
        
        for strategy in mitigation_strategies:
            story.append(Paragraph(f"• {strategy}", self.styles['CustomBodyText']))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_recommendations(self, summary: Dict[str, int], risk_summary: Dict[str, Any], resource_changes: List[Dict]) -> List:
        """
        Create recommendations section based on analysis
        
        Args:
            summary: Change summary
            risk_summary: Risk assessment results
            resource_changes: List of resource changes
            
        Returns:
            List of reportlab elements for recommendations
        """
        story = []
        
        story.append(Paragraph("💡 Recommendations", self.styles['SectionHeading']))
        story.append(Spacer(1, 15))
        
        recommendations = []
        
        # Extract risk level
        if isinstance(risk_summary, dict) and 'overall_risk' in risk_summary:
            risk_level = risk_summary['overall_risk'].get('level', 'Unknown')
        else:
            risk_level = risk_summary.get('level', 'Unknown')
        
        # Risk-based recommendations
        if risk_level == 'Critical':
            recommendations.extend([
                "🚨 Critical Risk Deployment - Requires senior approval and extensive testing",
                "🔄 Consider breaking this deployment into smaller, incremental changes",
                "🧪 Mandatory staging environment testing before production deployment",
                "📋 Prepare detailed rollback procedures and test them"
            ])
        elif risk_level == 'High':
            recommendations.extend([
                "⚠️ High Risk Deployment - Requires careful review and testing",
                "🧪 Test thoroughly in staging environment",
                "📋 Prepare rollback procedures"
            ])
        elif risk_level == 'Medium':
            recommendations.extend([
                "🔍 Medium Risk Deployment - Standard review process recommended",
                "🧪 Test in staging environment if possible"
            ])
        else:
            recommendations.append("✅ Low Risk Deployment - Standard deployment process")
        
        # Change-specific recommendations
        if summary.get('delete', 0) > 0:
            recommendations.append(f"🗑️ Resource Deletion - {summary['delete']} resources will be deleted. Ensure data backup if needed")
        
        total_changes = sum([summary.get('create', 0), summary.get('update', 0), summary.get('delete', 0)])
        if total_changes > 50:
            recommendations.append("📊 Large Deployment - Consider phased deployment approach")
        
        # Security-related recommendations
        security_resources = [change for change in resource_changes 
                            if any(sec_type in change.get('type', '').lower() 
                                  for sec_type in ['security_group', 'iam', 'policy', 'role', 'key'])]
        
        if security_resources:
            recommendations.append(f"🔒 Security Resources - {len(security_resources)} security-related resources detected. Review permissions carefully")
        
        # Display recommendations
        for rec in recommendations:
            story.append(Paragraph(rec, self.styles['CustomBodyText']))
        
        story.append(Spacer(1, 20))
        
        # Best practices section
        story.append(Paragraph("🎯 Deployment Best Practices", self.styles['SubsectionHeading']))
        
        best_practices = [
            "Have team members review this plan before deployment",
            "Ensure current backups of critical resources",
            "Set up monitoring for new and modified resources",
            "Document any manual steps required post-deployment",
            "Notify stakeholders of planned changes and timeline"
        ]
        
        for practice in best_practices:
            story.append(Paragraph(f"• {practice}", self.styles['CustomBodyText']))
        
        return story
    
    def _get_risk_style(self, risk_level: str) -> str:
        """
        Get the appropriate style based on risk level
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Style name for the risk level
        """
        risk_level_lower = risk_level.lower()
        if risk_level_lower in ['high', 'critical']:
            return self.styles['CustomRiskBoxHigh']
        elif risk_level_lower == 'medium':
            return self.styles['CustomRiskBoxMedium']
        else:
            return self.styles['CustomRiskBoxLow']
    
    def _get_risk_description(self, risk_level: str) -> str:
        """
        Get risk description based on level
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Description of the risk level
        """
        descriptions = {
            'Low': 'Safe to proceed with standard deployment procedures',
            'Medium': 'Proceed with caution and standard review process',
            'High': 'Requires careful review and testing before deployment',
            'Critical': 'High-risk deployment requiring extensive review and approval'
        }
        return descriptions.get(risk_level, 'Risk level assessment unavailable')


def create_enhanced_pdf_generator() -> EnhancedPDFGenerator:
    """
    Factory function to create an enhanced PDF generator instance
    
    Returns:
        EnhancedPDFGenerator instance
    """
    return EnhancedPDFGenerator()