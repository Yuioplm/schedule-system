import streamlit as st
import os
import subprocess
import threading
from pathlib import Path

st.set_page_config(layout="wide")

st.title("外来スケジュール管理")
st.write("メニュー")


def _run_windows_bat(script_path: Path) -> tuple[bool, str]:
    completed = subprocess.run(
        ["cmd", "/c", str(script_path)],
        capture_output=True,
        text=True,
        encoding="cp932",
    )
    ok = completed.returncode == 0
    output = (completed.stdout or "") + (completed.stderr or "")
    return ok, output.strip()


def _run_backup_and_shutdown() -> tuple[bool, str]:
    if os.name != "nt":
        return False, "この操作は Windows サーバー上でのみ利用できます。"

    repo_root = Path(__file__).resolve().parents[1]
    backup_bat = repo_root / "ops" / "windows" / "backup_db.bat"
    stop_bat = repo_root / "ops" / "windows" / "stop_app.bat"

    if not backup_bat.exists() or not stop_bat.exists():
        return False, f"必要なバッチが見つかりません: {backup_bat} / {stop_bat}"

    backup_ok, backup_log = _run_windows_bat(backup_bat)
    if not backup_ok:
        return False, f"バックアップに失敗しました。\n{backup_log}"

    threading.Thread(
        target=lambda: subprocess.run(["cmd", "/c", str(stop_bat)], check=False),
        daemon=True,
    ).start()
    return True, "バックアップを実行し、アプリ終了を開始しました。"


with st.sidebar:
    st.markdown("---")
    if st.button("💾 バックアップして終了", use_container_width=True, type="primary"):
        ok, message = _run_backup_and_shutdown()
        if ok:
            st.success(message)
        else:
            st.error(message)

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

navigation = st.navigation(pages)
navigation.run()
