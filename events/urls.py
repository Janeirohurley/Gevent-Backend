from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import auth_views

router = DefaultRouter()
router.register(r'events', views.EventViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'tickets', views.TicketViewSet, basename='ticket')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'favorites', views.FavoriteViewSet, basename='favorite')

urlpatterns = [
    # Authentification (APIView)
    path('api/auth/register/', auth_views.RegisterView.as_view(), name='register'),
    path('api/auth/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/auth/login/', auth_views.LoginView.as_view(), name='login'),
    path('api/auth/user/', auth_views.UserProfileView.as_view(), name='user_profile'),
    
    # API avec ViewSets
    path('api/', include(router.urls)),
]