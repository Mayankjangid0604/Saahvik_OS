import os
from enterprise_os.infrastructure.operations_logger import OperationsLogger

def test_operations_logger_creates_file(tmp_path):
    log_dir = str(tmp_path / "logs")
    logger = OperationsLogger(log_dir=log_dir)
    logger.log("Operations entry")
    
    log_file = os.path.join(log_dir, "operations.log")
    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        content = f.read()
        assert "Operations entry" in content
