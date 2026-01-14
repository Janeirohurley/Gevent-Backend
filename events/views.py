from rest_framework import viewsets, filters, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Event, Category, Attendee, Ticket, Order, Review, Favorite, WalletTransaction
from .serializers import (
    EventSerializer, CategorySerializer, AttendeeSerializer,
    TicketSerializer, OrderSerializer, ReviewSerializer,
    FavoriteSerializer, UserSerializer, WalletTransactionSerializer
)

User = get_user_model()

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'is_free', 'is_popular']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'price', 'rating', 'created_at']
    ordering = ['-date']

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Événements à venir"""
        upcoming_events = self.queryset.filter(
            status='upcoming',
            date__gte=timezone.now()
        ).order_by('date')
        serializer = self.get_serializer(upcoming_events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Événements populaires"""
        popular_events = self.queryset.filter(is_popular=True)
        serializer = self.get_serializer(popular_events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        """Liste des participants"""
        event = self.get_object()
        attendees = event.attendees.all()
        serializer = AttendeeSerializer(attendees, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Rejoindre un événement"""
        event = self.get_object()
        attendee, created = Attendee.objects.get_or_create(
            event=event,
            user=request.user
        )
        if created:
            return Response({'message': 'Vous avez rejoint l\'événement'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Vous participez déjà à cet événement'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def leave(self, request, pk=None):
        """Quitter un événement"""
        event = self.get_object()
        try:
            attendee = Attendee.objects.get(event=event, user=request.user)
            attendee.delete()
            return Response({'message': 'Vous avez quitté l\'événement'}, status=status.HTTP_200_OK)
        except Attendee.DoesNotExist:
            return Response({'message': 'Vous ne participez pas à cet événement'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """Événements organisés par l'utilisateur connecté"""
        my_events = self.queryset.filter(organizer=request.user).exclude(status='deleted')
        serializer = self.get_serializer(my_events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel_event(self, request, pk=None):
        """Annuler un événement - remboursement 100% (55% gcash + 45% organisateur)"""
        event = self.get_object()
        
        if event.organizer != request.user:
            return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)
        
        if event.status in ['cancelled', 'completed', 'deleted']:
            return Response({'error': 'Cet événement ne peut pas être annulé'}, status=status.HTTP_400_BAD_REQUEST)
        
        from decimal import Decimal
        
        tickets = Ticket.objects.filter(event=event, status='confirmed')
        refunded_count = 0
        total_refunded = Decimal('0')
        
        # Récupérer le compte gcash
        try:
            gcash_user = User.objects.get(username='gcash')
        except User.DoesNotExist:
            return Response({'error': 'Compte système gcash introuvable'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        for ticket in tickets:
            # Prix de base (HT) et commission
            base_price = Decimal(str(ticket.price))
            commission = base_price * Decimal('0.10')
            total_paid = base_price + commission  # 110% du prix de base
            
            # Vérifier les soldes
            if gcash_user.wallet_balance < commission:
                return Response({'error': f'Solde gcash insuffisant pour rembourser le billet {ticket.code}'}, status=status.HTTP_400_BAD_REQUEST)
            if event.organizer.wallet_balance < base_price:
                return Response({'error': f'Solde organisateur insuffisant pour rembourser le billet {ticket.code}'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Rembourser 110% à l'acheteur (100% prix de base + 10% commission)
            buyer_balance_before = ticket.user.wallet_balance
            ticket.user.wallet_balance += total_paid
            ticket.user.save()
            
            WalletTransaction.objects.create(
                user=ticket.user,
                transaction_type='refund',
                amount=total_paid,
                balance_before=buyer_balance_before,
                balance_after=ticket.user.wallet_balance,
                description=f"Remboursement 110% - Événement annulé: {event.title}",
                ticket=ticket
            )
            
            # Déduire 10% de gcash (commission)
            gcash_balance_before = gcash_user.wallet_balance
            gcash_user.wallet_balance -= commission
            gcash_user.save()
            
            WalletTransaction.objects.create(
                user=gcash_user,
                transaction_type='refund',
                amount=-commission,
                balance_before=gcash_balance_before,
                balance_after=gcash_user.wallet_balance,
                description=f"Remboursement commission 10% - Événement annulé: {event.title} - Billet {ticket.code}",
                ticket=ticket
            )
            
            # Déduire 100% de l'organisateur (prix de base)
            organizer_balance_before = event.organizer.wallet_balance
            event.organizer.wallet_balance -= base_price
            event.organizer.save()
            
            WalletTransaction.objects.create(
                user=event.organizer,
                transaction_type='refund',
                amount=-base_price,
                balance_before=organizer_balance_before,
                balance_after=event.organizer.wallet_balance,
                description=f"Remboursement 100% - Événement annulé: {event.title} - Billet {ticket.code}",
                ticket=ticket
            )
            
            # Annuler le billet
            ticket.status = 'cancelled'
            ticket.cancelled_at = timezone.now()
            ticket.save()
            
            refunded_count += 1
            total_refunded += total_paid
        
        # Restaurer les sièges
        event.available_seats = event.total_capacity
        event.status = 'cancelled'
        event.save()
        
        return Response({
            'message': 'Événement annulé avec succès',
            'refunded_tickets': refunded_count,
            'total_refunded': str(total_refunded)
        })
    
    @action(detail=True, methods=['delete'])
    def soft_delete(self, request, pk=None):
        """Soft delete d'un événement (change le statut à deleted)"""
        event = self.get_object()
        
        if event.organizer != request.user:
            return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)
        
        if event.status == 'deleted':
            return Response({'error': 'Cet événement est déjà supprimé'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier s'il y a des billets vendus
        tickets_sold = Ticket.objects.filter(event=event, status='confirmed').count()
        if tickets_sold > 0:
            return Response({
                'error': f'Impossible de supprimer. {tickets_sold} billet(s) vendu(s). Annulez l\'événement d\'abord.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        event.status = 'deleted'
        event.save()
        
        return Response({'message': 'Événement supprimé avec succès'})
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Changer le statut d'un événement"""
        event = self.get_object()
        
        if event.organizer != request.user:
            return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)
        
        new_status = request.data.get('status')
        if new_status not in ['upcoming', 'ongoing', 'completed']:
            return Response({'error': 'Statut invalide'}, status=status.HTTP_400_BAD_REQUEST)
        
        event.status = new_status
        event.save()
        
        serializer = self.get_serializer(event)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        """Upload multiple images for an event"""
        event = self.get_object()
        
        # Vérifier que l'utilisateur est l'organisateur
        if event.organizer != request.user:
            return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)
        
        images = request.FILES.getlist('images')
        if not images:
            return Response({'error': 'Aucune image fournie'}, status=status.HTTP_400_BAD_REQUEST)
        
        from .models import EventImage
        uploaded_images = []
        
        for image in images:
            event_image = EventImage.objects.create(
                event=event,
                image=image,
                caption=request.data.get('caption', ''),
                order=EventImage.objects.filter(event=event).count()
            )
            uploaded_images.append({
                'id': event_image.id,
                'image': event_image.image.url,
                'caption': event_image.caption,
                'order': event_image.order
            })
        
        return Response({
            'message': f'{len(uploaded_images)} image(s) uploadée(s) avec succès',
            'images': uploaded_images
        }, status=status.HTTP_201_CREATED)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Événements par catégorie"""
        category = self.get_object()
        events = category.events.all()
        serializer = EventSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)

class TicketViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TicketSerializer
    
    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Billets à venir"""
        tickets = self.get_queryset().filter(
            status='confirmed',
            event__date__gte=timezone.now()
        )
        serializer = self.get_serializer(tickets, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Billets terminés"""
        tickets = self.get_queryset().filter(
            status__in=['used', 'expired'],
            event__date__lt=timezone.now()
        )
        serializer = self.get_serializer(tickets, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annuler un billet - remboursement de 45% du prix HT depuis le compte de l'organisateur"""
        ticket = self.get_object()
        if ticket.status != 'confirmed':
            return Response({'message': 'Ce billet ne peut pas être annulé'}, status=status.HTTP_400_BAD_REQUEST)
        
        from decimal import Decimal
        
        # Remboursement de 45% du prix HT (prix de base sans commission)
        refund_rate = Decimal('0.45')
        refund_amount = Decimal(str(ticket.price)) * refund_rate
        
        # Vérifier que l'organisateur a assez de fonds
        organizer = ticket.event.organizer
        if organizer.wallet_balance < refund_amount:
            return Response({'error': 'Solde insuffisant de l\'organisateur pour le remboursement'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Rembourser 45% à l'acheteur
        buyer_balance_before = ticket.user.wallet_balance
        ticket.user.wallet_balance += refund_amount
        ticket.user.save()
        
        WalletTransaction.objects.create(
            user=ticket.user,
            transaction_type='refund',
            amount=refund_amount,
            balance_before=buyer_balance_before,
            balance_after=ticket.user.wallet_balance,
            description=f"Remboursement 45% - Billet {ticket.code} - {ticket.event.title}",
            ticket=ticket
        )
        
        # Déduire 45% de l'organisateur
        organizer_balance_before = organizer.wallet_balance
        organizer.wallet_balance -= refund_amount
        organizer.save()
        
        WalletTransaction.objects.create(
            user=organizer,
            transaction_type='refund',
            amount=-refund_amount,
            balance_before=organizer_balance_before,
            balance_after=organizer.wallet_balance,
            description=f"Remboursement 45% client - Billet {ticket.code} - {ticket.event.title}",
            ticket=ticket
        )
        
        # Annuler le billet
        ticket.status = 'cancelled'
        ticket.cancelled_at = timezone.now()
        ticket.save()
        
        # Libérer le siège
        ticket.event.available_seats += 1
        ticket.event.save()
        
        return Response({'message': f'Billet annulé - Remboursement de {refund_amount} BIF (45%)'})
    
    @action(detail=False, methods=['post'])
    def validate_qr(self, request):
        """Valider un QR code - seuls les organisateurs peuvent valider leurs billets"""
        qr_data = request.data.get('qr_data')
        if not qr_data:
            return Response({'error': 'Données QR manquantes'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket, message = Ticket.validate_qr_code(qr_data)
        
        if ticket:
            # Vérifier que l'utilisateur est l'organisateur de l'événement
            if ticket.event.organizer != request.user:
                return Response({
                    'valid': False,
                    'message': 'Vous n\'êtes pas autorisé à valider ce billet'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Vérifier le statut de l'événement
            if ticket.event.status != 'ongoing':
                status_messages = {
                    'upcoming': 'L\'événement n\'a pas encore commencé',
                    'completed': 'L\'événement est déjà terminé',
                    'cancelled': 'L\'événement a été annulé',
                    'deleted': 'L\'événement a été supprimé'
                }
                return Response({
                    'valid': False,
                    'message': status_messages.get(ticket.event.status, 'L\'événement n\'est pas en cours')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.get_serializer(ticket)
            if ticket.status == 'confirmed':
                ticket.status = 'used'
                ticket.used_at = timezone.now()
                ticket.save()
            
            return Response({
                'valid': True,
                'message': message,
                'ticket': serializer.data
            })
        else:
            return Response({
                'valid': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)
    


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Créer une commande et générer automatiquement les billets si paiement immédiat"""
        order = serializer.save(user=self.request.user)
        
        if order.payment_status == 'completed':
            try:
                tickets = order.create_tickets()
                if not tickets:
                    order.payment_status = 'failed'
                    order.save()
                    raise serializers.ValidationError("Solde insuffisant")
            except ValueError as e:
                order.payment_status = 'failed'
                order.save()
                raise serializers.ValidationError(str(e))

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except serializers.ValidationError as e:
            return Response({'error': str(e.detail[0]) if isinstance(e.detail, list) else str(e.detail)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def payment(self, request, pk=None):
        """Mettre à jour le statut de paiement"""
        order = self.get_object()
        payment_status = request.data.get('payment_status')
        transaction_id = request.data.get('transaction_id')
        
        if payment_status in ['completed', 'failed', 'refunded']:
            order.payment_status = payment_status
            if transaction_id:
                order.transaction_id = transaction_id
            if payment_status == 'completed':
                order.payment_date = timezone.now()
                try:
                    tickets = order.create_tickets()
                    if not tickets:
                        return Response({'error': 'Solde insuffisant'}, status=status.HTTP_400_BAD_REQUEST)
                except ValueError as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            order.save()
            return Response({'message': 'Paiement mis à jour'})
        return Response({'message': 'Statut de paiement invalide'}, status=status.HTTP_400_BAD_REQUEST)

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    
    def get_queryset(self):
        event_id = self.request.query_params.get('event')
        if event_id:
            return Review.objects.filter(event_id=event_id)
        return Review.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        print(request.data)
        """Événements favoris des utilisateurs"""
        event_id = request.data.get('event_id')
        print(request.data)
        try:
            event = Event.objects.get(id=event_id)
            favorite, created = Favorite.objects.get_or_create(
                user=request.user,
                event=event
            )
            if not created:
                favorite.delete()
                return Response({'message': 'Retiré des favoris', 'favorited': False})
            return Response({'message': 'Ajouté aux favoris', 'favorited': True})
        except Event.DoesNotExist:
            return Response({'message': 'Événement non trouvé'}, status=status.HTTP_404_NOT_FOUND)

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletTransactionSerializer
    
    def get_queryset(self):
        return WalletTransaction.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Déposer de l'argent dans le wallet"""
        from decimal import Decimal
        amount = request.data.get('amount')
        
        if not amount or Decimal(str(amount)) <= 0:
            return Response({'error': 'Montant invalide'}, status=status.HTTP_400_BAD_REQUEST)
        
        balance_before = request.user.wallet_balance
        request.user.wallet_balance += Decimal(str(amount))
        request.user.save()
        
        WalletTransaction.objects.create(
            user=request.user,
            transaction_type='deposit',
            amount=Decimal(str(amount)),
            balance_before=balance_before,
            balance_after=request.user.wallet_balance,
            description=f"Dépôt de {amount} BIF"
        )
        
        return Response({
            'message': 'Dépôt réussi',
            'balance': request.user.wallet_balance
        })
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Obtenir le solde du wallet"""
        return Response({'balance': request.user.wallet_balance})