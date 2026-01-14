import qrcode
import base64
from io import BytesIO
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour GEvent
    """
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return self.username
    
class Category(models.Model):
    """
    Catégories d'événements (Musique, Sport, Théâtre, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Nom de l'icône
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Event(models.Model):
    """
    Modèle principal pour les événements
    """
    STATUS_CHOICES = [
        ('upcoming', 'À venir'),
        ('ongoing', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='events')
    image_url = models.ImageField(upload_to='events/', blank=True, null=True)

    # Informations de localisation
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    # Informations temporelles
    date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)  # Ex: "2h30"

    # Informations de tarification
    is_free = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Prix HT
    tva_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # TVA en %
    currency = models.CharField(max_length=3, default='BIF')  # Franc Burundais

    # Capacité et disponibilité
    total_capacity = models.IntegerField(default=0)
    available_seats = models.IntegerField(default=0)

    # Organisateur
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    organizer_name = models.CharField(max_length=255, blank=True, null=True)
    organizer_image = models.ImageField(upload_to='organizers/', blank=True, null=True)

    # Statut et métriques
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    is_popular = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'events'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['category', 'is_popular']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_sold_out(self):
        return self.available_seats <= 0
    
    @property
    def tva_amount(self):
        """Calcule le montant de la TVA"""
        if self.is_free:
            return 0
        from decimal import Decimal
        return (Decimal(str(self.price)) * Decimal(str(self.tva_rate))) / Decimal('100')
    
    @property
    def price_with_tva(self):
        from decimal import Decimal
        """Calcule le prix TTC (avec TVA)"""
        if self.is_free:
            return 0
        return Decimal(str(self.price)) + Decimal(str(self.tva_amount))

    
class EventImage(models.Model):
    """
    Images supplémentaires pour un événement
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='events/gallery/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'event_images'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.event.title}"
    
class Attendee(models.Model):
    """
    Participants confirmés à un événement
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attending_events')
    profile_image = models.ImageField(upload_to='attendees/', blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendees'
        unique_together = ['event', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"
    
class Ticket(models.Model):
    """
    Billets achetés par les utilisateurs
    """
    STATUS_CHOICES = [
        ('confirmed', 'Confirmé'),
        ('cancelled', 'Annulé'),
        ('used', 'Utilisé'),
        ('expired', 'Expiré'),
    ]

    code = models.CharField(max_length=50, unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')

    # Informations du détenteur
    holder_name = models.CharField(max_length=255)
    holder_email = models.EmailField()
    holder_phone = models.CharField(max_length=20, blank=True, null=True)

    # Informations du billet
    seat = models.CharField(max_length=50, blank=True, null=True)
    price= models.DecimalField(max_digits=10, decimal_places=2)  # Prix HT
    tva_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # TVA en %
    tva_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Montant TVA
    price_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Prix TTC
    currency = models.CharField(max_length=3, default='BIF')

    # QR Code pour validation (stocké en base64)
    qr_code = models.TextField(blank=True, null=True)  # Base64 encoded QR code

    # Statut et dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    purchase_date = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tickets'
        ordering = ['-purchase_date']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"Ticket {self.code} - {self.event.title}"

    def save(self, *args, **kwargs):
        if not self.code:
            # Générer un code unique
            import uuid
            self.code = f"TKT-{uuid.uuid4().hex[:12].upper()}"
        
        # Calculer automatiquement la TVA et le prix TTC
        if self.price:
            from decimal import Decimal
            self.tva_amount = (Decimal(str(self.price)) * Decimal(str(self.tva_rate))) / Decimal('100')
            self.price_ttc = Decimal(str(self.price)) + self.tva_amount
        
        # Générer le QR code en base64 si pas déjà présent
        if not self.qr_code:
            self.qr_code = self.generate_qr_code()
        
        super().save(*args, **kwargs)
    
    def generate_qr_code(self):
        """
        Génère un QR code en base64 contenant les informations du billet
        """
        # Créer les données du QR code
        qr_data = {
            'ticket_code': self.code,
            'event_title': self.event.title,
            'holder_name': self.holder_name,
            'event_date': self.event.date.isoformat() if self.event else None,
            'seat': self.seat or 'General',
            'price_ht': str(self.price),
            'tva_amount': str(self.tva_amount),
            'price_ttc': str(self.price_ttc)
        }
        
        # Convertir en chaîne JSON
        import json
        qr_string = json.dumps(qr_data, ensure_ascii=False)
        
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        
        # Créer l'image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir en base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_str}"
    
    @classmethod
    def validate_qr_code(cls, qr_data_string):
        """
        Valide un QR code et retourne le ticket correspondant
        """
        try:
            import json
            qr_data = json.loads(qr_data_string)
            ticket_code = qr_data.get('ticket_code')
            
            if not ticket_code:
                return None, "Code de billet manquant"
            
            try:
                ticket = cls.objects.get(code=ticket_code)
                
                # Vérifier le statut du billet
                if ticket.status == 'cancelled':
                    return None, "Ce billet a été annulé"
                elif ticket.status == 'used':
                    return None, "Ce billet a déjà été utilisé"
                elif ticket.status == 'expired':
                    return None, "Ce billet a expiré"
                
                return ticket, "Billet valide"
                
            except cls.DoesNotExist:
                return None, "Billet non trouvé"
                
        except json.JSONDecodeError:
            return None, "QR code invalide"
        except Exception as e:
            return None, f"Erreur de validation: {str(e)}"

class Order(models.Model):
    """
    Commandes de billets
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='orders')

    # Informations de paiement
    quantity = models.IntegerField(default=1)
    unit_price= models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)  # Prix unitaire HT
    tva_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # TVA en %
    total_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Total HT
    total_tva = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Total TVA
    total_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Total TTC
    currency = models.CharField(max_length=3, default='BIF')

    payment_method = models.CharField(max_length=50)  # Ex: "credit_card", "mobile_money"
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'payment_status']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Générer un numéro de commande unique
            import uuid
            from decimal import Decimal
            self.order_number = f"ORD-{uuid.uuid4().hex[:12].upper()}"
            self.payment_status = 'completed'  # Par défaut à complété pour simplification
        
        # Calculer automatiquement les totaux
        if self.quantity:
            from decimal import Decimal
            self.unit_price= Decimal(str(self.event.price)) if self.event else Decimal('0')
            self.total_ht = self.unit_price* Decimal(str(self.quantity))
            self.total_tva = (self.total_ht * Decimal(str(self.tva_rate))) / Decimal('100')
            self.total_ttc = self.total_ht + self.total_tva
        
        super().save(*args, **kwargs)
    
    def create_tickets(self):
        """Créer les billets pour cette commande basé sur la quantité"""
        if self.payment_status != 'completed':
            return []
        
        # Vérifier si les billets n'existent pas déjà
        existing_tickets = Ticket.objects.filter(
            user=self.user,
            event=self.event,
            purchase_date__date=self.created_at.date()
        ).count()
        
        if existing_tickets > 0:
            return Ticket.objects.filter(
                user=self.user,
                event=self.event,
                purchase_date__date=self.created_at.date()
            )
        
        tickets = []
        for i in range(self.quantity):
            seat_number = f"A{i+1}" if self.event.total_capacity > 0 else "General"
            
            ticket = Ticket.objects.create(
                event=self.event,
                user=self.user,
                holder_name=f"{self.user.first_name} {self.user.last_name}",
                holder_email=self.user.email,
                holder_phone=self.user.phone_number,
                seat=seat_number,
                price=self.unit_price,
                tva_rate=self.tva_rate
            )
            tickets.append(ticket)
        
        # Mettre à jour les sièges disponibles
        if self.event.available_seats >= self.quantity:
            self.event.available_seats -= self.quantity
            self.event.save()
        
        return tickets

class Review(models.Model):
    """
    Avis et évaluations des événements
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')

    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 étoiles
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        unique_together = ['event', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.rating}★)"
    


class Favorite(models.Model):
    """
    Événements favoris des utilisateurs
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorites'
        unique_together = ['user', 'event']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"