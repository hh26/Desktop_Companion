@echo off
title Stopping Display Buddy...

echo Stopping Display Buddy Desktop Companion...

:: Terminate running pythonw or DisplayBuddy instances
taskkill /F /IM DisplayBuddy.exe >nul 2>&1
wmic process where "commandline like '%%main.py%%' and name='pythonw.exe'" call terminate >nul 2>&1

echo Display Buddy has gone to sleep. 💤
timeout /t 2 >nul
exit /b 0
