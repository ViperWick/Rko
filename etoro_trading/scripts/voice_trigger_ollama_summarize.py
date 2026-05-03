# -*- coding: utf-8 -*-
"""
對麥克風說關鍵字 → 自動執行 `ollama-summarize`。

前置：
  1. 本機 Ollama 已開、已 pull 模型。
  2. pip install -r etoro_trading/requirements-voice.txt
     （Windows 上 PyAudio 失敗請見該檔案註解。）
  3. 需網路：預設用 Google 語音辨識（繁中 zh-TW）。

執行（在 repo 根目錄或任意目錄皆可，腳本會自行切到根目錄跑子行程）：
  py -m etoro_trading.scripts listen-ollama-summarize

關鍵字（說出任一句或含下列組合即可觸發）：
  「執行摘要」「開始摘要」「跑摘要」「Ollama 摘要」
  或英文：run summarize / ollama summarize
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _should_run_summarize(text: str) -> bool:
    t = text.strip().lower()
    if not t:
        return False
    # 英文
    if re.search(r"\b(run|start)\s+summarize\b", t):
        return True
    if "ollama" in t and "summarize" in t:
        return True
    # 中文（用原始字串）
    raw = text.strip()
    if "摘要" in raw and (
        "執行" in raw
        or "開始" in raw
        or "跑" in raw
        or "幫我" in raw
        or "現在" in raw
        or "立刻" in raw
    ):
        return True
    if "ollama" in t and "摘要" in raw:
        return True
    return False


def _run_summarize_subprocess() -> int:
    return subprocess.call(
        [sys.executable, "-m", "etoro_trading.scripts", "ollama-summarize"],
        cwd=str(_REPO_ROOT),
    )


def main() -> int:
    try:
        import speech_recognition as sr  # type: ignore
    except ImportError:
        print(
            "請先安裝語音依賴：\n"
            "  pip install -r etoro_trading/requirements-voice.txt\n"
            "若 pyaudio 安裝失敗，請看 requirements-voice.txt 裡的 pipwin 說明。",
            file=sys.stderr,
        )
        return 1

    r = sr.Recognizer()
    try:
        mic = sr.Microphone()
    except OSError as e:
        print(f"無法開啟麥克風：{e}", file=sys.stderr)
        return 1

    print(
        "語音監聽已啟動。請對麥克風說，例如：「執行摘要」或「開始摘要」。\n"
        "（使用 Google 線上辨識，需網路；按 Ctrl+C 結束。）\n"
    )

    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1.0)

    while True:
        try:
            with mic as source:
                print("聆聽中…")
                audio = r.listen(source, timeout=None, phrase_time_limit=8)
            print("辨識中…")
            try:
                text = r.recognize_google(audio, language="zh-TW")
            except sr.UnknownValueError:
                print("  （聽不清楚，再試一次）")
                continue
            except sr.RequestError as e:
                print(f"  語音服務錯誤：{e}", file=sys.stderr)
                continue

            print(f"  聽到：{text!r}")
            if _should_run_summarize(text):
                print(">>> 觸發 ollama-summarize\n")
                code = _run_summarize_subprocess()
                print(f"\n>>> 子行程結束，代碼 {code}\n")
            else:
                print("  （未符合關鍵字，略過）")
        except KeyboardInterrupt:
            print("\n已結束。")
            return 0


if __name__ == "__main__":
    sys.exit(main())
