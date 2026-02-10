@echo off
REM Script de démarrage rapide pour SafeDoc (Windows)
echo.
echo ============================================
echo   SafeDoc - Coffre-fort Numerique
echo ============================================
echo.

REM Vérifier si l'environnement virtuel existe
echo [INSTALLATION] Installation des dependances en mode global...
py -m pip install -r requirements.txt

echo [INSTALLATION] Telechargement du modele NLP francais...
py -m spacy download fr_core_news_md

echo [INSTALLATION] Telechargement des donnees NLTK...
py -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

echo.
echo [OK] Installation terminee!
echo.


REM Vérifier si le fichier .env existe
if not exist ".env" (
    echo.
    echo [AVERTISSEMENT] Fichier .env non trouve
    echo [ACTION] Copie de .env.example vers .env
    copy .env.example .env
    echo.
    echo [IMPORTANT] Modifiez le fichier .env avec vos parametres!
    echo Ouvrez .env et changez au minimum MASTER_KEY
    echo.
    pause
)

REM Lancer l'application
echo.
echo [LANCEMENT] Demarrage de SafeDoc...
echo.
echo.
echo  Ouverture automatique dans votre navigateur
echo  URL: http://localhost:8501
echo.
echo  Appuyez sur Ctrl+C pour arreter
echo.
echo ============================================
echo.

py -m streamlit run src\web\app.py

pause
