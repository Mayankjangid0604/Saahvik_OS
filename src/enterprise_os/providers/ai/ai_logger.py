import logging
from pathlib import Path

class AILogger:
    def __init__(self, log_dir: str = "logs") -> None:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("AIPlatform")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            fh = logging.FileHandler(f"{log_dir}/ai.log")
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
            
    def log_request(self, provider: str, model: str, capability: str, duration: float, status: str) -> None:
        self.logger.info(
            f"Provider={provider} | Model={model} | Capability={capability} | Duration={duration:.2f}s | Status={status}"
        )
