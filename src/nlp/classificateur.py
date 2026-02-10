"""
Module de classification NLP SafeDoc
Classification automatique de documents par catégorie
"""
from typing import Dict, List, Tuple
from loguru import logger

from config.config import DOCUMENT_CATEGORIES, CATEGORY_KEYWORDS


class ClassificateurDocument:
    """Classificateur de documents basé sur mots-clés et NLP"""
    
    def __init__(self):
        """Initialise le classificateur"""
        self.categories = DOCUMENT_CATEGORIES
        self.mots_cles = CATEGORY_KEYWORDS
    
    def categoriser_par_mots_cles(self, texte: str) -> Tuple[str, float]:
        """
        Catégorise un document basé sur les mots-clés
        
        Args:
            texte: Texte du document
            
        Returns:
            Tuple (catégorie, score de confiance 0-1)
        """
        texte_lower = texte.lower()
        scores = {}
        
        # Calculer le score pour chaque catégorie
        for categorie, mots_cles in self.mots_cles.items():
            score = 0
            for mot_cle in mots_cles:
                # Compter les occurrences du mot-clé
                count = texte_lower.count(mot_cle.lower())
                score += count
            
            scores[categorie] = score
        
        # Trouver la catégorie avec le score le plus élevé
        if not scores or max(scores.values()) == 0:
            return 'Autre', 0.0
        
        meilleure_categorie = max(scores, key=scores.get)
        score_max = scores[meilleure_categorie]
        
        # Normaliser le score (confiance)
        # Plus de mots-clés trouvés = plus de confiance
        confiance = min(score_max / 5.0, 1.0)  # Max à 5 occurrences
        
        logger.debug(f"Catégorie détectée: {meilleure_categorie} (confiance: {confiance:.2f})")
        return meilleure_categorie, confiance
    
    def categoriser_par_structure(self, texte: str) -> Tuple[str, float]:
        """
        Catégorise un document basé sur la structure du texte
        
        Args:
            texte: Texte du document
            
        Returns:
            Tuple (catégorie, score de confiance)
        """
        texte_lower = texte.lower()
        
        # Factures - recherche de structure typique
        if any(terme in texte_lower for terme in ['total ttc', 'montant à payer', 'tva']) and \
           any(terme in texte_lower for terme in ['facture', 'invoice']):
            return 'Facture', 0.85
        
        # Contrats - termes juridiques
        if any(terme in texte_lower for terme in ['soussigné', 'partie', 'clause', 'signé le']) and \
           'contrat' in texte_lower:
            return 'Contrat', 0.80
        
        # Pièces d'identité - informations personnelles
        if any(terme in texte_lower for terme in ['né(e) le', 'nationalité', 'carte d\'identité', 'passeport']):
            return 'Pièce d\'identité', 0.75
        
        # Documents médicaux
        if any(terme in texte_lower for terme in ['patient', 'médecin', 'ordonnance', 'diagnostic', 'prescription']):
            return 'Document médical', 0.70
        
        # Relevés bancaires
        if any(terme in texte_lower for terme in ['relevé de compte', 'solde', 'débit', 'crédit', 'iban']):
            return 'Relevé bancaire', 0.75
        
        return 'Autre', 0.3
    
    def predire_categorie(self, texte: str, nom_fichier: str = '') -> Tuple[str, float]:
        """
        Prédit la catégorie d'un document
        
        Args:
            texte: Texte du document
            nom_fichier: Nom du fichier (optionnel)
            
        Returns:
            Tuple (catégorie, confiance)
        """
        logger.info(f"Classification du document: {nom_fichier or 'sans nom'}")
        
        if not texte or len(texte) < 10:
            logger.warning("Texte trop court pour classification")
            return 'Autre', 0.0
        
        # Essayer la classification par nom de fichier
        if nom_fichier:
            cat_nom, conf_nom = self._categoriser_par_nom(nom_fichier)
            if conf_nom > 0.7:
                logger.success(f"Catégorie prédite (par nom): {cat_nom} (confiance: {conf_nom:.2f})")
                return cat_nom, conf_nom
        
        # Classification par mots-clés
        cat_mots, conf_mots = self.categoriser_par_mots_cles(texte)
        
        # Classification par structure
        cat_structure, conf_structure = self.categoriser_par_structure(texte)
        
        # Combiner les résultats (pondération)
        if cat_mots == cat_structure and max(conf_mots, conf_structure) > 0.5:
            # Les deux méthodes sont d'accord et confiantes
            categorie = cat_mots
            confiance = (conf_mots + conf_structure) / 2
        elif conf_mots > conf_structure:
            categorie = cat_mots
            confiance = conf_mots
        else:
            categorie = cat_structure
            confiance = conf_structure
        
        logger.success(f"Catégorie prédite: {categorie} (confiance: {confiance:.2f})")
        return categorie, confiance
    
    def _categoriser_par_nom(self, nom_fichier: str) -> Tuple[str, float]:
        """
        Catégorise basé sur le nom du fichier
        
        Args:
            nom_fichier: Nom du fichier
            
        Returns:
            Tuple (catégorie, confiance)
        """
        nom_lower = nom_fichier.lower()
        
        # Patterns dans les noms de fichiers
        patterns = {
            'Facture': ['facture', 'invoice', 'bill'],
            'Contrat': ['contrat', 'contract', 'accord'],
            'Pièce d\'identité': ['carte', 'identite', 'passeport', 'cni'],
            'Document médical': ['medical', 'ordonnance', 'analyse'],
            'Document fiscal': ['impot', 'tax', 'fiscal', 'declaration'],
            'Relevé bancaire': ['releve', 'banque', 'bank', 'statement'],
            'Diplôme': ['diplome', 'certificat', 'attestation'],
        }
        
        for categorie, mots in patterns.items():
            for mot in mots:
                if mot in nom_lower:
                    return categorie, 0.8
        
        return 'Autre', 0.0
    
    def obtenir_suggestions_categories(self, texte: str, top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Obtient les N meilleures suggestions de catégories
        
        Args:
            texte: Texte du document
            top_n: Nombre de suggestions
            
        Returns:
            Liste de tuples (catégorie, confiance)
        """
        texte_lower = texte.lower()
        scores = {}
        
        # Calculer les scores pour toutes les catégories
        for categorie, mots_cles in self.mots_cles.items():
            score = sum(texte_lower.count(mot.lower()) for mot in mots_cles)
            if score > 0:
                scores[categorie] = min(score / 5.0, 1.0)
        
        # Trier par score décroissant
        suggestions = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return suggestions or [('Autre', 0.0)]


# Instance globale
classificateur = ClassificateurDocument()
