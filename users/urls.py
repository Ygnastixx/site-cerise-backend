from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    PendingUsersListView,
    ApproveUserView,
)

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Modération Admin
    path('pending/', PendingUsersListView.as_view(), name='pending_users'),
    path('<int:pk>/approve/', ApproveUserView.as_view(), name='approve_user'),
]