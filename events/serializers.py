from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Event, Category, Attendee, Ticket, Order, Review, Favorite, EventImage

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'phone_number', 'profile_image', 'bio', 'date_of_birth']
        extra_kwargs = {'password': {'write_only': True}}

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon', 'created_at']

class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ['id', 'image', 'caption', 'order']

class AttendeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Attendee
        fields = ['id', 'username', 'profile_image', 'joined_at']

class EventSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    attendees = AttendeeSerializer(many=True, read_only=True)
    attendee_count = serializers.SerializerMethodField()
    images = EventImageSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    tva_amount = serializers.ReadOnlyField()
    price_with_tva = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category', 'category_id',
            'image_url', 'location', 'latitude', 'longitude',
            'date', 'end_date', 'duration',
            'is_free', 'price', 'tva_rate', 'tva_amount', 'price_with_tva', 'currency',
            'total_capacity', 'available_seats',
            'organizer_name', 'organizer_image',
            'status', 'is_popular', 'rating', 'total_reviews',
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

class TicketSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        source='event',
        write_only=True
    )
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'code', 'event', 'event_id', 'holder_name', 'holder_email', 'holder_phone',
            'seat', 'price', 'tva_rate', 'tva_amount', 'price_ttc', 'currency', 
            'qr_code', 'status',
            'purchase_date', 'used_at', 'cancelled_at'
        ]
        read_only_fields = ['code', 'qr_code', 'tva_amount', 'price_ttc', 'purchase_date']
    
 

class OrderSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    tickets = TicketSerializer(many=True, read_only=True)
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        source='event',
        write_only=True
    )
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'event', 'event_id', 'quantity', 'unit_price', 'tva_rate',
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