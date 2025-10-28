# staff_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.staff_login, name='staff-login'),
    path('logout/', views.staff_logout, name='staff-logout'),
    path('verify-token/', views.verify_staff_token, name='verify-staff-token'),
    path('token/refresh/', views.staff_token_refresh, name='staff-token-refresh'),
    
    # Profile & Dashboard
    path('profile/', views.staff_profile, name='staff-profile'),
    path('dashboard/', views.staff_dashboard, name='staff-dashboard'),
    
    # Staff Features (role-based)
    path('reports/', views.staff_reports, name='staff-reports'),
    # Student Management
    path('students/create/', views.create_student, name='create-student'),
    path('students/list/', views.list_students, name='list-students'),
    path('students/<int:student_id>/', views.get_student_detail, name='student-detail'),
    path('students/<int:student_id>/update/', views.update_student, name='update-student'),
    path('students/stats/', views.student_stats, name='student-stats'),
    path('students/options/', views.get_student_options, name='student-options'),  # New endpoint
    # Student Registration
    path('registrations/options/', views.get_registration_options, name='registration-options'),
    path('registrations/courses/<int:course_type_id>/', views.get_courses_by_type, name='courses-by-type'),
    path('registrations/create/', views.create_student_registration, name='create-registration'),
    path('registrations/list/', views.list_student_registrations, name='list-registrations'),
    path('registrations/<int:registration_id>/', views.get_registration_detail, name='registration-detail'),
]