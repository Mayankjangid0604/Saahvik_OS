import pytest
from datetime import datetime, timezone
from enterprise_os.domain.operations.result import ExecutionResult, SafetyBoundary, ActionBoundaryType
from enterprise_os.domain.operations.task import Task, TaskStatus
from enterprise_os.domain.operations.worker import Worker, WorkerStatus
from enterprise_os.domain.organisation.blueprint import RoleBlueprint

def test_execution_result_worker_validation():
    role = RoleBlueprint("r1", "Role", "Purpose", (), (), "High", ())
    worker1 = Worker("w1", "Worker 1", "Purpose", role, (), (), "None", WorkerStatus.IDLE, datetime.now(timezone.utc))
    worker2 = Worker("w2", "Worker 2", "Purpose", role, (), (), "None", WorkerStatus.IDLE, datetime.now(timezone.utc))
    
    task = Task("t1", "Obj", "Desc", "High", worker1, None, (), "Out", TaskStatus.PENDING)
    
    with pytest.raises(ValueError, match="worker must match task's assigned worker"):
        ExecutionResult(
            task=task,
            worker=worker2,
            output="Done",
            evidence=(),
            success=True,
            issues=(),
            recommendations=(),
            completion_timestamp=datetime.now(timezone.utc),
            safety_boundaries_checked=()
        )
