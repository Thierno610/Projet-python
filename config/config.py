"""
Configuration principale de SafeDoc
Charge les variables d'environnement et définit les constantes
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Répertoire racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# ===== BASE DE DONNÉES =====
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/data/safedoc.db')
DATABASE_PATH = BASE_DIR / 'data' / 'safedoc.db'

# ===== CHEMINS DE STOCKAGE =====
DOCUMENTS_PATH = BASE_DIR / os.getenv('DOCUMENTS_PATH', 'data/documents')
ENCRYPTED_PATH = BASE_DIR / os.getenv('ENCRYPTED_PATH', 'data/chiffres')
TEMP_PATH = BASE_DIR / os.getenv('TEMP_PATH', 'data/temp')
LOGS_PATH = BASE_DIR / 'logs'

# Créer les répertoires s'ils n'existent pas
for path in [DOCUMENTS_PATH, ENCRYPTED_PATH, TEMP_PATH, LOGS_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# ===== SÉCURITÉ =====
MASTER_KEY = os.getenv('MASTER_KEY', 'dev_key_change_in_production')
SESSION_SECRET_KEY = os.getenv('SESSION_SECRET_KEY', 'dev_session_key')
SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '60'))

# Paramètres de chiffrement
ENCRYPTION_ALGORITHM = 'AES-256-GCM'
KEY_DERIVATION_ITERATIONS = 100000
SALT_LENGTH = 32

# ===== OCR =====
TESSERACT_PATH = os.getenv('TESSERACT_PATH', 'tesseract')
OCR_LANGUAGE = os.getenv('OCR_LANGUAGE', 'fra')
OCR_CONFIDENCE_THRESHOLD = 60  # Seuil de confiance minimum (%)

# Prétraitement d'images pour OCR
IMAGE_PREPROCESSING = {
    'resize_factor': 2,  # Agrandir l'image
    'denoise': True,
    'threshold': True,
    'deskew': True,
}

# ===== NLP =====
SPACY_MODEL = 'fr_core_news_md'  # Modèle français moyen

# Catégories de documents
DOCUMENT_CATEGORIES = [
    'Facture',
    'Contrat',
    'Pièce d\'identité',
    'Document médical',
    'Document fiscal',
    'Document éducatif',
    'Document administratif',
    'Acte de naissance',
    'Relevé bancaire',
    'Assurance',
    'Diplôme',
    'Autre',
]

# Mots-clés pour classification automatique
CATEGORY_KEYWORDS = {
    'Facture': ['facture', 'invoice', 'montant', 'tva', 'total', 'paiement'],
    'Contrat': ['contrat', 'signé', 'partie', 'engagement', 'clause'],
    'Pièce d\'identité': ['identité', 'carte', 'passeport', 'permis', 'né(e) le'],
    'Document médical': ['médical', 'patient', 'docteur', 'ordonnance', 'diagnostic'],
    'Document fiscal': ['impôt', 'fiscal', 'taxe', 'déclaration', 'revenus'],
    'Document éducatif': ['école', 'université', 'diplôme', 'étudiant', 'note'],
    'Relevé bancaire': ['banque', 'compte', 'solde', 'transaction', 'virement'],
    'Assurance': ['assurance', 'police', 'prime', 'garantie', 'sinistre'],
}

# ===== STOCKAGE =====
# Limites de stockage (en MB)
FREE_TIER_LIMIT_MB = int(os.getenv('FREE_TIER_LIMIT_MB', '500'))
PREMIUM_TIER_LIMIT_MB = int(os.getenv('PREMIUM_TIER_LIMIT_MB', '50000'))

# Taille maximale de fichier uploadé
MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', '50'))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Extensions de fichiers autorisées
ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', 'pdf,png,jpg,jpeg,tiff,bmp').split(',')

# ===== GOOGLE DRIVE (PREMIUM) =====
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8501')
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/drive.file']

# ===== APPLICATION =====
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Configuration Streamlit
STREAMLIT_CONFIG = {
    'page_title': 'SafeDoc - Coffre-fort Numérique',
    'page_icon': '🔒',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded',
}

# ===== TIERS UTILISATEUR =====
USER_TIERS = {
    'free': {
        'name': 'Gratuit',
        'storage_limit_mb': FREE_TIER_LIMIT_MB,
        'cloud_sync': False,
        'max_documents': 1000,
    },
    'premium': {
        'name': 'Premium',
        'storage_limit_mb': PREMIUM_TIER_LIMIT_MB,
        'cloud_sync': True,
        'max_documents': -1,  # Illimité
    },
}

# ===== MESSAGES =====
MESSAGES = {
    'welcome': '🔒 Bienvenue sur SafeDoc - Votre coffre-fort numérique intelligent',
    'upload_success': '✅ Document téléversé et traité avec succès !',
    'encryption_success': '🔐 Document chiffré avec succès',
    'storage_limit': '⚠️ Limite de stockage atteinte. Passez à Premium pour plus d\'espace.',
    'invalid_file': '❌ Type de fichier non supporté',
    'file_too_large': '❌ Fichier trop volumineux',
}

# ===== JOURNALISATION =====
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
LOG_ROTATION = "10 MB"
LOG_RETENTION = "1 month"

# ===== VALIDATION =====
# Validation du mot de passe
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = False

# Validation du nom d'utilisateur
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 50
USERNAME_PATTERN = r'^[a-zA-Z0-9_-]+$'
