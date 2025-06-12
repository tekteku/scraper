@echo off
title Installation Systeme Estimation Materiaux Tunisiens
color 0A

echo ===============================================================================
echo                 INSTALLATION AUTOMATIQUE WINDOWS
echo        Systeme d'Estimation Materiaux Tunisiens
echo ===============================================================================
echo.

REM Verification Python
echo [1/6] Verification Python...
python --version > nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python non trouve. Installer Python 3.8+ depuis python.org
    pause
    exit /b 1
)
echo OK: Python trouve

REM Verification Git
echo [2/6] Verification Git...
git --version > nul 2>&1
if errorlevel 1 (
    echo ERREUR: Git non trouve. Installer Git depuis git-scm.com
    pause
    exit /b 1
)
echo OK: Git trouve

REM Creation environnement virtuel
echo [3/6] Creation environnement virtuel...
if not exist "venv" (
    python -m venv venv
    if errorlevel 1 (
        echo ERREUR: Impossible de creer l'environnement virtuel
        pause
        exit /b 1
    )
)
echo OK: Environnement virtuel pret

REM Activation et installation
echo [4/6] Installation des dependances...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip > nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo ERREUR: Installation des dependances echouee
    pause
    exit /b 1
)
echo OK: Dependances installees

REM Installation Playwright
echo [5/6] Installation navigateurs Playwright...
python -m playwright install > nul 2>&1
if errorlevel 1 (
    echo ATTENTION: Installation Playwright echouee (optionnel)
) else (
    echo OK: Playwright installe
)

REM Test
echo [6/6] Test de l'installation...
python -c "import fastapi, streamlit, pandas; print('Test reussi')" > nul 2>&1
if errorlevel 1 (
    echo ATTENTION: Certains modules peuvent manquer
) else (
    echo OK: Test reussi
)

echo.
echo ===============================================================================
echo                        INSTALLATION TERMINEE
echo ===============================================================================
echo.
echo PROCHAINES ETAPES:
echo 1. Ouvrir un nouveau terminal
echo 2. Activer: venv\Scripts\activate
echo 3. Lancer API: python llm_api_server.py
echo 4. Lancer Dashboard: streamlit run materials_dashboard.py
echo.
echo ACCES:
echo - Dashboard: http://localhost:8501
echo - API: http://localhost:8000
echo.
echo Appuyez sur une touche pour continuer...
pause > nul
