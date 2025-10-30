# student_lms/permissions.py
from rest_framework.permissions import BasePermission
from staff_app.models import StudentRegistration

class IsStudentAuthenticated(BasePermission):
    """
    Custom permission to check if student is authenticated
    """
    def has_permission(self, request, view):
        # Check if user exists and is a StudentRegistration instance
        if not request.user:
            return False
        
        # Check if it's a StudentRegistration object
        if isinstance(request.user, StudentRegistration):
            return True
        
        # Check if user has the student-specific attribute
        if hasattr(request.user, 'registration_number'):
            return True
            
        return False
