import sqlite3
import os

db_path = "data/safedoc.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define columns to add
    columns_to_add = [
        ("photo_profil", "VARCHAR(500)"),
        ("niveau", "VARCHAR(20) DEFAULT 'free'"),
        ("stockage_utilise", "INTEGER DEFAULT 0"),
        ("theme_accent_color", "VARCHAR(10) DEFAULT '#6366f1'"),
        ("glass_intensity", "FLOAT DEFAULT 16.0"),
        ("ai_vocal_enabled", "BOOLEAN DEFAULT 0"),
        ("notifications_email", "BOOLEAN DEFAULT 1"),
        ("date_creation", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("derniere_connexion", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ]

    # Get existing columns
    cursor.execute("PRAGMA table_info(utilisateurs)")
    existing_columns = [col[1] for col in cursor.fetchall()]

    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            print(f"Adding column {col_name} to table utilisateurs...")
            try:
                cursor.execute(f"ALTER TABLE utilisateurs ADD COLUMN {col_name} {col_type}")
                print(f"Successfully added {col_name}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
