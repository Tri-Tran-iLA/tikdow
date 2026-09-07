@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 launch.py
goto finished
:usepython
python launch.py
:finished
if errorlevel 1 (
  echo TikDow could not start. Install Python 3.10+ with Tcl/Tk and check the error above.
  pause
)
endlocal
