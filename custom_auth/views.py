from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ForgotPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email__iexact=email)
            # In a real app, send an email. For this simulation, we provide a mock token.
            return Response({
                "message": "Password reset instructions have been sent.",
                "reset_token": "mock-reset-token-12345"
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                "message": "If the email is registered, password reset instructions have been sent."
            }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        token = request.data.get('token')
        email = request.data.get('email')
        new_password = request.data.get('password')

        if not email or not new_password or not token:
            return Response({"error": "Email, password, and token are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email__iexact=email)
            if token != "mock-reset-token-12345":
                return Response({"error": "Invalid or expired password reset token."}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)


class AdminUserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Admin can view all users, others get empty list
        if self.request.user.role != 'ADMIN':
            return User.objects.none()
        return User.objects.all().order_by('id')

    def destroy(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        
        user_to_delete = self.get_object()
        if user_to_delete == request.user:
            return Response({"error": "You cannot delete yourself."}, status=status.HTTP_400_BAD_REQUEST)
            
        return super().destroy(request, *args, **kwargs)
