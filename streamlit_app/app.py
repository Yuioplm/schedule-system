import streamlit as st
import os
import subprocess
import threading
from time import perf_counter
from pathlib import Path

from streamlit_app.log_events import log_event
from streamlit_app.logging_config import setup_logger

st.set_page_config(layout="wide")

logger = setup_logger("streamlit_app.app")

st.title("外来スケジュール管理")
st.write("メニュー")

if "_app_started_logged" not in st.session_state:
    log_event("app_start", "メニュー")
    st.session_state["_app_started_logged"] = True


def _run_windows_bat(script_path: Path) -> tuple[bool, str]:
    request_id = log_event("windows_bat_start", "メニュー", script=str(script_path))
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
    log_event(
        "windows_bat_result",
        "メニュー",
        request_id=request_id,
        script=str(script_path),
        returncode=completed.returncode,
        elapsed_ms=elapsed_ms,
    )
    return ok, output.strip()


def _run_backup_and_shutdown() -> tuple[bool, str]:
    request_id = log_event("backup_start", "メニュー")
    backup_started_at = perf_counter()
    if os.name != "nt":
        logger.warning("backup_and_shutdown_called_on_non_windows")
        log_event(
            "backup_failed",
            "メニュー",
            request_id=request_id,
            reason="non_windows",
            elapsed_ms=int((perf_counter() - backup_started_at) * 1000),
        )
        return False, "この操作は Windows サーバー上でのみ利用できます。"

    repo_root = Path(__file__).resolve().parents[1]
    backup_bat = repo_root / "ops" / "windows" / "backup_db.bat"
    stop_bat = repo_root / "ops" / "windows" / "stop_app.bat"

    if not backup_bat.exists() or not stop_bat.exists():
        logger.error(
            "required_bat_not_found backup=%s stop=%s",
            backup_bat,
            stop_bat,
        )
        log_event(
            "backup_failed",
            "メニュー",
            request_id=request_id,
            reason="required_bat_not_found",
            backup_bat_exists=backup_bat.exists(),
            stop_bat_exists=stop_bat.exists(),
            elapsed_ms=int((perf_counter() - backup_started_at) * 1000),
        )
        return False, f"必要なバッチが見つかりません: {backup_bat} / {stop_bat}"

    backup_ok, backup_log = _run_windows_bat(backup_bat)
    if not backup_ok:
        logger.error("backup_failed backup_bat=%s detail=%s", backup_bat, backup_log)
        log_event(
            "backup_failed",
            "メニュー",
            request_id=request_id,
            reason="backup_bat_failed",
            backup_bat=str(backup_bat),
            elapsed_ms=int((perf_counter() - backup_started_at) * 1000),
        )
        return False, f"バックアップに失敗しました。\n{backup_log}"

    logger.info("backup_success_starting_stop_app stop_bat=%s", stop_bat)
    log_event(
        "backup_success",
        "メニュー",
        request_id=request_id,
        backup_bat=str(backup_bat),
        stop_bat=str(stop_bat),
        elapsed_ms=int((perf_counter() - backup_started_at) * 1000),
    )

    def _invoke_stop_app() -> None:
        stop_request_id = log_event(
            "stop_app_dispatch_start",
            "メニュー",
            parent_request_id=request_id,
            stop_bat=str(stop_bat),
        )
        try:
            completed = subprocess.run(["cmd", "/c", str(stop_bat)], check=False)
            log_event(
                "stop_app_dispatch_result",
                "メニュー",
                request_id=stop_request_id,
                stop_bat=str(stop_bat),
                returncode=completed.returncode,
            )
        except Exception as exc:
            log_event(
                "stop_app_dispatch_failed",
                "メニュー",
                request_id=stop_request_id,
                stop_bat=str(stop_bat),
                error=type(exc).__name__,
            )

    threading.Thread(
        target=_invoke_stop_app,
        daemon=True,
    ).start()
    return True, ""


with st.sidebar:
    st.markdown("---")
    shutdown_started = st.session_state.get("shutdown_started", False)

    if st.button(
        "💾 バックアップして終了",
        use_container_width=True,
        type="primary",
        disabled=shutdown_started,
    ):
        button_request_id = log_event("shutdown_requested", "メニュー")
        st.session_state["shutdown_started"] = True
        with st.spinner("バックアップして終了しています..."):
            logger.info("backup_button_clicked")
            ok, message = _run_backup_and_shutdown()
        if not ok:
            logger.error("backup_and_shutdown_failed message=%s", message)
            log_event("shutdown_failed", "メニュー", request_id=button_request_id)
            st.session_state["shutdown_started"] = False
            st.error(message)
        else:
            logger.info("backup_and_shutdown_completed")
            log_event("shutdown_completed", "メニュー", request_id=button_request_id)

pages = [
    st.Page("pages/1_枠管理.py", title="枠管理"),
    st.Page("pages/2_予定検索.py", title="予定検索"),
    st.Page("pages/3_予定変更入力.py", title="予定変更入力"),
    st.Page("pages/4_反映後予定検索.py", title="反映後予定検索"),
    st.Page("pages/5_変更登録履歴.py", title="変更登録履歴検索"),
    st.Page("pages/6_帳票1.py", title="帳票➀ 外来担当医表"),
    st.Page("pages/7_帳票2.py", title="帳票➁ 予定変更一覧"),
    st.Page("pages/8_帳票3.py", title="帳票➂ 外来数"),
    st.Page("pages/9_帳票4.py", title="帳票➃ 常勤日別コマ数"),
    st.Page("pages/10_帳票5.py", title="帳票➄ 常勤・非常勤月別コマ数"),
    st.Page("pages/11_帳票6.py", title="帳票⑥ 非常勤医師勤務報告書"),
    st.Page("pages/12_マスタ管理.py", title="マスタ管理"),
]

log_event("navigation_start", "メニュー", page_count=len(pages))
navigation = st.navigation(pages)
log_event("navigation_ready", "メニュー", page_count=len(pages))
navigation.run()
