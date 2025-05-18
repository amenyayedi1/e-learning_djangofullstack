import os
import django
import random
from decimal import Decimal
from datetime import timedelta, datetime

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu_plus.settings')
django.setup()

# Import des modèles après avoir configuré l'environnement Django
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify
from django.db.models.signals import post_save

from courses.models import Category, Course, Module, Content, Enrollment
from users.models import UserProfile
from payments.models import Payment, Coupon, Invoice
from users.signals import create_user_profile, save_user_profile

CustomUser = get_user_model()

# Liste de données fictives
FIRST_NAMES = [
    "Alexandre", "Marie", "Jean", "Sophie", "Thomas", "Camille", "Lucas", "Emma",
    "Noah", "Chloé", "Léo", "Inès", "Hugo", "Léa", "Louis", "Manon", "Gabriel", "Alice",
    "Raphaël", "Juliette", "Jules", "Sarah", "Arthur", "Louise", "Adam", "Zoé"
]

LAST_NAMES = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand",
    "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David",
    "Bertrand", "Roux", "Vincent", "Fournier", "Morel", "Girard", "Andre", "Lefevre",
    "Mercier", "Bonnet", "Dupont", "Lambert", "Fontaine", "Rousseau", "Muller", "Henry"
]

CATEGORIES = [
    {"name": "Développement Web", "description": "Apprenez à créer des sites et applications web modernes"},
    {"name": "Intelligence Artificielle", "description": "Découvrez le monde de l'IA et du machine learning"},
    {"name": "Design UX/UI", "description": "L'art de créer des interfaces utilisateur intuitives et attrayantes"},
    {"name": "Marketing Digital", "description": "Stratégies et techniques pour réussir en ligne"},
    {"name": "Langues Étrangères", "description": "Apprenez de nouvelles langues facilement"},
    {"name": "Photographie", "description": "Maîtrisez l'art de la photographie"},
    {"name": "Musique", "description": "De la théorie à la pratique musicale"},
    {"name": "Développement Personnel", "description": "Améliorez vos compétences personnelles"}
]

COURSES = [
    {
        "category": "Développement Web",
        "title": "HTML & CSS : Les Fondamentaux",
        "overview": "Apprenez à créer des sites web avec HTML et CSS de A à Z.",
        "objectives": "- Comprendre la structure HTML\n- Maîtriser les sélecteurs CSS\n- Créer des mises en page responsive",
        "requirements": "Aucune connaissance préalable requise. Un ordinateur avec un éditeur de texte.",
        "price": "49.99",
        "difficulty_level": "beginner",
        "language": "Français"
    },
    {
        "category": "Développement Web",
        "title": "JavaScript Moderne",
        "overview": "Maîtrisez JavaScript et les frameworks modernes comme React et Vue.",
        "objectives": "- Comprendre les concepts avancés de JavaScript\n- Travailler avec les API Web\n- Créer des applications avec React",
        "requirements": "Connaissances de base en HTML et CSS. Notions de programmation.",
        "price": "79.99",
        "difficulty_level": "intermediate",
        "language": "Français"
    },
    {
        "category": "Intelligence Artificielle",
        "title": "Introduction au Machine Learning avec Python",
        "overview": "Découvrez les bases du machine learning et implémentez vos premiers modèles.",
        "objectives": "- Comprendre les algorithmes de ML\n- Manipuler des données avec Pandas\n- Créer des modèles avec Scikit-learn",
        "requirements": "Connaissances de base en Python. Notions de mathématiques.",
        "price": "89.99",
        "difficulty_level": "intermediate",
        "language": "Français"
    },
    {
        "category": "Intelligence Artificielle",
        "title": "Deep Learning et Réseaux de Neurones",
        "overview": "Explorez les réseaux de neurones profonds et leurs applications.",
        "objectives": "- Comprendre l'architecture des réseaux de neurones\n- Implémenter des modèles avec TensorFlow\n- Résoudre des problèmes réels avec le deep learning",
        "requirements": "Bonnes connaissances en Python et bases du machine learning.",
        "price": "129.99",
        "difficulty_level": "advanced",
        "language": "Français"
    },
    {
        "category": "Design UX/UI",
        "title": "Principes de Design UX",
        "overview": "Apprenez à créer des expériences utilisateur exceptionnelles.",
        "objectives": "- Comprendre les principes d'UX\n- Réaliser des recherches utilisateurs\n- Créer des wireframes et prototypes",
        "requirements": "Aucune connaissance préalable requise. Un intérêt pour le design.",
        "price": "69.99",
        "difficulty_level": "beginner",
        "language": "Français"
    },
    {
        "category": "Marketing Digital",
        "title": "SEO Avancé",
        "overview": "Optimisez vos sites web pour les moteurs de recherche comme un pro.",
        "objectives": "- Maîtriser le référencement on-page et off-page\n- Analyser et améliorer le positionnement\n- Créer une stratégie SEO complète",
        "requirements": "Connaissances de base en marketing digital et fonctionnement des sites web.",
        "price": "99.99",
        "difficulty_level": "advanced",
        "language": "Français"
    },
    {
        "category": "Développement Personnel",
        "title": "Gestion du Temps et Productivité",
        "overview": "Maximisez votre efficacité et atteignez vos objectifs plus rapidement.",
        "objectives": "- Apprendre des techniques de gestion du temps\n- Mettre en place des systèmes de productivité\n- Réduire le stress et éviter la procrastination",
        "requirements": "Aucun prérequis. Juste la volonté de s'améliorer.",
        "price": "0",
        "difficulty_level": "beginner",
        "language": "Français"
    },
    {
        "category": "Langues Étrangères",
        "title": "Espagnol pour Débutants",
        "overview": "Apprenez l'espagnol facilement avec une méthode progressive et efficace.",
        "objectives": "- Maîtriser les bases de la grammaire espagnole\n- Acquérir un vocabulaire essentiel\n- Pouvoir tenir des conversations simples",
        "requirements": "Aucune connaissance préalable requise.",
        "price": "59.99",
        "difficulty_level": "beginner",
        "language": "Français"
    }
]

MODULE_TEMPLATES = [
    {
        "title": "Introduction au cours",
        "description": "Présentation générale et objectifs du cours",
        "contents": [
            {"title": "Bienvenue au cours", "content_type": "text", "text": "Bienvenue dans ce cours ! Vous allez apprendre...", "is_free": True},
            {"title": "Structure du cours", "content_type": "text", "text": "Ce cours est divisé en plusieurs modules qui couvrent...", "is_free": True},
            {"title": "Vidéo d'introduction", "content_type": "video", "url": "https://www.youtube.com/watch?v=example", "is_free": True}
        ]
    },
    {
        "title": "Concepts fondamentaux",
        "description": "Les bases essentielles à comprendre avant d'aller plus loin",
        "contents": [
            {"title": "Terminologie essentielle", "content_type": "text", "text": "Voici les termes clés que vous devez connaître...", "is_free": False},
            {"title": "Principes de base", "content_type": "text", "text": "Dans cette leçon, nous allons explorer les principes fondamentaux...", "is_free": False},
            {"title": "Quiz de compréhension", "content_type": "link", "url": "https://quizz.example/fondamentals", "is_free": False}
        ]
    },
    {
        "title": "Techniques avancées",
        "description": "Approfondissement des concepts et techniques spécialisées",
        "contents": [
            {"title": "Étude de cas", "content_type": "text", "text": "Analysons ensemble ce cas pratique...", "is_free": False},
            {"title": "Démonstration pratique", "content_type": "video", "url": "https://www.youtube.com/watch?v=advanced_demo", "is_free": False},
            {"title": "Exercice guidé", "content_type": "text", "text": "Suivez les étapes suivantes pour réaliser cet exercice...", "is_free": False}
        ]
    },
    {
        "title": "Projets pratiques",
        "description": "Mise en application des connaissances acquises",
        "contents": [
            {"title": "Consignes du projet", "content_type": "text", "text": "Votre mission est de créer...", "is_free": False},
            {"title": "Ressources complémentaires", "content_type": "link", "url": "https://resources.example/project_resources", "is_free": False},
            {"title": "Exemples de réalisations", "content_type": "image", "url": "https://example.com/project_examples.jpg", "is_free": False}
        ]
    },
    {
        "title": "Conclusion et perspectives",
        "description": "Bilan du cours et ouvertures vers d'autres sujets",
        "contents": [
            {"title": "Récapitulatif des concepts clés", "content_type": "text", "text": "Nous avons couvert les points suivants...", "is_free": False},
            {"title": "Ressources pour aller plus loin", "content_type": "text", "text": "Voici une liste de ressources pour approfondir...", "is_free": False},
            {"title": "Message de conclusion", "content_type": "video", "url": "https://www.youtube.com/watch?v=conclusion", "is_free": False}
        ]
    }
]

def disable_signals():
    """Désactive les signaux Django pour la création de profils utilisateurs"""
    post_save.disconnect(create_user_profile, sender=CustomUser)
    post_save.disconnect(save_user_profile, sender=CustomUser)
    print("Signaux de profil utilisateur désactivés")

def enable_signals():
    """Réactive les signaux Django pour la création de profils utilisateurs"""
    post_save.connect(create_user_profile, sender=CustomUser)
    post_save.connect(save_user_profile, sender=CustomUser)
    print("Signaux de profil utilisateur réactivés")

@transaction.atomic
def create_users(num_students=10, num_instructors=5, admin=True):
    """Créer des utilisateurs (étudiants, instructeurs et admin)"""
    print("Création des utilisateurs...")
    
    # Désactiver les signaux pendant la création des utilisateurs
    disable_signals()
    
    users = []
    
    try:
        # Créer un superutilisateur (admin)
        if admin and not CustomUser.objects.filter(username="admin").exists():
            admin_user = CustomUser.objects.create_superuser(
                username="admin",
                email="admin@eduplus.fr",
                password="adminpassword",
                first_name="Admin",
                last_name="EduPlus",
                user_type="admin"
            )
            # Vérifier si le profil existe avant de le créer
            if not hasattr(admin_user, 'profile'):
                UserProfile.objects.create(user=admin_user)
            print(f"Admin créé: {admin_user.username}")
        
        # Créer des instructeurs
        for i in range(num_instructors):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}"
            email = f"{username}@example.com"
            
            if not CustomUser.objects.filter(username=username).exists():
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password="password123",
                    first_name=first_name,
                    last_name=last_name,
                    user_type="instructor",
                    bio=f"Instructeur spécialisé avec plus de {random.randint(2, 15)} ans d'expérience.",
                    expertise=random.choice(["Développement", "Design", "Marketing", "Data Science", "Langues", "Business"])
                )
                
                # Vérifier si le profil existe avant de le créer
                try:
                    profile = UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    profile = UserProfile.objects.create(user=user)
                
                profile.job_title = f"{random.choice(['Senior', 'Consultant', 'Expert', 'Formateur'])} en {user.expertise}"
                profile.company = random.choice(["Freelance", "EduTech Inc.", "Digital Solutions", "Tech Innovate", "FormaPro"])
                profile.save()
                
                users.append(user)
                print(f"Instructeur créé: {user.username}")
        
        # Créer des étudiants
        for i in range(num_students):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}"
            email = f"{username}@example.com"
            
            if not CustomUser.objects.filter(username=username).exists():
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password="password123",
                    first_name=first_name,
                    last_name=last_name,
                    user_type="student",
                    bio=f"Passionné(e) d'apprentissage continu."
                )
                
                # Vérifier si le profil existe avant de le créer
                try:
                    profile = UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    profile = UserProfile.objects.create(user=user)
                
                profile.learning_goal = random.choice([
                    "Acquérir de nouvelles compétences professionnelles",
                    "Se reconvertir dans un nouveau domaine",
                    "Approfondir mes connaissances actuelles",
                    "Développement personnel et curiosité"
                ])
                profile.save()
                
                users.append(user)
                print(f"Étudiant créé: {user.username}")
    finally:
        # Réactiver les signaux quoi qu'il arrive
        enable_signals()
    
    return users

@transaction.atomic
def create_categories():
    """Créer des catégories de cours"""
    print("Création des catégories...")
    
    categories = []
    for category_data in CATEGORIES:
        name = category_data["name"]
        print(f"Tentative de création de la catégorie '{name}'")
        
        try:
            # Vérifier si la catégorie existe déjà
            existing_category = Category.objects.filter(name=name).first()
            
            if existing_category:
                print(f"La catégorie '{name}' existe déjà (id={existing_category.id})")
                categories.append(existing_category)
            else:
                # Créer une nouvelle catégorie
                category = Category.objects.create(
                    name=name,
                    slug=slugify(name),
                    description=category_data["description"]
                )
                categories.append(category)
                print(f"✓ Catégorie créée: '{category.name}' (id={category.id})")
        except Exception as e:
            print(f"Erreur lors de la création de la catégorie '{name}': {str(e)}")
    
    all_categories = Category.objects.all()
    print(f"Total de catégories après la création: {all_categories.count()}")
    
    return categories if categories else all_categories

@transaction.atomic
def create_courses(instructors):
    """Créer des cours avec leurs modules et contenus"""
    print("Création des cours...")
    
    courses = []
    categories = Category.objects.all()
    print(f"Nombre de catégories trouvées: {categories.count()}")
    for cat in categories:
        print(f"  - {cat.name}")
    
    for course_data in COURSES:
        title = course_data["title"]
        print(f"Tentative de création du cours '{title}'")
        
        if not Course.objects.filter(title=title).exists():
            # Trouver la catégorie correspondante
            category_name = course_data["category"]
            category = categories.filter(name=category_name).first()
            
            if not category:
                print(f"Catégorie non trouvée: '{category_name}'")
                continue
            
            # Sélectionner un instructeur aléatoire
            instructor = random.choice(instructors)
            print(f"Instructeur sélectionné: {instructor.username}")
            
            # Créer le cours
            try:
                course = Course.objects.create(
                    title=title,
                    slug=slugify(title),
                    instructor=instructor,
                    overview=course_data["overview"],
                    objectives=course_data["objectives"],
                    requirements=course_data["requirements"],
                    category=category,
                    price=Decimal(course_data["price"]),
                    difficulty_level=course_data["difficulty_level"],
                    language=course_data["language"],
                    is_published=True
                )
                
                # Ajouter des modules et du contenu
                for i, module_template in enumerate(MODULE_TEMPLATES, 1):
                    module = Module.objects.create(
                        course=course,
                        title=module_template["title"],
                        description=module_template["description"],
                        order=i
                    )
                    
                    # Ajouter des contenus
                    for j, content_data in enumerate(module_template["contents"], 1):
                        Content.objects.create(
                            module=module,
                            title=content_data["title"],
                            content_type=content_data["content_type"],
                            text=content_data.get("text", ""),
                            url=content_data.get("url", ""),
                            is_free=content_data["is_free"],
                            order=j
                        )
                
                courses.append(course)
                print(f"Cours créé: {course.title} (par {instructor.username})")
            except Exception as e:
                print(f"Erreur lors de la création du cours '{title}': {str(e)}")
        else:
            print(f"Le cours '{title}' existe déjà")
    
    return courses

@transaction.atomic
def create_enrollments(students, courses):
    """Inscrire des étudiants à des cours de manière aléatoire"""
    print("Création des inscriptions...")
    
    enrollments = []
    for student in students:
        # Chaque étudiant s'inscrit à 1-4 cours aléatoirement
        num_enrollments = random.randint(1, min(4, len(courses)))
        selected_courses = random.sample(courses, num_enrollments)
        
        for course in selected_courses:
            # Vérifier si l'inscription existe déjà
            if not Enrollment.objects.filter(student=student, course=course).exists():
                # Créer l'inscription
                enrollment = Enrollment.objects.create(
                    student=student,
                    course=course,
                    enrolled_at=timezone.now() - timedelta(days=random.randint(1, 60)),
                    active=True,
                    completed=random.choice([True, False, False, False])  # 25% de chances d'être complété
                )
                
                # Si le cours est payant, créer un paiement (adaptée à la structure de la table)
                if course.price > 0:
                    try:
                        # Note: c'est un exemple simplifié qui correspond à la structure de la table actuelle
                        # Les noms de champs et la structure peuvent être différents sur votre système
                        from django.db import connection
                        
                        # Vérifier si la table a un champ 'enrollment' ou 'course'
                        with connection.cursor() as cursor:
                            cursor.execute("PRAGMA table_info(payments_payment)")
                            columns = [col[1] for col in cursor.fetchall()]
                            has_enrollment = 'enrollment_id' in columns
                            has_course = 'course_id' in columns
                        
                        payment_data = {
                            'user_id': student.id,
                            'amount': course.price,
                            'currency': "EUR",
                            'payment_method': "card",
                            'status': "completed",
                            'payment_id': f"PAY-{student.id}-{course.id}-{int(datetime.now().timestamp())}",
                            'charge_id': f"CH-{random.randint(10000, 99999)}",
                            'created_at': enrollment.enrolled_at,
                            'updated_at': enrollment.enrolled_at,
                            'metadata': '{}'
                        }
                        
                        if has_enrollment:
                            payment_data['enrollment_id'] = enrollment.id
                        elif has_course:
                            payment_data['course_id'] = course.id
                        
                        # Insérer directement dans la base de données
                        with connection.cursor() as cursor:
                            placeholders = ', '.join(['%s'] * len(payment_data))
                            columns = ', '.join(payment_data.keys())
                            values = list(payment_data.values())
                            
                            sql = f"INSERT INTO payments_payment ({columns}) VALUES ({placeholders})"
                            cursor.execute(sql, values)
                        
                        print(f"Paiement créé pour l'inscription: {student.username} → {course.title}")
                    except Exception as e:
                        print(f"Erreur lors de la création du paiement: {str(e)}")
                
                enrollments.append(enrollment)
                print(f"Inscription créée: {student.username} → {course.title}")
    
    return enrollments

@transaction.atomic
def create_coupons():
    """Créer quelques codes promo"""
    print("Création des codes promo...")
    
    coupons = []
    
    # Types de coupons à créer
    coupon_types = [
        {"code": "BIENVENUE", "discount_percent": 15, "description": "Offre de bienvenue pour les nouveaux utilisateurs"},
        {"code": "SUMMER2025", "discount_percent": 20, "description": "Promotion d'été"},
        {"code": "FLASH50", "discount_percent": 50, "description": "Offre flash limitée"},
    ]
    
    for coupon_data in coupon_types:
        code = coupon_data["code"]
        if not Coupon.objects.filter(code=code).exists():
            coupon = Coupon.objects.create(
                code=code,
                discount_percent=coupon_data["discount_percent"],
                description=coupon_data["description"],
                valid_from=timezone.now(),
                valid_until=timezone.now() + timedelta(days=90),
                is_active=True,
                max_uses=100
            )
            coupons.append(coupon)
            print(f"Code promo créé: {coupon.code} ({coupon.discount_percent}%)")
    
    return coupons

def main():
    """Fonction principale pour peupler la base de données"""
    print("Démarrage de la génération des données de test...")
    
    # Créer des utilisateurs
    all_users = create_users(num_students=20, num_instructors=8)
    
    # Séparer les utilisateurs par type
    instructors = [user for user in all_users if user.user_type == "instructor"]
    students = [user for user in all_users if user.user_type == "student"]
    
    # S'assurer qu'on a au moins un instructeur
    if not instructors:
        print("Aucun instructeur trouvé, impossible de créer des cours.")
        return
    
    # Créer des catégories
    create_categories()
    
    # Créer des cours
    courses = create_courses(instructors)
    
    # Si aucun cours n'a été créé, récupérer les cours existants
    if not courses:
        print("Récupération des cours existants...")
        courses_queryset = Course.objects.all()
        if courses_queryset.exists():
            courses = list(courses_queryset)  # Convertir le QuerySet en liste
            print(f"{len(courses)} cours existants trouvés.")
            for course in courses:
                print(f"  - {course.title} (par {course.instructor.username})")
        else:
            print("Aucun cours existant trouvé. Impossible de continuer.")
            return
    
    # Créer des inscriptions
    create_enrollments(students, courses)
    
    # Créer des codes promo
    create_coupons()
    
    print("Génération des données de test terminée !")
    print("\nVous pouvez maintenant vous connecter avec les identifiants suivants :")
    print("Admin : username='admin', password='adminpassword'")
    print("Pour les étudiants et instructeurs : password='password123'")

if __name__ == "__main__":
    main() 