from typing import Any, Dict, List, Optional, Set


class AtomicFact:
    """Represents a single atomic verified candidate fact with a canonical ID."""

    def __init__(self, fact_id: str, category: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.fact_id = fact_id
        self.category = category  # profile, experience, education, skill, project
        self.content = content
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "category": self.category,
            "content": self.content,
            "metadata": self.metadata,
        }


class AtomicFactRegistry:
    """Indexes verified candidate profile ground truth into granular, traceable atomic facts."""

    def __init__(self):
        self.facts: Dict[str, AtomicFact] = {}
        self._categories: Dict[str, List[AtomicFact]] = {
            "profile": [],
            "experience": [],
            "education": [],
            "skill": [],
            "project": [],
        }

    def register(self, fact_id: str, category: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> AtomicFact:
        fact = AtomicFact(fact_id=fact_id, category=category, content=content, metadata=metadata)
        self.facts[fact_id] = fact
        if category in self._categories:
            self._categories[category].append(fact)
        return fact

    def get(self, fact_id: str) -> Optional[AtomicFact]:
        return self.facts.get(fact_id)

    def has(self, fact_id: str) -> bool:
        return fact_id in self.facts

    def all_fact_ids(self) -> Set[str]:
        return set(self.facts.keys())

    @classmethod
    def from_ground_truth(cls, ground_truth: Dict[str, Any]) -> "AtomicFactRegistry":
        """Build atomic fact registry from candidate verified ground truth dictionary."""
        registry = cls()
        candidate = ground_truth.get("candidate", {})
        profile_id = candidate.get("id") or ground_truth.get("profile_id", 1)

        # 1. Profile metadata facts
        if candidate.get("headline"):
            registry.register(
                fact_id=f"profile:{profile_id}:headline",
                category="profile",
                content=candidate["headline"],
                metadata={"field": "headline"},
            )
        if candidate.get("summary"):
            registry.register(
                fact_id=f"profile:{profile_id}:summary",
                category="profile",
                content=candidate["summary"],
                metadata={"field": "summary"},
            )

        # 2. Work Experience facts
        for exp in ground_truth.get("experiences", []):
            exp_id = exp.get("id", "x")
            company = exp.get("company", "Unknown")
            position = exp.get("position", "Engineer")
            start = exp.get("start_date", "")
            end = "Present" if exp.get("is_current") else exp.get("end_date", "")

            # Base role fact
            registry.register(
                fact_id=f"exp:{exp_id}",
                category="experience",
                content=f"{position} at {company} ({start} - {end})",
                metadata={"exp_id": exp_id, "company": company, "position": position},
            )

            # Granular highlight bullets (support both structured highlights array and description text)
            raw_highlights = exp.get("highlights") or []
            if not raw_highlights and exp.get("description"):
                desc_text = str(exp["description"]).strip()
                desc_lines = [line.strip().lstrip("•-* ").strip() for line in desc_text.split("\n") if line.strip()]
                raw_highlights = desc_lines if desc_lines else [desc_text]

            for h_idx, highlight in enumerate(raw_highlights):
                h_str = highlight.get("text", "") if isinstance(highlight, dict) else str(highlight)
                if h_str and h_str.strip():
                    registry.register(
                        fact_id=f"exp:{exp_id}:h{h_idx}",
                        category="experience",
                        content=h_str.strip(),
                        metadata={"exp_id": exp_id, "company": company, "highlight_index": h_idx},
                    )

            # Skills used in role
            for s in exp.get("skills_used", []):
                s_clean = s.strip()
                if s_clean:
                    registry.register(
                        fact_id=f"exp:{exp_id}:skill:{s_clean.lower()}",
                        category="experience",
                        content=f"Used {s_clean} at {company}",
                        metadata={"exp_id": exp_id, "company": company, "skill": s_clean},
                    )

        # 3. Education facts
        for edu in ground_truth.get("educations", []):
            edu_id = edu.get("id", "x")
            inst = edu.get("institution", "University")
            deg = edu.get("degree", "Degree")
            field = edu.get("field_of_study", "")
            full_deg = f"{deg} in {field}" if field else deg

            registry.register(
                fact_id=f"edu:{edu_id}",
                category="education",
                content=f"{full_deg} from {inst}",
                metadata={"edu_id": edu_id, "institution": inst, "degree": deg},
            )

            for h_idx, highlight in enumerate(edu.get("highlights", [])):
                if highlight and highlight.strip():
                    registry.register(
                        fact_id=f"edu:{edu_id}:h{h_idx}",
                        category="education",
                        content=highlight.strip(),
                        metadata={"edu_id": edu_id, "institution": inst},
                    )

        # 4. Skill facts
        for sk in ground_truth.get("skills", []):
            name = sk.get("name", "").strip()
            cat = sk.get("category", "general")
            prof = sk.get("proficiency", "competent")
            sk_id = sk.get("id") or name.lower().replace(" ", "_")
            if name:
                registry.register(
                    fact_id=f"skill:{sk_id}",
                    category="skill",
                    content=f"{name} ({cat}, {prof})",
                    metadata={"name": name, "category": cat, "proficiency": prof},
                )

        # 5. Project facts
        for proj in ground_truth.get("projects", []):
            proj_id = proj.get("id", "x")
            p_name = proj.get("name", "Project")
            p_desc = proj.get("description", "")

            registry.register(
                fact_id=f"proj:{proj_id}",
                category="project",
                content=f"{p_name}: {p_desc}" if p_desc else p_name,
                metadata={"proj_id": proj_id, "name": p_name},
            )

            for h_idx, highlight in enumerate(proj.get("highlights", [])):
                if highlight and highlight.strip():
                    registry.register(
                        fact_id=f"proj:{proj_id}:h{h_idx}",
                        category="project",
                        content=highlight.strip(),
                        metadata={"proj_id": proj_id, "name": p_name, "highlight_index": h_idx},
                    )

        return registry

    def format_for_prompt(self) -> str:
        """Format atomic facts with explicit IDs for inclusion in LLM tailoring prompt."""
        lines = ["### AUTHORITATIVE VERIFIED CANDIDATE FACTS (ATOMIC FACT REGISTRY)"]
        lines.append("Every tailored bullet point and statement you produce MUST reference one or more of these exact `fact_id`s:\n")

        for cat, facts in self._categories.items():
            if not facts:
                continue
            lines.append(f"#### {cat.upper()} FACTS:")
            for f in facts:
                lines.append(f"- `[{f.fact_id}]` {f.content}")
            lines.append("")

        return "\n".join(lines)
