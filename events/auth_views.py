from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from .serializers import UserSerializer

User = get_user_model()

class RegisterView(APIView):
    """Inscription d'un nouvel utilisateur"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug("========== REGISTER REQUEST ==========")
        logger.debug(f"Request data: {request.data}")
        
        serializer = UserSerializer(data=request.data)
        
        if serializer.is_valid():
            logger.debug(f"Serializer valid. Validated data: {serializer.validated_data}")
            
            try:
                user = User.objects.create_user(
                    username=serializer.validated_data['username'],
                    email=serializer.validated_data['email'],
                    password=request.data['password'],
                    first_name=serializer.validated_data.get('first_name', ''),
                    last_name=serializer.validated_data.get('last_name', ''),
                    phone_number=serializer.validated_data.get('phone_number', ''),
                    bio=serializer.validated_data.get('bio', ''),
                    date_of_birth=serializer.validated_data.get('date_of_birth')
                )
                logger.debug(f"User created: {user.username} (ID: {user.id})")
                
                token, created = Token.objects.get_or_create(user=user)
                logger.debug(f"Token created: {token.key[:10]}...")
                
                user_data = UserSerializer(user, context={'request': request}).data
                logger.debug(f"User serialized data: {user_data}")
                
                response_data = {
                    'token': token.key,
                    'user': user_data
                }
                logger.debug(f"Response data: {response_data}")
                logger.debug("======================================")
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                import traceback
                logger.error(traceback.format_exc())
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.error(f"Serializer errors: {serializer.errors}")
        logger.debug("======================================")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """Connexion utilisateur"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user, context={'request': request}).data
                })
            return Response({'error': 'Identifiants invalides'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'error': 'Username et password requis'}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """Déconnexion utilisateur"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'message': 'Déconnexion réussie'})
        except:
            return Response({'error': 'Erreur lors de la déconnexion'}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    """Profil utilisateur"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)