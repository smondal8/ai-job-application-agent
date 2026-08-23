from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Work Experience Schemas ---

class WorkExperienceBase(BaseModel):
    company: str = Field(..., min_length=1, max_length=255, examples=["Google DeepMind"])
    position: str = Field(..., min_length=1, max_length=255, examples=["Senior AI Research Engineer"])
    location: Optional[str] = Field(None, max_length=255, examples=["London, UK"])
    start_date: str = Field(..., max_length=50, examples=["2022-01"])
    end_date: Optional[str] = Field(None, max_length=50, examples=["2024-03"])
    is_current: bool = Field(False)
    description: Optional[str] = None
    highlights: List[str] = Field(default_factory=list, examples=[["Architected autonomous coding agent infrastructure."]])
    skills_used: List[str] = Field(default_factory=list, examples=[["Python", "FastAPI", "PyTorch"]])
    order_index: int = Field(0)


class WorkExperienceCreate(WorkExperienceBase):
    pass


class WorkExperienceUpdate(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None
    highlights: Optional[List[str]] = None
    skills_used: Optional[List[str]] = None
    order_index: Optional[int] = None


class WorkExperienceResponse(WorkExperienceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime


# --- Education Schemas ---

class EducationBase(BaseModel):
    institution: str = Field(..., min_length=1, max_length=255, examples=["Stanford University"])
    degree: str = Field(..., min_length=1, max_length=255, examples=["M.S. Computer Science"])
    field_of_study: Optional[str] = Field(None, max_length=255, examples=["Artificial Intelligence"])
    start_date: Optional[str] = Field(None, max_length=50, examples=["2018"])
    end_date: Optional[str] = Field(None, max_length=50, examples=["2020"])
    gpa: Optional[str] = Field(None, max_length=50, examples=["3.95"])
    highlights: List[str] = Field(default_factory=list)


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    highlights: Optional[List[str]] = None


class EducationResponse(EducationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime


# --- Skill Schemas ---

class CandidateSkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Python"])
    category: str = Field("general", max_length=50, examples=["languages"])
    proficiency: str = Field("intermediate", max_length=50, examples=["expert"])
    years_of_experience: Optional[float] = Field(None, ge=0)


class CandidateSkillCreate(CandidateSkillBase):
    pass


class CandidateSkillBulkCreate(BaseModel):
    skills: List[CandidateSkillCreate]


class CandidateSkillResponse(CandidateSkillBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime


# --- Project Schemas ---

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Autonomous Agent Framework"])
    description: Optional[str] = None
    url: Optional[str] = Field(None, max_length=512, examples=["https://github.com/example/agent"])
    highlights: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list, examples=[["Python", "FastAPI", "React"]])


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    highlights: Optional[List[str]] = None
    technologies: Optional[List[str]] = None


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime


# --- Raw Resume Ingestion Schemas ---

class RawResumeImportCreateText(BaseModel):
    raw_text: str = Field(..., min_length=10, description="Raw resume text or markdown")
    label: Optional[str] = Field("Pasted Resume Text", max_length=100)


class RawResumeImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_id: Optional[int] = None
    filename: str
    file_path: str
    file_hash: str
    file_size_bytes: int
    mime_type: str
    status: str
    parsed_data: Optional[Dict[str, Any]] = None
    created_at: datetime


# --- Candidate Profile Schemas ---

class CandidateProfileBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255, examples=["Alex Morgan"])
    email: str = Field(..., min_length=3, max_length=255, examples=["alex.morgan@example.com"])
    phone: Optional[str] = Field(None, max_length=50, examples=["+1 (555) 019-2834"])
    location: Optional[str] = Field(None, max_length=255, examples=["San Francisco, CA"])
    headline: Optional[str] = Field(None, max_length=255, examples=["Staff Software Engineer"])
    summary: Optional[str] = None
    website: Optional[str] = Field(None, max_length=512)
    linkedin_url: Optional[str] = Field(None, max_length=512)
    github_url: Optional[str] = Field(None, max_length=512)
    portfolio_url: Optional[str] = Field(None, max_length=512)


class CandidateProfileCreate(CandidateProfileBase):
    pass


class CandidateProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class CandidateProfileResponse(CandidateProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_verified: bool
    verified_at: Optional[datetime] = None
    experiences: List[WorkExperienceResponse] = Field(default_factory=list)
    educations: List[EducationResponse] = Field(default_factory=list)
    skills: List[CandidateSkillResponse] = Field(default_factory=list)
    projects: List[ProjectResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# --- Verified Ground Truth Context Schema ---

class VerifiedGroundTruthContextResponse(BaseModel):
    profile_id: int
    profile_verified: bool
    verified_at: Optional[str] = None
    candidate: Dict[str, Any]
    experiences: List[Dict[str, Any]]
    educations: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    stats: Dict[str, int]
    formatted_llm_prompt_context: str
