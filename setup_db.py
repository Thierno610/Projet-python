
import sys
import os
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from src.stockage.base_de_donnees import gestionnaire_bdd, Base
from loguru import logger

def initialize_safedoc_db():
    print("🔒 SafeDoc - Initialisation de la Base de Données")
    print("=" * 50)
    
    # S'assurer que le dossier data existe
    data_dir = ROOT_DIR / 'data'
    data_dir.mkdir(exist_ok=True)
    
    try:
        # Création des tables
        print("🛠️  Création des tables SQLAlchemy...")
        gestionnaire_bdd.creer_tables()
        print("✅ Tables créées avec succès.")
        
        # Vérification des colonnes (Migration rapide si nécessaire)
        from sqlalchemy import create_engine, inspect
        inspector = inspect(gestionnaire_bdd.engine)
        columns = [c['name'] for c in inspector.get_columns('etiquettes')]
        
        if 'utilisateur_id' not in columns:
            print("📦 Migration : Ajout de la colonne 'utilisateur_id' à 'etiquettes'...")
            with gestionnaire_bdd.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("ALTER TABLE etiquettes ADD COLUMN utilisateur_id INTEGER"))
                conn.commit()
            print("✅ Migration terminée.")
            
        print("=" * 50)
        print("🎉 Base de données SafeDoc prête à l'emploi !")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")
        sys.exit(1)

if __name__ == "__main__":
    initialize_safedoc_db()
