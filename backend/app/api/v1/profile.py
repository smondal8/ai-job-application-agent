from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.candidate import (
    CandidateProfileCreate,
    CandidateProfileUpdate,
    CandidateProfileResponse,
    WorkExperienceCreate,
    WorkExperienceUpdate,
    WorkExperienceResponse,
    EducationCreate,
    EducationUpdate,
    EducationResponse,
    CandidateSkillCreate,
    CandidateSkillBulkCreate,
    CandidateSkillResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    VerifiedGroundTruthContextResponse,
)
from app.services.profile_service import profile_service

router = APIRouter(prefix="/profile", tags=["Candidate Profile & Master Resume (Phase 2)"])


@router.get("", response_model=CandidateProfileResponse, summary="Get Primary Candidate Profile")
def get_primary_profile(db: Session = Depends(get_db)) -> CandidateProfileResponse:
    """Fetch the active master candidate profile with all sub-entities and verification flags."""
    profile = profile_service.get_or_create_primary_profile(db)
    return CandidateProfileResponse.model_validate(profile)


@router.post("", response_model=CandidateProfileResponse, status_code=status.HTTP_201_CREATED, summary="Create Candidate Profile")
def create_profile(
    profile_in: CandidateProfileCreate, db: Session = Depends(get_db)
) -> CandidateProfileResponse:
    """Create a new candidate profile."""
    from app.models.candidate import CandidateProfile
    profile = CandidateProfile(**profile_in.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return CandidateProfileResponse.model_validate(profile)


@router.get("/{profile_id}", response_model=CandidateProfileResponse, summary="Get Candidate Profile by ID")
def get_profile_by_id(profile_id: int, db: Session = Depends(get_db)) -> CandidateProfileResponse:
    profile = profile_service.get_profile_by_id(db, profile_id)
    return CandidateProfileResponse.model_validate(profile)


@router.put("/{profile_id}", response_model=CandidateProfileResponse, summary="Update Candidate Profile")
def update_profile(
    profile_id: int,
    profile_update: CandidateProfileUpdate,
    db: Session = Depends(get_db),
) -> CandidateProfileResponse:
    updated = profile_service.update_profile(
        db, profile_id, profile_update.model_dump(exclude_unset=True)
    )
    return CandidateProfileResponse.model_validate(updated)


@router.post("/{profile_id}/verify", response_model=CandidateProfileResponse, summary="Verify & Approve Profile Facts")
def verify_profile(
    profile_id: int,
    verify_all_children: bool = Query(True, description="Also verify all child experiences, educations, skills, and projects"),
    db: Session = Depends(get_db),
) -> CandidateProfileResponse:
    """Explicit human-in-the-loop verification gate approving candidate facts as authoritative ground truth."""
    verified = profile_service.verify_profile(db, profile_id, verify_all_children=verify_all_children)
    return CandidateProfileResponse.model_validate(verified)


@router.get(
    "/{profile_id}/verified-context",
    response_model=VerifiedGroundTruthContextResponse,
    summary="Get Authoritative Verified LLM Ground Truth Context",
    description="AUTHORITATIVE SERVICE BOUNDARY: Strictly returns ONLY verified candidate facts (is_verified=true). Excludes unverified/draft items.",
)
def get_verified_ground_truth_context(
    profile_id: int, db: Session = Depends(get_db)
) -> VerifiedGroundTruthContextResponse:
    context = profile_service.get_verified_ground_truth_context(db, profile_id)
    return VerifiedGroundTruthContextResponse(**context)


# --- Work Experiences ---

@router.post("/{profile_id}/experiences", response_model=WorkExperienceResponse, status_code=status.HTTP_201_CREATED, summary="Add Work Experience")
def add_experience(
    profile_id: int, exp_in: WorkExperienceCreate, db: Session = Depends(get_db)
) -> WorkExperienceResponse:
    exp = profile_service.add_experience(db, profile_id, exp_in.model_dump())
    return WorkExperienceResponse.model_validate(exp)


@router.put("/experiences/{exp_id}", response_model=WorkExperienceResponse, summary="Update Work Experience")
def update_experience(
    exp_id: int, exp_update: WorkExperienceUpdate, db: Session = Depends(get_db)
) -> WorkExperienceResponse:
    exp = profile_service.update_experience(db, exp_id, exp_update.model_dump(exclude_unset=True))
    return WorkExperienceResponse.model_validate(exp)


@router.delete("/experiences/{exp_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Work Experience")
def delete_experience(exp_id: int, db: Session = Depends(get_db)) -> None:
    profile_service.delete_experience(db, exp_id)


@router.post("/experiences/{exp_id}/verify", response_model=WorkExperienceResponse, summary="Toggle Experience Verification")
def verify_experience(
    exp_id: int, verified: bool = Query(True), db: Session = Depends(get_db)
) -> WorkExperienceResponse:
    exp = profile_service.verify_experience(db, exp_id, verified=verified)
    return WorkExperienceResponse.model_validate(exp)


# --- Educations ---

@router.post("/{profile_id}/educations", response_model=EducationResponse, status_code=status.HTTP_201_CREATED, summary="Add Education")
def add_education(
    profile_id: int, edu_in: EducationCreate, db: Session = Depends(get_db)
) -> EducationResponse:
    edu = profile_service.add_education(db, profile_id, edu_in.model_dump())
    return EducationResponse.model_validate(edu)


@router.put("/educations/{edu_id}", response_model=EducationResponse, summary="Update Education")
def update_education(
    edu_id: int, edu_update: EducationUpdate, db: Session = Depends(get_db)
) -> EducationResponse:
    edu = profile_service.update_education(db, edu_id, edu_update.model_dump(exclude_unset=True))
    return EducationResponse.model_validate(edu)


@router.delete("/educations/{edu_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Education")
def delete_education(edu_id: int, db: Session = Depends(get_db)) -> None:
    profile_service.delete_education(db, edu_id)


@router.post("/educations/{edu_id}/verify", response_model=EducationResponse, summary="Toggle Education Verification")
def verify_education(
    edu_id: int, verified: bool = Query(True), db: Session = Depends(get_db)
) -> EducationResponse:
    edu = profile_service.verify_education(db, edu_id, verified=verified)
    return EducationResponse.model_validate(edu)


# --- Skills ---

@router.post("/{profile_id}/skills", response_model=CandidateSkillResponse, status_code=status.HTTP_201_CREATED, summary="Add Skill")
def add_skill(
    profile_id: int, skill_in: CandidateSkillCreate, db: Session = Depends(get_db)
) -> CandidateSkillResponse:
    skill = profile_service.add_skill(db, profile_id, skill_in.model_dump())
    return CandidateSkillResponse.model_validate(skill)


@router.post("/{profile_id}/skills/bulk", response_model=List[CandidateSkillResponse], status_code=status.HTTP_201_CREATED, summary="Add Skills Bulk")
def add_skills_bulk(
    profile_id: int, bulk_in: CandidateSkillBulkCreate, db: Session = Depends(get_db)
) -> List[CandidateSkillResponse]:
    skills = profile_service.add_skills_bulk(
        db, profile_id, [s.model_dump() for s in bulk_in.skills]
    )
    return [CandidateSkillResponse.model_validate(s) for s in skills]


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Skill")
def delete_skill(skill_id: int, db: Session = Depends(get_db)) -> None:
    profile_service.delete_skill(db, skill_id)


@router.post("/skills/{skill_id}/verify", response_model=CandidateSkillResponse, summary="Toggle Skill Verification")
def verify_skill(
    skill_id: int, verified: bool = Query(True), db: Session = Depends(get_db)
) -> CandidateSkillResponse:
    skill = profile_service.verify_skill(db, skill_id, verified=verified)
    return CandidateSkillResponse.model_validate(skill)


# --- Projects ---

@router.post("/{profile_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Add Project")
def add_project(
    profile_id: int, proj_in: ProjectCreate, db: Session = Depends(get_db)
) -> ProjectResponse:
    proj = profile_service.add_project(db, profile_id, proj_in.model_dump())
    return ProjectResponse.model_validate(proj)


@router.put("/projects/{proj_id}", response_model=ProjectResponse, summary="Update Project")
def update_project(
    proj_id: int, proj_update: ProjectUpdate, db: Session = Depends(get_db)
) -> ProjectResponse:
    proj = profile_service.update_project(db, proj_id, proj_update.model_dump(exclude_unset=True))
    return ProjectResponse.model_validate(proj)


@router.delete("/projects/{proj_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Project")
def delete_project(proj_id: int, db: Session = Depends(get_db)) -> None:
    profile_service.delete_project(db, proj_id)


@router.post("/projects/{proj_id}/verify", response_model=ProjectResponse, summary="Toggle Project Verification")
def verify_project(
    proj_id: int, verified: bool = Query(True), db: Session = Depends(get_db)
) -> ProjectResponse:
    proj = profile_service.verify_project(db, proj_id, verified=verified)
    return ProjectResponse.model_validate(proj)
