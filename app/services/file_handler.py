import os
import uuid
import aiofiles
from pathlib import Path
from typing import Dict
from fastapi import UploadFile
import time

from app.config import settings
from app.utils.logger import get_logger
from app.utils.validators import validate_file_size, validate_excel_file
from app.utils.exceptions import FileHandlingError

logger = get_logger(__name__)

class FileHandler:
    def __init__(self, upload_dir: str = None, output_dir: str = None):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIR)
        self.output_dir = Path(output_dir or settings.OUTPUT_DIR)
        self.logger = logger
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> str:
        """
        Save uploaded Excel file and return file path
        """
        try:
            # Validate file size
            file_content = await file.read()
            validate_file_size(len(file_content))
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix.lower()
            safe_filename = f"{file_id}_{file.filename}"
            file_path = self.upload_dir / safe_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Validate it's a proper Excel file
            validate_excel_file(str(file_path))
            
            self.logger.info(f"File uploaded successfully: {file.filename} -> {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Error saving uploaded file: {str(e)}")
            raise FileHandlingError(f"Failed to save uploaded file: {str(e)}")
    
    def validate_excel_file(self, file_path: str) -> bool:
        """
        Validate that uploaded file is a valid Excel file
        """
        try:
            return validate_excel_file(file_path)
        except Exception as e:
            raise FileHandlingError(f"File validation failed: {str(e)}")
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> None:
        """
        Clean up old uploaded and generated files
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            # Clean upload directory
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        self.logger.debug(f"Deleted old upload file: {file_path}")
            
            # Clean output directory
            for file_path in self.output_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        self.logger.debug(f"Deleted old output file: {file_path}")
            
            self.logger.info(f"Cleanup completed for files older than {max_age_hours} hours")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    def get_file_info(self, file_path: str) -> Dict:
        """
        Extract file metadata (size, sheets, etc.)
        """
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                raise FileHandlingError(f"File not found: {file_path}")
            
            file_stats = file_path_obj.stat()
            
            info = {
                'file_name': file_path_obj.name,
                'file_size': file_stats.st_size,
                'created_at': file_stats.st_ctime,
                'modified_at': file_stats.st_mtime,
                'file_extension': file_path_obj.suffix.lower()
            }
            
            # Try to get Excel-specific info
            try:
                import pandas as pd
                excel_file = pd.ExcelFile(file_path)
                info['sheet_names'] = excel_file.sheet_names
                info['sheet_count'] = len(excel_file.sheet_names)
            except Exception:
                info['sheet_names'] = []
                info['sheet_count'] = 0
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting file info: {str(e)}")
            raise FileHandlingError(f"Failed to get file info: {str(e)}")
    
    def get_file_id_from_path(self, file_path: str) -> str:
        """Extract file ID from file path"""
        try:
            filename = Path(file_path).name
            # File ID is the first part before the first underscore
            file_id = filename.split('_')[0]
            return file_id
        except Exception:
            return str(uuid.uuid4())
    
    def find_file_by_id(self, file_id: str) -> str:
        """Find uploaded file by ID"""
        try:
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file() and file_path.name.startswith(file_id):
                    return str(file_path)
            
            raise FileHandlingError(f"File with ID {file_id} not found")
            
        except Exception as e:
            self.logger.error(f"Error finding file by ID: {str(e)}")
            raise FileHandlingError(f"Failed to find file: {str(e)}")
    
    def get_output_file_path(self, filename: str) -> str:
        """Get full path for output file"""
        return str(self.output_dir / filename)
