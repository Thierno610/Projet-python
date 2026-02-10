# 🔒 SafeDoc - Coffre-fort Numérique Intelligent

## 🚀 Lancement Ultra-Rapide

```bash
python run_safedoc.py
```

C'est tout ! L'application se lance automatiquement à http://localhost:5000

---

## ✨ Caractéristiques

SafeDoc est une application Flask moderne pour la gestion sécurisée de documents avec :

- 📷 **OCR intelligent** - Extraction de texte depuis PDF et images
- 🔐 **Chiffrement AES-256** - Protection militaire de vos documents
- 🧠 **Classification automatique** - Organisation intelligente par catégorie
- 🏷️ **Système d'étiquettes** - Organisation personnalisée avec couleurs
- 📊 **Tableau de bord** - Statistiques et analyses en temps réel
- 📱 **Interface responsive** - Fonctionne sur tous les appareils

## 🛠️ Installation Automatique

Le lanceur `run_safedoc.py` gère automatiquement :
- ✅ Installation des dépendances manquantes
- ✅ Configuration de la base de données
- ✅ Création des dossiers nécessaires
- ✅ Mode dégradé si des modules optionnels manquent

## 🌐 Accès

Après lancement, accédez à :
- **URL locale** : http://localhost:5000
- **URL réseau** : http://192.168.1.192:5000 (si disponible)

## 📁 Structure du Projet

```
SafeDoc/
├── run_safedoc.py              # 🚀 Lanceur principal (utilisez celui-ci)
├── src/web/app_flask_optimized.py  # Application Flask optimisée
├── src/web/templates/          # Templates HTML
├── requirements_minimal.txt    # Dépendances essentielles
├── data/                       # Base de données SQLite
├── temp/                       # Fichiers temporaires
└── logs/                       # Journaux
```

## 🔧 Fonctionnalités

### 📊 Dashboard
- Métriques en temps réel
- Documents récents
- Statistiques de stockage

### 📤 Téléversement
- Support PDF, PNG, JPG, TIFF
- OCR automatique
- Classification intelligente
- Chiffrement immédiat

### 📚 Bibliothèque
- Recherche et filtrage
- Gestion des étiquettes
- Visualisation sécurisée
- Téléchargement déchiffré

### 📈 Analyses
- Graphiques d'utilisation
- Répartition par catégorie
- Tendances de stockage

## 🛡️ Sécurité

- **Chiffrement AES-256** pour tous les documents
- **Hachage bcrypt** pour les mots de passe
- **Session sécurisée** Flask
- **Validation stricte** des fichiers

## 📋 Dépendances

### Essentielles (installées automatiquement)
- Flask 3.0+
- SQLAlchemy 2.0+
- Tesseract OCR
- Pillow
- pdf2image
- Loguru
- python-dotenv

### Optionnelles
- spaCy (NLP avancé)
- Google Cloud Storage
- NLTK

## 🐛 Dépannage

### "ModuleNotFoundError"
➡️ **Solution** : Lancez `python run_safedoc.py` - il installe automatiquement les dépendances.

### "Port déjà utilisé"
➡️ **Solution** : Modifiez le port dans `run_safedoc.py` (ligne ~70)

### "Permission refusée"
➡️ **Solution** : Les dépendances s'installent automatiquement dans le répertoire utilisateur

## 🔄 Modes de fonctionnement

### 🚀 **Mode complet** (recommandé)
Toutes les fonctionnalités avec base de données SQLite et OCR complet.

### 🔄 **Mode dégradé** 
Si des dépendances optionnelles manquent, l'application fonctionne avec des données de démonstration.

## 📝 Développement

```bash
# Mode développement
python run_safedoc.py

# Installation manuelle des dépendances
pip install -r requirements_minimal.txt

# Installation complète (optionnel)
pip install -r requirements.txt
```

## 📄 Licence

Projet éducatif et de démonstration.

---

**SafeDoc - La solution moderne pour la gestion sécurisée de vos documents** 🔒

*Démarrage en 30 secondes - Aucune configuration manuelle requise* ⚡
