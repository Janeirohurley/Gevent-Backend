#!/usr/bin/env python
"""
Script de test pour les catégories de tickets
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_ticket_categories():
    """Test des fonctionnalités de catégories de tickets"""
    
    # 1. Connexion pour obtenir un token
    login_data = {
        "username": "organizer1",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    if response.status_code == 200:
        token = response.json()['token']
        headers = {'Authorization': f'Token {token}'}
        print("✅ Connexion réussie")
    else:
        print("❌ Échec de connexion")
        return
    
    # 2. Créer un événement
    event_data = {
        "title": "Concert Test avec Catégories",
        "description": "Test des catégories de tickets",
        "category_id": 1,
        "location": "Bujumbura",
        "date": "2024-03-15T19:00:00Z",
        "is_free": False,
        "price": 10000,
        "total_capacity": 100
    }
    
    response = requests.post(f"{BASE_URL}/events/", json=event_data, headers=headers)
    if response.status_code == 201:
        event = response.json()
        event_id = event['id']
        print(f"✅ Événement créé: {event['title']}")
    else:
        print("❌ Échec création événement")
        return
    
    # 3. L'organisateur ajoute ses propres catégories personnalisées
    # Exemple : Concert de jazz avec catégories spécifiques
    categories = [
        {
            "event_id": event_id,
            "name": "Étudiant",
            "description": "Tarif réduit pour étudiants",
            "price": 5000,
            "capacity": 40,
            "color": "#17a2b8",
            "benefits": "Accès standard avec tarif étudiant",
            "order": 1
        },
        {
            "event_id": event_id,
            "name": "Standard",
            "description": "Accès normal au concert",
            "price": 15000,
            "capacity": 40,
            "color": "#28a745",
            "benefits": "Accès au concert, programme inclus",
            "order": 2
        },
        {
            "event_id": event_id,
            "name": "Premium",
            "description": "Première rangée avec meet & greet",
            "price": 35000,
            "capacity": 20,
            "color": "#dc3545",
            "benefits": "Première rangée, meet & greet avec l'artiste, boisson offerte",
            "order": 3
        }
    ]
    
    category_ids = []
    for cat_data in categories:
        response = requests.post(f"{BASE_URL}/ticket-categories/", json=cat_data, headers=headers)
        if response.status_code == 201:
            category = response.json()
            category_ids.append(category['id'])
            print(f"✅ Catégorie créée: {category['name']} - {category['price']} BIF")
        else:
            print(f"❌ Échec création catégorie: {cat_data['name']}")
    
    # 4. Vérifier les catégories de l'événement
    response = requests.get(f"{BASE_URL}/events/{event_id}/ticket_categories/", headers=headers)
    if response.status_code == 200:
        categories = response.json()
        print(f"✅ {len(categories)} catégories trouvées pour l'événement")
        for cat in categories:
            print(f"   - {cat['name']}: {cat['price']} BIF ({cat['available_seats']}/{cat['capacity']} places)")
    
    # 5. Créer une commande avec la catégorie "Standard"
    if category_ids:
        order_data = {
            "event_id": event_id,
            "ticket_category_id": category_ids[1],  # Standard
            "quantity": 1,
            "payment_method": "wallet"
        }
        
        response = requests.post(f"{BASE_URL}/orders/", json=order_data, headers=headers)
        if response.status_code == 201:
            order = response.json()
            print(f"✅ Commande créée: {order['order_number']}")
            print(f"   - Catégorie: Standard")
            print(f"   - Quantité: {order['quantity']}")
            print(f"   - Total: {order['total_ttc']} BIF")
        else:
            print("❌ Échec création commande")
            print(response.json())
    
    # 6. Vérifier les tickets créés
    response = requests.get(f"{BASE_URL}/tickets/", headers=headers)
    if response.status_code == 200:
        tickets = response.json()
        print(f"✅ {len(tickets)} ticket(s) trouvé(s)")
        for ticket in tickets:
            if 'ticket_category' in ticket and ticket['ticket_category']:
                print(f"   - {ticket['code']}: {ticket['ticket_category']['name']} - {ticket['seat']}")

if __name__ == "__main__":
    test_ticket_categories()