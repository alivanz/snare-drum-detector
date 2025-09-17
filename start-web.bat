@echo off
echo Starting Drum Web Application...
cd /d "%~dp0apps\drum-web"
call pnpm dev
pause