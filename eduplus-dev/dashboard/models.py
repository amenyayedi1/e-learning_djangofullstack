from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from courses.models import Course, Module, Content


class CourseProgress(models.Model):
    """Suivi de la progression globale d'un étudiant dans un cours"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_progresses',
        verbose_name=_('étudiant')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='student_progresses',
        verbose_name=_('cours')
    )
    started_at = models.DateTimeField(_('date de début'), auto_now_add=True)
    last_accessed = models.DateTimeField(_('dernier accès'), auto_now=True)
    completed = models.BooleanField(_('terminé'), default=False)
    completed_at = models.DateTimeField(_('date de fin'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('progression de cours')
        verbose_name_plural = _('progressions de cours')
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
    
    @property
    def progress_percent(self):
        """Calcule le pourcentage de progression du cours"""
        total_contents = self.course.modules.aggregate(
            total=models.Count('contents')
        )['total'] or 0
        
        if total_contents == 0:
            return 0
        
        completed_contents = self.content_progresses.filter(completed=True).count()
        return int((completed_contents / total_contents) * 100)
    
    @property
    def total_time_spent(self):
        """Retourne le temps total passé sur le cours en minutes"""
        return sum(cp.time_spent for cp in self.content_progresses.all())


class ContentProgress(models.Model):
    """Suivi de la progression d'un étudiant pour un contenu spécifique"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='content_progresses',
        verbose_name=_('étudiant')
    )
    course_progress = models.ForeignKey(
        CourseProgress,
        on_delete=models.CASCADE,
        related_name='content_progresses',
        verbose_name=_('progression du cours')
    )
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='student_progresses',
        verbose_name=_('contenu')
    )
    started_at = models.DateTimeField(_('date de début'), auto_now_add=True)
    last_accessed = models.DateTimeField(_('dernier accès'), auto_now=True)
    completed = models.BooleanField(_('terminé'), default=False)
    completed_at = models.DateTimeField(_('date de fin'), blank=True, null=True)
    time_spent = models.PositiveIntegerField(_('temps passé (minutes)'), default=0)
    
    class Meta:
        verbose_name = _('progression de contenu')
        verbose_name_plural = _('progressions de contenu')
        unique_together = ['student', 'content']
    
    def __str__(self):
        return f"{self.student.username} - {self.content.title}"


class Note(models.Model):
    """Notes personnelles d'un étudiant sur un contenu"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name=_('étudiant')
    )
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='student_notes',
        verbose_name=_('contenu')
    )
    text = models.TextField(_('texte'))
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de mise à jour'), auto_now=True)
    
    class Meta:
        verbose_name = _('note')
        verbose_name_plural = _('notes')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.content.title}"


class CourseReview(models.Model):
    """Avis d'un étudiant sur un cours"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_reviews',
        verbose_name=_('étudiant')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('cours')
    )
    rating = models.PositiveSmallIntegerField(
        _('note'), 
        choices=[(i, str(i)) for i in range(1, 6)]
    )  # 1-5 étoiles
    comment = models.TextField(_('commentaire'))
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de mise à jour'), auto_now=True)
    is_approved = models.BooleanField(_('approuvé'), default=True)
    
    class Meta:
        verbose_name = _('avis sur un cours')
        verbose_name_plural = _('avis sur les cours')
        ordering = ['-created_at']
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} - {self.rating}/5"


class ActivityLog(models.Model):
    """Journal d'activité des utilisateurs"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name=_('utilisateur')
    )
    
    # Types d'activité
    LOGIN = 'login'
    LOGOUT = 'logout'
    VIEW_COURSE = 'view_course'
    ENROLL_COURSE = 'enroll_course'
    COMPLETE_CONTENT = 'complete_content'
    SUBMIT_ASSIGNMENT = 'submit_assignment'
    
    ACTIVITY_TYPES = [
        (LOGIN, _('Connexion')),
        (LOGOUT, _('Déconnexion')),
        (VIEW_COURSE, _('Consultation de cours')),
        (ENROLL_COURSE, _('Inscription à un cours')),
        (COMPLETE_CONTENT, _('Contenu terminé')),
        (SUBMIT_ASSIGNMENT, _('Soumission de devoir')),
    ]
    
    activity_type = models.CharField(
        _('type d\'activité'),
        max_length=50,
        choices=ACTIVITY_TYPES
    )
    
    timestamp = models.DateTimeField(_('horodatage'), auto_now_add=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name=_('cours')
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name=_('module')
    )
    content = models.ForeignKey(
        Content,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name=_('contenu')
    )
    ip_address = models.GenericIPAddressField(_('adresse IP'), blank=True, null=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    
    class Meta:
        verbose_name = _('journal d\'activité')
        verbose_name_plural = _('journaux d\'activité')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp}"
