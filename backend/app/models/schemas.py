"""
Pydantic models for request/response schemas.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    kb_id: str = Field(..., description="Knowledge base ID")
    file_names: List[str] = Field(..., description="List of uploaded file names")
    message: str = Field(..., description="Success message")


class KnowledgeBase(BaseModel):
    """Knowledge base information."""
    kb_id: str = Field(..., description="Knowledge base ID")
    name: str = Field(..., description="Knowledge base name")
    created_at: datetime = Field(..., description="Creation timestamp")
    file_count: int = Field(0, description="Number of files in the knowledge base")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class KnowledgeBaseList(BaseModel):
    """List of knowledge bases."""
    knowledge_bases: List[KnowledgeBase] = Field(..., description="List of knowledge bases")


class ChatMessage(BaseModel):
    """Chat message model."""
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Model temperature")
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Validate temperature is within acceptable range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="AI response")
    sources: List[str] = Field(default_factory=list, description="Source documents")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field("healthy", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field("1.0.0", description="API version")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class KnowledgeBaseUpdate(BaseModel):
    """Model for updating knowledge base information."""
    name: str = Field(..., min_length=1, max_length=100, description="New knowledge base name")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate knowledge base name."""
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()

