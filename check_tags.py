from src.stockage.base_de_donnees import GestionnaireBaseDeDonnees, EtiquetteDB, UtilisateurDB
import os

# Ensure the database path is correct
db_path = "data/safedoc.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

manager = GestionnaireBaseDeDonnees(f"sqlite:///{db_path}")
session = manager.obtenir_session()

print("--- Utilisateurs ---")
users = session.query(UtilisateurDB).all()
for u in users:
    print(f"ID: {u.id}, Username: {u.nom_utilisateur}")

print("\n--- Étiquettes ---")
tags = session.query(EtiquetteDB).all()
if not tags:
    print("Aucune étiquette trouvée dans la base de données.")
for t in tags:
    print(f"ID: {t.id}, Nom: {t.nom}, Couleur: {t.couleur}, UserID: {t.utilisateur_id}")

session.close()
