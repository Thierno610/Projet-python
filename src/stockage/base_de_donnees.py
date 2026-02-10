"""
Module de base de données SafeDoc
Modèles SQLAlchemy pour utilisateurs, documents et étiquettes
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Table, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from loguru import logger

from config.config import DATABASE_URL

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
    niveau = Column(String(20), default='free')  # 'free' ou 'premium'
    stockage_utilise = Column(Integer, default=0)  # en octets
    date_creation = Column(DateTime, default=datetime.now)
    derniere_connexion = Column(DateTime, default=datetime.now)
    
    # Relations
    documents = relationship('DocumentDB', back_populates='utilisateur', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Utilisateur(id={self.id}, nom='{self.nom_utilisateur}', niveau='{self.niveau}')>"


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
    nom = Column(String(100), unique=True, nullable=False, index=True)
    couleur = Column(String(7), default='#3498db')  # Couleur hex
    
    # Relations
    documents = relationship('DocumentDB', secondary=association_document_etiquette, back_populates='etiquettes')
    
    def __repr__(self):
        return f"<Etiquette(id={self.id}, nom='{self.nom}')>"


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
        confiance_ocr: float = None
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
                confiance_ocr=confiance_ocr
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
            query = session.query(DocumentDB).filter_by(utilisateur_id=utilisateur_id)
            
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
            documents = session.query(DocumentDB).filter(
                DocumentDB.utilisateur_id == utilisateur_id,
                (DocumentDB.nom.ilike(f'%{terme_recherche}%')) |
                (DocumentDB.texte_extrait.ilike(f'%{terme_recherche}%'))
            ).all()
            
            return documents
            
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

    def creer_etiquette(self, nom: str, couleur: str = "#3B82F6") -> Optional[EtiquetteDB]:
        """Crée une nouvelle étiquette"""
        session = self.obtenir_session()
        try:
            # Vérifier si elle existe déjà
            existe = session.query(EtiquetteDB).filter_by(nom=nom).first()
            if existe:
                return existe
            
            etiquette = EtiquetteDB(nom=nom, couleur=couleur)
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

    def obtenir_toutes_etiquettes(self) -> List[EtiquetteDB]:
        """Récupère toutes les étiquettes"""
        session = self.obtenir_session()
        try:
            return session.query(EtiquetteDB).all()
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


# Instance globale
gestionnaire_bdd = GestionnaireBaseDeDonnees()
