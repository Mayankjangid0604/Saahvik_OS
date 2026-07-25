import os
from enterprise_os.infrastructure.evolution_logger import EvolutionLogger

def test_evolution_logger_creates_file(tmp_path):
    log_dir = str(tmp_path / "logs")
    logger = EvolutionLogger(log_dir=log_dir)
    logger.log("Evolution entry")
    
    log_file = os.path.join(log_dir, "evolution.log")
    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        content = f.read()
        assert "Evolution entry" in content
