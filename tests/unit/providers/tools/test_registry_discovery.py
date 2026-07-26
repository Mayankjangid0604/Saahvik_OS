import sys
from enterprise_os.providers.tools.registry import ToolRegistry

def test_auto_discovery():
    registry = ToolRegistry()
    registry.auto_discover('enterprise_os.providers.tools.implementations', workspace_root=".")

    assert registry.get_provider("shell") is not None
    assert registry.get_provider("filesystem") is not None
    assert registry.get_provider("python") is not None
    assert registry.get_provider("browser") is not None
    assert registry.get_provider("git") is not None


def test_auto_discovery_logs_and_skips_a_provider_that_fails_to_construct(tmp_path, monkeypatch, caplog):
    """Regression test: a provider whose __init__ raises used to be silently
    swallowed (`except Exception: pass`) during auto_discover(), with zero
    trace -- meaning the tool platform could silently register fewer
    capabilities than expected and nobody would know why. It must now be
    logged, and must not prevent other, valid providers in the same package
    from being registered."""
    package_dir = tmp_path / "fake_tool_providers"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("")
    (package_dir / "broken_provider.py").write_text(
        "from enterprise_os.providers.tools.capability import ToolCapability\n"
        "class BrokenProvider:\n"
        "    def __init__(self):\n"
        "        raise RuntimeError('boom: misconfigured provider')\n"
        "    @property\n"
        "    def name(self) -> str:\n"
        "        return 'broken'\n"
        "    @property\n"
        "    def capabilities(self):\n"
        "        return [ToolCapability.FILE_READ]\n"
        "    def execute(self, request):\n"
        "        raise NotImplementedError\n"
    )
    (package_dir / "working_provider.py").write_text(
        "from enterprise_os.providers.tools.capability import ToolCapability\n"
        "class WorkingProvider:\n"
        "    @property\n"
        "    def name(self) -> str:\n"
        "        return 'working'\n"
        "    @property\n"
        "    def capabilities(self):\n"
        "        return [ToolCapability.FILE_LIST]\n"
        "    def execute(self, request):\n"
        "        raise NotImplementedError\n"
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop("fake_tool_providers", None)
    sys.modules.pop("fake_tool_providers.broken_provider", None)
    sys.modules.pop("fake_tool_providers.working_provider", None)

    registry = ToolRegistry()
    with caplog.at_level("WARNING"):
        registry.auto_discover("fake_tool_providers")

    assert registry.get_provider("working") is not None
    assert registry.get_provider("broken") is None
    assert any("broken_provider" in record.message or "BrokenProvider" in record.message for record in caplog.records)
