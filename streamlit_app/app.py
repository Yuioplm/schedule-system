import streamlit as st

st.set_page_config(layout="wide")

st.title("外来スケジュール管理")
st.write("メニュー")

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
    st.Page("pages/11_マスタ管理.py", title="マスタ管理"),
]

navigation = st.navigation(pages)
navigation.run()
