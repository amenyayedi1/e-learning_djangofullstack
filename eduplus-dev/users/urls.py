from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
# Vérifie cette ligne dans urls.py pour servir les fichiers statiques en développement
from django.conf import settings
from django.conf.urls.static import static
app_name = 'users'

urlpatterns = [
    path('payout-settings/', views.payout_settings, name='payout_settings'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('login/', views.custom_login, name='login'),
    path('register/', views.custom_register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('instructors/', views.instructor_list, name='instructor_list'),
    path('instructors/<int:pk>/', views.instructor_detail, name='instructor_detail'),
    path('password/change/', auth_views.PasswordChangeView.as_view(), name='change_password'),
    path('notifications/settings/', views.notification_settings, name='notification_settings'),
    path('privacy/settings/', views.privacy_settings, name='privacy_settings'),
    path('logout/', views.custom_logout, name='logout'),
    path('delete_account/', views.delete_account, name='delete_account'),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)