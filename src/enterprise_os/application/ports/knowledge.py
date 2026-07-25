from abc import ABC, abstractmethod
from enterprise_os.domain.knowledge.asset import KnowledgeAsset
from enterprise_os.domain.knowledge.retrieval import RetrievalRequest

class KnowledgeIndexPort(ABC):
    @abstractmethod
    def index_asset(self, asset: KnowledgeAsset) -> None:
        """Indexes a knowledge asset into the persistence layer."""
        pass

    @abstractmethod
    def retrieve(self, request: RetrievalRequest) -> tuple[KnowledgeAsset, ...]:
        """Retrieves knowledge assets matching the abstract retrieval request."""
        pass
