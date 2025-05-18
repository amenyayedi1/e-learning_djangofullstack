from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Max
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse, HttpResponse
from django.utils.text import slugify
import os

from courses.models import Course, Enrollment, Category, Submission, Question, Answer, Review, Module, Content
from payments.models import Payment
from users.models import CustomUser, Notification

@login_required
def dashboard_home(request):
    """Rediriger vers le tableau de bord approprié en fonction du rôle de l'utilisateur"""
    user = request.user
    
    if user.is_staff or user.is_superuser:
        return redirect('dashboard:admin')
    elif hasattr(user, 'instructor_profile') and user.instructor_profile.is_active:
        return redirect('dashboard:instructor')
    else:
        return redirect('dashboard:student')

@login_required
def student_dashboard(request):
    """Tableau de bord pour les étudiants"""
    user = request.user
    
    # Récupérer les cours inscrits
    enrolled_courses = user.get_enrolled_courses().order_by('-enrolled_at')[:4]
    
    # Récupérer les cours en cours (avec progression)
    in_progress_courses = []
    for course in enrolled_courses:
        # Calculer la progression pour chaque cours (peut être remplacé par une logique plus complexe)
        progress = Enrollment.objects.get(student=user, course=course).progress
        in_progress_courses.append({
            'course': course,
            'progress': progress
        })
    
    # Récupérer les paiements récents
    recent_payments = Payment.objects.filter(user=user).order_by('-created_at')[:3]
    
    # Récupérer les soumissions récentes
    recent_submissions = Submission.objects.filter(student=user).order_by('-submitted_at')[:3]
    
    # Cours recommandés basés sur les catégories des cours déjà suivis
    enrolled_categories = Category.objects.filter(courses__in=enrolled_courses.values_list('course_id', flat=True)).distinct()

    recommended_courses = Course.objects.filter(category__in=enrolled_categories).exclude(
        id__in=enrolled_courses.values_list('id', flat=True)
    ).order_by('-created_at')[:4]
    
    context = {
        'enrolled_courses': enrolled_courses,
        'in_progress_courses': in_progress_courses,
        'recent_payments': recent_payments,
        'recent_submissions': recent_submissions,
        'recommended_courses': recommended_courses,
    }
    
    return render(request, 'dashboard/student_dashboard.html', context)

@login_required
@user_passes_test(lambda u: hasattr(u, 'instructor_profile') and u.instructor_profile.is_active)
def instructor_dashboard(request):
    """Tableau de bord pour les instructeurs"""
    user = request.user
    
    # Récupérer les cours créés par l'instructeur
    courses = Course.objects.filter(instructor=user)
    courses_count = courses.count()
    
    # Récupérer les statistiques des cours
    students_count = Enrollment.objects.filter(course__instructor=user).count()
    
    # Calculer la note moyenne des cours
    average_rating = courses.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    
    # Calculer les revenus totaux
    # Dans une version réelle, cela devrait prendre en compte les commissions et les taxes
    total_revenue = Payment.objects.filter(course__instructor=user, status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Récupérer les cours récents
    recent_courses = courses.order_by('-created_at')[:3]
    
    # Récupérer les soumissions récentes à évaluer
    recent_submissions = Submission.objects.filter(
        assignment__course__instructor=user,
        status='submitted'
    ).order_by('-submission_date')[:3]
    
    # Récupérer les avis récents sur les cours
    recent_reviews = []  # À implémenter lorsque le modèle Review sera ajouté
    
    # Récupérer les messages récents des étudiants
    recent_messages = []  # À implémenter lorsque le modèle Message sera ajouté
    
    context = {
        'courses_count': courses_count,
        'students_count': students_count,
        'average_rating': average_rating,
        'total_revenue': total_revenue,
        'recent_courses': recent_courses,
        'recent_submissions': recent_submissions,
        'recent_reviews': recent_reviews,
        'recent_messages': recent_messages,
        'pending_submissions_count': Submission.objects.filter(
            assignment__course__instructor=user,
            status='submitted'
        ).count(),
    }
    
    return render(request, 'dashboard/instructor_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_dashboard(request):
    """Tableau de bord pour les administrateurs"""
    # Statistiques globales
    total_users = CustomUser.objects.count()
    total_courses = Course.objects.count()
    total_students = CustomUser.objects.filter(enrollments__isnull=False).distinct().count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    
    # Cours populaires - Utiliser un nom différent pour l'annotation pour éviter le conflit avec la propriété
    popular_courses = Course.objects.annotate(enrollment_count=Count('enrollments')).order_by('-enrollment_count')[:5]
    
    # Calculer le pourcentage d'inscription pour la visualisation
    max_students = popular_courses.first().enrollment_count if popular_courses.exists() else 1
    for course in popular_courses:
        course.enrollment_percentage = (course.enrollment_count / max_students) * 100 if max_students != 0 else 0

    
    # Activités récentes du site
    recent_activities = []  # À implémenter lorsque le modèle ActivityLog sera ajouté
    
    # Demandes récentes d'instructeurs
    instructor_applications = []  # À implémenter lorsque le modèle InstructorApplication sera ajouté
    
    # Nouveaux utilisateurs
    new_users = CustomUser.objects.order_by('-date_joined')[:5]
    
    context = {
        'total_users': total_users,
        'total_courses': total_courses,
        'total_students': total_students,
        'total_revenue': total_revenue,
        'popular_courses': popular_courses,
        'recent_activities': recent_activities,
        'instructor_applications': instructor_applications,
        'new_users': new_users,
        'pending_courses': Course.objects.filter(is_published=False).count(),
        'notifications_count': 0,  # À implémenter lorsque le système de notifications sera ajouté
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def enrolled_courses(request):
    """Afficher tous les cours auxquels l'utilisateur est inscrit"""
    user = request.user
    enrolled_courses = user.get_enrolled_courses().order_by('-enrolled_at')
    
    return render(request, 'dashboard/enrolled_courses.html', {
        'enrolled_courses': enrolled_courses
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'instructor_profile') and u.instructor_profile.is_active)
def teaching_courses(request):
    """Afficher tous les cours enseignés par l'instructeur"""
    courses = Course.objects.filter(instructor=request.user).order_by('-created_at')
    
    return render(request, 'dashboard/teaching_courses.html', {
        'courses': courses
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'instructor_profile') and u.instructor_profile.is_active)
def pending_submissions(request):
    """Afficher toutes les soumissions en attente d'évaluation"""
    submissions = Submission.objects.filter(
        assignment__course__instructor=request.user,
        status='submitted'
    ).order_by('-submission_date')
    
    return render(request, 'dashboard/pending_submissions.html', {
        'submissions': submissions
    })

@login_required
def course_progress(request, course_slug):
    """Afficher la progression d'un étudiant dans un cours spécifique"""
    user = request.user
    course = get_object_or_404(Course, slug=course_slug)
    
    # Vérifier que l'utilisateur est inscrit au cours
    if not user.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, "Vous n'êtes pas inscrit à ce cours.")
        return redirect('dashboard:student')
    
    # Récupérer l'inscription
    enrollment = get_object_or_404(Enrollment, student=user, course=course)
    
    # Récupérer les modules et le contenu terminé
    modules = course.modules.all().prefetch_related('contents')
    completed_contents = enrollment.completed_contents.all()
    
    # Calculer la progression pour chaque module
    module_progress = []
    for module in modules:
        total_contents = module.contents.count()
        if total_contents > 0:
            completed_in_module = completed_contents.filter(module=module).count()
            progress_percent = (completed_in_module / total_contents) * 100
            module_progress.append({
                'module': module,
                'completed': completed_in_module,
                'total': total_contents,
                'percent': progress_percent
            })
        else:
            module_progress.append({
                'module': module,
                'completed': 0,
                'total': 0,
                'percent': 0
            })
    
    # Récupérer les soumissions de l'étudiant pour ce cours
    submissions = Submission.objects.filter(
        student=user,
        assignment__course=course
    ).order_by('-submission_date')
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'module_progress': module_progress,
        'submissions': submissions,
        'overall_progress': enrollment.progress
    }
    
    return render(request, 'dashboard/course_progress.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def site_reports(request):
    """Afficher les rapports du site pour les administrateurs"""
    # Statistiques sur les inscriptions
    last_month = timezone.now() - timedelta(days=30)
    monthly_enrollments = Enrollment.objects.filter(enrolled_at__gte=last_month).count()
    total_enrollments = Enrollment.objects.count()
    
    # Statistiques sur les revenus
    monthly_revenue = Payment.objects.filter(
        created_at__gte=last_month,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Statistiques sur les utilisateurs
    monthly_new_users = CustomUser.objects.filter(date_joined__gte=last_month).count()
    
    # Cours et catégories populaires
    popular_categories = Category.objects.annotate(
        course_count=Count('courses'),
        enrollment_count=Count('courses__enrollments')
    ).order_by('-enrollment_count')[:5]
    
    context = {
        'monthly_enrollments': monthly_enrollments,
        'total_enrollments': total_enrollments,
        'monthly_revenue': monthly_revenue,
        'monthly_new_users': monthly_new_users,
        'popular_categories': popular_categories,
    }
    
    return render(request, 'dashboard/site_reports.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def users_management(request):
    """Gestion des utilisateurs pour les administrateurs"""
    # Récupérer tous les utilisateurs
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Statistiques des utilisateurs
    total_users = users.count()
    total_students = users.filter(user_type='student').count()
    total_instructors = users.filter(user_type='instructor').count()
    total_admins = users.filter(is_staff=True).count()
    
    # Utilisateurs récemment inscrits
    recent_users = users[:10]
    
    context = {
        'users': users,
        'total_users': total_users,
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_admins': total_admins,
        'recent_users': recent_users,
    }
    
    return render(request, 'dashboard/users_management.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def courses_management(request):
    """Gestion des cours pour les administrateurs"""
    # Récupérer tous les cours
    courses = Course.objects.all().order_by('-created_at')
    
    # Vérifier si une exportation est demandée
    export_format = request.GET.get('export')
    if export_format:
        # Import des bibliothèques nécessaires
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        if export_format == 'csv':
            # Créer une réponse CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="courses_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            # Créer le writer CSV
            writer = csv.writer(response)
            writer.writerow(['Titre', 'Instructeur', 'Catégorie', 'Prix', 'Étudiants', 'Statut', 'Date de création'])
            
            # Ajouter chaque cours
            for course in courses:
                writer.writerow([
                    course.title,
                    course.instructor.get_full_name() or course.instructor.username,
                    course.category.name,
                    course.price,
                    course.enrollments.count(),
                    'Publié' if course.is_published else 'Non publié',
                    course.created_at.strftime('%d/%m/%Y')
                ])
            
            return response
        
        elif export_format == 'excel':
            try:
                import xlwt
                
                # Créer un workbook Excel
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = f'attachment; filename="courses_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls"'
                
                wb = xlwt.Workbook(encoding='utf-8')
                ws = wb.add_sheet('Cours')
                
                # Styles
                header_style = xlwt.easyxf('font: bold on, color black; align: horiz center; pattern: pattern solid, fore_color light_blue;')
                
                # Ajouter les en-têtes
                row_num = 0
                columns = ['Titre', 'Instructeur', 'Catégorie', 'Prix', 'Étudiants', 'Statut', 'Date de création']
                
                for col_num, column_title in enumerate(columns):
                    ws.write(row_num, col_num, column_title, header_style)
                
                # Ajouter les données
                for course in courses:
                    row_num += 1
                    row = [
                        course.title,
                        course.instructor.get_full_name() or course.instructor.username,
                        course.category.name,
                        course.price,
                        course.enrollments.count(),
                        'Publié' if course.is_published else 'Non publié',
                        course.created_at.strftime('%d/%m/%Y')
                    ]
                    
                    for col_num, cell_value in enumerate(row):
                        ws.write(row_num, col_num, cell_value)
                
                wb.save(response)
                return response
            except ImportError:
                messages.error(request, "L'exportation Excel n'est pas disponible. Veuillez installer le package xlwt.")
        
        elif export_format == 'pdf':
            try:
                from django.template.loader import render_to_string
                from xhtml2pdf import pisa
                from io import BytesIO
                
                # Statistiques des cours pour le PDF
                total_courses = courses.count()
                published_courses = courses.filter(is_published=True).count()
                pending_courses = courses.filter(is_published=False).count()
                
                # Préparer le contexte pour le template PDF
                context = {
                    'courses': courses,
                    'date': datetime.now().strftime('%d/%m/%Y'),
                    'title': 'Liste des Cours',
                    'total_courses': total_courses,
                    'published_courses': published_courses,
                    'pending_courses': pending_courses
                }
                
                # Rendre le template HTML
                html_string = render_to_string('dashboard/exports/courses_pdf_template.html', context)
                
                # Créer la réponse HTTP
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="courses_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
                
                # Convertir HTML en PDF
                buffer = BytesIO()
                pisa_status = pisa.CreatePDF(html_string, dest=buffer)
                
                if not pisa_status.err:
                    response.write(buffer.getvalue())
                    buffer.close()
                    return response
                else:
                    return HttpResponse('Une erreur est survenue pendant la génération du PDF.', status=400)
            except ImportError:
                messages.error(request, "L'exportation PDF n'est pas disponible. Veuillez installer le package xhtml2pdf.")
    
    # Statistiques des cours
    total_courses = courses.count()
    active_courses = courses.filter(is_published=True).count()
    pending_courses = courses.filter(is_published=False).count()
    
    # Cours récemment créés
    recent_courses = courses[:10]
    
    # Récupérer toutes les catégories
    categories = Category.objects.all()
    
    context = {
        'courses': courses,
        'total_courses': total_courses,
        'active_courses': active_courses,
        'pending_courses': pending_courses,
        'recent_courses': recent_courses,
        'categories': categories,
    }
    
    return render(request, 'dashboard/courses_management.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def instructors_management(request):
    """Gestion des instructeurs pour les administrateurs"""
    # Récupérer tous les instructeurs
    instructors = CustomUser.objects.filter(user_type='instructor').order_by('-date_joined')
    
    # Statistiques des instructeurs
    total_instructors = instructors.count()
    active_instructors = instructors.filter(is_active=True).count()
    
    # Instructeurs les plus populaires (par nombre d'inscriptions à leurs cours)
    popular_instructors = instructors.annotate(
        enrollment_count=Count('courses_taught__enrollments')
    ).order_by('-enrollment_count')[:10]
    
    context = {
        'instructors': instructors,
        'total_instructors': total_instructors,
        'active_instructors': active_instructors,
        'popular_instructors': popular_instructors,
    }
    
    return render(request, 'dashboard/instructors_management.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def students_management(request):
    """Gestion des étudiants pour les administrateurs"""
    # Récupérer tous les étudiants
    students = CustomUser.objects.filter(user_type='student').order_by('-date_joined')
    
    # Statistiques des étudiants
    total_students = students.count()
    active_students = students.filter(is_active=True).count()
    
    # Étudiants les plus actifs (par nombre de cours suivis)
    active_students_list = students.annotate(
        course_count=Count('enrollments')
    ).order_by('-course_count')[:10]
    
    context = {
        'students': students,
        'total_students': total_students,
        'active_students': active_students,
        'active_students_list': active_students_list,
    }
    
    return render(request, 'dashboard/students_management.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def transactions_management(request):
    """Gestion des transactions pour les administrateurs"""
    # Récupérer toutes les transactions avec values() pour éviter les erreurs de relation
    transactions = Payment.objects.all().order_by('-created_at').values(
        'id', 'user_id', 'amount', 'currency', 'status', 'created_at'
    )
    
    # Enrichir les données des transactions avec les informations utilisateur
    for transaction in transactions:
        try:
            user = CustomUser.objects.get(id=transaction['user_id'])
            transaction['user'] = user
        except CustomUser.DoesNotExist:
            transaction['user'] = None
    
    # Statistiques des transactions
    all_payments = Payment.objects.all()
    total_revenue = all_payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    total_transactions = all_payments.count()
    completed_transactions = all_payments.filter(status='completed').count()
    
    # Transactions récentes avec values()
    recent_transactions = Payment.objects.all().order_by('-created_at')[:10].values(
        'id', 'user_id', 'amount', 'currency', 'status', 'created_at'
    )
    
    # Enrichir les données des transactions récentes
    for transaction in recent_transactions:
        try:
            user = CustomUser.objects.get(id=transaction['user_id'])
            transaction['user'] = user
        except CustomUser.DoesNotExist:
            transaction['user'] = None
    
    context = {
        'transactions': transactions,
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'completed_transactions': completed_transactions,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'dashboard/transactions_management.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def reports_management(request):
    """Gestion des rapports pour les administrateurs"""
    return render(request, 'dashboard/reports_management.html')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def settings_management(request):
    """Gestion des paramètres pour les administrateurs"""
    return render(request, 'dashboard/settings_management.html')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def notifications_management(request):
    """Gestion des notifications pour les administrateurs"""
    # Récupérer toutes les notifications
    notifications = Notification.objects.all().order_by('-created_at')
    
    # Statistiques des notifications
    total_notifications = notifications.count()
    unread_notifications = notifications.filter(is_read=False).count()
    
    # Notifications récentes
    recent_notifications = notifications[:10]
    
    context = {
        'notifications': notifications,
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'recent_notifications': recent_notifications,
    }
    
    return render(request, 'dashboard/notifications_management.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def student_detail(request, student_id):
    """Afficher les détails d'un étudiant"""
    student = get_object_or_404(CustomUser, id=student_id, user_type='student')
    
    # Récupérer les cours auxquels l'étudiant est inscrit
    enrollments = Enrollment.objects.filter(student=student).order_by('-enrolled_at')
    
    # Récupérer les paiements de l'étudiant, mais sans essayer d'accéder à course
    # Utiliser values() pour éviter le chargement des relations qui pourraient causer des erreurs
    payments = Payment.objects.filter(user=student).order_by('-created_at').values('id', 'amount', 'created_at', 'status')
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'payments': payments,
    }
    
    return render(request, 'dashboard/student_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def student_edit(request, student_id):
    """Éditer un étudiant"""
    student = get_object_or_404(CustomUser, id=student_id, user_type='student')
    
    if request.method == 'POST':
        # Traiter le formulaire de mise à jour
        student.first_name = request.POST.get('first_name', '')
        student.last_name = request.POST.get('last_name', '')
        student.email = request.POST.get('email', '')
        student.bio = request.POST.get('bio', '')
        student.is_active = 'is_active' in request.POST
        
        # Enregistrer les modifications
        student.save()
        
        # Traiter les options avancées
        if 'reset_password' in request.POST:
            # Génération d'un lien de réinitialisation de mot de passe
            try:
                from django.contrib.auth.tokens import default_token_generator
                from django.utils.http import urlsafe_base64_encode
                from django.utils.encoding import force_bytes
                from django.core.mail import send_mail
                from django.template.loader import render_to_string
                from django.urls import reverse
                
                # Générer le token et l'UID
                token = default_token_generator.make_token(student)
                uid = urlsafe_base64_encode(force_bytes(student.pk))
                
                # Construire l'URL de réinitialisation
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                
                # Préparer et envoyer l'email
                context = {
                    'user': student,
                    'reset_url': reset_url,
                    'site_name': 'EduPlus',
                }
                email_subject = 'Réinitialisation de votre mot de passe sur EduPlus'
                email_body = render_to_string('registration/password_reset_email.html', context)
                
                send_mail(
                    email_subject,
                    email_body,
                    'noreply@eduplus.com',
                    [student.email],
                    fail_silently=False,
                )
                
                messages.success(request, "Un email de réinitialisation de mot de passe a été envoyé à l'étudiant.")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'envoi de l'email de réinitialisation : {str(e)}")
        
        if 'unenroll_all' in request.POST:
            # Désinscrire l'étudiant de tous ses cours
            try:
                enrollments_count = Enrollment.objects.filter(student=student).count()
                Enrollment.objects.filter(student=student).delete()
                messages.success(request, f"L'étudiant a été désinscrit de {enrollments_count} cours.")
            except Exception as e:
                messages.error(request, f"Erreur lors de la désinscription des cours : {str(e)}")
        
        messages.success(request, "Les informations de l'étudiant ont été mises à jour avec succès.")
        return redirect('dashboard:student_detail', student_id=student_id)
    
    context = {
        'student': student,
    }
    
    return render(request, 'dashboard/student_edit.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def student_delete(request, student_id):
    """Supprimer un étudiant"""
    student = get_object_or_404(CustomUser, id=student_id, user_type='student')
    
    if request.method == 'POST':
        try:
            # Désactiver d'abord la cascade de suppression (on delete) pour éviter les erreurs
            student.is_active = False
            student.save()
            
            # Supprimer les relations manuellement dans l'ordre correct
            # 1. Notifications et Coupon usages
            Notification.objects.filter(user=student).delete()
            
            # 2. Supprimer les paiements
            payments = Payment.objects.filter(user=student)
            for payment in payments:
                # S'il y a une facture liée, la supprimer d'abord
                try:
                    if hasattr(payment, 'invoice'):
                        payment.invoice.delete()
                except:
                    pass
                payment.delete()
            
            # 3. Supprimer les soumissions et les questions/réponses
            Submission.objects.filter(student=student).delete()
            Answer.objects.filter(author=student).delete()
            Question.objects.filter(student=student).delete()
            
            # 4. Supprimer les avis (reviews)
            Review.objects.filter(student=student).delete()
            
            # 5. Supprimer les inscriptions
            Enrollment.objects.filter(student=student).delete()
            
            # 6. Maintenant, supprimer complètement l'étudiant
            student.delete()
            
            messages.success(request, "L'étudiant a été supprimé avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression de l'étudiant : {str(e)}")
        
        return redirect('dashboard:students')
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def user_detail(request, user_id):
    """Afficher les détails d'un utilisateur"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Obtenir les informations spécifiques au type d'utilisateur
    context = {
        'user_detail': user,
    }
    
    # Si l'utilisateur est un étudiant
    if user.user_type == 'student':
        # Récupérer les cours auxquels l'étudiant est inscrit
        enrollments = Enrollment.objects.filter(student=user).order_by('-enrolled_at')
        
        # Récupérer les paiements de l'étudiant sans accéder à course
        payments = Payment.objects.filter(user=user).order_by('-created_at').values('id', 'amount', 'created_at', 'status')
        
        context.update({
            'enrollments': enrollments,
            'payments': payments,
        })
    
    # Si l'utilisateur est un instructeur
    elif user.user_type == 'instructor':
        # Récupérer les cours de l'instructeur
        courses = Course.objects.filter(instructor=user).order_by('-created_at')
        
        # Statistiques des cours
        total_students = Enrollment.objects.filter(course__instructor=user).count()
        
        # Revenus totaux 
        total_revenue = Payment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context.update({
            'courses': courses,
            'total_students': total_students,
            'total_revenue': total_revenue,
        })
    
    return render(request, 'dashboard/user_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def user_edit(request, user_id):
    """Éditer un utilisateur"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        # Traiter le formulaire de mise à jour
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.bio = request.POST.get('bio', '')
        user.is_active = 'is_active' in request.POST
        
        # Si c'est un changement de type d'utilisateur
        new_user_type = request.POST.get('user_type')
        if new_user_type and new_user_type != user.user_type:
            user.user_type = new_user_type
        
        # Administrateur / staff
        if request.user.is_superuser:  # Seuls les superusers peuvent promouvoir/dégrader des admins
            user.is_staff = 'is_staff' in request.POST
        
        # Enregistrer les modifications
        user.save()
        
        # Traiter les options avancées
        if 'reset_password' in request.POST:
            # Génération d'un lien de réinitialisation de mot de passe
            try:
                from django.contrib.auth.tokens import default_token_generator
                from django.utils.http import urlsafe_base64_encode
                from django.utils.encoding import force_bytes
                from django.core.mail import send_mail
                from django.template.loader import render_to_string
                from django.urls import reverse
                
                # Générer le token et l'UID
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Construire l'URL de réinitialisation
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                
                # Préparer et envoyer l'email
                context = {
                    'user': user,
                    'reset_url': reset_url,
                    'site_name': 'EduPlus',
                }
                email_subject = 'Réinitialisation de votre mot de passe sur EduPlus'
                email_body = render_to_string('registration/password_reset_email.html', context)
                
                send_mail(
                    email_subject,
                    email_body,
                    'noreply@eduplus.com',
                    [user.email],
                    fail_silently=False,
                )
                
                messages.success(request, "Un email de réinitialisation de mot de passe a été envoyé à l'utilisateur.")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'envoi de l'email de réinitialisation : {str(e)}")
        
        messages.success(request, "Les informations de l'utilisateur ont été mises à jour avec succès.")
        return redirect('dashboard:user_detail', user_id=user_id)
    
    context = {
        'user_detail': user,
    }
    
    return render(request, 'dashboard/user_edit.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def user_delete(request, user_id):
    """Supprimer un utilisateur"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Vérifier que l'utilisateur ne se supprime pas lui-même
    if user.id == request.user.id:
        messages.error(request, "Vous ne pouvez pas vous supprimer vous-même.")
        return redirect('dashboard:users')
    
    # Vérifier que l'utilisateur n'est pas un superuser (sauf si c'est un autre superuser qui fait la demande)
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "Vous n'avez pas les permissions pour supprimer un superuser.")
        return redirect('dashboard:users')
    
    if request.method == 'POST':
        try:
            # Désactiver d'abord la cascade de suppression pour éviter les erreurs
            user.is_active = False
            user.save()
            
            # Supprimer les relations manuellement dans l'ordre correct
            
            # 1. Notifications et usages de coupons
            Notification.objects.filter(user=user).delete()
            
            # 2. Supprimer les paiements et factures associées
            payments = Payment.objects.filter(user=user)
            for payment in payments:
                try:
                    if hasattr(payment, 'invoice'):
                        payment.invoice.delete()
                except:
                    pass
                payment.delete()
            
            # 3. Si étudiant, supprimer les soumissions et les questions/réponses
            if user.user_type == 'student':
                Submission.objects.filter(student=user).delete()
                Answer.objects.filter(author=user).delete()
                Question.objects.filter(student=user).delete()
                
                # Supprimer les avis (reviews)
                Review.objects.filter(student=user).delete()
                
                # Supprimer les inscriptions
                Enrollment.objects.filter(student=user).delete()
            
            # 4. Si instructeur, vérifier les cours
            elif user.user_type == 'instructor':
                # Vérifier si l'instructeur a des cours avec des étudiants inscrits
                courses_with_students = Course.objects.filter(
                    instructor=user, 
                    enrollments__isnull=False
                ).distinct()
                
                if courses_with_students.exists():
                    messages.warning(
                        request, 
                        f"Attention : {courses_with_students.count()} cours de cet instructeur ont des étudiants inscrits."
                    )
                    # Option : transférer les cours à un instructeur par défaut ou les marquer comme archivés
                
                # Pour une suppression complète, on pourrait supprimer les cours de l'instructeur aussi
                
            # 5. Maintenant, supprimer complètement l'utilisateur
            user.delete()
            
            messages.success(request, "L'utilisateur a été supprimé avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression de l'utilisateur : {str(e)}")
        
        return redirect('dashboard:users')
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def instructor_detail(request, instructor_id):
    """Afficher les détails d'un instructeur"""
    instructor = get_object_or_404(CustomUser, id=instructor_id, user_type='instructor')
    
    # Récupérer les cours enseignés par l'instructeur
    courses_taught = Course.objects.filter(instructor=instructor).order_by('-created_at')
    
    # Récupérer les étudiants inscrits aux cours de l'instructeur
    students = CustomUser.objects.filter(
        enrollments__course__instructor=instructor
    ).distinct()
    
    # Calculer les revenus générés par l'instructeur (via les cours)
    # Utiliser values() pour éviter les erreurs de relation
    payments = Payment.objects.filter(
        status='completed',
    ).values('id', 'amount', 'user_id')
    
    # Récupérer les IDs des utilisateurs inscrits aux cours de l'instructeur
    student_ids = Enrollment.objects.filter(
        course__instructor=instructor
    ).values_list('student_id', flat=True).distinct()
    
    # Calculer le revenu total manuellement
    revenue = sum(
        payment['amount'] 
        for payment in payments 
        if payment['user_id'] in student_ids
    )
    
    context = {
        'instructor': instructor,
        'courses_taught': courses_taught,
        'students_count': students.count(),
        'revenue': revenue,
    }
    
    return render(request, 'dashboard/instructor_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def instructor_edit(request, instructor_id):
    """Éditer un instructeur"""
    instructor = get_object_or_404(CustomUser, id=instructor_id, user_type='instructor')
    
    if request.method == 'POST':
        # Traiter le formulaire de mise à jour
        instructor.first_name = request.POST.get('first_name', '')
        instructor.last_name = request.POST.get('last_name', '')
        instructor.email = request.POST.get('email', '')
        instructor.bio = request.POST.get('bio', '')
        instructor.is_active = 'is_active' in request.POST
        
        # Enregistrer les modifications
        instructor.save()
        
        # Traiter les options avancées
        if 'reset_password' in request.POST:
            # Génération d'un lien de réinitialisation de mot de passe
            try:
                from django.contrib.auth.tokens import default_token_generator
                from django.utils.http import urlsafe_base64_encode
                from django.utils.encoding import force_bytes
                from django.core.mail import send_mail
                from django.template.loader import render_to_string
                from django.urls import reverse
                
                # Générer le token et l'UID
                token = default_token_generator.make_token(instructor)
                uid = urlsafe_base64_encode(force_bytes(instructor.pk))
                
                # Construire l'URL de réinitialisation
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                
                # Préparer et envoyer l'email
                context = {
                    'user': instructor,
                    'reset_url': reset_url,
                    'site_name': 'EduPlus',
                }
                email_subject = 'Réinitialisation de votre mot de passe sur EduPlus'
                email_body = render_to_string('registration/password_reset_email.html', context)
                
                send_mail(
                    email_subject,
                    email_body,
                    'noreply@eduplus.com',
                    [instructor.email],
                    fail_silently=False,
                )
                
                messages.success(request, "Un email de réinitialisation de mot de passe a été envoyé à l'instructeur.")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'envoi de l'email de réinitialisation : {str(e)}")
        
        messages.success(request, "Les informations de l'instructeur ont été mises à jour avec succès.")
        return redirect('dashboard:instructor_detail', instructor_id=instructor_id)
    
    context = {
        'instructor': instructor,
    }
    
    return render(request, 'dashboard/instructor_edit.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def instructor_delete(request, instructor_id):
    """Supprimer un instructeur"""
    instructor = get_object_or_404(CustomUser, id=instructor_id, user_type='instructor')
    
    if request.method == 'POST':
        try:
            # Supprimer les relations manuellement dans l'ordre correct
            # 1. Notifications
            Notification.objects.filter(user=instructor).delete()
            
            # 2. Supprimer les paiements et factures associées
            # Mais éviter d'accéder à Invoice si la colonne user_id n'existe pas
            payments = Payment.objects.filter(user=instructor)
            for payment in payments:
                payment.delete()
            
            # 3. Pour les instructeurs, vérifier les cours
            courses = Course.objects.filter(instructor=instructor)
            if courses.exists():
                # Si l'instructeur a des cours, les marquer comme archivés ou les supprimer
                for course in courses:
                    # Supprimer les inscriptions associées au cours
                    Enrollment.objects.filter(course=course).delete()
                    # Supprimer le cours
                    course.delete()
            
            # 4. Maintenant, supprimer complètement l'utilisateur
            instructor.delete()
            
            messages.success(request, "L'instructeur a été supprimé avec succès.")
            return redirect('dashboard:instructors')
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression de l'instructeur : {str(e)}")
            return redirect('dashboard:instructor_detail', instructor_id=instructor_id)
    
    context = {
        'instructor': instructor,
    }
    
    return render(request, 'dashboard/instructor_delete.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def course_detail(request, course_id):
    """Afficher les détails d'un cours"""
    course = get_object_or_404(Course, id=course_id)
    
    # Obtenir les statistiques du cours
    enrollments = Enrollment.objects.filter(course=course)
    total_students = enrollments.count()
    total_reviews = Review.objects.filter(course=course).count()
    average_rating = course.average_rating
    
    context = {
        'course': course,
        'total_students': total_students,
        'total_reviews': total_reviews,
        'average_rating': average_rating,
        'enrollments': enrollments[:10],
    }
    
    return render(request, 'dashboard/course_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def course_edit(request, course_id):
    """Éditer un cours existant"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        # Logique de mise à jour du cours
        course.title = request.POST.get('title', course.title)
        course.overview = request.POST.get('overview', course.overview)
        course.price = request.POST.get('price', course.price)
        course.is_published = request.POST.get('is_published') == 'on'
        
        # Gérer la catégorie si elle est modifiée
        category_id = request.POST.get('category')
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                course.category = category
            except Category.DoesNotExist:
                pass
        
        # Gérer l'image si elle est modifiée
        if 'image' in request.FILES:
            course.image = request.FILES['image']
            
        course.save()
        messages.success(request, f'Le cours "{course.title}" a été mis à jour avec succès.')
        return redirect('dashboard:course_detail', course_id=course.id)
    
    # Obtenir toutes les catégories pour le formulaire
    categories = Category.objects.all()
    
    context = {
        'course': course,
        'categories': categories,
    }
    
    return render(request, 'dashboard/course_edit.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def course_delete(request, course_id):
    """Supprimer un cours"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(request, f'Le cours "{course_title}" a été supprimé avec succès.')
        return redirect('dashboard:courses_management')
    
    return render(request, 'dashboard/course_delete.html', {'course': course})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def course_create(request):
    """Créer un nouveau cours"""
    if request.method == 'POST':
        title = request.POST.get('title')
        overview = request.POST.get('overview')
        price = request.POST.get('price', 0)
        is_published = request.POST.get('is_published') == 'on'
        
        # Récupérer l'instructeur
        instructor_id = request.POST.get('instructor')
        if not instructor_id:
            messages.error(request, 'Veuillez sélectionner un instructeur pour le cours.')
            return redirect('dashboard:course_create')
        
        try:
            instructor = CustomUser.objects.get(id=instructor_id, user_type='instructor')
        except CustomUser.DoesNotExist:
            messages.error(request, 'L\'instructeur sélectionné n\'existe pas.')
            return redirect('dashboard:course_create')
        
        # Récupérer la catégorie
        category_id = request.POST.get('category')
        if not category_id:
            messages.error(request, 'Veuillez sélectionner une catégorie pour le cours.')
            return redirect('dashboard:course_create')
            
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, 'La catégorie sélectionnée n\'existe pas.')
            return redirect('dashboard:course_create')
        
        # Créer le cours
        course = Course(
            title=title,
            overview=overview,
            price=price,
            is_published=is_published,
            instructor=instructor,
            category=category
        )
        
        # Gérer l'image si elle est fournie
        if 'image' in request.FILES:
            course.image = request.FILES['image']
        
        # Générer le slug
        course.slug = slugify(title)
        
        course.save()
        messages.success(request, f'Le cours "{title}" a été créé avec succès.')
        return redirect('dashboard:course_detail', course_id=course.id)
    
    # Obtenir tous les instructeurs pour le formulaire
    instructors = CustomUser.objects.filter(user_type='instructor')
    categories = Category.objects.all()
    
    context = {
        'instructors': instructors,
        'categories': categories,
    }
    
    return render(request, 'dashboard/course_create.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def modules_management(request, course_id):
    """Gestion des modules pour un cours spécifique"""
    course = get_object_or_404(Course, id=course_id)
    
    # Vérifier si l'utilisateur est autorisé (admin ou instructeur du cours)
    if not request.user.is_superuser and request.user != course.instructor:
        messages.error(request, "Vous n'êtes pas autorisé à gérer les modules de ce cours.")
        return redirect('dashboard:courses_management')
    
    # Récupérer tous les modules du cours
    modules = course.modules.all().order_by('order')
    
    if request.method == 'POST':
        if 'add_module' in request.POST:
            # Formulaire d'ajout de module
            title = request.POST.get('title')
            description = request.POST.get('description')
            
            if title:
                # Déterminer l'ordre du nouveau module
                max_order = modules.aggregate(Max('order'))['order__max'] or 0
                
                # Créer le nouveau module
                Module.objects.create(
                    course=course,
                    title=title,
                    description=description,
                    order=max_order + 1
                )
                messages.success(request, f"Le module '{title}' a été ajouté avec succès.")
                return redirect('dashboard:modules_management', course_id=course_id)
            else:
                messages.error(request, "Le titre du module est obligatoire.")
        
        elif 'update_order' in request.POST:
            # Mettre à jour l'ordre des modules
            module_ids = request.POST.getlist('module_id')
            
            for i, module_id in enumerate(module_ids, 1):
                Module.objects.filter(id=module_id).update(order=i)
            
            messages.success(request, "L'ordre des modules a été mis à jour.")
            return redirect('dashboard:modules_management', course_id=course_id)
    
    context = {
        'course': course,
        'modules': modules,
    }
    
    return render(request, 'dashboard/modules_management.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def module_detail(request, module_id):
    """Afficher les détails d'un module spécifique"""
    module = get_object_or_404(Module, id=module_id)
    course = module.course
    
    # Vérifier si l'utilisateur est autorisé (admin ou instructeur du cours)
    if not request.user.is_superuser and request.user != course.instructor:
        messages.error(request, "Vous n'êtes pas autorisé à voir les détails de ce module.")
        return redirect('dashboard:courses_management')
    
    # Récupérer tous les contenus du module
    contents = module.contents.all().order_by('order')
    
    context = {
        'module': module,
        'course': course,
        'contents': contents,
    }
    
    return render(request, 'dashboard/module_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def module_edit(request, module_id=None, course_id=None):
    """Créer ou modifier un module"""
    # Si module_id est fourni, nous modifions un module existant
    if module_id:
        module = get_object_or_404(Module, id=module_id)
        course = module.course
        
        # Vérifier si l'utilisateur est autorisé (admin ou instructeur du cours)
        if not request.user.is_superuser and request.user != course.instructor:
            messages.error(request, "Vous n'êtes pas autorisé à modifier ce module.")
            return redirect('dashboard:courses_management')
    
    # Sinon, nous créons un nouveau module pour le cours spécifié
    else:
        if not course_id:
            messages.error(request, "ID du cours non spécifié.")
            return redirect('dashboard:courses_management')
        
        course = get_object_or_404(Course, id=course_id)
        module = None
        
        # Vérifier si l'utilisateur est autorisé (admin ou instructeur du cours)
        if not request.user.is_superuser and request.user != course.instructor:
            messages.error(request, "Vous n'êtes pas autorisé à créer un module pour ce cours.")
            return redirect('dashboard:courses_management')
    
    if request.method == 'POST':
        # Traiter le formulaire soumis
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        if not title:
            messages.error(request, "Le titre du module est obligatoire.")
        else:
            if module:
                # Mettre à jour le module existant
                module.title = title
                module.description = description
                module.save()
                messages.success(request, f"Le module '{title}' a été mis à jour.")
                return redirect('dashboard:module_detail', module_id=module.id)
            else:
                # Créer un nouveau module
                max_order = course.modules.aggregate(Max('order'))['order__max'] or 0
                module = Module.objects.create(
                    course=course,
                    title=title,
                    description=description,
                    order=max_order + 1
                )
                messages.success(request, f"Le module '{title}' a été créé.")
                return redirect('dashboard:modules_management', course_id=course.id)
    
    context = {
        'module': module,
        'course': course,
    }
    
    return render(request, 'dashboard/module_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def module_delete(request, module_id):
    """Supprimer un module"""
    module = get_object_or_404(Module, id=module_id)
    course = module.course
    
    # Vérifier si l'utilisateur est autorisé (admin ou instructeur du cours)
    if not request.user.is_superuser and request.user != course.instructor:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce module.")
        return redirect('dashboard:courses_management')
    
    if request.method == 'POST':
        if 'confirm_delete' in request.POST:
            course_id = course.id
            module_title = module.title
            
            # Supprimer le module
            module.delete()
            
            # Réorganiser les modules restants
            for i, m in enumerate(course.modules.all().order_by('order'), 1):
                m.order = i
                m.save()
            
            messages.success(request, f"Le module '{module_title}' a été supprimé.")
            return redirect('dashboard:modules_management', course_id=course_id)
    
    context = {
        'module': module,
        'course': course,
    }
    
    return render(request, 'dashboard/module_delete.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def content_create(request, module_id):
    """Créer un nouveau contenu pour un module"""
    module = get_object_or_404(Module, id=module_id)
    course = module.course
    
    # Vérifier si l'utilisateur est autorisé (admin ou instructeur du cours)
    if not request.user.is_superuser and request.user != course.instructor:
        messages.error(request, "Vous n'êtes pas autorisé à ajouter du contenu à ce module.")
        return redirect('dashboard:courses_management')
    
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        title = request.POST.get('title')
        text = request.POST.get('text', '')
        video_url = request.POST.get('video_url', '')
        
        if not title or not content_type:
            messages.error(request, "Le titre et le type de contenu sont obligatoires.")
        else:
            # Déterminer l'ordre du nouveau contenu
            max_order = module.contents.aggregate(Max('order'))['order__max'] or 0
            
            # Créer le nouveau contenu
            content = Content.objects.create(
                module=module,
                title=title,
                content_type=content_type,
                text=text if content_type == 'text' else '',
                video_url=video_url if content_type == 'video' else '',
                order=max_order + 1
            )
            
            # Traiter le fichier téléchargé si c'est un contenu de type fichier
            if content_type == 'file' and 'file' in request.FILES:
                content.file = request.FILES['file']
                content.save()
            
            messages.success(request, f"Le contenu '{title}' a été ajouté avec succès.")
            return redirect('dashboard:module_detail', module_id=module_id)
    
    context = {
        'module': module,
        'course': course,
    }
    
    return render(request, 'dashboard/content_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def content_edit(request, content_id):
    """Modifier un contenu existant"""
    content = get_object_or_404(Content, id=content_id)
    module = content.module
    course = module.course
    
    # Vérifier si l'utilisateur est autorisé (admin ou instructeur du cours)
    if not request.user.is_superuser and request.user != course.instructor:
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce contenu.")
        return redirect('dashboard:courses_management')
    
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        title = request.POST.get('title')
        text = request.POST.get('text', '')
        video_url = request.POST.get('video_url', '')
        
        if not title or not content_type:
            messages.error(request, "Le titre et le type de contenu sont obligatoires.")
        else:
            # Mettre à jour le contenu
            content.title = title
            content.content_type = content_type
            content.text = text if content_type == 'text' else ''
            content.video_url = video_url if content_type == 'video' else ''
            
            # Traiter le fichier téléchargé si c'est un contenu de type fichier
            if content_type == 'file' and 'file' in request.FILES:
                # Supprimer l'ancien fichier si existant
                if content.file:
                    if os.path.isfile(content.file.path):
                        os.remove(content.file.path)
                
                content.file = request.FILES['file']
            
            content.save()
            messages.success(request, f"Le contenu '{title}' a été mis à jour.")
            return redirect('dashboard:module_detail', module_id=module.id)
    
    context = {
        'content': content,
        'module': module,
        'course': course,
    }
    
    return render(request, 'dashboard/content_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def content_delete(request, content_id):
    """Supprimer un contenu"""
    content = get_object_or_404(Content, id=content_id)
    module = content.module
    course = module.course
    
    # Vérifier si l'utilisateur est autorisé (admin ou instructeur du cours)
    if not request.user.is_superuser and request.user != course.instructor:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce contenu.")
        return redirect('dashboard:courses_management')
    
    if request.method == 'POST':
        if 'confirm_delete' in request.POST:
            module_id = module.id
            content_title = content.title
            
            # Supprimer le fichier associé si existant
            if content.file:
                if os.path.isfile(content.file.path):
                    os.remove(content.file.path)
            
            # Supprimer le contenu
            content.delete()
            
            # Réorganiser les contenus restants
            for i, c in enumerate(module.contents.all().order_by('order'), 1):
                c.order = i
                c.save()
            
            messages.success(request, f"Le contenu '{content_title}' a été supprimé.")
            return redirect('dashboard:module_detail', module_id=module_id)
    
    context = {
        'content': content,
        'module': module,
        'course': course,
    }
    
    return render(request, 'dashboard/content_delete.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def update_content_order(request, module_id):
    """Mettre à jour l'ordre des contenus d'un module"""
    if request.method == 'POST' and request.is_ajax():
        module = get_object_or_404(Module, id=module_id)
        course = module.course
        
        # Vérifier si l'utilisateur est autorisé (admin ou instructeur du cours)
        if not request.user.is_superuser and request.user != course.instructor:
            return JsonResponse({'status': 'error', 'message': "Vous n'êtes pas autorisé à modifier ce module."}, status=403)
        
        try:
            content_ids = request.POST.getlist('content_ids[]')
            
            for i, content_id in enumerate(content_ids, 1):
                Content.objects.filter(id=content_id, module=module).update(order=i)
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
