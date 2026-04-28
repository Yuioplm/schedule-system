import streamlit as st

from streamlit_app.log_events import log_page_open
from streamlit_app.page_support import DOC_FILES, get_document_content, render_page_guide

st.title("ドキュメント閲覧")
log_page_open("ドキュメント閲覧")
render_page_guide("ドキュメント閲覧", show_manual_link=False)

default_doc = st.session_state.get("doc_viewer_target", DOC_FILES[0])
default_index = DOC_FILES.index(default_doc) if default_doc in DOC_FILES else 0

selected_doc = st.selectbox("表示するドキュメント", DOC_FILES, index=default_index)
st.session_state["doc_viewer_target"] = selected_doc

try:
    content = get_document_content(selected_doc)
except FileNotFoundError:
    st.error(f"ドキュメントが見つかりません: {selected_doc}")
else:
    st.markdown(content)
