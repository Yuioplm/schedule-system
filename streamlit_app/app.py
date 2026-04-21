import streamlit as st

from streamlit_app.log_events import log_event
from streamlit_app.logging_config import setup_logger
from streamlit_app.services.shutdown_service import backup_and_shutdown_with_logger

st.set_page_config(layout="wide")

logger = setup_logger("streamlit_app.app")

st.title("外来スケジュール管理")
st.write("メニュー")

if "_app_started_logged" not in st.session_state:
    log_event("app_start", "メニュー")
    st.session_state["_app_started_logged"] = True
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
            result = backup_and_shutdown_with_logger(event_logger=log_event)
        if not result.ok:
            logger.error("backup_and_shutdown_failed message=%s", result.message)
            log_event("shutdown_failed", "メニュー", request_id=button_request_id)
            st.session_state["shutdown_started"] = False
            st.error(result.message)
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
