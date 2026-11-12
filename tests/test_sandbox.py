"""OS sandbox: what the static policy cannot stop (`python -c`, code run by tests) is stopped here.

These commands are ones `Policy.check` allows. They run for real, so they only use a
throwaway marker file and a local socket."""
import socket
import threading
import uuid
from pathlib import Path

import pytest

from guardrails.policy import Action, Policy, ToolCall
from supervisor.tools import Workspace, resolve_sandbox

FIXTURE = Path(__file__).resolve().parents[1] / "evals" / "fixtures" / "tinycalc"
needs_seatbelt = pytest.mark.skipif(resolve_sandbox("auto") != "seatbelt", reason="needs macOS sandbox-exec")


@pytest.fixture
def ws(monkeypatch):
    monkeypatch.delenv("NOISEGATE_SANDBOX", raising=False)
    w = Workspace(FIXTURE)
    yield w
    w.cleanup()


def run_allowed(ws, cmd):
    assert Policy(ws.path).check(ToolCall(name="shell", args={"cmd": cmd})).action is Action.ALLOW
    return ws.run(cmd, timeout=30)


def test_sandbox_mode_resolution(monkeypatch):
    assert resolve_sandbox("docker") == "docker" and resolve_sandbox("LOCAL") == "local"
    with pytest.raises(ValueError):
        resolve_sandbox("none")
    monkeypatch.setenv("NOISEGATE_SANDBOX", "local")
    w = Workspace(FIXTURE)
    try:
        assert w.sandbox == "local" and not w.isolated
    finally:
        w.cleanup()


@needs_seatbelt
def test_normal_work_still_runs(ws):
    assert ws.isolated
    code, out = run_allowed(ws, "python -c 'import calc; print(calc.add(2, 3))' > out.txt && cat out.txt")
    assert code == 0 and out.strip() == "-1"
    code, out = run_allowed(ws, "python -m pytest -q")
    assert "failed" in out and "passed" in out  # the fixture's bug, found by a real pytest run
    assert run_allowed(ws, "git status --short")[0] == 0


@needs_seatbelt
def test_write_outside_workspace_is_denied(ws):
    marker = Path.home() / f".noisegate_sandbox_probe_{uuid.uuid4().hex}"
    try:
        code, out = run_allowed(ws, f"python -c \"open({str(marker)!r}, 'w').write('x')\"")
        assert code != 0 and "not permitted" in out and not marker.exists()
    finally:
        marker.unlink(missing_ok=True)


@needs_seatbelt
def test_read_of_home_directory_is_denied(ws):
    marker = Path.home() / f".noisegate_sandbox_probe_{uuid.uuid4().hex}"
    marker.write_text("not-a-real-secret")
    try:
        code, out = run_allowed(ws, f"python -c \"print(open({str(marker)!r}).read())\"")
        assert code != 0 and "not-a-real-secret" not in out
    finally:
        marker.unlink(missing_ok=True)


@needs_seatbelt
def test_network_is_denied(ws):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    srv.settimeout(10)
    port, hits = srv.getsockname()[1], []

    def accept():
        try:
            hits.append(srv.accept())
        except OSError:
            pass

    t = threading.Thread(target=accept, daemon=True)
    t.start()
    code, out = run_allowed(ws, f"python -c \"import socket; socket.create_connection(('127.0.0.1', {port}), 3)\"")
    srv.close()
    t.join(2)
    assert code != 0 and not hits, out


@needs_seatbelt
def test_test_file_edit_via_python_is_caught_at_submit(ws):
    from guardrails.output import check_patch
    run_allowed(ws, "python -c \"open('tests/test_calc.py', 'w').write('')\"")
    names, lines, _ = ws.diff()
    assert "TEST_FILE_CHANGED" in check_patch(ws.path, names, lines).failures
