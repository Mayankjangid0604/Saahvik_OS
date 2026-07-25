from dataclasses import dataclass
from datetime import datetime
from enterprise_os.domain.operations.result import ExecutionResult
from enterprise_os.domain.research.evidence import Evidence

@dataclass(frozen=True)
class Observation:
    identifier: str
    title: str
    description: str
    related_execution_results: tuple[ExecutionResult, ...]
    supporting_evidence: tuple[Evidence, ...]
    confidence: str
    created_timestamp: datetime
