import pytest
from datetime import datetime, timezone
from enterprise_os.domain.knowledge.asset import KnowledgeAsset
from enterprise_os.domain.knowledge.lesson import Lesson

def test_knowledge_asset_requires_lessons():
    with pytest.raises(ValueError, match="KnowledgeAsset must be based on at least one Lesson"):
        KnowledgeAsset(
            identifier="a1",
            title="Title",
            description="Desc",
            category="Cat",
            lessons=(),
            supporting_evidence=(),
            strategic_relevance="High",
            confidence="High",
            provenance="Prov"
        )
