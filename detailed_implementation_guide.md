# Complete Implementation Guide: AI Agent for Requirements Analysis

## 📋 Project Overview

**Project Name**: Requirements Traceability Matrix (RTM) AI Agent  
**Purpose**: Automated analysis of Excel-based project documentation to generate professional Requirements Traceability Matrices  
**Primary Focus**: Process "2- tool Requirements" sheet with detailed mapping to test cases

---

## 🏗️ System Architecture

### High-Level Architecture
```
Input Excel File → Excel Parser → Gemini AI Analysis Engine → RTM Generator → Output Excel File
```

### Detailed Component Flow
```
1. File Upload Interface
2. Multi-Sheet Excel Reader
3. Requirements Extractor
4. Gemini AI-Powered Classifier & Analyzer
5. RTM Data Model Builder
6. Professional Excel Generator
7. Output Delivery System
```

---

## 🛠️ Technical Stack Specification

### Core Technologies
```python
# Backend Framework
fastapi==0.104.1          # Modern Python web framework
uvicorn==0.24.0           # ASGI server

# Excel Processing
openpyxl==3.1.2           # Excel file manipulation
pandas==2.1.4            # Data analysis and manipulation
xlsxwriter==3.1.9        # Advanced Excel formatting

# AI/LLM Integration
google-generativeai==0.3.0  # Gemini API client

# Data Validation & Models
pydantic==2.5.2          # Data validation using Python type annotations
typing-extensions==4.8.0  # Extended typing support

# Web Interface (Optional)
streamlit==1.28.1         # Quick web UI
streamlit-file-uploader==0.0.3

# Utilities
python-dotenv==1.0.0      # Environment variable management
loguru==0.7.2            # Advanced logging
python-multipart==0.0.6   # File upload handling
```

### Development Tools
```python
# Development & Testing
pytest==7.4.3           # Testing framework
black==23.11.0           # Code formatting
flake8==6.1.0           # Code linting
mypy==1.7.1             # Type checking
```

---

## 📁 Project Structure

```
rtm_ai_agent/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .env                       # Environment variables (not in git)
├── .gitignore                 # Git ignore rules
├── README.md                  # Project documentation
│
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── main.py                # FastAPI application
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requirement.py     # Pydantic models for requirements
│   │   ├── rtm.py            # RTM data structures
│   │   └── responses.py       # API response models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── excel_processor.py # Excel reading/writing logic
│   │   ├── gemini_analyzer.py # Gemini AI integration
│   │   ├── rtm_generator.py   # RTM creation logic
│   │   └── file_handler.py    # File operations
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # API endpoints
│   │   └── dependencies.py    # Dependency injection
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # Logging configuration
│       ├── validators.py      # Data validation utilities
│       └── exceptions.py      # Custom exceptions
│
├── templates/
│   ├── rtm_template.xlsx      # Excel template for output
│   └── styles/
│       └── excel_styles.py    # Excel formatting definitions
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Test configuration
│   ├── test_excel_processor.py
│   ├── test_gemini_analyzer.py
│   ├── test_rtm_generator.py
│   └── sample_files/
│       ├── test_requirements.xlsx
│       └── expected_output.xlsx
│
└── docs/
    ├── api_documentation.md
    ├── user_guide.md
    └── deployment_guide.md
```

---

## 📊 Data Models Specification

### 1. Requirement Model
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime

class RequirementType(str, Enum):
    FUNCTIONAL = "Functional"
    NON_FUNCTIONAL = "Non-functional" 
    BUSINESS = "Business"
    TECHNICAL = "Technical"
    USER = "User"

class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class Status(str, Enum):
    NOT_TESTED = "Not Tested"
    IN_PROGRESS = "In Progress"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class Requirement(BaseModel):
    id: str = Field(..., description="Unique requirement identifier (REQ-001)")
    description: str = Field(..., description="Exact requirement description from source")
    source: str = Field(..., description="Sheet name and cell reference")
    requirement_type: RequirementType = Field(..., description="Category of requirement")
    priority: Priority = Field(..., description="Business priority level")
    status: Status = Field(default=Status.NOT_TESTED, description="Current status")
    related_deliverables: Optional[str] = Field(None, description="Linked project deliverables")
    test_case_id: str = Field(..., description="Unique test case identifier (TC-001)")
    comments: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.now)
    
class RequirementsCollection(BaseModel):
    requirements: List[Requirement]
    metadata: dict
    total_count: int
    summary_stats: dict
```

### 2. RTM Output Model
```python
class RTMOutput(BaseModel):
    file_path: str
    requirements_count: int
    summary_statistics: dict
    processing_time: float
    source_file_name: str
    generated_at: datetime
```

### 3. API Models
```python
class FileUploadResponse(BaseModel):
    message: str
    file_id: str
    file_name: str
    file_size: int
    
class AnalysisRequest(BaseModel):
    file_id: str
    focus_sheet: str = "2- tool Requirements"
    include_all_sheets: bool = True
    
class AnalysisResponse(BaseModel):
    status: str
    rtm_file_path: str
    analysis_summary: dict
    requirements_found: int
    processing_details: dict
```

---

## 🔧 Core Components Implementation Specs

### 1. Excel Processor Service

**File**: `app/services/excel_processor.py`

**Required Functions**:
```python
class ExcelProcessor:
    def __init__(self):
        pass
    
    async def read_excel_file(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Read all sheets from Excel file
        Returns: Dictionary with sheet names as keys, DataFrames as values
        """
        pass
    
    def extract_requirements_from_sheet(self, df: pd.DataFrame, sheet_name: str) -> List[Dict]:
        """
        Extract requirements from a specific sheet
        Focus on "2- tool Requirements" sheet
        Returns: List of requirement dictionaries
        """
        pass
    
    def identify_requirement_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Auto-detect columns containing requirements
        Returns: Mapping of expected fields to actual column names
        """
        pass
    
    def generate_rtm_excel(self, requirements: List[Requirement], output_path: str) -> str:
        """
        Create formatted Excel RTM file
        Include data validation, formatting, and professional styling
        """
        pass
```

**Key Implementation Details**:
- Handle various Excel formats (.xlsx, .xls)
- Preserve original formatting and structure references
- Extract exact text without modification
- Support merged cells and complex layouts
- Create professional output with dropdown validations

### 2. Gemini AI Analyzer Service

**File**: `app/services/gemini_analyzer.py`

**Required Functions**:
```python
import google.generativeai as genai
import json
from typing import List, Dict

class GeminiAnalyzer:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    async def analyze_requirements(self, requirements_text: str, context: dict) -> List[Dict]:
        """
        Use Gemini AI to classify and analyze requirements
        Returns: Enhanced requirement data with classifications
        """
        pass
    
    def classify_requirement_type(self, requirement: str) -> RequirementType:
        """
        Classify requirement into functional/non-functional/business/etc.
        """
        pass
    
    def determine_priority(self, requirement: str, context: str) -> Priority:
        """
        Analyze requirement to determine business priority
        """
        pass
    
    def generate_test_case_suggestions(self, requirement: str) -> List[str]:
        """
        Generate test case ideas for the requirement
        """
        pass
    
    def extract_deliverables(self, requirement: str, project_context: str) -> str:
        """
        Identify related deliverables for the requirement
        """
        pass
    
    def batch_analyze_requirements(self, requirements_list: List[str], context: dict) -> List[Dict]:
        """
        Process multiple requirements in a single API call for efficiency
        Takes advantage of Gemini's large context window
        """
        pass
```

**Gemini Prompt Templates**:
```python
REQUIREMENT_ANALYSIS_PROMPT = """
You are an expert business analyst and project manager. Analyze the following requirements and provide structured analysis for each.

For each requirement, determine:
1. Requirement Type: Classify as Functional, Non-functional, Business, Technical, or User
2. Priority: Determine if High, Medium, or Low based on business impact and complexity
3. Related Deliverables: Identify project components this requirement affects
4. Test Case Suggestions: Provide 2-3 specific test scenario ideas

PROJECT CONTEXT:
- Source File: {file_name}
- Focus Sheet: {sheet_name}
- Total Requirements: {total_count}

REQUIREMENTS TO ANALYZE:
{requirements_text}

INSTRUCTIONS:
- Maintain exact requirement descriptions - do not modify the text
- Be specific with deliverables and test cases
- Consider dependencies between requirements
- Focus extra attention on requirements from "2- tool Requirements" sheet

Respond with a JSON array where each object contains:
{{
    "original_requirement": "exact text from source",
    "requirement_type": "Functional|Non-functional|Business|Technical|User",
    "priority": "High|Medium|Low",
    "priority_reasoning": "brief explanation",
    "related_deliverables": "specific project components",
    "test_case_suggestions": ["test case 1", "test case 2", "test case 3"],
    "comments": "additional insights or dependencies",
    "analysis_confidence": 0.95
}}
"""

BATCH_ANALYSIS_PROMPT = """
You are processing requirements for a Requirements Traceability Matrix (RTM). 

CRITICAL INSTRUCTIONS:
1. NEVER modify requirement descriptions - use exact text from source
2. Focus special attention on "2- tool Requirements" sheet items
3. Generate unique, sequential test case suggestions
4. Identify relationships between requirements
5. Consider business impact for priority assignment

EXCEL FILE CONTEXT:
- File: {file_name}
- Sheets Processed: {sheet_names}
- Primary Focus: "2- tool Requirements"
- Total Requirements Found: {total_count}

REQUIREMENTS DATA:
{formatted_requirements}

Generate comprehensive analysis maintaining source traceability and exact requirement text.
"""
```

### 3. RTM Generator Service

**File**: `app/services/rtm_generator.py`

**Required Functions**:
```python
class RTMGenerator:
    def __init__(self):
        self.excel_processor = ExcelProcessor()
    
    async def create_rtm(self, requirements: List[Requirement], source_file_info: dict) -> RTMOutput:
        """
        Generate complete RTM Excel file
        """
        pass
    
    def generate_requirement_ids(self, requirements: List[Dict]) -> List[Dict]:
        """
        Assign unique REQ-001, REQ-002, etc. identifiers
        """
        pass
    
    def generate_test_case_ids(self, requirements: List[Dict]) -> List[Dict]:
        """
        Assign unique TC-001, TC-002, etc. identifiers
        """
        pass
    
    def create_summary_statistics(self, requirements: List[Requirement]) -> Dict:
        """
        Generate summary stats for the RTM
        """
        pass
    
    def apply_excel_formatting(self, workbook, worksheet) -> None:
        """
        Apply professional formatting to RTM Excel file
        """
        pass
```

### 4. File Handler Service

**File**: `app/services/file_handler.py`

**Required Functions**:
```python
class FileHandler:
    def __init__(self, upload_dir: str = "uploads", output_dir: str = "outputs"):
        self.upload_dir = Path(upload_dir)
        self.output_dir = Path(output_dir)
    
    async def save_uploaded_file(self, file: UploadFile) -> str:
        """
        Save uploaded Excel file and return file path
        """
        pass
    
    def validate_excel_file(self, file_path: str) -> bool:
        """
        Validate that uploaded file is a valid Excel file
        """
        pass
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> None:
        """
        Clean up old uploaded and generated files
        """
        pass
    
    def get_file_info(self, file_path: str) -> Dict:
        """
        Extract file metadata (size, sheets, etc.)
        """
        pass
```

---

## 🌐 API Endpoints Specification

**File**: `app/api/routes.py`

### Endpoint Definitions
```python
@router.post("/upload", response_model=FileUploadResponse)
async def upload_excel_file(file: UploadFile = File(...)):
    """
    Upload Excel file for processing
    - Validates file type and size
    - Returns file ID for subsequent operations
    """
    pass

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_requirements(request: AnalysisRequest):
    """
    Process uploaded Excel file and generate RTM
    - Reads all sheets with focus on "2- tool Requirements"
    - Uses Gemini AI to classify and analyze requirements
    - Generates formatted RTM Excel output
    """
    pass

@router.get("/download/{file_id}")
async def download_rtm(file_id: str):
    """
    Download generated RTM Excel file
    """
    pass

@router.get("/status/{file_id}")
async def get_processing_status(file_id: str):
    """
    Check processing status for long-running operations
    """
    pass

@router.get("/health")
async def health_check():
    """
    API health check endpoint
    """
    pass
```

---

## 📋 Excel Output Specifications

### RTM Excel File Structure

**Sheet 1: Requirements Traceability Matrix**
| Column | Width | Data Type | Validation | Format |
|--------|--------|-----------|------------|---------|
| Requirement ID | 15 | Text | REQ-XXX pattern | Bold header |
| Requirement Description | 50 | Text | Required | Wrap text |
| Source | 20 | Text | Sheet!Cell format | Centered |
| Requirement Type | 15 | Dropdown | 5 options | Centered |
| Priority | 12 | Dropdown | High/Med/Low | Color coded |
| Status | 15 | Dropdown | 4 status options | Color coded |
| Related Deliverables | 25 | Text | Optional | Wrap text |
| Test Case ID | 15 | Text | TC-XXX pattern | Bold |
| Comments | 30 | Text | Optional | Wrap text |

**Sheet 2: Summary Statistics**
- Total requirements by type
- Priority distribution  
- Source sheet breakdown
- Processing metadata

**Sheet 3: Raw Data (Optional)**
- Original extracted data for reference

### Excel Formatting Requirements
```python
# Header formatting
header_font = Font(name='Calibri', size=12, bold=True, color='FFFFFF')
header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')

# Data validation dropdowns
requirement_type_validation = DataValidation(
    type="list",
    formula1='"Functional,Non-functional,Business,Technical,User"'
)

# Conditional formatting for priorities
priority_colors = {
    'High': 'FF6B6B',    # Red
    'Medium': 'FFE66D',  # Yellow  
    'Low': '4ECDC4'      # Green
}
```

---

## ⚙️ Configuration Management

**File**: `app/config.py`

```python
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # AI Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"
    AI_MAX_TOKENS: int = 8000
    AI_TEMPERATURE: float = 0.1
    
    # File Configuration  
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = ['.xlsx', '.xls']
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    
    # Processing Configuration
    FOCUS_SHEET_NAME: str = "2- tool Requirements"
    REQUIREMENT_ID_PREFIX: str = "REQ"
    TEST_CASE_ID_PREFIX: str = "TC"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## 🧪 Testing Strategy

### Test Files Required
```
tests/sample_files/
├── valid_requirements.xlsx          # Standard test case
├── complex_requirements.xlsx        # Multiple sheets, merged cells
├── tool_requirements_focused.xlsx   # Heavy "2- tool Requirements" data  
├── invalid_file.txt                # Invalid file type test
└── corrupted_file.xlsx             # Corrupted Excel file test
```

### Test Cases to Implement
```python
# test_excel_processor.py
def test_read_valid_excel_file()
def test_extract_requirements_from_tool_sheet()
def test_handle_merged_cells()
def test_identify_requirement_columns()
def test_generate_rtm_excel_output()

# test_gemini_analyzer.py  
def test_classify_functional_requirement()
def test_classify_non_functional_requirement()
def test_determine_high_priority()
def test_generate_test_case_suggestions()
def test_batch_analysis_performance()

# test_rtm_generator.py
def test_create_complete_rtm()
def test_generate_unique_ids()
def test_summary_statistics()
def test_excel_formatting()

# test_api_routes.py
def test_upload_valid_file()
def test_upload_invalid_file()
def test_analyze_requirements_endpoint()
def test_download_rtm_file()
```

---

## 🚀 Local Development Setup

### Environment Variables (.env)
```bash
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Application Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
LOG_LEVEL=INFO

# File Storage
MAX_FILE_SIZE=52428800  # 50MB in bytes
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs

# Processing Settings
GEMINI_MODEL=gemini-1.5-flash
AI_MAX_TOKENS=8000
AI_TEMPERATURE=0.1
```

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir uploads outputs logs

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: Run with Streamlit UI
streamlit run streamlit_app.py
```

---

## 📖 Usage Instructions for AI Implementation

### Phase 1: Core Implementation
1. **Set up project structure** as specified above
2. **Implement data models** in `app/models/`
3. **Create ExcelProcessor** with all specified functions
4. **Build GeminiAnalyzer** with Google Gemini API integration
5. **Develop RTMGenerator** for Excel output creation

### Phase 2: API Development  
1. **Implement FastAPI routes** as specified
2. **Add file upload handling** with validation
3. **Create processing workflows** linking all services
4. **Add error handling and logging** throughout

### Phase 3: Testing & Polish
1. **Write comprehensive tests** for all components
2. **Add Excel formatting** and professional styling
3. **Implement file cleanup** and management
4. **Add processing status tracking**

### Phase 4: Streamlit UI (Optional)
1. **Create simple web interface** for file uploads
2. **Add progress bars** and status indicators
3. **Enable direct file download** of generated RTMs
4. **Test end-to-end workflows**

---

## 🎯 Key Implementation Notes

### Critical Requirements
1. **Exact Text Preservation**: Never modify requirement descriptions from source
2. **Focus Sheet Priority**: "2- tool Requirements" gets detailed analysis
3. **Professional Output**: RTM must be presentation-ready
4. **Source Traceability**: Every requirement links back to source location
5. **Unique Identifiers**: Sequential REQ-XXX and TC-XXX numbering

### Performance Targets
- Process 500 requirements in under 2 minutes
- Support Excel files up to 50MB
- Generate RTM with professional formatting
- Leverage Gemini's 1M token context for large files

### Cost Optimization
- Use Gemini's free tier for development (500 requests/day)
- Batch process requirements to minimize API calls
- Cache common analysis patterns
- Implement efficient error handling and retries

### Error Handling
- Invalid Excel files should return clear error messages
- API failures should not crash the application  
- Large files should show progress indicators
- Failed Gemini API calls should have retry logic with exponential backoff

## 🆓 Getting Started with Free Gemini API

### Step 1: Get Free API Key
1. Go to [Google AI Studio](https://makersuite.google.com/)
2. Sign in with Google account
3. Create new project and get API key
4. Free tier: 500 requests/day, perfect for development

### Step 2: Test Integration
```python
import google.generativeai as genai

genai.configure(api_key="your_api_key_here")
model = genai.GenerativeModel("gemini-1.5-flash")

# Test with simple requirement
response = model.generate_content("Classify this requirement: User should be able to login with email")
print(response.text)
```

This updated specification focuses on Gemini AI integration and removes Docker complexity, making it perfect for rapid development and testing with the free Gemini API tier.