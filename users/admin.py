from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, UserProfile, Notification


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Profil utilisateur')
    fk_name = 'user'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'date_joined', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    inlines = (UserProfileInline,)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informations personnelles'), {'fields': (
            'first_name', 'last_name', 'email', 'date_of_birth', 'bio', 'profile_picture',
            'phone_number', 'address'
        )}),
        (_('Type et statut'), {'fields': ('user_type', 'account_verified')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Dates importantes'), {'fields': ('last_login', 'date_joined')}),
        (_('Préférences'), {'fields': ('language', 'email_notifications')}),
        (_('Instructeur'), {'fields': ('expertise', 'website')}),
        (_('Réseaux sociaux'), {'fields': ('linkedin', 'twitter', 'facebook', 'instagram')}),
    )
    
    # Ajouter ces champs lors de la création d'un utilisateur
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__email', 'title', 'message')
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, _("Les notifications sélectionnées ont été marquées comme lues."))
    mark_as_read.short_description = _("Marquer comme lues")
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, _("Les notifications sélectionnées ont été marquées comme non lues."))
    mark_as_unread.short_description = _("Marquer comme non lues")
