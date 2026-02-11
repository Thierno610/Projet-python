"""
Module de limitation de taux (Rate Limiting) pour SafeDoc
Protège contre les attaques par force brute et les abus
"""
from datetime import datetime, timedelta
from typing import Dict, Tuple
from collections import defaultdict
from loguru import logger


class RateLimiter:
    """Gestionnaire de limitation de taux pour les téléchargements"""
    
    def __init__(
        self,
        max_tentatives: int = 10,
        fenetre_minutes: int = 1,
        blocage_minutes: int = 15
    ):
        """
        Initialise le rate limiter
        
        Args:
            max_tentatives: Nombre maximum de tentatives dans la fenêtre
            fenetre_minutes: Durée de la fenêtre en minutes
            blocage_minutes: Durée du blocage en cas de dépassement
        """
        self.max_tentatives = max_tentatives
        self.fenetre = timedelta(minutes=fenetre_minutes)
        self.duree_blocage = timedelta(minutes=blocage_minutes)
        
        # Stockage: {user_id: [(timestamp, action), ...]}
        self.tentatives: Dict[int, list] = defaultdict(list)
        
        # Stockage des blocages: {user_id: timestamp_fin_blocage}
        self.blocages: Dict[int, datetime] = {}
    
    def est_bloque(self, user_id: int) -> Tuple[bool, str]:
        """
        Vérifie si un utilisateur est bloqué
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Tuple (est_bloqué, message)
        """
        if user_id in self.blocages:
            fin_blocage = self.blocages[user_id]
            if datetime.now() < fin_blocage:
                temps_restant = (fin_blocage - datetime.now()).seconds // 60
                return True, f"Trop de tentatives. Réessayez dans {temps_restant} minutes."
            else:
                # Blocage expiré, nettoyer
                del self.blocages[user_id]
                self.tentatives[user_id] = []
        
        return False, ""
    
    def enregistrer_tentative(self, user_id: int, action: str = "download") -> Tuple[bool, str]:
        """
        Enregistre une tentative et vérifie les limites
        
        Args:
            user_id: ID de l'utilisateur
            action: Type d'action (download, decrypt, etc.)
            
        Returns:
            Tuple (autorisé, message)
        """
        # Vérifier si déjà bloqué
        bloque, msg = self.est_bloque(user_id)
        if bloque:
            return False, msg
        
        maintenant = datetime.now()
        
        # Nettoyer les anciennes tentatives (hors fenêtre)
        debut_fenetre = maintenant - self.fenetre
        self.tentatives[user_id] = [
            (ts, act) for ts, act in self.tentatives[user_id]
            if ts > debut_fenetre
        ]
        
        # Ajouter la nouvelle tentative
        self.tentatives[user_id].append((maintenant, action))
        
        # Vérifier si la limite est dépassée
        nb_tentatives = len(self.tentatives[user_id])
        
        if nb_tentatives > self.max_tentatives:
            # Bloquer l'utilisateur
            self.blocages[user_id] = maintenant + self.duree_blocage
            logger.warning(
                f"Utilisateur {user_id} bloqué pour {self.duree_blocage.seconds // 60} minutes "
                f"({nb_tentatives} tentatives en {self.fenetre.seconds // 60} minute(s))"
            )
            return False, f"Trop de tentatives. Bloqué pour {self.duree_blocage.seconds // 60} minutes."
        
        # Avertir si proche de la limite
        if nb_tentatives > self.max_tentatives * 0.7:
            restantes = self.max_tentatives - nb_tentatives
            logger.info(f"Utilisateur {user_id}: {restantes} tentatives restantes")
        
        return True, ""
    
    def reinitialiser_utilisateur(self, user_id: int):
        """Réinitialise les compteurs pour un utilisateur"""
        if user_id in self.tentatives:
            del self.tentatives[user_id]
        if user_id in self.blocages:
            del self.blocages[user_id]
        logger.info(f"Rate limiter réinitialisé pour utilisateur {user_id}")
    
    def nettoyer_anciens(self):
        """Nettoie les anciennes entrées pour libérer la mémoire"""
        maintenant = datetime.now()
        
        # Nettoyer les blocages expirés
        blocages_expires = [
            uid for uid, fin in self.blocages.items()
            if maintenant > fin
        ]
        for uid in blocages_expires:
            del self.blocages[uid]
        
        # Nettoyer les tentatives hors fenêtre
        debut_fenetre = maintenant - self.fenetre
        for user_id in list(self.tentatives.keys()):
            self.tentatives[user_id] = [
                (ts, act) for ts, act in self.tentatives[user_id]
                if ts > debut_fenetre
            ]
            # Supprimer si vide
            if not self.tentatives[user_id]:
                del self.tentatives[user_id]
        
        if blocages_expires:
            logger.info(f"Nettoyage: {len(blocages_expires)} blocages expirés supprimés")


# Instance globale
rate_limiter = RateLimiter(
    max_tentatives=10,      # 10 téléchargements max
    fenetre_minutes=1,      # par minute
    blocage_minutes=15      # blocage de 15 minutes si dépassé
)
