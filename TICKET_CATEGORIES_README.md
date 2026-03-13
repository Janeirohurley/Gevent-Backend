# Nouvelles Fonctionnalités - Catégories de Tickets et Approbation Admin

## 🎫 Système de Catégories de Tickets

### Fonctionnalités ajoutées :

1. **Catégories multiples par événement** : VIP, VVIP, Basique, etc.
2. **Prix différenciés** par catégorie
3. **Capacités spécifiques** pour chaque catégorie
4. **QR codes enrichis** avec informations de catégorie
5. **Approbation admin** des événements

### Nouveaux Modèles :

#### TicketCategory
- `name` : Nom de la catégorie (VIP, VVIP, Basique)
- `description` : Description de la catégorie
- `price` : Prix HT de la catégorie
- `capacity` : Nombre de places pour cette catégorie
- `available_seats` : Places disponibles
- `color` : Couleur hex pour l'interface
- `benefits` : Avantages de cette catégorie
- `order` : Ordre d'affichage

### Modifications des Modèles Existants :

#### Event
- `is_approved` : Booléen pour l'approbation admin

#### Ticket
- `ticket_category` : Référence vers TicketCategory

#### Order
- `ticket_category` : Référence vers TicketCategory

## 🔧 Nouveaux Endpoints API

### Catégories de Tickets
```
GET    /api/ticket-categories/?event=<event_id>  # Liste des catégories d'un événement
POST   /api/ticket-categories/                   # Créer une catégorie (organisateur)
PUT    /api/ticket-categories/<id>/              # Modifier une catégorie
DELETE /api/ticket-categories/<id>/              # Supprimer une catégorie
```

### Gestion des Événements
```
GET    /api/events/<id>/ticket_categories/       # Catégories d'un événement
POST   /api/events/<id>/add_ticket_category/     # Ajouter une catégorie
GET    /api/events/pending_approval/             # Événements en attente (admin)
POST   /api/events/<id>/approve/                 # Approuver un événement (admin)
POST   /api/events/<id>/reject/                  # Rejeter un événement (admin)
```

## 📱 Utilisation

### 1. Créer un Événement avec Catégories

```python
# 1. Créer l'événement
event_data = {
    "title": "Concert VIP",
    "description": "Concert avec plusieurs catégories",
    "category_id": 1,
    "location": "Bujumbura",
    "date": "2024-03-15T19:00:00Z",
    "total_capacity": 100
}

# 2. Ajouter des catégories
categories = [
    {
        "name": "Basique",
        "price": 10000,
        "capacity": 60,
        "color": "#28a745"
    },
    {
        "name": "VIP", 
        "price": 20000,
        "capacity": 30,
        "color": "#ffc107"
    },
    {
        "name": "VVIP",
        "price": 30000, 
        "capacity": 10,
        "color": "#dc3545"
    }
]
```

### 2. Acheter un Ticket avec Catégorie

```python
order_data = {
    "event_id": 1,
    "ticket_category_id": 2,  # VIP
    "quantity": 2,
    "payment_method": "wallet"
}
```

### 3. QR Code Enrichi

Le QR code contient maintenant :
```json
{
    "ticket_code": "TKT-ABC123",
    "event_title": "Concert VIP",
    "ticket_category": "VIP",
    "category_color": "#ffc107",
    "holder_name": "John Doe",
    "seat": "V1",
    "price_ttc": "22000"
}
```

## 👨‍💼 Approbation Admin

### Workflow :
1. **Organisateur** crée un événement → `is_approved = False`
2. **Admin** voit les événements en attente via `/api/events/pending_approval/`
3. **Admin** approuve via `/api/events/<id>/approve/` → `is_approved = True`
4. **Utilisateurs** voient seulement les événements approuvés

### Permissions :
- **Utilisateurs normaux** : Voient seulement les événements approuvés
- **Staff/Admin** : Voient tous les événements
- **Organisateurs** : Voient leurs propres événements (approuvés ou non)

## 🚀 Migration et Commandes

### Appliquer les migrations :
```bash
python manage.py migrate
```

### Créer des catégories par défaut pour les événements existants :
```bash
python manage.py create_default_categories
```

### Tester les nouvelles fonctionnalités :
```bash
python test_ticket_categories.py
```

## 📊 Exemples d'Utilisation

### Interface Mobile - Sélection de Catégorie
```
┌─────────────────────────────────┐
│ Concert de Jazz - 15 Mars       │
├─────────────────────────────────┤
│ 🟢 Basique    10,000 BIF       │
│    60/60 places disponibles     │
│    ✓ Accès à l'événement       │
├─────────────────────────────────┤
│ 🟡 VIP        20,000 BIF       │
│    28/30 places disponibles     │
│    ✓ Places réservées          │
│    ✓ Rafraîchissements         │
├─────────────────────────────────┤
│ 🔴 VVIP       30,000 BIF       │
│    10/10 places disponibles     │
│    ✓ Service personnalisé      │
│    ✓ Cadeaux exclusifs         │
└─────────────────────────────────┘
```

### Scanner QR - Validation avec Catégorie
```
✅ TICKET VALIDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎫 TKT-VIP123456
🎵 Concert de Jazz
👤 Jean Dupont
📅 15 Mars 2024 - 19h00
🎯 Catégorie: VIP
💺 Siège: V12
💰 22,000 BIF (TTC)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🔒 Sécurité

- **Validation des permissions** : Seuls les organisateurs peuvent gérer leurs catégories
- **Vérification des stocks** : Impossible de vendre plus que la capacité
- **QR codes sécurisés** : Informations de catégorie intégrées
- **Approbation admin** : Contrôle de qualité des événements