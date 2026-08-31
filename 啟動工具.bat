@echo off
chcp 65001 >nul
cd /d "%~dp0"
python youtube_url_tracker.py
pause
