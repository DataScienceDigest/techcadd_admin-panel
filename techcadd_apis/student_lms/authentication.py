# student_lms/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings
from staff_app.models import StudentRegistration
import jwt

class StudentJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication for students
    """
    
    def authenticate(self, request):
        """
        Override authenticate to handle student tokens
        """
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

    def get_validated_token(self, raw_token):
        """
        Validate the token
        """
        try:
            return UntypedToken(raw_token)
        except TokenError as e:
            raise InvalidToken({
                'detail': 'Token is invalid or expired',
                'code': 'token_not_valid',
            })

    def get_user(self, validated_token):
        """
        Override to get student instead of Django User
        """
        try:
            student_id = validated_token.get('student_id')
            if student_id is None:
                raise AuthenticationFailed('Token contained no recognizable student identification')
            
            student = StudentRegistration.objects.get(id=student_id)
            
            # Add a flag to identify this as a student
            student.is_authenticated = True
            
            return student
            
        except StudentRegistration.DoesNotExist:
            raise AuthenticationFailed('Student not found')
        except KeyError:
            raise AuthenticationFailed('Token contained no recognizable student identification')
