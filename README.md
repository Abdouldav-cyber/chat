# 🤖 Chatbot RH - Fonction Publique

Chatbot intelligent pour la gestion des ressources humaines de la fonction publique.

## 📋 Fonctionnalités

### Pour les Employés
- 💬 **Chatbot intelligent** : Réponses automatiques sur les congés, la paie, les avantages sociaux
- 📅 **Gestion des congés** : Demande, suivi et annulation des congés
- 💰 **Demandes de remboursement** : Transport, frais professionnels
- 📄 **Attestations** : Demande d'attestations de travail et de salaire
- 🔔 **Notifications** : Alertes sur les échéances RH

### Pour les Gestionnaires RH
- 📊 **Dashboard** : Vue d'ensemble des demandes et statistiques
- ✅ **Validation** : Approuver ou refuser les demandes
- 👥 **Gestion des employés** : Consulter les profils et historiques
- 📈 **Analytics Chatbot** : Analyse des conversations et amélioration continue
- 🧠 **Gestion des intentions** : Configurer les réponses du chatbot

## 🛠️ Technologies

| Composant | Technologie |
|-----------|-------------|
| Backend | Flask (Python 3.10+) |
| NLP | SpaCy (fr_core_news_md) |
| Base de données | PostgreSQL |
| Frontend | HTML5, CSS3, JavaScript |

## 🚀 Installation

### 1. Prérequis
- Python 3.10+
- PostgreSQL 12+
- pip

### 2. Créer l'environnement virtuel
```powershell
cd Chatbot/chatbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances
```powershell
pip install -r requirements.txt
```

### 4. Télécharger le modèle SpaCy français
```powershell
python -m spacy download fr_core_news_md
```

### 5. Configurer la base de données

#### Créer la base PostgreSQL
```sql
CREATE DATABASE botrh;
```

#### Configurer les variables d'environnement
Modifier le fichier `.env` avec vos paramètres :
```env
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=postgres
DB_PASS=votre_mot_de_passe
DB_NAME=botrh
```

### 6. Initialiser la base de données
```powershell
python app.py
```
Puis accédez à : `http://localhost:5000/init-db`

### 7. Lancer l'application
```powershell
python app.py
```

L'application est accessible sur : **http://localhost:5000**

## 📁 Structure du projet

```
chatbot/
├── app.py                    # Application Flask principale
├── requirements.txt          # Dépendances Python
├── migrations.sql            # Scripts SQL PostgreSQL
├── .env                      # Variables d'environnement
│
├── app/
│   ├── controllers/          # Contrôleurs API
│   │   ├── chat_controller.py
│   │   ├── demandes_controller.py
│   │   ├── notifications_controller.py
│   │   └── gestionnaire_controller.py
│   │
│   ├── database/
│   │   └── connection.py     # Connexion PostgreSQL
│   │
│   └── services/
│       └── nlp_service.py    # Service NLP SpaCy
│
├── templates/                # Pages HTML
│   ├── index.html           # Page d'accueil
│   ├── chatbot.html         # Interface chatbot
│   ├── employe.html         # Espace employé
│   └── gestionnaire.html    # Dashboard RH
│
└── static/
    └── style.css            # Styles CSS
```

## 🔗 Routes disponibles

### Pages
| Route | Description |
|-------|-------------|
| `/` | Page d'accueil |
| `/chatbot` | Interface du chatbot |
| `/employe` | Espace employé |
| `/gestionnaire` | Dashboard gestionnaire RH |
| `/test-db` | Test connexion PostgreSQL |
| `/init-db` | Initialiser la base de données |

### API
| Route | Méthode | Description |
|-------|---------|-------------|
| `/chat` | POST | Envoyer un message au chatbot |
| `/api/demandes` | GET/POST | Lister/créer des demandes |
| `/api/demandes/traiter` | PUT | Approuver/refuser une demande |
| `/api/notifications` | GET | Lister les notifications |
| `/api/gestionnaire/stats` | GET | Statistiques du dashboard |
| `/api/gestionnaire/intents` | GET/POST | Gérer les intentions |

## 🧠 Intentions du Chatbot

Le chatbot comprend les intentions suivantes :

| Catégorie | Exemples de questions |
|-----------|----------------------|
| **Congés** | Solde, demande, types, annulation |
| **Paie** | Date de virement, fiche de paie, primes |
| **Avantages** | Mutuelle, transport, tickets restaurant |
| **Remboursements** | Demande, suivi |
| **Attestations** | Travail, salaire |
| **Général** | Salutations, aide, contact RH |

## 📊 Critères de Succès

- ✅ Réduction des requêtes RH manuelles
- ✅ Précision des réponses aux employés
- ✅ Satisfaction des utilisateurs (suivi via feedback)
- ✅ Interface de suivi pour les gestionnaires

## 👨‍💻 Auteur

Projet développé pour la gestion RH de la fonction publique.

---

© 2024 Chatbot RH - Fonction Publique
