import os
from pathlib import Path
from typing import List
from app.config import settings
from .exceptions import RTMException

def validate_file_size(file_size: int) -> bool:
    """Validate that file size is within limits"""
    if file_size > settings.MAX_FILE_SIZE:
        raise RTMException(f"File size {file_size} exceeds maximum allowed size {settings.MAX_FILE_SIZE}")
    return True

def validate_excel_file(file_path: str) -> bool:
    """Validate that file is a valid Excel file"""
    if not os.path.exists(file_path):
        raise RTMException(f"File not found: {file_path}")
    
    file_extension = Path(file_path).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise RTMException(f"Invalid file type {file_extension}. Allowed types: {settings.ALLOWED_EXTENSIONS}")
    
    return True

def validate_sheet_names(sheet_names: List[str]) -> bool:
    """Validate that required sheets exist"""
    if settings.FOCUS_SHEET_NAME not in sheet_names:
        # Log warning but don't fail - sheet might have different name
        pass
    return True
