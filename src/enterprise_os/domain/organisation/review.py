from dataclasses import dataclass


@dataclass(frozen=True)
class OrganisationReview:
    duplication: tuple[str, ...]
    bottlenecks: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    excessive_hierarchy: tuple[str, ...]
    unclear_ownership: tuple[str, ...]
    scalability_concerns: tuple[str, ...]
    summary: str
