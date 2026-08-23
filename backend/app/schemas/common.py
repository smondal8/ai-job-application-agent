from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class PaginationMeta(BaseModel):
    """Metadata for paginated collection responses."""
    page: int = Field(1, ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items available")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class ResponseEnvelope(BaseModel, Generic[DataT]):
    """Standardized top-level API success response envelope."""
    success: bool = True
    data: DataT
    meta: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MessageResponse(BaseModel):
    """Simple status/confirmation message response."""
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
