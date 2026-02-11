
import sqlite3
import os
from pathlib import Path

def fix_database():
    db_path = Path('data/safedoc.db')
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    print(f"Opening database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # --- Fix table 'utilisateurs' ---
        cursor.execute("PRAGMA table_info(utilisateurs)")
        user_columns = [column[1] for column in cursor.fetchall()]
        
        missing_user_cols = [
            ('nom_complet', 'VARCHAR(100)'),
            ('email', 'VARCHAR(100)'),
            ('telephone', 'VARCHAR(20)'),
            ('adresse', 'TEXT'),
            ('photo_profil', 'VARCHAR(500)'),
            ('niveau', "VARCHAR(20) DEFAULT 'free'"),
            ('stockage_utilise', 'INTEGER DEFAULT 0'),
            ('date_creation', 'DATETIME'),
            ('derniere_connexion', 'DATETIME')
        ]
        
        for col_name, col_type in missing_user_cols:
            if col_name not in user_columns:
                print(f"Adding column '{col_name}' to 'utilisateurs' table...")
                cursor.execute(f"ALTER TABLE utilisateurs ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"Column '{col_name}' added successfully.")

        # --- Fix table 'etiquettes' ---
        cursor.execute("PRAGMA table_info(etiquettes)")
        tag_columns = [column[1] for column in cursor.fetchall()]
        
        if 'utilisateur_id' not in tag_columns:
            print("Adding column 'utilisateur_id' to 'etiquettes' table...")
            cursor.execute("ALTER TABLE etiquettes ADD COLUMN utilisateur_id INTEGER")
            conn.commit()
            print("Column 'utilisateur_id' added successfully.")
            
        print("=" * 50)
        print("Database schema synchronization complete!")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()
