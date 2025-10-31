# student_lms/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.student_login, name='student-login'),
    path('dashboard/', views.student_dashboard, name='student-dashboard'),
    # Debug (remove after fixing)
    path('debug-course/', views.debug_course, name='debug-course'),
    
    # Course & Curriculum
    path('my-course/', views.my_course_detail, name='my-course'),
    path('modules/<int:module_id>/', views.module_detail, name='module-detail'),
    path('lessons/<int:lesson_id>/', views.lesson_detail, name='lesson-detail'),
    
    # Progress Tracking
    path('lessons/<int:lesson_id>/progress/', views.update_lesson_progress, name='update-progress'),
    
    # Notes
    path('lessons/<int:lesson_id>/notes/', views.lesson_notes, name='lesson-notes'),
    path('notes/<int:note_id>/', views.note_detail, name='note-detail'),
]