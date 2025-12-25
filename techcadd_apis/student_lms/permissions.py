# student_lms/permissions.py
from rest_framework.permissions import BasePermission
from staff_app.models import StudentRegistration

# class IsStudentAuthenticated(BasePermission):
#     """
#     Custom permission to check if student is authenticated
#     """
#     def has_permission(self, request, view):
#         # Check if user exists and is a StudentRegistration instance
#         if not request.user:
#             return False
        
#         # Check if it's a StudentRegistration object
#         if isinstance(request.user, StudentRegistration):
#             return True
        
#         # Check if user has the student-specific attribute
#         if hasattr(request.user, 'registration_number'):
#             return True
            
#         return False

class IsStudentAuthenticated(BasePermission):
    """
    Custom permission to check if student is authenticated OR if user is admin
    """
    def has_permission(self, request, view):
        if not request.user:
            return False
        
        # ADMIN CHECK - Admins can do everything students can do
        if hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            return True
        
        # STUDENT CHECK
        if isinstance(request.user, StudentRegistration):
            return True
        
        if hasattr(request.user, 'registration_number'):
            return True
            
        return False