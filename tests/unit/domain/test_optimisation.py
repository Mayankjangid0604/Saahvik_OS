from enterprise_os.domain.optimisation.metric import Metric
from enterprise_os.domain.optimisation.policy import OptimisationPolicy

def test_metric_creation():
    metric = Metric("m1", "Name", "Desc", 10.0, 5.0, "Up", "High")
    assert metric.value == 10.0

def test_optimisation_policy_creation():
    policy = OptimisationPolicy("p1", "Name", "Desc", 1)
    assert policy.priority == 1
