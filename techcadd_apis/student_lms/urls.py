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
    # Live Classes
    # path('live-classes/', live_class_views.my_live_classes, name='my-live-classes'),
    # path('live-classes/<int:class_id>/', live_class_views.live_class_detail, name='live-class-detail'),
    # path('live-classes/<int:class_id>/register/', live_class_views.register_for_class, name='register-class'),
    # path('live-classes/<int:class_id>/join/', live_class_views.join_class, name='join-class'),
    # path('live-classes/<int:class_id>/leave/', live_class_views.leave_class, name='leave-class'),
    # path('live-classes/<int:class_id>/feedback/', live_class_views.submit_feedback, name='class-feedback'),
    # path('live-classes/<int:class_id>/questions/', live_class_views.class_questions, name='class-questions'),
    # path('attendance/history/', live_class_views.my_attendance_history, name='attendance-history'),

]