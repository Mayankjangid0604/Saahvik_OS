import os
from enterprise_os.infrastructure.organisation_logger import OrganisationLogger

def test_organisation_logger_creates_file(tmp_path):
    log_dir = str(tmp_path / "logs")
    logger = OrganisationLogger(log_dir=log_dir)
    logger.log("Organisation entry")
    
    log_file = os.path.join(log_dir, "organisation.log")
    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        content = f.read()
        assert "Organisation entry" in content
