import os
from io import BytesIO
from django.conf import settings
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa


def generate_invoice_pdf(invoice):
    """
    Génère un PDF de facture à partir d'un objet Invoice
    Retourne le chemin du fichier sauvegardé
    """
    # Préparer le contexte pour le template
    context = {
        'invoice': invoice,
        'payment': invoice.payment,
        'user': invoice.user,
        'course': invoice.payment.course,
        'date': timezone.now().strftime('%d/%m/%Y'),
        'site_url': settings.SITE_URL,
        'company_name': 'EduPlus',
        'company_address': '123 Rue de la Formation, 75000 Paris',
        'company_email': 'contact@eduplus.com',
        'company_phone': '+33 1 23 45 67 89',
    }
    
    # Charger le template HTML
    template = get_template('payments/pdf/invoice_template.html')
    html = template.render(context)
    
    # Créer le fichier PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        # Générer le nom du fichier et le chemin
        filename = f"facture_{invoice.invoice_number}.pdf"
        file_path = os.path.join('invoices', filename)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Sauvegarder le PDF
        with open(full_path, 'wb') as output_file:
            output_file.write(result.getvalue())
        
        # Mettre à jour l'objet Invoice
        invoice.pdf_file.name = file_path
        invoice.save(update_fields=['pdf_file'])
        
        return file_path
    
    return None


def send_invoice_email(invoice):
    """
    Envoie un email avec la facture en pièce jointe
    """
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string
    
    # Générer le PDF si nécessaire
    if not invoice.pdf_file:
        generate_invoice_pdf(invoice)
    
    # Préparation du contexte pour le template d'email
    context = {
        'user': invoice.user,
        'invoice': invoice,
        'payment': invoice.payment,
        'course': invoice.payment.course,
        'site_url': settings.SITE_URL,
    }
    
    # Charger le template d'email
    email_html = render_to_string('payments/email/invoice_email.html', context)
    email_subject = f"Votre facture #{invoice.invoice_number} - EduPlus"
    
    # Créer l'email
    email = EmailMessage(
        subject=email_subject,
        body=email_html,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invoice.user.email],
    )
    email.content_subtype = "html"  # Pour envoyer l'email en HTML
    
    # Ajouter la pièce jointe
    if invoice.pdf_file:
        email.attach_file(os.path.join(settings.MEDIA_ROOT, invoice.pdf_file.name))
    
    # Envoyer l'email
    return email.send() 