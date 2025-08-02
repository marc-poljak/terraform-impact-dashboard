"""
Enhanced PDF Generator

A comprehensive PDF generator using pure Python libraries (reportlab) to generate
PDFs directly from data structures. This eliminates all WeasyPrint dependencies
and system library requirements.

Requirements addressed: 1.1, 1.4, 2.1, 2.2, 2.4, 3.5
"""

import io
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import hashlib
from dataclasses import dataclass, field

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
    from reportlab.lib.pagesizes import letter, A4, LETTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


@dataclass
class PDFStyleConfig:
    """Configuration for PDF styling and appearance"""
    primary_color: str = "#1f77b4"
    secondary_color: str = "#2c3e50"
    accent_color: str = "#3498db"
    success_color: str = "#27ae60"
    warning_color: str = "#f39c12"
    danger_color: str = "#e74c3c"
    light_bg_color: str = "#f8f9fa"
    medium_bg_color: str = "#e9ecef"
    font_family: str = "Helvetica"
    font_family_bold: str = "Helvetica-Bold"
    page_size: str = "A4"
    margins: Dict[str, float] = field(default_factory=lambda: {
        "top": 72, "bottom": 72, "left": 72, "right": 72
    })


@dataclass
class PDFSectionConfig:
    """Configuration for which sections to include in the PDF"""
    title_page: bool = True
    executive_summary: bool = True
    resource_analysis: bool = True
    risk_assessment: bool = True
    recommendations: bool = True
    appendix: bool = False


@dataclass
class PDFTemplateConfig:
    """Configuration for PDF templates"""
    name: str
    style_config: PDFStyleConfig
    section_config: PDFSectionConfig
    compact_mode: bool = False
    detailed_mode: bool = False
    max_resources_shown: int = 20


class PDFTemplateManager:
    """Manages PDF templates and their configurations"""
    
    def __init__(self):
        """Initialize the template manager with predefined templates"""
        self.templates = self._create_default_templates()
    
    def _create_default_templates(self) -> Dict[str, PDFTemplateConfig]:
        """Create the default set of PDF templates"""
        templates = {}
        
        # Default template
        default_style = PDFStyleConfig()
        default_sections = PDFSectionConfig()
        templates["default"] = PDFTemplateConfig(
            name="default",
            style_config=default_style,
            section_config=default_sections,
            max_resources_shown=20
        )
        
        # Compact template
        compact_style = PDFStyleConfig(
            primary_color="#34495e",
            secondary_color="#2c3e50",
            accent_color="#3498db",
            margins={"top": 50, "bottom": 50, "left": 50, "right": 50}
        )
        compact_sections = PDFSectionConfig(
            title_page=True,
            executive_summary=True,
            resource_analysis=True,
            risk_assessment=False,
            recommendations=False,
            appendix=False
        )
        templates["compact"] = PDFTemplateConfig(
            name="compact",
            style_config=compact_style,
            section_config=compact_sections,
            compact_mode=True,
            max_resources_shown=10
        )
        
        # Detailed template
        detailed_style = PDFStyleConfig(
            primary_color="#2c3e50",
            secondary_color="#34495e",
            accent_color="#3498db",
            margins={"top": 72, "bottom": 72, "left": 72, "right": 72}
        )
        detailed_sections = PDFSectionConfig(
            title_page=True,
            executive_summary=True,
            resource_analysis=True,
            risk_assessment=True,
            recommendations=True,
            appendix=True
        )
        templates["detailed"] = PDFTemplateConfig(
            name="detailed",
            style_config=detailed_style,
            section_config=detailed_sections,
            detailed_mode=True,
            max_resources_shown=50
        )
        
        return templates
    
    def get_template(self, template_name: str) -> PDFTemplateConfig:
        """Get a template configuration by name"""
        return self.templates.get(template_name, self.templates["default"])
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names"""
        return list(self.templates.keys())


class EnhancedPDFGenerator:
    """
    Enhanced PDF generator that creates comprehensive reports directly from data structures
    using reportlab. Eliminates all WeasyPrint dependencies and system requirements.
    """
    
    def __init__(self):
        """Initialize the enhanced PDF generator"""
        self.styles = None
        self.is_available = REPORTLAB_AVAILABLE
        self.template_manager = PDFTemplateManager()
        self.current_template = None
        
        if self.is_available:
            self._setup_base_styles()
        else:
            logger.warning("Reportlab not available - PDF generation will be disabled")
    
    def validate_dependencies(self) -> Tuple[bool, str]:
        """
        Validate that required dependencies are available
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        return validate_dependencies()
    
    def _setup_base_styles(self):
        """Setup base PDF styles that will be customized per template"""
        if not REPORTLAB_AVAILABLE:
            return
            
        self.base_styles = getSampleStyleSheet()
    
    def _setup_template_styles(self, style_config: PDFStyleConfig):
        """Setup comprehensive PDF styles based on template configuration"""
        if not REPORTLAB_AVAILABLE:
            return
            
        self.styles = getSampleStyleSheet()
        
        # Get colors from config
        primary_color = colors.HexColor(style_config.primary_color)
        secondary_color = colors.HexColor(style_config.secondary_color)
        accent_color = colors.HexColor(style_config.accent_color)
        success_color = colors.HexColor(style_config.success_color)
        warning_color = colors.HexColor(style_config.warning_color)
        danger_color = colors.HexColor(style_config.danger_color)
        light_bg = colors.HexColor(style_config.light_bg_color)
        medium_bg = colors.HexColor(style_config.medium_bg_color)
        
        # Font settings
        font_family = style_config.font_family
        font_family_bold = style_config.font_family_bold
        
        # Main title style
        title_size = 28 if not self.current_template.compact_mode else 24
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontSize=title_size,
            spaceAfter=30 if not self.current_template.compact_mode else 20,
            spaceBefore=20 if not self.current_template.compact_mode else 10,
            textColor=primary_color,
            alignment=TA_CENTER,
            fontName=font_family_bold
        ))
        
        # Section heading style
        section_size = 18 if not self.current_template.compact_mode else 16
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading1'],
            fontSize=section_size,
            spaceAfter=15 if not self.current_template.compact_mode else 10,
            spaceBefore=20 if not self.current_template.compact_mode else 15,
            textColor=secondary_color,
            fontName=font_family_bold,
            borderWidth=1,
            borderColor=accent_color,
            borderPadding=8 if not self.current_template.compact_mode else 6,
            backColor=light_bg
        ))
        
        # Subsection heading style
        subsection_size = 14 if not self.current_template.compact_mode else 12
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading2'],
            fontSize=subsection_size,
            spaceAfter=10 if not self.current_template.compact_mode else 8,
            spaceBefore=15 if not self.current_template.compact_mode else 10,
            textColor=secondary_color,
            fontName=font_family_bold
        ))
        
        # Body text style
        body_size = 11 if not self.current_template.compact_mode else 10
        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=body_size,
            spaceAfter=8 if not self.current_template.compact_mode else 6,
            leftIndent=10 if not self.current_template.compact_mode else 8,
            fontName=font_family,
            alignment=TA_LEFT
        ))
        
        # Summary box style
        summary_size = 12 if not self.current_template.compact_mode else 11
        self.styles.add(ParagraphStyle(
            name='CustomSummaryBox',
            parent=self.styles['Normal'],
            fontSize=summary_size,
            spaceAfter=12 if not self.current_template.compact_mode else 8,
            spaceBefore=8 if not self.current_template.compact_mode else 6,
            leftIndent=20 if not self.current_template.compact_mode else 15,
            rightIndent=20 if not self.current_template.compact_mode else 15,
            borderWidth=2,
            borderColor=success_color,
            borderPadding=12 if not self.current_template.compact_mode else 8,
            backColor=light_bg,
            fontName=font_family
        ))
        
        # Risk box styles
        self.styles.add(ParagraphStyle(
            name='CustomRiskBoxLow',
            parent=self.styles['CustomSummaryBox'],
            borderColor=success_color,
            backColor=colors.HexColor('#d4edda')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomRiskBoxMedium',
            parent=self.styles['CustomSummaryBox'],
            borderColor=warning_color,
            backColor=colors.HexColor('#fff3cd')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomRiskBoxHigh',
            parent=self.styles['CustomSummaryBox'],
            borderColor=danger_color,
            backColor=colors.HexColor('#f8d7da')
        ))
        
        # Metadata style
        metadata_size = 10 if not self.current_template.compact_mode else 9
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=metadata_size,
            spaceAfter=6 if not self.current_template.compact_mode else 4,
            textColor=colors.HexColor('#6c757d'),
            fontName=font_family
        ))
        
        # AppendixHeading style (always available for appendix sections)
        self.styles.add(ParagraphStyle(
            name='AppendixHeading',
            parent=self.styles['SubsectionHeading'],
            fontSize=12,
            textColor=colors.HexColor('#7f8c8d')
        ))
        
        # Detailed mode specific styles
        if self.current_template.detailed_mode:
            self.styles.add(ParagraphStyle(
                name='DetailedBodyText',
                parent=self.styles['CustomBodyText'],
                fontSize=10,
                spaceAfter=6,
                alignment=TA_JUSTIFY
            ))
    
    def generate_comprehensive_report(self,
                                    summary: Dict[str, int],
                                    risk_summary: Dict[str, Any],
                                    resource_changes: List[Dict],
                                    resource_types: Dict[str, int],
                                    plan_data: Dict[str, Any],
                                    template_name: str = "default",
                                    include_sections: Optional[Dict[str, bool]] = None,
                                    custom_style_config: Optional[PDFStyleConfig] = None,
                                    progress_callback: Optional[callable] = None) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Generate a comprehensive PDF report directly from data structures with enhanced error handling
        
        Args:
            summary: Change summary with create/update/delete counts
            risk_summary: Risk assessment results
            resource_changes: List of resource changes
            resource_types: Dictionary of resource types and counts
            plan_data: Original Terraform plan data
            template_name: Template to use (default, compact, detailed)
            include_sections: Dictionary specifying which sections to include
            custom_style_config: Optional custom style configuration
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (PDF content as bytes or None, error message or None)
        """
        # Initialize progress tracking
        if progress_callback:
            progress_callback(0.0, "🔍 Validating dependencies...")
        
        # Validate dependencies first
        is_valid, error_msg = self.validate_dependencies()
        if not is_valid:
            detailed_error = f"PDF generation failed due to missing dependencies: {error_msg}"
            logger.error(detailed_error)
            return None, detailed_error
        
        if not self.is_available:
            error_msg = "Reportlab library not available for PDF generation. Please install reportlab: pip install reportlab"
            logger.error(error_msg)
            return None, error_msg
        
        # Validate input data
        validation_error = self._validate_input_data(summary, risk_summary, resource_changes, resource_types, plan_data)
        if validation_error:
            logger.error(f"Input validation failed: {validation_error}")
            return None, f"Input data validation failed: {validation_error}"
        
        try:
            if progress_callback:
                progress_callback(0.1, "⚙️ Setting up PDF template...")
            
            # Get template configuration
            self.current_template = self.template_manager.get_template(template_name)
            
            # Use custom style config if provided, otherwise use template's config
            style_config = custom_style_config or self.current_template.style_config
            
            # Setup styles based on template
            self._setup_template_styles(style_config)
            
            if progress_callback:
                progress_callback(0.2, "📄 Creating PDF document structure...")
            
            # Create PDF in memory buffer
            buffer = io.BytesIO()
            
            # Get page size
            page_size = A4 if style_config.page_size == "A4" else LETTER
            
            # Configure document with template-specific settings
            doc = SimpleDocTemplate(
                buffer,
                pagesize=page_size,
                rightMargin=style_config.margins["right"],
                leftMargin=style_config.margins["left"],
                topMargin=style_config.margins["top"],
                bottomMargin=style_config.margins["bottom"],
                title="Terraform Plan Impact Report"
            )
            
            # Build the story (content elements)
            story = []
            
            # Use template sections if include_sections not provided
            if include_sections is None:
                template_sections = self.current_template.section_config
                include_sections = {
                    'title_page': template_sections.title_page,
                    'executive_summary': template_sections.executive_summary,
                    'resource_analysis': template_sections.resource_analysis,
                    'risk_assessment': template_sections.risk_assessment,
                    'recommendations': template_sections.recommendations,
                    'appendix': template_sections.appendix
                }
            
            # Count enabled sections for progress tracking
            enabled_sections = sum(1 for enabled in include_sections.values() if enabled)
            section_progress_step = 0.6 / max(enabled_sections, 1)  # 60% of progress for sections
            current_section = 0
            
            # Generate sections based on configuration
            if include_sections.get('title_page', True):
                if progress_callback:
                    progress_callback(0.3 + current_section * section_progress_step, "📋 Creating title page...")
                try:
                    story.extend(self._create_title_page(plan_data, summary))
                    current_section += 1
                except Exception as e:
                    error_msg = f"Failed to create title page: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    return None, error_msg
            
            if include_sections.get('executive_summary', True):
                if progress_callback:
                    progress_callback(0.3 + current_section * section_progress_step, "📊 Creating executive summary...")
                try:
                    story.extend(self._create_executive_summary(summary, risk_summary))
                    current_section += 1
                except Exception as e:
                    error_msg = f"Failed to create executive summary: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    return None, error_msg
            
            if include_sections.get('resource_analysis', True):
                if progress_callback:
                    progress_callback(0.3 + current_section * section_progress_step, "🔍 Creating resource analysis...")
                try:
                    story.extend(self._create_resource_analysis(resource_changes, resource_types))
                    current_section += 1
                except Exception as e:
                    error_msg = f"Failed to create resource analysis: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    return None, error_msg
            
            if include_sections.get('risk_assessment', True):
                if progress_callback:
                    progress_callback(0.3 + current_section * section_progress_step, "⚠️ Creating risk assessment...")
                try:
                    story.extend(self._create_risk_assessment(risk_summary))
                    current_section += 1
                except Exception as e:
                    error_msg = f"Failed to create risk assessment: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    return None, error_msg
            
            if include_sections.get('recommendations', True):
                if progress_callback:
                    progress_callback(0.3 + current_section * section_progress_step, "💡 Creating recommendations...")
                try:
                    story.extend(self._create_recommendations(summary, risk_summary, resource_changes))
                    current_section += 1
                except Exception as e:
                    error_msg = f"Failed to create recommendations: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    return None, error_msg
            
            if include_sections.get('appendix', False):
                if progress_callback:
                    progress_callback(0.3 + current_section * section_progress_step, "📎 Creating appendix...")
                try:
                    story.extend(self._create_appendix(plan_data, resource_changes))
                    current_section += 1
                except Exception as e:
                    error_msg = f"Failed to create appendix: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    return None, error_msg
            
            if progress_callback:
                progress_callback(0.9, "🔨 Building final PDF document...")
            
            # Build the PDF document
            try:
                doc.build(story)
            except Exception as e:
                error_msg = f"Failed to build PDF document: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return None, error_msg
            
            if progress_callback:
                progress_callback(0.95, "✅ Finalizing PDF...")
            
            # Get the PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            if pdf_bytes and len(pdf_bytes) > 0:
                if progress_callback:
                    progress_callback(1.0, f"✅ PDF generated successfully ({len(pdf_bytes)} bytes)")
                logger.info(f"Successfully generated PDF report using '{template_name}' template ({len(pdf_bytes)} bytes)")
                return pdf_bytes, None
            else:
                error_msg = "PDF generation produced empty content - this may indicate a data processing issue"
                logger.error(error_msg)
                return None, error_msg
                
        except MemoryError as e:
            error_msg = f"Insufficient memory to generate PDF. Try using a smaller template or reducing data size: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg
        except ImportError as e:
            error_msg = f"Missing required PDF generation dependencies: {str(e)}. Please install reportlab: pip install reportlab"
            logger.error(error_msg, exc_info=True)
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during PDF generation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg
    
    def _validate_input_data(self, summary: Dict[str, int], risk_summary: Dict[str, Any], 
                           resource_changes: List[Dict], resource_types: Dict[str, int], 
                           plan_data: Dict[str, Any]) -> Optional[str]:
        """
        Validate input data for PDF generation
        
        Args:
            summary: Change summary
            risk_summary: Risk assessment results
            resource_changes: List of resource changes
            resource_types: Dictionary of resource types and counts
            plan_data: Original Terraform plan data
            
        Returns:
            Error message if validation fails, None if valid
        """
        try:
            # Validate summary data
            if not isinstance(summary, dict):
                return "Summary must be a dictionary"
            
            required_summary_keys = ['create', 'update', 'delete']
            for key in required_summary_keys:
                if key not in summary:
                    return f"Summary missing required key: {key}"
                if not isinstance(summary[key], int) or summary[key] < 0:
                    return f"Summary key '{key}' must be a non-negative integer"
            
            # Validate risk summary
            if not isinstance(risk_summary, dict):
                return "Risk summary must be a dictionary"
            
            # Validate resource changes
            if not isinstance(resource_changes, list):
                return "Resource changes must be a list"
            
            # Validate resource types
            if not isinstance(resource_types, dict):
                return "Resource types must be a dictionary"
            
            # Validate plan data
            if not isinstance(plan_data, dict):
                return "Plan data must be a dictionary"
            
            # Check for reasonable data sizes
            if len(resource_changes) > 10000:
                return f"Too many resource changes ({len(resource_changes)}). Maximum supported: 10,000"
            
            if len(resource_types) > 1000:
                return f"Too many resource types ({len(resource_types)}). Maximum supported: 1,000"
            
            return None
            
        except Exception as e:
            return f"Validation error: {str(e)}"
    
    def generate_fallback_report(self, summary: Dict[str, int], risk_summary: Dict[str, Any], 
                               resource_changes: List[Dict], resource_types: Dict[str, int], 
                               plan_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate a fallback text report when PDF generation fails
        
        Args:
            summary: Change summary
            risk_summary: Risk assessment results
            resource_changes: List of resource changes
            resource_types: Dictionary of resource types and counts
            plan_data: Original Terraform plan data
            
        Returns:
            Tuple of (report content as text, suggested filename)
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report_lines = []
            
            # Header
            report_lines.extend([
                "=" * 80,
                "TERRAFORM PLAN IMPACT REPORT (TEXT FALLBACK)",
                "=" * 80,
                f"Generated: {timestamp}",
                f"Terraform Version: {plan_data.get('terraform_version', 'Unknown')}",
                "",
            ])
            
            # Executive Summary
            report_lines.extend([
                "EXECUTIVE SUMMARY",
                "-" * 40,
                f"Total Changes: {summary.get('total', sum(summary.get(k, 0) for k in ['create', 'update', 'delete']))}",
                f"Create Operations: {summary.get('create', 0)}",
                f"Update Operations: {summary.get('update', 0)}",
                f"Delete Operations: {summary.get('delete', 0)}",
                "",
            ])
            
            # Risk Assessment
            if isinstance(risk_summary, dict) and 'overall_risk' in risk_summary:
                risk_level = risk_summary['overall_risk'].get('level', 'Unknown')
                risk_score = risk_summary['overall_risk'].get('score', 0)
            else:
                risk_level = risk_summary.get('level', 'Unknown')
                risk_score = risk_summary.get('score', 0)
            
            report_lines.extend([
                "RISK ASSESSMENT",
                "-" * 40,
                f"Overall Risk Level: {risk_level}",
                f"Risk Score: {risk_score}/100",
                "",
            ])
            
            # Resource Type Breakdown
            report_lines.extend([
                "RESOURCE TYPE BREAKDOWN",
                "-" * 40,
            ])
            
            for resource_type, count in sorted(resource_types.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"{resource_type}: {count}")
            
            report_lines.append("")
            
            # Resource Changes (limited to first 50 for readability)
            report_lines.extend([
                "RESOURCE CHANGES (First 50)",
                "-" * 40,
            ])
            
            for i, change in enumerate(resource_changes[:50]):
                address = change.get('address', 'Unknown')
                resource_type = change.get('type', 'Unknown')
                action = change.get('change', {}).get('actions', ['unknown'])[0]
                report_lines.append(f"{i+1:3d}. [{action.upper()}] {address} ({resource_type})")
            
            if len(resource_changes) > 50:
                report_lines.append(f"... and {len(resource_changes) - 50} more changes")
            
            report_lines.extend([
                "",
                "=" * 80,
                "END OF REPORT",
                "=" * 80,
                "",
                "NOTE: This is a fallback text report generated when PDF creation failed.",
                "For full functionality, please ensure reportlab is properly installed.",
            ])
            
            report_content = "\n".join(report_lines)
            filename = f"terraform-plan-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
            
            return report_content, filename
            
        except Exception as e:
            # Ultimate fallback - minimal report
            error_report = f"""
TERRAFORM PLAN REPORT - MINIMAL FALLBACK
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ERROR: Could not generate detailed report due to: {str(e)}

BASIC SUMMARY:
- Create: {summary.get('create', 0)}
- Update: {summary.get('update', 0)}  
- Delete: {summary.get('delete', 0)}
- Total Resources: {len(resource_changes)}

Please check your data and try again.
"""
            filename = f"terraform-plan-error-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
            return error_report, filename
    
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
        
        # Professional header section
        story.extend(self._create_professional_header())
        
        # Main title with enhanced styling
        story.append(Spacer(1, 20))
        story.append(Paragraph("🚀 Terraform Plan Impact Report", self.styles['MainTitle']))
        story.append(Spacer(1, 10))
        
        # Subtitle with version information
        subtitle_text = f"Infrastructure Change Analysis & Risk Assessment"
        story.append(Paragraph(subtitle_text, self.styles['SubsectionHeading']))
        story.append(Spacer(1, 30))
        
        # Generate comprehensive metadata
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_version = "1.0.0"  # Could be made configurable
        
        # Calculate comprehensive statistics
        total_changes = summary.get('total', sum([
            summary.get('create', 0),
            summary.get('update', 0),
            summary.get('delete', 0),
            summary.get('no-op', 0)
        ]))
        
        total_resources = len(plan_data.get('resource_changes', []))
        
        # Enhanced metadata table with more comprehensive information
        metadata_data = [
            ['Report Information', ''],
            ['Generated:', timestamp],
            ['Report Version:', report_version],
            ['Document ID:', f"TF-{datetime.now().strftime('%Y%m%d-%H%M%S')}"],
            ['', ''],
            ['Terraform Configuration', ''],
            ['Terraform Version:', plan_data.get('terraform_version', 'Unknown')],
            ['Plan Format Version:', plan_data.get('format_version', 'Unknown')],
            ['Configuration Hash:', self._generate_config_hash(plan_data)],
            ['', ''],
            ['Resource Summary', ''],
            ['Total Resources in Plan:', str(total_resources)],
            ['Resources with Changes:', str(total_changes)],
            ['Resources Unchanged:', str(summary.get('no-op', 0))],
            ['Change Percentage:', f"{(total_changes/total_resources*100):.1f}%" if total_resources > 0 else "0%"]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2.8*inch, 2.7*inch])
        metadata_table.setStyle(TableStyle([
            # Header rows styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 5), (-1, 5), colors.white),
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 10), (-1, 10), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 10), (-1, 10), colors.white),
            ('FONTNAME', (0, 10), (-1, 10), 'Helvetica-Bold'),
            
            # Empty row styling
            ('BACKGROUND', (0, 4), (-1, 4), colors.white),
            ('BACKGROUND', (0, 9), (-1, 9), colors.white),
            ('LINEBELOW', (0, 4), (-1, 4), 0, colors.white),
            ('LINEBELOW', (0, 9), (-1, 9), 0, colors.white),
            
            # General styling
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 30))
        
        # Enhanced summary section with visual indicators
        story.append(Paragraph("📊 Change Summary Overview", self.styles['SubsectionHeading']))
        story.append(Spacer(1, 10))
        
        # Create visual summary with color coding
        summary_data = [
            ['Change Type', 'Count', 'Impact Level', 'Description'],
            ['Create', str(summary.get('create', 0)), self._get_impact_level('create'), 'New resources to be provisioned'],
            ['Update', str(summary.get('update', 0)), self._get_impact_level('update'), 'Existing resources to be modified'],
            ['Delete', str(summary.get('delete', 0)), self._get_impact_level('delete'), 'Resources to be removed'],
            ['No Change', str(summary.get('no-op', 0)), self._get_impact_level('no-op'), 'Resources with no modifications']
        ]
        
        summary_table = Table(summary_data, colWidths=[1.2*inch, 0.8*inch, 1.2*inch, 2.3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Color coding for different change types
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#d4edda')),  # Create - green
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#fff3cd')),  # Update - yellow
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#f8d7da')),  # Delete - red
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#e2e3e5')),  # No-op - gray
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Professional footer for title page
        story.extend(self._create_professional_footer())
        story.append(PageBreak())
        
        return story
    
    def _create_professional_header(self) -> List:
        """
        Create a professional header for the document
        
        Returns:
            List of reportlab elements for the header
        """
        header_elements = []
        
        # Header line
        header_line_data = [['Terraform Infrastructure Analysis Report']]
        header_table = Table(header_line_data, colWidths=[6*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        header_elements.append(header_table)
        header_elements.append(Spacer(1, 5))
        
        return header_elements
    
    def _create_professional_footer(self) -> List:
        """
        Create a professional footer for the document
        
        Returns:
            List of reportlab elements for the footer
        """
        footer_elements = []
        
        footer_elements.append(Spacer(1, 20))
        
        # Footer information
        footer_text = f"""
        <i>This report was automatically generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}.<br/>
        Report contains analysis of Terraform plan changes and associated risk assessment.<br/>
        For questions or support, please contact your infrastructure team.</i>
        """
        
        footer_elements.append(Paragraph(footer_text, self.styles['Metadata']))
        
        # Footer line
        footer_line_data = [['End of Title Page']]
        footer_table = Table(footer_line_data, colWidths=[6*inch])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#7f8c8d')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        footer_elements.append(Spacer(1, 10))
        footer_elements.append(footer_table)
        
        return footer_elements
    
    def _generate_config_hash(self, plan_data: Dict[str, Any]) -> str:
        """
        Generate a simple hash for the configuration to help with tracking
        
        Args:
            plan_data: Terraform plan data
            
        Returns:
            Configuration hash string
        """
        import hashlib
        
        # Create a simple hash based on terraform version and resource count
        hash_input = f"{plan_data.get('terraform_version', 'unknown')}-{len(plan_data.get('resource_changes', []))}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()
    
    def _get_impact_level(self, change_type: str) -> str:
        """
        Get impact level description for different change types
        
        Args:
            change_type: Type of change (create, update, delete, no-op)
            
        Returns:
            Impact level description
        """
        impact_levels = {
            'create': 'Low',
            'update': 'Medium',
            'delete': 'High',
            'no-op': 'None'
        }
        return impact_levels.get(change_type, 'Unknown')
    
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
        
        # Detailed changes (limited based on template configuration)
        if resource_changes:
            max_resources = self.current_template.max_resources_shown
            title = f"Detailed Changes (Top {max_resources})" if len(resource_changes) > max_resources else "Detailed Changes"
            story.append(Paragraph(title, self.styles['SubsectionHeading']))
            
            change_data = [['Resource Address', 'Action', 'Type', 'Provider']]
            
            for i, change in enumerate(resource_changes[:max_resources]):
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
            max_resources = self.current_template.max_resources_shown
            if len(resource_changes) > max_resources:
                story.append(Spacer(1, 10))
                story.append(Paragraph(
                    f"<i>... and {len(resource_changes) - max_resources} more resource changes</i>",
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
    
    def _create_appendix(self, plan_data: Dict[str, Any], resource_changes: List[Dict]) -> List:
        """
        Create appendix section with additional technical details (detailed template only)
        
        Args:
            plan_data: Original Terraform plan data
            resource_changes: List of resource changes
            
        Returns:
            List of reportlab elements for appendix
        """
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("📎 Appendix", self.styles['SectionHeading']))
        story.append(Spacer(1, 15))
        
        # Technical details section
        story.append(Paragraph("Technical Details", self.styles['AppendixHeading']))
        
        tech_details = [
            f"Terraform Version: {plan_data.get('terraform_version', 'Unknown')}",
            f"Format Version: {plan_data.get('format_version', 'Unknown')}",
            f"Total Resource Changes: {len(resource_changes)}",
            f"Configuration Files: {len(plan_data.get('configuration', {}).get('root_module', {}).get('resources', []))} resources defined"
        ]
        
        # Use appropriate body text style (DetailedBodyText if available, otherwise CustomBodyText)
        body_style = 'DetailedBodyText' if 'DetailedBodyText' in self.styles else 'CustomBodyText'
        
        for detail in tech_details:
            story.append(Paragraph(f"• {detail}", self.styles[body_style]))
        
        story.append(Spacer(1, 15))
        
        # Provider information
        if 'configuration' in plan_data:
            providers = plan_data['configuration'].get('provider_config', {})
            if providers:
                story.append(Paragraph("Provider Configuration", self.styles['AppendixHeading']))
                
                for provider_name, provider_config in providers.items():
                    story.append(Paragraph(f"• {provider_name}: {provider_config.get('name', 'Unknown')}", 
                                         self.styles[body_style]))
                
                story.append(Spacer(1, 15))
        
        # Variables information
        if 'variables' in plan_data:
            variables = plan_data['variables']
            if variables:
                story.append(Paragraph("Variables Used", self.styles['AppendixHeading']))
                
                var_count = len(variables)
                story.append(Paragraph(f"Total variables defined: {var_count}", self.styles[body_style]))
                
                # Show first few variables as examples
                for i, (var_name, var_info) in enumerate(list(variables.items())[:5]):
                    var_value = var_info.get('value', 'Not set')
                    if isinstance(var_value, str) and len(var_value) > 50:
                        var_value = var_value[:47] + "..."
                    story.append(Paragraph(f"• {var_name}: {var_value}", self.styles[body_style]))
                
                if var_count > 5:
                    story.append(Paragraph(f"... and {var_count - 5} more variables", self.styles['Metadata']))
        
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
    
    def get_available_templates(self) -> List[str]:
        """
        Get list of available template names
        
        Returns:
            List of template names
        """
        return self.template_manager.get_available_templates()
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        Get information about a specific template
        
        Args:
            template_name: Name of the template
            
        Returns:
            Dictionary with template information
        """
        template = self.template_manager.get_template(template_name)
        return {
            'name': template.name,
            'compact_mode': template.compact_mode,
            'detailed_mode': template.detailed_mode,
            'max_resources_shown': template.max_resources_shown,
            'sections': {
                'title_page': template.section_config.title_page,
                'executive_summary': template.section_config.executive_summary,
                'resource_analysis': template.section_config.resource_analysis,
                'risk_assessment': template.section_config.risk_assessment,
                'recommendations': template.section_config.recommendations,
                'appendix': template.section_config.appendix
            },
            'style': {
                'primary_color': template.style_config.primary_color,
                'secondary_color': template.style_config.secondary_color,
                'accent_color': template.style_config.accent_color,
                'font_family': template.style_config.font_family,
                'page_size': template.style_config.page_size
            }
        }
    
    def create_custom_template(self, 
                             template_name: str,
                             style_config: Optional[PDFStyleConfig] = None,
                             section_config: Optional[PDFSectionConfig] = None,
                             **kwargs) -> bool:
        """
        Create a custom template configuration
        
        Args:
            template_name: Name for the new template
            style_config: Custom style configuration
            section_config: Custom section configuration
            **kwargs: Additional template options
            
        Returns:
            True if template was created successfully
        """
        try:
            if style_config is None:
                style_config = PDFStyleConfig()
            if section_config is None:
                section_config = PDFSectionConfig()
            
            custom_template = PDFTemplateConfig(
                name=template_name,
                style_config=style_config,
                section_config=section_config,
                compact_mode=kwargs.get('compact_mode', False),
                detailed_mode=kwargs.get('detailed_mode', False),
                max_resources_shown=kwargs.get('max_resources_shown', 20)
            )
            
            self.template_manager.templates[template_name] = custom_template
            logger.info(f"Created custom template: {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create custom template {template_name}: {str(e)}")
            return False


def create_enhanced_pdf_generator() -> EnhancedPDFGenerator:
    """
    Factory function to create an enhanced PDF generator instance
    
    Returns:
        EnhancedPDFGenerator instance
    """
    return EnhancedPDFGenerator()