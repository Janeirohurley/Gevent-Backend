from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Event, Category, Attendee, Ticket, Order, Review, Favorite
from .serializers import (
    EventSerializer, CategorySerializer, AttendeeSerializer,
    TicketSerializer, OrderSerializer, ReviewSerializer,
    FavoriteSerializer, UserSerializer
)

User = get_user_model()

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    parser_classes = [MultiPartParser, FormParser]
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
        my_events = self.queryset.filter(organizer=request.user)
        serializer = self.get_serializer(my_events, many=True)
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
        """Annuler un billet"""
        ticket = self.get_object()
        if ticket.status == 'confirmed':
            ticket.status = 'cancelled'
            ticket.cancelled_at = timezone.now()
            ticket.save()
            return Response({'message': 'Billet annulé avec succès'})
        return Response({'message': 'Ce billet ne peut pas être annulé'}, status=status.HTTP_400_BAD_REQUEST)
    
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
        
        # Si le paiement est déjà complété lors de la création
        if order.payment_status == 'completed':
            order.create_tickets()

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
                # Créer les billets via la méthode du modèle
                order.create_tickets()
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
        """Ajouter/retirer des favoris"""
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