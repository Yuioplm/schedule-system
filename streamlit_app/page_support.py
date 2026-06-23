import base64
import mimetypes
import pathlib
import re

import streamlit as st

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
DOC_DIR = ROOT_DIR / "docs"
MANUAL_FILE = "担当者マニュアル.md"
DOC_FILES = [
    "README.md",
    MANUAL_FILE,
    "障害対応手順.md",
    "ログ出力仕様.md",
    "保守引継ぎ_ページ関連マップ.md",
]

PAGE_GUIDES: dict[str, list[str]] = {
    "枠管理": [
        "期間・曜日・診療科などを指定して対象の枠を絞り込みます。",
        "編集対象の行を選んで内容を更新し、保存して反映します。",
    ],
    "予定検索": [
        "開始日・終了日と必要な絞り込み条件を指定して検索します。",
        "変更したい行の『変更』ボタンから予定変更入力画面へ進みます。",
    ],
    "予定変更入力": [
        "『通常枠の予定変更』は予定検索画面で対象枠を選択してから入力します。",
        "『臨時外来登録』はこの画面から直接入力できます。",
        "必須項目を入力して登録後、反映後予定検索で結果を確認します。",
    ],
    "反映後予定検索": [
        "反映後の実績予定を条件指定で検索し、表示内容を確認します。",

    ],
    "変更登録履歴検索": [
        "期間や条件を指定して変更履歴を検索します。",
        "必要に応じて帳票出力やエクスポートを実行します。",
    ],
    "帳票① 外来担当医表": [
        "対象年月を選択して帳票を作成します。",
        "出力内容を確認後、必要に応じてダウンロードします。",
    ],
    "帳票➁ 予定変更一覧": [
        "開始日を指定して予定変更一覧を取得します。",
        "CSVに加えて、前回の配布用Excel出力との差分を反映した書式付きExcelを出力できます。",
        "プレビューExcelは履歴に残さず、配布用Excelのみ次回差分判定の基準になります。",
    ],
    "帳票➂ 外来数": [
        "年と月を指定して外来数を集計します。",
        "月次の報告資料に利用します。",
    ],
    "帳票➃ 常勤日別コマ数": [
        "対象の年・月を指定して日別コマ数を表示します。",
        "月次の報告資料に利用します。",
    ],
    "帳票➄ 常勤・非常勤月別コマ数": [
        "対象の年・月を選んで月別コマ数を集計します。",
        "月次の報告資料に利用します。",
    ],
    "帳票⑥ 非常勤医師勤務報告書": [
        "上部プレビューは対象年月と非常勤医師を選択して個人別に確認できます。",
        "Excelダウンロードは選択した年月の対象医師分を一括で出力します。",
    ],
    "マスタ管理": [
        "対象マスタのタブを選択し、追加・更新・有効/無効を管理します。",
        "変更後は関連画面で検索し、意図どおり反映されたか確認します。",
    ],
    "ドキュメント閲覧": [
        "参照したいドキュメントを選択し、内容を画面上で確認します。",
    ],
}


_MD_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def _resolve_document_path(document_name: str) -> pathlib.Path:
    if document_name == "README.md":
        return ROOT_DIR / document_name
    return DOC_DIR / document_name


def _normalize_image_path(path_value: str) -> str:
    normalized = path_value.strip().strip('"').strip("'")
    if " " in normalized and not normalized.startswith("http"):
        normalized = normalized.split(" ", 1)[0]
    return normalized


def _embed_local_images(markdown_text: str, base_dir: pathlib.Path) -> str:
    def replace(match: re.Match[str]) -> str:
        alt_text = match.group(1)
        image_path_raw = _normalize_image_path(match.group(2))

        if image_path_raw.startswith(("http://", "https://", "data:", "#")):
            return match.group(0)

        image_path = (base_dir / image_path_raw).resolve()
        if not image_path.exists() or not image_path.is_file():
            return match.group(0)

        mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"![{alt_text}](data:{mime_type};base64,{encoded})"

    return _MD_IMAGE_PATTERN.sub(replace, markdown_text)


def render_page_guide(page_name: str, *, show_manual_link: bool = True) -> None:
    steps = PAGE_GUIDES.get(page_name)
    if not steps:
        return

    with st.expander("簡単操作ガイド", expanded=True):
        for idx, step in enumerate(steps, start=1):
            st.markdown(f"{idx}. {step}")

        if show_manual_link:
            st.caption("詳細な操作手順は『担当者マニュアル.md』をご確認ください。")
            if st.button("📘 担当者マニュアルを開く", key=f"open_manual::{page_name}", use_container_width=False):
                st.session_state["doc_viewer_target"] = MANUAL_FILE
                st.switch_page("pages/13_ドキュメント閲覧.py")


def get_document_content(document_name: str) -> str:
    if document_name not in DOC_FILES:
        raise ValueError("Unsupported document")

    path = _resolve_document_path(document_name)
    if not path.exists():
        raise FileNotFoundError(str(path))

    raw_content = path.read_text(encoding="utf-8")
    return _embed_local_images(raw_content, path.parent)
