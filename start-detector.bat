@echo off
echo Starting Snare Drum Detector...
cd /d "%~dp0apps\detector"

REM Run python with explicit environment activation
micromamba run -n drum python -u main-v2.py -w
pause