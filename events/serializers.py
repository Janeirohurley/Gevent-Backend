from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Event, Category, Attendee, Ticket, Order, Review, Favorite, EventImage, WalletTransaction, TicketCategory

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'phone_number', 'profile_image', 'bio', 'date_of_birth', 'wallet_balance', 'created_at']
        extra_kwargs = {'password': {'write_only': True}}
    
    def get_profile_image(self, obj):
        if obj.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon', 'created_at']

class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ['id', 'image', 'caption', 'order']

class TicketCategorySerializer(serializers.ModelSerializer):
    tva_amount = serializers.ReadOnlyField()
    price_with_tva = serializers.ReadOnlyField()
    is_sold_out = serializers.ReadOnlyField()
    
    class Meta:
        model = TicketCategory
        fields = ['id', 'name', 'description', 'price', 'tva_amount', 'price_with_tva', 
                 'capacity', 'available_seats', 'color', 'benefits', 'order', 'is_sold_out']

class AttendeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_name = serializers.SerializerMethodField()
    tickets_info = serializers.ReadOnlyField()
    total_paid = serializers.ReadOnlyField()
    
    class Meta:
        model = Attendee
        fields = ['id', 'username', 'user_name', 'profile_image', 'joined_at', 'tickets_info', 'total_paid']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name else obj.user.username

class EventSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    ticket_categories = TicketCategorySerializer(many=True, read_only=True)
    attendees = AttendeeSerializer(many=True, read_only=True)
    attendee_count = serializers.SerializerMethodField()
    images = EventImageSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    tva_amount = serializers.ReadOnlyField()
    price_with_tva = serializers.ReadOnlyField()
    organizer_name = serializers.SerializerMethodField()
    organizer_image = serializers.SerializerMethodField()
    organizer_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category', 'category_id',
            'image_url', 'location', 'latitude', 'longitude',
            'date', 'end_date', 'duration',
            'is_free', 'price', 'tva_rate', 'tva_amount', 'price_with_tva', 'currency',
            'total_capacity', 'available_seats', 'ticket_categories',
            'organizer_name', 'organizer_image', 'organizer_phone',
            'status', 'is_approved', 'is_popular', 'rating', 'total_reviews',
            'attendees', 'attendee_count', 'images', 'is_favorited',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['rating', 'total_reviews', 'tva_amount', 'price_with_tva', 'created_at', 'updated_at']

    def get_attendee_count(self, obj):
        return obj.attendees.count()
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False
    
    def get_organizer_name(self, obj):
        return f"{obj.organizer.first_name} {obj.organizer.last_name}" if obj.organizer.first_name else obj.organizer.username
    
    def get_organizer_image(self, obj):
        if obj.organizer.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.organizer.profile_image.url)
            return obj.organizer.profile_image.url
        return None
    
    def get_organizer_phone(self, obj):
        phone = obj.organizer.phone_number
        if phone:
            if not phone.startswith('+'):
                return f'+257{phone}'
            return phone
        return None
    
    def create(self, validated_data):
        import json
        
        # Récupérer les ticket_categories depuis les données brutes si elles ne sont pas dans validated_data
        ticket_categories_data = validated_data.pop('ticket_categories', [])
        
        # Si pas de données, essayer de les récupérer depuis la requête
        if not ticket_categories_data and hasattr(self, 'context'):
            request = self.context.get('request')
            if request and 'ticket_categories' in request.data:
                ticket_categories_json = request.data.get('ticket_categories')
                if isinstance(ticket_categories_json, str):
                    try:
                        ticket_categories_data = json.loads(ticket_categories_json)
                    except json.JSONDecodeError:
                        ticket_categories_data = []
        
        event = Event.objects.create(**validated_data)
        
        for category_data in ticket_categories_data:
            TicketCategory.objects.create(event=event, **category_data)
        
        return event

class TicketSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    ticket_category = TicketCategorySerializer(read_only=True)
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        source='event',
        write_only=True
    )
    ticket_category_id = serializers.PrimaryKeyRelatedField(
        queryset=TicketCategory.objects.all(),
        source='ticket_category',
        write_only=True
    )
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'code', 'event', 'event_id', 'ticket_category', 'ticket_category_id',
            'holder_name', 'holder_email', 'holder_phone',
            'seat', 'price', 'tva_rate', 'tva_amount', 'price_ttc', 'currency', 
            'qr_code', 'status',
            'purchase_date', 'used_at', 'cancelled_at'
        ]
        read_only_fields = ['code', 'qr_code', 'tva_amount', 'price_ttc', 'purchase_date']
    
 

class OrderSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    ticket_category = TicketCategorySerializer(read_only=True)
    tickets = TicketSerializer(many=True, read_only=True)
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        source='event',
        write_only=True
    )
    ticket_category_id = serializers.PrimaryKeyRelatedField(
        queryset=TicketCategory.objects.all(),
        source='ticket_category',
        write_only=True
    )
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'event', 'event_id', 'ticket_category', 'ticket_category_id',
            'quantity', 'unit_price', 'tva_rate',
            'total_ht', 'total_tva', 'total_ttc', 'currency', 'payment_method', 'payment_status',
            'payment_date', 'transaction_id', 'tickets', 'created_at'
        ]
        read_only_fields = ['order_number', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class FavoriteSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'event', 'created_at']
        read_only_fields = ['created_at']

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'transaction_type', 'amount', 'balance_before', 'balance_after', 'description', 'created_at']
        read_only_fields = ['balance_before', 'balance_after', 'created_at']