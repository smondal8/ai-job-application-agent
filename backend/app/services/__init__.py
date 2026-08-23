from app.services.file_storage_service import storage_service, FileStorageService
from app.services.resume_parser_service import resume_parser, ResumeParserService
from app.services.profile_service import profile_service, CandidateProfileService
from app.services.job_dedup_service import job_dedup_service, JobDeduplicationService
from app.services.job_ingestion_service import job_ingestion_service, JobIngestionService
from app.services.discovery.registry import discovery_registry, DiscoveryAdapterRegistry
from app.services.discovery.orchestrator import discovery_orchestrator, DiscoveryOrchestrationService

__all__ = [
    "storage_service",
    "FileStorageService",
    "resume_parser",
    "ResumeParserService",
    "profile_service",
    "CandidateProfileService",
    "job_dedup_service",
    "JobDeduplicationService",
    "job_ingestion_service",
    "JobIngestionService",
    "discovery_registry",
    "DiscoveryAdapterRegistry",
    "discovery_orchestrator",
    "DiscoveryOrchestrationService",
]
