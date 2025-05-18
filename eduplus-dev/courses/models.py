from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Avg

import uuid


class Category(models.Model):
    """Catégorie de cours"""
    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    image = models.ImageField(_('image'), upload_to='categories/', blank=True, null=True)
    
    class Meta:
        verbose_name = _('catégorie')
        verbose_name_plural = _('catégories')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('courses:course_list_by_category', args=[self.slug])


class Course(models.Model):
    """Modèle représentant un cours"""
    # Niveaux de difficulté
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    EXPERT = 'expert'
    
    DIFFICULTY_CHOICES = [
        (BEGINNER, _('Débutant')),
        (INTERMEDIATE, _('Intermédiaire')),
        (ADVANCED, _('Avancé')),
        (EXPERT, _('Expert')),
    ]
    
    title = models.CharField(_('titre'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_taught',
        verbose_name=_('instructeur')
    )
    overview = models.TextField(_('présentation'))
    objectives = models.TextField(_('objectifs'), blank=True)
    requirements = models.TextField(_('prérequis'), blank=True)
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_('catégorie')
    )
    
    image = models.ImageField(_('image'), upload_to='courses/', blank=True, null=True)
    price = models.DecimalField(_('prix'), max_digits=7, decimal_places=2, default=0.00)
    discount_price = models.DecimalField(_('prix réduit'), max_digits=7, decimal_places=2, null=True, blank=True)
    is_published = models.BooleanField(_('publié'), default=False)
    
    difficulty_level = models.CharField(
        _('niveau de difficulté'),
        max_length=15,
        choices=DIFFICULTY_CHOICES,
        default=BEGINNER
    )
    
    language = models.CharField(_('langue'), max_length=50, default='Français')
    
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de mise à jour'), auto_now=True)
    
    class Meta:
        verbose_name = _('cours')
        verbose_name_plural = _('cours')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('courses:course_detail', args=[self.slug])
    
    @property
    def formatted_price(self):
        if self.price == 0:
            return _('Gratuit')
        return f"{self.price} €"
    
    @property
    def discount_percentage(self):
        if self.discount_price and self.price > 0:
            discount = ((self.price - self.discount_price) / self.price) * 100
            return int(discount)
        return 0
    
    @property
    def student_count(self):
        return self.enrollments.count()
    
    @property
    def average_rating(self):
        rating = self.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        return rating if rating else 0
    
    @property
    def current_price(self):
        return self.discount_price if self.discount_price else self.price
    
    def update_rating(self):
        """Mettre à jour la note moyenne du cours basée sur les avis"""
        reviews = self.reviews.all()
        if reviews.exists():
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            self.rating = round(avg_rating, 1)
        else:
            self.rating = 0
        self.save()


class Module(models.Model):
    """Module de cours contenant des sections de contenu"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name=_('cours')
    )
    title = models.CharField(_('titre'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    order = models.PositiveIntegerField(_('ordre'), default=0)
    
    class Meta:
        verbose_name = _('module')
        verbose_name_plural = _('modules')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def get_absolute_url(self):
        return reverse('courses:module_detail', args=[self.course.slug, self.id])


class Content(models.Model):
    """Contenu d'un module de cours"""
    # Types de contenu
    TEXT = 'text'
    VIDEO = 'video'
    FILE = 'file'
    IMAGE = 'image'
    LINK = 'link'
    
    CONTENT_TYPES = [
        (TEXT, _('Texte')),
        (VIDEO, _('Vidéo')),
        (FILE, _('Fichier')),
        (IMAGE, _('Image')),
        (LINK, _('Lien')),
    ]
    
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='contents',
        verbose_name=_('module')
    )
    title = models.CharField(_('titre'), max_length=200)
    content_type = models.CharField(_('type de contenu'), max_length=10, choices=CONTENT_TYPES)
    text = models.TextField(_('texte'), blank=True)
    file = models.FileField(_('fichier'), upload_to='content/', blank=True, null=True)
    url = models.URLField(_('URL'), blank=True)
    order = models.PositiveIntegerField(_('ordre'), default=0)
    is_free = models.BooleanField(_('contenu gratuit'), default=False)
    
    class Meta:
        verbose_name = _('contenu')
        verbose_name_plural = _('contenus')
        ordering = ['order']
    
    def __str__(self):
        return self.title
    
    @property
    def course(self):
        return self.module.course


class Assignment(models.Model):
    """Devoir à rendre par les étudiants"""
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name=_('module')
    )
    title = models.CharField(_('titre'), max_length=200)
    description = models.TextField(_('description'))
    due_date = models.DateTimeField(_('date limite'), blank=True, null=True)
    max_score = models.PositiveIntegerField(_('score maximum'), default=100)
    
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de mise à jour'), auto_now=True)
    
    class Meta:
        verbose_name = _('devoir')
        verbose_name_plural = _('devoirs')
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.module.course.title} - {self.title}"
    
    @property
    def is_past_due(self):
        if self.due_date:
            return timezone.now() > self.due_date
        return False


class Submission(models.Model):
    """Soumission d'un devoir par un étudiant"""
    # Statuts de soumission
    SUBMITTED = 'submitted'
    GRADED = 'graded'
    RETURNED = 'returned'
    
    STATUS_CHOICES = [
        (SUBMITTED, _('Soumis')),
        (GRADED, _('Noté')),
        (RETURNED, _('Retourné')),
    ]
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('étudiant')
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('devoir')
    )
    file = models.FileField(_('fichier'), upload_to='submissions/')
    submitted_at = models.DateTimeField(_('date de soumission'), auto_now_add=True)
    status = models.CharField(_('statut'), max_length=15, choices=STATUS_CHOICES, default=SUBMITTED)
    score = models.PositiveIntegerField(_('score'), blank=True, null=True)
    feedback = models.TextField(_('feedback de l\'instructeur'), blank=True)
    comments = models.TextField(_('commentaires de l\'étudiant'), blank=True)
    
    class Meta:
        verbose_name = _('soumission')
        verbose_name_plural = _('soumissions')
        ordering = ['-submitted_at']
        unique_together = ['student', 'assignment']
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"
    
    @property
    def is_late(self):
        if self.assignment.due_date:
            return self.submitted_at > self.assignment.due_date
        return False
    
    @property
    def score_percentage(self):
        if self.score is not None and self.assignment.max_score > 0:
            return (self.score / self.assignment.max_score) * 100
        return 0


class Enrollment(models.Model):
    """Inscription d'un étudiant à un cours"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('étudiant')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('cours')
    )
    enrolled_at = models.DateTimeField(_('date d\'inscription'), auto_now_add=True)
    active = models.BooleanField(_('actif'), default=True)
    completed = models.BooleanField(_('terminé'), default=False)
    
    class Meta:
        verbose_name = _('inscription')
        verbose_name_plural = _('inscriptions')
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"


class Question(models.Model):
    """Question posée par un étudiant sur un contenu"""
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('contenu')
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('étudiant')
    )
    text = models.TextField(_('texte de la question'))
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('question')
        verbose_name_plural = _('questions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.content.title}"


class Answer(models.Model):
    """Réponse à une question"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('question')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('auteur')
    )
    text = models.TextField(_('texte de la réponse'))
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('réponse')
        verbose_name_plural = _('réponses')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author.username} - Réponse à {self.question.student.username}"


class Review(models.Model):
    """Modèle pour les avis des utilisateurs sur les cours"""
    RATING_CHOICES = (
        (1, '1 étoile'),
        (2, '2 étoiles'),
        (3, '3 étoiles'),
        (4, '4 étoiles'),
        (5, '5 étoiles'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_reviews')
    student = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='reviews_made')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-created_at']
        unique_together = ['course', 'student']  # Un utilisateur ne peut laisser qu'un seul avis par cours
    
    def __str__(self):
        return f"Avis de {self.student.username} sur {self.course.title}"
