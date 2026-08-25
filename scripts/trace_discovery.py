import asyncio
import json
import os
import sys
from typing import Any, Dict, List
import httpx

# Ensure backend path is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.job import Job
from app.models.discovery import JobDiscoveryRun
from app.schemas.discovery import SearchCriteria
from app.services.discovery.orchestrator import DiscoveryOrchestrationService
from app.services.discovery.adapters.greenhouse import GreenhouseDiscoveryAdapter, DEFAULT_GREENHOUSE_BOARDS
from app.services.discovery.adapters.lever import LeverDiscoveryAdapter, DEFAULT_LEVER_COMPANIES
from app.services.discovery.adapters.remote_tech import RemoteTechDiscoveryAdapter
from app.services.discovery.registry import discovery_registry


async def run_discovery_trace():
    criteria = SearchCriteria(
        keywords=[
            "Senior Software Engineer",
            "Staff Software Engineer",
            "Backend Engineer",
            "Java",
            "Spring Boot",
            "Distributed Systems",
        ],
        locations=[
            "Bangalore",
            "Bengaluru",
            "India",
            "Remote",
        ],
        remote_only=False,
        seniority_levels=[
            "senior",
            "staff",
            "lead",
        ],
        sources=[
            "greenhouse",
            "lever",
            "remote_tech",
        ],
        max_results_per_source=100,
    )

    print("=" * 80, flush=True)
    print("STARTING REAL DISCOVERY TRACE FOR INDIA / BANGALORE SEARCH PROFILE", flush=True)
    print("=" * 80, flush=True)

    keywords = [k.lower().strip() for k in criteria.keywords if k.strip()]
    locations = [loc.lower().strip() for loc in criteria.locations if loc.strip()]
    seniority_levels = [s.lower().strip() for s in criteria.seniority_levels if s.strip()]

    # 1. TRACE GREENHOUSE
    print("\n" + "=" * 40 + " 1. GREENHOUSE ADAPTER TRACE " + "=" * 40, flush=True)
    gh_adapter = GreenhouseDiscoveryAdapter()
    gh_boards_report = []
    gh_raw_all = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        async def fetch_gh(board: str):
            url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
            try:
                resp = await client.get(url)
                status = resp.status_code
                job_count = 0
                board_jobs = []
                if status == 200:
                    data = resp.json()
                    jobs = data.get("jobs", [])
                    job_count = len(jobs)
                    for rj in jobs:
                        loc_obj = rj.get("location") or {}
                        location_str = loc_obj.get("name") if isinstance(loc_obj, dict) else str(loc_obj)
                        depts = rj.get("departments") or []
                        dept_name = depts[0].get("name") if depts and isinstance(depts[0], dict) else None
                        raw_content = rj.get("content") or ""
                        clean_desc = gh_adapter._strip_html(raw_content)

                        board_jobs.append({
                            "external_id": str(rj.get("id")),
                            "source": "discovery_greenhouse",
                            "title": rj.get("title", ""),
                            "company": board.capitalize(),
                            "location": location_str,
                            "department": dept_name,
                            "url": rj.get("absolute_url"),
                            "description_raw": clean_desc or raw_content,
                            "remote_type": "remote" if "remote" in (location_str or "").lower() else "unspecified",
                            "job_type": "full-time",
                        })
                return {"board": board, "url": url, "status": status, "raw_jobs": job_count, "jobs": board_jobs}
            except Exception as e:
                return {"board": board, "url": url, "status": f"Error: {e}", "raw_jobs": 0, "jobs": []}

        gh_results = await asyncio.gather(*[fetch_gh(b) for b in DEFAULT_GREENHOUSE_BOARDS])
        for r in gh_results:
            gh_boards_report.append(r)
            gh_raw_all.extend(r["jobs"])

        print("\nGreenhouse Board HTTP Statuses:", flush=True)
        for b in gh_boards_report:
            print(f"  - {b['board']}: HTTP {b['status']} | {b['raw_jobs']} raw jobs", flush=True)

        print(f"\nTotal Greenhouse Jobs BEFORE filtering: {len(gh_raw_all)}", flush=True)

        # Keyword filter trace
        gh_after_kw = []
        gh_kw_rejected = []
        for job in gh_raw_all:
            title = str(job.get("title") or "").lower()
            desc = str(job.get("description_raw") or "").lower()
            if any(k in title or k in desc for k in keywords):
                gh_after_kw.append(job)
            else:
                gh_kw_rejected.append((job, "No matching keyword in title or description"))

        # Location filter trace
        gh_after_loc = []
        gh_loc_rejected = []
        for job in gh_after_kw:
            title = str(job.get("title") or "").lower()
            loc = str(job.get("location") or "").lower()
            remote_type = str(job.get("remote_type") or "").lower()
            matches_location = False
            for loc_query in locations:
                if loc_query in ["remote", "anywhere", "worldwide", "distributed"]:
                    if remote_type == "remote" or any(r in loc or r in title for r in ["remote", "anywhere", "worldwide", "distributed"]):
                        matches_location = True
                        break
                else:
                    aliases = gh_adapter._expand_location_aliases(loc_query)
                    if any(alias in loc for alias in aliases):
                        matches_location = True
                        break
            if matches_location:
                gh_after_loc.append(job)
            else:
                gh_loc_rejected.append((job, f"Location '{job.get('location')}' does not match {locations}"))

        # Seniority filter trace
        gh_after_sen = []
        gh_sen_rejected = []
        for job in gh_after_loc:
            title = str(job.get("title") or "").lower()
            sen = str(job.get("seniority_level") or "").lower()
            if any(s in sen or s in title for s in seniority_levels):
                gh_after_sen.append(job)
            else:
                gh_sen_rejected.append((job, f"Title '{job.get('title')}' does not contain seniority levels {seniority_levels}"))

        print(f"Greenhouse after Keyword filtering: {len(gh_after_kw)}", flush=True)
        print(f"Greenhouse after Location filtering: {len(gh_after_loc)}", flush=True)
        print(f"Greenhouse after Seniority filtering: {len(gh_after_sen)}", flush=True)

        # 2. TRACE LEVER
        print("\n" + "=" * 40 + " 2. LEVER ADAPTER TRACE " + "=" * 40, flush=True)
        lever_adapter = LeverDiscoveryAdapter()
        lever_boards_report = []
        lever_raw_all = []

        async def fetch_lever(comp: str):
            url = f"https://api.lever.co/v0/postings/{comp}?mode=json"
            try:
                resp = await client.get(url)
                status = resp.status_code
                job_count = 0
                comp_jobs = []
                if status == 200:
                    raw_postings = resp.json()
                    if isinstance(raw_postings, list):
                        job_count = len(raw_postings)
                        for posting in raw_postings:
                            categories = posting.get("categories") or {}
                            location_str = categories.get("location") or ""
                            team_name = categories.get("team")
                            commitment = categories.get("commitment") or "full-time"

                            comp_jobs.append({
                                "external_id": str(posting.get("id")),
                                "source": "discovery_lever",
                                "title": posting.get("text", ""),
                                "company": comp.capitalize(),
                                "location": location_str,
                                "department": team_name,
                                "url": posting.get("hostedUrl"),
                                "description_raw": posting.get("descriptionPlain") or posting.get("description"),
                                "remote_type": "remote" if "remote" in location_str.lower() else "unspecified",
                                "job_type": str(commitment).lower(),
                            })
                return {"company": comp, "url": url, "status": status, "raw_jobs": job_count, "jobs": comp_jobs}
            except Exception as e:
                return {"company": comp, "url": url, "status": f"Error: {e}", "raw_jobs": 0, "jobs": []}

        lever_results = await asyncio.gather(*[fetch_lever(c) for c in DEFAULT_LEVER_COMPANIES])
        for r in lever_results:
            lever_boards_report.append(r)
            lever_raw_all.extend(r["jobs"])

        print("\nLever Company HTTP Statuses:", flush=True)
        for b in lever_boards_report:
            print(f"  - {b['company']}: HTTP {b['status']} | {b['raw_jobs']} raw jobs", flush=True)

        print(f"\nTotal Lever Jobs BEFORE filtering: {len(lever_raw_all)}", flush=True)

        lever_after_kw = []
        for job in lever_raw_all:
            title = str(job.get("title") or "").lower()
            desc = str(job.get("description_raw") or "").lower()
            if any(k in title or k in desc for k in keywords):
                lever_after_kw.append(job)

        lever_after_loc = []
        for job in lever_after_kw:
            title = str(job.get("title") or "").lower()
            loc = str(job.get("location") or "").lower()
            remote_type = str(job.get("remote_type") or "").lower()
            matches_location = False
            for loc_query in locations:
                if loc_query in ["remote", "anywhere", "worldwide", "distributed"]:
                    if remote_type == "remote" or any(r in loc or r in title for r in ["remote", "anywhere", "worldwide", "distributed"]):
                        matches_location = True
                        break
                else:
                    aliases = lever_adapter._expand_location_aliases(loc_query)
                    if any(alias in loc for alias in aliases):
                        matches_location = True
                        break
            if matches_location:
                lever_after_loc.append(job)

        lever_after_sen = []
        for job in lever_after_loc:
            title = str(job.get("title") or "").lower()
            sen = str(job.get("seniority_level") or "").lower()
            if any(s in sen or s in title for s in seniority_levels):
                lever_after_sen.append(job)

        print(f"Lever after Keyword filtering: {len(lever_after_kw)}", flush=True)
        print(f"Lever after Location filtering: {len(lever_after_loc)}", flush=True)
        print(f"Lever after Seniority filtering: {len(lever_after_sen)}", flush=True)

        # 3. TRACE REMOTE_TECH
        print("\n" + "=" * 40 + " 3. REMOTE_TECH ADAPTER TRACE " + "=" * 40, flush=True)
        rt_adapter = RemoteTechDiscoveryAdapter()
        rt_raw_all = []
        try:
            url = "https://remoteok.com/api"
            headers = {"User-Agent": "AIJobAgent/0.3.0 (Operational; dev)"}
            resp = await client.get(url, headers=headers)
            status = resp.status_code
            if status == 200:
                data = resp.json()
                raw_items = [d for d in data if isinstance(d, dict) and d.get("position")]
                for item in raw_items:
                    skills = item.get("tags") or []
                    rt_raw_all.append({
                        "external_id": str(item.get("id")),
                        "source": "discovery_remote_tech",
                        "title": item.get("position", ""),
                        "company": item.get("company", "Unknown"),
                        "location": item.get("location") or "Remote",
                        "url": item.get("url"),
                        "description_raw": item.get("description"),
                        "remote_type": "remote",
                        "job_type": "full-time",
                        "skills_raw": skills if isinstance(skills, list) else [str(skills)],
                        "salary_min": item.get("salary_min"),
                        "salary_max": item.get("salary_max"),
                    })
            print(f"RemoteTech API Status: HTTP {status} | {len(rt_raw_all)} raw jobs", flush=True)
        except Exception as e:
            print(f"RemoteTech API Error: {e}", flush=True)

        rt_after_kw = []
        for job in rt_raw_all:
            title = str(job.get("title") or "").lower()
            desc = str(job.get("description_raw") or "").lower()
            if any(k in title or k in desc for k in keywords):
                rt_after_kw.append(job)

        rt_after_loc = []
        for job in rt_after_kw:
            title = str(job.get("title") or "").lower()
            loc = str(job.get("location") or "").lower()
            remote_type = str(job.get("remote_type") or "").lower()
            matches_location = False
            for loc_query in locations:
                if loc_query in ["remote", "anywhere", "worldwide", "distributed"]:
                    if remote_type == "remote" or any(r in loc or r in title for r in ["remote", "anywhere", "worldwide", "distributed"]):
                        matches_location = True
                        break
                else:
                    aliases = rt_adapter._expand_location_aliases(loc_query)
                    if any(alias in loc for alias in aliases):
                        matches_location = True
                        break
            if matches_location:
                rt_after_loc.append(job)

        rt_after_sen = []
        for job in rt_after_loc:
            title = str(job.get("title") or "").lower()
            sen = str(job.get("seniority_level") or "").lower()
            if any(s in sen or s in title for s in seniority_levels):
                rt_after_sen.append(job)

        print(f"RemoteTech after Keyword filtering: {len(rt_after_kw)}", flush=True)
        print(f"RemoteTech after Location filtering: {len(rt_after_loc)}", flush=True)
        print(f"RemoteTech after Seniority filtering: {len(rt_after_sen)}", flush=True)

    # 4. EXECUTE FULL REAL ORCHESTRATOR RUN & INGESTION
    print("\n" + "=" * 40 + " 4. FULL ORCHESTRATOR RUN & INGESTION " + "=" * 40, flush=True)
    db = SessionLocal()
    try:
        orch = DiscoveryOrchestrationService()
        run_result = await orch.execute_discovery_run(db=db, criteria=criteria)
        db.commit()

        print(f"Run ID: {run_result.run_id}", flush=True)
        print(f"Status: {run_result.status}", flush=True)
        print(f"Total Discovered: {run_result.total_discovered}", flush=True)
        print(f"Total Inserted: {run_result.inserted_count}", flush=True)
        print(f"Total Duplicates: {run_result.duplicate_count}", flush=True)
        print(f"Total Errors: {run_result.error_count}", flush=True)
        print(f"Adapter Logs: {json.dumps(run_result.adapter_logs, indent=2)}", flush=True)

        # 5. QUERY DATABASE FOR INDIA / BANGALORE / BENGALURU / BLR JOBS
        print("\n" + "=" * 40 + " 5. PERSISTED INDIA / BANGALORE JOBS IN DATABASE " + "=" * 40, flush=True)
        from sqlalchemy import or_
        india_jobs = (
            db.query(Job)
            .filter(
                or_(
                    Job.location.ilike("%india%"),
                    Job.location.ilike("%bangalore%"),
                    Job.location.ilike("%bengaluru%"),
                    Job.location.ilike("%blr%"),
                )
            )
            .order_by(Job.id.desc())
            .all()
        )

        print(f"Total matching India/Bangalore jobs in database: {len(india_jobs)}", flush=True)
        print(f"{'job_id':<8} | {'title':<42} | {'company':<16} | {'location':<30} | {'source':<22} | {'created_at'}", flush=True)
        print("-" * 145, flush=True)
        for j in india_jobs:
            created = j.created_at.strftime("%Y-%m-%d %H:%M:%S") if j.created_at else "N/A"
            print(f"{j.id:<8} | {j.title[:40]:<42} | {j.company[:14]:<16} | {str(j.location)[:28]:<30} | {str(j.source)[:20]:<22} | {created}", flush=True)

        print("\n" + "=" * 40 + " 6. ALL ACCEPTED JOBS FROM THE 3 ADAPTERS " + "=" * 40, flush=True)
        for ad_name, ad_res in [("Greenhouse", gh_after_sen), ("Lever", lever_after_sen), ("RemoteTech", rt_after_sen)]:
            print(f"\n--- {ad_name} Accepted ({len(ad_res)}) ---", flush=True)
            for aj in ad_res:
                print(f"  * Title: {aj['title']}\n    Company: {aj['company']}\n    Location: {aj['location']}\n    URL: {aj['url']}\n", flush=True)

        print("\n" + "=" * 40 + " 7. RAW INDIA/BANGALORE JOBS BEFORE FILTERING (SAMPLE) " + "=" * 40, flush=True)
        raw_india_jobs = [
            j for j in (gh_raw_all + lever_raw_all + rt_raw_all)
            if any(x in str(j.get("location")).lower() for x in ["india", "bangalore", "bengaluru", "blr"])
        ]
        print(f"Total Raw India/Bangalore jobs retrieved across all boards: {len(raw_india_jobs)}", flush=True)
        for rij in raw_india_jobs[:30]:
            t_low = rij['title'].lower()
            d_low = rij.get('description_raw', '').lower()
            has_kw = any(k in t_low or k in d_low for k in keywords)
            matched_kws = [k for k in keywords if k in t_low or k in d_low]
            has_loc = any(x in str(rij.get("location")).lower() for x in ["india", "bangalore", "bengaluru", "blr"])
            has_sen = any(s in t_low for s in seniority_levels)
            print(f"  * Company: {rij['company']} | Title: {rij['title']} | Location: {rij['location']}", flush=True)
            print(f"    -> Keywords Match: {has_kw} (matched: {matched_kws}) | Loc Match: {has_loc} | Seniority Match ({seniority_levels}): {has_sen}", flush=True)
            if not has_sen:
                print(f"    ==> REJECTED BY SENIORITY FILTER because title '{rij['title']}' lacks 'senior', 'staff', 'lead'", flush=True)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run_discovery_trace())
