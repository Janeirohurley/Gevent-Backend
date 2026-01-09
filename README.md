# GEvent Backend - API Django REST

Backend API pour l'application mobile GEvent, une plateforme de gestion d'événements au Burundi.

## 🚀 Fonctionnalités

- **Gestion des utilisateurs** : Inscription, connexion, profils
- **Événements** : Création, recherche, filtrage, participation
- **Billets électroniques** : Génération automatique avec QR codes en base64
- **Système de paiement** : Gestion des commandes et transactions
- **Favoris** : Sauvegarde d'événements favoris
- **Avis et évaluations** : Système de notation des événements
- **API REST complète** : Endpoints pour toutes les fonctionnalités

## 🛠️ Technologies

- **Django 5.0** : Framework web Python
- **Django REST Framework** : API REST
- **SQLite** : Base de données (développement)
- **QR Code** : Génération de codes QR en base64
- **Token Authentication** : Authentification par token
- **CORS** : Support pour applications frontend

## 📦 Installation

### 1. Cloner le projet
```bash
git clone <repository-url>
cd Gevent
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configurer la base de données
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Créer des données de test
```bash
python manage.py populate_db
```

### 6. Lancer le serveur
```bash
python manage.py runserver
```

L'API sera accessible à : `http://localhost:8000/api/`

## 🔧 Configuration

### Variables d'environnement (optionnel)
Créez un fichier `.env` pour la production :
```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=your-database-url
```

### Utilisateurs de test créés
- **Admin** : `admin` / `admin123`
- **Organisateur 1** : `organizer1` / `password123`
- **Organisateur 2** : `organizer2` / `password123`
- **Utilisateur** : `user1` / `password123`

## 📚 Documentation API

Consultez [API_DOCUMENTATION.md](API_DOCUMENTATION.md) pour la documentation complète des endpoints.

### Endpoints principaux

```
POST   /api/auth/register/           # Inscription
POST   /api/auth/login/              # Connexion
GET    /api/events/                  # Liste des événements
GET    /api/events/upcoming/         # Événements à venir
GET    /api/tickets/                 # Mes billets
POST   /api/tickets/validate_qr/     # Valider un QR code
GET    /api/categories/              # Catégories
POST   /api/orders/                  # Créer une commande
```

## 🎫 Système de QR Codes

Les billets génèrent automatiquement des QR codes en base64 contenant :
- Code du billet
- Informations de l'événement
- Détails du détenteur
- Date et siège

### Test des QR codes
```bash
python test_qrcode.py
```

## 🗂️ Structure du projet

```
Gevent/
├── events/                 # Application principale
│   ├── models.py          # Modèles de données
│   ├── serializers.py     # Sérialiseurs API
│   ├── views.py           # Vues API
│   ├── auth_views.py      # Vues d'authentification
│   ├── admin.py           # Interface admin
│   └── management/        # Commandes personnalisées
├── Gevent/                # Configuration Django
│   ├── settings.py        # Paramètres
│   └── urls.py           # URLs principales
├── requirements.txt       # Dépendances
├── test_qrcode.py        # Tests QR codes
└── README.md             # Ce fichier
```

## 🔒 Sécurité

- Authentification par token
- Validation des données d'entrée
- Protection CSRF
- Permissions par utilisateur
- Validation des QR codes

## 🚀 Déploiement

### Production avec PostgreSQL
1. Installer PostgreSQL
2. Modifier `DATABASES` dans `settings.py`
3. Configurer les variables d'environnement
4. Collecter les fichiers statiques : `python manage.py collectstatic`

### Docker (optionnel)
```dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🧪 Tests

### Tester l'API
```bash
# Test des QR codes
python test_qrcode.py

# Tests Django (à implémenter)
python manage.py test
```

### Exemples de requêtes
```bash
# Obtenir un token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "password123"}'

# Lister les événements
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/events/
```

## 📱 Frontend

Cette API est conçue pour être utilisée avec :
- Applications mobiles (React Native, Flutter)
- Applications web (React, Vue.js, Angular)
- Applications desktop

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Pour toute question ou support :
- Email : support@gevent.bi
- Documentation : [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

**GEvent** - Connecter les gens aux événements au Burundi 🇧🇮