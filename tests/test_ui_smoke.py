from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
from urllib.request import urlopen


@pytest.mark.skipif(os.name != "nt", reason="Windows運用環境向けスモーク")
def test_streamlit_top_page_is_reachable() -> None:
    if shutil.which("streamlit") is None:
        pytest.skip("streamlit command is not available in this environment")
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_app/app.py",
        "--server.headless",
        "true",
        "--server.port",
        "18501",
        "--browser.gatherUsageStats",
        "false",
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        url = "http://127.0.0.1:18501"
        deadline = time.time() + 30
        last_error: Exception | None = None
        while time.time() < deadline:
            try:
                with urlopen(url, timeout=1) as response:
                    body = response.read().decode("utf-8", errors="ignore")
                    if response.status == 200:
                        assert "Streamlit" in body
                        return
            except Exception as exc:  # noqa: BLE001
                last_error = exc
            time.sleep(0.5)

        output = ""
        if proc.stdout is not None:
            output = proc.stdout.read()
        raise AssertionError(f"Streamlit起動確認に失敗: {last_error}\n{output}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
