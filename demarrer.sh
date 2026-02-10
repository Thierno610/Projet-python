#!/bin/bash
# Script de démarrage rapide pour SafeDoc (Linux/Mac)

echo ""
echo "============================================"
echo "  SafeDoc - Coffre-fort Numérique"
echo "============================================"
echo ""

echo "[INSTALLATION] Installation des dépendances en mode global..."
python3 -m pip install -r requirements.txt

echo "[INSTALLATION] Téléchargement du modèle NLP français..."
python3 -m spacy download fr_core_news_md

echo "[INSTALLATION] Téléchargement des données NLTK..."
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

echo ""
echo "[OK] Installation terminée!"
echo ""


# Vérifier si le fichier .env existe
if [ ! -f ".env" ]; then
    echo ""
    echo "[AVERTISSEMENT] Fichier .env non trouvé"
    echo "[ACTION] Copie de .env.example vers .env"
    cp .env.example .env
    echo ""
    echo "[IMPORTANT] Modifiez le fichier .env avec vos paramètres!"
    echo "Ouvrez .env et changez au minimum MASTER_KEY"
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
fi

# Lancer l'application
echo ""
echo "[LANCEMENT] Démarrage de SafeDoc..."
echo ""
echo ""
echo "  Ouverture automatique dans votre navigateur"
echo "  URL: http://localhost:8501"
echo ""
echo "  Appuyez sur Ctrl+C pour arrêter"
echo ""
echo "============================================"
echo ""

streamlit run src/web/app.py
