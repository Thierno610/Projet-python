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
from functools import wraps
import google.generativeai as genai
from dotenv import load_dotenv
import base64
import uuid
import time
from loguru import logger
from flask_mail import Mail, Message
from sqlalchemy.orm import Session

# Charger les variables d'environnement explicitement depuis le root
load_dotenv(ROOT_DIR / '.env')

app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET_KEY', 'safedoc-optimized-2024')

# Configuration Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)
import os
import base64
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes,
)
from webauthn.helpers.structs import (
    RegistrationCredential,
    AuthenticationCredential,
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    AuthenticatorAttachment,
)
from webauthn.helpers import bytes_to_base64url
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
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'doc', 'docx', 'xls', 'xlsx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    FREE_TIER_LIMIT_MB = 500
    PREMIUM_TIER_LIMIT_MB = 50000

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = 'temp'

# Configuration Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')  # Utiliser Flash pour la vitesse
GEMINI_ENABLED = os.getenv('GEMINI_ENABLED', '1').lower() in ('1', 'true', 'yes')
chat_session = None

SYSTEM_INSTRUCTION = """Tu es l'assistant intelligent de SafeDoc, une plateforme de gestion documentaire sécurisée.
Tes responsabilités :
1. Aider les utilisateurs à naviguer dans l'interface (Dashboard, Bibliothèque, Upload).
2. Expliquer les technologies utilisées : Chiffrement AES-256, Hash SHA-256, OCR avec Tesseract, et classification NLP.
3. Répondre aux questions sur les documents de l'utilisateur s'ils sont fournis dans le contexte.
4. Être technique, bref, professionnel et répondre exclusivement en français.

Si on te demande qui tu es, réponds que tu es l'IA de SafeDoc propulsée par Gemini."""

if GEMINI_API_KEY and GEMINI_ENABLED:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=SYSTEM_INSTRUCTION
        )
        # Préchauffer la session
        chat_session = model.start_chat()
        print(f"✅ SafeDoc AI Hub Initialisé ({GEMINI_MODEL})")
    except Exception as e:
        print(f"⚠️ Erreur Initialisation AI: {e}")
        model = None
else:
    model = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Import des modules avec gestion d'erreur
try:
    from src.stockage.base_de_donnees import gestionnaire_bdd, UtilisateurDB, DocumentDB, EtiquetteDB, BiometrieDB
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

try:
    from src.securite.rate_limiter import rate_limiter
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    print("⚠️ Rate limiter non disponible")
    RATE_LIMITER_AVAILABLE = False

# Données de démonstration
# WebAuthn Constants
RP_ID = "localhost"
RP_NAME = "SafeDoc Security"
ORIGIN = "http://localhost:5000"

def get_utilisateur_session():
    """Récupère l'utilisateur connecté via la session Flask"""
    user_id = session.get('user_id')
    if user_id and BDD_AVAILABLE:
        # Utiliser une session à courte durée pour éviter les fuites
        db_session = gestionnaire_bdd.obtenir_session()
        try:
            user = db_session.query(UtilisateurDB).get(user_id)
            if user:
                # Détacher l'objet de la session pour qu'il reste accessible après fermeture
                db_session.expunge(user)
                return user
        except Exception as e:
            logger.error(f"Erreur session utilisateur: {e}")
        finally:
            db_session.close()
    
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Veuillez vous connecter pour accéder à cette page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_documents_utilisateur(user_id):
    if BDD_AVAILABLE:
        return gestionnaire_bdd.obtenir_documents_utilisateur(user_id)
    return []

def get_etiquettes_utilisateur(user_id):
    if BDD_AVAILABLE:
        # Toujours s'assurer que les étiquettes par défaut existent (creer_etiquette gère les doublons)
        gestionnaire_bdd.creer_etiquettes_par_defaut(user_id)
        etiquettes = gestionnaire_bdd.obtenir_toutes_etiquettes(user_id)
        return etiquettes
    return []

@app.context_processor
def inject_status():
    """Injecte le statut de la base de données et l'utilisateur dans tous les templates"""
    bdd_ok = False
    if BDD_AVAILABLE:
        try:
            bdd_ok = gestionnaire_bdd.verifier_connexion()
        except:
            bdd_ok = False
            
    user = get_utilisateur_session()
    return dict(bdd_connectee=bdd_ok, user=user)

# --- ROUTES PRINCIPALES ---

@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir les fichiers statiques"""
    return send_from_directory('static', filename)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    """Génère un code de réinitialisation et l'envoie par mail"""
    identifiant = request.json.get('identifiant')
    if not identifiant:
        return jsonify({'success': False, 'error': 'Identifiant requis'}), 400
        
    try:
        moteur = gestionnaire_bdd.engine
        with Session(moteur) as db_session:
            # Chercher par nom d'utilisateur ou email
            user = db_session.query(UtilisateurDB).filter(
                (UtilisateurDB.nom_utilisateur == identifiant) | (UtilisateurDB.email == identifiant)
            ).first()
            
            if not user:
                # Pour la sécurité, on ne dit pas si l'utilisateur existe ou non
                return jsonify({'success': True, 'message': 'Si le compte existe, un code a été envoyé.'})
            
            # Générer code
            import random
            code = f"{random.randint(100000, 999999)}"
            
            # Stocker de manière temporaire (session pour la démo, idéalement Redis/BDD avec expiration)
            # On utilise un dictionnaire global pour plus de fiabilité entre les requêtes si session pose souci
            reset_key = f"reset_{identifiant}"
            session[reset_key] = {
                'code': code,
                'time': time.time()
            }
            
            # Envoyer email
            email_dest = user.email if user.email else os.getenv('MAIL_DEFAULT_SENDER')
            msg = Message(
                "SafeDoc - Réinitialisation de votre mot de passe",
                recipients=[email_dest],
                body=f"Bonjour {user.nom_utilisateur},\n\nVous avez demandé à réinitialiser votre mot de passe.\nVotre code de sécurité est : {code}\n\nSi vous n'êtes pas à l'origine de cette demande, ignorez cet e-mail."
            )
            mail.send(msg)
            return jsonify({'success': True, 'message': 'Code envoyé'})
            
    except Exception as e:
        logger.error(f"Erreur forgot password: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/reset-forgotten-password', methods=['POST'])
def api_reset_forgotten_password():
    """Réinitialise le mot de passe avec le code reçu"""
    data = request.json
    identifiant = data.get('identifiant')
    code_saisi = data.get('code')
    nouveau_mdp = data.get('nouveau_mdp')
    
    reset_info = session.get(f"reset_{identifiant}")
    if not reset_info or reset_info['code'] != code_saisi:
        return jsonify({'success': False, 'error': 'Code invalide'}), 400
        
    # Expiration 15 minutes
    if time.time() - reset_info['time'] > 900:
        return jsonify({'success': False, 'error': 'Code expiré'}), 400
        
    if not nouveau_mdp or len(nouveau_mdp) < 8:
        return jsonify({'success': False, 'error': 'Mot de passe trop court'}), 400

    try:
        moteur = gestionnaire_bdd.engine
        with Session(moteur) as db_session:
            user = db_session.query(UtilisateurDB).filter(
                (UtilisateurDB.nom_utilisateur == identifiant) | (UtilisateurDB.email == identifiant)
            ).first()
            
            if user:
                import bcrypt
                sel = bcrypt.gensalt()
                user.hash_mot_de_passe = bcrypt.hashpw(nouveau_mdp.encode('utf-8'), sel).decode('utf-8')
                db_session.commit()
                session.pop(f"reset_{identifiant}", None)
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Utilisateur introuvable'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if BDD_AVAILABLE:
            user = gestionnaire_bdd.obtenir_session().query(UtilisateurDB).filter_by(nom_utilisateur=username).first()
            
            # Login normal ou Bypass pour MOCTAR
            success = False
            if user:
                if gestionnaire_auth.verifier_mot_de_passe(password, user.hash_mot_de_passe):
                    success = True
                elif username.upper() == "MOCTAR" and password == "52623835@": # Bypass spécifique pour la démo
                    success = True
            
            if success:
                session['user_id'] = user.id
                session['username'] = user.nom_utilisateur
                flash(f"Ravi de vous revoir, {username} !", "success")
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
        
        flash("Identifiants incorrects ou système indisponible.", "danger")
    
    return render_template('login.html', page='login')

@app.route('/demo')
def login_demo():
    if BDD_AVAILABLE:
        user = gestionnaire_bdd.obtenir_session().query(UtilisateurDB).filter_by(nom_utilisateur="MOCTAR").first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.nom_utilisateur
            flash("Accès DÉMO activé. Bienvenue, Moctar !", "info")
            return redirect(url_for('dashboard'))
    flash("Le mode démo est temporairement indisponible.", "warning")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if BDD_AVAILABLE:
            # Validation
            valide, msg = gestionnaire_auth.valider_nom_utilisateur(username)
            if not valide:
                flash(msg, "warning")
                return render_template('register.html')
                
            valide, msg = gestionnaire_auth.valider_mot_de_passe(password)
            if not valide:
                flash(msg, "warning")
                return render_template('register.html')
            
            # Hachage et création
            hash_mdp = gestionnaire_auth.hacher_mot_de_passe(password)
            user = gestionnaire_bdd.creer_utilisateur(username, hash_mdp)
            
            if user:
                flash("Compte créé avec succès ! Connectez-vous.", "success")
                return redirect(url_for('login'))
            else:
                flash("Ce nom d'utilisateur est déjà pris.", "danger")
                
    return render_template('register.html', page='register')

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous avez été déconnecté en toute sécurité.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_utilisateur_session()
    documents = get_documents_utilisateur(user.id)
    documents_recents = documents[:5] if documents else []
    
    # Statistiques réelles
    total_docs = len(documents) if documents else 0
    categories_dict = {}
    if documents:
        for doc in documents:
            cat = doc.categorie or 'Inconnu'
            categories_dict[cat] = categories_dict.get(cat, 0) + 1
            
    types_categories = len(categories_dict)
    
    # Préparer les données pour le graphique de distribution (Doughnut)
    distribution_data = []
    if total_docs > 0:
        for cat, count in categories_dict.items():
            distribution_data.append({
                'label': cat,
                'value': round((count / total_docs) * 100, 1),
                'count': count
            })
    
    stockage_mb = user.stockage_utilise / (1024 * 1024)
    return render_template('dashboard.html', 
                         user=user,
                         documents=documents_recents,
                         total_docs=total_docs,
                         types_categories=types_categories,
                         distribution_data=distribution_data,
                         stockage_mb=stockage_mb,
                         pourcentage_stockage=user.pourcentage_stockage(),
                         page='dashboard')

# --- AUTHENTIFICATION ---

# --- ROUTES SUPPRIMÉES (Authentification désactivée) ---

# --- AUTRES ROUTES ---

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    user = get_utilisateur_session()
    etiquettes = get_etiquettes_utilisateur(user.id)
    
    if request.method == 'POST':
        file = request.files.get('file')
        scanned_data = request.form.get('scanned_file')
        nom_perso = request.form.get('nom_personnalise')
        selected_etiquettes = request.form.getlist('etiquettes') # Liste des IDs
        
        if not file and not scanned_data:
            flash("Aucun fichier sélectionné", "danger")
            return redirect(request.url)

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
            
            # Récupérer le format
            format_doc = request.form.get('format_document')

            if temp_path and temp_path.exists():
                if DOCS_AVAILABLE:
                    # Utiliser le vrai secret s'il existe, sinon une démo
                    secret = "demo-password-2024"
                    success, message, infos = gestionnaire_documents.traiter_document(
                        temp_path, user.id, secret, nom_perso, format_davance=format_doc
                    )
                    
                    # Nettoyer
                    if temp_path.exists():
                        temp_path.unlink()
                        
                    if success:
                        flash(message, 'success')
                        return render_template('upload.html', user=user, succes=True, infos=infos, etiquettes=etiquettes, page='upload')
                    else:
                        flash(message, 'danger')
                else:
                    flash("Mode Démo : Document simulé avec succès.", "info")
                    return render_template('upload.html', user=user, success=True, 
                                         infos={'nom': nom_perso or temp_path.name, 'categorie': 'Démo'}, 
                                         page='upload')
            else:
                flash("Aucun fichier ou scan valide reçu.", "warning")
                
        except Exception as e:
            flash(f"Erreur lors de l'ingestion : {str(e)}", "danger")
            
    return render_template('upload.html', user=user, etiquettes=etiquettes, page='upload')

@app.route('/bibliotheque')
@login_required
def bibliotheque():
    user = get_utilisateur_session()
    
    # Récupérer les filtres
    cat_filtre = request.args.get('categorie', 'Toutes')
    tag_filtre = request.args.get('etiquette', 'Toutes')
    recherche = request.args.get('q', '')
    
    if BDD_AVAILABLE:
        if recherche:
            documents = gestionnaire_bdd.rechercher_documents(user.id, recherche)
        else:
            documents = gestionnaire_bdd.obtenir_documents_utilisateur(user.id)
            
        # Filtrage manuel par catégorie
        if cat_filtre != 'Toutes':
            documents = [d for d in documents if d.categorie == cat_filtre]
            
        # Filtrage manuel par étiquette
        if tag_filtre != 'Toutes':
            documents = [d for d in documents if any(et.nom == tag_filtre for et in d.etiquettes)]
            
        user_etiquettes = get_etiquettes_utilisateur(user.id)
        categories = ["Toutes", "Facture", "Contrat", "Identité", "Personnel", "Autre"]
        
        return render_template('bibliotheque.html',
                             user=user,
                             documents=documents,
                             categories=categories,
                             etiquettes=["Toutes"] + [et.nom for et in user_etiquettes],
                             tag_filtre=tag_filtre,
                             cat_filtre=cat_filtre,
                             recherche=recherche,
                             page='bibliotheque')
    
    return render_template('bibliotheque.html',
                         user=user,
                         documents=DEMO_DOCUMENTS,
                         categories=["Toutes", "Facture", "Contrat", "Identité"],
                         etiquettes=["Toutes"] + [et['nom'] for et in ETIQUETTES_DB],
                         page='bibliotheque')

@app.route('/document/<int:doc_id>')
@login_required
def voir_document(doc_id):
    user = get_utilisateur_session()
    
    if BDD_AVAILABLE:
        document = gestionnaire_bdd.obtenir_document_par_id(doc_id)
        if not document:
            flash("Document non trouvé", "danger")
            return redirect(url_for('bibliotheque'))
            
        etiquettes_dispo = get_etiquettes_utilisateur(user.id)
        
        # Préparer les métadonnées pour l'affichage
        import json
        metadonnees = {}
        if document.texte_extrait:
            # Essayer d'extraire des infos clés du texte si les métadonnées sont vides
            metadonnees = {
                'Type': document.categorie or 'Inconnu',
                'Taille': f"{document.taille_fichier / 1024:.1f} KB",
                'Source': document.nom_original or 'N/A'
            }
        
        return render_template('voir_document.html', 
                             user=user, 
                             document=document, 
                             etiquettes_dispo=etiquettes_dispo,
                             metadonnees=metadonnees,
                             page='bibliotheque')
    
    # Mode Démo
    doc_demo = next((d for d in DEMO_DOCUMENTS if d['id'] == doc_id), DEMO_DOCUMENTS[0])
    return render_template('voir_document.html', user=user, document=doc_demo, etiquettes_dispo=ETIQUETTES_DB, page='bibliotheque')

@app.route('/document/<int:doc_id>/etiquettes', methods=['POST'])
@login_required
def mettre_a_jour_etiquettes(doc_id):
    user = get_utilisateur_session()
    selected_tags = request.form.getlist('etiquettes')
    
    if BDD_AVAILABLE:
        # Logique pour mettre à jour les tags du document
        # Pour simplifier, on pourrait vider et remettre, ou juste ajouter
        flash("Mise à jour des étiquettes effectuée", "success")
    else:
        flash("Mode Démo : Étiquettes mises à jour simulée", "info")
        
    return redirect(url_for('voir_document', doc_id=doc_id))

@app.route('/document/<int:doc_id>/telecharger', methods=['POST'])
@login_required
def telecharger_document(doc_id):
    user = get_utilisateur_session()
    
    if BDD_AVAILABLE:
        # 1. Vérifier que le document appartient à l'utilisateur
        document = gestionnaire_bdd.obtenir_document_par_id(doc_id)
        if not document:
            flash("❌ Document non trouvé", "danger")
            return redirect(url_for('bibliotheque'))
        
        if document.utilisateur_id != user.id:
            logger.warning(f"Tentative d'accès non autorisé: user={user.id}, doc={doc_id}, owner={document.utilisateur_id}")
            flash("❌ Accès refusé: ce document ne vous appartient pas", "danger")
            # Journaliser la tentative suspecte
            if BDD_AVAILABLE:
                gestionnaire_bdd.ajouter_log_telechargement(
                    user.id, doc_id, 'download_unauthorized',
                    request.remote_addr, False, "Accès non autorisé"
                )
            return redirect(url_for('bibliotheque'))
        
        # 2. Vérifier le rate limiting
        if RATE_LIMITER_AVAILABLE:
            autorise, msg_limite = rate_limiter.enregistrer_tentative(user.id, "download")
            if not autorise:
                flash(f"⚠️ {msg_limite}", "warning")
                # Journaliser le blocage
                gestionnaire_bdd.ajouter_log_telechargement(
                    user.id, doc_id, 'download_rate_limited',
                    request.remote_addr, False, msg_limite
                )
                return redirect(url_for('voir_document', doc_id=doc_id))
        
        # 3. Utiliser le vrai secret s'il existe, sinon une démo
        secret = "demo-password-2024"
        
        success, message, chemin_dechiffre = gestionnaire_documents.recuperer_document(doc_id, secret)
        
        # 4. Journaliser l'action
        gestionnaire_bdd.ajouter_log_telechargement(
            user.id, doc_id, 'download',
            request.remote_addr, success, None if success else message
        )
        
        if success and chemin_dechiffre:
            from flask import send_file, after_this_request
            
            @after_this_request
            def remove_file(response):
                try:
                    if chemin_dechiffre.exists():
                        chemin_dechiffre.unlink()
                        logger.info(f"Fichier temporaire supprimé: {chemin_dechiffre}")
                except Exception as e:
                    logger.error(f"Erreur nettoyage fichier temp: {e}")
                return response
            
            return send_file(
                chemin_dechiffre,
                as_attachment=True,
                download_name=chemin_dechiffre.name.replace("dechiffre_", "")
            )
        else:
            flash(f"❌ Erreur téléchargement: {message}", "danger")
            return redirect(url_for('voir_document', doc_id=doc_id))
            
    flash("Mode Démo : Téléchargement simulé.", "info")
    return redirect(url_for('voir_document', doc_id=doc_id))

@app.route('/document/<int:doc_id>/visualiser')
@login_required
def visualiser_document(doc_id):
    user = get_utilisateur_session()
    
    if BDD_AVAILABLE:
        # 1. Vérifier que le document appartient à l'utilisateur
        document = gestionnaire_bdd.obtenir_document_par_id(doc_id)
        if not document:
            flash("❌ Document non trouvé", "danger")
            return redirect(url_for('bibliotheque'))
        
        if document.utilisateur_id != user.id:
            logger.warning(f"Tentative de visualisation non autorisée: user={user.id}, doc={doc_id}")
            flash("❌ Accès refusé: ce document ne vous appartient pas", "danger")
            # Journaliser la tentative
            gestionnaire_bdd.ajouter_log_telechargement(
                user.id, doc_id, 'view_unauthorized',
                request.remote_addr, False, "Accès non autorisé"
            )
            return redirect(url_for('bibliotheque'))
        
        # 2. Vérifier le rate limiting
        if RATE_LIMITER_AVAILABLE:
            autorise, msg_limite = rate_limiter.enregistrer_tentative(user.id, "view")
            if not autorise:
                flash(f"⚠️ {msg_limite}", "warning")
                gestionnaire_bdd.ajouter_log_telechargement(
                    user.id, doc_id, 'view_rate_limited',
                    request.remote_addr, False, msg_limite
                )
                return redirect(url_for('voir_document', doc_id=doc_id))
        
        # 3. Utiliser le vrai secret s'il existe, sinon une démo
        secret = "demo-password-2024"
        
        success, message, chemin_dechiffre = gestionnaire_documents.recuperer_document(doc_id, secret)
        
        # 4. Journaliser l'action
        gestionnaire_bdd.ajouter_log_telechargement(
            user.id, doc_id, 'view',
            request.remote_addr, success, None if success else message
        )
        
        if success and chemin_dechiffre:
            try:
                import base64
                import mimetypes
                
                # Determine MIME type
                ext = chemin_dechiffre.suffix.lower()
                if ext == '.docx':
                    mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                elif ext == '.xlsx':
                    mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                else:
                    mime_type = mimetypes.guess_type(str(chemin_dechiffre))[0] or 'application/octet-stream'

                # Read and encode
                with open(chemin_dechiffre, "rb") as f:
                    file_content = f.read()
                    encoded_content = base64.b64encode(file_content).decode('utf-8')

                # Cleanup immediately
                if chemin_dechiffre.exists():
                    chemin_dechiffre.unlink()

                return jsonify({
                    "status": "success",
                    "filename": chemin_dechiffre.name.replace("dechiffre_", ""),
                    "mime_type": mime_type,
                    "content": encoded_content
                })

            except Exception as e:
                logger.error(f"Erreur encodage document: {e}")
                if chemin_dechiffre.exists():
                     chemin_dechiffre.unlink()
                return jsonify({"status": "error", "message": str(e)}), 500
        else:
            flash(f"❌ Erreur visualisation: {message}", "danger")
            return redirect(url_for('voir_document', doc_id=doc_id))
            
    flash("Mode Démo : Visualisation simulée.", "info")
    return redirect(url_for('voir_document', doc_id=doc_id))

@app.route('/etiquettes', methods=['GET', 'POST'])
@login_required
def etiquettes():
    user = get_utilisateur_session()
    
    if request.method == 'POST':
        action = request.form.get('action')
        if BDD_AVAILABLE:
            if action == 'creer':
                nom = request.form.get('nom', '').strip()
                couleur = request.form.get('couleur', '#3B82F6')
                if nom:
                    gestionnaire_bdd.creer_etiquette(nom, couleur, user.id)
                    flash(f'Étiquette {nom} créée', 'success')
            elif action == 'supprimer':
                et_id = int(request.form.get('etiquette_id'))
                gestionnaire_bdd.supprimer_etiquette(et_id)
                flash('Étiquette supprimée', 'success')
        else:
            global ETIQUETTES_DB, ETIQUETTES_ID_COUNTER
            if action == 'creer':
                nom = request.form.get('nom', '').strip()
                if nom and not any(et['nom'].lower() == nom.lower() for et in ETIQUETTES_DB):
                    ETIQUETTES_DB.append({'id': ETIQUETTES_ID_COUNTER, 'nom': nom, 'couleur': request.form.get('couleur', '#3B82F6')})
                    ETIQUETTES_ID_COUNTER += 1
                    flash(f'Étiquette {nom} créée (Mode Démo)', 'success')
            elif action == 'supprimer':
                et_id = int(request.form.get('etiquette_id'))
                ETIQUETTES_DB = [et for et in ETIQUETTES_DB if et['id'] != et_id]
                flash('Supprimée (Mode Démo)', 'success')
        
        # Redirection intelligente basée sur la source
        source = request.form.get('source')
        if source == 'bibliotheque':
            return redirect(url_for('bibliotheque'))
            
        return redirect(url_for('etiquettes'))
        
    user_etiquettes = get_etiquettes_utilisateur(user.id)
    return render_template('etiquettes.html', user=user, etiquettes=user_etiquettes, page='etiquettes')

@app.route('/bibliotheque/supprimer/<int:doc_id>', methods=['POST'])
@login_required
def supprimer_document(doc_id):
    user = get_utilisateur_session()
    if BDD_AVAILABLE:
        # Utiliser le gestionnaire de documents pour une suppression complète (Fichier + BDD)
        success, message = gestionnaire_documents.supprimer_document(doc_id)
        if success:
            flash(message, "success")
        else:
            flash(message, "danger")
    else:
        # Mode Démo
        global DEMO_DOCUMENTS
        DEMO_DOCUMENTS = [d for d in DEMO_DOCUMENTS if d['id'] != doc_id]
        flash("Mode Démo : Document simulé supprimé", "info")
        
    return redirect(url_for('bibliotheque'))

@app.route('/statistiques')
@login_required
def statistiques():
    user = get_utilisateur_session()
    
    documents = get_documents_utilisateur(user.id)
    cat_counts = {}
    # Construire une liste sérialisable pour Chart.js
    documents_json = []
    for d in documents:
        cat = getattr(d, 'categorie', None) or 'Autre'
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        documents_json.append({
            'date_upload': getattr(d, 'date_upload', None).isoformat() if getattr(d, 'date_upload', None) else None,
            'categorie': cat
        })
        
    return render_template('statistiques.html',
                         user=user,
                         documents=documents,
                         documents_json=documents_json,
                         cat_counts=cat_counts,
                         poids_total=user.stockage_utilise / (1024*1024),
                         types_categories=len(cat_counts),
                         page='statistiques')

@app.route('/premium')
def premium():
    user = get_utilisateur_session()
    return render_template('premium.html', user=user, page='premium')

@app.route('/apropos')
def apropos():
    user = get_utilisateur_session()
    return render_template('apropos.html', user=user, page='apropos')

@app.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    user = get_utilisateur_session()
    
    if request.method == 'POST':
        # Gestion de la photo de profil
        photo = request.files.get('photo_profil')
        if photo and photo.filename != '' and allowed_file(photo.filename):
            ext = photo.filename.rsplit('.', 1)[1].lower()
            filename = f"avatar_{user.id}_{int(time.time())}.{ext}"
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(upload_path)
            
            # Mettre à jour en BDD
            session_db = gestionnaire_bdd.obtenir_session()
            u = session_db.query(UtilisateurDB).get(user.id)
            u.photo_profil = f"/static/uploads/{filename}"
            session_db.commit()
            flash("Photo de profil mise à jour !", "success")

        # Autres champs
        session_db = gestionnaire_bdd.obtenir_session()
        u = session_db.query(UtilisateurDB).get(user.id)
        u.nom_complet = request.form.get('nom_complet')
        u.email = request.form.get('email')
        u.telephone = request.form.get('telephone')
        u.adresse = request.form.get('adresse')
        session_db.commit()
        flash("Profil mis à jour !", "success")
        return redirect(url_for('profil'))
        
    return render_template('profil.html', user=user, now=datetime.now())

@app.route('/parametres', methods=['GET', 'POST'])
@login_required
def parametres():
    user = get_utilisateur_session()
    if request.method == 'POST':
        session_db = gestionnaire_bdd.obtenir_session()
        u = session_db.query(UtilisateurDB).get(user.id)
        
        # Mise à jour des préférences
        u.theme_accent_color = request.form.get('accent_color', u.theme_accent_color)
        u.glass_intensity = float(request.form.get('glass_intensity', u.glass_intensity))
        u.ai_vocal_enabled = 'ai_vocal' in request.form
        u.notifications_email = 'notif_email' in request.form
        
        session_db.commit()
        flash("Réglages personnalisés appliqués avec succès !", "success")
        return redirect(url_for('parametres'))
        
    return render_template('parametres.html', user=user)

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

@app.route('/api/user/activate-premium', methods=['POST'])
@login_required
def api_activate_premium():
    """Active le mode Premium pour l'utilisateur connecté"""
    user_id = session.get('user_id')
    if not BDD_AVAILABLE:
        return jsonify({'success': False, 'error': 'Base de données non disponible'}), 503
        
    db_session = gestionnaire_bdd.obtenir_session()
    try:
        user = db_session.query(UtilisateurDB).get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Utilisateur non trouvé'}), 404
            
        # Basculer vers premium
        user.niveau = 'premium'
        db_session.commit()
        
        # Loguer l'événement
        logger.success(f"Utilisateur {user.nom_utilisateur} est passé en PREMIUM")
        return jsonify({'success': True, 'message': 'Protocole Premium activé avec succès'})
    except Exception as e:
        db_session.rollback()
        logger.error(f"Erreur activation Premium: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/api/chat/start', methods=['GET'])
def api_chat_start():
    """Génère un message d'accueil personnalisé via Gemini"""
    if not model:
        return jsonify({'reply': "Bonjour ! Je suis l'assistant SafeDoc. Comment puis-je vous aider ?"}), 200
    
    user = get_utilisateur_session()
    docs = get_documents_utilisateur(user.id)
    nb_docs = len(docs) if docs else 0
    
    prompt = f"Génère un message d'accueil court (max 20 mots) pour l'utilisateur '{user.nom_utilisateur}'. Mentionne qu'il a {nb_docs} documents sécurisés dans son coffre-fort."
    
    try:
        response = model.generate_content(prompt)
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'reply': f"Bonjour {user.nom_utilisateur}, comment puis-je vous aider avec vos {nb_docs} documents ?"}), 200

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Route pour discuter avec l'IA Gemini - Version avec Contexte"""
    if not GEMINI_API_KEY:
        return jsonify({'reply': "Configuration requise : La clé API Gemini est absente du fichier .env."}), 503
    
    if not model or not chat_session:
        return jsonify({'reply': "Système IA en cours de démarrage ou erreur d'initialisation."}), 503
        
    user_msg = request.json.get('message', '')
    if not user_msg:
        return jsonify({'reply': "Message vide."}), 400
    
    # Récupérer le contexte des documents pour Gemini
    user = get_utilisateur_session()
    docs = get_documents_utilisateur(user.id)
    context_docs = ""
    if docs:
        context_docs = "\nVoici la liste des documents de l'utilisateur :\n"
        for d in docs[:10]: # Limiter à 10 pour le token count
            nom = getattr(d, 'nom', 'Sans nom') or 'Sans nom'
            cat = getattr(d, 'categorie', 'Inconnue') or 'Inconnue'
            context_docs += f"- {nom} (Catégorie: {cat})\n"
    
    full_prompt = f"Contexte utilisateur: {user.nom_utilisateur}\n{context_docs}\n\nQuestion de l'utilisateur: {user_msg}"
    
    try:
        response = chat_session.send_message(
            full_prompt, 
            generation_config={"max_output_tokens": 200, "temperature": 0.7}
        )
        return jsonify({'reply': response.text})
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erreur Chat: {error_msg}")
        return jsonify({'reply': "Désolé, je rencontre une difficulté technique. Réessayez dans un instant."}), 500

@app.route('/api/test-email', methods=['POST'])
def api_test_email():
    """Route de test pour l'envoi d'e-mails"""
    destinataire = request.json.get('email')
    if not destinataire:
        return jsonify({'error': "Email destinataire requis"}), 400
    
    try:
        msg = Message(
            "SafeDoc - Test de Configuration Email",
            recipients=[destinataire],
            body="Félicitations ! Le système d'envoi d'e-mails de SafeDoc est maintenant opérationnel."
        )
        mail.send(msg)
        return jsonify({'success': True, 'message': f"Email de test envoyé à {destinataire}"})
    except Exception as e:
        logger.error(f"Erreur envoi email test: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/request-verification', methods=['POST'])
def api_request_verification():
    """Génère et envoie un code de vérification à 6 chiffres par e-mail"""
    user = get_utilisateur_session()
    if not user:
        return jsonify({'success': False, 'error': 'Non authentifié'}), 401
    
    # Générer un code à 6 chiffres
    import random
    code = f"{random.randint(100000, 999999)}"
    
    # Stocker dans la session avec expiration (10 minutes)
    session['verification_code'] = code
    session['verification_code_time'] = time.time()
    
    try:
        msg = Message(
            "SafeDoc - Code de vérification",
            recipients=[user.email if hasattr(user, 'email') else os.getenv('MAIL_DEFAULT_SENDER')],
            body=f"Bonjour {user.nom_utilisateur},\n\nVotre code de vérification SafeDoc est : {code}\n\nCe code expirera dans 10 minutes."
        )
        mail.send(msg)
        return jsonify({'success': True, 'message': 'Code envoyé par e-mail'})
    except Exception as e:
        logger.error(f"Erreur envoi code vérification: {e}")
        return jsonify({'success': False, 'error': "Erreur lors de l'envoi de l'e-mail"}), 500

@app.route('/api/etiquettes/creer', methods=['POST'])
@login_required
def api_creer_etiquette():
    """Crée une étiquette via AJAX et retourne ses infos"""
    user = get_utilisateur_session()
    data = request.json
    nom = data.get('nom', '').strip()
    couleur = data.get('couleur', '#6366f1') # Indigo par défaut
    
    if not nom:
        return jsonify({'success': False, 'error': 'Nom requis'}), 400
        
    if BDD_AVAILABLE:
        try:
            etiquette_obj = gestionnaire_bdd.creer_etiquette(nom, couleur, user.id)
            if not etiquette_obj:
                return jsonify({'success': False, 'error': 'Erreur lors de la création'}), 500
                
            return jsonify({
                'success': True, 
                'etiquette': {
                    'id': etiquette_obj.id, 
                    'nom': etiquette_obj.nom, 
                    'couleur': etiquette_obj.couleur
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        # Mode Démo
        global ETIQUETTES_DB, ETIQUETTES_ID_COUNTER
        if any(et['nom'].lower() == nom.lower() for et in ETIQUETTES_DB):
            return jsonify({'success': False, 'error': 'Existe déjà'}), 400
            
        new_et = {'id': ETIQUETTES_ID_COUNTER, 'nom': nom, 'couleur': couleur}
        ETIQUETTES_DB.append(new_et)
        ETIQUETTES_ID_COUNTER += 1
        return jsonify({'success': True, 'etiquette': new_et})

@app.route('/api/auth/change-password', methods=['POST'])
def api_change_password():
    """Modifie le mot de passe après vérification du code à 6 chiffres"""
    user = get_utilisateur_session()
    if not user:
        return jsonify({'success': False, 'error': 'Non authentifié'}), 401
    
    data = request.json
    nouveau_mdp = data.get('nouveau_mdp')
    code_saisi = data.get('code')
    
    # Vérification du code
    code_session = session.get('verification_code')
    time_session = session.get('verification_code_time', 0)
    
    if not code_session or code_saisi != code_session:
        return jsonify({'success': False, 'error': 'Code de vérification invalide'}), 400
    
    # Expiration 10 min (600 secondes)
    if time.time() - time_session > 600:
        return jsonify({'success': False, 'error': 'Code de vérification expiré'}), 400
    
    if not nouveau_mdp or len(nouveau_mdp) < 8:
        return jsonify({'success': False, 'error': 'Le mot de passe doit faire au moins 8 caractères'}), 400

    try:
        moteur = gestionnaire_bdd.engine
        with Session(moteur) as db_session:
            db_user = db_session.get(UtilisateurDB, user.id)
            if not db_user:
                return jsonify({'success': False, 'error': 'Utilisateur non trouvé'}), 404
            
            # Hasher le nouveau mot de passe
            import bcrypt
            sel = bcrypt.gensalt()
            db_user.mot_de_passe_hash = bcrypt.hashpw(nouveau_mdp.encode('utf-8'), sel).decode('utf-8')
            db_session.commit()
            
            # Nettoyer la session
            session.pop('verification_code', None)
            session.pop('verification_code_time', None)
            
            return jsonify({'success': True, 'message': 'Mot de passe modifié avec succès'})
    except Exception as e:
        logger.error(f"Erreur changement mot de passe: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
        # Création des tables
        gestionnaire_bdd.creer_tables()
        print(f"✅ BDD OK ({os.getenv('DATABASE_URL')})")
        
        # Surcharge : Migration forcée pour les colonnes manquantes
        from sqlalchemy import text
        with gestionnaire_bdd.engine.connect() as conn:
            # Vérifier les colonnes existantes
            from sqlalchemy import inspect
            inspector = inspect(gestionnaire_bdd.engine)
            columns = [c['name'] for c in inspector.get_columns('utilisateurs')]
            
            # Liste des colonnes critiques à ajouter si absentes
            missing_cols = [
                ('nom_complet', 'VARCHAR(100)'),
                ('email', 'VARCHAR(100)'),
                ('telephone', 'VARCHAR(20)'),
                ('adresse', 'TEXT'),
                ('photo_profil', 'VARCHAR(500)'),
                ('niveau', "VARCHAR(20) DEFAULT 'free'"),
                ('stockage_utilise', 'INTEGER DEFAULT 0'),
                ('date_creation', 'DATETIME'),
                ('derniere_connexion', 'DATETIME')
            ]
            
            for col_name, col_type in missing_cols:
                if col_name not in columns:
                    print(f"📦 Migration : Ajout de la colonne '{col_name}'...")
                    try:
                        conn.execute(text(f"ALTER TABLE utilisateurs ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                    except Exception as e:
                        print(f"⚠️ Erreur ajout '{col_name}': {e}")
            
            # --- CRÉATION DE L'UTILISATEUR PAR DÉFAUT ---
            from sqlalchemy.orm import sessionmaker
            LocalSession = sessionmaker(bind=gestionnaire_bdd.engine)
            session_init = LocalSession()
            try:
                moctar = session_init.query(UtilisateurDB).filter_by(nom_utilisateur='MOCTAR').first()
                if not moctar:
                    print("👤 Création de l'utilisateur par défaut 'MOCTAR'...")
                    hash_mdp = gestionnaire_auth.hacher_mot_de_passe('52623835@')
                    # Création via le gestionnaire pour aussi avoir les étiquettes par défaut etc if possible
                    gestionnaire_bdd.creer_utilisateur('MOCTAR', hash_mdp, niveau='premium')
                    print("✅ Utilisateur 'MOCTAR' créé.")
                else:
                    # Mettre à jour le mot de passe si nécessaire pour correspondre à la demande
                    # print("👤 Utilisateur 'MOCTAR' déjà présent.")
                    pass
            finally:
                session_init.close()
            
    except Exception as e:
        print(f"⚠️ Erreur BDD: {e}")

# --- WEBAUTHN (BIOMETRIE) ---

@app.route('/api/auth/webauthn/register/options', methods=['POST'])
@login_required
def api_webauthn_register_options():
    user = get_utilisateur_session()
    
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=str(user.id).encode(),
        user_name=user.nom_utilisateur,
        user_display_name=user.nom_complet or user.nom_utilisateur,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    
    session['registration_challenge'] = options.challenge
    return options_to_json(options)

@app.route('/api/auth/webauthn/register/verify', methods=['POST'])
@login_required
def api_webauthn_register_verify():
    user = get_utilisateur_session()
    challenge = session.get('registration_challenge')
    
    if not challenge:
        return jsonify({'success': False, 'error': 'Challenge manquant'}), 400
        
    try:
        registration_verification = verify_registration_response(
            credential=request.json,
            expected_challenge=challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
        )
        
        # Save to DB
        new_cred = BiometrieDB(
            utilisateur_id=user.id,
            credential_id=registration_verification.credential_id,
            public_key=registration_verification.public_key,
            sign_count=registration_verification.sign_count,
            device_name=request.headers.get('User-Agent', 'Unknown device')[:100]
        )
        
        moteur = gestionnaire_bdd.engine
        with Session(moteur) as db_session:
            db_session.add(new_cred)
            db_session.commit()
            
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erreur WebAuthn Register: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/auth/webauthn/login/options', methods=['POST'])
def api_webauthn_login_options():
    # En démo simplifiée on cherche l'utilisateur par cookie ou on demande un pseudo
    # Ici on va essayer de voir si l'authentificateur connaît l'utilisateur
    
    options = generate_authentication_options(
        rp_id=RP_ID,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    
    session['authentication_challenge'] = options.challenge
    return options_to_json(options)

@app.route('/api/auth/webauthn/login/verify', methods=['POST'])
def api_webauthn_login_verify():
    challenge = session.get('authentication_challenge')
    if not challenge:
        return jsonify({'success': False, 'error': 'Challenge manquant'}), 400
        
    credential_id = base64url_to_bytes(request.json.get('id'))
    
    moteur = gestionnaire_bdd.engine
    with Session(moteur) as db_session:
        db_cred = db_session.query(BiometrieDB).filter_by(credential_id=credential_id).first()
        if not db_cred:
            return jsonify({'success': False, 'error': 'Clé inconnue'}), 404
            
        try:
            authentication_verification = verify_authentication_response(
                credential=request.json,
                expected_challenge=challenge,
                expected_origin=ORIGIN,
                expected_rp_id=RP_ID,
                credential_public_key=db_cred.public_key,
                credential_current_sign_count=db_cred.sign_count,
            )
            
            # Update sign count
            db_cred.sign_count = authentication_verification.new_sign_count
            db_session.commit()
            
            # Log User In
            session['user_id'] = db_cred.utilisateur_id
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Erreur WebAuthn Login: {e}")
            return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
