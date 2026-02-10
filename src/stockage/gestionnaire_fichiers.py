"""
Module de gestion des fichiers SafeDoc
Gestion du stockage local des documents
"""
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from loguru import logger

from config.config import (
    DOCUMENTS_PATH,
    ENCRYPTED_PATH,
    TEMP_PATH,
    MAX_UPLOAD_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
)


class GestionnaireFichiers:
    """Gestionnaire de fichiers locaux"""
    
    def __init__(self):
        self.documents_path = DOCUMENTS_PATH
        self.encrypted_path = ENCRYPTED_PATH
        self.temp_path = TEMP_PATH
        
        # Créer les répertoires si nécessaire
        for path in [self.documents_path, self.encrypted_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def valider_fichier(self, fichier_path: Path) -> Tuple[bool, str]:
        """
        Valide un fichier avant upload
        
        Args:
            fichier_path: Chemin du fichier
            
        Returns:
            Tuple (valide, message d'erreur)
        """
        # Vérifier l'existence
        if not fichier_path.exists():
            return False, "Le fichier n'existe pas"
        
        # Vérifier l'extension
        extension = fichier_path.suffix.lstrip('.').lower()
        if extension not in ALLOWED_EXTENSIONS:
            return False, f"Format de fichier non supporté. Formats acceptés: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Vérifier la taille
        taille = fichier_path.stat().st_size
        if taille > MAX_UPLOAD_SIZE_BYTES:
            taille_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
            return False, f"Fichier trop volumineux (max {taille_mb}MB)"
        
        if taille == 0:
            return False, "Le fichier est vide"
        
        return True, ""
    
    def generer_nom_unique(self, nom_original: str, utilisateur_id: int) -> str:
        """
        Génère un nom de fichier unique
        
        Args:
            nom_original: Nom du fichier original
            utilisateur_id: ID de l'utilisateur
            
        Returns:
            Nom unique
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nom_base = Path(nom_original).stem
        extension = Path(nom_original).suffix
        
        # Nettoyer le nom de base
        nom_base = "".join(c for c in nom_base if c.isalnum() or c in (' ', '-', '_'))
        nom_base = nom_base.replace(' ', '_')
        
        nom_unique = f"user{utilisateur_id}_{timestamp}_{nom_base}{extension}"
        return nom_unique
    
    def sauvegarder_fichier_temporaire(
        self,
        fichier_source: Path,
        nom_fichier: str
    ) -> Path:
        """
        Sauvegarde un fichier dans le dossier temporaire
        
        Args:
            fichier_source: Chemin du fichier source
            nom_fichier: Nom du fichier de destination
            
        Returns:
            Chemin du fichier temporaire
        """
        chemin_temp = self.temp_path / nom_fichier
        shutil.copy2(fichier_source, chemin_temp)
        logger.debug(f"Fichier copié vers temp: {chemin_temp}")
        return chemin_temp
    
    def sauvegarder_document(
        self,
        fichier_source: Path,
        utilisateur_id: int,
        nom_original: str
    ) -> Tuple[Path, str]:
        """
        Sauvegarde un document dans le dossier documents
        
        Args:
            fichier_source: Chemin du fichier source
            utilisateur_id: ID de l'utilisateur
            nom_original: Nom original du fichier
            
        Returns:
            Tuple (chemin du document, nom unique)
        """
        # Générer un nom unique
        nom_unique = self.generer_nom_unique(nom_original, utilisateur_id)
        
        # Créer le sous-dossier utilisateur
        dossier_utilisateur = self.documents_path / f"user_{utilisateur_id}"
        dossier_utilisateur.mkdir(exist_ok=True)
        
        # Copier le fichier
        chemin_document = dossier_utilisateur / nom_unique
        shutil.copy2(fichier_source, chemin_document)
        
        logger.info(f"Document sauvegardé: {chemin_document}")
        return chemin_document, nom_unique
    
    def sauvegarder_fichier_chiffre(
        self,
        fichier_chiffre: Path,
        utilisateur_id: int,
        nom_document: str
    ) -> Path:
        """
        Sauvegarde un fichier chiffré dans le dossier chiffrés
        
        Args:
            fichier_chiffre: Chemin du fichier chiffré
            utilisateur_id: ID de l'utilisateur
            nom_document: Nom du document
            
        Returns:
            Chemin du fichier chiffré
        """
        # Créer le sous-dossier utilisateur
        dossier_utilisateur = self.encrypted_path / f"user_{utilisateur_id}"
        dossier_utilisateur.mkdir(exist_ok=True)
        
        # Nom du fichier chiffré
        nom_chiffre = f"{Path(nom_document).stem}.enc"
        chemin_chiffre = dossier_utilisateur / nom_chiffre
        
        # Copier ou déplacer le fichier
        if fichier_chiffre != chemin_chiffre:
            shutil.move(str(fichier_chiffre), str(chemin_chiffre))
        
        logger.info(f"Fichier chiffré sauvegardé: {chemin_chiffre}")
        return chemin_chiffre
    
    def obtenir_document(self, chemin: Path) -> Optional[Path]:
        """
        Récupère un document
        
        Args:
            chemin: Chemin du document
            
        Returns:
            Chemin si existe, None sinon
        """
        if chemin.exists():
            return chemin
        logger.warning(f"Document non trouvé: {chemin}")
        return None
    
    def supprimer_fichier(self, chemin: Path) -> bool:
        """
        Supprime un fichier
        
        Args:
            chemin: Chemin du fichier
            
        Returns:
            True si supprimé avec succès
        """
        try:
            if chemin.exists():
                chemin.unlink()
                logger.info(f"Fichier supprimé: {chemin}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur suppression fichier: {e}")
            return False
    
    def supprimer_document(
        self,
        chemin_original: Path,
        chemin_chiffre: Path
    ) -> bool:
        """
        Supprime un document (original et chiffré)
        
        Args:
            chemin_original: Chemin du document original
            chemin_chiffre: Chemin du document chiffré
            
        Returns:
            True si supprimé avec succès
        """
        succes = True
        
        if chemin_original.exists():
            succes &= self.supprimer_fichier(chemin_original)
        
        if chemin_chiffre.exists():
            succes &= self.supprimer_fichier(chemin_chiffre)
        
        return succes
    
    def nettoyer_temporaires(self) -> int:
        """
        Nettoie les fichiers temporaires
        
        Returns:
            Nombre de fichiers supprimés
        """
        count = 0
        for fichier in self.temp_path.iterdir():
            if fichier.is_file():
                try:
                    fichier.unlink()
                    count += 1
                except Exception as e:
                    logger.error(f"Erreur suppression temp: {e}")
        
        if count > 0:
            logger.info(f"{count} fichiers temporaires nettoyés")
        
        return count
    
    def obtenir_taille_stockage_utilisateur(self, utilisateur_id: int) -> int:
        """
        Calcule la taille totale du stockage utilisateur
        
        Args:
            utilisateur_id: ID de l'utilisateur
            
        Returns:
            Taille totale en octets
        """
        taille_totale = 0
        
        # Documents
        dossier_docs = self.documents_path / f"user_{utilisateur_id}"
        if dossier_docs.exists():
            for fichier in dossier_docs.rglob('*'):
                if fichier.is_file():
                    taille_totale += fichier.stat().st_size
        
        # Fichiers chiffrés
        dossier_chiffres = self.encrypted_path / f"user_{utilisateur_id}"
        if dossier_chiffres.exists():
            for fichier in dossier_chiffres.rglob('*'):
                if fichier.is_file():
                    taille_totale += fichier.stat().st_size
        
        return taille_totale


# Instance globale
gestionnaire_fichiers = GestionnaireFichiers()
