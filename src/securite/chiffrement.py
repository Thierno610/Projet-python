"""
Module de chiffrement SafeDoc
Implémentation du chiffrement AES-256-GCM pour sécuriser les documents
"""
import os
import base64
from pathlib import Path
from typing import Tuple, Optional
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from loguru import logger

from config.config import KEY_DERIVATION_ITERATIONS, SALT_LENGTH


class ChiffrementAES:
    """Gestionnaire de chiffrement AES-256-GCM"""
    
    def __init__(self):
        self.key_size = 32  # 256 bits
        self.nonce_size = 12  # 96 bits pour GCM
    
    def generer_cle_depuis_mot_de_passe(self, mot_de_passe: str, sel: bytes = None) -> Tuple[bytes, bytes]:
        """
        Génère une clé de chiffrement à partir d'un mot de passe
        
        Args:
            mot_de_passe: Mot de passe utilisateur
            sel: Sel optionnel (généré si non fourni)
            
        Returns:
            Tuple (clé, sel)
        """
        if sel is None:
            sel = os.urandom(SALT_LENGTH)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_size,
            salt=sel,
            iterations=KEY_DERIVATION_ITERATIONS,
            backend=default_backend()
        )
        
        cle = kdf.derive(mot_de_passe.encode())
        logger.debug(f"Clé générée depuis mot de passe (sel: {len(sel)} octets)")
        
        return cle, sel
    
    def generer_cle_aleatoire(self) -> bytes:
        """
        Génère une clé de chiffrement aléatoire
        
        Returns:
            Clé de 256 bits
        """
        cle = AESGCM.generate_key(bit_length=256)
        logger.debug("Clé aléatoire générée")
        return cle
    
    def chiffrer_donnees(self, donnees: bytes, cle: bytes) -> Tuple[bytes, bytes]:
        """
        Chiffre des données avec AES-256-GCM
        
        Args:
            donnees: Données à chiffrer
            cle: Clé de chiffrement (32 octets)
            
        Returns:
            Tuple (données chiffrées, nonce)
        """
        aesgcm = AESGCM(cle)
        nonce = os.urandom(self.nonce_size)
        
        donnees_chiffrees = aesgcm.encrypt(nonce, donnees, None)
        logger.debug(f"Données chiffrées: {len(donnees)} -> {len(donnees_chiffrees)} octets")
        
        return donnees_chiffrees, nonce
    
    def dechiffrer_donnees(self, donnees_chiffrees: bytes, cle: bytes, nonce: bytes) -> bytes:
        """
        Déchiffre des données avec AES-256-GCM
        
        Args:
            donnees_chiffrees: Données à déchiffrer
            cle: Clé de chiffrement (32 octets)
            nonce: Nonce utilisé lors du chiffrement
            
        Returns:
            Données déchiffrées
            
        Raises:
            InvalidTag: Si la clé est incorrecte ou les données corrompues
        """
        aesgcm = AESGCM(cle)
        
        try:
            donnees = aesgcm.decrypt(nonce, donnees_chiffrees, None)
            logger.debug(f"Données déchiffrées: {len(donnees_chiffrees)} -> {len(donnees)} octets")
            return donnees
        except Exception as e:
            logger.error(f"Erreur de déchiffrement: {e}")
            raise ValueError("Déchiffrement échoué - clé incorrecte ou données corrompues")
    
    def chiffrer_fichier(
        self, 
        chemin_source: Path, 
        chemin_destination: Path, 
        mot_de_passe: str
    ) -> Tuple[Path, bytes]:
        """
        Chiffre un fichier complet
        
        Args:
            chemin_source: Chemin du fichier à chiffrer
            chemin_destination: Chemin du fichier chiffré
            mot_de_passe: Mot de passe pour générer la clé
            
        Returns:
            Tuple (chemin fichier chiffré, sel)
        """
        logger.info(f"Chiffrement du fichier: {chemin_source}")
        
        # Lire le fichier source
        with open(chemin_source, 'rb') as f:
            donnees = f.read()
        
        # Générer la clé
        cle, sel = self.generer_cle_depuis_mot_de_passe(mot_de_passe)
        
        # Chiffrer
        donnees_chiffrees, nonce = self.chiffrer_donnees(donnees, cle)
        
        # Créer le répertoire de destination si nécessaire
        chemin_destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Écrire le fichier chiffré avec le format:
        # [sel (32 octets)][nonce (12 octets)][données chiffrées]
        with open(chemin_destination, 'wb') as f:
            f.write(sel)
            f.write(nonce)
            f.write(donnees_chiffrees)
        
        logger.success(f"Fichier chiffré: {chemin_destination}")
        return chemin_destination, sel
    
    def dechiffrer_fichier(
        self, 
        chemin_chiffre: Path, 
        chemin_destination: Path, 
        mot_de_passe: str
    ) -> Path:
        """
        Déchiffre un fichier complet
        
        Args:
            chemin_chiffre: Chemin du fichier chiffré
            chemin_destination: Chemin du fichier déchiffré
            mot_de_passe: Mot de passe pour générer la clé
            
        Returns:
            Chemin du fichier déchiffré
            
        Raises:
            ValueError: Si le déchiffrement échoue
        """
        logger.info(f"Déchiffrement du fichier: {chemin_chiffre}")
        
        # Lire le fichier chiffré
        with open(chemin_chiffre, 'rb') as f:
            sel = f.read(SALT_LENGTH)
            nonce = f.read(self.nonce_size)
            donnees_chiffrees = f.read()
        
        # Régénérer la clé avec le sel
        cle, _ = self.generer_cle_depuis_mot_de_passe(mot_de_passe, sel)
        
        # Déchiffrer
        donnees = self.dechiffrer_donnees(donnees_chiffrees, cle, nonce)
        
        # Créer le répertoire de destination si nécessaire
        chemin_destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Écrire le fichier déchiffré
        with open(chemin_destination, 'wb') as f:
            f.write(donnees)
        
        logger.success(f"Fichier déchiffré: {chemin_destination}")
        return chemin_destination
    
    def chiffrer_texte(self, texte: str, mot_de_passe: str) -> str:
        """
        Chiffre du texte et retourne une chaîne encodée en base64
        
        Args:
            texte: Texte à chiffrer
            mot_de_passe: Mot de passe
            
        Returns:
            Texte chiffré encodé en base64 (format: sel:nonce:données)
        """
        # Générer la clé
        cle, sel = self.generer_cle_depuis_mot_de_passe(mot_de_passe)
        
        # Chiffrer
        donnees_chiffrees, nonce = self.chiffrer_donnees(texte.encode(), cle)
        
        # Encoder en base64
        sel_b64 = base64.b64encode(sel).decode()
        nonce_b64 = base64.b64encode(nonce).decode()
        donnees_b64 = base64.b64encode(donnees_chiffrees).decode()
        
        return f"{sel_b64}:{nonce_b64}:{donnees_b64}"
    
    def dechiffrer_texte(self, texte_chiffre: str, mot_de_passe: str) -> str:
        """
        Déchiffre du texte encodé en base64
        
        Args:
            texte_chiffre: Texte chiffré (format: sel:nonce:données)
            mot_de_passe: Mot de passe
            
        Returns:
            Texte déchiffré
        """
        # Décoder depuis base64
        sel_b64, nonce_b64, donnees_b64 = texte_chiffre.split(':')
        
        sel = base64.b64decode(sel_b64)
        nonce = base64.b64decode(nonce_b64)
        donnees_chiffrees = base64.b64decode(donnees_b64)
        
        # Régénérer la clé
        cle, _ = self.generer_cle_depuis_mot_de_passe(mot_de_passe, sel)
        
        # Déchiffrer
        donnees = self.dechiffrer_donnees(donnees_chiffrees, cle, nonce)
        
        return donnees.decode()


# Instance globale
chiffreur = ChiffrementAES()
