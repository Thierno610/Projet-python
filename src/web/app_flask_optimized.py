"""
SafeDoc Flask Application - Version Optimisée & Corrigée
"""

import sys
from pathlib import Path
from datetime import datetime
import os

# Racine du projet
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify, send_from_directory
import google.generativeai as genai
from dotenv import load_dotenv
import base64
import uuid

# Charger les variables d'environnement explicitement depuis le root
load_dotenv(ROOT_DIR / '.env')

app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET_KEY', 'safedoc-optimized-2024')

# Configuration
try:
    from config.config import (
        MAX_UPLOAD_SIZE_BYTES, 
        ALLOWED_EXTENSIONS as CONFIG_ALLOWED,
        FREE_TIER_LIMIT_MB,
        PREMIUM_TIER_LIMIT_MB
    )
    ALLOWED_EXTENSIONS = set(CONFIG_ALLOWED)
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_BYTES
except ImportError:
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    FREE_TIER_LIMIT_MB = 500
    PREMIUM_TIER_LIMIT_MB = 50000

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = 'temp'

# Configuration Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
chat_session = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction="Tu es l'assistant SafeDoc ultra-rapide. Aide pour l'ingestion (PDF/Caméra), l'OCR, la sécurité AES-256 et la bibliothèque. Sois bref et technique. Réponds en français."
        )
        # Préchauffer la session
        chat_session = model.start_chat()
        print("✅ SafeDoc AI Hub Initialisé")
    except Exception as e:
        print(f"⚠️ Erreur Initialisation AI: {e}")
        model = None
else:
    model = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Import des modules avec gestion d'erreur
try:
    from src.stockage.base_de_donnees import gestionnaire_bdd
    BDD_AVAILABLE = True
except ImportError:
    print("⚠️ Base de données non disponible - Mode démonstration")
    BDD_AVAILABLE = False

try:
    from src.securite.authentification import gestionnaire_auth, Utilisateur
    AUTH_AVAILABLE = True
except ImportError:
    print("⚠️ Authentification non disponible - Mode démonstration")
    AUTH_AVAILABLE = False

try:
    from src.utils.gestionnaire_documents import gestionnaire_documents
    DOCS_AVAILABLE = True
except ImportError:
    print("⚠️ Gestionnaire de documents non disponible - Mode démonstration")
    DOCS_AVAILABLE = False

# Données de démonstration
DEMO_USER = {
    'id': 1,
    'nom_utilisateur': 'Utilisateur',
    'niveau': 'premium',
    'stockage_utilise': 1048576,
    'date_creation': datetime.now().isoformat()
}

DEMO_DOCUMENTS = [
    {
        'id': 1,
        'nom': 'facture_electricite.pdf',
        'categorie': 'Facture',
        'taille_fichier': 2048576,
        'date_upload': datetime.now(),
        'etiquettes': [{'nom': 'Urgent', 'couleur': '#FF4444'}]
    },
    {
        'id': 2,
        'nom': 'contrat_travail.pdf',
        'categorie': 'Contrat',
        'taille_fichier': 1024576,
        'date_upload': datetime.now(),
        'etiquettes': [{'nom': 'Important', 'couleur': '#4444FF'}]
    }
]

# Stockage des étiquettes en mémoire (pour la démo)
ETIQUETTES_DB = [
    {'id': 1, 'nom': 'Urgent', 'couleur': '#FF4444'},
    {'id': 2, 'nom': 'Important', 'couleur': '#4444FF'},
    {'id': 3, 'nom': 'Travail', 'couleur': '#44FF44'}
]
ETIQUETTES_ID_COUNTER = 4

class UtilisateurOptimized:
    def __init__(self, data):
        self.id = data['id']
        self.nom_utilisateur = data['nom_utilisateur']
        self.niveau = data['niveau']
        self.stockage_utilise = data.get('stockage_utilise', 0)
        self.date_creation = data.get('date_creation')
    
    def est_premium(self):
        return self.niveau == 'premium'
    
    def pourcentage_stockage(self):
        limite = self.obtenir_limite_stockage()
        return (self.stockage_utilise / limite) * 100 if limite > 0 else 0
    
    def obtenir_limite_stockage(self):
        limit_mb = PREMIUM_TIER_LIMIT_MB if self.est_premium() else FREE_TIER_LIMIT_MB
        return limit_mb * 1024 * 1024

def get_utilisateur_session():
    # Toujours retourner l'utilisateur de démonstration pour l'accès direct
    return UtilisateurOptimized(DEMO_USER)

def get_documents_utilisateur(user_id):
    if DOCS_AVAILABLE and BDD_AVAILABLE:
        try:
            return gestionnaire_bdd.obtenir_documents_utilisateur(user_id)
        except Exception as e:
            print(f"⚠️ Erreur documents: {e}")
            return DEMO_DOCUMENTS
    return DEMO_DOCUMENTS

# --- ROUTES PRINCIPALES ---

@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir les fichiers statiques"""
    return send_from_directory('static', filename)

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    user = get_utilisateur_session()
    documents = get_documents_utilisateur(user.id)
    documents_recents = documents[:5] if documents else []
    
    stockage_mb = user.stockage_utilise / (1024 * 1024)
    return render_template('dashboard.html', 
                         user=user,
                         documents=documents_recents,
                         stockage_mb=stockage_mb,
                         pourcentage_stockage=user.pourcentage_stockage(),
                         page='dashboard')

# --- AUTHENTIFICATION ---

# --- ROUTES SUPPRIMÉES (Authentification désactivée) ---

# --- AUTRES ROUTES ---

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    user = get_utilisateur_session()
    
    if request.method == 'POST':
        nom_personnalise = request.form.get('nom_personnalise')
        file = request.files.get('file')
        scanned_data = request.form.get('scanned_file')
        
        temp_path = None
        
        try:
            # Cas 1: Upload de fichier classique
            if file and file.filename != '' and allowed_file(file.filename):
                filename = f"upload_{uuid.uuid4().hex}_{file.filename}"
                temp_path = Path(app.config['UPLOAD_FOLDER']) / filename
                temp_path.parent.mkdir(exist_ok=True)
                file.save(str(temp_path))
                
            # Cas 2: Capture caméra (Base64)
            elif scanned_data and scanned_data.startswith('data:image'):
                header, encoded = scanned_data.split(",", 1)
                data = base64.b64decode(encoded)
                filename = f"scan_{uuid.uuid4().hex}.jpg"
                temp_path = Path(app.config['UPLOAD_FOLDER']) / filename
                temp_path.parent.mkdir(exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(data)
            
            if temp_path and temp_path.exists():
                if DOCS_AVAILABLE:
                    # Utiliser le vrai secret s'il existe, sinon une démo
                    secret = "demo-password-2024"
                    success, message, infos = gestionnaire_documents.traiter_document(
                        temp_path, user.id, secret, nom_personnalise
                    )
                    
                    # Nettoyer
                    if temp_path.exists():
                        temp_path.unlink()
                        
                    if success:
                        flash(message, 'success')
                        return render_template('upload.html', user=user, success=True, infos=infos, page='upload')
                    else:
                        flash(message, 'danger')
                else:
                    flash("Mode Démo : Document simulé avec succès.", "info")
                    return render_template('upload.html', user=user, success=True, 
                                         infos={'nom': nom_personnalise or temp_path.name, 'categorie': 'Démo'}, 
                                         page='upload')
            else:
                flash("Aucun fichier ou scan valide reçu.", "warning")
                
        except Exception as e:
            flash(f"Erreur lors de l'ingestion : {str(e)}", "danger")
            
    return render_template('upload.html', user=user, page='upload')

@app.route('/bibliotheque')
def bibliotheque():
    user = get_utilisateur_session()
    
    documents = get_documents_utilisateur(user.id)
    return render_template('bibliotheque.html',
                         user=user,
                         documents=documents,
                         categories=["Toutes", "Facture", "Contrat", "Identité"],
                         etiquettes=["Toutes"] + [et['nom'] for et in ETIQUETTES_DB],
                         page='bibliotheque')

@app.route('/etiquettes', methods=['GET', 'POST'])
def etiquettes():
    user = get_utilisateur_session()
    
    global ETIQUETTES_DB, ETIQUETTES_ID_COUNTER
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'creer':
            nom = request.form.get('nom', '').strip()
            if nom and not any(et['nom'].lower() == nom.lower() for et in ETIQUETTES_DB):
                ETIQUETTES_DB.append({'id': ETIQUETTES_ID_COUNTER, 'nom': nom, 'couleur': request.form.get('couleur', '#3B82F6')})
                ETIQUETTES_ID_COUNTER += 1
                flash(f'Étiquette {nom} créée', 'success')
        elif action == 'supprimer':
            et_id = int(request.form.get('etiquette_id'))
            ETIQUETTES_DB = [et for et in ETIQUETTES_DB if et['id'] != et_id]
            flash('Supprimée', 'success')
        return redirect(url_for('etiquettes'))
        
    return render_template('etiquettes.html', user=user, etiquettes=ETIQUETTES_DB, page='etiquettes')

@app.route('/statistiques')
def statistiques():
    user = get_utilisateur_session()
    
    documents = get_documents_utilisateur(user.id)
    cat_counts = {}
    for d in documents:
        cat = d.get('categorie', 'Autre')
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        
    return render_template('statistiques.html',
                         user=user,
                         documents=documents,
                         cat_counts=cat_counts,
                         poids_total=user.stockage_utilise / (1024*1024),
                         types_categories=len(cat_counts),
                         page='statistiques')

@app.route('/premium')
def premium():
    user = get_utilisateur_session()
    return render_template('premium.html', user=user, page='premium')

# --- API ---

@app.route('/api/user-data')
def api_user_data():
    """API pour récupérer les données utilisateur au format JSON"""
    user = get_utilisateur_session()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    data = {
        'id': user.id,
        'nom_utilisateur': user.nom_utilisateur,
        'niveau': user.niveau,
        'stockage_utilise': user.stockage_utilise,
        'stockage_limite': user.obtenir_limite_stockage(),
        'pourcentage': user.pourcentage_stockage(),
        'est_premium': user.est_premium()
    }
    return jsonify(data)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Route pour discuter avec l'IA Gemini - Version Optimisée"""
    if not GEMINI_API_KEY:
        return jsonify({'reply': "Configuration requise : La clé API Gemini est absente du fichier .env."}), 503
    
    if not model or not chat_session:
        return jsonify({'reply': "Système IA en cours de démarrage ou erreur d'initialisation. Réessayez dans quelques secondes."}), 503
        
    user_msg = request.json.get('message', '')
    if not user_msg:
        return jsonify({'reply': "Message vide."}), 400
        
    try:
        # Utilisation de la session pour la rapidité
        response = chat_session.send_message(user_msg, generation_config={"max_output_tokens": 300, "temperature": 0.7})
        return jsonify({'reply': response.text})
    except Exception as e:
        print(f"❌ Erreur Chat: {e}")
        return jsonify({'reply': "L'IA rencontre une difficulté technique temporaire."}), 500

@app.route('/api/statistiques')
def api_statistiques():
    """API pour récupérer les statistiques au format JSON"""
    user = get_utilisateur_session()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    documents = get_documents_utilisateur(user.id)
    
    stats = {
        'total_documents': len(documents),
        'stockage_utilise': user.stockage_utilise,
        'stockage_limite': user.obtenir_limite_stockage(),
        'pourcentage_stockage': user.pourcentage_stockage(),
        'est_premium': user.est_premium()
    }
    
    return jsonify(stats)

# Initialisation
if BDD_AVAILABLE:
    try:
        gestionnaire_bdd.creer_tables()
        print("✅ BDD OK")
    except Exception as e:
        print(f"⚠️ Erreur BDD: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
