from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from events.models import Category, Event
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Création des données de test...')
        
        # Créer un superutilisateur si il n'existe pas
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@gevent.com',
                password='admin123',
                first_name='Admin',
                last_name='GEvent'
            )
            self.stdout.write(self.style.SUCCESS('Superutilisateur créé: admin/admin123'))

        # Créer des catégories
        categories_data = [
            {'name': 'Musique', 'description': 'Concerts et événements musicaux', 'icon': 'music'},
            {'name': 'Sport', 'description': 'Événements sportifs', 'icon': 'sports'},
            {'name': 'Théâtre', 'description': 'Pièces de théâtre et spectacles', 'icon': 'theater'},
            {'name': 'Conférence', 'description': 'Conférences et séminaires', 'icon': 'conference'},
            {'name': 'Festival', 'description': 'Festivals culturels', 'icon': 'festival'},
            {'name': 'Exposition', 'description': 'Expositions et galeries', 'icon': 'exhibition'},
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon']
                }
            )
            if created:
                self.stdout.write(f'Catégorie créée: {category.name}')

        # Créer des utilisateurs de test
        test_users = [
            {'username': 'organizer1', 'email': 'org1@test.com', 'first_name': 'Jean', 'last_name': 'Dupont'},
            {'username': 'organizer2', 'email': 'org2@test.com', 'first_name': 'Marie', 'last_name': 'Martin'},
            {'username': 'user1', 'email': 'user1@test.com', 'first_name': 'Pierre', 'last_name': 'Durand'},
        ]

        for user_data in test_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'phone_number': '+25779123456'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Utilisateur créé: {user.username}')

        # Créer des événements de test
        organizer = User.objects.get(username='organizer1')
        music_category = Category.objects.get(name='Musique')
        sport_category = Category.objects.get(name='Sport')

        events_data = [
            {
                'title': 'Concert de Jazz au Centre Culturel',
                'description': 'Une soirée exceptionnelle avec les meilleurs musiciens de jazz du Burundi.',
                'category': music_category,
                'location': 'Centre Culturel Français, Bujumbura',
                'date': timezone.now() + timedelta(days=15),
                'end_date': timezone.now() + timedelta(days=15, hours=3),
                'duration': '3h',
                'is_free': False,
                'price': 15000,
                'total_capacity': 200,
                'available_seats': 150,
                'organizer': organizer,
                'organizer_name': 'Centre Culturel Français',
                'status': 'upcoming',
                'is_popular': True,
            },
            {
                'title': 'Match de Football - Vital\'O vs Prince Louis',
                'description': 'Match de championnat national entre deux équipes phares.',
                'category': sport_category,
                'location': 'Stade Prince Louis Rwagasore, Bujumbura',
                'date': timezone.now() + timedelta(days=7),
                'end_date': timezone.now() + timedelta(days=7, hours=2),
                'duration': '90min',
                'is_free': False,
                'price': 5000,
                'total_capacity': 5000,
                'available_seats': 3500,
                'organizer': organizer,
                'organizer_name': 'Fédération de Football du Burundi',
                'status': 'upcoming',
                'is_popular': True,
            },
            {
                'title': 'Festival des Arts de Gitega',
                'description': 'Célébration de la culture burundaise avec danses, musiques et artisanat.',
                'category': Category.objects.get(name='Festival'),
                'location': 'Place de l\'Indépendance, Gitega',
                'date': timezone.now() + timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=32),
                'duration': '3 jours',
                'is_free': True,
                'price': 0,
                'total_capacity': 1000,
                'available_seats': 1000,
                'organizer': organizer,
                'organizer_name': 'Ministère de la Culture',
                'status': 'upcoming',
                'is_popular': False,
            }
        ]

        for event_data in events_data:
            event, created = Event.objects.get_or_create(
                title=event_data['title'],
                defaults=event_data
            )
            if created:
                self.stdout.write(f'Événement créé: {event.title}')

        self.stdout.write(self.style.SUCCESS('Base de données peuplée avec succès!'))