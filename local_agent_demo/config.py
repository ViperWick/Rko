"""本機 Ollama（OpenAI 相容端點）設定。可改環境變數覆寫。"""
import os

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
# 本機不驗證，隨便填即可
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "ollama")

MAX_AGENT_STEPS = 8
