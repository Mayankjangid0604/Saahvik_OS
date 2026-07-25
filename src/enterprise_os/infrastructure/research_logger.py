import logging
import os


class ResearchLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "research.log")
        
        self.logger = logging.getLogger("research")
        self.logger.setLevel(logging.INFO)
        
        # Ensure we don't duplicate handlers
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Prevent logs from bubbling up to the root logger
            self.logger.propagate = False

    def log(self, message: str) -> None:
        self.logger.info(message)
