"""
Module OCR SafeDoc
Reconnaissance optique de caractères pour extraire le texte des documents
"""
import io
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from pdf2image import convert_from_path
from loguru import logger

from config.config import TESSERACT_PATH, OCR_LANGUAGE, OCR_CONFIDENCE_THRESHOLD, IMAGE_PREPROCESSING


# Configurer le chemin Tesseract (Windows)
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class ScannerOCR:
    """Scanner OCR pour extraire du texte depuis images et PDF"""
    
    def __init__(self, langue: str = OCR_LANGUAGE):
        """
        Initialise le scanner OCR
        
        Args:
            langue: Code langue Tesseract (fra, eng, etc.)
        """
        self.langue = langue
        self.config_tesseract = f'--oem 3 --psm 3 -l {langue}'
    
    def pretraiter_image(self, image: Image.Image) -> Image.Image:
        """
        Prétraite une image pour améliorer la reconnaissance OCR
        
        Args:
            image: Image PIL
            
        Returns:
            Image prétraitée
        """
        # Convertir en niveaux de gris
        if image.mode != 'L':
            image = image.convert('L')
        
        # Agrandir l'image pour meilleure précision
        if IMAGE_PREPROCESSING.get('resize_factor', 1) > 1:
            factor = IMAGE_PREPROCESSING['resize_factor']
            nouvelle_taille = (image.width * factor, image.height * factor)
            image = image.resize(nouvelle_taille, Image.Resampling.LANCZOS)
        
        # Améliorer le contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Améliorer la netteté
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)
        
        # Réduire le bruit
        if IMAGE_PREPROCESSING.get('denoise', False):
            image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # Binarisation (seuillage)
        if IMAGE_PREPROCESSING.get('threshold', False):
            # Seuil d'Otsu
            threshold = 128
            image = image.point(lambda p: 255 if p > threshold else 0)
        
        logger.debug("Image prétraitée pour OCR")
        return image
    
    def scanner_image(self, chemin_image: Path) -> Tuple[str, float]:
        """
        Extrait le texte d'une image
        
        Args:
            chemin_image: Chemin de l'image
            
        Returns:
            Tuple (texte extrait, confiance moyenne)
        """
        logger.info(f"Scan OCR de l'image: {chemin_image}")
        
        try:
            # Charger l'image
            image = Image.open(chemin_image)
            
            # Prétraiter
            image_traitee = self.pretraiter_image(image)
            
            # Extraire le texte
            texte = pytesseract.image_to_string(image_traitee, config=self.config_tesseract)
            
            # Obtenir la confiance
            donnees = pytesseract.image_to_data(image_traitee, output_type=pytesseract.Output.DICT, config=self.config_tesseract)
            confiances = [float(conf) for conf in donnees['conf'] if conf != '-1']
            confiance_moyenne = sum(confiances) / len(confiances) if confiances else 0.0
            
            logger.success(f"OCR terminé - {len(texte)} caractères extraits (confiance: {confiance_moyenne:.1f}%)")
            
            return texte.strip(), confiance_moyenne
            
        except Exception as e:
            logger.error(f"Erreur OCR image: {e}")
            return "", 0.0
    
    def scanner_pdf(self, chemin_pdf: Path, max_pages: int = None) -> Tuple[str, float]:
        """
        Extrait le texte d'un PDF
        
        Args:
            chemin_pdf: Chemin du PDF
            max_pages: Nombre maximum de pages à scanner
            
        Returns:
            Tuple (texte extrait, confiance moyenne)
        """
        logger.info(f"Scan OCR du PDF: {chemin_pdf}")
        
        try:
            # Essayer d'abord d'extraire le texte directement (PDF texte)
            from PyPDF2 import PdfReader
            
            reader = PdfReader(str(chemin_pdf))
            texte_direct = ""
            
            for page in reader.pages[:max_pages] if max_pages else reader.pages:
                texte_direct += page.extract_text() + "\n"
            
            # Si le texte est présent, le retourner
            if texte_direct.strip():
                logger.success(f"Texte extrait directement du PDF - {len(texte_direct)} caractères")
                return texte_direct.strip(), 100.0  # Confiance maximale pour extraction directe
            
            # Sinon, utiliser OCR sur les images
            logger.info("PDF sans texte détecté - conversion en images pour OCR")
            
            # Convertir PDF en images
            images = convert_from_path(str(chemin_pdf), dpi=300)
            
            if max_pages:
                images = images[:max_pages]
            
            texte_total = ""
            confiances = []
            
            for i, image in enumerate(images, 1):
                logger.debug(f"Scan page {i}/{len(images)}")
                
                # Prétraiter
                image_traitee = self.pretraiter_image(image)
                
                # Extraire le texte
                texte = pytesseract.image_to_string(image_traitee, config=self.config_tesseract)
                texte_total += texte + "\n"
                
                # Confiance
                donnees = pytesseract.image_to_data(image_traitee, output_type=pytesseract.Output.DICT, config=self.config_tesseract)
                conf = [float(c) for c in donnees['conf'] if c != '-1']
                if conf:
                    confiances.extend(conf)
            
            confiance_moyenne = sum(confiances) / len(confiances) if confiances else 0.0
            
            logger.success(f"OCR PDF terminé - {len(texte_total)} caractères extraits (confiance: {confiance_moyenne:.1f}%)")
            
            return texte_total.strip(), confiance_moyenne
            
        except Exception as e:
            logger.error(f"Erreur OCR PDF: {e}")
            return "", 0.0
    
    def scanner_document(self, chemin_fichier: Path) -> Tuple[str, float]:
        """
        Scanne un document (détecte automatiquement le type)
        
        Args:
            chemin_fichier: Chemin du fichier
            
        Returns:
            Tuple (texte extrait, confiance moyenne)
        """
        extension = chemin_fichier.suffix.lower()
        
        if extension == '.pdf':
            return self.scanner_pdf(chemin_fichier)
        elif extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return self.scanner_image(chemin_fichier)
        else:
            logger.warning(f"Type de fichier non supporté pour OCR: {extension}")
            return "", 0.0
    
    def scanner_lot(self, chemins_fichiers: list[Path]) -> dict:
        """
        Scanne plusieurs fichiers
        
        Args:
            chemins_fichiers: Liste de chemins de fichiers
            
        Returns:
            Dictionnaire {chemin: (texte, confiance)}
        """
        resultats = {}
        
        for i, chemin in enumerate(chemins_fichiers, 1):
            logger.info(f"Scan fichier {i}/{len(chemins_fichiers)}")
            texte, confiance = self.scanner_document(chemin)
            resultats[str(chemin)] = (texte, confiance)
        
        return resultats


# Instance globale
scanner_ocr = ScannerOCR()
