@echo off
set "cred=%1"
set "filename=credpath.txt"

:ifnull
REM Checks if the path was provided
if "%cred%"=="" (
    REM Checks if the file path exists
    if not exist "%filename%" (
        set /p cred= "Insira o caminho das credenciais de acesso: "
        goto :ifnull
    ) else (
        REM Gets the 1st line of the file
        for /f "delims=" %%a in ('type "%filename%"') do (
            set "cred=%%a"
            goto :done
        )
    )
)

:done
REM Checks if it's a valid path
:ifnotvalid
if exist "%cred%" (
    echo %cred% > "%filename%"
) else (
    echo O caminho informado não é válido.
    set /p cred= "Insira o caminho das credenciais de acesso: "
    goto :ifnotvalid
)

echo Creating environment
call .\configs\env.bat
set VENV_DIR = BotEnvironment

echo Activating environment
call %VENV_DIR%\Scripts\activate


if exist "%VENV_DIR%" (
    call .\configs\dependencies.bat
    echo Rodando o relatorio de atingimento mensal
    call python .\main.py %cred%
    echo Deactivating environment
    deactivate
) else (
    echo Environment not found
)
