import os
from enterprise_os.infrastructure.research_logger import ResearchLogger

def test_research_logger_creates_file(tmp_path):
    log_dir = str(tmp_path / "logs")
    logger = ResearchLogger(log_dir=log_dir)
    logger.log("Test log entry")
    
    log_file = os.path.join(log_dir, "research.log")
    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        content = f.read()
        assert "Test log entry" in content
