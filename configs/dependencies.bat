@echo off
echo Installing libraries for Bot...

python -m pip install pandas==2.2.1 >nul 2>&1
python -m pip install google-cloud==0.34.0 >nul 2>&1
python -m pip install google-cloud-bigquery==3.29.0 >nul 2>&1
python -m pip install -U langchain-google-genai
python -m pip install streamlit

echo Libraries installed succesfully!
