from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from streamlit_app.services import shutdown_service


def test_backup_and_shutdown_non_windows(monkeypatch) -> None:
    monkeypatch.setattr(shutdown_service, "os", SimpleNamespace(name="posix"))
    result = shutdown_service.backup_and_shutdown_with_logger(
        event_logger=shutdown_service._noop_log_event
    )
    assert result.ok is False
    assert "Windows" in result.message


def test_backup_and_shutdown_missing_batch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(shutdown_service, "os", SimpleNamespace(name="nt"))
    fake_file = tmp_path / "services" / "shutdown_service.py"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("# test", encoding="utf-8")
    monkeypatch.setattr(shutdown_service, "__file__", str(fake_file))
    result = shutdown_service.backup_and_shutdown_with_logger(
        event_logger=shutdown_service._noop_log_event
    )
    assert result.ok is False
    assert "必要なバッチが見つかりません" in result.message


def test_backup_and_shutdown_backup_failed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(shutdown_service, "os", SimpleNamespace(name="nt"))
    repo_root = tmp_path
    backup = repo_root / "ops" / "windows" / "backup_db.bat"
    stop = repo_root / "ops" / "windows" / "stop_app.bat"
    backup.parent.mkdir(parents=True)
    backup.write_text("echo backup", encoding="utf-8")
    stop.write_text("echo stop", encoding="utf-8")

    fake_file = tmp_path / "streamlit_app" / "services" / "shutdown_service.py"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("# test", encoding="utf-8")
    monkeypatch.setattr(shutdown_service, "__file__", str(fake_file))

    monkeypatch.setattr(shutdown_service, "run_windows_bat_with_logger", lambda script_path, event_logger: (False, "failed"))
    called = {"dispatched": False}

    def _fake_dispatch(*, stop_bat: Path, parent_request_id: str) -> None:
        _ = (stop_bat, parent_request_id)
        called["dispatched"] = True

    monkeypatch.setattr(shutdown_service, "dispatch_stop_app", _fake_dispatch)

    result = shutdown_service.backup_and_shutdown_with_logger(
        event_logger=shutdown_service._noop_log_event
    )
    assert result.ok is False
    assert "バックアップに失敗" in result.message
    assert called["dispatched"] is False


def test_backup_and_shutdown_success_dispatches_stop(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(shutdown_service, "os", SimpleNamespace(name="nt"))
    repo_root = tmp_path
    backup = repo_root / "ops" / "windows" / "backup_db.bat"
    stop = repo_root / "ops" / "windows" / "stop_app.bat"
    backup.parent.mkdir(parents=True)
    backup.write_text("echo backup", encoding="utf-8")
    stop.write_text("echo stop", encoding="utf-8")

    fake_file = tmp_path / "streamlit_app" / "services" / "shutdown_service.py"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("# test", encoding="utf-8")
    monkeypatch.setattr(shutdown_service, "__file__", str(fake_file))

    monkeypatch.setattr(shutdown_service, "run_windows_bat_with_logger", lambda script_path, event_logger: (True, "ok"))
    captured = {"stop_bat": None, "parent_request_id": None}

    def _fake_dispatch(*, stop_bat: Path, parent_request_id: str, event_logger) -> None:
        _ = event_logger
        captured["stop_bat"] = stop_bat
        captured["parent_request_id"] = parent_request_id

    monkeypatch.setattr(shutdown_service, "dispatch_stop_app", _fake_dispatch)

    result = shutdown_service.backup_and_shutdown_with_logger(
        event_logger=shutdown_service._noop_log_event
    )
    assert result.ok is True
    assert result.message == ""
    assert captured["stop_bat"] == stop
    assert isinstance(captured["parent_request_id"], str)
    assert captured["parent_request_id"]


def test_dispatch_stop_app_executes_subprocess(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def _fake_run(cmd, check=False):
        _ = check
        calls.append(cmd)
        return SimpleNamespace(returncode=0)

    class _ImmediateThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            self.target()

    monkeypatch.setattr(shutdown_service.subprocess, "run", _fake_run)
    monkeypatch.setattr(shutdown_service.threading, "Thread", _ImmediateThread)

    stop_bat = tmp_path / "stop_app.bat"
    shutdown_service.dispatch_stop_app(
        stop_bat=stop_bat,
        parent_request_id="parent-id",
        event_logger=shutdown_service._noop_log_event,
    )

    assert calls == [["cmd", "/c", str(stop_bat)]]
