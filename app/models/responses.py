from pydantic import BaseModel
from typing import Optional

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
