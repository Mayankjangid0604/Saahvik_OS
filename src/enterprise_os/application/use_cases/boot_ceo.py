from enterprise_os.application.ports.action_logger import ActionLogger
from enterprise_os.application.ports.document_loader import DocumentLoader
from enterprise_os.application.ports.thought_logger import ThoughtLogger
from enterprise_os.application.services.action_logging import logged_action
from enterprise_os.application.services.cognitive_engine import CognitiveEngine
from enterprise_os.application.services.ceo_runtime import CEORuntime
from enterprise_os.domain.ceo.company_state import CompanyState
from enterprise_os.domain.ceo.constitution import Constitution
from enterprise_os.domain.ceo.context import CEOContext
from enterprise_os.domain.ceo.runtime_configuration import RuntimeConfiguration
from enterprise_os.domain.cognition.reasoning import ExecutiveReasoner
from enterprise_os.domain.memory.runtime_memory import RuntimeMemory
from enterprise_os.domain.owner.profile import OwnerProfile


MODULE_NAME = "application.boot_ceo"


class BootCEO:
    def __init__(
        self,
        document_loader: DocumentLoader,
        action_logger: ActionLogger,
        thought_logger: ThoughtLogger,
    ) -> None:
        self._document_loader = document_loader
        self._action_logger = action_logger
        self._thought_logger = thought_logger

    def execute(self) -> CEORuntime:
        self._action_logger.log_action(
            "ceo_boot_started",
            module=MODULE_NAME,
            result="started",
            duration_seconds=0.0,
        )

        runtime_configuration = logged_action(
            self._action_logger,
            action="configuration_loaded",
            module=MODULE_NAME,
            operation=lambda: RuntimeConfiguration.from_mapping(
                self._document_loader.load_mapping("system.json")
            ),
        )

        constitution = logged_action(
            self._action_logger,
            action="constitution_loaded",
            module=MODULE_NAME,
            operation=lambda: Constitution(self._document_loader.load_text("constitution.md")),
        )

        owner_profile = logged_action(
            self._action_logger,
            action="owner_profile_loaded",
            module=MODULE_NAME,
            operation=lambda: OwnerProfile.from_mapping(
                self._document_loader.load_mapping("owner_profile.json")
            ),
        )

        company_state = logged_action(
            self._action_logger,
            action="company_state_loaded",
            module=MODULE_NAME,
            operation=lambda: CompanyState.from_mapping(
                self._document_loader.load_mapping("company_state.json")
            ),
        )

        memory = logged_action(
            self._action_logger,
            action="memory_loaded",
            module=MODULE_NAME,
            operation=lambda: RuntimeMemory.from_mapping(
                self._document_loader.load_mapping("memory.json")
            ),
        )

        context = CEOContext(
            runtime_configuration=runtime_configuration,
            constitution=constitution,
            owner_profile=owner_profile,
            company_state=company_state,
            memory=memory,
        )

        self._persist_loaded_memory(memory)
        cognitive_engine = CognitiveEngine(
            context=context,
            reasoner=ExecutiveReasoner(),
            thought_logger=self._thought_logger,
            action_logger=self._action_logger,
        )
        runtime = CEORuntime(
            context=context,
            action_logger=self._action_logger,
            loop_step=cognitive_engine.complete_cycle,
        )

        self._action_logger.log_action(
            "ceo_boot_completed",
            module=MODULE_NAME,
            result="success",
            duration_seconds=0.0,
        )
        return runtime

    def _persist_loaded_memory(self, memory: RuntimeMemory) -> None:
        logged_action(
            self._action_logger,
            action="memory_saved",
            module=MODULE_NAME,
            operation=lambda: self._document_loader.save_mapping("memory.json", memory.to_mapping()),
        )
