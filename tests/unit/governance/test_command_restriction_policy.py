import pytest

from enterprise_os.governance.policies.command_restriction import CommandRestrictionPolicy
from enterprise_os.providers.tools.request import ToolRequest


def _shell(command: str) -> ToolRequest:
    return ToolRequest(tool_name="SHELL_EXECUTE", arguments={"command": command})


def _git(command: str) -> ToolRequest:
    return ToolRequest(tool_name="GIT_EXECUTE", arguments={"command": command})


def test_ignores_non_shell_requests():
    policy = CommandRestrictionPolicy()
    request = ToolRequest(tool_name="FILE_READ", arguments={"command": "rm -rf /"})
    approved, reason = policy.evaluate(request)
    assert approved is True


def test_allows_legitimate_commands():
    policy = CommandRestrictionPolicy()
    for command in ["mkdir flask_blog", "python app.py", "git init", "echo hello", "pip install flask"]:
        approved, reason = policy.evaluate(_shell(command))
        assert approved is True, f"expected '{command}' to be allowed, got: {reason}"


def test_blocks_forbidden_executable_directly():
    policy = CommandRestrictionPolicy()
    approved, reason = policy.evaluate(_shell("rm -rf /tmp/x"))
    assert approved is False
    assert "rm" in reason


@pytest.mark.parametrize("bypass_command", [
    "rm  -rf /tmp/x",           # extra whitespace defeated the old substring match
    "/bin/rm -rf /tmp/x",       # absolute path defeated the old substring match
    "echo hi && rm -rf /tmp/x", # chaining after an allowed command
    "echo hi; sudo ls",         # semicolon-separated forbidden command
    "echo hi || sudo ls",       # or-chained forbidden command
    "echo hi | sudo tee /x",    # piped forbidden command
])
def test_blocks_previously_working_bypasses(bypass_command):
    policy = CommandRestrictionPolicy()
    approved, reason = policy.evaluate(_shell(bypass_command))
    assert approved is False, f"expected '{bypass_command}' to be blocked"


@pytest.mark.parametrize("substitution_command", [
    "echo $(rm -rf /)",
    "echo `rm -rf /`",
])
def test_blocks_command_substitution(substitution_command):
    policy = CommandRestrictionPolicy()
    approved, reason = policy.evaluate(_shell(substitution_command))
    assert approved is False
    assert "substitution" in reason


def test_empty_command_is_allowed_here_and_left_to_the_provider():
    policy = CommandRestrictionPolicy()
    approved, reason = policy.evaluate(_shell(""))
    assert approved is True


def test_allows_legitimate_git_commands():
    policy = CommandRestrictionPolicy()
    for command in ["log", "status", "git status", "diff HEAD~1"]:
        approved, reason = policy.evaluate(_git(command))
        assert approved is True, f"expected '{command}' to be allowed, got: {reason}"


def test_blocks_forbidden_executable_chained_after_git_command():
    """Regression test: GitProvider runs its 'command' argument through
    subprocess.run(shell=True) exactly like ShellProvider (prefixing it with
    "git " first), but CommandRestrictionPolicy previously only inspected
    SHELL_EXECUTE requests -- a command that was correctly blocked when
    routed as SHELL_EXECUTE sailed through completely unchecked when routed
    as GIT_EXECUTE, even though it runs through the identical shell=True
    subprocess call. Confirmed exploitable via a live PolicyEngine +
    CommandRestrictionPolicy + GitProvider reproduction before this fix."""
    policy = CommandRestrictionPolicy()
    approved, reason = policy.evaluate(_git("log; rm -rf /tmp/x"))
    assert approved is False
    assert "rm" in reason


def test_blocks_command_substitution_in_git_commands():
    policy = CommandRestrictionPolicy()
    approved, reason = policy.evaluate(_git("log $(rm -rf /)"))
    assert approved is False
    assert "substitution" in reason
