@echo off
if not defined API_PORT set API_PORT=8000
cd /d "%~dp0..\src"
py -m uvicorn api_server:app --host 0.0.0.0 --port %API_PORT% --reload
