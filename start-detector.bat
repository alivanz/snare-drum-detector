@echo off
echo Starting Snare Drum Detector...
cd /d "%~dp0apps\detector"

REM Initialize micromamba for this session
call micromamba shell hook -s cmd.exe
call micromamba activate drum

python main.py -w
pause