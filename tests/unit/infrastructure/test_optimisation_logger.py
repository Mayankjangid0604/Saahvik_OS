import os
from enterprise_os.infrastructure.optimisation_logger import OptimisationLogger

def test_optimisation_logger_creates_file(tmp_path):
    log_dir = str(tmp_path / "logs")
    logger = OptimisationLogger(log_dir=log_dir)
    logger.log("Optimisation entry")
    
    log_file = os.path.join(log_dir, "optimisation.log")
    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        content = f.read()
        assert "Optimisation entry" in content
