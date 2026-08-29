@echo off
cd /d "%~dp0"
if exist ".venv-semantic\Scripts\python.exe" (
  ".venv-semantic\Scripts\python.exe" ui_demo.py --catalog data/catalog.jsonl
) else (
  python ui_demo.py --catalog data/catalog.jsonl
)
if errorlevel 1 pause
