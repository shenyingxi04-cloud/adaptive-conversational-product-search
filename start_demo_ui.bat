@echo off
cd /d "%~dp0"
python ui_demo.py --catalog data/catalog_copy.jsonl
if errorlevel 1 pause
