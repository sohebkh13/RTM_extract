# RTM AI Agent 🚀

**Automated Requirements Traceability Matrix Generator with AI Analysis**

Transform your Excel requirements documents into professional Requirements Traceability Matrices (RTM) using AI-powered analysis.

## 🌟 Features

- **AI-Powered Analysis**: Uses Gemini 1.5 Flash and Groq for intelligent requirement classification
- **Excel Processing**: Reads multiple sheet formats and complex layouts
- **Professional RTM Output**: Generates formatted Excel files with data validation
- **Focus Sheet Priority**: Special attention to "2- tool Requirements" sheet
- **Web Interface**: Both API and Streamlit UI available
- **Source Traceability**: Maintains exact links to original requirement locations
- **Rule-based Fallback**: Works without AI APIs for basic analysis

## 🏗️ Architecture

```
Excel Upload → Excel Parser → AI Analysis → RTM Generator → Professional Excel Output
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **AI/LLM**: Google Gemini, Groq
- **Excel Processing**: OpenPyXL, Pandas, XlsxWriter
- **Data Validation**: Pydantic
- **Web UI**: Streamlit
- **Testing**: Pytest

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd rtm_extract

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file (copy from `env_example.txt`):

```bash
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Application Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
LOG_LEVEL=INFO

# File Storage
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs

# Processing Settings
GEMINI_MODEL=gemini-1.5-flash
GROQ_MODEL=llama3-8b-8192
AI_MAX_TOKENS=8000
AI_TEMPERATURE=0.1
FOCUS_SHEET_NAME=2- tool Requirements
```

### 3. Get Free API Keys

**Gemini (Recommended)**:
1. Visit [Google AI Studio](https://makersuite.google.com/)
2. Sign in and create a new project
3. Generate API key (Free: 500 requests/day)

**Groq (Alternative)**:
1. Visit [Groq Console](https://console.groq.com/)
2. Sign up and get API key
3. Free tier available

### 4. Run the Application

**Option A: API Server**
```bash
python main.py
```

**Option B: Streamlit Web UI**
```bash
# Terminal 1: Start API server
python main.py

# Terminal 2: Start Streamlit UI
streamlit run streamlit_app.py
```

### 5. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501
- **API Endpoints**: http://localhost:8000/api/v1/

## 📋 Usage

### Web Interface (Recommended)

1. Open Streamlit UI at http://localhost:8501
2. Upload your Excel file (.xlsx or .xls)
3. Configure focus sheet name (default: "2- tool Requirements")
4. Click "Upload and Analyze"
5. Download the generated RTM Excel file

### API Usage

**1. Upload Excel File**
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@your_requirements.xlsx"
```

**2. Analyze Requirements**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "your-file-id",
    "focus_sheet": "2- tool Requirements",
    "include_all_sheets": true
  }'
```

**3. Download RTM**
```bash
curl -X GET "http://localhost:8000/api/v1/download/{file_id}" \
  --output rtm_output.xlsx
```

## 📊 RTM Output Format

The generated Excel file contains:

### Sheet 1: Requirements Traceability Matrix
| Column | Description | Format |
|--------|-------------|---------|
| Requirement ID | Unique identifier | REQ-001, REQ-002, etc. |
| Requirement Description | Exact text from source | Original requirement text |
| Source | Location reference | SheetName!CellReference |
| Requirement Type | AI classification | Functional/Non-functional/Business/Technical/User |
| Priority | Business priority | High/Medium/Low |
| Status | Current status | Not Tested/In Progress/Approved/Rejected |
| Related Deliverables | Project components | AI-identified deliverables |
| Test Case ID | Test mapping | TC-001, TC-002, etc. |
| Comments | Additional notes | AI insights and dependencies |

### Sheet 2: Summary Statistics
- Total requirements by type
- Priority distribution
- Source sheet breakdown
- Processing metadata

## 🎯 Key Features

### AI Analysis Capabilities

- **Requirement Classification**: Automatically categorizes requirements
- **Priority Assessment**: Determines business priority based on content
- **Deliverable Mapping**: Identifies related project components
- **Test Case Suggestions**: Generates test scenario ideas
- **Dependency Analysis**: Identifies relationships between requirements

### Excel Processing

- **Multi-sheet Support**: Processes all sheets in workbook
- **Focus Sheet Priority**: Special attention to "2- tool Requirements"
- **Format Preservation**: Maintains source references and traceability
- **Complex Layout Handling**: Supports merged cells and varied structures

### Professional Output

- **Data Validation**: Dropdown lists for consistent data entry
- **Professional Formatting**: Headers, colors, and styling
- **Column Optimization**: Appropriate widths and text wrapping
- **Summary Analytics**: Statistics and distribution charts

## 🔧 Configuration

### Focus Sheet Configuration

The system prioritizes the sheet named "2- tool Requirements" by default. Configure this in your `.env` file:

```bash
FOCUS_SHEET_NAME=2- tool Requirements
```

### File Size Limits

Maximum file size is set to 10MB by default:

```bash
MAX_FILE_SIZE=10485760  # 10MB in bytes
```

### AI Model Selection

Choose your preferred AI models:

```bash
GEMINI_MODEL=gemini-1.5-flash    # Fast, cost-effective
GROQ_MODEL=llama3-8b-8192       # Alternative option
```

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run specific test categories
pytest tests/test_excel_processor.py
pytest tests/test_ai_analyzer.py
```

## 📁 Project Structure

```
rtm_extract/
├── app/
│   ├── models/           # Pydantic data models
│   ├── services/         # Core business logic
│   ├── api/              # FastAPI routes and dependencies
│   ├── utils/            # Utilities and helpers
│   ├── config.py         # Configuration management
│   └── main.py           # FastAPI application
├── templates/            # Excel templates and styles
├── tests/                # Test files
├── uploads/              # Temporary upload storage
├── outputs/              # Generated RTM files
├── main.py               # Application entry point
├── streamlit_app.py      # Web interface
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🚨 Troubleshooting

### Common Issues

**1. API Keys Not Working**
- Verify your API keys in the `.env` file
- Check quota limits on your AI provider accounts
- The system will fallback to rule-based analysis if AI fails

**2. Excel Processing Errors**
- Ensure file is a valid Excel format (.xlsx, .xls)
- Check file size limits (10MB default)
- Verify file is not corrupted

**3. Requirements Not Found**
- Check that your Excel contains text-based requirements
- Verify sheet names (especially focus sheet)
- Requirements should be substantive text (>10 characters)

**4. Connection Errors**
- Ensure API server is running (`python main.py`)
- Check port 8000 is not in use by another application
- Verify firewall settings

### Logs and Debugging

Logs are stored in the `logs/` directory:

```bash
# View recent logs
tail -f logs/rtm_agent.log

# Check for errors
grep ERROR logs/rtm_agent.log
```

Enable debug mode in `.env`:

```bash
DEBUG=True
LOG_LEVEL=DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini for AI analysis capabilities
- Groq for fast inference
- OpenPyXL for Excel processing
- FastAPI for the robust API framework
- Streamlit for the user-friendly interface

---

**Happy Requirements Tracing! 📊✨**
