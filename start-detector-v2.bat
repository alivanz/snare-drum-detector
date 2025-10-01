@echo off
echo Starting Snare Drum Detector v2 (WebSocket)...
echo.
echo This will start the advanced detector with WebSocket streaming
echo Default settings: localhost:8765, threshold=0.2, decay=0.95
echo.
cd /d "%~dp0apps\detector"

REM Run python with explicit environment activation
echo Starting WebSocket server...
micromamba run -n drum python -u main-v2.py --threshold 0.05

echo.
echo Detector stopped.
pause