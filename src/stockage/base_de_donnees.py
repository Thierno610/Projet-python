"""
Module de base de données SafeDoc
Modèles SQLAlchemy pour utilisateurs, documents et étiquettes
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Table, Text, Float, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session, joinedload
from loguru import logger

from config.config import DATABASE_URL, FREE_TIER_LIMIT_MB, PREMIUM_TIER_LIMIT_MB

Base = declarative_base()

# Table d'association pour la relation many-to-many entre documents et étiquettes
association_document_etiquette = Table(
    'document_etiquette',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id')),
    Column('etiquette_id', Integer, ForeignKey('etiquettes.id'))
)


class UtilisateurDB(Base):
    """Modèle Utilisateur pour la base de données"""
    __tablename__ = 'utilisateurs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nom_utilisateur = Column(String(50), unique=True, nullable=False, index=True)
    hash_mot_de_passe = Column(String(255), nullable=False)
    
    # Profil
    nom_complet = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    telephone = Column(String(20), nullable=True)
    adresse = Column(Text, nullable=True)
    photo_profil = Column(String(500), nullable=True)
    
    niveau = Column(String(20), default='free')  # 'free' ou 'premium'
    stockage_utilise = Column(Integer, default=0)  # en octets
    
    # Paramètres de Personnalisation
    theme_accent_color = Column(String(10), default='#6366f1') # Indigo par défaut
    glass_intensity = Column(Float, default=16.0) # Intensité du blur en px
    ai_vocal_enabled = Column(Boolean, default=False)
    notifications_email = Column(Boolean, default=True)
    
    date_creation = Column(DateTime, default=datetime.now)
    derniere_connexion = Column(DateTime, default=datetime.now)
    
    # Relations
    documents = relationship('DocumentDB', back_populates='utilisateur', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Utilisateur(id={self.id}, nom='{self.nom_utilisateur}', niveau='{self.niveau}')>"

    def est_premium(self) -> bool:
        """Vérifie si l'utilisateur est premium"""
        return self.niveau == 'premium'
    
    def obtenir_limite_stockage(self) -> int:
        """Retourne la limite de stockage en octets"""
        limit_mb = PREMIUM_TIER_LIMIT_MB if self.est_premium() else FREE_TIER_LIMIT_MB
        return limit_mb * 1024 * 1024
    
    def pourcentage_stockage(self) -> float:
        """Retourne le pourcentage d'utilisation du stockage (0-100)"""
        limite = self.obtenir_limite_stockage()
        if limite <= 0:
            return 0
        return min(100, (self.stockage_utilise / limite) * 100)


class DocumentDB(Base):
    """Modèle Document pour la base de données"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(255), nullable=False)
    nom_original = Column(String(255), nullable=False)
    categorie = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    
    # Chemins de fichiers
    chemin_original = Column(String(500), nullable=False)  # Fichier original (non chiffré temporaire)
    chemin_chiffre = Column(String(500), nullable=False)  # Fichier chiffré
    
    # Métadonnées
    taille_fichier = Column(Integer, nullable=False)  # en octets
    type_fichier = Column(String(50), nullable=False)  # pdf, jpg, png, etc.
    texte_extrait = Column(Text, nullable=True)  # Texte OCR
    confiance_ocr = Column(Float, nullable=True)  # Confiance OCR (0-100)
    hash_fichier = Column(String(64), nullable=True)  # SHA-256 pour vérification d'intégrité
    
    # Dates
    date_upload = Column(DateTime, default=datetime.now)
    date_modification = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relations
    utilisateur_id = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    utilisateur = relationship('UtilisateurDB', back_populates='documents')
    etiquettes = relationship('EtiquetteDB', secondary=association_document_etiquette, back_populates='documents')
    
    def __repr__(self):
        return f"<Document(id={self.id}, nom='{self.nom}', categorie='{self.categorie}')>"


class EtiquetteDB(Base):
    """Modèle Étiquette pour organiser les documents"""
    __tablename__ = 'etiquettes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(100), nullable=False, index=True)
    couleur = Column(String(7), default='#3B82F6')  # Couleur hex
    utilisateur_id = Column(Integer, ForeignKey('utilisateurs.id'), nullable=True) # Null = global ou système
    
    # Relations
    documents = relationship('DocumentDB', secondary=association_document_etiquette, back_populates='etiquettes')
    
    def __repr__(self):
        return f"<Etiquette(id={self.id}, nom='{self.nom}')>"


class LogTelechargementDB(Base):
    """Modèle pour journaliser les téléchargements et accès aux documents"""
    __tablename__ = 'logs_telechargements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    action = Column(String(50), nullable=False)  # 'download', 'view', 'decrypt_failed'
    adresse_ip = Column(String(45), nullable=True)  # IPv4 ou IPv6
    succes = Column(Boolean, default=True)
    message_erreur = Column(Text, nullable=True)
    date_action = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<LogTelechargement(user={self.utilisateur_id}, doc={self.document_id}, action='{self.action}')>"


class BiometrieDB(Base):
    """Stocke les clés publiques WebAuthn pour la biométrie"""
    __tablename__ = 'biometrie_creds'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    
    credential_id = Column(LargeBinary, unique=True, nullable=False)
    public_key = Column(LargeBinary, nullable=False)
    sign_count = Column(Integer, default=0)
    device_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    utilisateur = relationship('UtilisateurDB', backref='biometrie')
    
    def __repr__(self):
        return f"<BiometrieDB(user={self.utilisateur_id}, device='{self.device_name}')>"


class GestionnaireBaseDeDonnees:
    """Gestionnaire de base de données SafeDoc"""
    
    def __init__(self, url_bdd: str = DATABASE_URL):
        """
        Initialise la connexion à la base de données
        
        Args:
            url_bdd: URL de connexion à la base de données
        """
        self.engine = create_engine(url_bdd, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Connexion à la base de données: {url_bdd}")
    
    def creer_tables(self):
        """Crée toutes les tables de la base de données"""
        Base.metadata.create_all(self.engine)
        logger.success("Tables de base de données créées")
    
    def obtenir_session(self) -> Session:
        """
        Obtient une nouvelle session de base de données
        
        Returns:
            Session SQLAlchemy
        """
        return self.SessionLocal()
    
    def verifier_connexion(self) -> bool:
        """Vérifie si la connexion à la base de données est active"""
        try:
            with self.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Échec de la vérification de connexion BDD: {e}")
            return False
    
    def creer_utilisateur(
        self,
        nom_utilisateur: str,
        hash_mot_de_passe: str,
        niveau: str = 'free'
    ) -> Optional[UtilisateurDB]:
        """
        Crée un nouvel utilisateur
        
        Args:
            nom_utilisateur: Nom d'utilisateur
            hash_mot_de_passe: Hash du mot de passe
            niveau: Niveau de compte ('free' ou 'premium')
            
        Returns:
            Utilisateur créé ou None si existe déjà
        """
        session = self.obtenir_session()
        
        try:
            # Vérifier si l'utilisateur existe déjà
            existe = session.query(UtilisateurDB).filter_by(nom_utilisateur=nom_utilisateur).first()
            if existe:
                logger.warning(f"L'utilisateur '{nom_utilisateur}' existe déjà")
                return None
            
            # Créer l'utilisateur
            utilisateur = UtilisateurDB(
                nom_utilisateur=nom_utilisateur,
                hash_mot_de_passe=hash_mot_de_passe,
                niveau=niveau
            )
            
            session.add(utilisateur)
            session.commit()
            session.refresh(utilisateur)
            
            logger.success(f"Utilisateur créé: {nom_utilisateur}")
            return utilisateur
            
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur création utilisateur: {e}")
            return None
        finally:
            session.close()
    
    def obtenir_utilisateur_par_nom(self, nom_utilisateur: str) -> Optional[UtilisateurDB]:
        """
        Récupère un utilisateur par son nom
        
        Args:
            nom_utilisateur: Nom d'utilisateur
            
        Returns:
            Utilisateur ou None
        """
        session = self.obtenir_session()
        try:
            utilisateur = session.query(UtilisateurDB).filter_by(nom_utilisateur=nom_utilisateur).first()
            return utilisateur
        finally:
            session.close()
    
    def obtenir_utilisateur_par_id(self, id_utilisateur: int) -> Optional[UtilisateurDB]:
        """
        Récupère un utilisateur par son ID
        
        Args:
            id_utilisateur: ID de l'utilisateur
            
        Returns:
            Utilisateur ou None
        """
        session = self.obtenir_session()
        try:
            utilisateur = session.query(UtilisateurDB).filter_by(id=id_utilisateur).first()
            return utilisateur
        finally:
            session.close()
    
    def ajouter_document(
        self,
        utilisateur_id: int,
        nom: str,
        nom_original: str,
        chemin_original: str,
        chemin_chiffre: str,
        taille_fichier: int,
        type_fichier: str,
        categorie: str = None,
        texte_extrait: str = None,
        confiance_ocr: float = None,
        hash_fichier: str = None
    ) -> Optional[DocumentDB]:
        """
        Ajoute un nouveau document
        
        Args:
            utilisateur_id: ID de l'utilisateur propriétaire
            nom: Nom du document
            nom_original: Nom du fichier original
            chemin_original: Chemin du fichier original
            chemin_chiffre: Chemin du fichier chiffré
            taille_fichier: Taille en octets
            type_fichier: Extension du fichier
            categorie: Catégorie du document
            texte_extrait: Texte extrait par OCR
            confiance_ocr: Score de confiance OCR
            hash_fichier: Hash SHA-256 du fichier original
            
        Returns:
            Document créé ou None
        """
        session = self.obtenir_session()
        
        try:
            document = DocumentDB(
                utilisateur_id=utilisateur_id,
                nom=nom,
                nom_original=nom_original,
                chemin_original=chemin_original,
                chemin_chiffre=chemin_chiffre,
                taille_fichier=taille_fichier,
                type_fichier=type_fichier,
                categorie=categorie,
                texte_extrait=texte_extrait,
                confiance_ocr=confiance_ocr,
                hash_fichier=hash_fichier
            )
            
            session.add(document)
            
            # Mettre à jour le stockage utilisateur
            utilisateur = session.query(UtilisateurDB).filter_by(id=utilisateur_id).first()
            if utilisateur:
                utilisateur.stockage_utilise += taille_fichier
            
            session.commit()
            session.refresh(document)
            
            logger.success(f"Document ajouté: {nom} (ID: {document.id})")
            return document
            
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur ajout document: {e}")
            return None
        finally:
            session.close()
    
    def obtenir_documents_utilisateur(
        self,
        utilisateur_id: int,
        categorie: str = None,
        limite: int = None
    ) -> List[DocumentDB]:
        """
        Récupère les documents d'un utilisateur
        
        Args:
            utilisateur_id: ID de l'utilisateur
            categorie: Filtrer par catégorie (optionnel)
            limite: Nombre maximum de résultats
            
        Returns:
            Liste de documents
        """
        session = self.obtenir_session()
        
        try:
            query = session.query(DocumentDB).options(joinedload(DocumentDB.etiquettes)).filter_by(utilisateur_id=utilisateur_id)
            
            if categorie:
                query = query.filter_by(categorie=categorie)
            
            query = query.order_by(DocumentDB.date_upload.desc())
            
            if limite:
                query = query.limit(limite)
            
            documents = query.all()
            return documents
            
        finally:
            session.close()
    
    def rechercher_documents(
        self,
        utilisateur_id: int,
        terme_recherche: str
    ) -> List[DocumentDB]:
        """
        Recherche des documents par nom ou texte extrait
        
        Args:
            utilisateur_id: ID de l'utilisateur
            terme_recherche: Terme à rechercher
            
        Returns:
            Liste de documents correspondants
        """
        session = self.obtenir_session()
        
        try:
            from sqlalchemy import or_
            query = session.query(DocumentDB).options(joinedload(DocumentDB.etiquettes)).filter(DocumentDB.utilisateur_id == utilisateur_id)
            query = query.filter(or_(
                DocumentDB.nom.ilike(f"%{terme_recherche}%"),
                DocumentDB.texte_extrait.ilike(f"%{terme_recherche}%"),
                DocumentDB.categorie.ilike(f"%{terme_recherche}%")
            ))
            return query.all()
        finally:
            session.close()

    def obtenir_document_par_id(self, document_id: int) -> Optional[DocumentDB]:
        """Récupère un document par son ID"""
        session = self.obtenir_session()
        try:
            return session.query(DocumentDB).options(joinedload(DocumentDB.etiquettes)).filter_by(id=document_id).first()
        finally:
            session.close()
    
    def supprimer_document(self, document_id: int) -> bool:
        """
        Supprime un document
        
        Args:
            document_id: ID du document
            
        Returns:
            True si supprimé avec succès
        """
        session = self.obtenir_session()
        
        try:
            document = session.query(DocumentDB).filter_by(id=document_id).first()
            
            if not document:
                logger.warning(f"Document {document_id} non trouvé")
                return False
            
            # Mettre à jour le stockage utilisateur
            utilisateur = session.query(UtilisateurDB).filter_by(id=document.utilisateur_id).first()
            if utilisateur:
                utilisateur.stockage_utilise -= document.taille_fichier
            
            session.delete(document)
            session.commit()
            
            logger.success(f"Document {document_id} supprimé")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur suppression document: {e}")
            return False
        finally:
            session.close()

    def creer_etiquette(self, nom: str, couleur: str = "#3B82F6", utilisateur_id: int = None) -> Optional[EtiquetteDB]:
        """Crée une nouvelle étiquette pour un utilisateur spécifique"""
        session = self.obtenir_session()
        try:
            # Vérifier si elle existe déjà pour cet utilisateur
            existe = session.query(EtiquetteDB).filter_by(nom=nom, utilisateur_id=utilisateur_id).first()
            if existe:
                return existe
            
            etiquette = EtiquetteDB(nom=nom, couleur=couleur, utilisateur_id=utilisateur_id)
            session.add(etiquette)
            session.commit()
            session.refresh(etiquette)
            return etiquette
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur création étiquette: {e}")
            return None
        finally:
            session.close()

    def obtenir_toutes_etiquettes(self, utilisateur_id: int = None) -> List[EtiquetteDB]:
        """Récupère toutes les étiquettes accessibles à l'utilisateur (les sienens + système)"""
        session = self.obtenir_session()
        try:
            from sqlalchemy import or_
            return session.query(EtiquetteDB).filter(
                or_(
                    EtiquetteDB.utilisateur_id == utilisateur_id,
                    EtiquetteDB.utilisateur_id == None
                )
            ).all()
        finally:
            session.close()

    def supprimer_etiquette(self, etiquette_id: int) -> bool:
        """Supprime une étiquette"""
        session = self.obtenir_session()
        try:
            etiquette = session.query(EtiquetteDB).filter_by(id=etiquette_id).first()
            if etiquette:
                session.delete(etiquette)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur suppression étiquette: {e}")
            return False
        finally:
            session.close()

    def ajouter_etiquette_a_document(self, document_id: int, etiquette_id: int) -> bool:
        """Associe une étiquette à un document"""
        session = self.obtenir_session()
        try:
            document = session.query(DocumentDB).filter_by(id=document_id).first()
            etiquette = session.query(EtiquetteDB).filter_by(id=etiquette_id).first()
            
            if document and etiquette and etiquette not in document.etiquettes:
                document.etiquettes.append(etiquette)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur association étiquette: {e}")
            return False
        finally:
            session.close()

    def retirer_etiquette_de_document(self, document_id: int, etiquette_id: int) -> bool:
        """Retire une étiquette d'un document"""
        session = self.obtenir_session()
        try:
            document = session.query(DocumentDB).filter_by(id=document_id).first()
            etiquette = session.query(EtiquetteDB).filter_by(id=etiquette_id).first()
            
            if document and etiquette and etiquette in document.etiquettes:
                document.etiquettes.remove(etiquette)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur retrait étiquette: {e}")
            return False
        finally:
            session.close()
    def creer_etiquettes_par_defaut(self, utilisateur_id: int):
        """Initialise les étiquettes standard pour un nouvel utilisateur"""
        defaults = [
        ("Factures", "#F59E0B"),   # Amber
        ("Identité", "#3B82F6"),   # Blue
        ("Urgent", "#EF4444")      # Red
    ]
        for nom, couleur in defaults:
            self.creer_etiquette(nom, couleur, utilisateur_id)

    def obtenir_etiquette_par_nom(self, nom: str, utilisateur_id: int = None) -> Optional[EtiquetteDB]:
        """Récupère une étiquette par son nom"""
        session = self.obtenir_session()
        try:
            from sqlalchemy import or_
            return session.query(EtiquetteDB).filter(
                EtiquetteDB.nom == nom,
                or_(
                    EtiquetteDB.utilisateur_id == utilisateur_id,
                    EtiquetteDB.utilisateur_id == None
                )
            ).first()
        finally:
            session.close()
    
    def ajouter_log_telechargement(
        self,
        utilisateur_id: int,
        document_id: int,
        action: str,
        adresse_ip: str = None,
        succes: bool = True,
        message_erreur: str = None
    ) -> bool:
        """
        Enregistre un log de téléchargement/accès
        
        Args:
            utilisateur_id: ID de l'utilisateur
            document_id: ID du document
            action: Type d'action ('download', 'view', 'decrypt_failed')
            adresse_ip: Adresse IP de l'utilisateur
            succes: Si l'action a réussi
            message_erreur: Message d'erreur si échec
            
        Returns:
            True si enregistré avec succès
        """
        session = self.obtenir_session()
        try:
            log = LogTelechargementDB(
                utilisateur_id=utilisateur_id,
                document_id=document_id,
                action=action,
                adresse_ip=adresse_ip,
                succes=succes,
                message_erreur=message_erreur
            )
            session.add(log)
            session.commit()
            logger.info(f"Log téléchargement: user={utilisateur_id}, doc={document_id}, action={action}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur ajout log téléchargement: {e}")
            return False
        finally:
            session.close()

# Instance globale
gestionnaire_bdd = GestionnaireBaseDeDonnees()
