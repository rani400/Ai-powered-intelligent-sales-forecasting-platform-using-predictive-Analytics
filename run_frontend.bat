@echo off
cd /d %~dp0
.venv312\Scripts\python.exe -m streamlit run frontend.py
pause
