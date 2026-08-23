from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobIngestJsonRequest(BaseModel):
    json_payload: Optional[str] = Field(None, description="Raw JSON string containing jobs array")
    jobs: Optional[List[Dict[str, Any]]] = Field(None, description="Direct array of job dicts")
    source: str = Field("json_import", max_length=100, description="Source label (e.g. json_fixture, feed)")


class JobIngestCsvRequest(BaseModel):
    csv_text: str = Field(..., min_length=5, description="Raw CSV content string")
    source: str = Field("csv_import", max_length=100, description="Source label")


class JobIngestionBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    batch_id: str
    source: str
    filename: Optional[str] = None
    total_records: int
    inserted_count: int
    updated_count: int
    duplicate_count: int
    error_count: int
    status: str
    error_log: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class JobIngestionBatchListResponse(BaseModel):
    items: List[JobIngestionBatchResponse]
    total: int
