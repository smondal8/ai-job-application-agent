from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Stripe"])
    domain: Optional[str] = Field(None, max_length=255, examples=["stripe.com"])
    industry: Optional[str] = Field(None, max_length=100, examples=["Fintech / Payments"])
    company_size: Optional[str] = Field(None, max_length=50, examples=["1000+"])
    careers_url: Optional[str] = Field(None, max_length=1024, examples=["https://stripe.com/jobs"])
    location_headquarters: Optional[str] = Field(None, max_length=255, examples=["San Francisco, CA"])


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    normalized_name: str
    created_at: datetime
    updated_at: datetime


class CompanyListResponse(BaseModel):
    items: List[CompanyResponse]
    total: int
