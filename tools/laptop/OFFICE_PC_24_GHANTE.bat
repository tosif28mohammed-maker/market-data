@echo off
chcp 65001 >nul
cd /d "%~dp0"
title YouTube Script Robot - 24 ghante (office PC)
echo Office PC mode: 1 video/minute, block par 3 ghante aaram, phir khud dobara. Window band mat kijiye.
python -c "import youtube_transcript_api, yt_dlp" 2>nul
if errorlevel 1 python -m pip install --quiet youtube-transcript-api yt-dlp certifi
python yt_robot.py --loop
pause
