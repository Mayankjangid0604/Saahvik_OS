import json
from datetime import UTC, datetime

from enterprise_os.application.services.cognitive_engine import CognitiveEngine
from enterprise_os.application.use_cases.boot_ceo import BootCEO
from enterprise_os.domain.cognition.reasoning import ExecutiveReasoner
from enterprise_os.infrastructure.event_store.file_thought_logger import FileThoughtLogger
from tests.support import InMemoryActionLogger, InMemoryDocumentStore


def test_file_thought_logger_writes_cognitive_cycle(tmp_path) -> None:
    action_logger = InMemoryActionLogger()
    thought_logger = FileThoughtLogger(tmp_path / "ceo_thoughts.log")
    runtime = BootCEO(
        document_loader=InMemoryDocumentStore(),
        action_logger=action_logger,
        thought_logger=thought_logger,
    ).execute()
    engine = CognitiveEngine(
        context=runtime.context,
        reasoner=ExecutiveReasoner(),
        thought_logger=thought_logger,
        action_logger=action_logger,
        clock=lambda: datetime(2026, 7, 26, tzinfo=UTC),
    )

    engine.complete_cycle()

    event = json.loads((tmp_path / "ceo_thoughts.log").read_text(encoding="utf-8").splitlines()[0])
    assert event["cycle_id"] == "cognitive-cycle-1"
    assert event["thought"]["reasoning"]
    assert event["decision"]["chosen_strategy"]["title"]
    assert event["risk_profile"]["dimensions"][0]["name"] == "technical"
