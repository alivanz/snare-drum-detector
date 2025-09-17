@echo off
echo Starting Snare Drum Detector...
cd /d "%~dp0apps\detector"
micromamba run -n drum python main.py -w
pause