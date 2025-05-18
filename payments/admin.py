from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import Payment, Invoice, Coupon, CouponUsage


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course_name', 'amount_with_currency', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'user__email', 'course__title', 'reference_id', 'stripe_payment_id')
    readonly_fields = ('reference_id', 'stripe_payment_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'course', 'amount', 'currency', 'status')
        }),
        (_('Détails du paiement'), {
            'fields': ('payment_method', 'reference_id', 'stripe_payment_id', 'payment_details')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at', 'paid_at')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def course_name(self, obj):
        return obj.course.title
    course_name.short_description = _("Cours")
    
    def amount_with_currency(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_with_currency.short_description = _("Montant")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'payment', 'user_info', 'created_at', 'download_pdf')
    search_fields = ('invoice_number', 'payment__user__username', 'payment__user__email', 'billing_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('payment', 'invoice_number', 'created_at', 'pdf_file')
        }),
        (_('Informations de facturation'), {
            'fields': ('billing_name', 'billing_address', 'billing_city', 'billing_postal_code', 'billing_country')
        }),
    )
    
    def user_info(self, obj):
        return f"{obj.payment.user.username} ({obj.payment.user.email})"
    user_info.short_description = _("Utilisateur")
    
    def download_pdf(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">Télécharger</a>', obj.pdf_file.url)
        return '-'
    download_pdf.short_description = _("Facture PDF")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_display', 'valid_from', 'valid_until', 'current_uses', 'max_uses', 'is_active')
    list_filter = ('is_active', 'valid_from', 'valid_until')
    search_fields = ('code', 'description')
    filter_horizontal = ('courses',)
    date_hierarchy = 'valid_from'
    
    fieldsets = (
        (None, {
            'fields': ('code', 'description', 'is_active', 'courses')
        }),
        (_('Réduction'), {
            'fields': ('discount_amount', 'discount_percent')
        }),
        (_('Validité'), {
            'fields': ('valid_from', 'valid_until', 'max_uses', 'current_uses', 'is_single_use')
        }),
    )
    
    readonly_fields = ('current_uses',)


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'payment', 'used_at')
    list_filter = ('used_at',)
    search_fields = ('coupon__code', 'user__username', 'user__email')
    date_hierarchy = 'used_at'
    
    readonly_fields = ('coupon', 'user', 'payment', 'used_at')
