import json

from enterprise_os.infrastructure.event_store.file_action_logger import FileActionLogger


def test_file_action_logger_writes_required_fields(tmp_path) -> None:
    log_path = tmp_path / "enterprise_os.log"
    logger = FileActionLogger(log_path)

    logger.log_action(
        "test_action",
        module="tests",
        result="success",
        duration_seconds=0.25,
        error=None,
    )

    event = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])

    assert event["timestamp"]
    assert event["action"] == "test_action"
    assert event["module"] == "tests"
    assert event["result"] == "success"
    assert event["duration_seconds"] == 0.25
    assert event["error"] is None
