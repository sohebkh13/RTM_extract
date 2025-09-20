from pydantic import BaseModel
from datetime import datetime

class RTMOutput(BaseModel):
    file_path: str
    requirements_count: int
    summary_statistics: dict
    processing_time: float
    source_file_name: str
    generated_at: datetime
