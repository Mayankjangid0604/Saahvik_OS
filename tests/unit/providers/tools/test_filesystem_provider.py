from pathlib import Path
from enterprise_os.providers.tools.implementations.filesystem_provider import FilesystemProvider
from enterprise_os.providers.tools.request import ToolRequest

def test_filesystem_provider_read_write(tmp_path: Path):
    provider = FilesystemProvider(workspace_root=str(tmp_path))

    # Write
    write_req = ToolRequest(tool_name="FILE_WRITE", arguments={"path": "test.txt", "content": "hello"})
    resp1 = provider.execute(write_req)
    assert resp1.success is True

    # Read
    read_req = ToolRequest(tool_name="FILE_READ", arguments={"path": "test.txt"})
    resp2 = provider.execute(read_req)
    assert resp2.success is True
    assert resp2.result == "hello"

    # List
    list_req = ToolRequest(tool_name="FILE_LIST", arguments={"path": "."})
    resp3 = provider.execute(list_req)
    assert resp3.success is True
    assert "test.txt" in str(resp3.result)

def test_filesystem_provider_security(tmp_path: Path):
    provider = FilesystemProvider(workspace_root=str(tmp_path))

    # Attempt directory traversal outside workspace
    read_req = ToolRequest(tool_name="FILE_READ", arguments={"path": "../outside.txt"})
    resp = provider.execute(read_req)

    assert resp.success is False
    assert "Access denied" in resp.error_message

def test_filesystem_provider_blocks_sibling_directory_with_overlapping_prefix(tmp_path: Path):
    """Regression test: str(target).startswith(str(root)) incorrectly let a
    'workspace-evil' sibling through a 'workspace' root check (confirmed
    exploitable before the fix to Path.is_relative_to())."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    evil = tmp_path / "workspace-evil"
    evil.mkdir()
    (evil / "secret.txt").write_text("leaked")

    provider = FilesystemProvider(workspace_root=str(workspace))
    resp = provider.execute(ToolRequest(tool_name="FILE_READ", arguments={"path": "../workspace-evil/secret.txt"}))

    assert resp.success is False
    assert "Access denied" in resp.error_message

def test_filesystem_provider_blocks_symlink_escape(tmp_path: Path):
    """A symlink planted inside the workspace pointing outside it must not be
    followed to leak files: _resolve_safe_path() calls .resolve() (which
    follows symlinks) before the containment check, so the resolved target
    correctly lands outside workspace_root and is rejected."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("leaked-via-symlink")
    (workspace / "escape").symlink_to(outside)

    provider = FilesystemProvider(workspace_root=str(workspace))
    resp = provider.execute(ToolRequest(tool_name="FILE_READ", arguments={"path": "escape/secret.txt"}))

    assert resp.success is False
    assert "Access denied" in resp.error_message
