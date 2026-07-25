import os
from enterprise_os.infrastructure.growth_logger import GrowthLogger

def test_growth_logger_creates_file(tmp_path):
    log_dir = str(tmp_path / "logs")
    logger = GrowthLogger(log_dir=log_dir)
    logger.log("Growth entry")
    
    log_file = os.path.join(log_dir, "growth.log")
    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        content = f.read()
        assert "Growth entry" in content
