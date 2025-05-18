from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('category/<slug:category_slug>/', views.course_list, name='course_list_by_category'),
    path('create/', views.course_create, name='course_create'),
    path('<slug:slug>/', views.course_detail, name='course_detail'),
    path('<slug:slug>/update/', views.course_update, name='course_update'),
    path('<slug:slug>/delete/', views.course_delete, name='course_delete'),
    path('<slug:slug>/enroll/', views.course_enroll, name='course_enroll'),
    path('<slug:slug>/module/<int:module_id>/', views.module_detail, name='module_detail'),
    path('<slug:slug>/module/<int:module_id>/assignment/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('<slug:slug>/module/<int:module_id>/assignment/<int:assignment_id>/submit/', views.assignment_submit, name='assignment_submit'),
    path('<slug:slug>/review/', views.add_review, name='add_review'),
] 