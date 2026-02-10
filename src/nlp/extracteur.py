"""
Module d'extraction NLP SafeDoc
Extraction d'entités et d'informations clés depuis le texte
"""
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger

try:
    import spacy
    from spacy.tokens import Doc
    SPACY_DISPONIBLE = True
except ImportError:
    SPACY_DISPONIBLE = False
    logger.warning("spaCy non disponible - extraction NLP limitée")

from config.config import SPACY_MODEL


class ExtracteurNLP:
    """Extracteur d'informations basé sur NLP"""
    
    def __init__(self):
        """Initialise l'extracteur NLP"""
        self.nlp = None
        
        if SPACY_DISPONIBLE:
            try:
                self.nlp = spacy.load(SPACY_MODEL)
                logger.success(f"Modèle spaCy chargé: {SPACY_MODEL}")
            except OSError:
                logger.error(f"Modèle spaCy '{SPACY_MODEL}' non trouvé. Exécutez: python -m spacy download {SPACY_MODEL}")
    
    def extraire_entites(self, texte: str) -> Dict[str, List[str]]:
        """
        Extrait les entités nommées du texte
        
        Args:
            texte: Texte à analyser
            
        Returns:
            Dictionnaire {type_entité: [entités]}
        """
        if not self.nlp or not texte:
            return {}
        
        doc = self.nlp(texte)
        
        entites = {
            'personnes': [],
            'organisations': [],
            'lieux': [],
            'dates': [],
            'montants': [],
            'autres': []
        }
        
        for ent in doc.ents:
            if ent.label_ == 'PER':
                entites['personnes'].append(ent.text)
            elif ent.label_ == 'ORG':
                entites['organisations'].append(ent.text)
            elif ent.label_ in ['LOC', 'GPE']:
                entites['lieux'].append(ent.text)
            elif ent.label_ in ['DATE', 'TIME']:
                entites['dates'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entites['montants'].append(ent.text)
            else:
                entites['autres'].append(f"{ent.text} ({ent.label_})")
        
        # Supprimer les doublons
        for cle in entites:
            entites[cle] = list(set(entites[cle]))
        
        logger.debug(f"Entités extraites: {sum(len(v) for v in entites.values())} au total")
        return entites
    
    def extraire_dates(self, texte: str) -> List[str]:
        """
        Extrait les dates du texte (format FR)
        
        Args:
            texte: Texte à analyser
            
        Returns:
            Liste des dates trouvées
        """
        dates = []
        
        # Patterns de dates françaises
        patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # 01/12/2024, 1-12-24
            r'\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}',  # 12 janvier 2024
            r'\d{4}-\d{2}-\d{2}',  # 2024-01-12 (ISO)
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, texte, re.IGNORECASE)
            dates.extend(matches)
        
        # Utiliser spaCy si disponible
        if self.nlp:
            doc = self.nlp(texte)
            for ent in doc.ents:
                if ent.label_ in ['DATE', 'TIME']:
                    dates.append(ent.text)
        
        dates = list(set(dates))
        logger.debug(f"Dates extraites: {len(dates)}")
        return dates
    
    def extraire_montants(self, texte: str) -> List[str]:
        """
        Extrait les montants monétaires du texte
        
        Args:
            texte: Texte à analyser
            
        Returns:
            Liste des montants trouvés
        """
        montants = []
        
        # Patterns de montants
        patterns = [
            r'\d+[,\s]\d{2}\s*€',  # 123,45 €
            r'\d+\.\d{2}\s*EUR',  # 123.45 EUR
            r'\d+\s*euros?',  # 123 euros
            r'€\s*\d+[,\.]\d{2}',  # € 123,45
            r'Total\s*:?\s*\d+[,\.]\d{2}',  # Total: 123,45
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, texte, re.IGNORECASE)
            montants.extend(matches)
        
        # Utiliser spaCy si disponible
        if self.nlp:
            doc = self.nlp(texte)
            for ent in doc.ents:
                if ent.label_ == 'MONEY':
                    montants.append(ent.text)
        
        montants = list(set(montants))
        logger.debug(f"Montants extraits: {len(montants)}")
        return montants
    
    def extraire_emails(self, texte: str) -> List[str]:
        """
        Extrait les adresses email du texte
        
        Args:
            texte: Texte à analyser
            
        Returns:
            Liste des emails trouvés
        """
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, texte)
        logger.debug(f"Emails extraits: {len(emails)}")
        return list(set(emails))
    
    def extraire_telephones(self, texte: str) -> List[str]:
        """
        Extrait les numéros de téléphone du texte (formats français)
        
        Args:
            texte: Texte à analyser
            
        Returns:
            Liste des numéros trouvés
        """
        patterns = [
            r'0[1-9](?:[\s.-]?\d{2}){4}',  # 01 23 45 67 89
            r'\+33[\s.-]?[1-9](?:[\s.-]?\d{2}){4}',  # +33 1 23 45 67 89
        ]
        
        telephones = []
        for pattern in patterns:
            matches = re.findall(pattern, texte)
            telephones.extend(matches)
        
        logger.debug(f"Téléphones extraits: {len(telephones)}")
        return list(set(telephones))
    
    def extraire_infos_cles(self, texte: str, type_doc: str = None) -> Dict[str, Any]:
        """
        Extrait les informations clés selon le type de document
        
        Args:
            texte: Texte à analyser
            type_doc: Type de document (optionnel)
            
        Returns:
            Dictionnaire d'informations clés
        """
        logger.info(f"Extraction d'informations clés (type: {type_doc or 'auto'})")
        
        infos = {
            'entites': self.extraire_entites(texte),
            'dates': self.extraire_dates(texte),
            'montants': self.extraire_montants(texte),
            'emails': self.extraire_emails(texte),
            'telephones': self.extraire_telephones(texte),
        }
        
        # Extraction spécifique selon le type
        if type_doc:
            if 'facture' in type_doc.lower():
                infos['numero_facture'] = self._extraire_numero_facture(texte)
                infos['tva'] = self._extraire_tva(texte)
            
            elif 'identité' in type_doc.lower() or 'carte' in type_doc.lower():
                infos['numero_document'] = self._extraire_numero_document(texte)
            
            elif 'contrat' in type_doc.lower():
                infos['numero_contrat'] = self._extraire_numero_contrat(texte)
        
        logger.success(f"Informations clés extraites: {sum(len(v) if isinstance(v, list) else 1 for v in infos.values() if v)}")
        return infos
    
    def _extraire_numero_facture(self, texte: str) -> Optional[str]:
        """Extrait le numéro de facture"""
        patterns = [
            r'Facture\s*n[°o]?\s*:?\s*([A-Z0-9-]+)',
            r'Invoice\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'N[°o]\s*facture\s*:?\s*([A-Z0-9-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texte, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extraire_tva(self, texte: str) -> Optional[str]:
        """Extrait le montant de TVA"""
        pattern = r'TVA\s*:?\s*(\d+[,\.]\d{2})'
        match = re.search(pattern, texte, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _extraire_numero_document(self, texte: str) -> Optional[str]:
        """Extrait le numéro de document d'identité"""
        patterns = [
            r'N[°o]\s*:?\s*([A-Z0-9]{8,})',
            r'Numéro\s*:?\s*([A-Z0-9]{8,})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texte, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extraire_numero_contrat(self, texte: str) -> Optional[str]:
        """Extrait le numéro de contrat"""
        patterns = [
            r'Contrat\s*n[°o]?\s*:?\s*([A-Z0-9-]+)',
            r'Référence\s*:?\s*([A-Z0-9-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texte, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extraire_metadonnees(self, texte: str) -> Dict[ str, Any]:
        """
        Extrait les métadonnées générales du document
        
        Args:
            texte: Texte du document
            
        Returns:
            Dictionnaire de métadonnées
        """
        return {
            'nb_caracteres': len(texte),
            'nb_mots': len(texte.split()),
            'nb_lignes': len(texte.split('\n')),
            'langue_detectee': self._detecter_langue(texte),
            'date_extraction': datetime.now().isoformat(),
        }
    
    def _detecter_langue(self, texte: str) -> str:
        """Détecte la langue du texte (simple)"""
        # Mots français courants
        mots_francais = ['le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'est', 'dans', 'pour']
        texte_lower = texte.lower()
        
        count_fr = sum(1 for mot in mots_francais if f' {mot} ' in texte_lower)
        
        return 'fr' if count_fr > 3 else 'autre'


# Instance globale
extracteur_nlp = ExtracteurNLP()
