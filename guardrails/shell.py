"""Shell rules: an allow-list of commands, checked per pipeline segment.

Deny by default. A command runs only if every segment starts with a known command and every
path it names stays inside the workspace. Anything that hides the real command from this
check (command substitution, subshells, `bash -c`, `xargs`, `env`, variable expansion) is
blocked rather than parsed.

What this cannot do: `python -c ...`, `python script.py` and pytest run arbitrary code, and
the model can edit that code. No static check contains that. The OS sandbox in
`supervisor/tools.py` (seatbelt or docker) is the boundary for network, writes outside the
workspace and reads of the home directory; these rules stop the obvious attempts early and
give the model a reason it can act on.
"""
from __future__ import annotations

import re
import shlex
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # pragma: no cover
    from .policy import Policy, Verdict

SHELL_NOT_ALLOWED = "SHELL_NOT_ALLOWED"

_SUBSTITUTION = re.compile(r"\$\(|`|[<>]\(|\$['\"]")
_VARIABLE = re.compile(r"\$\{?[A-Za-z_@*#?0-9]")
_SECRET_TEXT = [
    re.compile(r"os\.environ|getenv\(|/proc/[^ ]*/environ"),
    re.compile(r"(^|[\s/'\"=])(\.env|\.netrc|\.pypirc|kaggle\.json|id_rsa|id_ed25519)\b"
               r"|\.(ssh|aws|kaggle|gnupg|docker)/"),
]
_PYTHON = re.compile(r"^(python|pypy)(\d+(\.\d+)?)?$")
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

READ_ONLY = {"ls", "cat", "head", "tail", "wc", "grep", "egrep", "fgrep", "rg", "find", "echo",
             "printf", "pwd", "diff", "sort", "uniq", "cut", "tr", "nl", "tree", "file", "stat",
             "true", "false", "cd", "which", "basename", "dirname", "date", "sed"}
WRITERS = {"rm", "rmdir", "mv", "cp", "mkdir", "touch"}
PATTERN_FIRST = {"grep", "egrep", "fgrep", "rg", "sed", "tr"}  # first operand is not a path
NO_PATHS = {"echo", "printf"}
NETWORK = {"curl", "wget", "nc", "ncat", "netcat", "telnet", "ssh", "scp", "sftp", "rsync", "ftp",
           "gh", "docker", "podman", "open"}
PACKAGE_MANAGERS = {"pip", "pip3", "pipx", "uv", "poetry", "pdm", "conda", "mamba", "npm", "npx",
                    "yarn", "pnpm", "apt", "apt-get", "brew", "gem", "cargo", "go", "easy_install"}
PIP_READ_ONLY = {"list", "show", "freeze", "check", "--version", "-V"}
DESTRUCTIVE = {"sudo", "su", "doas", "dd", "shutdown", "reboot", "halt", "kill", "killall",
               "pkill", "chmod", "chown", "chgrp", "mkfs", "diskutil", "launchctl", "crontab"}
SECRET_COMMANDS = {"env", "printenv", "set", "export", "declare", "typeset", "history"}
FIND_DELETES = {"-delete"}
FIND_EXECUTES = {"-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprintf", "-fls", "-fprint0"}

GIT_READ = {"status", "diff", "log", "show", "grep", "ls-files", "blame", "rev-parse",
            "describe", "shortlog", "ls-tree", "cat-file"}
GIT_REMOTE = {"push", "pull", "fetch", "clone", "remote", "submodule", "ls-remote", "send-pack",
              "request-pull", "archive", "bundle", "svn", "daemon"}
GIT_DESTRUCTIVE = {"reset", "clean", "checkout", "restore", "switch", "stash", "rm", "mv",
                   "rebase", "gc", "prune", "filter-branch", "update-ref", "reflog", "worktree"}
PYTHON_MODULES = {"pytest", "unittest", "doctest", "py_compile", "compileall", "json.tool",
                  "tokenize", "ast", "dis", "timeit", "this"}


_OPERATOR_CHARS = "();<>|&"
_MASK = {c: chr(0xE000 + i) for i, c in enumerate(_OPERATOR_CHARS)}
_UNMASK = {v: k for k, v in _MASK.items()}


def _mask_quoted(cmd: str) -> str:
    """Swap operator characters that sh treats as literal (quoted or backslash-escaped) for
    placeholders, so `grep 'a|b'` is one command and `ls | sh` is two. Follows POSIX sh quoting."""
    out, quote, i = [], "", 0
    while i < len(cmd):
        ch = cmd[i]
        if quote == "'":
            quote = "" if ch == "'" else quote
            out.append(_MASK.get(ch, ch))
        elif ch == "\\" and i + 1 < len(cmd):
            out.append(ch + _MASK.get(cmd[i + 1], cmd[i + 1]))
            i += 1
        elif quote == '"':
            quote = "" if ch == '"' else quote
            out.append(_MASK.get(ch, ch))
        else:
            quote = ch if ch in "'\"" else ""
            out.append(" ; " if ch == "\n" else ch)  # an unquoted newline ends the command
        i += 1
    return "".join(out)


def _lex(cmd: str) -> list[tuple[str, bool]]:
    """Tokens as (text, is_operator)."""
    if any(c in cmd for c in _UNMASK):
        raise ValueError("unsupported characters")
    lex = shlex.shlex(_mask_quoted(cmd.replace("\r", "\n")), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""  # the shell does not treat `a#b` as a comment; neither do we
    out = []
    for tok in lex:
        is_op = bool(tok) and all(c in _OPERATOR_CHARS for c in tok)
        out.append((tok if is_op else "".join(_UNMASK.get(c, c) for c in tok), is_op))
    return out


class _Checker:
    def __init__(self, policy: "Policy"):
        from .policy import Action, Verdict, is_secret_path, is_test_path
        self.p, self.Action, self.Verdict = policy, Action, Verdict
        self.is_secret, self.is_test = is_secret_path, is_test_path

    def block(self, reason: str, detail: str) -> "Verdict":
        return self.Verdict(action=self.Action.BLOCK, reason=reason, detail=detail)

    def escalate(self, what: str, seg: str) -> "Verdict":
        return self.Verdict(action=self.Action.ESCALATE, reason="BOUNDARY_ACTION", detail=f"{what}: {seg}")

    # -- paths --
    def path(self, raw: str, writing: bool, seg: str, removing: bool = False) -> Optional["Verdict"]:
        if raw in ("/dev/null", "-", ""):
            return None
        rel = self.p.rel(raw.split("::")[0])
        if rel is None:
            return self.block("DESTRUCTIVE_COMMAND" if removing else "PATH_OUTSIDE_WORKSPACE", seg)
        if removing and rel == ".":
            return self.block("DESTRUCTIVE_COMMAND", seg)
        if self.is_secret(rel):
            return self.block("SECRET_ACCESS", rel)
        if writing and self.is_test(rel):
            return self.block("TEST_FILE_EDIT", rel)
        return None

    def operands(self, args: list[str]) -> list[str]:
        """Non-flag arguments, plus the value of any --flag=value."""
        out = []
        for a in args:
            if a.startswith("--") and "=" in a:
                out.append(a.split("=", 1)[1])
            elif not a.startswith("-") or a == "-":
                out.append(a)
        return out

    def paths(self, operands: list[str], writing: bool, seg: str, removing: bool = False) -> Optional["Verdict"]:
        for o in operands:
            v = self.path(o, writing, seg, removing)
            if v:
                return v
        return None

    # -- one command --
    def segment(self, argv: list[str], seg: str) -> Optional["Verdict"]:
        if _ASSIGNMENT.match(argv[0]):
            return self.block(SHELL_NOT_ALLOWED, f"variable assignment: {seg}")
        name, args = argv[0].rsplit("/", 1)[-1], argv[1:]

        if name in NETWORK:
            return self.escalate("network", seg)
        if name in PACKAGE_MANAGERS:
            if name.startswith("pip") and args and args[0] in PIP_READ_ONLY:
                return None
            return self.escalate("dependency install", seg)
        if name in DESTRUCTIVE or name.startswith("mkfs"):
            return self.block("DESTRUCTIVE_COMMAND", seg)
        if name in SECRET_COMMANDS:
            return self.block("SECRET_ACCESS", seg)
        if name == "git":
            return self.git(args, seg)
        if _PYTHON.match(name) or name in ("pytest", "py.test"):
            return self.python(name, args, seg)
        if name in WRITERS:
            ops = self.operands(args)
            if name == "rm" and any(ch in o for o in ops for ch in "*?["):
                return self.block("DESTRUCTIVE_COMMAND", seg)
            return self.paths(ops, writing=True, seg=seg, removing=name in ("rm", "rmdir"))
        if name in READ_ONLY:
            return self.read_only(name, args, seg)
        return self.block(SHELL_NOT_ALLOWED, f"`{name}` is not an allowed command. Allowed: "
                          "python, pytest, git (read-only), ls, cat, head, tail, grep, find, sed, "
                          "diff, wc, rm/mv/cp/mkdir/touch inside the workspace.")

    def read_only(self, name: str, args: list[str], seg: str) -> Optional["Verdict"]:
        if name in NO_PATHS:
            return None
        if name == "find":
            if any(a in FIND_DELETES for a in args):
                return self.block("DESTRUCTIVE_COMMAND", seg)
            if any(a in FIND_EXECUTES for a in args):
                return self.block(SHELL_NOT_ALLOWED, f"find may not run or write: {seg}")
            ops = [a for a in args if not a.startswith("-") and ("/" in a or a in (".", "..", "~"))]
            return self.paths(ops, writing=False, seg=seg)
        ops = self.operands(args)
        in_place = name == "sed" and any(re.match(r"^(-[a-zA-Z]*i|--in-place)", a) for a in args)
        if name in PATTERN_FIRST and not any(a in ("-e", "-f") or a.startswith("--regexp")
                                             or a.startswith("--file") for a in args):
            ops = ops[1:]
        return self.paths(ops, writing=in_place, seg=seg)

    def git(self, args: list[str], seg: str) -> Optional["Verdict"]:
        if any(a in GIT_REMOTE for a in args):
            sub_at = next((i for i, a in enumerate(args) if a in GIT_REMOTE), 0)
            if args[sub_at] == "remote" and all(a in ("-v", "--verbose", "show") for a in args[sub_at + 1:]) \
                    and sub_at == 0:
                return None
            return self.escalate("git remote", seg)
        if not args or args[0].startswith("-") and args[0] not in ("--no-pager", "--version"):
            return self.block(SHELL_NOT_ALLOWED, f"git global options are not allowed: {seg}")
        rest = args[1:] if args[0] == "--no-pager" else args
        sub = rest[0] if rest else ""
        if sub in GIT_DESTRUCTIVE:
            return self.block("DESTRUCTIVE_COMMAND", seg)
        if sub not in GIT_READ and args[0] != "--version":
            return self.block(SHELL_NOT_ALLOWED, f"git {sub}: only read-only git commands are allowed "
                              "(status, diff, log, show, grep, blame, ls-files)")
        ops = [o for o in self.operands(rest[1:]) if o.startswith(("/", "~", ".")) or "/" in o]
        return self.paths(ops, writing=any(a.startswith("--output") for a in rest), seg=seg)

    def python(self, name: str, args: list[str], seg: str) -> Optional["Verdict"]:
        if name in ("pytest", "py.test"):
            return self.paths([o for o in self.operands(args) if "/" in o or o.endswith(".py")], False, seg)
        i = 0
        while i < len(args):
            a = args[i]
            if a == "-c":
                return None  # arbitrary code: contained by the OS sandbox, not by this check
            if a == "-m":
                mod = args[i + 1] if i + 1 < len(args) else ""
                rest = args[i + 2:]
                if mod in ("pip", "ensurepip"):
                    if mod == "pip" and rest and rest[0] in PIP_READ_ONLY:
                        return None
                    return self.escalate("dependency install", seg)
                if mod in PYTHON_MODULES or self.local_module(mod):
                    return self.paths([o for o in self.operands(rest) if "/" in o or o.endswith(".py")],
                                      False, seg)
                return self.block(SHELL_NOT_ALLOWED, f"python -m {mod}: only pytest, unittest and "
                                  "modules in the workspace may be run")
            if a.startswith("-"):
                i += 2 if a in ("-W", "-X") else 1
                continue
            return self.path(a, writing=False, seg=seg)  # a script: must live in the workspace
        return self.block(SHELL_NOT_ALLOWED, f"interactive python is not allowed: {seg}")

    def local_module(self, mod: str) -> bool:
        top = mod.split(".")[0]
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", top):
            return False
        ws = self.p.workspace
        return any((base / f"{top}.py").is_file() or (base / top).is_dir() for base in (ws, ws / "src"))


def shell_verdict(policy: "Policy", cmd: str) -> Optional["Verdict"]:
    """None when every segment is allowed. An ESCALATE anywhere wins over a BLOCK."""
    c = _Checker(policy)
    if _SUBSTITUTION.search(cmd):
        return c.block(SHELL_NOT_ALLOWED, "command substitution is not allowed; run one plain command")
    if _VARIABLE.search(cmd):
        return c.block("SECRET_ACCESS", "shell variables are not available")
    for rx in _SECRET_TEXT:
        if rx.search(cmd):
            return c.block("SECRET_ACCESS", cmd[:200])
    try:
        tokens = _lex(cmd)
    except ValueError as e:
        return c.block(SHELL_NOT_ALLOWED, f"could not parse the command ({e})")

    verdicts: list["Verdict"] = []
    argv: list[str] = []
    segments: list[list[str]] = []
    i = 0
    while i < len(tokens):
        tok, is_op = tokens[i]
        i += 1
        if not is_op:
            argv.append(tok)
            continue
        if "(" in tok or ")" in tok:
            verdicts.append(c.block(SHELL_NOT_ALLOWED, "subshells are not allowed"))
        elif "<" in tok or ">" in tok:
            target = tokens[i][0] if i < len(tokens) and not tokens[i][1] else None
            i += 1 if target is not None else 0
            if "<<" in tok or target is None:
                verdicts.append(c.block(SHELL_NOT_ALLOWED, "here-documents are not allowed; use the write tool"))
            elif not ("&" in tok and target.isdigit()):
                v = c.path(target, writing=">" in tok, seg=f"{tok} {target}")
                if v:
                    verdicts.append(v)
            if argv and argv[-1].isdigit() and ">" in tok:
                argv.pop()  # the fd in `2> file`
        else:  # | || && ; &
            segments.append(argv)
            argv = []
    segments.append(argv)

    for seg_argv in segments:
        if seg_argv:
            v = c.segment(seg_argv, " ".join(seg_argv)[:200])
            if v:
                verdicts.append(v)
    for v in verdicts:
        if v.action is c.Action.ESCALATE:
            return v
    return verdicts[0] if verdicts else None
