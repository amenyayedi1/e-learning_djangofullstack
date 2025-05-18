from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('student/', views.student_dashboard, name='student'),
    path('instructor/', views.instructor_dashboard, name='instructor'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('courses/', views.enrolled_courses, name='enrolled_courses'),
    path('teaching/', views.teaching_courses, name='teaching_courses'),
    path('submissions/', views.pending_submissions, name='pending_submissions'),
    path('progress/<slug:course_slug>/', views.course_progress, name='course_progress'),
    path('reports/', views.site_reports, name='reports'),
    
    # Nouvelles URLs pour la gestion administrative
    path('users/', views.users_management, name='users'),
    path('users/view/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/edit/<int:user_id>/', views.user_edit, name='user_edit'),
    path('users/delete/<int:user_id>/', views.user_delete, name='user_delete'),
    path('courses-management/', views.courses_management, name='courses_management'),
    path('courses-management/create/', views.course_create, name='course_create'),
    path('courses-management/view/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses-management/edit/<int:course_id>/', views.course_edit, name='course_edit'),
    path('courses-management/delete/<int:course_id>/', views.course_delete, name='course_delete'),
    path('instructors/', views.instructors_management, name='instructors'),
    path('instructors/view/<int:instructor_id>/', views.instructor_detail, name='instructor_detail'),
    path('instructors/edit/<int:instructor_id>/', views.instructor_edit, name='instructor_edit'),
    path('instructors/delete/<int:instructor_id>/', views.instructor_delete, name='instructor_delete'),
    path('students/', views.students_management, name='students'),
    path('students/view/<int:student_id>/', views.student_detail, name='student_detail'),
    path('students/edit/<int:student_id>/', views.student_edit, name='student_edit'),
    path('students/delete/<int:student_id>/', views.student_delete, name='student_delete'),
    path('transactions/', views.transactions_management, name='transactions'),
    path('reports-management/', views.reports_management, name='reports_management'),
    path('settings/', views.settings_management, name='settings'),
    path('notifications/', views.notifications_management, name='notifications'),
]

# URLs pour la gestion des modules
urlpatterns += [
    path('courses/<int:course_id>/modules/', views.modules_management, name='modules_management'),
    path('modules/<int:module_id>/', views.module_detail, name='module_detail'),
    path('modules/add/<int:course_id>/', views.module_edit, name='module_create'),
    path('modules/edit/<int:module_id>/', views.module_edit, name='module_edit'),
    path('modules/delete/<int:module_id>/', views.module_delete, name='module_delete'),
]

# URLs pour la gestion des contenus
urlpatterns += [
    path('modules/<int:module_id>/content/add/', views.content_create, name='content_create'),
    path('content/edit/<int:content_id>/', views.content_edit, name='content_edit'),
    path('content/delete/<int:content_id>/', views.content_delete, name='content_delete'),
    path('modules/<int:module_id>/content/order/', views.update_content_order, name='update_content_order'),
] 