from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count, Avg

from .models import (
    Category, Course, Module, Content, Assignment,
    Submission, Enrollment, Question, Answer, Review
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'course_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = _("Nombre de cours")
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _course_count=Count('courses', distinct=True)
        )
        return queryset


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'created_at', 'is_published', 'price', 'student_count', 'avg_rating')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'instructor__username', 'overview')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('instructor',)
    date_hierarchy = 'created_at'
    inlines = [ModuleInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'instructor', 'category')
        }),
        (_('Contenu'), {
            'fields': ('image', 'overview', 'objectives', 'requirements')
        }),
        (_('Détails'), {
            'fields': ('price', 'discount_price', 'difficulty_level', 'language')
        }),
        (_('Statut'), {
            'fields': ('is_published', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def student_count(self, obj):
        return obj.enrollments.count()
    student_count.short_description = _("Nombre d'étudiants")
    
    def avg_rating(self, obj):
        avg = obj.reviews.aggregate(avg=Avg('rating'))['avg']
        if avg:
            return round(avg, 1)
        return '-'
    avg_rating.short_description = _("Note moyenne")
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _student_count=Count('enrollments', distinct=True),
            _avg_rating=Avg('reviews__rating')
        )
        return queryset


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'content_count')
    list_filter = ('course__title',)
    search_fields = ('title', 'description', 'course__title')
    raw_id_fields = ('course',)
    
    def content_count(self, obj):
        return obj.contents.count()
    content_count.short_description = _("Éléments de contenu")


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'content_type', 'is_free', 'order')
    list_filter = ('content_type', 'is_free', 'module__course__title')
    search_fields = ('title', 'text', 'module__title', 'module__course__title')
    raw_id_fields = ('module',)
    fieldsets = (
        (None, {
            'fields': ('module', 'title', 'order', 'is_free')
        }),
        (_('Contenu'), {
            'fields': ('content_type', 'text', 'file', 'url')
        }),
    )


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'due_date', 'max_score', 'submission_count')
    list_filter = ('module__course__title', 'due_date')
    search_fields = ('title', 'description', 'module__title')
    raw_id_fields = ('module',)
    date_hierarchy = 'due_date'
    
    def submission_count(self, obj):
        return obj.submissions.count()
    submission_count.short_description = _("Nombre de soumissions")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'submitted_at', 'status', 'score', 'file_preview')
    list_filter = ('status', 'submitted_at', 'assignment__title')
    search_fields = ('student__username', 'assignment__title', 'comments')
    raw_id_fields = ('student', 'assignment')
    date_hierarchy = 'submitted_at'
    
    readonly_fields = ('submitted_at',)
    
    def file_preview(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Voir le fichier</a>', obj.file.url)
        return '-'
    file_preview.short_description = _("Fichier")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'active', 'completed')
    list_filter = ('active', 'completed', 'enrolled_at')
    search_fields = ('student__username', 'student__email', 'course__title')
    raw_id_fields = ('student', 'course')
    date_hierarchy = 'enrolled_at'
    
    readonly_fields = ('enrolled_at',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('content', 'student', 'created_at', 'is_answered')
    list_filter = ('created_at',)
    search_fields = ('content__title', 'student__username', 'text')
    raw_id_fields = ('content', 'student')
    date_hierarchy = 'created_at'
    
    readonly_fields = ('created_at',)
    
    def is_answered(self, obj):
        return obj.answers.exists()
    is_answered.boolean = True
    is_answered.short_description = _("Répondue")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'author', 'created_at', 'is_instructor_answer')
    list_filter = ('created_at',)
    search_fields = ('question__text', 'author__username', 'text')
    raw_id_fields = ('question', 'author')
    date_hierarchy = 'created_at'
    
    readonly_fields = ('created_at',)
    
    def is_instructor_answer(self, obj):
        return obj.author == obj.question.content.module.course.instructor
    is_instructor_answer.boolean = True
    is_instructor_answer.short_description = _("Réponse de l'instructeur")


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('student__username', 'student__email', 'course__title', 'comment')
    ordering = ('-created_at',)
    
admin.site.register(Review, ReviewAdmin)
