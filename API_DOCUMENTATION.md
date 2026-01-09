# GEvent API Documentation

## Base URL
```
http://localhost:8000/api/
```

## Authentification

### 1. Inscription
```http
POST /api/auth/register/
Content-Type: application/json

{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+25779123456"
}
```

**Réponse:**
```json
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+25779123456"
    }
}
```

### 2. Connexion
```http
POST /api/auth/login/
Content-Type: application/json

{
    "username": "testuser",
    "password": "password123"
}
```

### 3. Déconnexion
```http
POST /api/auth/logout/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

## Événements

### 1. Liste des événements
```http
GET /api/events/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Paramètres de filtrage:**
- `category`: ID de la catégorie
- `status`: upcoming, ongoing, completed, cancelled
- `is_free`: true/false
- `is_popular`: true/false
- `search`: recherche dans titre, description, location

### 2. Événements à venir
```http
GET /api/events/upcoming/
```

### 3. Événements populaires
```http
GET /api/events/popular/
```

### 4. Détails d'un événement
```http
GET /api/events/{id}/
```

### 5. Rejoindre un événement
```http
POST /api/events/{id}/join/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### 6. Quitter un événement
```http
DELETE /api/events/{id}/leave/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

## Billets

### 1. Mes billets
```http
GET /api/tickets/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### 2. Billets à venir
```http
GET /api/tickets/upcoming/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### 3. Valider un QR code
```http
POST /api/tickets/validate_qr/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json

{
    "qr_data": "{\"ticket_code\": \"TKT-ABC123\", \"event_title\": \"Concert\", ...}"
}
```

**Réponse (succès):**
```json
{
    "valid": true,
    "message": "Billet valide",
    "ticket": {
        "id": 1,
        "code": "TKT-ABC123",
        "event": {...},
        "holder_name": "John Doe",
        "status": "confirmed",
        "qr_code": "data:image/png;base64,iVBORw0KGgo..."
    }
}
```

### 4. Utiliser un billet
```http
POST /api/tickets/{id}/use_ticket/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### 5. Annuler un billet
```http
POST /api/tickets/{id}/cancel/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

## Commandes

### 1. Créer une commande
```http
POST /api/orders/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json

{
    "event": 1,
    "quantity": 2,
    "unit_price": "15000.00",
    "total_amount": "30000.00",
    "payment_method": "mobile_money"
}
```

### 2. Mettre à jour le paiement
```http
PUT /api/orders/{id}/payment/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json

{
    "payment_status": "completed",
    "transaction_id": "TXN123456789"
}
```

## Favoris

### 1. Mes favoris
```http
GET /api/favorites/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### 2. Ajouter/Retirer des favoris
```http
POST /api/favorites/toggle/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json

{
    "event_id": 1
}
```

## Avis

### 1. Avis d'un événement
```http
GET /api/reviews/?event=1
```

### 2. Ajouter un avis
```http
POST /api/reviews/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json

{
    "event": 1,
    "rating": 5,
    "comment": "Excellent événement!"
}
```

## Catégories

### 1. Liste des catégories
```http
GET /api/categories/
```

### 2. Événements par catégorie
```http
GET /api/categories/{id}/events/
```

## Format des QR Codes

Les QR codes contiennent des données JSON avec les informations suivantes:

```json
{
    "ticket_code": "TKT-ABC123456789",
    "event_title": "Concert de Jazz",
    "holder_name": "John Doe",
    "event_date": "2026-02-15T20:00:00Z",
    "seat": "A12",
    "price": "15000.00"
}
```

Le QR code est stocké en base64 dans le format:
```
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAjoA...
```

## Codes d'erreur

- `400 Bad Request`: Données invalides
- `401 Unauthorized`: Token manquant ou invalide
- `403 Forbidden`: Permissions insuffisantes
- `404 Not Found`: Ressource non trouvée
- `500 Internal Server Error`: Erreur serveur

## Pagination

Les listes sont paginées avec 20 éléments par page par défaut.

**Réponse paginée:**
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/events/?page=2",
    "previous": null,
    "results": [...]
}
```