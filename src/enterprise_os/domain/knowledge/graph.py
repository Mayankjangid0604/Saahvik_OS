from dataclasses import dataclass
from enterprise_os.domain.research.evidence import Evidence
from enterprise_os.domain.research.fact import Fact
from enterprise_os.domain.research.hypothesis import Hypothesis
from enterprise_os.domain.research.finding import Finding
from enterprise_os.domain.strategy.option import StrategicOption
from enterprise_os.domain.knowledge.work_item import WorkItem
from enterprise_os.domain.knowledge.lesson import Lesson
from enterprise_os.domain.knowledge.asset import KnowledgeAsset

@dataclass(frozen=True)
class KnowledgeGraph:
    evidence_nodes: tuple[Evidence, ...]
    fact_nodes: tuple[Fact, ...]
    hypothesis_nodes: tuple[Hypothesis, ...]
    finding_nodes: tuple[Finding, ...]
    strategy_nodes: tuple[StrategicOption, ...]
    work_item_nodes: tuple[WorkItem, ...]
    lesson_nodes: tuple[Lesson, ...]
    asset_nodes: tuple[KnowledgeAsset, ...]
