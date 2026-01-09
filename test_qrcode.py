#!/usr/bin/env python
"""
Script de test pour les QR codes des billets
"""
import os
import sys
import django

# Configuration Django
sys.path.append('/home/ndikumana/Documents/Python/Django/Gevent')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Gevent.settings')
django.setup()

from events.models import Ticket, Event, User, Order
from django.utils import timezone
import json

def test_qr_code_generation():
    """Test de génération de QR code"""
    print("=== Test de génération de QR code ===")
    
    # Récupérer un événement et un utilisateur
    try:
        event = Event.objects.first()
        user = User.objects.get(username='user1')
        
        if not event or not user:
            print("Erreur: Événement ou utilisateur non trouvé")
            return
        
        # Créer un billet de test
        ticket = Ticket.objects.create(
            event=event,
            user=user,
            holder_name=f"{user.first_name} {user.last_name}",
            holder_email=user.email,
            holder_phone=user.phone_number,
            seat="A12",
            price=event.price
        )
        
        print(f"Billet créé: {ticket.code}")
        print(f"QR Code généré: {'Oui' if ticket.qr_code else 'Non'}")
        
        if ticket.qr_code:
            print(f"Longueur du QR code: {len(ticket.qr_code)} caractères")
            print(f"Début du QR code: {ticket.qr_code[:50]}...")
        
        return ticket
        
    except Exception as e:
        print(f"Erreur lors de la création du billet: {e}")
        return None

def test_qr_code_validation(ticket):
    """Test de validation de QR code"""
    print("\n=== Test de validation de QR code ===")
    
    if not ticket or not ticket.qr_code:
        print("Pas de billet ou QR code pour tester")
        return
    
    # Extraire les données du QR code (simuler le scan)
    try:
        # Le QR code contient les données JSON
        qr_data = {
            'ticket_code': ticket.code,
            'event_title': ticket.event.title,
            'holder_name': ticket.holder_name,
            'event_date': ticket.event.date.isoformat(),
            'seat': ticket.seat or 'General',
            'price': str(ticket.price)
        }
        
        qr_string = json.dumps(qr_data, ensure_ascii=False)
        print(f"Données QR simulées: {qr_string}")
        
        # Tester la validation
        validated_ticket, message = Ticket.validate_qr_code(qr_string)
        
        print(f"Validation: {'Succès' if validated_ticket else 'Échec'}")
        print(f"Message: {message}")
        
        if validated_ticket:
            print(f"Billet validé: {validated_ticket.code}")
            print(f"Statut: {validated_ticket.status}")
        
        return validated_ticket
        
    except Exception as e:
        print(f"Erreur lors de la validation: {e}")
        return None

def test_ticket_usage(ticket):
    """Test d'utilisation du billet"""
    print("\n=== Test d'utilisation du billet ===")
    
    if not ticket:
        print("Pas de billet pour tester")
        return
    
    print(f"Statut avant utilisation: {ticket.status}")
    
    # Marquer comme utilisé
    if ticket.status == 'confirmed':
        ticket.status = 'used'
        ticket.used_at = timezone.now()
        ticket.save()
        print(f"Billet marqué comme utilisé à: {ticket.used_at}")
    
    # Tester la validation après utilisation
    qr_data = {
        'ticket_code': ticket.code,
        'event_title': ticket.event.title,
        'holder_name': ticket.holder_name,
        'event_date': ticket.event.date.isoformat(),
        'seat': ticket.seat or 'General',
        'price': str(ticket.price)
    }
    
    qr_string = json.dumps(qr_data, ensure_ascii=False)
    validated_ticket, message = Ticket.validate_qr_code(qr_string)
    
    print(f"Validation après utilisation: {'Succès' if validated_ticket else 'Échec'}")
    print(f"Message: {message}")

def main():
    """Fonction principale"""
    print("Démarrage des tests QR Code...")
    
    # Test 1: Génération
    ticket = test_qr_code_generation()
    
    # Test 2: Validation
    validated_ticket = test_qr_code_validation(ticket)
    
    # Test 3: Utilisation
    test_ticket_usage(validated_ticket)
    
    print("\n=== Tests terminés ===")

if __name__ == "__main__":
    main()