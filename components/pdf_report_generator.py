"""
Pure Python PDF Report Generator

A clean, minimal-dependency PDF generator using reportlab.
No HTML conversion, no system dependencies, just pure Python magic!
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime
import io

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


class PurePythonPDFGenerator:
    """
    Clean, minimal PDF generator using pure Python.
    No system dependencies, no HTML conversion - just works!
    """
    
    def __init__(self):
        self.styles = None
        if REPORTLAB_AVAILABLE:
            self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom styles for the PDF"""
        self.styles = getSampleStyleSheet()
        
        # Custom title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1f77b4'),
            alignment=TA_CENTER
        ))
        
        # Custom heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#2c3e50'),
            borderWidth=1,
            borderColor=colors.HexColor('#3498db'),
            borderPadding=5
        ))
        
        # Custom body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=10
        ))
        
        # Summary box style
        self.styles.add(ParagraphStyle(
            name='SummaryBox',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            leftIndent=20,
            rightIndent=20,
            borderWidth=1,
            borderColor=colors.HexColor('#27ae60'),
            borderPadding=10,
            backColor=colors.HexColor('#f8f9fa')
        ))
    
    def generate_pdf_report(self, 
                           summary: Dict[str, int],
                           risk_summary: Dict[str, Any],
                           resource_changes: List[Dict],
                           resource_types: Dict[str, int],
                           plan_data: Dict[str, Any],
                           template_name: str = "default") -> Optional[bytes]:
        """
        Generate a beautiful PDF report using pure Python
        
        Returns:
            PDF content as bytes, or None if generation fails
        """
        if not REPORTLAB_AVAILABLE:
            st.error("📄 PDF generation requires reportlab. Install with: pip install reportlab")
            return None
        
        try:
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build the story (content)
            story = []
            
            # Title page
            story.extend(self._create_title_page(plan_data))
            
            # Executive summary
            story.extend(self._create_executive_summary(summary, risk_summary))
            
            # Resource changes section
            story.extend(self._create_resource_changes_section(resource_changes, resource_types))
            
            # Risk analysis section
            story.extend(self._create_risk_analysis_section(risk_summary))
            
            # Build the PDF
            doc.build(story)
            
            # Get the PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
            
        except Exception as e:
            st.error(f"❌ PDF generation failed: {str(e)}")
            return None
    
    def _create_title_page(self, plan_data: Dict[str, Any]) -> List:
        """Create the title page"""
        story = []
        
        # Main title
        story.append(Paragraph("🚀 Terraform Plan Impact Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Metadata table
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = [
            ['Report Generated:', timestamp],
            ['Terraform Version:', plan_data.get('terraform_version', 'Unknown')],
            ['Format Version:', plan_data.get('format_version', 'Unknown')],
            ['Total Resources:', str(len(plan_data.get('resource_changes', [])))]
        ]
        
        metadata_table = Table(metadata, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
        ]))
        
        story.append(metadata_table)
        story.append(PageBreak())
        
        return story
    
    def _create_executive_summary(self, summary: Dict[str, int], risk_summary: Dict[str, Any]) -> List:
        """Create executive summary section"""
        story = []
        
        story.append(Paragraph("📋 Executive Summary", self.styles['CustomHeading']))
        story.append(Spacer(1, 12))
        
        # Calculate total if not present
        total = summary.get('total', sum([
            summary.get('create', 0),
            summary.get('update', 0), 
            summary.get('delete', 0),
            summary.get('no-op', 0)
        ]))
        
        # Summary metrics
        summary_text = f"""
        <b>Total Changes:</b> {total} resources<br/>
        <b>Resources to Create:</b> {summary.get('create', 0)}<br/>
        <b>Resources to Update:</b> {summary.get('update', 0)}<br/>
        <b>Resources to Delete:</b> {summary.get('delete', 0)}<br/>
        <b>No Changes:</b> {summary.get('no-op', 0)}
        """
        
        story.append(Paragraph(summary_text, self.styles['SummaryBox']))
        story.append(Spacer(1, 20))
        
        # Risk assessment
        risk_level = risk_summary.get('level', 'Unknown')
        risk_score = risk_summary.get('score', 0)
        
        risk_text = f"""
        <b>Risk Assessment:</b><br/>
        <b>Risk Level:</b> {risk_level}<br/>
        <b>Risk Score:</b> {risk_score}/100
        """
        
        story.append(Paragraph(risk_text, self.styles['SummaryBox']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_resource_changes_section(self, resource_changes: List[Dict], resource_types: Dict[str, int]) -> List:
        """Create resource changes section"""
        story = []
        
        story.append(Paragraph("🔧 Resource Changes", self.styles['CustomHeading']))
        story.append(Spacer(1, 12))
        
        # Resource types table
        if resource_types:
            story.append(Paragraph("<b>Resource Types Summary:</b>", self.styles['CustomBody']))
            
            type_data = [['Resource Type', 'Count']]
            for resource_type, count in sorted(resource_types.items()):
                type_data.append([resource_type, str(count)])
            
            type_table = Table(type_data, colWidths=[3*inch, 1*inch])
            type_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(type_table)
            story.append(Spacer(1, 20))
        
        # Detailed changes (first 10 for brevity)
        if resource_changes:
            story.append(Paragraph("<b>Detailed Changes (Top 10):</b>", self.styles['CustomBody']))
            
            change_data = [['Resource', 'Action', 'Type']]
            for i, change in enumerate(resource_changes[:10]):
                address = change.get('address', 'Unknown')
                actions = change.get('change', {}).get('actions', ['unknown'])
                action_str = ', '.join(actions)
                resource_type = change.get('type', 'Unknown')
                
                change_data.append([address, action_str, resource_type])
            
            change_table = Table(change_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
            change_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(change_table)
            
            if len(resource_changes) > 10:
                story.append(Spacer(1, 10))
                story.append(Paragraph(f"<i>... and {len(resource_changes) - 10} more changes</i>", self.styles['CustomBody']))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_risk_analysis_section(self, risk_summary: Dict[str, Any]) -> List:
        """Create risk analysis section"""
        story = []
        
        story.append(Paragraph("⚠️ Risk Analysis", self.styles['CustomHeading']))
        story.append(Spacer(1, 12))
        
        # Risk details
        risk_level = risk_summary.get('level', 'Unknown')
        risk_score = risk_summary.get('score', 0)
        
        # Color code based on risk level
        if risk_level.lower() == 'high':
            risk_color = colors.HexColor('#e74c3c')
        elif risk_level.lower() == 'medium':
            risk_color = colors.HexColor('#f39c12')
        else:
            risk_color = colors.HexColor('#27ae60')
        
        risk_text = f"""
        <b>Overall Risk Level:</b> <font color="{risk_color.hexval()}">{risk_level}</font><br/>
        <b>Risk Score:</b> {risk_score}/100<br/>
        <b>Recommendation:</b> {'Proceed with caution' if risk_level.lower() == 'high' else 'Safe to proceed'}
        """
        
        story.append(Paragraph(risk_text, self.styles['SummaryBox']))
        
        # Add recommendations
        story.append(Spacer(1, 15))
        story.append(Paragraph("<b>Recommendations:</b>", self.styles['CustomBody']))
        
        recommendations = [
            "• Review all resource deletions carefully",
            "• Test changes in a staging environment first", 
            "• Ensure proper backup procedures are in place",
            "• Monitor resource quotas and limits",
            "• Validate security group and network changes"
        ]
        
        for rec in recommendations:
            story.append(Paragraph(rec, self.styles['CustomBody']))
        
        return story


def create_simple_pdf_generator():
    """Factory function to create PDF generator"""
    return PurePythonPDFGenerator()