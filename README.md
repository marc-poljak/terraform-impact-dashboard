# 🚀 Terraform Plan Change Impact Dashboard

A professional web dashboard for visualizing Terraform plan changes, analyzing risk levels, and making data-driven deployment decisions.

## 📋 Features

- **📊 Change Summary**: Visual overview of create/update/delete operations
- **⚠️ Risk Assessment**: Intelligent risk scoring based on resource types and actions
- **📈 Interactive Charts**: Resource type distributions, change flows, and risk heatmaps
- **🔍 Advanced Filtering**: Filter by action type, resource type, and risk level
- **📥 Data Export**: Download filtered results as CSV
- **📱 Responsive Design**: Works on desktop and mobile devices

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)

### Step 3: Install Dependencies
```powershell
# With virtual environment activated
pip install -r requirements.txt
```

### Step 4: Create the Files
Save each of the provided code files in their respective locations:

```
terraform-dashboard/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── parsers/
│   └── plan_parser.py       # JSON parsing logic
├── visualizers/
│   └── charts.py           # Plotly chart generators
├── utils/
│   └── risk_assessment.py  # Risk scoring algorithms
└── assets/
    └── styles.css          # Custom CSS styling
```

### Step 5: Run the Dashboard
```powershell
# Make sure your virtual environment is activated
.\venv\Scripts\activate

# Run the Streamlit app
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## 📁 Usage

### 1. Upload Terraform Plan JSON
- Click "Browse files" or drag & drop your plan JSON file
- Supported format: `plan-{id}-structured-output.json`
- File size: Up to 10MB supported

### 2. View Change Summary
- **Create**: New resources being added
- **Update**: Existing resources being modified  
- **Delete**: Resources being removed
- **Risk Level**: Overall deployment risk assessment

### 3. Analyze Visualizations
- **Resource Types Pie Chart**: Distribution of resource types
- **Change Actions Bar Chart**: Breakdown by operation type
- **Risk Heatmap**: Risk levels by resource type

### 4. Filter and Export
- Use sidebar filters to focus on specific changes
- Export filtered data as CSV for further analysis

## 🎯 Risk Assessment Logic

### Risk Levels
- **🟢 Low (0-3)**: Safe operations, minimal impact
- **🟡 Medium (4-6)**: Moderate risk, requires attention
- **🔴 High (7-10)**: High impact, proceed with caution

### High-Risk Resource Types
- **Security**: `aws_security_group`, `aws_iam_*`
- **Networking**: `aws_vpc`, `aws_subnet`, `aws_route_table`
- **Databases**: `aws_rds_*`, `aws_dynamodb_table`
- **Storage**: `aws_s3_bucket` (with policies)

### Action Risk Multipliers
- **Create**: 1.0x (lowest risk)
- **Update**: 1.5x (medium risk)
- **Delete**: 2.5x (highest risk)

## 📊 Sample Data

If you want to test the dashboard without a real Terraform plan:

1. Click "🔧 Generate Sample Plan Data" button
2. Download the sample JSON file
3. Upload it to see the dashboard in action

## 🔧 Troubleshooting

### Common Issues

**Streamlit command not found:**
```powershell
# Try running with Python module
python -m streamlit run app.py
```

**Import errors:**
```powershell
# Make sure virtual environment is activated
.\venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Large file upload issues:**
```powershell
# Increase Streamlit file upload limit
streamlit run app.py --server.maxUploadSize=50
```

**Port already in use:**
```powershell
# Use different port
streamlit run app.py --server.port=8502
```

## 🚀 Next Steps (Phase 2)

Future enhancements planned:
- **🕸️ Dependency Graph**: Interactive network of resource relationships
- **📈 Sankey Diagrams**: Resource state flow visualization
- **📊 Multi-plan Comparison**: Compare different plan versions
- **🔔 Alert System**: Automated risk notifications
- **💾 Configuration Save/Load**: Persistent dashboard settings

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

This project is provided as-is for internal use. Modify and distribute as needed for your organization.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all files are in correct locations
3. Ensure virtual environment is properly activated
4. Test with sample data first

