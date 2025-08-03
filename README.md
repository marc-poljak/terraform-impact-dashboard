# 🚀 Terraform Plan Impact Dashboard

A comprehensive, professional web dashboard for visualizing Terraform plan changes, analyzing risk levels, and making data-driven deployment decisions. Built with advanced features for enterprise-grade infrastructure management.

## ✨ Key Features

### 📊 Core Analysis
- **📈 Change Summary**: Visual overview of create/update/delete operations with detailed metrics
- **⚠️ Enhanced Risk Assessment**: Intelligent risk scoring with multi-cloud provider support
- **📊 Interactive Visualizations**: Resource distributions, change flows, risk heatmaps, and dependency graphs
- **🔍 Advanced Filtering**: Multi-criteria filtering by action, resource type, risk level, and provider
- **📥 Data Export**: Export filtered results as CSV with customizable columns

### 🌟 Advanced Features
- **☁️ Multi-Cloud Support**: Analyze plans spanning AWS, Azure, GCP, and other providers
- **🔒 Security Analysis**: Dedicated security-focused resource highlighting and compliance checks
- **📄 Report Generation**: Professional PDF and HTML reports for stakeholders
- **🎯 Smart Defaults**: Pre-configured settings for common use cases (security review, production deployment, etc.)
- **📱 Responsive Design**: Optimized for desktop, tablet, and mobile devices

### 🎓 User Experience
- **🎯 Interactive Guided Tours**: Step-by-step tutorials for new users and complex workflows
- **💡 Contextual Help System**: Comprehensive in-app help with tooltips and expandable sections
- **♿ Full Accessibility**: WCAG 2.1 AA compliant with keyboard navigation and screen reader support
- **🔍 Feature Discovery**: Interactive feature discovery system with progressive hints
- **📢 Feature Announcements**: Built-in system for highlighting new capabilities

![Dashboard Beispiel](assets/dashboard_example.png)

## ⚠️ Disclaimer

**USE AT YOUR OWN RISK**. This tool is provided "as is", without warranty of any kind, express or implied. Neither the authors nor contributors shall be liable for any damages or consequences arising from the use of this tool. Always:

- 🧪 Test in a non-production environment first
- ✓ Verify results manually before taking action
- 💾 Maintain proper backups
- 🔒 Follow your organization's security policies

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)

### Quick Start

1. **Clone the repository:**
```bash
git clone <repository-url>
cd terraform-impact-dashboard
```

2. **Create and activate virtual environment:**
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the dashboard:**
```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Project Structure

```
terraform-impact-dashboard/
├── app.py                           # Main Streamlit application
├── requirements.txt                 # Python dependencies
├── Pipfile                         # Pipenv dependency management
├── Pipfile.lock                    # Locked dependency versions
├── README.md                       # This documentation
├── components/                     # UI Components
│   ├── __init__.py                 # Component module initialization
│   ├── base_component.py           # Base component class
│   ├── header.py                   # Header and navigation
│   ├── sidebar.py                  # Sidebar controls
│   ├── upload_section.py           # File upload interface
│   ├── summary_cards.py            # Summary metrics display
│   ├── visualizations.py           # Chart components
│   ├── data_table.py              # Interactive data table
│   ├── enhanced_sections.py        # Enhanced feature sections
│   ├── help_system.py             # Comprehensive help system
│   ├── report_generator.py        # PDF/HTML report generation
│   ├── enhanced_pdf_generator.py   # Enhanced PDF generation engine
│   ├── security_analysis.py       # Security-focused analysis
│   └── onboarding_checklist.py    # User onboarding
├── parsers/
│   ├── __init__.py                 # Parser module initialization
│   └── plan_parser.py             # Terraform JSON parsing
├── visualizers/
│   ├── __init__.py                 # Visualizer module initialization
│   └── charts.py                  # Plotly chart generators
├── utils/
│   ├── __init__.py                 # Utils module initialization
│   ├── plan_processor.py          # Centralized plan data processing
│   ├── risk_assessment.py         # Basic risk scoring
│   ├── enhanced_risk_assessment.py # Advanced multi-cloud risk analysis
│   ├── security_analyzer.py       # Security analysis utilities
│   └── provider_factory.py        # Provider factory pattern
├── providers/
│   ├── __init__.py                 # Provider module initialization
│   ├── base_provider.py           # Base provider class
│   ├── cloud_detector.py          # Multi-cloud provider detection
│   ├── aws_provider.py            # AWS-specific provider logic
│   ├── azure_provider.py          # Azure-specific provider logic
│   └── gcp_provider.py            # GCP-specific provider logic
├── config/
│   ├── __init__.py                 # Config module initialization
│   ├── provider_settings.py       # Provider configuration settings
│   └── risk_profiles.py           # Risk assessment profiles
├── ui/
│   ├── __init__.py                 # UI module initialization
│   ├── session_manager.py         # Session state management
│   ├── error_handler.py           # Error handling and user guidance
│   ├── progress_tracker.py        # Progress tracking
│   └── performance_optimizer.py   # Performance optimization
├── tests/                          # Comprehensive test suite
│   ├── __init__.py                 # Test module initialization
│   ├── README.md                   # Testing documentation
│   ├── unit/                       # Unit tests (including PDF generator tests)
│   ├── integration/                # Integration tests (including PDF integration)
│   ├── performance/                # Performance tests (including PDF performance)
│   └── fixtures/                   # Test fixtures and sample data
├── assets/
│   └── styles.css                 # Custom CSS styling
└── .kiro/                          # Kiro AI configuration
    └── specs/                      # Project specifications
```

### PDF Report Generation

The dashboard includes an **Enhanced PDF Generator** that creates professional reports using reportlab, a pure Python library with no system dependencies:

**Features:**
- 🎨 **Multiple Templates**: Default, Executive, Technical, and Security-focused templates
- 📊 **Professional Styling**: Clean layouts with proper typography and spacing
- 📈 **Rich Content**: Executive summaries, risk analysis, detailed changes, and recommendations
- 🔧 **Template-Specific Titles**: Each template uses appropriate titles (e.g., "Security Assessment Report")
- 📏 **Smart Sizing**: Automatic file size optimization and display

**Installation:**
```bash
pip install reportlab
```

The reportlab library is included in requirements.txt and installs automatically with `pip install -r requirements.txt`.

**Usage:**
1. Select your preferred template (Default, Executive, Technical, Security)
2. Choose report sections to include
3. Click "Generate Report" to create both HTML and PDF simultaneously
4. Download either format with template-specific titles and styling

## 📁 Usage Guide

### 1. Generate Terraform Plan JSON

First, create a JSON plan file from your Terraform configuration:

```bash
# Generate plan
terraform plan -out=tfplan

# Convert to JSON
terraform show -json tfplan > terraform-plan.json
```

### 2. Upload and Analyze

1. **Upload Plan**: Drag & drop or browse for your JSON file (up to 200MB supported)
2. **Review Summary**: Check the summary cards for change counts and risk levels
3. **Explore Visualizations**: Interactive charts show resource distributions and patterns
4. **Use Data Table**: Filter, search, and examine detailed resource information

## 🔗 TFE Connection Feature

The dashboard includes a powerful **Terraform Cloud/Enterprise (TFE) Integration** that allows you to connect directly to your TFE workspace and analyze plans without manual file downloads.

### ✨ Key Benefits

- **🚀 Direct Connection**: Connect to Terraform Cloud or Enterprise instances
- **⚡ Automated Retrieval**: Fetch plan data directly from workspace runs
- **🔄 Real-time Analysis**: Analyze plans immediately without file downloads
- **🔒 Secure Processing**: All credentials handled securely in memory only
- **📊 Always Current**: Analyze the latest run data automatically

### 🛠️ Setup Requirements

To use the TFE connection feature, you'll need:

1. **TFE Server URL**: Your Terraform Cloud/Enterprise instance
   - Terraform Cloud: `app.terraform.io`
   - Enterprise: Your custom TFE server URL

2. **API Token**: Personal or team token with workspace read permissions
   - Generate in TFE: User Settings → Tokens → Create API Token

3. **Organization Name**: Your TFE organization identifier

4. **Workspace ID**: Target workspace identifier (format: `ws-XXXXXXXXX`)

5. **Run ID**: Specific run to analyze (format: `run-XXXXXXXXX`)

### 📋 Configuration File Format

Create a YAML configuration file with your TFE connection details:

```yaml
# Basic TFE Configuration
tfe_server: app.terraform.io          # or your TFE server URL
organization: my-organization         # Your TFE organization
token: your-api-token-here           # Your TFE API token
workspace_id: ws-ABC123456           # Target workspace ID
run_id: run-XYZ789012               # Specific run to analyze

# Optional settings
verify_ssl: true                     # SSL certificate verification
timeout: 30                         # Request timeout in seconds
retry_attempts: 3                   # Number of retry attempts
```

### 🚀 How to Use TFE Integration

1. **Access TFE Tab**: In the dashboard, click on the "TFE Connection" tab

2. **Upload Configuration**: Upload your YAML configuration file using the file uploader

3. **Automatic Processing**: The dashboard will:
   - ✅ Validate connection to TFE server
   - ✅ Authenticate with your API token
   - ✅ Verify workspace and run access
   - ✅ Retrieve and process plan data

4. **Analyze Results**: Once connected, the plan data flows through the same analysis pipeline as uploaded files

### 🔍 Finding Your IDs

#### Workspace ID
**From TFE URL:**
```
https://app.terraform.io/app/my-org/workspaces/my-workspace
```
The workspace ID can be found in the workspace settings or via API.

**From API:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://app.terraform.io/api/v2/organizations/YOUR_ORG/workspaces
```

#### Run ID
**From Run URL:**
```
https://app.terraform.io/app/my-org/workspaces/my-workspace/runs/run-XXXXXXXXX
```
The run ID is visible in the URL when viewing a specific run.

**From API:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://app.terraform.io/api/v2/workspaces/WORKSPACE_ID/runs
```

### 🔒 Security & Privacy

The TFE integration is designed with security as a top priority:

- **🔐 Memory-Only Storage**: Credentials are never written to disk
- **🧹 Automatic Cleanup**: All data cleared when you close the browser
- **🎭 Masked Display**: Sensitive values are hidden in the UI
- **🔒 Encrypted Communication**: All API calls use HTTPS/TLS
- **📝 No Persistence**: No data stored on servers or in logs
- **🔄 Session Isolation**: Each session is completely independent

### 🎯 Configuration Templates

The dashboard provides several pre-configured templates:

- **🌐 Terraform Cloud**: Standard setup for app.terraform.io
- **🏢 Terraform Enterprise**: Custom server configuration
- **🔧 Development**: Testing and development environments
- **🔒 Production**: High-security production setups

### 🔧 Troubleshooting

#### Authentication Issues
- **Invalid Token**: Generate a new token in TFE user settings
- **Expired Token**: Check token expiration and renew if needed
- **Insufficient Permissions**: Ensure token has workspace read access
- **Wrong Organization**: Verify organization name matches exactly

#### Connection Issues
- **Connection Timeout**: Check internet connectivity and TFE server status
- **SSL Certificate Errors**: Verify TFE server certificate
- **Firewall Blocking**: Ensure outbound HTTPS (port 443) is allowed

#### Data Issues
- **Workspace Not Found**: Verify workspace ID format (`ws-XXXXXXXXX`)
- **Run Not Found**: Check run ID format (`run-XXXXXXXXX`)
- **No JSON Output**: Ensure run completed successfully
- **Empty Plan**: Run may have no changes (normal for up-to-date infrastructure)

### 💡 Best Practices

- **🔑 Use Dedicated Tokens**: Create tokens specifically for dashboard integration
- **🔄 Rotate Regularly**: Change tokens periodically for security
- **📝 Limit Permissions**: Use minimum required permissions
- **🚫 Never Share**: Don't commit configuration files with real tokens
- **💾 Secure Storage**: Store config files securely, not in version control
- **🧪 Test First**: Start with a small, recent run to test your setup

### 3. Advanced Features

#### 🎯 Smart Defaults
Choose from pre-configured settings:
- **Security Review**: Focus on security-related resources and high-risk changes
- **Production Deployment**: Emphasize deletion operations and critical risks
- **Multi-Cloud Migration**: Enable cross-provider analysis
- **Cost Optimization**: Highlight compute and storage resources

#### 🔍 Advanced Filtering
- **Action Filters**: Create, update, delete, replace operations
- **Risk Filters**: Low, medium, high, critical risk levels
- **Provider Filters**: AWS, Azure, GCP, and other cloud providers
- **Text Search**: Search across resource names, types, and addresses

#### 📄 Enhanced Report Generation
1. **Template Selection**: Choose from Default, Executive, Technical, or Security templates
2. **Section Configuration**: Select which sections to include (executive summary, risk analysis, detailed changes, recommendations)
3. **Simultaneous Generation**: Both HTML and PDF are generated together with matching titles and styling
4. **Professional Output**: Template-specific titles, optimized layouts, and proper file size reporting
5. **Easy Download**: Side-by-side download buttons with clear file size information

#### 🎓 Getting Help
- **Guided Tours**: Interactive tutorials for different workflows
- **Contextual Help**: Enable tooltips and guidance throughout the interface
- **Feature Discovery**: Progressive hints based on your usage patterns
- **Accessibility Guide**: Comprehensive keyboard navigation and screen reader support

## 🎯 Risk Assessment System

### Risk Levels

- **🟢 Low (0-30)**: Safe operations with minimal impact
- **🟡 Medium (31-70)**: Changes requiring attention and review
- **🟠 High (71-90)**: Potentially dangerous changes, proceed with caution
- **🔴 Critical (91-100)**: High risk of service disruption, requires careful planning

### Enhanced Risk Factors

#### Resource Type Criticality
- **Security Resources**: IAM roles, security groups, policies (high base risk)
- **Networking Infrastructure**: VPCs, subnets, route tables (medium-high risk)
- **Data Storage**: Databases, storage buckets, persistent volumes (high risk)
- **Compute Resources**: Instances, containers, serverless functions (medium risk)
- **Monitoring & Logging**: CloudWatch, logging services (low-medium risk)

#### Action Risk Multipliers
- **Create**: 1.0x (lowest risk - new resources)
- **Update**: 1.5x (medium risk - configuration changes)
- **Replace**: 2.0x (high risk - resource recreation)
- **Delete**: 2.5x (highest risk - potential data loss)

#### Multi-Cloud Risk Analysis
- **Cross-Provider Dependencies**: Additional risk for resources spanning multiple clouds
- **Provider-Specific Risks**: Tailored risk assessment for AWS, Azure, GCP patterns
- **Compliance Considerations**: Industry-specific compliance framework checks

### Security Analysis
- **Security Resource Highlighting**: Automatic identification of security-related changes
- **Compliance Framework Checks**: Built-in checks for common compliance requirements
- **Access Control Analysis**: Review of permission and access control changes

## 📊 Sample Data

If you want to test the dashboard without a real Terraform plan:

1. Click "🔧 Generate Sample Plan Data" button
2. Download the sample JSON file
3. Upload it to see the dashboard in action

## 🔧 Troubleshooting

### Common Issues

**Streamlit command not found:**
```bash
# Try running with Python module
python -m streamlit run app.py
```

**Import errors:**
```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Large file upload issues:**
```bash
# Increase Streamlit file upload limit
streamlit run app.py --server.maxUploadSize=200
```

**PDF generation not working:**
```bash
# Test enhanced PDF generator
python -c "from components.enhanced_pdf_generator import EnhancedPDFGenerator; print('Enhanced PDF generator working!')"

# Test reportlab installation
python -c "import reportlab; print('Reportlab working!')"

# Reinstall if needed
pip install reportlab

# Verify PDF generation works
python -c "from components.report_generator import ReportGeneratorComponent; print('Report generator ready!')"
```

**Enhanced features not available:**
- Check that all files in `providers/` and `utils/` directories are present
- Verify enhanced dependencies are installed
- Restart the application after installing missing components

**Performance issues with large plans:**
- Enable debug mode to see processing details
- Consider using filters to focus analysis
- Large plans (>50MB) may take 30-60 seconds to process

### Getting Help

1. **In-App Help**: Use the guided tour and contextual help system
2. **Accessibility**: Full keyboard navigation and screen reader support available
3. **Feature Discovery**: Enable discovery mode for interactive feature hints
4. **Debug Mode**: Enable in sidebar for detailed processing information

## 🚀 Advanced Capabilities

### Multi-Cloud Support
- **Provider Detection**: Automatic identification of AWS, Azure, GCP, and other providers
- **Cross-Cloud Analysis**: Unified risk assessment across multiple cloud platforms
- **Provider-Specific Insights**: Tailored recommendations for each cloud provider
- **Resource Distribution**: Visual breakdown of resources across different clouds

### Enterprise Features
- **Workflow-Specific Tours**: Guided tutorials for security reviews, production deployments
- **Enhanced Professional Reporting**: Template-based PDF/HTML generation with executive summaries, technical analysis, and security assessments
- **Advanced PDF Engine**: Pure Python PDF generation with no system dependencies, multiple templates, and professional styling
- **Accessibility Compliance**: Full WCAG 2.1 AA compliance with keyboard navigation
- **Performance Optimization**: Efficient handling of large Terraform plans (200MB+)

### User Experience Enhancements
- **Interactive Onboarding**: Progressive checklist and contextual hints
- **Feature Discovery**: Smart suggestions based on usage patterns
- **Customizable Interface**: Smart defaults for different use cases
- **Comprehensive Help**: In-app documentation, tooltips, and guided tours

## 📝 File Structure Details

### `app.py`

Main Streamlit application with:

- File upload interface
- Dashboard layout and components
- Integration with all modules

### `parsers/plan_parser.py`

JSON parsing functionality:

- Extract resource changes
- Calculate summary statistics
- Validate plan structure

### `visualizers/charts.py`

Plotly chart generation:

- Pie charts for resource distribution
- Bar charts for action breakdown
- Heatmaps for risk visualization

### `utils/risk_assessment.py`

Risk analysis engine:

- Resource type risk scoring
- Action risk multipliers
- Overall plan risk calculation

### `assets/styles.css`

Custom styling:

- Professional color scheme
- Responsive design
- Interactive hover effects

## 🤝 Contributing

To extend the dashboard:

1. **Add new chart types** in `visualizers/charts.py`
2. **Enhance risk logic** in `utils/risk_assessment.py`
3. **Add new parsers** for different Terraform versions
4. **Improve styling** in `assets/styles.css`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues or questions:

1. Check the troubleshooting section above
2. Verify all files are in correct locations
3. Ensure virtual environment is properly activated
4. Test with sample data first

## 🤖 Development Credits

This project was significantly enhanced and expanded with the assistance of **Kiro AI** - an intelligent development assistant that helped implement advanced features including:

- 🎯 Comprehensive help system with guided tours and contextual assistance
- ♿ Full accessibility compliance (WCAG 2.1 AA) with keyboard navigation and screen reader support
- 🔍 Interactive feature discovery system with progressive user guidance
- 📄 Professional report generation with PDF and HTML export capabilities
- ☁️ Multi-cloud analysis support for AWS, Azure, GCP, and other providers
- 🔒 Enhanced security analysis with compliance framework checks
- 🎓 Interactive onboarding system with workflow-specific tutorials
- 📊 Advanced visualizations and risk assessment algorithms

### 🤝 Acknowledgments

- **🤖 Kiro AI**: Advanced development assistance and feature implementation
- **🧠 Claude by Anthropic**: Initial development support and architectural guidance
- **🚀 Streamlit Community**: Excellent framework for rapid dashboard development
- **📊 Plotly**: Powerful visualization library for interactive charts
- **📄 ReportLab**: Professional PDF generation with pure Python

### 💡 Inspiration

Created to address the growing need for comprehensive Terraform plan analysis in enterprise environments, with a focus on:
- Risk-aware infrastructure deployment
- Multi-cloud infrastructure management
- Accessible and inclusive user interfaces
- Professional reporting and documentation
- Enhanced developer experience and productivity

---

**Built with ❤️ for the DevOps and Infrastructure community**
