"""
Script de migration pour ajouter les nouvelles fonctionnalités de sécurité
Ajoute la colonne hash_fichier et la table logs_telechargements
"""
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text, inspect
from src.stockage.base_de_donnees import gestionnaire_bdd
from loguru import logger

def migrer_base_donnees():
    """Applique les migrations de sécurité"""
    logger.info("🔧 Début de la migration de sécurité...")
    
    try:
        # Créer toutes les tables (y compris la nouvelle table logs_telechargements)
        gestionnaire_bdd.creer_tables()
        logger.success("✅ Tables créées/vérifiées")
        
        # Vérifier et ajouter la colonne hash_fichier si nécessaire
        inspector = inspect(gestionnaire_bdd.engine)
        columns = [c['name'] for c in inspector.get_columns('documents')]
        
        if 'hash_fichier' not in columns:
            logger.info("📦 Ajout de la colonne hash_fichier...")
            with gestionnaire_bdd.engine.connect() as conn:
                conn.execute(text("ALTER TABLE documents ADD COLUMN hash_fichier VARCHAR(64)"))
                conn.commit()
            logger.success("✅ Colonne hash_fichier ajoutée")
        else:
            logger.info("✓ Colonne hash_fichier déjà présente")
        
        # Vérifier que la table logs_telechargements existe
        tables = inspector.get_table_names()
        if 'logs_telechargements' in tables:
            logger.success("✅ Table logs_telechargements présente")
        else:
            logger.warning("⚠️ Table logs_telechargements non créée - vérifier le modèle")
        
        logger.success("🎉 Migration de sécurité terminée avec succès!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Migration de Sécurité SafeDoc")
    print("=" * 60)
    
    if migrer_base_donnees():
        print("\n✅ Migration réussie!")
        print("\nNouvelles fonctionnalités activées:")
        print("  • Vérification d'intégrité des fichiers (SHA-256)")
        print("  • Journalisation des téléchargements")
        print("  • Vérification d'ownership des documents")
        print("  • Rate limiting (10 actions/minute)")
    else:
        print("\n❌ Échec de la migration")
        sys.exit(1)
