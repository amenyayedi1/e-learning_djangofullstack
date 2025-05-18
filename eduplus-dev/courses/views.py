from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Course, Review, Category


def course_list(request, category_slug=None):
    """Affiche la liste des cours, éventuellement filtrée par catégorie"""
    categories = Category.objects.all()
    courses = Course.objects.filter(is_published=True)
    selected_categories = request.GET.getlist('category')
    
    # Filtre par catégorie si un slug est fourni
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        courses = courses.filter(category=selected_category)
    
    # Filtre par recherche
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) | 
            Q(overview__icontains=search_query) |
            Q(objectives__icontains=search_query)
        )
    
    # Filtre par catégorie
    category_ids = request.GET.getlist('category')
    if category_ids:
        courses = courses.filter(category__id__in=category_ids)
    
    # Filtre par niveau de difficulté
    levels = request.GET.getlist('level')
    if levels:
        courses = courses.filter(difficulty_level__in=levels)
    
    # Filtre par prix
    if request.GET.get('free') == '1' and not request.GET.get('paid') == '1':
        courses = courses.filter(price=0)
    elif request.GET.get('paid') == '1' and not request.GET.get('free') == '1':
        courses = courses.filter(price__gt=0)
    
    # Tri des résultats
    sort_by = request.GET.get('sort', 'latest')
    if sort_by == 'price_asc':
        courses = courses.order_by('price')
    elif sort_by == 'price_desc':
        courses = courses.order_by('-price')
    elif sort_by == 'rating':
        courses = courses.order_by('-rating')
    elif sort_by == 'popular':
        courses = courses.annotate(student_count=Count('enrollments')).order_by('-student_count')
    else:  # latest est le tri par défaut
        courses = courses.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(courses, 9)  # 9 cours par page
    page = request.GET.get('page')
    courses = paginator.get_page(page)
    
    # Liste des niveaux de difficulté pour les filtres
    difficulty_levels = Course.DIFFICULTY_CHOICES
    
    # Paramètres d'URL pour la pagination
    query_params = ""
    for key in request.GET:
        if key != 'page':
            value = request.GET.getlist(key)
            for v in value:
                query_params += f"&{key}={v}"
    
    context = {
        'categories': categories,
        'selected_categories': selected_categories,
        'courses': courses,
        'selected_category': selected_category,
        'difficulty_levels': difficulty_levels,
        'sort': sort_by,
        'query_params': query_params,
        'levels': levels,  # 👈 on ajoute ici les niveaux sélectionnés dans le contexte
    }
    
    return render(request, 'courses/course_list.html', context)



def course_detail(request, slug):
    """Affiche les détails d'un cours"""
    course = get_object_or_404(Course, slug=slug)
    
    # Vérifier si l'utilisateur est inscrit à ce cours
    is_enrolled = False
    has_reviewed = False
    
    if request.user.is_authenticated:
        is_enrolled = course in request.user.get_enrolled_courses()
        has_reviewed = Review.objects.filter(course=course, student=request.user).exists()
    
    # Récupérer d'autres cours de l'instructeur
    instructor_courses = Course.objects.filter(instructor=course.instructor).exclude(id=course.id)[:4]
    
    # Récupérer des cours similaires (même catégorie)
    related_courses = Course.objects.filter(category=course.category).exclude(id=course.id)[:4]
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'has_reviewed': has_reviewed,
        'instructor_courses': instructor_courses,
        'related_courses': related_courses
    }
    
    return render(request, 'courses/course_detail.html', context)


@login_required
def course_create(request):
    """Permet à un enseignant de créer un nouveau cours"""
    # Cette vue sera développée davantage dans la prochaine phase
    return render(request, 'courses/course_form.html')


@login_required
def course_update(request, slug):
    """Permet à un enseignant de modifier un cours existant"""
    # Cette vue sera développée davantage dans la prochaine phase
    return render(request, 'courses/course_form.html')


@login_required
def course_delete(request, slug):
    """Permet à un enseignant de supprimer un cours existant"""
    # Cette vue sera développée davantage dans la prochaine phase
    return redirect('courses:course_list')


@login_required
def course_enroll(request, slug):
    """Permet à un étudiant de s'inscrire à un cours"""
    # Cette vue sera développée davantage dans la prochaine phase
    return redirect('courses:course_detail', slug=slug)


@login_required
def module_detail(request, slug, module_id):
    """Affiche le contenu d'un module spécifique d'un cours"""
    # Cette vue sera développée davantage dans la prochaine phase
    return render(request, 'courses/module_detail.html')


@login_required
def assignment_detail(request, slug, module_id, assignment_id):
    """Affiche les détails d'un devoir"""
    # Cette vue sera développée davantage dans la prochaine phase
    return render(request, 'courses/assignment_detail.html')


@login_required
def assignment_submit(request, slug, module_id, assignment_id):
    """Permet à un étudiant de soumettre un devoir"""
    # Cette vue sera développée davantage dans la prochaine phase
    return render(request, 'courses/assignment_submit.html')


@login_required
def add_review(request, slug):
    """Permettre à un étudiant de laisser un avis sur un cours"""
    course = get_object_or_404(Course, slug=slug)
    
    # Vérifier que l'étudiant est inscrit au cours
    if course not in request.user.get_enrolled_courses():
        messages.error(request, "Vous devez être inscrit à ce cours pour laisser un avis.")
        return redirect('courses:course_detail', slug=slug)
    
    # Vérifier si l'utilisateur a déjà laissé un avis
    existing_review = Review.objects.filter(course=course, student=request.user).first()
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if not rating or not comment:
            messages.error(request, "Veuillez sélectionner une note et laisser un commentaire.")
            return redirect('courses:course_detail', slug=slug)
        
        # Créer ou mettre à jour l'avis
        if existing_review:
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
            messages.success(request, "Votre avis a été mis à jour avec succès!")
        else:
            Review.objects.create(
                course=course,
                student=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, "Votre avis a été ajouté avec succès!")
        
        # Mettre à jour la note moyenne du cours
        course.update_rating()
        
        return redirect('courses:course_detail', slug=slug)
    
    context = {
        'course': course,
        'existing_review': existing_review
    }
    
    return render(request, 'courses/add_review.html', context)
