"""
Point d'entrée principal de SafeDoc
Initialisation et lancement de l'application
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from src.utils.journalisation import configurer_logs
from src.stockage.base_de_donnees import gestionnaire_bdd


def initialiser_application():
    """Initialise l'application SafeDoc"""
    logger.info("=" * 60)
    logger.info("🔒 SAFEDOC - Coffre-fort Numérique Intelligent")
    logger.info("=" * 60)
    
    # Créer les tables de base de données
    logger.info("Initialisation de la base de données...")
    gestionnaire_bdd.creer_tables()
    
    logger.success("✅ Application initialisée")
    logger.info("")


def lancer_interface_web():
    """Lance l'interface web Flask"""
    logger.info("Lancement de l'interface web Flask...")
    logger.info("URL: http://localhost:5000")
    logger.info("Appuyez sur Ctrl+C pour arrêter")
    
    from src.web.app_flask import app
    app.run(debug=True, host='0.0.0.0', port=5000)


def main():
    """Fonction principale"""
    initialiser_application()
    
    # Afficher le menu
    print("\n" + "=" *  60)
    print("🔒 SAFEDOC - Coffre-fort Numérique Intelligent")
    print("=" * 60)
    print("\nChoisissez une option :")
    print("1. Lancer l'interface Web (Flask)")
    print("2. Quitter")
    print()
    
    choix = input("Votre choix (1-2) : ").strip()
    
    if choix == "1":
        lancer_interface_web()
    else:
        print("\n👋 Au revoir !")
        logger.info("Application fermée")


if __name__ == "__main__":
    main()
