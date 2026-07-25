from abc import ABC, abstractmethod
from enterprise_os.domain.operations.responsibility import Responsibility
from enterprise_os.domain.operations.result import ExecutionResult
from enterprise_os.domain.operations.task import Task
from enterprise_os.domain.operations.tools import ToolInterface
from enterprise_os.domain.operations.worker import Worker
from enterprise_os.domain.organisation.blueprint import RoleBlueprint

class WorkerFactoryPort(ABC):
    @abstractmethod
    def create_worker(self, role: RoleBlueprint, responsibilities: tuple[Responsibility, ...]) -> Worker:
        pass

class TaskExecutorPort(ABC):
    @abstractmethod
    def execute_task(self, task: Task) -> ExecutionResult:
        pass

class ToolProviderPort(ABC):
    @abstractmethod
    def get_tools(self) -> tuple[ToolInterface, ...]:
        pass

class ResultCollectorPort(ABC):
    @abstractmethod
    def collect_result(self, result: ExecutionResult) -> None:
        pass
