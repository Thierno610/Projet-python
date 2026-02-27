# 🔒 SafeDoc - Prérequis et Difficultés Rencontrées

Ce document récapitule les prérequis techniques nécessaires au fonctionnement du projet SafeDoc et les défis majeurs surmontés lors de son développement.

## 📋 Prérequis Techniques

### 1. Prérequis Système
*   **Système d'exploitation** : Windows, macOS ou Linux.
*   **Python** : Version 3.10 ou supérieure.
*   **Tesseract OCR** : Binaire installé sur le système pour la reconnaissance de caractères.
    *   *Windows* : Installeur exécutable (doit être configuré dans `.env`).
    *   *Linux/macOS* : Via le gestionnaire de paquets (`apt-get install tesseract-ocr`, `brew install tesseract`).
*   **Poppler** : Binaire nécessaire pour la conversion des fichiers PDF en images.
    *   *Windows* : À télécharger et ajouter au PATH système.
    *   *Linux/macOS* : Via le gestionnaire de paquets (`apt-get install poppler-utils`, `brew install poppler`).
*   **Réseau** :
    *   Port local `5000` ou `5001` disponible.
    *   Connexion internet pour le téléchargement initial des dépendances et l'utilisation de certaines API (Google Generative AI).

### 2. Dépendances Logicielles (Python)
Les dépendances complètes sont listées dans `requirements.txt`. Les principales sont :
*   **Application Web** : `Flask`, `Werkzeug`.
*   **Base de données** : `SQLAlchemy` (ORM), `Alembic` (migrations).
*   **Traitement d'images et OCR** : `Pillow` (PIL), `pdf2image`, `pytesseract`.
*   **Sécurité et Chiffrement** : `cryptography` (pour le chiffrement AES-256), `bcrypt` (hachage des mots de passe).
*   **Intelligence Artificielle** : `google-generativeai` (intégration Gemini).
*   **Utilitaires** : `python-dotenv` (variables d'environnement), `loguru` (journalisation avancée).

### 3. Configuration de l'Environnement (`.env`)
Le projet nécessite un fichier `.env` configuré à partir de `.env.example`. Les variables critiques incluent :
*   `MASTER_KEY` : Clé unique de chiffrement (32 caractères minimum) pour sécuriser les documents avec AES-256. Ne doit jamais être perdue ou partagée.
*   `SESSION_SECRET_KEY` : Clé secrète Flask pour sécuriser les sessions utilisateur.
*   `TESSERACT_PATH` : Chemin absolu vers l'exécutable Tesseract (surtout sur Windows).
*   `DATABASE_URL` : URL de connexion à la base de données (par défaut SQLite).
*   *Optionnel* : Identifiants Google (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`) pour les fonctionnalités cloud/premium.

---

## 🚧 Difficultés Surmontées

### 1. Migration de Streamlit vers Flask
L'un des défis majeurs a été la transformation complète du projet, initialement conçu avec Streamlit, vers le framework Flask.
*   **Défi** : Passer d'une interface générée automatiquement en Python à une architecture MVC avec des routes distinctes et des templates HTML.
*   **Résolution** : Création d'une structure de templates modulaires (`base.html`), implémentation de 16 routes fonctionnelles, et séparation claire entre la logique métier et l'interface utilisateur.

### 2. Gestion des Performances Frontend (Jinja2 vs JavaScript)
L'utilisation intensive de Jinja2 pour le rendu dynamique posait des problèmes de performance et de maintenabilité.
*   **Défi** : Des re-chargements complets de page qui nuisaient à l'expérience utilisateur, notamment pour des éléments dynamiques comme les barres de progression de stockage.
*   **Résolution** : Migration d'une grande partie de la logique de rendu vers **JavaScript moderne asynchrone** (Fetch API). Création d'endpoints API REST, permettant des mises à jour partielles du DOM, des animations fluides et une réduction significative de l'utilisation mémoire.

### 3. Structuration et Qualité du CSS
L'intégration du design a initialement souffert de l'utilisation de CSS inline et de styles éparpillés.
*   **Défi** : Erreurs de syntaxe fréquentes dans les templates, conflits de styles, et difficultés à maintenir un design responsif cohérent (notamment le *glassmorphism* et le thème sombre).
*   **Résolution** : Mise en place d'une architecture CSS professionnelle. Création d'un "design system" basé sur des variables CSS, regroupé dans des fichiers externes (`safedoc.css`), garantissant un code propre, sans erreurs et 100% responsif (mobile-first).

### 4. Traitement Documentaire et OCR
L'extraction de texte à partir de documents variés (PDF, images) présentait des obstacles techniques.
*   **Défi** : Gérer les dépendances système externes (Tesseract, Poppler) de manière transparente pour l'utilisateur, et assurer la stabilité du traitement sur différents formats.
*   **Résolution** : Implémentation de mécanismes robustes avec `pytesseract` et `pdf2image`, accompagnés d'un script de démarrage (`run_safedoc.py`) intelligent capable de détecter les environnements et de proposer un "mode dégradé" si certaines dépendances lourdes manquent.

### 5. Sécurisation des Données
La promesse d'un "coffre-fort numérique" impliquait des exigences strictes en matière de sécurité.
*   **Défi** : Implémenter un chiffrement fort systématique sans impacter drastiquement les performances lors du téléversement ou du téléchargement.
*   **Résolution** : Mise en place du chiffrement **AES-256** couplé à une gestion stricte des clés (`MASTER_KEY`) via les variables d'environnement, sécurisation des sessions Flask, et hachage des mots de passe avec `bcrypt`.

### 6. Évolution de la Base de Données
*   **Défi** : L'ajout de nouvelles fonctionnalités a nécessité des modifications du schéma de données existant, notamment lors de l'intégration du système d'étiquettes personnalisées.
*   **Résolution** : Utilisation d'`SQLAlchemy` et développement de scripts de migration automatique (`setup_db.py`, `migration_securite.py`) et de vérification dynamique (`fix_db_schema.py`) permettant de mettre à jour le schéma (ex: ajout de colonnes comme `utilisateur_id` à la table `etiquettes`) sans perte de données.
