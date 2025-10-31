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


    # -------------------course details view-------------------
# student_lms/course_views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .authentication import StudentJWTAuthentication
from .permissions import IsStudentAuthenticated
from .models import CourseModule, Lesson, StudentProgress, StudentNote
from .serializers import (
    CourseDetailSerializer,
    CourseModuleSerializer,
    LessonDetailSerializer,
    StudentProgressSerializer,
    StudentNoteSerializer
)


@api_view(['GET'])
@authentication_classes([StudentJWTAuthentication])
@permission_classes([IsStudentAuthenticated])
def my_course_detail(request):
    """
    Get detailed view of student's enrolled course with all modules and lessons
    """
    try:
        student = request.user
        print('=====',student)
        if not student.course:
            return Response({
                'error': 'You are not enrolled in any course'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CourseDetailSerializer(
            student.course,
            context={'request': request}
        )
        
        return Response({
            'message': 'Course details retrieved successfully',
            'course': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([StudentJWTAuthentication])
@permission_classes([IsStudentAuthenticated])
def module_detail(request, module_id):
    """
    Get detailed view of a specific module with all its lessons
    """
    try:
        student = request.user
        module = get_object_or_404(CourseModule, id=module_id, is_active=True)
        
        # Check if module belongs to student's course
        if student.course != module.course:
            return Response({
                'error': 'You do not have access to this module'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CourseModuleSerializer(
            module,
            context={'request': request}
        )
        
        return Response({
            'message': 'Module details retrieved successfully',
            'module': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([StudentJWTAuthentication])
@permission_classes([IsStudentAuthenticated])
def lesson_detail(request, lesson_id):
    """
    Get detailed view of a specific lesson
    """
    try:
        student = request.user
        lesson = get_object_or_404(Lesson, id=lesson_id, is_active=True)
        
        # Check if lesson belongs to student's course
        if student.course != lesson.module.course:
            return Response({
                'error': 'You do not have access to this lesson'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = LessonDetailSerializer(
            lesson,
            context={'request': request}
        )
        
        # Create or update progress entry (mark as accessed)
        progress, created = StudentProgress.objects.get_or_create(
            student=student,
            lesson=lesson,
            defaults={'status': 'in_progress'}
        )
        
        if progress.status == 'not_started':
            progress.status = 'in_progress'
            progress.save()
        
        return Response({
            'message': 'Lesson details retrieved successfully',
            'lesson': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([StudentJWTAuthentication])
@permission_classes([IsStudentAuthenticated])
def update_lesson_progress(request, lesson_id):
    """
    Update student's progress for a lesson
    Expected data:
    {
        "completion_percentage": 75.5,
        "time_spent_minutes": 15,
        "status": "in_progress" or "completed"
    }
    """
    try:
        student = request.user
        lesson = get_object_or_404(Lesson, id=lesson_id, is_active=True)
        
        # Check access
        if student.course != lesson.module.course:
            return Response({
                'error': 'You do not have access to this lesson'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get or create progress
        progress, created = StudentProgress.objects.get_or_create(
            student=student,
            lesson=lesson,
            defaults={'status': 'in_progress'}
        )
        
        # Update progress
        completion_percentage = request.data.get('completion_percentage', progress.completion_percentage)
        time_spent = request.data.get('time_spent_minutes', progress.time_spent_minutes)
        new_status = request.data.get('status', progress.status)
        
        progress.completion_percentage = completion_percentage
        progress.time_spent_minutes = time_spent
        progress.status = new_status
        
        # Mark completed time if status is completed
        if new_status == 'completed' and not progress.completed_at:
            progress.completed_at = timezone.now()
            progress.completion_percentage = 100.00
        
        progress.save()
        
        serializer = StudentProgressSerializer(progress)
        
        return Response({
            'message': 'Progress updated successfully',
            'progress': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@authentication_classes([StudentJWTAuthentication])
@permission_classes([IsStudentAuthenticated])
def lesson_notes(request, lesson_id):
    """
    GET: Get all notes for a lesson
    POST: Create a new note for a lesson
    Expected POST data:
    {
        "note_text": "This is my note",
        "timestamp_seconds": 120
    }
    """
    try:
        student = request.user
        lesson = get_object_or_404(Lesson, id=lesson_id, is_active=True)
        
        # Check access
        if student.course != lesson.module.course:
            return Response({
                'error': 'You do not have access to this lesson'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            # Get all notes for this lesson
            notes = StudentNote.objects.filter(
                student=student,
                lesson=lesson
            ).order_by('timestamp_seconds')
            
            serializer = StudentNoteSerializer(notes, many=True)
            
            return Response({
                'message': 'Notes retrieved successfully',
                'notes': serializer.data
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Create new note
            data = request.data.copy()
            data['student'] = student.id
            data['lesson'] = lesson.id
            
            serializer = StudentNoteSerializer(data=data)
            
            if serializer.is_valid():
                serializer.save(student=student, lesson=lesson)
                return Response({
                    'message': 'Note created successfully',
                    'note': serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@authentication_classes([StudentJWTAuthentication])
@permission_classes([IsStudentAuthenticated])
def note_detail(request, note_id):
    """
    PUT: Update a note
    DELETE: Delete a note
    """
    try:
        student = request.user
        note = get_object_or_404(StudentNote, id=note_id, student=student)
        
        if request.method == 'PUT':
            serializer = StudentNoteSerializer(note, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Note updated successfully',
                    'note': serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            note.delete()
            return Response({
                'message': 'Note deleted successfully'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)



# 
# Add this temporary debug view to course_views.py

@api_view(['GET'])
@authentication_classes([StudentJWTAuthentication])
@permission_classes([IsStudentAuthenticated])
def debug_course(request):
    """
    Debug view to check what's happening with course data
    """
    try:
        student = request.user
        
        debug_info = {
            'student_id': student.id,
            'student_name': student.student_name,
            'student_course_id': student.course.id if student.course else None,
            'student_course_name': student.course.name if student.course else None,
        }
        
        # Check all courses in system
        from staff_app.models import Course
        all_courses = Course.objects.all()
        debug_info['all_courses'] = [
            {'id': c.id, 'name': c.name} for c in all_courses
        ]
        
        # Check modules for this course
        if student.course:
            from .models import CourseModule
            all_modules = CourseModule.objects.filter(course=student.course)
            debug_info['modules_for_my_course'] = [
                {
                    'id': m.id,
                    'title': m.title,
                    'course_id': m.course.id,
                    'course_name': m.course.name,
                    'is_active': m.is_active,
                    'order': m.order
                }
                for m in all_modules
            ]
            
            # Check all modules in system
            all_modules_system = CourseModule.objects.all()
            debug_info['all_modules_in_system'] = [
                {
                    'id': m.id,
                    'title': m.title,
                    'course_id': m.course.id,
                    'course_name': m.course.name,
                    'is_active': m.is_active
                }
                for m in all_modules_system
            ]
            
            # Check lessons
            from .models import Lesson
            all_lessons = Lesson.objects.filter(module__course=student.course)
            debug_info['lessons_for_my_course'] = [
                {
                    'id': l.id,
                    'title': l.title,
                    'module_id': l.module.id,
                    'module_title': l.module.title,
                    'is_active': l.is_active
                }
                for l in all_lessons
            ]
        
        return Response({
            'debug_info': debug_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_400_BAD_REQUEST)