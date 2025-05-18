from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone

import stripe

from courses.models import Course, Enrollment
from users.models import CustomUser
from .models import Payment, Invoice, Coupon, CouponUsage
from .utils import generate_invoice_pdf, send_invoice_email

# Configurez Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def checkout(request, course_id):
    """Vue pour afficher la page de paiement"""
    course = get_object_or_404(Course, id=course_id)
    
    # Vérifier si l'utilisateur est déjà inscrit à ce cours
    enrollments = request.user.get_enrolled_courses()
    if enrollments.filter(course_id=course_id).exists():
        messages.info(request, "Vous êtes déjà inscrit à ce cours.")
        return redirect('courses:course_detail', slug=course.slug)
    
    # Préparation des données pour la template
    context = {
        'course': course,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    
    return render(request, 'payments/checkout.html', context)

@login_required
@require_POST
def apply_coupon(request, course_id):
    """Vue pour appliquer un coupon à un achat"""
    course = get_object_or_404(Course, id=course_id)
    coupon_code = request.POST.get('code', '').strip()
    
    if not coupon_code:
        return JsonResponse({
            'success': False,
            'message': 'Veuillez entrer un code promotionnel.'
        })
    
    # Rechercher le coupon dans la base de données
    try:
        coupon = Coupon.objects.get(code=coupon_code, is_active=True)
    except Coupon.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Code promotionnel invalide ou expiré.'
        })
    
    # Vérifier si le coupon est valide
    if not coupon.is_valid:
        return JsonResponse({
            'success': False,
            'message': 'Ce code promotionnel a expiré ou n\'est plus valide.'
        })
    
    # Vérifier si le coupon est applicable à ce cours
    if coupon.courses.exists() and not coupon.courses.filter(id=course.id).exists():
        return JsonResponse({
            'success': False,
            'message': 'Ce code promotionnel n\'est pas applicable à ce cours.'
        })
    
    # Vérifier si l'utilisateur a déjà utilisé ce coupon (si usage unique)
    if coupon.is_single_use and CouponUsage.objects.filter(coupon=coupon, user=request.user).exists():
        return JsonResponse({
            'success': False,
            'message': 'Vous avez déjà utilisé ce code promotionnel.'
        })
    
    # Calculer le nouveau prix après application du coupon
    original_price = course.price
    new_price = original_price
    
    if coupon.discount_amount:
        new_price = max(0, original_price - coupon.discount_amount)
        discount_message = f"{coupon.discount_amount} €"
    elif coupon.discount_percent:
        discount_amount = (original_price * coupon.discount_percent) / 100
        new_price = max(0, original_price - discount_amount)
        discount_message = f"{coupon.discount_percent}%"
    else:
        discount_message = "montant non spécifié"
    
    # Stocker le coupon dans la session pour l'utiliser lors du paiement
    request.session['applied_coupon'] = {
        'id': coupon.id,
        'code': coupon.code,
        'discount_amount': float(original_price - new_price),
        'discount_percent': coupon.discount_percent,
        'course_id': course.id,
    }
    
    return JsonResponse({
        'success': True,
        'message': f'Code promotionnel appliqué avec succès ! Réduction de {discount_message}.',
        'original_price': float(original_price),
        'new_price': float(new_price),
        'discount_amount': float(original_price - new_price),
        'discount_message': discount_message
    })

@login_required
def create_checkout_session(request, course_id):
    """Créer une session Stripe pour le paiement"""
    course = get_object_or_404(Course, id=course_id)
    
    # Vérifier si l'utilisateur est déjà inscrit
    enrollments = request.user.get_enrolled_courses()
    if enrollments.filter(course_id=course_id).exists():
        return JsonResponse({'error': 'Vous êtes déjà inscrit à ce cours.'}, status=400)
    
    # Récupérer les informations sur l'utilisateur
    user = request.user
    
    # Vérifier s'il y a un coupon appliqué dans la session
    coupon_data = request.session.get('applied_coupon')
    discount_amount = 0
    coupon = None
    
    if coupon_data and coupon_data.get('course_id') == course_id:
        try:
            coupon = Coupon.objects.get(id=coupon_data.get('id'))
            if coupon.is_valid:
                discount_amount = coupon_data.get('discount_amount', 0)
            else:
                # Le coupon n'est plus valide
                del request.session['applied_coupon']
                coupon = None
        except Coupon.DoesNotExist:
            # Le coupon n'existe plus
            del request.session['applied_coupon']
    
    # Calculer le prix final
    final_price = max(0, course.price - discount_amount)
    
    # Créer une session Stripe avec des options avancées
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'eur',
                        'unit_amount': int(final_price * 100),  # Stripe utilise les centimes
                        'product_data': {
                            'name': course.title,
                            'description': course.short_description if hasattr(course, 'short_description') else course.title,
                            'images': [request.build_absolute_uri(course.image.url)] if course.image else [],
                        },
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                'course_id': course.id,
                'user_id': user.id,
                'course_title': course.title,
                'username': user.username,
                'email': user.email,
                'coupon_id': coupon.id if coupon else None,
                'discount_amount': discount_amount,
                'original_price': course.price,
            },
            customer_email=user.email,  # Pré-remplir l'email
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payments:success')) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri(reverse('payments:cancel', kwargs={'course_id': course.id})),
            payment_intent_data={
                'description': f"Inscription au cours: {course.title}",
                'metadata': {
                    'course_id': course.id,
                    'user_id': user.id,
                    'coupon_id': coupon.id if coupon else None,
                },
            },
            locale='fr',  # Interface en français
        )
        return JsonResponse({'id': checkout_session.id})
    except stripe.error.StripeError as e:
        # Log l'erreur pour le débogage
        print(f"Stripe error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        # Log l'erreur pour le débogage
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({'error': 'Une erreur inattendue s\'est produite. Veuillez réessayer.'}, status=400)

@login_required
def payment_success(request):
    """Vue pour la page de succès après paiement"""
    session_id = request.GET.get('session_id')
    
    if session_id:
        try:
            # Récupérer les données de la session
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Récupérer le payment intent
            payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)
            
            # Créer un paiement dans notre base de données
            course_id = session.metadata.get('course_id')
            course = get_object_or_404(Course, id=course_id)
            
            # Vérifier si un coupon a été utilisé
            coupon_id = session.metadata.get('coupon_id')
            coupon = None
            discount_amount = 0
            
            if coupon_id:
                try:
                    coupon = Coupon.objects.get(id=coupon_id)
                    discount_amount = float(session.metadata.get('discount_amount', 0))
                    
                    # Incrémenter le nombre d'utilisations du coupon
                    coupon.current_uses += 1
                    coupon.save()
                except Coupon.DoesNotExist:
                    # Le coupon n'existe plus
                    pass
            
            # Nettoyer la session
            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']
            
            # Créer ou récupérer le paiement
            payment, created = Payment.objects.get_or_create(
                stripe_payment_id=payment_intent.id,
                defaults={
                    'user': request.user,
                    'course': course,
                    'amount': float(session.amount_total) / 100,  # Convertir centimes en euros
                    'status': 'completed',
                    'payment_method': 'card',
                    'paid_at': timezone.now(),
                    'payment_details': str(payment_intent),
                }
            )
            
            # Si le paiement existe déjà mais n'est pas complété, le mettre à jour
            if not created and payment.status != 'completed':
                payment.status = 'completed'
                payment.paid_at = timezone.now()
                payment.payment_details = str(payment_intent)
                payment.save()
            
            # Inscrire l'utilisateur au cours s'il ne l'est pas déjà
            if not request.user.get_enrolled_courses().filter(id=course.id).exists():
                request.user.get_enrolled_courses().add(course)
                # Créer ou mettre à jour l'inscription
                enrollment, _ = Enrollment.objects.get_or_create(
                    student=request.user,
                    course=course,
                    defaults={
                        'active': True,
                    }
                )
            
            # Enregistrer l'utilisation du coupon si nécessaire
            if coupon:
                CouponUsage.objects.create(
                    coupon=coupon,
                    user=request.user,
                    payment=payment
                )
            
            # Récupérer le prix original et calculer la réduction
            original_price = float(session.metadata.get('original_price', payment.amount))
            
            # Générer une facture
            invoice, invoice_created = Invoice.objects.get_or_create(
                payment=payment,
                defaults={
                    'user': request.user,
                    'subtotal': original_price,
                    'discount_amount': discount_amount,
                    'discount_percent': coupon.discount_percent if coupon and coupon.discount_percent else 0,
                    'total': payment.amount,
                    'billing_name': request.user.get_full_name() or request.user.username,
                }
            )
            
            # Générer le PDF et envoyer l'email si c'est une nouvelle facture
            if invoice_created:
                # Générer le PDF de la facture
                try:
                    generate_invoice_pdf(invoice)
                except Exception as e:
                    print(f"Error generating invoice PDF: {str(e)}")
                
                # Envoyer l'email avec la facture
                try:
                    send_invoice_email(invoice)
                except Exception as e:
                    print(f"Error sending invoice email: {str(e)}")
            
            context = {
                'payment': payment,
                'invoice': invoice,
                'user': request.user,
                'course': course,
                'coupon': coupon
            }
            
            return render(request, 'payments/success.html', context)
        
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite: {str(e)}")
            return redirect('dashboard:home')
    
    return render(request, 'payments/success.html')

@login_required
def payment_cancel(request, course_id):
    """Vue pour la page d'annulation de paiement"""
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'payments/cancel.html', {'course': course})

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Webhook pour recevoir les événements Stripe"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    # Vérifier la signature de l'événement
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Payload invalide
        print(f"Webhook error: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Signature invalide
        print(f"Webhook signature verification failed: {str(e)}")
        return HttpResponse(status=400)
    
    # Journaliser l'événement pour le débogage
    print(f"Webhook event received: {event['type']}")
    
    # Gérer les différents types d'événements
    event_type = event['type']
    event_data = event['data']['object']
    
    # Événements liés au checkout
    if event_type == 'checkout.session.completed':
        handle_checkout_session_completed(event_data)
    
    # Événements liés au paiement
    elif event_type == 'payment_intent.succeeded':
        handle_payment_intent_succeeded(event_data)
    elif event_type == 'payment_intent.payment_failed':
        handle_payment_intent_failed(event_data)
    
    # Événements liés aux remboursements
    elif event_type == 'charge.refunded':
        handle_charge_refunded(event_data)
    
    # Événements liés aux contestations (chargebacks)
    elif event_type == 'charge.dispute.created':
        handle_dispute_created(event_data)
    elif event_type == 'charge.dispute.closed':
        handle_dispute_closed(event_data)
    
    # Retourner une réponse 200 pour confirmer la réception
    return HttpResponse(status=200)

def handle_checkout_session_completed(session):
    """Gérer l'événement checkout.session.completed"""
    # Récupérer les métadonnées
    course_id = session.get('metadata', {}).get('course_id')
    user_id = session.get('metadata', {}).get('user_id')
    coupon_id = session.get('metadata', {}).get('coupon_id')
    
    if not course_id or not user_id:
        print("Missing course_id or user_id in session metadata")
        return
    
    try:
        course = Course.objects.get(id=course_id)
        user = CustomUser.objects.get(id=user_id)
        
        # Vérifier si un coupon a été utilisé
        coupon = None
        discount_amount = 0
        
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                discount_amount = float(session.get('metadata', {}).get('discount_amount', 0))
                
                # Incrémenter le nombre d'utilisations du coupon
                coupon.current_uses += 1
                coupon.save()
            except Coupon.DoesNotExist:
                # Le coupon n'existe plus
                pass
        
        # Créer le paiement
        payment, created = Payment.objects.get_or_create(
            stripe_payment_id=session.payment_intent,
            defaults={
                'user': user,
                'course': course,
                'amount': float(session.amount_total) / 100,  # Convertir centimes en euros
                'status': 'completed',
                'payment_method': 'card',
            }
        )
        
        # Mettre à jour le statut du paiement si nécessaire
        if not created and payment.status != 'completed':
            payment.status = 'completed'
            payment.save()
        
        # Inscrire l'utilisateur au cours s'il ne l'est pas déjà
        enrollments = user.get_enrolled_courses()
        if not enrollments.filter(course=course).exists():
            # Créer une nouvelle inscription
            Enrollment.objects.create(
                student=user,
                course=course,
                active=True
            )
        
        # Enregistrer l'utilisation du coupon si nécessaire
        if coupon:
            CouponUsage.objects.create(
                coupon=coupon,
                user=user,
                payment=payment
            )
        
        # Récupérer le prix original et calculer la réduction
        original_price = float(session.get('metadata', {}).get('original_price', payment.amount))
        
        # Générer une facture si nécessaire
        if created or not Invoice.objects.filter(payment=payment).exists():
            invoice = Invoice.objects.create(
                payment=payment,
                subtotal=original_price,
                discount_amount=discount_amount,
                discount_percent=coupon.discount_percent if coupon and coupon.discount_percent else 0,
                total=payment.amount,
                user=user
            )
            
            # Générer le PDF de la facture
            try:
                generate_invoice_pdf(invoice)
            except Exception as e:
                print(f"Error generating invoice PDF: {str(e)}")
            
            # Envoyer l'email avec la facture
            try:
                send_invoice_email(invoice)
            except Exception as e:
                print(f"Error sending invoice email: {str(e)}")
        
        print(f"Payment processed successfully for user {user.username} and course {course.title}")
        
    except Course.DoesNotExist:
        print(f"Course not found: {course_id}")
    except CustomUser.DoesNotExist:
        print(f"User not found: {user_id}")
    except Exception as e:
        print(f"Error processing checkout session: {str(e)}")

def handle_payment_intent_succeeded(payment_intent):
    """Gérer l'événement payment_intent.succeeded"""
    # Ce code s'exécute quand un paiement est réussi
    payment_id = payment_intent.get('id')
    
    try:
        # Mettre à jour le statut du paiement dans notre base de données
        payment = Payment.objects.filter(stripe_payment_id=payment_id).first()
        if payment:
            payment.status = 'completed'
            payment.payment_details = str(payment_intent)
            payment.save()
            print(f"Payment {payment_id} marked as completed")
    except Exception as e:
        print(f"Error handling payment_intent.succeeded: {str(e)}")

def handle_payment_intent_failed(payment_intent):
    """Gérer l'événement payment_intent.payment_failed"""
    # Ce code s'exécute quand un paiement échoue
    payment_id = payment_intent.get('id')
    error_message = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
    
    try:
        # Mettre à jour le statut du paiement dans notre base de données
        payment = Payment.objects.filter(stripe_payment_id=payment_id).first()
        if payment:
            payment.status = 'failed'
            payment.notes = f"Payment failed: {error_message}"
            payment.save()
            print(f"Payment {payment_id} marked as failed: {error_message}")
    except Exception as e:
        print(f"Error handling payment_intent.payment_failed: {str(e)}")

def handle_charge_refunded(charge):
    """Gérer l'événement charge.refunded"""
    # Ce code s'exécute quand un paiement est remboursé
    payment_intent_id = charge.get('payment_intent')
    
    if not payment_intent_id:
        return
    
    try:
        payment = Payment.objects.filter(stripe_payment_id=payment_intent_id).first()
        if payment:
            payment.status = 'refunded'
            payment.save()
            print(f"Payment {payment_intent_id} marked as refunded")
            
            # Si le remboursement est total, désinscrire l'utilisateur du cours
            if charge.get('refunded'):
                user = payment.user
                course = payment.course
                
                if user and course:
                    # Désinscrire l'étudiant en supprimant l'inscription
                    Enrollment.objects.filter(student=user, course=course).delete()
                    
                    print(f"User {user.username} unenrolled from course {course.title} due to refund")
    except Exception as e:
        print(f"Error handling charge.refunded: {str(e)}")

def handle_dispute_created(dispute):
    """Gérer l'événement charge.dispute.created"""
    # Ce code s'exécute quand une contestation (chargeback) est créée
    payment_intent_id = dispute.get('payment_intent')
    
    if not payment_intent_id:
        return
    
    try:
        payment = Payment.objects.filter(stripe_payment_id=payment_intent_id).first()
        if payment:
            payment.status = 'disputed'
            payment.notes = f"Dispute created: {dispute.get('reason')}"
            payment.save()
            print(f"Payment {payment_intent_id} marked as disputed")
    except Exception as e:
        print(f"Error handling charge.dispute.created: {str(e)}")

def handle_dispute_closed(dispute):
    """Gérer l'événement charge.dispute.closed"""
    # Ce code s'exécute quand une contestation (chargeback) est résolue
    payment_intent_id = dispute.get('payment_intent')
    status = dispute.get('status')
    
    if not payment_intent_id:
        return
    
    try:
        payment = Payment.objects.filter(stripe_payment_id=payment_intent_id).first()
        if payment:
            # Mettre à jour le statut en fonction du résultat de la contestation
            if status == 'won':
                payment.status = 'completed'
                payment.notes = "Dispute won"
                print(f"Dispute for payment {payment_intent_id} won")
            elif status == 'lost':
                payment.status = 'refunded'
                payment.notes = "Dispute lost"
                print(f"Dispute for payment {payment_intent_id} lost")
            
            payment.save()
    except Exception as e:
        print(f"Error handling charge.dispute.closed: {str(e)}")

@login_required
def payment_history(request):
    """Afficher l'historique des paiements de l'utilisateur"""
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'payments/history.html', {'payments': payments})

@login_required
def invoice(request, payment_id):
    """Afficher la facture d'un paiement"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    invoice = get_object_or_404(Invoice, payment=payment)
    
    context = {
        'payment': payment,
        'invoice': invoice,
    }
    
    return render(request, 'payments/invoice.html', context)

@login_required
@require_POST
def remove_coupon(request):
    """Vue pour supprimer un coupon appliqué de la session"""
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
    
    return JsonResponse({
        'success': True,
        'message': 'Code promotionnel supprimé.'
    })
