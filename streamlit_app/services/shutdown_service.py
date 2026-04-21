from __future__ import annotations

import os
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from streamlit_app.logging_config import setup_logger

logger = setup_logger("streamlit_app.services.shutdown")
EventLogger = Callable[..., str]


@dataclass
class ShutdownResult:
    ok: bool
    message: str = ""


def run_windows_bat(script_path: Path) -> tuple[bool, str]:
    return run_windows_bat_with_logger(script_path=script_path, event_logger=_noop_log_event)


def run_windows_bat_with_logger(script_path: Path, event_logger: EventLogger) -> tuple[bool, str]:
    request_id = event_logger("windows_bat_start", "メニュー", script=str(script_path))
    started_at = perf_counter()
    logger.info("running_windows_bat script=%s", script_path)
    completed = subprocess.run(
        ["cmd", "/c", str(script_path)],
        capture_output=True,
        text=True,
        encoding="cp932",
    )
    ok = completed.returncode == 0
    output = (completed.stdout or "") + (completed.stderr or "")
    logger.info(
        "windows_bat_completed script=%s returncode=%s",
        script_path,
        completed.returncode,
    )
    elapsed_ms = int((perf_counter() - started_at) * 1000)
    event_logger(
        "windows_bat_result",
        "メニュー",
        request_id=request_id,
        script=str(script_path),
        returncode=completed.returncode,
        elapsed_ms=elapsed_ms,
    )
    return ok, output.strip()


def backup_and_shutdown() -> ShutdownResult:
    return backup_and_shutdown_with_logger(event_logger=_noop_log_event)


def backup_and_shutdown_with_logger(event_logger: EventLogger) -> ShutdownResult:
    request_id = event_logger("backup_start", "メニュー")
    backup_started_at = perf_counter()
    if os.name != "nt":
        logger.warning("backup_and_shutdown_called_on_non_windows")
        event_logger(
            "backup_failed",
            "メニュー",
            request_id=request_id,
            reason="non_windows",
            elapsed_ms=int((perf_counter() - backup_started_at) * 1000),
        )
        return ShutdownResult(ok=False, message="この操作は Windows サーバー上でのみ利用できます。")

    repo_root = Path(__file__).resolve().parents[2]
    backup_bat = repo_root / "ops" / "windows" / "backup_db.bat"
    stop_bat = repo_root / "ops" / "windows" / "stop_app.bat"

    if not backup_bat.exists() or not stop_bat.exists():
        logger.error(
            "required_bat_not_found backup=%s stop=%s",
            backup_bat,
            stop_bat,
        )
        event_logger(
            "backup_failed",
            "メニュー",
            request_id=request_id,
            reason="required_bat_not_found",
            backup_bat_exists=backup_bat.exists(),
            stop_bat_exists=stop_bat.exists(),
            elapsed_ms=int((perf_counter() - backup_started_at) * 1000),
        )
        return ShutdownResult(
            ok=False,
            message=f"必要なバッチが見つかりません: {backup_bat} / {stop_bat}",
        )

    backup_ok, backup_log = run_windows_bat_with_logger(
        script_path=backup_bat,
        event_logger=event_logger,
    )
    if not backup_ok:
        logger.error("backup_failed backup_bat=%s detail=%s", backup_bat, backup_log)
        event_logger(
            "backup_failed",
            "メニュー",
            request_id=request_id,
            reason="backup_bat_failed",
            backup_bat=str(backup_bat),
            elapsed_ms=int((perf_counter() - backup_started_at) * 1000),
        )
        return ShutdownResult(ok=False, message=f"バックアップに失敗しました。\n{backup_log}")

    logger.info("backup_success_starting_stop_app stop_bat=%s", stop_bat)
    event_logger(
        "backup_success",
        "メニュー",
        request_id=request_id,
        backup_bat=str(backup_bat),
        stop_bat=str(stop_bat),
        elapsed_ms=int((perf_counter() - backup_started_at) * 1000),
    )
    dispatch_stop_app(stop_bat=stop_bat, parent_request_id=request_id, event_logger=event_logger)
    return ShutdownResult(ok=True, message="")


def dispatch_stop_app(stop_bat: Path, parent_request_id: str, event_logger: EventLogger) -> None:
    def _invoke_stop_app() -> None:
        stop_request_id = event_logger(
            "stop_app_dispatch_start",
            "メニュー",
            parent_request_id=parent_request_id,
            stop_bat=str(stop_bat),
        )
        try:
            completed = subprocess.run(["cmd", "/c", str(stop_bat)], check=False)
            event_logger(
                "stop_app_dispatch_result",
                "メニュー",
                request_id=stop_request_id,
                stop_bat=str(stop_bat),
                returncode=completed.returncode,
            )
        except Exception as exc:
            event_logger(
                "stop_app_dispatch_failed",
                "メニュー",
                request_id=stop_request_id,
                stop_bat=str(stop_bat),
                error=type(exc).__name__,
            )

    threading.Thread(target=_invoke_stop_app, daemon=True).start()


def _noop_log_event(_event: str, _page: str, **_fields: Any) -> str:
    return "noop-request-id"
