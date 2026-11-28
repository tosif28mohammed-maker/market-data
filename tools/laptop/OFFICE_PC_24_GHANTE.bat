@echo off
chcp 65001 >nul
cd /d "%~dp0"
title YouTube Script Robot - 24 ghante (office PC)
set PY=python
%PY% --version >nul 2>&1 || set PY=py
%PY% --version >nul 2>&1 || (echo Python nahi mila. Pehle Python install kijiye ^(step 1^). & pause & exit /b)
%PY% -c "import youtube_transcript_api, yt_dlp, truststore" 2>nul
if errorlevel 1 %PY% -m pip install --quiet --user youtube-transcript-api yt-dlp certifi truststore
if not exist github_token.txt (
  echo.
  echo GitHub token chahiye ^(laptop ke github_token.txt wala hi^). Paste karke Enter dabaiye:
  set /p TOK=Token: 
  call echo %%TOK%%> github_token.txt
)
if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\YT_Robot.bat" (
  echo @echo off> "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\YT_Robot.bat"
  echo start "YT Robot" /min "%~f0">> "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\YT_Robot.bat"
  echo PC restart hone par robot khud chalega ^(Startup mein jod diya^).
)
echo Office PC mode: 1 video/minute, block par 3 ghante aaram, phir khud dobara. Window band mat kijiye ^(minimize theek hai^).
%PY% yt_robot.py --loop
pause
