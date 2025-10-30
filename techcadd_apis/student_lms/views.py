# student_lms/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import StudentLoginSerializer, StudentDashboardSerializer
from .authentication import StudentJWTAuthentication
from .permissions import IsStudentAuthenticated
from staff_app.models import StudentRegistration

@api_view(['POST'])
@permission_classes([AllowAny])
def student_login(request):
    """
    Student login API
    """
    serializer = StudentLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        student = serializer.validated_data['student']
        
        # Generate JWT tokens
        refresh = RefreshToken()
        
        # Add custom claims to the token
        refresh['student_id'] = student.id
        refresh['registration_number'] = student.registration_number
        refresh['username'] = student.username
        
        return Response({
            'message': 'Login successful',
            'student': {
                'id': student.id,
                'registration_number': student.registration_number,
                'student_name': student.student_name,
                'email': student.email,
                'course_name': student.course.name if student.course else None,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([StudentJWTAuthentication])
@permission_classes([IsStudentAuthenticated])
def student_dashboard(request):
    try:
        # request.user will now be the StudentRegistration object
        student = request.user
        
        if not isinstance(student, StudentRegistration):
            return Response({
                'error': 'Invalid authentication',
                'debug': {
                    'user_type': str(type(student)),
                    'user': str(student)
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = StudentDashboardSerializer(student)
        
        # Add some quick stats
        dashboard_data = serializer.data
        dashboard_data['quick_stats'] = {
            'total_courses': 1,
            'completed_lessons': 0,
            'upcoming_classes': 0,
            'pending_assignments': 0,
        }
        
        return Response({
            'message': 'Dashboard data retrieved successfully',
            'dashboard': dashboard_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_400_BAD_REQUEST)