# student_lms/utils.py
from rest_framework.exceptions import AuthenticationFailed

def get_student_from_token(request):
    """
    Extract student from request
    Since we're using custom authentication, request.user is already the student
    """
    if hasattr(request.user, 'registration_number'):
        return request.user
    raise AuthenticationFailed('Invalid student authentication')