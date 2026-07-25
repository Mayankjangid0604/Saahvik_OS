from enterprise_os.domain.evolution.health import EnterpriseHealth
from enterprise_os.domain.evolution.governance import GovernancePolicy

def test_enterprise_health_creation():
    health = EnterpriseHealth("High", "High", "High", "High", "High", "High")
    assert health.strategic_alignment == "High"

def test_governance_policy_creation():
    policy = GovernancePolicy("p1", "Name", "Desc", {"threshold": "1"})
    assert policy.parameters["threshold"] == "1"
