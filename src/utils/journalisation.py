"""
Module de journalisation SafeDoc
Configuration centralisée des logs
"""
import sys
from pathlib import Path
from loguru import logger

from config.config import LOGS_PATH, LOG_FORMAT, LOG_ROTATION, LOG_RETENTION, LOG_LEVEL, DEBUG


def configurer_logs():
    """Configure le système de journalisation"""
    
    # Retirer le handler par défaut
    logger.remove()
    
    # Console - toujours actif en mode DEBUG
    if DEBUG:
        logger.add(
            sys.stderr,
            format=LOG_FORMAT,
            level=LOG_LEVEL,
            colorize=True,
        )
    else:
        # En production, seulement les warnings et erreurs dans la console
        logger.add(
            sys.stderr,
            format="{time:HH:mm:ss} | {level: <8} | {message}",
            level="WARNING",
            colorize=True,
        )
    
    # Fichier de log général
    logger.add(
        LOGS_PATH / "safedoc.log",
        format=LOG_FORMAT,
        level="DEBUG",
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression="zip",
        encoding="utf-8",
    )
    
    # Fichier de log pour les erreurs uniquement
    logger.add(
        LOGS_PATH / "erreurs.log",
        format=LOG_FORMAT,
        level="ERROR",
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression="zip",
        encoding="utf-8",
    )
    
    logger.success("Système de journalisation configuré")


# Configurer automatiquement au chargement du module
configurer_logs()
