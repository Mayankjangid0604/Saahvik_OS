from datetime import datetime, timezone
from enterprise_os.application.ports.operations import ResultCollectorPort, TaskExecutorPort, WorkerFactoryPort
from enterprise_os.application.services.operational_orchestrator import OperationalOrchestrator
from enterprise_os.domain.operations.responsibility import Responsibility
from enterprise_os.domain.operations.result import ExecutionResult
from enterprise_os.domain.operations.task import Task
from enterprise_os.domain.operations.worker import Worker, WorkerStatus
from enterprise_os.domain.organisation.blueprint import RoleBlueprint


class MockWorkerFactory(WorkerFactoryPort):
    def create_worker(self, role: RoleBlueprint, responsibilities: tuple[Responsibility, ...]) -> Worker:
        return Worker("w1", "W", "P", role, responsibilities, (), "None", WorkerStatus.IDLE, datetime.now(timezone.utc))

class MockTaskExecutor(TaskExecutorPort):
    def execute_task(self, task: Task) -> ExecutionResult:
        return ExecutionResult(task, task.assigned_worker, "Done", (), True, (), (), datetime.now(timezone.utc), ())

class MockResultCollector(ResultCollectorPort):
    def __init__(self):
        self.results = []
    
    def collect_result(self, result: ExecutionResult) -> None:
        self.results.append(result)

def test_operational_orchestrator():
    role = RoleBlueprint("r1", "Role", "Purpose", (), (), "High", ())
    resp = Responsibility("resp1", "Title", "Desc", "Outcome", (), (), "High", ())
    
    factory = MockWorkerFactory()
    executor = MockTaskExecutor()
    collector = MockResultCollector()
    
    orchestrator = OperationalOrchestrator(factory, executor, collector)
    orchestrator.orchestrate_operations(role, (resp,))
    
    assert len(collector.results) == 1
    assert collector.results[0].task.objective == "Title"
