@echo off
chcp 65001 >nul
cd /d "%~dp0"
REM 預設用本機 Ollama 摘要：請先 ollama serve，並 ollama pull 你的模型（預設 llama3.2）
REM 若改用 OpenAI：設定 OPENAI_API_KEY，並在下行加上 --llm openai
python gmail_agent.py --once --query newer_than:1d --max 40
if errorlevel 1 pause
