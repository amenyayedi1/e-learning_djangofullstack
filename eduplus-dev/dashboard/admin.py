from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum

from .models import CourseProgress, ContentProgress, Note, CourseReview, ActivityLog


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'progress_percent', 'total_time_spent', 'started_at', 'completed')
    list_filter = ('completed', 'started_at', 'last_accessed')
    search_fields = ('student__username', 'student__email', 'course__title')
    date_hierarchy = 'started_at'
    
    readonly_fields = ('started_at',)


class ContentProgressInline(admin.TabularInline):
    model = ContentProgress
    extra = 0
    readonly_fields = ('started_at',)
    fields = ('content', 'started_at', 'completed', 'time_spent')
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ContentProgress)
class ContentProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'content', 'course_name', 'time_spent', 'completed', 'last_accessed')
    list_filter = ('completed', 'started_at', 'last_accessed')
    search_fields = ('student__username', 'student__email', 'content__title', 'course_progress__course__title')
    date_hierarchy = 'started_at'
    
    readonly_fields = ('started_at',)
    
    def course_name(self, obj):
        return obj.course_progress.course.title
    course_name.short_description = _("Cours")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('student', 'content_title', 'course_name', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('student__username', 'student__email', 'content__title', 'text')
    date_hierarchy = 'created_at'
    
    readonly_fields = ('created_at', 'updated_at')
    
    def content_title(self, obj):
        return obj.content.title
    content_title.short_description = _("Contenu")
    
    def course_name(self, obj):
        return obj.content.module.course.title
    course_name.short_description = _("Cours")


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating', 'created_at', 'is_approved')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('student__username', 'student__email', 'course__title', 'comment')
    date_hierarchy = 'created_at'
    actions = ['approve_reviews', 'unapprove_reviews']
    
    readonly_fields = ('created_at',)
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, _("Les avis sélectionnés ont été approuvés."))
    approve_reviews.short_description = _("Approuver les avis sélectionnés")
    
    def unapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, _("Les avis sélectionnés ont été désapprouvés."))
    unapprove_reviews.short_description = _("Désapprouver les avis sélectionnés")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'course', 'ip_address', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'user__email', 'course__title', 'ip_address')
    date_hierarchy = 'timestamp'
    
    readonly_fields = ('user', 'activity_type', 'timestamp', 'course', 'module', 'content', 'ip_address', 'user_agent')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
