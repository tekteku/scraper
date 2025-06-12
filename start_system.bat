@echo off
title Demarrage Systeme Estimation Materiaux
color 0B

echo ===============================================================================
echo               DEMARRAGE SYSTEME ESTIMATION MATERIAUX
echo ===============================================================================
echo.

REM Verification environnement virtuel
if not exist "venv\Scripts\activate.bat" (
    echo ERREUR: Environnement virtuel non trouve
    echo Executer d'abord: install_windows.bat
    pause
    exit /b 1
)

echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo.
echo ===============================================================================
echo                           MENU DE DEMARRAGE
echo ===============================================================================
echo.
echo 1. Lancer API ML/LLM (port 8000)
echo 2. Lancer Dashboard Streamlit (port 8501)
echo 3. Lancer les deux (recommande)
echo 4. Tester l'installation
echo 5. Generer un devis
echo 6. Analyser les prix
echo 7. Quitter
echo.
set /p choice="Votre choix (1-7): "

if "%choice%"=="1" goto api
if "%choice%"=="2" goto dashboard
if "%choice%"=="3" goto both
if "%choice%"=="4" goto test
if "%choice%"=="5" goto devis
if "%choice%"=="6" goto analyze
if "%choice%"=="7" goto end
goto menu

:api
echo.
echo Demarrage API ML/LLM...
echo Acces: http://localhost:8000
echo Documentation: http://localhost:8000/docs
echo.
python llm_api_server.py
goto end

:dashboard
echo.
echo Demarrage Dashboard Streamlit...
echo Acces: http://localhost:8501
echo.
streamlit run materials_dashboard.py
goto end

:both
echo.
echo Demarrage API et Dashboard...
echo.
start "API ML/LLM" cmd /k "call venv\Scripts\activate.bat && python llm_api_server.py"
timeout /t 3 > nul
start "Dashboard" cmd /k "call venv\Scripts\activate.bat && streamlit run materials_dashboard.py"
echo.
echo Services demarres:
echo - API: http://localhost:8000
echo - Dashboard: http://localhost:8501
echo.
pause
goto end

:test
echo.
echo Test de l'installation...
python -c "import fastapi, streamlit, pandas, playwright; print('✅ Tous les modules OK!')"
echo.
echo Test des donnees...
python -c "import os; print('✅ Donnees:', 'OK' if os.path.exists('DONNEES_JSON_ORGANISEES') else 'MANQUANTES')"
echo.
pause
goto menu

:devis
echo.
echo Generation d'un devis...
python devis_generator.py
echo.
pause
goto menu

:analyze
echo.
echo Analyse des prix...
python simple_price_analyzer.py
echo.
pause
goto menu

:end
echo.
echo Au revoir!
pause > nul
