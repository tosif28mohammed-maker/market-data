@echo off
chcp 65001 >nul
cd /d "%~dp0"
title YouTube Script Robot
echo ================================================
echo   YouTube Script Robot - Tosif
echo ================================================
echo.
echo [1] Zaroori tools check ho rahe hain...
python -c "import youtube_transcript_api, yt_dlp" 2>nul
if errorlevel 1 python -m pip install --quiet youtube-transcript-api yt-dlp
python -c "import youtube_transcript_api, yt_dlp" 2>nul
if errorlevel 1 (
  echo.
  echo Tools install nahi hue. Is window ki photo Claude ko bhejiye.
  pause
  exit /b
)
if not exist links.txt (
  echo # Har line mein ek YouTube video ya channel ka link daaliye, phir save karke band kijiye> links.txt
  echo.
  echo [2] links.txt khul raha hai - links daal kar SAVE karke Notepad band kijiye...
  notepad links.txt
)
echo.
echo [3] Robot chal raha hai... (beech mein window band mat kijiye)
echo.
python yt_robot.py
echo.
echo Kaam khatam. Scripts "scripts" folder mein hain.
pause
