#!/usr/bin/env python3
"""
SafeDoc - Lanceur rapide et sans erreur
Version optimisée pour un démarrage instantané
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

# Configuration de l'environnement
os.environ['PYTHONPATH'] = str(Path(__file__).parent)
os.environ['FLASK_ENV'] = 'development'

def verifier_dependances():
    """Vérifie et installe les dépendances essentielles"""
    dependances_essentielles = [
        'flask',
        'loguru', 
        'python-dotenv',
        'bcrypt',
        'sqlalchemy',
        'pytesseract',
        'pillow',
        'pdf2image',
        'google-generativeai'
    ]
    
    manquantes = []
    for dep in dependances_essentielles:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            manquantes.append(dep)
    
    if manquantes:
        print("🔧 Installation des dépendances manquantes...")
        for dep in manquantes:
            os.system(f"pip install {dep}")
        print("✅ Dépendances installées")

def initialiser_config():
    """Crée les fichiers de configuration si nécessaires"""
    
    # Créer le fichier .env s'il n'existe pas
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        env_example = Path(__file__).parent / '.env.example'
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Fichier .env créé")
    
    # Créer les dossiers nécessaires
    dossiers = ['data', 'temp', 'logs']
    for dossier in dossiers:
        Path(dossier).mkdir(exist_ok=True)
    
    print("✅ Configuration initialisée")

def lancer_application():
    """Lance l'application Flask optimisée"""
    
    # Importer après vérification des dépendances
    try:
        from src.web.app_flask_optimized import app
        print("🚀 Lancement de SafeDoc...")
        print("=" * 50)
        print("🌐 URL: http://localhost:5000")
        print("🔒 SafeDoc - Coffre-fort Numérique Intelligent")
        print("=" * 50)
        print("⚠️  Mode développement - Ne pas utiliser en production")
        print("🛑 Appuyez sur Ctrl+C pour arrêter")
        print("=" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("🔄 Tentative avec la version simplifiée...")
        
        # Fallback vers la version simplifiée
        from src.web.app_flask_simple import app
        print("🚀 Lancement de SafeDoc (Mode Démonstration)...")
        print("=" * 50)
        print("🌐 URL: http://localhost:5000")
        print("🔒 SafeDoc - Coffre-fort Numérique Intelligent")
        print("=" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

if __name__ == '__main__':
    print("🔒 SafeDoc - Initialisation...")
    
    # Étape 1: Vérifier les dépendances
    verifier_dependances()
    
    # Étape 2: Initialiser la configuration
    initialiser_config()
    
    # Étape 3: Lancer l'application
    lancer_application()
