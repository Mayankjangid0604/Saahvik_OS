from enterprise_os.domain.strategy.goal import StrategicGoal
from enterprise_os.domain.organisation.capability import Capability, CapabilityAnalysis
from enterprise_os.domain.organisation.function import BusinessFunction
from enterprise_os.domain.organisation.blueprint import DepartmentBlueprint, RoleBlueprint, OrganisationBlueprint
from enterprise_os.domain.organisation.review import OrganisationReview
from enterprise_os.domain.organisation.recommendation import OrganisationalRecommendation


class OrganisationalOrchestrator:
    def execute_cycle(self, goals: tuple[StrategicGoal, ...]) -> OrganisationalRecommendation:
        capabilities = self._derive_capabilities(goals)
        analysis = self._analyze_capabilities(capabilities)
        functions = self._group_functions(capabilities)
        departments = self._propose_departments(capabilities, functions)
        roles = self._propose_roles(capabilities)
        
        blueprint = OrganisationBlueprint(
            strategic_goals=goals,
            capabilities=capabilities,
            functions=functions,
            departments=departments,
            roles=roles,
            reporting_graph=("CEO -> Dept Head",),
            rationale="Aligned with strategy"
        )
        
        review = self._perform_review(blueprint)
        
        return OrganisationalRecommendation(
            executive_summary="Organisation structured for goals",
            blueprint=blueprint,
            review=review,
            benefits=("Clear alignment",),
            risks=("Execution risk",),
            assumptions=("Market holds",),
            future_concerns=()
        )

    def _derive_capabilities(self, goals: tuple[StrategicGoal, ...]) -> tuple[Capability, ...]:
        return (
            Capability(
                identifier="cap-1",
                name="Engineering Excellence",
                description="Ability to build software.",
                purpose="Product development",
                strategic_importance="High",
                required_skills=("Python", "Architecture"),
                dependencies=(),
                maturity="Low",
                confidence="High"
            ),
        )

    def _analyze_capabilities(self, capabilities: tuple[Capability, ...]) -> CapabilityAnalysis:
        return CapabilityAnalysis(
            missing_capabilities=capabilities,
            existing_capabilities=(),
            overlapping_capabilities=(),
            critical_capabilities=capabilities,
            optional_capabilities=(),
            reasoning="Current state assessment"
        )

    def _group_functions(self, capabilities: tuple[Capability, ...]) -> tuple[BusinessFunction, ...]:
        return (
            BusinessFunction(
                identifier="fun-1",
                name="Product Development",
                description="Builds the product",
                purpose="Value creation"
            ),
        )

    def _propose_departments(self, capabilities: tuple[Capability, ...], functions: tuple[BusinessFunction, ...]) -> tuple[DepartmentBlueprint, ...]:
        return (
            DepartmentBlueprint(
                identifier="dept-1",
                purpose="Software engineering",
                supported_capabilities=capabilities,
                supported_functions=functions,
                responsibilities=("Deliver code",),
                interfaces=("Product",),
                constraints=("Budget",)
            ),
        )

    def _propose_roles(self, capabilities: tuple[Capability, ...]) -> tuple[RoleBlueprint, ...]:
        return (
            RoleBlueprint(
                identifier="role-1",
                title="Lead Engineer",
                purpose="Lead tech",
                required_capabilities=capabilities,
                responsibilities=("Architecture",),
                authority="High",
                reporting_relationships=("CTO",)
            ),
        )

    def _perform_review(self, blueprint: OrganisationBlueprint) -> OrganisationReview:
        return OrganisationReview(
            duplication=(),
            bottlenecks=("Single lead",),
            missing_capabilities=(),
            excessive_hierarchy=(),
            unclear_ownership=(),
            scalability_concerns=("Cannot scale single lead",),
            summary="Review complete"
        )
