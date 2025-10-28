# admin_app/urls.py

from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', views.admin_login, name='admin-login'),
    path('logout/', views.admin_logout, name='admin-logout'),
    path('profile/', views.get_admin_profile, name='admin-profile'),
    path('verify-token/', views.verify_admin_token, name='verify-admin-token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    # Staff Management (Admin only)
    path('staff/create/', views.create_staff_account, name='admin-create-staff'),
    path('staff/list/', views.list_staff, name='admin-list-staff'),
    path('staff/<int:staff_id>/', views.get_staff_detail, name='admin-staff-detail'),
    path('staff/<int:staff_id>/update/', views.update_staff_status, name='admin-update-staff'),
    path('staff/<int:staff_id>/delete/', views.delete_staff_account, name='admin-delete-staff'),
]