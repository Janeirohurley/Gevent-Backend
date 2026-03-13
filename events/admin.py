from django.contrib import admin
from .models import User, Category, Event, EventImage, Attendee, Ticket, Order, Review, Favorite, WalletTransaction, TicketCategory

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'wallet_balance', 'created_at']
    list_filter = ['created_at', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']

class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1

class TicketCategoryInline(admin.TabularInline):
    model = TicketCategory
    extra = 1
    fields = ['name', 'price', 'capacity', 'color']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'date', 'location', 'status', 'is_popular', 'is_approved']
    list_filter = ['category', 'status', 'is_popular', 'is_free', 'is_approved', 'created_at']
    search_fields = ['title', 'description', 'location']
    inlines = [EventImageInline, TicketCategoryInline]
    readonly_fields = ['rating', 'total_reviews']
    actions = ['approve_events', 'reject_events']
    
    def approve_events(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} événements approuvés.")
    approve_events.short_description = "Approuver les événements sélectionnés"
    
    def reject_events(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} événements rejetés.")
    reject_events.short_description = "Rejeter les événements sélectionnés"

@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'price', 'capacity', 'color']
    list_filter = ['event', 'price']
    search_fields = ['name', 'event__title']

@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'joined_at']
    list_filter = ['joined_at']
    search_fields = ['user__username', 'event__title']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['code', 'event', 'user', 'status', 'purchase_date']
    list_filter = ['status', 'purchase_date']
    search_fields = ['code', 'user__username', 'event__title']
    readonly_fields = ['code', 'qr_code', 'tva_amount', 'price_ttc']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'event', 'total_ttc', 'payment_status']
    list_filter = ['payment_status', 'created_at']
    search_fields = ['order_number', 'user__username', 'event__title']
    readonly_fields = ['order_number', 'total_ht', 'total_tva', 'total_ttc']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'event__title']

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'event__title']

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['balance_before', 'balance_after', 'created_at']
