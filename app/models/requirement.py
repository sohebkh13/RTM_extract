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
    
    class Config:
        use_enum_values = True

class RequirementsCollection(BaseModel):
    requirements: List[Requirement]
    metadata: dict
    total_count: int
    summary_stats: dict
