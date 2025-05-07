echo Creating environment
call .\configs\env.bat
set VENV_DIR = BotEnvironment

echo Activating environment
call %VENV_DIR%\Scripts\activate


if exist "%VENV_DIR%" (
    call .\configs\dependencies.bat
    echo Rodando o assistente do CUBO.
    call streamlit run streamlit.py --server.address=0.0.0.0 --server.port=8501
    echo Deactivating environment
    deactivate
) else (
    echo Environment not found
)
