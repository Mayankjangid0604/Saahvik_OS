from enterprise_os.application.ports.operations import ResultCollectorPort, TaskExecutorPort, WorkerFactoryPort
from enterprise_os.domain.operations.plan import TaskPlan
from enterprise_os.domain.operations.responsibility import Responsibility
from enterprise_os.domain.operations.task import Task, TaskStatus
from enterprise_os.domain.organisation.blueprint import RoleBlueprint

class OperationalOrchestrator:
    def __init__(self, worker_factory: WorkerFactoryPort, task_executor: TaskExecutorPort, result_collector: ResultCollectorPort):
        self.worker_factory = worker_factory
        self.task_executor = task_executor
        self.result_collector = result_collector

    def orchestrate_operations(self, role: RoleBlueprint, responsibilities: tuple[Responsibility, ...]) -> None:
        # Create worker
        worker = self.worker_factory.create_worker(role, responsibilities)
        
        # Build tasks
        tasks = []
        for i, resp in enumerate(responsibilities):
            t = Task(
                identifier=f"task-{i}",
                objective=resp.title,
                description=resp.description,
                priority="High",
                assigned_worker=worker,
                required_capability=resp.required_capabilities[0] if resp.required_capabilities else None,
                dependencies=resp.dependencies,
                expected_output=resp.expected_outcome,
                status=TaskStatus.PENDING
            )
            tasks.append(t)
            
        plan = TaskPlan(
            ordered_tasks=tuple(tasks),
            dependencies=(),
            execution_order=tuple(t.identifier for t in tasks),
            completion_criteria=("All tasks complete",),
            estimated_complexity="Medium"
        )
        
        # Execute tasks
        for task in plan.ordered_tasks:
            result = self.task_executor.execute_task(task)
            self.result_collector.collect_result(result)
