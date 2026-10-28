@echo off
cd /d %~dp0
if not exist .venv312\Scripts\python.exe py -m venv .venv312
.venv312\Scripts\python.exe -m pip install -r requirements.txt
.venv312\Scripts\python.exe -m uvicorn app.main:app --reload
pause
