from pathlib import Path

from enterprise_os.governance.policies.workspace_confinement import WorkspaceConfinementPolicy
from enterprise_os.providers.tools.request import ToolRequest


def test_ignores_non_filesystem_requests(tmp_path: Path):
    policy = WorkspaceConfinementPolicy(workspace_root=str(tmp_path))
    request = ToolRequest(tool_name="SHELL_EXECUTE", arguments={"command": "rm -rf /"})
    approved, reason = policy.evaluate(request)
    assert approved is True


def test_allows_paths_inside_workspace(tmp_path: Path):
    policy = WorkspaceConfinementPolicy(workspace_root=str(tmp_path))
    request = ToolRequest(tool_name="FILE_READ", arguments={"path": "sub/file.txt"})
    approved, reason = policy.evaluate(request)
    assert approved is True


def test_blocks_directory_traversal_outside_workspace(tmp_path: Path):
    policy = WorkspaceConfinementPolicy(workspace_root=str(tmp_path))
    request = ToolRequest(tool_name="FILE_WRITE", arguments={"path": "../outside.txt"})
    approved, reason = policy.evaluate(request)
    assert approved is False
    assert "Access denied" in reason


def test_blocks_sibling_directory_with_overlapping_name_prefix(tmp_path: Path):
    """Regression test: str(target).startswith(str(root)) incorrectly allowed a
    'workspace-evil' sibling through a 'workspace' root check, since the string
    prefix match doesn't respect path boundaries. Confirmed exploitable via
    FilesystemProvider (which shares this pattern) before the fix to
    Path.is_relative_to()."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    policy = WorkspaceConfinementPolicy(workspace_root=str(workspace))

    request = ToolRequest(tool_name="FILE_READ", arguments={"path": "../workspace-evil/secret.txt"})
    approved, reason = policy.evaluate(request)

    assert approved is False
    assert "Access denied" in reason
