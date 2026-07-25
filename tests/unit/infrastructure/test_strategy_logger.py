import os
from enterprise_os.infrastructure.strategy_logger import StrategyLogger

def test_strategy_logger_creates_file(tmp_path):
    log_dir = str(tmp_path / "logs")
    logger = StrategyLogger(log_dir=log_dir)
    logger.log("Strategy entry")
    
    log_file = os.path.join(log_dir, "strategy.log")
    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        content = f.read()
        assert "Strategy entry" in content
