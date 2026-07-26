import re
import shlex
from pathlib import Path
from enterprise_os.governance.policy_engine import Policy
from enterprise_os.providers.tools.request import ToolRequest

# Splits a shell command into the sub-commands it could actually invoke.
_SEGMENT_SEPARATORS = re.compile(r";|&&|\|\||\|")

class CommandRestrictionPolicy(Policy):
    """Blocks a fixed set of destructive/privilege-escalating executables.

    Applies to both SHELL_EXECUTE and GIT_EXECUTE requests: ShellProvider and
    GitProvider both ultimately run their "command" argument through
    subprocess.run(shell=True), so both share the same shell-injection
    surface and must share the same gate (GitProvider was found unguarded
    during a v1.0 hardening pass -- see V1_RELEASE_PLAN.md P2-4).

    ShellProvider/GitProvider are general-purpose tools (the CEO/worker use
    them for arbitrary build, test, and file-management commands), so this is
    deliberately an executable-name blocklist rather than a strict argument
    allowlist -- a full allowlist would break their intended use. Instead
    of matching the forbidden name anywhere in the raw command string (which is
    trivially bypassed by whitespace variants, absolute paths, or chaining a
    forbidden command after an allowed one), it parses each ``;``/``&&``/``||``/
    ``|``-separated segment with ``shlex`` and checks the actual invoked
    executable name. Command substitution (``$(...)`` / backticks), which can
    hide an arbitrary sub-command from this segment-level parsing, is rejected
    outright. This closes the specific bypasses found during the v1.0 security
    audit but is not a full shell sandbox -- see SECURITY.md for residual risk.
    """

    FORBIDDEN_EXECUTABLES = frozenset({
        "rm", "sudo", "su", "mkfs", "chown", "chmod", "dd",
        "shutdown", "reboot", "halt", "poweroff", "kill", "killall",
        "userdel", "passwd", "visudo",
    })

    GATED_TOOL_NAMES = frozenset({"SHELL_EXECUTE", "GIT_EXECUTE"})

    def __init__(self):
        self.forbidden_commands = sorted(self.FORBIDDEN_EXECUTABLES)

    @property
    def name(self) -> str:
        return "CommandRestriction"

    def evaluate(self, request: ToolRequest) -> tuple[bool, str]:
        if request.tool_name not in self.GATED_TOOL_NAMES:
            return True, ""

        command = request.arguments.get("command", "")
        if not command:
            return True, ""

        if "$(" in command or "`" in command:
            return False, "Command contains command substitution ($() or backticks), which is not allowed."

        for segment in _SEGMENT_SEPARATORS.split(command):
            segment = segment.strip()
            if not segment:
                continue
            try:
                tokens = shlex.split(segment)
            except ValueError as e:
                return False, f"Command could not be safely parsed: {e}"
            if not tokens:
                continue
            executable = Path(tokens[0]).name
            if executable in self.FORBIDDEN_EXECUTABLES:
                return False, f"Command invokes forbidden executable '{executable}'."

        return True, ""
