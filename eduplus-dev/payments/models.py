from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
from courses.models import Course, Enrollment


class Payment(models.Model):
    """Modèle pour les paiements"""
    # Statuts de paiement
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    DISPUTED = 'disputed'
    CANCELED = 'canceled'
    
    STATUS_CHOICES = [
        (PENDING, _('En attente')),
        (COMPLETED, _('Complété')),
        (FAILED, _('Échoué')),
        (REFUNDED, _('Remboursé')),
        (DISPUTED, _('Contesté')),
        (CANCELED, _('Annulé')),
    ]
    
    # Méthodes de paiement
    CARD = 'card'
    PAYPAL = 'paypal'
    BANK_TRANSFER = 'bank_transfer'
    
    PAYMENT_METHOD_CHOICES = [
        (CARD, _('Carte de crédit')),
        (PAYPAL, _('PayPal')),
        (BANK_TRANSFER, _('Virement bancaire')),
    ]
    
    # Champs du modèle
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('utilisateur')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('cours'),
        null=True,  
        
    )
    amount = models.DecimalField(_('montant'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('devise'), max_length=3, default='EUR')
    reference_id = models.CharField(_('ID de référence'), max_length=100, unique=True, blank=True)
    stripe_payment_id = models.CharField(_('ID de paiement Stripe'), max_length=100, blank=True)
    payment_method = models.CharField(
        _('méthode de paiement'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default=CARD
    )
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de mise à jour'), auto_now=True)
    paid_at = models.DateTimeField(_('date de paiement'), null=True, blank=True)
    payment_details = models.TextField(_('détails du paiement'), blank=True)
    notes = models.TextField(_('notes'), blank=True)
    
    class Meta:
        verbose_name = _('paiement')
        verbose_name_plural = _('paiements')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Générer un ID de référence unique lors de la création
        if not self.reference_id:
            self.reference_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        
        # Mettre à jour la date de paiement si le statut passe à complété
        if self.status == self.COMPLETED and not self.paid_at:
            self.paid_at = timezone.now()
        
        super().save(*args, **kwargs)


class Invoice(models.Model):
    """Modèle pour les factures"""
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='invoice',
        verbose_name=_('paiement')
    )
    invoice_number = models.CharField(_('numéro de facture'), max_length=50, unique=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_('utilisateur'),
        null=True,
        blank=True
    )
    subtotal = models.DecimalField(_('sous-total'), max_digits=10, decimal_places=2, default=0.0)
    tax_percent = models.DecimalField(_('pourcentage de taxe'), max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_('montant de la taxe'), max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(_('pourcentage de réduction'), max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(_('montant de la réduction'), max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(_('total'), max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    billing_name = models.CharField(_('nom de facturation'), max_length=200, blank=True)
    billing_address = models.TextField(_('adresse de facturation'), blank=True)
    billing_city = models.CharField(_('ville de facturation'), max_length=100, blank=True)
    billing_country = models.CharField(_('pays de facturation'), max_length=100, blank=True)
    billing_postcode = models.CharField(_('code postal de facturation'), max_length=20, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    pdf_file = models.FileField(_('fichier PDF'), upload_to='invoices/', null=True, blank=True)
    
    class Meta:
        verbose_name = _('facture')
        verbose_name_plural = _('factures')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Facture {self.invoice_number} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Générer un numéro de facture unique lors de la création
        if not self.invoice_number:
            date_str = timezone.now().strftime('%Y%m')
            last_invoice = Invoice.objects.filter(invoice_number__startswith=f"INV-{date_str}").order_by('invoice_number').last()
            
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.invoice_number = f"INV-{date_str}-{new_number:04d}"
        
        # Calculer les montants de taxe et de réduction si nécessaire
        if self.tax_percent and not self.tax_amount:
            self.tax_amount = self.subtotal * (self.tax_percent / 100)
            
        if self.discount_percent and not self.discount_amount:
            self.discount_amount = self.subtotal * (self.discount_percent / 100)
        
        # Mettre à jour le total si nécessaire
        if not self.total:
            self.total = self.subtotal + self.tax_amount - self.discount_amount
        
        # Définir le nom de facturation par défaut
        if not self.billing_name and self.user:
            self.billing_name = self.user.get_full_name() or self.user.username
        
        super().save(*args, **kwargs)


class Coupon(models.Model):
    """Coupons de réduction pour les cours"""
    code = models.CharField(_('code'), max_length=50, unique=True)
    discount_amount = models.DecimalField(
        _('montant de réduction'), 
        max_digits=10, 
        decimal_places=2,
        blank=True,
        null=True
    )
    discount_percent = models.PositiveIntegerField(
        _('pourcentage de réduction'),
        blank=True,
        null=True
    )
    description = models.CharField(_('description'), max_length=255, blank=True)
    
    # Limites d'utilisation
    valid_from = models.DateTimeField(_('valide à partir de'))
    valid_until = models.DateTimeField(_('valide jusqu\'à'), blank=True, null=True)
    max_uses = models.PositiveIntegerField(_('utilisations maximum'), blank=True, null=True)
    current_uses = models.PositiveIntegerField(_('utilisations actuelles'), default=0)
    
    # Association à des cours spécifiques
    courses = models.ManyToManyField(
        Course,
        related_name='coupons',
        blank=True,
        verbose_name=_('cours applicables')
    )
    
    # Limites par utilisateur
    is_single_use = models.BooleanField(_('usage unique par utilisateur'), default=False)
    
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('coupon')
        verbose_name_plural = _('coupons')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.discount_display}"
    
    @property
    def is_valid(self):
        """Vérifie si le coupon est encore valide"""
        now = timezone.now()
        
        # Vérifier la période de validité
        if now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        
        # Vérifier le nombre d'utilisations
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        
        return self.is_active
    
    @property
    def discount_display(self):
        """Affiche la réduction de manière lisible"""
        if self.discount_amount:
            return f"{self.discount_amount} €"
        if self.discount_percent:
            return f"{self.discount_percent}%"
        return "0"


class CouponUsage(models.Model):
    """Enregistre l'utilisation d'un coupon par un utilisateur"""
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usages',
        verbose_name=_('coupon')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coupon_usages',
        verbose_name=_('utilisateur'),
        null=True,
        blank=True
    
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='coupon_usage',
        verbose_name=_('paiement')
    )
    used_at = models.DateTimeField(_('date d\'utilisation'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('utilisation de coupon')
        verbose_name_plural = _('utilisations de coupons')
        unique_together = ['coupon', 'user', 'payment']
        ordering = ['-used_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.coupon.code}"
