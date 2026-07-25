from enterprise_os.application.use_cases.boot_ceo import BootCEO
from tests.support import InMemoryActionLogger, InMemoryDocumentStore, InMemoryThoughtLogger


def test_boot_ceo_loads_required_materials_and_returns_runtime() -> None:
    logger = InMemoryActionLogger()
    documents = InMemoryDocumentStore()

    runtime = BootCEO(
        document_loader=documents,
        action_logger=logger,
        thought_logger=InMemoryThoughtLogger(),
    ).execute()

    assert runtime is not None
    assert logger.actions == [
        "ceo_boot_started",
        "configuration_loaded",
        "constitution_loaded",
        "owner_profile_loaded",
        "company_state_loaded",
        "memory_loaded",
        "memory_saved",
        "ceo_boot_completed",
    ]


def test_boot_ceo_builds_runtime_context_from_external_documents() -> None:
    logger = InMemoryActionLogger()

    runtime = BootCEO(
        document_loader=InMemoryDocumentStore(),
        action_logger=logger,
        thought_logger=InMemoryThoughtLogger(),
    ).execute()

    assert runtime.context.runtime_configuration.runtime_name == "EnterpriseOS"
    assert runtime.context.owner_profile.owner_id == "owner"
    assert "Owner is above the CEO" in runtime.context.constitution.text
    assert runtime.context.company_state.company_name == "EnterpriseOS"
    assert runtime.context.company_state.current_projects == ()
    assert runtime.context.company_state.departments == ()
    assert runtime.context.company_state.employees == ()
    assert runtime.context.company_state.has_dynamic_departments
    assert runtime.context.company_state.has_dynamic_employees
    assert runtime.context.memory.entries[0]["kind"] == "boot_marker"


def test_boot_ceo_saves_loaded_memory_without_learning() -> None:
    logger = InMemoryActionLogger()
    documents = InMemoryDocumentStore()

    BootCEO(
        document_loader=documents,
        action_logger=logger,
        thought_logger=InMemoryThoughtLogger(),
    ).execute()

    assert documents.saved["memory.json"] == {"entries": [{"kind": "boot_marker"}]}


def test_boot_ceo_logs_failures_before_reraising() -> None:
    logger = InMemoryActionLogger()
    documents = InMemoryDocumentStore({"system.json": {}})

    try:
        BootCEO(
            document_loader=documents,
            action_logger=logger,
            thought_logger=InMemoryThoughtLogger(),
        ).execute()
    except KeyError:
        pass
    else:
        raise AssertionError("BootCEO should re-raise unrecoverable boot errors")

    assert logger.events[-1]["action"] == "configuration_loaded"
    assert logger.events[-1]["result"] == "failure"
    assert "KeyError" in str(logger.events[-1]["error"])
