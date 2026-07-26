import re
import shlex
from pathlib import Path
from enterprise_os.governance.policy_engine import Policy
from enterprise_os.providers.tools.request import ToolRequest

# Splits a shell command into the sub-commands it could actually invoke.
_SEGMENT_SEPARATORS = re.compile(r";|&&|\|\||\|")

class CommandRestrictionPolicy(Policy):
    """Blocks a fixed set of destructive/privilege-escalating executables.

    ShellProvider is a general-purpose shell tool (the CEO/worker use it for
    arbitrary build, test, and file-management commands), so this is
    deliberately an executable-name blocklist rather than a strict argument
    allowlist -- a full allowlist would break the tool's intended use. Instead
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

    def __init__(self):
        self.forbidden_commands = sorted(self.FORBIDDEN_EXECUTABLES)

    @property
    def name(self) -> str:
        return "CommandRestriction"

    def evaluate(self, request: ToolRequest) -> tuple[bool, str]:
        if request.tool_name != "SHELL_EXECUTE":
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
