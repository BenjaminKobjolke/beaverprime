cd /d "%~dp0"

call .venv\Scripts\activate 

python scripts/export_user_data.py user@example.com > user_data.json
echo Exported to user_data.json