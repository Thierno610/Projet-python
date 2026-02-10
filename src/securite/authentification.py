"""
Module d'authentification SafeDoc
Gestion des utilisateurs, authentification et sessions
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Dict
import bcrypt
from loguru import logger

from config.config import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_REQUIRE_UPPERCASE,
    PASSWORD_REQUIRE_LOWERCASE,
    PASSWORD_REQUIRE_DIGIT,
    USERNAME_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_PATTERN,
)


class Utilisateur:
    """Classe représentant un utilisateur SafeDoc"""
    
    def __init__(
        self,
        id: int,
        nom_utilisateur: str,
        hash_mot_de_passe: str,
        niveau: str = 'free',
        stockage_utilise: int = 0,
        date_creation: datetime = None,
    ):
        self.id = id
        self.nom_utilisateur = nom_utilisateur
        self.hash_mot_de_passe = hash_mot_de_passe
        self.niveau = niveau  # 'free' ou 'premium'
        self.stockage_utilise = stockage_utilise  # en octets
        self.date_creation = date_creation or datetime.now()
    
    def est_premium(self) -> bool:
        """Vérifie si l'utilisateur est premium"""
        return self.niveau == 'premium'
    
    def obtenir_limite_stockage(self) -> int:
        """Retourne la limite de stockage en octets"""
        from config.config import USER_TIERS
        return USER_TIERS[self.niveau]['storage_limit_mb'] * 1024 * 1024
    
    def peut_uploader(self, taille_fichier: int) -> bool:
        """Vérifie si l'utilisateur peut uploader un fichier"""
        limite = self.obtenir_limite_stockage()
        return (self.stockage_utilise + taille_fichier) <= limite
    
    def pourcentage_stockage(self) -> float:
        """Retourne le pourcentage de stockage utilisé"""
        limite = self.obtenir_limite_stockage()
        return (self.stockage_utilise / limite) * 100 if limite > 0 else 0
    
    def to_dict(self) -> Dict:
        """Convertit l'utilisateur en dictionnaire"""
        return {
            'id': self.id,
            'nom_utilisateur': self.nom_utilisateur,
            'niveau': self.niveau,
            'stockage_utilise': self.stockage_utilise,
            'date_creation': self.date_creation.isoformat(),
        }


class GestionnaireAuthentification:
    """Gestionnaire d'authentification et de validation"""
    
    @staticmethod
    def hacher_mot_de_passe(mot_de_passe: str) -> str:
        """
        Hache un mot de passe avec bcrypt
        
        Args:
            mot_de_passe: Mot de passe en clair
            
        Returns:
            Hash du mot de passe
        """
        sel = bcrypt.gensalt()
        hash_mdp = bcrypt.hashpw(mot_de_passe.encode(), sel)
        return hash_mdp.decode()
    
    @staticmethod
    def verifier_mot_de_passe(mot_de_passe: str, hash_mdp: str) -> bool:
        """
        Vérifie si un mot de passe correspond à son hash
        
        Args:
            mot_de_passe: Mot de passe en clair
            hash_mdp: Hash du mot de passe
            
        Returns:
            True si le mot de passe est correct
        """
        try:
            return bcrypt.checkpw(mot_de_passe.encode(), hash_mdp.encode())
        except Exception as e:
            logger.error(f"Erreur vérification mot de passe: {e}")
            return False
    
    @staticmethod
    def valider_mot_de_passe(mot_de_passe: str) -> tuple[bool, str]:
        """
        Valide un mot de passe selon les critères de sécurité
        
        Args:
            mot_de_passe: Mot de passe à valider
            
        Returns:
            Tuple (valide, message d'erreur)
        """
        if len(mot_de_passe) < PASSWORD_MIN_LENGTH:
            return False, f"Le mot de passe doit contenir au moins {PASSWORD_MIN_LENGTH} caractères"
        
        if PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in mot_de_passe):
            return False, "Le mot de passe doit contenir au moins une majuscule"
        
        if PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in mot_de_passe):
            return False, "Le mot de passe doit contenir au moins une minuscule"
        
        if PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in mot_de_passe):
            return False, "Le mot de passe doit contenir au moins un chiffre"
        
        return True, ""
    
    @staticmethod
    def valider_nom_utilisateur(nom_utilisateur: str) -> tuple[bool, str]:
        """
        Valide un nom d'utilisateur
        
        Args:
            nom_utilisateur: Nom d'utilisateur à valider
            
        Returns:
            Tuple (valide, message d'erreur)
        """
        if len(nom_utilisateur) < USERNAME_MIN_LENGTH:
            return False, f"Le nom d'utilisateur doit contenir au moins {USERNAME_MIN_LENGTH} caractères"
        
        if len(nom_utilisateur) > USERNAME_MAX_LENGTH:
            return False, f"Le nom d'utilisateur ne doit pas dépasser {USERNAME_MAX_LENGTH} caractères"
        
        if not re.match(USERNAME_PATTERN, nom_utilisateur):
            return False, "Le nom d'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores"
        
        return True, ""


class GestionnaireSession:
    """Gestionnaire de sessions utilisateur (pour Streamlit)"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def creer_session(self, utilisateur: Utilisateur, duree_minutes: int = 60) -> str:
        """
        Crée une nouvelle session pour un utilisateur
        
        Args:
            utilisateur: Utilisateur connecté
            duree_minutes: Durée de validité de la session
            
        Returns:
            Token de session
        """
        import secrets
        token = secrets.token_urlsafe(32)
        
        expiration = datetime.now() + timedelta(minutes=duree_minutes)
        
        self.sessions[token] = {
            'utilisateur': utilisateur,
            'expiration': expiration,
            'derniere_activite': datetime.now(),
        }
        
        logger.info(f"Session créée pour {utilisateur.nom_utilisateur}")
        return token
    
    def obtenir_session(self, token: str) -> Optional[Utilisateur]:
        """
        Récupère l'utilisateur d'une session
        
        Args:
            token: Token de session
            
        Returns:
            Utilisateur ou None si session invalide/expirée
        """
        if token not in self.sessions:
            return None
        
        session = self.sessions[token]
        
        # Vérifier l'expiration
        if datetime.now() > session['expiration']:
            del self.sessions[token]
            logger.warning("Session expirée")
            return None
        
        # Mettre à jour la dernière activité
        session['derniere_activite'] = datetime.now()
        
        return session['utilisateur']
    
    def detruire_session(self, token: str):
        """Détruit une session"""
        if token in self.sessions:
            del self.sessions[token]
            logger.info("Session détruite")
    
    def nettoyer_sessions_expirees(self):
        """Nettoie les sessions expirées"""
        tokens_expires = [
            token for token, session in self.sessions.items()
            if datetime.now() > session['expiration']
        ]
        
        for token in tokens_expires:
            del self.sessions[token]
        
        if tokens_expires:
            logger.info(f"{len(tokens_expires)} sessions expirées nettoyées")


# Instance globale
gestionnaire_auth = GestionnaireAuthentification()
gestionnaire_session = GestionnaireSession()
