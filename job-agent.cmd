@echo off
python "%~dp0scripts\job_agent.py" %*
exit /b %ERRORLEVEL%
