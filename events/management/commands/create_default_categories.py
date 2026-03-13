from django.core.management.base import BaseCommand
from events.models import Category

class Command(BaseCommand):
    help = 'Créer les catégories par défaut pour GEvent'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Musique', 'description': 'Concerts, festivals musicaux, spectacles live', 'icon': 'music'},
            {'name': 'Sport', 'description': 'Matchs, compétitions sportives, événements athlétiques', 'icon': 'sports'},
            {'name': 'Théâtre', 'description': 'Pièces de théâtre, spectacles dramatiques', 'icon': 'theater'},
            {'name': 'Conférence', 'description': 'Conférences, séminaires, formations professionnelles', 'icon': 'conference'},
            {'name': 'Festival', 'description': 'Festivals culturels, événements communautaires', 'icon': 'festival'},
            {'name': 'Exposition', 'description': 'Expositions d\'art, galeries, musées', 'icon': 'exhibition'},
            {'name': 'Gastronomie', 'description': 'Événements culinaires, dégustations, restaurants', 'icon': 'food'},
            {'name': 'Technologie', 'description': 'Événements tech, hackathons, innovations', 'icon': 'tech'},
            {'name': 'Éducation', 'description': 'Ateliers éducatifs, cours, formations', 'icon': 'education'},
            {'name': 'Autre', 'description': 'Autres types d\'événements', 'icon': 'other'}
        ]

        created_count = 0
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Catégorie "{category.name}" créée avec succès')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Catégorie "{category.name}" existe déjà')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n{created_count} nouvelles catégories créées sur {len(categories)} au total')
        )