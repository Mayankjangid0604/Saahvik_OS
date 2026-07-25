import pytest
from pathlib import Path
from enterprise_os.providers.tools.implementations.filesystem_provider import FilesystemProvider
from enterprise_os.providers.tools.request import ToolRequest

def test_filesystem_provider_read_write(tmp_path: Path):
    provider = FilesystemProvider(workspace_root=str(tmp_path))
    
    # Write
    write_req = ToolRequest(tool_name="write_file", arguments={"path": "test.txt", "content": "hello"})
    resp1 = provider.execute(write_req)
    assert resp1.success is True
    
    # Read
    read_req = ToolRequest(tool_name="read_file", arguments={"path": "test.txt"})
    resp2 = provider.execute(read_req)
    assert resp2.success is True
    assert resp2.result == "hello"
    
    # List
    list_req = ToolRequest(tool_name="list_dir", arguments={"path": "."})
    resp3 = provider.execute(list_req)
    assert resp3.success is True
    assert "test.txt" in str(resp3.result)

def test_filesystem_provider_security(tmp_path: Path):
    provider = FilesystemProvider(workspace_root=str(tmp_path))
    
    # Attempt directory traversal outside workspace
    read_req = ToolRequest(tool_name="read_file", arguments={"path": "../outside.txt"})
    resp = provider.execute(read_req)
    
    assert resp.success is False
    assert "Access denied" in resp.error_message
