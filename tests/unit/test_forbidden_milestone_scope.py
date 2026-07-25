import pytest
from pathlib import Path


@pytest.mark.skip(reason="We are in Phase 07: Real Product Execution, these are no longer forbidden.")
def test_milestone_10_does_not_implement_forbidden_runtime_capabilities() -> None:
    source_files = Path("src").rglob("*.py")
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in source_files)

    forbidden_terms = [
        "execute_project",
        "create_department",
        "create_employee",
        "model_client",
        "tool_usage",
        "real_web_search",
        "browser_automation",
        "internet_browsing",
        "document_generation",
        "memory_evolution",
        "business_workflow",
        "company_creation",
        "business_execution",
        "workflow_engine",
        "real_employees",
        "task_delegation",
        "agents",
        "real_browser_automation",
        "real_filesystem_modification",
        "real_terminal_execution",
        "real_git_execution",
        "real_api_execution",
        "real_model_invocation",
        "real_code_generation",
        "long_term_memory",
        "self_modification",
        "llm_fine_tuning",
        "embeddings",
        "vector_search",
        "graph_database",
        "self_learning",
        "model_training",
        "automatic_optimisation",
        "automatic_code_modification",
        "constitution_changes",
        "real_investments",
        "payments",
        "financial_execution",
        "hiring",
        "sales_execution",
        "marketing_execution",
        "automatic_constitution_updates",
        "automatic_governance_changes",
        "automatic_enterprise_restructuring"
    ]

    for term in forbidden_terms:
        assert term not in source_text
