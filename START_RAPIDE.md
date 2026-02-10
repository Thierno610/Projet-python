# 🚀 SafeDoc - Lancement Rapide et Sans Erreur

## ⚡ Lancement en 1 commande

```bash
python run_safedoc.py
```

C'est tout ! 🎉

## ✅ Ce que fait le lanceur optimisé

### 📦 **Vérification automatique des dépendances**
- Détecte les modules manquants
- Les installe automatiquement
- Pas d'erreur de `ModuleNotFoundError`

### 🗂️ **Configuration automatique**
- Crée le fichier `.env` si nécessaire
- Crée les dossiers `data/`, `temp/`, `logs/`
- Initialise la base de données SQLite

### 🔄 **Mode dégradé intelligent**
- Si un module optionnel manque (spaCy, google-cloud) → mode démonstration
- L'application fonctionne toujours avec les fonctionnalités de base
- Messages clairs pour indiquer ce qui fonctionne

### 🚀 **Performance optimisée**
- `use_reloader=False` pour éviter les redémarrages multiples
- Import conditionnel pour accélérer le démarrage
- Gestion d'erreur silencieuse

## 🌐 Accès à l'application

Une fois lancée, l'application est accessible à :
- **URL principale** : http://localhost:5000
- **URL réseau** : http://192.168.1.192:5000

## 📋 Fonctionnalités disponibles

### ✅ **Toujours disponibles**
- 📊 Dashboard avec métriques
- 📤 Téléversement de documents
- 📚 Bibliothèque avec filtres
- 🏷️ Gestion des étiquettes
- 📈 Statistiques et graphiques
- 🔐 Chiffrement AES-256
- 📷 OCR sur PDF et images

### ⚠️ **Mode dégradé si dépendances manquantes**
- 🧠 NLP avancé (spaCy)
- ☁️ Stockage cloud Google Drive
- 📊 Classification intelligente avancée

## 🔧 Si vous voulez toutes les fonctionnalités

```bash
# Installer les dépendances optionnelles
pip install spacy
python -m spacy download fr_core_news_md
pip install google-cloud-storage google-auth
pip install nltk
```

## 📁 Fichiers importants

- `run_safedoc.py` - **Lanceur principal** (utilisez celui-ci)
- `src/web/app_flask_optimized.py` - Application optimisée
- `requirements_minimal.txt` - Dépendances essentielles
- `.env` - Configuration (créé automatiquement)

## 🐛 Dépannage

### "ModuleNotFoundError" → Résolu automatiquement
Le lanceur installe les dépendances manquantes automatiquement.

### "Base de données erreur" → Résolu automatiquement
Les dossiers et tables sont créés automatiquement.

### "Port déjà utilisé" → Changez le port
```bash
# Dans run_safedoc.py, changez port=5000 vers port=5001
```

### "Permission refusée" → Utilisez l'installation utilisateur
Les dépendances sont installées dans le répertoire utilisateur automatiquement.

## 🎯 Avantages de cette version

1. **🚀 Ultra-rapide** : 1 commande et ça démarre
2. **🛡️ Sans erreur** : Gère automatiquement les problèmes
3. **🔄 Intelligent** : Mode dégradé si quelque chose manque
4. **📱 Complet** : Toutes les fonctionnalités essentielles
5. **🔧 Maintenable** : Code clair et modulaire

---

**SafeDoc est maintenant prêt en 30 secondes !** ⚡

Lancez simplement : `python run_safedoc.py`
