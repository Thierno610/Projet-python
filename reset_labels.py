from src.stockage.base_de_donnees import GestionnaireBaseDeDonnees, EtiquetteDB, UtilisateurDB
import os

# Ensure the database path is correct
db_path = "data/safedoc.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

manager = GestionnaireBaseDeDonnees(f"sqlite:///{db_path}")
session = manager.obtenir_session()

# Find MOCTAR user
moctar = session.query(UtilisateurDB).filter_by(nom_utilisateur="MOCTAR").first()

if moctar:
    print(f"Alignement des étiquettes pour {moctar.nom_utilisateur}...")
    
    # Delete existing labels for this user
    # Note: cascading delete might handle document associations, but let's be safe
    existing_tags = session.query(EtiquetteDB).filter_by(utilisateur_id=moctar.id).all()
    for tag in existing_tags:
        session.delete(tag)
    
    session.commit()
    print("Anciennes étiquettes supprimées.")
    
    # Re-create defaults using the updated method logic
    # We can't call the method directly easily because it's part of the class instance we just created
    # but let's just use the manager instance
    manager.creer_etiquettes_par_defaut(moctar.id)
    print("Nouvelles étiquettes par défaut créées : Important, Urgent, Personnel, Note.")
else:
    print("Utilisateur MOCTAR non trouvé.")

session.close()
