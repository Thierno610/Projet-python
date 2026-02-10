"""
Module de gestion des documents SafeDoc
Orchestre l'upload, le traitement et le stockage des documents
"""
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from loguru import logger

from src.ocr.scanner import scanner_ocr
from src.nlp.extracteur import extracteur_nlp
from src.nlp.classificateur import classificateur
from src.securite.chiffrement import chiffreur
from src.stockage.base_de_donnees import gestionnaire_bdd
from src.stockage.gestionnaire_fichiers import gestionnaire_fichiers
from config.config import TEMP_PATH


class GestionnaireDocuments:
    """Gestionnaire principal des documents"""
    
    def __init__(self):
        """Initialise le gestionnaire"""
        self.scanner = scanner_ocr
        self.extracteur = extracteur_nlp
        self.classificateur = classificateur
        self.chiffreur = chiffreur
        self.bdd = gestionnaire_bdd
        self.fichiers = gestionnaire_fichiers
    
    def traiter_document(
        self,
        chemin_fichier: Path,
        utilisateur_id: int,
        mot_de_passe: str,
        nom_personnalise: str = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Traite un document complet: OCR, extraction, classification, chiffrement, stockage
        
        Args:
            chemin_fichier: Chemin du fichier à traiter
            utilisateur_id: ID de l'utilisateur
            mot_de_passe: Mot de passe pour le chiffrement
            nom_personnalise: Nom personnalisé (optionnel)
            
        Returns:
            Tuple (succès, message, infos_document)
        """
        logger.info(f"Traitement du document: {chemin_fichier.name}")
        
        try:
            # 1. Validation du fichier
            valide, msg_erreur = self.fichiers.valider_fichier(chemin_fichier)
            if not valide:
                return False, msg_erreur, None
            
            # 2. Vérifier le quota utilisateur
            taille_fichier = chemin_fichier.stat().st_size
            utilisateur = self.bdd.obtenir_utilisateur_par_id(utilisateur_id)
            
            if not utilisateur:
                return False, "Utilisateur non trouvé", None
            
            from src.securite.authentification import Utilisateur
            user_obj = Utilisateur(
                id=utilisateur.id,
                nom_utilisateur=utilisateur.nom_utilisateur,
                hash_mot_de_passe=utilisateur.hash_mot_de_passe,
                niveau=utilisateur.niveau,
                stockage_utilise=utilisateur.stockage_utilise
            )
            
            if not user_obj.peut_uploader(taille_fichier):
                return False, f"Quota de stockage dépassé. Passez à Premium pour plus d'espace.", None
            
            # 3. OCR - Extraction du texte
            logger.info("Étape 1/5: Extraction OCR...")
            texte_extrait, confiance_ocr = self.scanner.scanner_document(chemin_fichier)
            
            if not texte_extrait:
                logger.warning("Aucun texte extrait - traitement limité")
            
            # 4. Classification automatique
            logger.info("Étape 2/5: Classification automatique...")
            nom_fichier = nom_personnalise or chemin_fichier.name
            categorie, confiance_cat = self.classificateur.predire_categorie(texte_extrait, nom_fichier)
            
            # 5. Extraction d'informations
            logger.info("Étape 3/5: Extraction d'informations...")
            infos_extraites = self.extracteur.extraire_infos_cles(texte_extrait, categorie)
            
            # 6. Sauvegarde du document original (temporaire)
            logger.info("Étape 4/5: Chiffrement...")
            chemin_temp_doc, nom_unique = self.fichiers.sauvegarder_document(
                chemin_fichier,
                utilisateur_id,
                nom_fichier
            )
            
            # 7. Chiffrement
            chemin_temp_chiffre = TEMP_PATH / f"{nom_unique}.enc"
            self.chiffreur.chiffrer_fichier(chemin_temp_doc, chemin_temp_chiffre, mot_de_passe)
            
            # 8. Sauvegarde du fichier chiffré
            chemin_chiffre_final = self.fichiers.sauvegarder_fichier_chiffre(
                chemin_temp_chiffre,
                utilisateur_id,
                nom_unique
            )
            
            # 9. Enregistrer dans la base de données
            logger.info("Étape 5/5: Enregistrement en base de données...")
            document = self.bdd.ajouter_document(
                utilisateur_id=utilisateur_id,
                nom=nom_fichier,
                nom_original=chemin_fichier.name,
                chemin_original=str(chemin_temp_doc),
                chemin_chiffre=str(chemin_chiffre_final),
                taille_fichier=taille_fichier,
                type_fichier=chemin_fichier.suffix.lstrip('.'),
                categorie=categorie,
                texte_extrait=texte_extrait[:5000] if texte_extrait else None,  # Limiter la taille
                confiance_ocr=confiance_ocr
            )
            
            if not document:
                return False, "Erreur lors de l'enregistrement en base de données", None
            
            # 10. Nettoyer le fichier temporaire chiffré
            chemin_temp_chiffre.unlink(missing_ok=True)
            
            # Préparer les informations du document
            infos_document = {
                'id': document.id,
                'nom': document.nom,
                'categorie': categorie,
                'confiance_categorie': confiance_cat,
                'confiance_ocr': confiance_ocr,
                'taille': taille_fichier,
                'texte_extrait': texte_extrait[:500] if texte_extrait else '',  # Aperçu
                'infos_extraites': infos_extraites,
            }
            
            logger.success(f"Document traité avec succès (ID: {document.id})")
            return True, f"Document '{nom_fichier}' traité et sécurisé avec succès !", infos_document
            
        except Exception as e:
            logger.error(f"Erreur traitement document: {e}", exc_info=True)
            return False, f"Erreur: {str(e)}", None
    
    def recuperer_document(
        self,
        document_id: int,
        mot_de_passe: str
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Récupère et déchiffre un document
        
        Args:
            document_id: ID du document
            mot_de_passe: Mot de passe pour le déchiffrement
            
        Returns:
            Tuple (succès, message, chemin_fichier_dechiffre)
        """
        logger.info(f"Récupération du document ID: {document_id}")
        
        try:
            # Récupérer depuis la BDD
            session = self.bdd.obtenir_session()
            try:
                from src.stockage.base_de_donnees import DocumentDB
                document = session.query(DocumentDB).filter_by(id=document_id).first()
                
                if not document:
                    return False, "Document non trouvé", None
                
                chemin_chiffre = Path(document.chemin_chiffre)
                
                if not chemin_chiffre.exists():
                    return False, "Fichier chiffré introuvable", None
                
                # Déchiffrer dans le dossier temporaire
                nom_dechiffre = f"dechiffre_{document.nom_original}"
                chemin_dechiffre = TEMP_PATH / nom_dechiffre
                
                self.chiffreur.dechiffrer_fichier(chemin_chiffre, chemin_dechiffre, mot_de_passe)
                
                logger.success(f"Document déchiffré: {chemin_dechiffre}")
                return True, "Document déchiffré avec succès", chemin_dechiffre
                
            finally:
                session.close()
                
        except ValueError as e:
            logger.error(f"Erreur déchiffrement: {e}")
            return False, "Mot de passe incorrect ou fichier corrompu", None
        except Exception as e:
            logger.error(f"Erreur récupération document: {e}", exc_info=True)
            return False, f"Erreur: {str(e)}", None


# Instance globale
gestionnaire_documents = GestionnaireDocuments()
