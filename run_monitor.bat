@echo off
cd /d "%~dp0"
if not exist logs mkdir logs

echo ===== STARTUP ATTEMPT: %date% %time% ===== >> logs\monitor.log
echo Working dir: %cd% >> logs\monitor.log
dir credentials.json >> logs\monitor.log 2>&1

"C:\Users\DELL\AppData\Local\Programs\Python\Python313\python.exe" -u src\gmail_monitor.py >> logs\monitor.log 2>&1

echo ===== PROCESS EXITED at %date% %time% ===== >> logs\monitor.log