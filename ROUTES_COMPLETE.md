# 🚀 SafeDoc - Routes Flask Complètes

## 📋 Liste des routes disponibles

### 🏠 **Routes principales**
- `GET /` → Redirection vers dashboard ou connexion
- `GET /dashboard` → Tableau de bord principal
- `GET /upload` → Page de téléversement
- `GET /bibliotheque` → Bibliothèque de documents
- `GET /etiquettes` → Gestion des étiquettes (GET/POST)
- `GET /statistiques` → Page de statistiques
- `GET /premium` → Page premium

### 🔐 **Routes d'authentification**
- `GET/POST /connexion` → Connexion utilisateur
- `GET/POST /inscription` → Inscription nouvel utilisateur
- `GET/POST /mot-de-passe-oublie` → Mot de passe oublié
- `GET /deconnexion` → Déconnexion utilisateur

### 📄 **Routes documents**
- `GET /document/<int:doc_id>` → Visualisation d'un document
- `POST /document/<int:doc_id>/supprimer` → Suppression d'un document
- `POST /document/<int:doc_id>/telecharger` → Téléchargement déchiffré

### 🔌 **Routes API**
- `GET /api/etiquettes` → API JSON des étiquettes
- `GET /api/statistiques` → API JSON des statistiques

## ✅ **Fonctionnalités de chaque route**

### 🏠 **Dashboard**
- Affiche les métriques utilisateur
- Liste des documents récents
- Statistiques de stockage
- Navigation rapide

### 📤 **Upload**
- Formulaire de téléversement
- Support multiples formats
- Validation des fichiers
- Traitement OCR

### 📚 **Bibliothèque**
- Liste complète des documents
- Filtres par catégorie/étiquette
- Recherche plein texte
- Actions sur documents

### 🏷️ **Étiquettes**
- **GET** : Affiche la liste des étiquettes
- **POST** : Créer/supprimer des étiquettes
- Formulaire de création avec couleur
- Confirmation de suppression

### 📊 **Statistiques**
- Graphiques d'utilisation
- Répartition par catégorie
- Tendances de stockage
- Métriques détaillées

### 🔐 **Authentification**
- **Connexion** : Formulaire avec validation
- **Inscription** : Création de compte
- **Mot de passe oublié** : Récupération
- **Déconnexion** : Nettoyage session

### 📄 **Documents**
- **Visualisation** : Détails du document
- **Suppression** : Confirmation et suppression
- **Téléchargement** : Déchiffrement et download

### 🔌 **API**
- **Étiquettes** : JSON pour interactions AJAX
- **Statistiques** : Données en temps réel

## 🔄 **Flux de navigation**

1. **Accueil** → `/` → Redirection intelligente
2. **Connexion** → `/connexion` → `/dashboard`
3. **Dashboard** → Navigation vers toutes les fonctionnalités
4. **Déconnexion** → `/deconnexion` → `/connexion`

## 🛡️ **Sécurité des routes**

- **Protection** : Vérification session utilisateur
- **Redirection** : Auto-redirection si non connecté
- **Validation** : Input validation sur tous les formulaires
- **Flash messages** : Feedback utilisateur

## 🎯 **Points d'accès**

- **URL principale** : http://localhost:5000
- **API endpoints** : `/api/*`
- **Templates** : `/templates/*.html`

---

**Toutes les routes sont fonctionnelles et testées** ✅
