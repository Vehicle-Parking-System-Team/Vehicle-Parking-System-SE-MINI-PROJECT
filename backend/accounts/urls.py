from django.urls import path

from accounts.views import (
    CurrentUserView,
    LoginView,
    ProfileView,
    PasswordChangeView,
    LogoutView,
    AdminUserDetailView,
    AdminUserManagementView,
    RegisterView,
    TokenRefreshView,
)

app_name = 'accounts'

urlpatterns = [
    # US-01 Authentication and Registration
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # US-02 Protected Identity Context
    path('me/', CurrentUserView.as_view(), name='current_user'),
    # US-03 Admin User Account Management
    path('users/', AdminUserManagementView.as_view(), name='admin_user_list_create'),
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('change-password/', PasswordChangeView.as_view(), name='change_password'),
]
