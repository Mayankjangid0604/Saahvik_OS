from pathlib import Path

from enterprise_os.application.use_cases.boot_ceo import BootCEO
from enterprise_os.infrastructure.config.file_document_loader import FileDocumentLoader
from enterprise_os.infrastructure.event_store.file_action_logger import FileActionLogger
from enterprise_os.infrastructure.event_store.file_thought_logger import FileThoughtLogger


MODULE_NAME = "bootstrap.ceo_bootstrap"


def boot_ceo() -> None:
    project_root = Path(__file__).resolve().parents[3]
    action_logger = FileActionLogger(project_root / "logs" / "enterprise_os.log")
    thought_logger = FileThoughtLogger(project_root / "logs" / "ceo_thoughts.log")
    document_loader = FileDocumentLoader(project_root / "config")

    action_logger.log_action(
        "main_entrypoint_started",
        module=MODULE_NAME,
        result="started",
        duration_seconds=0.0,
    )

    runtime = BootCEO(
        document_loader=document_loader,
        action_logger=action_logger,
        thought_logger=thought_logger,
    ).execute()

    try:
        runtime.run_forever()
    except KeyboardInterrupt:
        action_logger.log_action(
            "ceo_shutdown_requested",
            module=MODULE_NAME,
            result="interrupted",
            duration_seconds=0.0,
            reason="keyboard_interrupt",
        )
        raise
