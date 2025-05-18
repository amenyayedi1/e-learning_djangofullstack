from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out

from .models import UserProfile, Notification

User = get_user_model()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Crée automatiquement un profil utilisateur à la création d'un utilisateur"""
    if created:
        # Évite les doublons avec get_or_create
        UserProfile.objects.get_or_create(user=instance)
        
        # Envoi d'un email de bienvenue
        try:
            subject = 'Bienvenue sur EduPlus !'
            html_message = render_to_string('users/emails/welcome_email.html', {'user': instance})
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                html_message=html_message,
                fail_silently=True
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email de bienvenue: {e}")
        
        # Création d'une notification
        Notification.objects.create(
            user=instance,
            title="Bienvenue sur EduPlus !",
            message="Nous sommes ravis de vous accueillir sur notre plateforme d'apprentissage en ligne. "
                    "Explorez nos cours et commencez votre parcours d'apprentissage dès maintenant !",
            notification_type=Notification.SYSTEM
        )

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarde le profil utilisateur lorsque l'utilisateur est sauvegardé"""
    # Vérifie si le profil existe déjà avant de sauvegarder
    profile, created = UserProfile.objects.get_or_create(user=instance)
    if not created:
        profile.save()

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Gestionnaire pour l'événement de connexion utilisateur"""
    # Mettre à jour l'adresse IP de dernière connexion
    if hasattr(request, 'META') and 'REMOTE_ADDR' in request.META:
        user.last_login_ip = request.META['REMOTE_ADDR']
        user.save(update_fields=['last_login_ip'])
    
    # Créer une entrée dans le journal d'activité
    from dashboard.models import ActivityLog
    
    if hasattr(request, 'META'):
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = request.META.get('REMOTE_ADDR', None)
    else:
        user_agent = ''
        ip_address = None
    
    ActivityLog.objects.create(
        user=user,
        activity_type=ActivityLog.LOGIN,
        ip_address=ip_address,
        user_agent=user_agent
    )


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """Gestionnaire pour l'événement de déconnexion utilisateur"""
    # Vérifiez si user est non None (peut être anonyme lors de certains événements de déconnexion)
    if user and user.is_authenticated:
        from dashboard.models import ActivityLog
        
        if hasattr(request, 'META'):
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = request.META.get('REMOTE_ADDR', None)
        else:
            user_agent = ''
            ip_address = None
        
        ActivityLog.objects.create(
            user=user,
            activity_type=ActivityLog.LOGOUT,
            ip_address=ip_address,
            user_agent=user_agent
        )


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def handle_user_type_change(sender, instance, **kwargs):
    """Gère les changements de type d'utilisateur"""
    if instance.pk:
        # Ceci ne s'applique qu'aux utilisateurs existants
        try:
            old_instance = User.objects.get(pk=instance.pk)
            if old_instance.user_type != instance.user_type:
                # Le type d'utilisateur a changé
                
                # Créer une notification pour l'utilisateur
                title = ""
                message = ""
                
                if instance.user_type == User.INSTRUCTOR:
                    title = "Vous êtes maintenant instructeur !"
                    message = ("Félicitations ! Votre compte a été promu au statut d'instructeur. "
                               "Vous pouvez maintenant créer et publier des cours sur la plateforme.")
                
                elif instance.user_type == User.STUDENT and old_instance.user_type == User.INSTRUCTOR:
                    title = "Votre statut a changé"
                    message = ("Votre compte n'a plus le statut d'instructeur. "
                               "Vous ne pourrez plus créer ou gérer des cours.")
                
                if title and message:
                    Notification.objects.create(
                        user=instance,
                        title=title,
                        message=message,
                        notification_type=Notification.SYSTEM
                    )
        except User.DoesNotExist:
            # Nouvel utilisateur, pas d'action nécessaire
            pass 