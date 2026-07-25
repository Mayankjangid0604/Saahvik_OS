import os
from enterprise_os.infrastructure.knowledge_logger import KnowledgeLogger

def test_knowledge_logger_creates_file(tmp_path):
    log_dir = str(tmp_path / "logs")
    logger = KnowledgeLogger(log_dir=log_dir)
    logger.log("Knowledge entry")
    
    log_file = os.path.join(log_dir, "knowledge.log")
    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        content = f.read()
        assert "Knowledge entry" in content
