@echo off
setlocal

rem Creates the local venv, or upgrades it when it already exists.
rem
rem The venv exists only to run comfy-cli for publishing to the Comfy Registry.
rem It does NOT contain torch/numpy/Pillow and is not needed to run the nodes --
rem those come from ComfyUI's own environment.
rem
rem Python itself is never upgraded here: whatever interpreter is found on PATH
rem is what a new venv is built against, and an existing venv keeps its version.

set "VENV_DIR=%~dp0venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

if exist "%VENV_PY%" (
    echo Existing venv found at "%VENV_DIR%".
    goto :upgrade
)

rem --- use whatever python is active on PATH, whatever version that is ---
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: no "python" found on PATH.
    goto :fail
)

echo Creating venv in "%VENV_DIR%" using:
python --version
python -m venv "%VENV_DIR%"
if errorlevel 1 goto :fail
if not exist "%VENV_PY%" (
    echo ERROR: venv creation did not produce "%VENV_PY%".
    goto :fail
)

:upgrade
"%VENV_PY%" --version

echo.
echo Upgrading pip / setuptools / wheel ...
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail

echo.
echo Installing / upgrading comfy-cli ...
"%VENV_PY%" -m pip install --upgrade comfy-cli
if errorlevel 1 goto :fail

echo.
echo Upgrading any remaining outdated packages ...
set "ANY_OUTDATED="
for /f "usebackq tokens=1 delims== " %%P in (`"%VENV_PY%" -m pip list --outdated --format^=freeze 2^>nul ^| findstr "=="`) do (
    set "ANY_OUTDATED=1"
    echo   %%P
    "%VENV_PY%" -m pip install --upgrade "%%P"
)
if not defined ANY_OUTDATED echo   nothing outdated.

echo.
echo Done.  Activate with:  venv\Scripts\activate
echo Publish with:          venv\Scripts\comfy.exe node publish
set "EXIT_CODE=0"
goto :finish

:fail
echo.
echo BUILD FAILED.
set "EXIT_CODE=1"

:finish
rem pause only when double-clicked from Explorer, so the output stays readable
echo %cmdcmdline% | find /i "%~nx0" >nul && pause
endlocal & exit /b %EXIT_CODE%
