"""
URL configuration for edu_plus project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # URLs d'authentification via django-allauth
    path('accounts/', include('allauth.urls')),
    
    # Redirection de accounts/profile vers users/profile
    path('accounts/profile/', RedirectView.as_view(url='/users/profile/', permanent=True)),
    
    # Page d'accueil temporaire
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # Page de contact
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    
    # Page à propos
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    
    # URLs des applications
    path('courses/', include('courses.urls', namespace='courses')),
    path('users/', include('users.urls', namespace='users')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('payments/', include('payments.urls', namespace='payments')),
]

# Configuration pour servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
