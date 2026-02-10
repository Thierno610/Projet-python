# 📖 Manuel Utilisateur SafeDoc

## 🔒 Bienvenue sur SafeDoc !

SafeDoc est votre coffre-fort numérique intelligent qui transforme la gestion de vos documents importants grâce à l'OCR, l'intelligence artificielle et le chiffrement de niveau militaire.

### 🌟 Notre Vision

SafeDoc est une application Python qui permet de :
- 📷 **Scanner** les documents
- 🔍 **Extraire** automatiquement le texte
- 🧠 **Classer** intelligemment les documents
- 🔐 **Sécuriser** les fichiers par chiffrement

---

## 📋 Table des Matières

1. [Installation](#installation)
2. [Premiers Pas](#premiers-pas)
3. [Utilisation de l'Interface Web](#interface-web)
4. [Fonctionnalités Principales](#fonctionnalités)
5. [Sécurité](#sécurité)
6. [FAQ](#faq)
7. [Dépannage](#dépannage)

---

## 🚀 Installation

### Prérequis

#### 1. Python
- Version requise: **Python 3.9 ou supérieur**
- Vérifiez votre version:
```bash
python --version
```

#### 2. Tesseract OCR
Tesseract est nécessaire pour la reconnaissance de texte.

**Windows:**
1. Télécharger depuis: https://github.com/UB-Mannheim/tesseract/wiki
2. Installer dans `C:\Program Files\Tesseract-OCR`
3. Le chemin sera automatiquement détecté

**Mac:**
```bash
brew install tesseract tesseract-lang
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-fra
```

### Installation de SafeDoc

#### Étape 1: Installer les dépendances

```bash
py -m pip install -r requirements.txt
```

#### Étape 2: Télécharger le modèle NLP français

```bash
py -m spacy download fr_core_news_md
```

#### Étape 3: Télécharger les données NLTK

```bash
py -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```


#### Étape 6: Configurer l'environnement

1. Copiez le fichier `.env.example` en `.env`
2. Modifiez les valeurs dans `.env`:

```env
# IMPORTANT: Changez cette clé!
MASTER_KEY=votre_cle_secrete_unique_et_tres_longue_minimum_32_caracteres

# Vérifiez le chemin Tesseract
TESSERACT_PATH=C:/Program Files/Tesseract-OCR/tesseract.exe
```

---

## 🎯 Premiers Pas

### Lancement de l'Application

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse: **http://localhost:8501** (Accès direct sans connexion).

---

## 🎯 Premiers Pas

### Accès Direct

SafeDoc est configuré en mode **Accès Direct**. Cela signifie que :
1. Vous n'avez pas besoin de créer de compte.
2. Vous accédez directement à votre tableau de bord.
3. Le chiffrement est géré automatiquement avec une clé de sécurité principale.

---

## 💻 Interface Web

### 🏠 Tableau de Bord
Le tableau de bord vous donne une vue d'ensemble de vos documents et de votre stockage.

- **📊 Statistiques:**
  - Nombre total de documents
  - Espace de stockage utilisé
  - Votre niveau (Gratuit/Premium)

- **📋 Documents récents:**
  - Les 5 derniers documents ajoutés
  - Accès rapide pour visualisation

### 📤 Téléverser un Document

1. **Cliquez sur "Téléverser" dans le menu**

2. **Sélectionnez votre fichier:**
   - Formats supportés: PDF, PNG, JPG, JPEG, TIFF, BMP
   - Taille maximum: 50 MB

3. **Nom personnalisé (optionnel):**
   - Par défaut: nom du fichier original
   - Vous pouvez le renommer

4. **Cliquez sur "Traiter et Sauvegarder"**

5. **Traitement automatique:**
   - ⏳ Extraction du texte (OCR)
   - 🧠 Classification automatique
   - 🔐 Chiffrement AES-256
   - 💾 Sauvegarde sécurisée

6. **Résultats affichés:**
   - Catégorie détectée (Facture, Contrat, etc.)
   - Score de confiance
   - Aperçu du texte extrait
   - Informations clés (dates, montants, etc.)

### 📚 Bibliothèque de Documents

1. **Accédez à votre bibliothèque**

2. **Recherchez vos documents:**
   - 🔍 Barre de recherche (nom, contenu)
   - 🏷️ Filtre par catégorie

3. **Actions disponibles:**
   - 👁️ **Voir:** Déchiffrer et télécharger
   - 🗑️ **Supprimer:** Effacer définitivement

### 👁️ Visualiser un Document

1. **Cliquez sur l'icône 👁️**

2. **Entrez votre mot de passe de chiffrement**

3. **Cliquez sur "Déchiffrer et télécharger"**

4. **Le fichier est automatiquement téléchargé**

---

## ✨ Fonctionnalités Principales

### 🔍 OCR Intelligent

**Qu'est-ce que c'est?**
- Reconnaissance Optique de Caractères
- Extrait automatiquement le texte de vos documents scannés

**Avantages:**
- ✅ Scanne les documents papier
- ✅ Extrait le texte des images
- ✅ Traite les PDF scannés
- ✅ Prétraitement d'image pour meilleure qualité
- ✅ Score de confiance pour chaque extraction

**Formats supportés:**
- PDF (texte ou scanné)
- Images: PNG, JPG, JPEG, TIFF, BMP

### 🧠 Classification Automatique

**Comment ça marche?**
SafeDoc analyse le contenu et classe automatiquement vos documents.

**Catégories disponibles:**
- 🧾 Facture
- 📝 Contrat
- 🪪 Pièce d'identité
- 🏥 Document médical
- 💰 Document fiscal
- 🎓 Document éducatif
- 📋 Document administratif
- 💳 Relevé bancaire
- 📄 Autre

**Extraction d'informations:**
- 📅 Dates
- 💶 Montants
- 👤 Noms et personnes
- 🏢 Organisations
- 📧 Emails
- 📞 Numéros de téléphone
- 🔢 Numéros de document

### 🔐 Sécurité Maximale

**Chiffrement AES-256:**
- Standard militaire
- Vos documents sont chiffrés individuellement
- Impossible à déchiffrer sans votre mot de passe

**Protection des données:**
- ✅ Chiffrement de bout en bout
- ✅ Mots de passe hachés avec bcrypt
- ✅ Clés dérivées avec PBKDF2 (100 000 itérations)
- ✅ Jamais stockés en clair

### 💾 Gestion du Stockage

**Version Gratuite:**
- 500 MB de stockage
- Stockage local sécurisé
- Nombre illimité de documents

**Version Premium:** ⭐
- 50 GB de stockage
- Synchronisation Google Drive
- Sauvegarde automatique
- Accès multi-appareils

---

## 🔐 Sécurité

SafeDoc utilise un chiffrement **AES-256** de niveau militaire. Vos documents sont chiffrés automatiquement à l'aide d'une clé maître configurée dans votre fichier `.env`.

> [!IMPORTANT]
> Ne partagez jamais votre fichier `.env` ou votre `MASTER_KEY` car ils sont essentiels à la protection de vos documents.

---

## ❓ FAQ

### **Q: J'ai oublié mon mot de passe de chiffrement. Que faire?**
**R:** Malheureusement, si vous perdez ce mot de passe, vos documents ne peuvent **PAS** être récupérés. C'est le prix de la sécurité maximale. Notez-le dans un lieu très sûr!

### **Q: Puis-je changer mon mot de passe de chiffrement?**
**R:** Oui, mais vous devrez déchiffrer tous vos documents avec l'ancien mot de passe, puis les rechiffrer avec le nouveau. Un outil sera fourni dans une future version.

### **Q: Mes documents sont-ils stockés dans le cloud?**
**R:** 
- Version gratuite: Non, tout est local
- Version premium: Oui, synchronisation Google Drive optionnelle

### **Q: L'OCR fonctionne-t-il avec tous les documents?**
**R:** L'OCR fonctionne mieux avec:
- Images de bonne qualité
- Texte clair et lisible
- Documents bien scannés

La qualité peut varier pour les documents manuscrits ou de mauvaise qualité.

### **Q: Quelle est la différence entre Gratuit et Premium?**
**R:** 
- **Gratuit:** 500 MB, stockage local uniquement
- **Premium:** 50 GB, synchronisation cloud, sauvegarde auto

### **Q: Puis-je uploader plusieurs fichiers à la fois?**
**R:** Actuellement non, mais cette fonctionnalité sera ajoutée prochainement.

### **Q: SafeDoc fonctionne-t-il hors ligne?**
**R:** Oui! SafeDoc fonctionne entièrement hors ligne (sauf sync cloud Premium).

---

## 🔧 Dépannage

### Problème: "Tesseract non trouvé"

**Solution:**
1. Vérifiez l'installation de Tesseract
2. Modifiez le chemin dans `.env`:
```env
TESSERACT_PATH=C:/Program Files/Tesseract-OCR/tesseract.exe
```

### Problème: "Modèle spaCy non trouvé"

**Solution:**
```bash
python -m spacy download fr_core_news_md
```

### Problème: "Erreur d'importation"

**Solution:**
Réinstallez les dépendances:
```bash
py -m pip install -r requirements.txt --force-reinstall
```


### Problème: "Quota de stockage dépassé"

**Solutions:**
1. Supprimez des documents inutiles
2. Passez à Premium pour plus d'espace
3. Archivez vos anciens documents

### Problème: "Le document ne se déchiffre pas"

**Causes possibles:**
- Mauvais mot de passe de chiffrement
- Fichier corrompu
- Version différente du logiciel

**Solution:**
Vérifiez bien votre mot de passe. Si le problème persiste, le fichier peut être corrompu.

### Problème: "L'application ne démarre pas"

**Solution:**
1. Vérifiez les logs dans `logs/safedoc.log`
2. Assurez-vous que le port 8501 n'est pas utilisé
3. Redémarrez l'application

---

## 📞 Support

### Besoin d'aide?

1. **Consultez ce manuel**
2. **Vérifiez les logs:** `logs/safedoc.log`
3. **Documentation API:** `docs/documentation_api.md`

### Signaler un bug

Si vous rencontrez un problème, incluez:
- Description du problème
- Étapes pour le reproduire
- Messages d'erreur
- Fichiers de logs

---

## 🎓 Conseils d'Utilisation

### Pour une utilisation optimale:

1. **Nommez vos documents clairement**
   - Utilisez des noms descriptifs
   - Incluez la date si pertinent

2. **Organisez par catégorie**
   - La classification automatique vous aide
   - Vérifiez et corrigez si nécessaire

3. **Scannez en haute qualité**
   - 300 DPI minimum recommandé
   - Bonne luminosité
   - Documents plats et droits

4. **Sauvegardez régulièrement**
   - Exportez vos documents importants
   - Gardez une copie du dossier `data/`

5. **Utilisez la recherche**
   - Recherche par nom
   - Recherche dans le contenu OCR
   - Filtres par catégorie

---

## 📊 Statistiques et Limites

### Limites Version Gratuite:
- 💾 Stockage: 500 MB
- 📄 Documents: Illimité
- 📤 Taille max par fichier: 50 MB
- ☁️ Cloud: Non

### Limites Version Premium:
- 💾 Stockage: 50 GB
- 📄 Documents: Illimité
- 📤 Taille max par fichier: 50 MB
- ☁️ Cloud: Oui

---

## 🚀 Prochaines Fonctionnalités

- 📱 Application mobile
- 🔄 Import/Export groupé
- 📊 Statistiques avancées
- 🏷️ Système d'étiquettes personnalisées
- 🔍 Recherche avancée avec filtres
- 📧 Notifications par email
- 🌐 Support multilingue

---

**🔒 SafeDoc - Vos documents, en sécurité, pour toujours.**

*Version 1.0.0 - Janvier 2024*
