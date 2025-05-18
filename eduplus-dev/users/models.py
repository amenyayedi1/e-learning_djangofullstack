from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class CustomUser(AbstractUser):
    """Modèle utilisateur personnalisé pour EduPlus"""
    is_instructor = models.BooleanField(default=False)

    # Types d'utilisateurs
    STUDENT = 'student'
    INSTRUCTOR = 'instructor'
    ADMIN = 'admin'
    
    USER_TYPE_CHOICES = [
        (STUDENT, _('Étudiant')),
        (INSTRUCTOR, _('Instructeur')),
        (ADMIN, _('Administrateur')),
    ]
    @property
    def is_student(self):
        return self.user_type == self.STUDENT


    # Champs de base
    user_type = models.CharField(
        _('type d\'utilisateur'),
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default=STUDENT
    )
    bio = models.TextField(_('biographie'), blank=True)
    profile_picture = models.ImageField(
        _('photo de profil'),
        upload_to='profile_pics/', 
        blank=True, 
        null=True
    )
    date_of_birth = models.DateField(_('date de naissance'), blank=True, null=True)
    phone_number = models.CharField(_('numéro de téléphone'), max_length=20, blank=True)
    address = models.TextField(_('adresse'), blank=True)
    
    # Préférences
    language = models.CharField(_('langue'), max_length=10, default='fr')
    email_notifications = models.BooleanField(_('notifications par email'), default=True)
    
    # Champs spécifiques aux instructeurs
    expertise = models.CharField(_('domaine d\'expertise'), max_length=255, blank=True)
    website = models.URLField(_('site web'), blank=True)
    
    # Champs relatifs aux réseaux sociaux
    linkedin = models.URLField(_('LinkedIn'), blank=True)
    twitter = models.URLField(_('Twitter'), blank=True)
    facebook = models.URLField(_('Facebook'), blank=True)
    instagram = models.URLField(_('Instagram'), blank=True)
    
    # Champs de suivi d'activité
    last_login_ip = models.GenericIPAddressField(_('IP de dernière connexion'), blank=True, null=True)
    account_verified = models.BooleanField(_('compte vérifié'), default=False)
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
    
    def __str__(self):
        return self.get_full_name() or self.username
    
    @property
    def is_student(self):
        return self.user_type == self.STUDENT
    
    
    
    @property
    def display_name(self):
        return self.get_full_name() or self.username
    
    def get_enrolled_courses(self):
        """Retourne les cours auxquels l'utilisateur est inscrit"""
        return self.enrollments.filter(active=True).select_related('course')
    
    def get_teaching_courses(self):
        """Retourne les cours que l'utilisateur enseigne"""
        if self.is_instructor:
            return self.courses_taught.all()
        return None


class UserProfile(models.Model):
    """Profil étendu pour les utilisateurs avec préférences additionnelles"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('utilisateur')
    )
    
    # Préférences d'apprentissage
    learning_goal = models.CharField(_('objectif d\'apprentissage'), max_length=255, blank=True)
    learning_style = models.CharField(_('style d\'apprentissage'), max_length=50, blank=True)
    daily_goal_minutes = models.PositiveIntegerField(_('objectif quotidien (minutes)'), default=30)
    
    # Compétences et intérêts
    skills = models.JSONField(_('compétences'), default=list, blank=True)
    interests = models.JSONField(_('centres d\'intérêt'), default=list, blank=True)
    
    # Informations professionnelles
    job_title = models.CharField(_('titre professionnel'), max_length=150, blank=True)
    company = models.CharField(_('entreprise'), max_length=150, blank=True)
    industry = models.CharField(_('secteur d\'activité'), max_length=150, blank=True)
    
    # Informations académiques
    education_level = models.CharField(_('niveau d\'éducation'), max_length=100, blank=True)
    certificates = models.JSONField(_('certificats'), default=list, blank=True)
    
    class Meta:
        verbose_name = _('profil utilisateur')
        verbose_name_plural = _('profils utilisateurs')
    
    def __str__(self):
        return f"Profil de {self.user.username}"


class Notification(models.Model):
    """Notifications pour les utilisateurs"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('utilisateur')
    )
    title = models.CharField(_('titre'), max_length=255)
    message = models.TextField(_('message'))
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    is_read = models.BooleanField(_('lu'), default=False)
    
    # Types de notification
    GENERAL = 'general'
    COURSE = 'course'
    ASSIGNMENT = 'assignment'
    SYSTEM = 'system'
    PAYMENT = 'payment'
    
    NOTIFICATION_TYPES = [
        (GENERAL, _('Général')),
        (COURSE, _('Cours')),
        (ASSIGNMENT, _('Devoir')),
        (SYSTEM, _('Système')),
        (PAYMENT, _('Paiement')),
    ]
    
    notification_type = models.CharField(
        _('type de notification'),
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default=GENERAL
    )
    
    # Liens optionnels vers des objets connexes
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('cours')
    )
    
    link = models.URLField(_('lien'), blank=True)
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        self.is_read = True
        self.save(update_fields=['is_read'])


# Création automatique du profil utilisateur lors de la création d'un utilisateur
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """Crée ou met à jour automatiquement un profil utilisateur"""
    if created:
        # Crée un profil uniquement si l'utilisateur n'en a pas déjà un
        UserProfile.objects.get_or_create(user=instance)
    else:
        # Sauvegarde le profil existant
        try:
            instance.profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)