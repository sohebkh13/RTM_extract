import pytest
import tempfile
from pathlib import Path
import pandas as pd
from openpyxl import Workbook

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_excel_file(temp_dir):
    """Create a sample Excel file for testing"""
    file_path = temp_dir / "test_requirements.xlsx"
    
    wb = Workbook()
    
    # Create main requirements sheet
    ws1 = wb.active
    ws1.title = "2- tool Requirements"
    ws1['A1'] = "Requirement ID"
    ws1['B1'] = "Description"
    ws1['A2'] = "REQ-001"
    ws1['B2'] = "The system shall provide user authentication functionality"
    ws1['A3'] = "REQ-002"
    ws1['B3'] = "The application must support password reset via email"
    
    # Create another sheet
    ws2 = wb.create_sheet("Business Requirements")
    ws2['A1'] = "Business Need"
    ws2['A2'] = "Users need to access the system securely"
    ws2['A3'] = "System should be available 24/7"
    
    wb.save(file_path)
    return str(file_path)

@pytest.fixture
def sample_requirements_list():
    """Sample requirements data for testing"""
    return [
        {
            'description': 'The system shall provide user authentication functionality',
            'source': '2- tool Requirements!B2',
            'sheet_name': '2- tool Requirements'
        },
        {
            'description': 'The application must support password reset via email',
            'source': '2- tool Requirements!B3', 
            'sheet_name': '2- tool Requirements'
        },
        {
            'description': 'Users need to access the system securely',
            'source': 'Business Requirements!A2',
            'sheet_name': 'Business Requirements'
        }
    ]
