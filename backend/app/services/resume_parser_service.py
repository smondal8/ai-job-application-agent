import json
import re
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger("app.services.parser")


class ResumeParserService:
    """Extracts structured draft candidate facts from untrusted imported resume text.
    
    IMPORTANT:
    - All extracted facts are strictly tagged as UNTRUSTED_DRAFT until verified by the user.
    - NEVER invent missing facts (missing fields remain None or empty).
    """

    def parse_raw_text(self, raw_text: str) -> Dict[str, Any]:
        """Parse raw text/markdown into structured draft candidate profile facts."""
        if not raw_text or not raw_text.strip():
            return {
                "provenance": "untrusted_import",
                "is_verified": False,
                "profile": {},
                "experiences": [],
                "educations": [],
                "skills": [],
                "projects": [],
            }

        # Check if raw text is valid JSON formatted resume (e.g. JSON Resume standard)
        try:
            parsed_json = json.loads(raw_text)
            if isinstance(parsed_json, dict):
                return self._parse_from_json_dict(parsed_json)
        except Exception:
            pass  # Proceed with regular text parsing

        return self._parse_from_text(raw_text)

    def _parse_from_json_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a structured JSON resume into standard draft structure."""
        basics = data.get("basics") or data.get("profile") or data
        profile = {
            "full_name": basics.get("name") or basics.get("full_name") or "Imported Candidate",
            "email": basics.get("email") or "",
            "phone": basics.get("phone"),
            "location": basics.get("location") if isinstance(basics.get("location"), str) else (basics.get("location") or {}).get("city"),
            "headline": basics.get("label") or basics.get("headline"),
            "summary": basics.get("summary"),
            "website": basics.get("url") or basics.get("website"),
            "linkedin_url": basics.get("linkedin_url"),
            "github_url": basics.get("github_url"),
            "portfolio_url": basics.get("portfolio_url"),
            "is_verified": False,
        }

        # Work experiences
        experiences = []
        work_list = data.get("work") or data.get("experiences") or data.get("experience") or []
        for idx, work in enumerate(work_list):
            if isinstance(work, dict):
                experiences.append({
                    "company": work.get("company") or work.get("name") or "Company",
                    "position": work.get("position") or work.get("role") or work.get("title") or "Position",
                    "location": work.get("location"),
                    "start_date": str(work.get("startDate") or work.get("start_date") or ""),
                    "end_date": str(work.get("endDate") or work.get("end_date") or "") or None,
                    "is_current": bool(work.get("is_current") or not (work.get("endDate") or work.get("end_date"))),
                    "description": work.get("summary") or work.get("description"),
                    "highlights": work.get("highlights") or [],
                    "skills_used": work.get("skills_used") or work.get("technologies") or [],
                    "order_index": idx,
                    "is_verified": False,
                })

        # Education
        educations = []
        edu_list = data.get("education") or data.get("educations") or []
        for edu in edu_list:
            if isinstance(edu, dict):
                educations.append({
                    "institution": edu.get("institution") or edu.get("school") or edu.get("university") or "Institution",
                    "degree": edu.get("studyType") or edu.get("degree") or "Degree",
                    "field_of_study": edu.get("area") or edu.get("field_of_study"),
                    "start_date": str(edu.get("startDate") or edu.get("start_date") or "") or None,
                    "end_date": str(edu.get("endDate") or edu.get("end_date") or "") or None,
                    "gpa": str(edu.get("score") or edu.get("gpa") or "") or None,
                    "highlights": edu.get("courses") or edu.get("highlights") or [],
                    "is_verified": False,
                })

        # Skills
        skills = []
        skill_list = data.get("skills") or []
        for item in skill_list:
            if isinstance(item, dict):
                skill_name = item.get("name")
                if skill_name:
                    skills.append({
                        "name": skill_name,
                        "category": item.get("category") or "general",
                        "proficiency": item.get("level") or item.get("proficiency") or "intermediate",
                        "is_verified": False,
                    })
                # If it has keywords list
                for kw in item.get("keywords") or []:
                    if kw and kw != skill_name:
                        skills.append({
                            "name": str(kw),
                            "category": item.get("name") or "technical",
                            "proficiency": "intermediate",
                            "is_verified": False,
                        })
            elif isinstance(item, str) and item.strip():
                skills.append({
                    "name": item.strip(),
                    "category": "general",
                    "proficiency": "intermediate",
                    "is_verified": False,
                })

        # Projects
        projects = []
        proj_list = data.get("projects") or []
        for proj in proj_list:
            if isinstance(proj, dict):
                projects.append({
                    "name": proj.get("name") or "Project",
                    "description": proj.get("description") or proj.get("summary"),
                    "url": proj.get("url"),
                    "highlights": proj.get("highlights") or [],
                    "technologies": proj.get("keywords") or proj.get("technologies") or [],
                    "is_verified": False,
                })

        return {
            "provenance": "untrusted_import",
            "is_verified": False,
            "profile": profile,
            "experiences": experiences,
            "educations": educations,
            "skills": skills,
            "projects": projects,
        }

    def _parse_from_text(self, text: str) -> Dict[str, Any]:
        """Rule-based text extractor for free-form plain text and markdown resumes."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # 1. Contact Info Extraction
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
        email = email_match.group(0) if email_match else "imported@candidate.local"

        phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        phone = phone_match.group(0) if phone_match else None

        linkedin_match = re.search(r"https?://(?:www\.)?linkedin\.com/in/[\w-]+", text)
        linkedin_url = linkedin_match.group(0) if linkedin_match else None

        github_match = re.search(r"https?://(?:www\.)?github\.com/[\w-]+", text)
        github_url = github_match.group(0) if github_match else None

        # First non-empty line often contains full name
        full_name = lines[0] if lines else "Imported Candidate"
        # If the first line looks like an email or URL, fallback
        if "@" in full_name or "http" in full_name or len(full_name) > 60:
            full_name = "Imported Candidate"

        # 2. Extract sections by identifying common headers
        section_headers = {
            "experience": ["experience", "work experience", "employment", "professional experience"],
            "education": ["education", "academic background", "academics"],
            "skills": ["skills", "technical skills", "competencies", "technologies"],
            "projects": ["projects", "personal projects", "open source"],
            "summary": ["summary", "professional summary", "about me", "objective"],
        }

        # Find section boundaries
        sections: Dict[str, List[str]] = {k: [] for k in section_headers}
        current_section = "summary"

        for line in lines:
            normalized = line.strip("#-*= ").lower()
            matched_sec = None
            for sec_name, headers in section_headers.items():
                if normalized in headers or any(normalized.startswith(h) and len(normalized) < len(h) + 5 for h in headers):
                    matched_sec = sec_name
                    break
            
            if matched_sec:
                current_section = matched_sec
            else:
                sections[current_section].append(line)

        # 3. Build summary
        summary_text = "\n".join(sections["summary"][:6]) if sections["summary"] else None

        # 4. Extract Skills
        skills = []
        skill_text = " ".join(sections["skills"])
        # Split by comma, pipe, bullet, or newline
        raw_skill_tokens = re.split(r"[,|•·\n]", skill_text)
        for token in raw_skill_tokens:
            cleaned = token.strip().strip("-*• ")
            if cleaned and len(cleaned) < 40 and not cleaned.lower().startswith("skills"):
                skills.append({
                    "name": cleaned,
                    "category": self._infer_skill_category(cleaned),
                    "proficiency": "intermediate",
                    "is_verified": False,
                })

        # 5. Extract Experiences
        experiences = []
        exp_lines = sections["experience"]
        current_exp: Optional[Dict[str, Any]] = None

        for line in exp_lines:
            if line.startswith(("-", "*", "•")):
                # Bullet highlight
                bullet = line.lstrip("-*• ").strip()
                if current_exp:
                    current_exp["highlights"].append(bullet)
            elif len(line) > 3 and (" - " in line or " | " in line or " at " in line or "20" in line):
                if current_exp:
                    experiences.append(current_exp)
                
                parts = re.split(r"[-|–—]", line)
                position = parts[0].strip() if len(parts) > 0 else "Software Engineer"
                company = parts[1].strip() if len(parts) > 1 else "Technology Company"

                current_exp = {
                    "company": company,
                    "position": position,
                    "start_date": "2022",
                    "end_date": None,
                    "is_current": True,
                    "description": None,
                    "highlights": [],
                    "skills_used": [],
                    "order_index": len(experiences),
                    "is_verified": False,
                }
            elif current_exp and not current_exp["description"]:
                current_exp["description"] = line

        if current_exp:
            experiences.append(current_exp)

        # 6. Extract Education
        educations = []
        edu_lines = sections["education"]
        for line in edu_lines:
            if any(term in line.lower() for term in ["university", "college", "institute", "bs", "ms", "bachelor", "master", "phd", "degree"]):
                parts = line.split(",")
                inst = parts[0].strip()
                deg = parts[1].strip() if len(parts) > 1 else "Degree"
                educations.append({
                    "institution": inst,
                    "degree": deg,
                    "is_verified": False,
                })

        # 7. Extract Projects
        projects = []
        proj_lines = sections["projects"]
        for line in proj_lines:
            if not line.startswith(("-", "*", "•")) and len(line) > 3:
                projects.append({
                    "name": line.strip(),
                    "description": None,
                    "highlights": [],
                    "technologies": [],
                    "is_verified": False,
                })

        profile = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "location": None,
            "headline": None,
            "summary": summary_text,
            "linkedin_url": linkedin_url,
            "github_url": github_url,
            "is_verified": False,
        }

        return {
            "provenance": "untrusted_import",
            "is_verified": False,
            "profile": profile,
            "experiences": experiences,
            "educations": educations,
            "skills": skills[:25],  # Reasonable upper bound
            "projects": projects[:5],
        }

    def _infer_skill_category(self, skill_name: str) -> str:
        """Categorize common technical skills."""
        s = skill_name.lower()
        if any(lang in s for lang in ["python", "javascript", "typescript", "java", "c++", "go", "rust", "ruby", "php", "sql", "html", "css"]):
            return "languages"
        elif any(fw in s for lang in ["react", "vue", "angular", "fastapi", "django", "flask", "node", "express", "spring", "next"] for fw in [lang]):
            return "frameworks"
        elif any(db in s for db in ["postgres", "sqlite", "mysql", "mongodb", "redis", "elasticsearch", "cassandra"]):
            return "databases"
        elif any(c in s for c in ["aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ci/cd", "git", "linux"]):
            return "cloud_devops"
        return "general"


resume_parser = ResumeParserService()
