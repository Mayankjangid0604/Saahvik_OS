from enterprise_os.providers.tools.implementations.browser_provider import BrowserProvider
from enterprise_os.providers.tools.request import ToolRequest


def test_rejects_missing_url():
    provider = BrowserProvider()
    resp = provider.execute(ToolRequest(tool_name="BROWSER_NAVIGATE", arguments={}))
    assert resp.success is False
    assert "Missing" in resp.error_message


def test_rejects_file_scheme_local_file_disclosure(tmp_path):
    """Regression test: BrowserProvider passed request.arguments['url'] straight
    to urllib.request.urlopen() with no scheme check. A file:// URL let the
    tool read arbitrary local files and return their contents as the tool
    result -- reproduced live (reading /etc/hostname) before this fix. Found
    via `ruff check --select S310`."""
    secret = tmp_path / "secret.txt"
    secret.write_text("top secret local file contents")

    provider = BrowserProvider()
    resp = provider.execute(ToolRequest(tool_name="BROWSER_NAVIGATE", arguments={"url": f"file://{secret}"}))

    assert resp.success is False
    assert "top secret" not in resp.result
    assert "file" in resp.error_message.lower()


def test_rejects_ftp_and_data_schemes():
    provider = BrowserProvider()
    for scheme_url in ["ftp://example.com/", "data:text/plain,hello"]:
        resp = provider.execute(ToolRequest(tool_name="BROWSER_NAVIGATE", arguments={"url": scheme_url}))
        assert resp.success is False, f"expected {scheme_url!r} to be rejected"


def test_allows_https(monkeypatch):
    provider = BrowserProvider()

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def read(self):
            return b"<html>ok</html>"

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=10: FakeResponse())

    resp = provider.execute(ToolRequest(tool_name="BROWSER_NAVIGATE", arguments={"url": "https://example.com"}))

    assert resp.success is True
    assert resp.result == "<html>ok</html>"
