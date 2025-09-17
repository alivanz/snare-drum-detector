@echo off
echo Starting Snare Drum Detector...
cd /d "%~dp0apps\detector"
call micromamba activate drum
python main.py -w
pause