from enterprise_os.domain.growth.metric import GrowthMetric
from enterprise_os.domain.growth.policy import GrowthPolicy

def test_growth_metric_creation():
    metric = GrowthMetric("m1", "Revenue Growth", "Desc", 10.0, 5.0, "Up", "High")
    assert metric.value == 10.0

def test_growth_policy_creation():
    policy = GrowthPolicy("p1", "Sustainable Growth", "Desc", 1)
    assert policy.priority == 1
