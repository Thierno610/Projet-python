
import sys
import os
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from src.stockage.base_de_donnees import gestionnaire_bdd
    from src.securite.authentification import gestionnaire_auth
    
    print("--- Test de Création d'Utilisateur ---")
    username = "TestUser"
    password = "Password123"
    
    # Check if exists
    user = gestionnaire_bdd.obtenir_utilisateur_par_nom(username)
    if user:
        print(f"L'utilisateur {username} existe déjà.")
    else:
        print(f"Création de l'utilisateur {username}...")
        hash_mdp = gestionnaire_auth.hacher_mot_de_passe(password)
        user = gestionnaire_bdd.creer_utilisateur(username, hash_mdp)
        if user:
            print(f"Utilisateur {user.nom_utilisateur} créé avec succès (ID: {user.id})")
        else:
            print("Échec de la création de l'utilisateur.")
            
    if user:
        print("\n--- Test de Vérification de Mot de Passe ---")
        # Get user again to ensure it's from DB
        user_db = gestionnaire_bdd.obtenir_utilisateur_par_nom(username)
        is_correct = gestionnaire_auth.verifier_mot_de_passe(password, user_db.hash_mot_de_passe)
        print(f"Vérification mot de passe correct: {is_correct}")
        
    print("\nTest terminé.")

except Exception as e:
    print(f"Erreur pendant le test: {e}")
    import traceback
    traceback.print_exc()
