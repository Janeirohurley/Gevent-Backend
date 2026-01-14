from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Cr\u00e9e le compte syst\u00e8me gcash pour les commissions'

    def handle(self, *args, **options):
        username = 'gcash'
        
        # V\u00e9rifier si le compte existe d\u00e9j\u00e0
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Le compte {username} existe d\u00e9j\u00e0'))
            return
        
        # Cr\u00e9er le compte gcash
        user = User.objects.create_user(
            username=username,
            email='gcash@gevent.bi',
            password='gcash_secure_password_2024',
            first_name='GEvent',
            last_name='Commission',
            is_staff=False,
            is_active=True,
            wallet_balance=0.00
        )
        
        self.stdout.write(self.style.SUCCESS(f'Compte {username} cr\u00e9\u00e9 avec succ\u00e8s'))
        self.stdout.write(self.style.SUCCESS(f'Email: {user.email}'))
        self.stdout.write(self.style.SUCCESS(f'Solde initial: {user.wallet_balance} BIF'))
