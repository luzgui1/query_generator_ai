@echo off

REM Find the path to the Python executable
for /f "delims=" %%i in ('where python') do (
    set PYTHON_EXECUTABLE=%%i
    goto :FoundPython
)

:FoundPython
REM Verify if Python executable was found
if not exist "%PYTHON_EXECUTABLE%" (
    @echo off
    call %USERPROFILE%\AppData\Local\anaconda3\Scripts\activate.bat
)

REM Set the path where you want to create the virtual environment
set VENV_DIR=VENV

REM Check if the virtual environment directory already exists
if exist "%VENV_DIR%" (
    echo Virtual environment already exists in %VENV_DIR%. Skipping creation.
) else (
    REM Create the virtual environment
    "%PYTHON_EXECUTABLE%" -m venv %VENV_DIR%
)
