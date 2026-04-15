import logging
from uuid import uuid4

import streamlit as st

from streamlit_app.logging_config import setup_logger

logger = setup_logger("streamlit_app.events")


def get_session_id() -> str:
    if "_session_id" not in st.session_state:
        st.session_state["_session_id"] = str(uuid4())
    return st.session_state["_session_id"]


def new_request_id() -> str:
    return str(uuid4())


def log_event(
    event: str,
    page: str,
    level: int = logging.INFO,
    request_id: str | None = None,
    **fields,
) -> str:
    resolved_request_id = request_id or new_request_id()
    session_id = get_session_id()
    details = [f"event={event}", f"page={page}", f"session_id={session_id}", f"request_id={resolved_request_id}"]
    for key, value in fields.items():
        details.append(f"{key}={value}")
    logger.log(level, " ".join(details))
    return resolved_request_id


def log_page_open(page: str) -> str:
    return log_event("page_open", page)
