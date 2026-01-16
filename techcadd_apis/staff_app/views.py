# staff_app/views.py
from rest_framework import status
from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .models import StaffProfile
from .serializers import *
from .models import Student_api
from .serializers import StudentSerializer, CreateStudentSerializer, StudentListSerializer, UpdateStudentSerializer
from django.db import transaction
from staff_app.serializers import ConvertEnquiryToRegistrationSerializer
# Helper functions
# def is_staff_user(user):
#     """Check if user is an active staff member"""
#     try:
#         return StaffProfile.objects.filter(user=user, is_active=True).exists()
#     except:
#         return False
# -----------------------------start here permissions ---------------------
def is_staff_user(user):
    """Check if user is an active staff member OR an admin"""
    try:
        # Check if user is a superuser (Admin)
        if hasattr(user, 'is_superuser') and user.is_superuser:
            return True
        
        # Check if user is an active staff member
        return StaffProfile.objects.filter(user=user, is_active=True).exists()
    except:
        return False


def get_staff_profile(user):
    """Get staff profile if user is staff (returns None for admins)"""
    try:
        if hasattr(user, 'is_superuser') and user.is_superuser:
            return None
        
        return StaffProfile.objects.get(user=user, is_active=True)
    except StaffProfile.DoesNotExist:
        return None


def is_admin_user(user):
    """Helper function to explicitly check if user is admin"""
    return hasattr(user, 'is_superuser') and user.is_superuser
#  -----------------------admin function ends here -------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def staff_login(request):
    serializer = StaffLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        staff_profile = serializer.validated_data['staff_profile']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Staff login successful',
            'user_type': 'staff',
            'role': staff_profile.role,
            'user': UserSerializer(user).data,
            'staff_profile': StaffProfileSerializer(staff_profile).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_logout(request):
    # Check if user is staff
    if not is_staff_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Staff logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_staff_token(request):
    """Verify if the current token belongs to an active staff user"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile:
        return Response({
            'valid': False,
            'error': 'User is not an active staff member'
        }, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        'valid': True,
        'user_type': 'staff',
        'role': staff_profile.role,
        'user': UserSerializer(request.user).data,
        'staff_profile': StaffProfileSerializer(staff_profile).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_profile(request):
    """Get current staff user profile"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = StaffProfileSerializer(staff_profile)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_dashboard(request):
    """Staff dashboard - accessible to all staff"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    dashboard_data = {
        'welcome_message': f'Welcome, {request.user.first_name or request.user.username}!',
        'role': staff_profile.role,
        'department': staff_profile.department,
        'quick_stats': {
            'pending_tasks': 5,
            'completed_today': 12,
            'messages': 3,
        }
    }
    
    return Response(dashboard_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_reports(request):
    """Staff reports - role-based access"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Check if user has permission to view reports (managers and sales can view)
    if staff_profile.role not in ['manager', 'sales']:
        return Response({
            'error': 'Access denied. Manager or Sales privileges required to view reports.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    reports_data = {
        'daily_sales': 1500,
        'new_customers': 23,
        'pending_orders': 7,
        'available_for_role': staff_profile.role,
    }
    
    return Response(reports_data)

@api_view(['POST'])
@permission_classes([AllowAny])
def staff_token_refresh(request):
    """Custom token refresh that verifies the user is still an active staff"""
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response({
            'error': 'Refresh token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        user_id = refresh['user_id']
        
        # Verify user exists and is still an active staff
        user = User.objects.get(id=user_id)
        staff_profile = get_staff_profile(user)
        
        if not staff_profile:
            return Response({
                'error': 'Staff account not found or inactive'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate new access token
        new_access_token = str(refresh.access_token)
        
        return Response({
            'access': new_access_token
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    

# staff_app/views.py - Update the student views to use Student_api
# --------------------students Views --------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_student(request):
    """
    Staff creates new student enquiry
    
    Required fields:
    - student_name, date_of_birth, qualification
    - student_type (college/school/working)
    - Based on student_type:
        * college: semester, college_name
        * school: class_name, school_name
        * working: job_role, company_name
    - mobile, email, address
    - centre, batch_time, class_mode
    - course_interested, trade, enquiry_source
    
    Optional fields:
    - assign_enquiry, course_fee_offer
    - enquiry_status, remark, next_follow_up_date
    """
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = CreateStudentSerializer(
        data=request.data, 
        context={'request': request}
    )
    
    if serializer.is_valid():
        try:
            student = serializer.save()
            
            # Return student details with generated credentials
            response_serializer = StudentSerializer(student)
            
            return Response({
                'message': 'Student created successfully',
                'student': response_serializer.data,
                'login_credentials': {
                    'username': student.username,
                    'password': student.password  # Plain password for first time only
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create student: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'error': 'Validation failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def list_students(request):
#     """Staff views all students (with filtering options)"""
#     staff_profile = get_staff_profile(request.user)
    
#     if not staff_profile and not is_admin_user(request.user):
#         return Response({
#             'error': 'Access denied. Staff privileges required.'
#         }, status=status.HTTP_403_FORBIDDEN)
    
#     # Get query parameters for filtering
#     enquiry_status = request.GET.get('enquiry_status')
#     trade = request.GET.get('trade')
#     centre = request.GET.get('centre')
    
#     students = Student_api.objects.all()
    
#     # Apply filters
#     if enquiry_status:
#         students = students.filter(enquiry_status=enquiry_status)
#     if trade:
#         students = students.filter(trade=trade)
#     if centre:
#         students = students.filter(centre=centre)
    
#     # If staff is not manager, only show their assigned enquiries
#     if staff_profile.role not in ['manager']:
#         students = students.filter(assign_enquiry=staff_profile)
    
#     serializer = StudentListSerializer(students, many=True)
    
#     return Response({
#         'count': students.count(),
#         'students': serializer.data
#     })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_students(request):
    """Staff views all students (with filtering options)"""
    staff_profile = get_staff_profile(request.user)
    
    # First, check if user is admin - admins can see everything
    if is_admin_user(request.user):
        # Admins can see all students, no filtering needed
        students = Student_api.objects.all()
    elif not staff_profile:
        # Non-admin users without staff profile are denied
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    else:
        # Regular staff users - start with all students
        students = Student_api.objects.all()
        
        # If staff is not manager, only show their assigned enquiries
        if staff_profile.role not in ['manager']:
            students = students.filter(assign_enquiry=staff_profile)
    
    # Get query parameters for filtering
    enquiry_status = request.GET.get('enquiry_status')
    trade = request.GET.get('trade')
    centre = request.GET.get('centre')
    
    # Apply filters (for both admin and staff)
    if enquiry_status:
        students = students.filter(enquiry_status=enquiry_status)
    if trade:
        students = students.filter(trade=trade)
    if centre:
        students = students.filter(centre=centre)
    
    serializer = StudentListSerializer(students, many=True)
    
    return Response({
        'count': students.count(),
        'students': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_detail(request, student_id):
    """Staff gets specific student details"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = Student_api.objects.get(id=student_id)
        
        # Check if staff has permission to view this student
        if staff_profile.role not in ['manager'] and student.assign_enquiry != staff_profile:
            return Response({
                'error': 'Access denied. You can only view your assigned students.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StudentSerializer(student)
        return Response(serializer.data)
        
    except Student_api.DoesNotExist:
        return Response({
            'error': 'Student not found'
        }, status=status.HTTP_404_NOT_FOUND)

# @api_view(['PUT'])
# @permission_classes([IsAuthenticated])
# def update_student(request, student_id):
#     """Staff updates student information"""
#     staff_profile = get_staff_profile(request.user)
    
#     if not staff_profile and not is_admin_user(request.user):
#         return Response({
#             'error': 'Access denied. Staff privileges required.'
#         }, status=status.HTTP_403_FORBIDDEN)
    
#     try:
#         student = Student_api.objects.get(id=student_id)
        
#         # Check if staff has permission to update this student
#         if staff_profile.role not in ['manager'] and student.assign_enquiry != staff_profile:
#             return Response({
#                 'error': 'Access denied. You can only update your assigned students.'
#             }, status=status.HTTP_403_FORBIDDEN)
        
#         serializer = UpdateStudentSerializer(student, data=request.data, partial=True)
        
#         if serializer.is_valid():
#             serializer.save()
            
#             # Return updated student data
#             updated_student = Student_api.objects.get(id=student_id)
#             response_serializer = StudentSerializer(updated_student)
            
#             return Response({
#                 'message': 'Student updated successfully',
#                 'student': response_serializer.data
#             })
        
#         return Response({
#             'error': 'Validation failed',
#             'details': serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
        
#     except Student_api.DoesNotExist:
#         return Response({
#             'error': 'Student not found'
#         }, status=status.HTTP_404_NOT_FOUND)
# staff_app/views.py - Replace existing update_student view



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_student(request, student_id):
    """
    Staff updates student information.
    When status is changed to 'admission_done', automatically converts to registration.
    """
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = Student_api.objects.get(id=student_id)
        
        # Check if staff has permission to update this student
        if staff_profile and staff_profile.role not in ['manager'] and student.assign_enquiry != staff_profile:
            return Response({
                'error': 'Access denied. You can only update your assigned students.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if enquiry status is being changed to 'admission_done'
        new_status = request.data.get('enquiry_status')
        
        if new_status == 'admission_done' and student.enquiry_status != 'admission_done':
            # Check if already converted
            if student.converted_to_registration:
                return Response({
                    'error': 'This enquiry has already been converted to registration',
                    'registration_id': student.registration_id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Attempt to convert to registration
            return convert_enquiry_to_registration(request, student, staff_profile)
        
        # Normal update (not admission_done)
        serializer = UpdateStudentSerializer(student, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            
            # Return updated student data
            updated_student = Student_api.objects.get(id=student_id)
            response_serializer = StudentSerializer(updated_student)
            
            return Response({
                'message': 'Student updated successfully',
                'student': response_serializer.data
            })
        
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Student_api.DoesNotExist:
        return Response({
            'error': 'Student not found'
        }, status=status.HTTP_404_NOT_FOUND)


def convert_enquiry_to_registration(request, enquiry, staff_profile):
    """
    Helper function to convert enquiry to registration.
    Validates all required fields and creates registration.
    """
    
    # List of required fields for registration
    required_fields = [
        'father_name', 'course_type', 'course', 
        'total_course_fee', 'branch', 'joining_date'
    ]
    
    # Check if conversion data is provided
    conversion_data = request.data.get('registration_data', {})
    
    if not conversion_data:
        return Response({
            'error': 'Cannot convert to registration',
            'message': 'Additional information required for registration',
            'required_fields': required_fields,
            'missing_fields_help': {
                'father_name': 'Father\'s name is required',
                'course_type': 'Select course type (ID)',
                'course': 'Select specific course (ID)',
                'total_course_fee': 'Enter total course fee amount',
                'branch': 'Select branch for registration',
                'joining_date': 'Enter joining date (YYYY-MM-DD)',
                'paid_fee': 'Enter initial payment amount (optional, default: 0)',
                'work_college': 'Current workplace/college (optional)',
                'contact_address': 'Full address (optional, will use enquiry address)',
                'whatsapp_no': 'WhatsApp number (optional)',
                'parents_no': 'Parent\'s contact number (optional)'
            },
            'example': {
                'enquiry_status': 'admission_done',
                'registration_data': {
                    'father_name': 'Ramesh Kumar',
                    'course_type': 1,
                    'course': 5,
                    'total_course_fee': 45000.00,
                    'paid_fee': 15000.00,
                    'branch': 'jalandhar1',
                    'joining_date': '2024-12-30',
                    'work_college': 'DAV College',
                    'contact_address': 'Model Town, Jalandhar',
                    'whatsapp_no': '9876543210',
                    'parents_no': '9988776655'
                }
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate conversion data
    conversion_serializer = ConvertEnquiryToRegistrationSerializer(data=conversion_data)
    
    if not conversion_serializer.is_valid():
        return Response({
            'error': 'Invalid registration data',
            'details': conversion_serializer.errors,
            'help': 'Please provide all required fields to convert enquiry to registration'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Prepare registration data from enquiry + conversion data
    validated_conversion_data = conversion_serializer.validated_data
    
    # ⭐ FIX: Extract IDs from the validated model instances
    course_type_id = validated_conversion_data['course_type'].id
    course_id = validated_conversion_data['course'].id
    
    registration_data = {
        # From conversion data (required) - ⭐ Use IDs instead of objects
        'father_name': validated_conversion_data['father_name'],
        'course_type': course_type_id,  # ⭐ Changed
        'course': course_id,  # ⭐ Changed
        'total_course_fee': validated_conversion_data['total_course_fee'],
        'paid_fee': validated_conversion_data.get('paid_fee', 0),
        'branch': validated_conversion_data['branch'],
        'joining_date': validated_conversion_data['joining_date'],
        
        # From enquiry (student personal details)
        'student_name': enquiry.student_name,
        'date_of_birth': enquiry.date_of_birth,
        'qualification': enquiry.qualification,
        'student_type': enquiry.student_type,
        'semester': enquiry.semester,
        'college_name': enquiry.college_name,
        'class_name': enquiry.class_name,
        'school_name': enquiry.school_name,
        'job_role': enquiry.job_role,
        'company_name': enquiry.company_name,
        'email': enquiry.email,
        'phone_no': enquiry.mobile,
        'class_mode': enquiry.class_mode,
        
        # From conversion data or auto-fill
        'work_college': validated_conversion_data.get('work_college') or enquiry.college_name or enquiry.school_name or enquiry.company_name or '',
        'contact_address': validated_conversion_data.get('contact_address') or enquiry.address,
        'whatsapp_no': validated_conversion_data.get('whatsapp_no', ''),
        'parents_no': validated_conversion_data.get('parents_no', ''),
        
        # Course details
        'duration_months': validated_conversion_data['duration_months'],
        'duration_hours': validated_conversion_data['duration_hours'],
        'software_covered': validated_conversion_data['software_covered'],
    }
    
    # Use transaction to ensure both operations succeed or fail together
    try:
        with transaction.atomic():
            # Create registration
            registration_serializer = CreateStudentRegistrationSerializer(
                data=registration_data,
                context={'request': request}
            )
            
            if registration_serializer.is_valid():
                registration = registration_serializer.save()
                
                # Update enquiry to mark as converted
                enquiry.enquiry_status = 'admission_done'
                enquiry.converted_to_registration = True
                enquiry.registration_id = registration.id
                enquiry.save()
                
                # Prepare response
                response_serializer = CreateStudentRegistrationResponseSerializer(registration)
                
                return Response({
                    'message': 'Enquiry successfully converted to registration',
                    'enquiry': {
                        'id': enquiry.id,
                        'student_name': enquiry.student_name,
                        'status': 'admission_done',
                        'converted': True
                    },
                    'registration': response_serializer.data,
                    'registration_summary': {
                        'registration_number': registration.registration_number,
                        'student_name': registration.student_name,
                        'branch': registration.get_branch_display(),
                        'course': registration.course.name,
                        'class_mode': registration.get_class_mode_display(),
                        'student_type': registration.get_student_type_display(),
                        'joining_date': str(registration.joining_date),
                        'completion_date': str(registration.course_completion_date),
                        'total_fee': float(registration.total_course_fee),
                        'paid_fee': float(registration.paid_fee),
                        'balance_fee': float(registration.fee_balance)
                    },
                    'login_credentials': {
                        'username': registration.username,
                        'password': registration.password,
                        'note': 'Please save these credentials securely. Password will not be shown again.'
                    }
                }, status=status.HTTP_201_CREATED)
            
            else:
                return Response({
                    'error': 'Failed to create registration',
                    'details': registration_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'error': 'Failed to convert enquiry to registration',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_stats(request):
    """Get student statistics for dashboard"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Base queryset
    if staff_profile.role == 'manager':
        students = Student_api.objects.all()
    else:
        students = Student_api.objects.filter(assign_enquiry=staff_profile)
    
    total_students = students.count()
    new_enquiries = students.filter(enquiry_status='new').count()
    converted_students = students.filter(enquiry_status='admission_done').count()
    
    # Trade-wise distribution
    trade_stats = students.values('trade').annotate(count=Count('id'))
    
    # Status-wise distribution
    status_stats = students.values('enquiry_status').annotate(count=Count('id'))
    
    # Centre-wise distribution
    centre_stats = students.values('centre').annotate(count=Count('id'))
    
    return Response({
        'total_students': total_students,
        'new_enquiries': new_enquiries,
        'converted_students': converted_students,
        'trade_distribution': list(trade_stats),
        'status_distribution': list(status_stats),
        'centre_distribution': list(centre_stats)
    })


# staff_app/views.py - Add this view
# this is for dropdown
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_options(request):
    """Get all choice options for student forms"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all staff for assign enquiry dropdown
    staff_members = StaffProfile.objects.filter(is_active=True).select_related('user')
    staff_options = [{'id': staff.id, 'name': staff.user.get_full_name() or staff.user.username} for staff in staff_members]
    
    return Response({
        'centre_choices': Student_api.CENTRE_CHOICES,
        'trade_choices': Student_api.TRADE_CHOICES,
        'enquiry_source_choices': Student_api.ENQUIRY_SOURCE_CHOICES,
        'enquiry_status_choices': Student_api.ENQUIRY_STATUS,
        'staff_options': staff_options
    })

# --------------------registration Views start from here --------------------
# staff_app/views.py - Add these views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_registration_options(request):
    """Get all options for registration form"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    course_types = CourseType.objects.filter(is_active=True)
    course_types_serializer = CourseTypeSerializer(course_types, many=True)
    
    duration_choices = []
    for choice in Course.DURATION_CHOICES:
        duration_choices.append({
            'value': choice[0],
            'label': choice[1]
        })
    
    return Response({
        'course_types': course_types_serializer.data,
        'duration_choices': duration_choices,
        'branch_choices': StudentRegistration.CENTRE_CHOICES
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_courses_by_type(request, course_type_id):
    """Get courses by course type"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        courses = Course.objects.filter(course_type_id=course_type_id, is_active=True)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)
    except Course.DoesNotExist:
        return Response([])

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_student_registration(request):
    """
    Staff creates new student registration
    
    Required fields:
    - branch, joining_date
    - student_name, father_name, date_of_birth, qualification
    - student_type (college/school/working)
    - Based on student_type:
        * college: semester, college_name
        * school: class_name, school_name
        * working: job_role, company_name
    - work_college (workplace or college name)
    - email, contact_address, phone_no
    - course_type, course, class_mode
    - duration_months, duration_hours
    - total_course_fee
    
    Optional fields:
    - whatsapp_no, parents_no
    - software_covered (overrides course software)
    - paid_fee (defaults to 0)
    
    Conditional fields:
    - class_name, school_name (required if student_type='school')
    - semester, college_name (required if student_type='college')
    - job_role, company_name (required if student_type='working')
    """
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = CreateStudentRegistrationSerializer(
        data=request.data, 
        context={'request': request}
    )
    
    if serializer.is_valid():
        try:
            registration = serializer.save()
            
            # Use special serializer that shows all registration details
            response_serializer = CreateStudentRegistrationResponseSerializer(registration)
            
            return Response({
                'message': 'Student registration created successfully',
                'registration': response_serializer.data,
                'registration_details': {
                    'registration_number': registration.registration_number,
                    'student_name': registration.student_name,
                    'branch': registration.get_branch_display(),
                    'course': registration.course.name if registration.course else None,
                    'class_mode': registration.get_class_mode_display(),
                    'student_type': registration.get_student_type_display(),
                    'joining_date': registration.joining_date,
                    'completion_date': registration.course_completion_date,
                    'total_fee': float(registration.total_course_fee),
                    'paid_fee': float(registration.paid_fee),
                    'balance_fee': float(registration.fee_balance)
                },
                'login_credentials': {
                    'username': registration.username,
                    'password': registration.password,  # Show plain password only once
                    'note': 'Please save these credentials securely. Password will not be shown again.'
                },
                'student_type_specific_info': registration.get_student_info()
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create registration: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'error': 'Validation failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_student_registrations(request):
    """List all student registrations"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    registrations = StudentRegistration.objects.select_related(
        'course_type', 'course', 'created_by__user'
    ).all()
    
    # Filter by branch if provided
    branch = request.GET.get('branch')
    if branch:
        registrations = registrations.filter(branch=branch)
    
    # Filter by course type if provided
    course_type = request.GET.get('course_type')
    if course_type:
        registrations = registrations.filter(course_type_id=course_type)
    
    serializer = StudentRegistrationSerializer(registrations, many=True)
    
    return Response({
        'count': registrations.count(),
        'registrations': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_registration_detail(request, registration_id):
    """Get specific registration details"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        registration = StudentRegistration.objects.get(id=registration_id)
        serializer = StudentRegistrationSerializer(registration)
        return Response(serializer.data)
    except StudentRegistration.DoesNotExist:
        return Response({
            'error': 'Registration not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_student_registrations(request):
    """Search student registrations - SECURE (no password)"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    search_query = request.GET.get('q')
    if not search_query:
        return Response({
            'error': 'Search query (q) parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    registrations = StudentRegistration.objects.select_related(
        'course_type', 'course', 'created_by__user'
    ).filter(
        models.Q(registration_number__icontains=search_query) |
        models.Q(student_name__icontains=search_query) |
        models.Q(email__icontains=search_query) |
        models.Q(phone_no__icontains=search_query) |
        models.Q(father_name__icontains=search_query)
    )
    
    # Use secure serializer (no password)
    serializer = StudentRegistrationSerializer(registrations, many=True)
    
    return Response({
        'search_query': search_query,
        'count': registrations.count(),
        'registrations': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_student_password(request, registration_id):
    """Staff can reset student password"""
    # Generate new password and show it once
    # Then student should change it immediately
    pass

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_change_password(request):
    """Student changes their own password"""
    # Student authentication required
    pass

# new views for fee and certifications
# staff_app/views.py - Add new views

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_student_fee(request):
    registration_number = request.GET.get('registration_number')
    if not registration_number:
        return Response({'error': 'registration_number parameter is required'}, status=400)
    print(' i am here for update fee----------------')
    
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        registration = StudentRegistration.objects.get(registration_number=registration_number)
        serializer = UpdateFeeSerializer(registration, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            
            # Return updated registration
            response_serializer = StudentRegistrationSerializer(registration)
            return Response({
                'message': 'Fee updated successfully',
                'registration': response_serializer.data
            })
        
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except StudentRegistration.DoesNotExist:
        return Response({
            'error': 'Registration not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_certificate(request):
    """Generate certificate for student if eligible"""
    registration_number = request.GET.get('registration_number')
    if not registration_number:
        return Response({'error': 'registration_number parameter is required'}, status=400)
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        registration = StudentRegistration.objects.get(registration_number=registration_number)
        
        # Check eligibility
        if not registration.is_eligible_for_certificate():
            return Response({
                'error': 'Student is not eligible for certificate',
                'requirements': {
                    'fees_cleared': registration.paid_fee >= registration.total_course_fee,
                    'fees_paid': float(registration.paid_fee),
                    'total_fees': float(registration.total_course_fee),
                    'course_completed': registration.course_completion_date and timezone.now().date() >= registration.course_completion_date,
                    'course_completion_date': registration.course_completion_date,
                    'current_date': timezone.now().date()
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate certificate
        registration.certificate_issued = True
        registration.certificate_issue_date = timezone.now().date()
        registration.generate_certificate_number()
        registration.save()
        
        response_serializer = StudentRegistrationSerializer(registration)
        
        return Response({
            'message': 'Certificate generated successfully',
            'certificate_number': registration.certificate_number,
            'issue_date': registration.certificate_issue_date,
            'registration': response_serializer.data
        })
        
    except StudentRegistration.DoesNotExist:
        return Response({
            'error': 'Registration not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_fee_payment_history(request):
    """Get fee payment history (you can expand this with a Payment model later)"""
    registration_number = request.GET.get('registration_number')
    if not registration_number:
        return Response({'error': 'registration_number parameter is required'}, status=400)
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        registration = StudentRegistration.objects.get(registration_number=registration_number)
        
        # Get all payment transactions
        payment_transactions = PaymentTransaction.objects.filter(
            student_registration=registration
        ).order_by('installment_number')
        
        payment_serializer = PaymentTransactionSerializer(payment_transactions, many=True)
        
        # Calculate summary
        total_paid = sum([t.amount for t in payment_transactions])
        payment_percentage = (total_paid / registration.total_course_fee) * 100 if registration.total_course_fee > 0 else 0
        
        return Response({
            'registration_number': registration.registration_number,
            'student_name': registration.student_name,
            'total_course_fee': float(registration.total_course_fee),
            'total_paid_fee': float(total_paid),
            'fee_balance': float(registration.total_course_fee - total_paid),
            'payment_percentage': round(payment_percentage, 2),
            'total_installments': payment_transactions.count(),
            'payment_status': 'fully_paid' if total_paid >= registration.total_course_fee else 'partially_paid',
            'payment_history': payment_serializer.data
        })
        
    except StudentRegistration.DoesNotExist:
        return Response({
            'error': 'Registration not found'
        }, status=status.HTTP_404_NOT_FOUND)

        # new api for add payments 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_payment_installment(request):
    registration_number = request.GET.get('registration_number')
    
    if not registration_number:
        return Response({'error': 'registration_number parameter is required'}, status=400)
    staff_profile = get_staff_profile(request.user)
    if not staff_profile and not is_admin_user(request.user):
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    try:
        registration = StudentRegistration.objects.get(registration_number=registration_number)
        
        serializer = AddPaymentSerializer(
            data=request.data,
            context={
                'request': request,
                'registration': registration,
                'staff_profile': staff_profile
            }
        )
        
        if serializer.is_valid():
            payment = serializer.save()
            
            # Return updated payment history
            payment_history_url = f"/api/staff/registrations/{registration_number}/fee-history/"
            
            return Response({
                'message': f'Payment installment #{payment.installment_number} added successfully',
                'payment_details': PaymentTransactionSerializer(payment).data,
                'updated_balance': float(registration.total_course_fee - registration.paid_fee),
                'payment_history_url': payment_history_url
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except StudentRegistration.DoesNotExist:
        return Response({
            'error': 'Registration not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
# ========================BRANCH SECTIONS START HERE ================

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from staff_app.models import BranchProfile, Student_api, StudentRegistration
from staff_app.serializers import (
    BranchLoginSerializer, 
    BranchProfileSerializer,
    BranchDashboardSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def branch_login(request):
    """Branch user login"""
    serializer = BranchLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        branch_profile = serializer.validated_data['branch_profile']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Add branch info to token
        refresh['branch'] = branch_profile.branch
        refresh['user_type'] = 'branch'
        
        return Response({
            'message': 'Login successful',
            'branch': BranchProfileSerializer(branch_profile).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def branch_logout(request):
    """Branch user logout"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_branch_profile(request):
    """Get current branch user profile"""
    user = request.user
    
    try:
        branch_profile = BranchProfile.objects.get(user=user, is_active=True)
        serializer = BranchProfileSerializer(branch_profile)
        return Response(serializer.data)
        
    except BranchProfile.DoesNotExist:
        return Response({
            'error': 'Branch profile not found or inactive'
        }, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def branch_dashboard(request):
    """Get branch dashboard statistics"""
    user = request.user
    
    try:
        branch_profile = BranchProfile.objects.get(user=user, is_active=True)
        branch_name = branch_profile.branch
        
        # Date calculations
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # ========== ENQUIRY STATISTICS ==========
        enquiries = Student_api.objects.filter(centre=branch_name)
        
        total_enquiries = enquiries.count()
        enquiries_today = enquiries.filter(enquiry_date=today).count()
        enquiries_this_week = enquiries.filter(enquiry_date__gte=week_start).count()
        enquiries_this_month = enquiries.filter(enquiry_date__gte=month_start).count()
        
        # Enquiry status breakdown
        enquiry_status_breakdown = {}
        for status_choice in Student_api.ENQUIRY_STATUS:
            count = enquiries.filter(enquiry_status=status_choice[0]).count()
            enquiry_status_breakdown[status_choice[1]] = count
        
        # ========== REGISTRATION STATISTICS ==========
        registrations = StudentRegistration.objects.filter(branch=branch_name)
        
        total_registrations = registrations.count()
        registrations_today = registrations.filter(joining_date=today).count()
        registrations_this_week = registrations.filter(joining_date__gte=week_start).count()
        registrations_this_month = registrations.filter(joining_date__gte=month_start).count()
        
        # Student type breakdown
        student_type_breakdown = {}
        for type_choice in StudentRegistration.STUDENT_TYPE_CHOICES:
            count = registrations.filter(student_type=type_choice[0]).count()
            student_type_breakdown[type_choice[1]] = count
        
        # Class mode breakdown
        class_mode_breakdown = {}
        for mode_choice in StudentRegistration.CLASS_MODE_CHOICES:
            count = registrations.filter(class_mode=mode_choice[0]).count()
            class_mode_breakdown[mode_choice[1]] = count
        
        # ========== FINANCIAL STATISTICS ==========
        financial_data = registrations.aggregate(
            total_fees=Sum('total_course_fee'),
            collected_fees=Sum('paid_fee'),
            pending_fees=Sum('fee_balance')
        )
        
        total_course_fees = financial_data['total_fees'] or 0
        total_fees_collected = financial_data['collected_fees'] or 0
        total_fees_pending = financial_data['pending_fees'] or 0
        
        # ========== COURSE STATUS ==========
        courses_ongoing = 0
        courses_completed = 0
        courses_not_started = 0
        
        for registration in registrations:
            status = registration.get_course_status()
            if status == 'ongoing':
                courses_ongoing += 1
            elif status == 'completed':
                courses_completed += 1
            elif status == 'not_started':
                courses_not_started += 1
        
        # ========== CERTIFICATE STATISTICS ==========
        certificates_issued = registrations.filter(certificate_issued=True).count()
        students_eligible = sum(1 for reg in registrations if reg.is_eligible_for_certificate())
        
        # ========== PREPARE RESPONSE ==========
        dashboard_data = {
            'branch_name': branch_name,
            'branch_display': branch_profile.get_branch_display(),
            
            # Enquiries
            'total_enquiries': total_enquiries,
            'enquiries_today': enquiries_today,
            'enquiries_this_week': enquiries_this_week,
            'enquiries_this_month': enquiries_this_month,
            'enquiry_status_breakdown': enquiry_status_breakdown,
            
            # Registrations
            'total_registrations': total_registrations,
            'registrations_today': registrations_today,
            'registrations_this_week': registrations_this_week,
            'registrations_this_month': registrations_this_month,
            'student_type_breakdown': student_type_breakdown,
            'class_mode_breakdown': class_mode_breakdown,
            
            # Financial
            'total_course_fees': total_course_fees,
            'total_fees_collected': total_fees_collected,
            'total_fees_pending': total_fees_pending,
            
            # Course Status
            'courses_ongoing': courses_ongoing,
            'courses_completed': courses_completed,
            'courses_not_started': courses_not_started,
            
            # Certificates
            'certificates_issued': certificates_issued,
            'students_eligible_for_certificate': students_eligible,
        }
        
        serializer = BranchDashboardSerializer(dashboard_data)
        return Response(serializer.data)
        
    except BranchProfile.DoesNotExist:
        return Response({
            'error': 'Branch profile not found or inactive'
        }, status=status.HTTP_403_FORBIDDEN)

from rest_framework.pagination import PageNumberPagination



class BranchPagination(PageNumberPagination):
    """Custom pagination for branch views"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def branch_enquiries(request):
    """
    Get all enquiries for the branch with comprehensive filtering
    
    Filter Parameters:
    - enquiry_status: Filter by status (e.g., in_process, visited, positive)
    - trade: Filter by trade (e.g., programming, graphic_designing)
    - class_mode: Filter by class mode (e.g., online, offline, both)
    - enquiry_source: Filter by source (e.g., social_media, friend_reference)
    - student_type: Filter by type (e.g., college, school, working)
    - converted: Filter by conversion status (true/false)
    - search: Search by name, email, or mobile
    - date_from: Filter enquiries from date (YYYY-MM-DD)
    - date_to: Filter enquiries to date (YYYY-MM-DD)
    - assigned_to: Filter by assigned staff ID
    
    Examples:
    GET /branch/enquiries/?enquiry_status=in_process
    GET /branch/enquiries/?trade=programming
    GET /branch/enquiries/?enquiry_status=in_process&trade=programming
    GET /branch/enquiries/?class_mode=online&student_type=college
    GET /branch/enquiries/?search=priya
    GET /branch/enquiries/?converted=false
    GET /branch/enquiries/?date_from=2024-01-01&date_to=2024-12-31
    """
    user = request.user
    
    try:
        branch_profile = BranchProfile.objects.get(user=user, is_active=True)
        branch_name = branch_profile.branch
        
        # Start with enquiries for this branch
        enquiries = Student_api.objects.filter(
            centre=branch_name
        ).select_related(
            'enquiry_taken_by__user',
            'assign_enquiry__user'
        ).order_by('-created_at')
        
        # ========================================
        # APPLY FILTERS
        # ========================================
        
        # Filter by enquiry_status
        enquiry_status = request.GET.get('enquiry_status')
        if enquiry_status:
            enquiries = enquiries.filter(enquiry_status=enquiry_status)
        
        # Filter by trade
        trade = request.GET.get('trade')
        if trade:
            enquiries = enquiries.filter(trade=trade)
        
        # Filter by class_mode
        class_mode = request.GET.get('class_mode')
        if class_mode:
            enquiries = enquiries.filter(class_mode=class_mode)
        
        # Filter by enquiry_source
        enquiry_source = request.GET.get('enquiry_source')
        if enquiry_source:
            enquiries = enquiries.filter(enquiry_source=enquiry_source)
        
        # Filter by student_type
        student_type = request.GET.get('student_type')
        if student_type:
            enquiries = enquiries.filter(student_type=student_type)
        
        # Filter by conversion status
        converted = request.GET.get('converted')
        if converted is not None:
            is_converted = converted.lower() == 'true'
            enquiries = enquiries.filter(converted_to_registration=is_converted)
        
        # Filter by assigned staff
        assigned_to = request.GET.get('assigned_to')
        if assigned_to:
            enquiries = enquiries.filter(assign_enquiry_id=assigned_to)
        
        # Filter by date range
        date_from = request.GET.get('date_from')
        if date_from:
            enquiries = enquiries.filter(enquiry_date__gte=date_from)
        
        date_to = request.GET.get('date_to')
        if date_to:
            enquiries = enquiries.filter(enquiry_date__lte=date_to)
        
        # Search functionality (name, email, mobile)
        search = request.GET.get('search')
        if search:
            enquiries = enquiries.filter(
                Q(student_name__icontains=search) |
                Q(email__icontains=search) |
                Q(mobile__icontains=search)
            )
        
        # Get total count before pagination
        total_count = enquiries.count()
        
        # Apply pagination
        paginator = BranchPagination()
        paginated_enquiries = paginator.paginate_queryset(enquiries, request)
        
        # Serialize
        from staff_app.serializers import StudentListSerializer
        serializer = StudentListSerializer(paginated_enquiries, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response({
            'branch': branch_profile.get_branch_display(),
            'total_enquiries': total_count,
            'enquiries': serializer.data,
            'filters_applied': {
                'enquiry_status': enquiry_status,
                'trade': trade,
                'class_mode': class_mode,
                'enquiry_source': enquiry_source,
                'student_type': student_type,
                'converted': converted,
                'search': search,
                'date_from': date_from,
                'date_to': date_to,
                'assigned_to': assigned_to
            }
        })
        
    except BranchProfile.DoesNotExist:
        return Response({
            'error': 'Branch profile not found or inactive'
        }, status=status.HTTP_403_FORBIDDEN)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def branch_registrations(request):
    """
    Get all registrations for the branch with comprehensive filtering
    
    Filter Parameters:
    - student_type: Filter by type (e.g., college, school, working)
    - class_mode: Filter by class mode (e.g., online, offline, both)
    - course_type: Filter by course type ID
    - course: Filter by course ID
    - certificate_issued: Filter by certificate status (true/false)
    - payment_status: Filter by payment (paid/pending/partial)
    - course_status: Filter by course status (not_started/ongoing/completed)
    - search: Search by name, email, phone, or registration number
    - date_from: Filter registrations from date (YYYY-MM-DD)
    - date_to: Filter registrations to date (YYYY-MM-DD)
    - created_by: Filter by staff ID who created the registration
    
    Examples:
    GET /branch/registrations/?student_type=college
    GET /branch/registrations/?class_mode=online
    GET /branch/registrations/?certificate_issued=false
    GET /branch/registrations/?payment_status=pending
    GET /branch/registrations/?course_status=ongoing
    GET /branch/registrations/?search=priya
    GET /branch/registrations/?student_type=college&class_mode=online
    GET /branch/registrations/?date_from=2024-01-01&date_to=2024-12-31
    """
    user = request.user
    
    try:
        branch_profile = BranchProfile.objects.get(user=user, is_active=True)
        branch_name = branch_profile.branch
        
        # Start with registrations for this branch
        registrations = StudentRegistration.objects.filter(
            branch=branch_name
        ).select_related(
            'course_type',
            'course',
            'created_by__user'
        ).order_by('-created_at')
        
        # ========================================
        # APPLY FILTERS
        # ========================================
        
        # Filter by student_type
        student_type = request.GET.get('student_type')
        if student_type:
            registrations = registrations.filter(student_type=student_type)
        
        # Filter by class_mode
        class_mode = request.GET.get('class_mode')
        if class_mode:
            registrations = registrations.filter(class_mode=class_mode)
        
        # Filter by course_type
        course_type = request.GET.get('course_type')
        if course_type:
            registrations = registrations.filter(course_type_id=course_type)
        
        # Filter by course
        course = request.GET.get('course')
        if course:
            registrations = registrations.filter(course_id=course)
        
        # Filter by certificate_issued
        certificate_issued = request.GET.get('certificate_issued')
        if certificate_issued is not None:
            is_issued = certificate_issued.lower() == 'true'
            registrations = registrations.filter(certificate_issued=is_issued)
        
        # Filter by payment_status
        payment_status = request.GET.get('payment_status')
        if payment_status:
            if payment_status == 'paid':
                registrations = registrations.filter(fee_balance=0)
            elif payment_status == 'pending':
                registrations = registrations.filter(fee_balance=models.F('total_course_fee'))
            elif payment_status == 'partial':
                registrations = registrations.filter(
                    fee_balance__gt=0,
                    fee_balance__lt=models.F('total_course_fee')
                )
        
        # Filter by course_status (not_started, ongoing, completed)
        course_status = request.GET.get('course_status')
        if course_status:
            today = timezone.now().date()
            
            if course_status == 'not_started':
                registrations = registrations.filter(joining_date__gt=today)
            elif course_status == 'ongoing':
                registrations = registrations.filter(
                    joining_date__lte=today,
                    course_completion_date__gte=today
                )
            elif course_status == 'completed':
                registrations = registrations.filter(course_completion_date__lt=today)
        
        # Filter by created_by staff
        created_by = request.GET.get('created_by')
        if created_by:
            registrations = registrations.filter(created_by_id=created_by)
        
        # Filter by date range (joining date)
        date_from = request.GET.get('date_from')
        if date_from:
            registrations = registrations.filter(joining_date__gte=date_from)
        
        date_to = request.GET.get('date_to')
        if date_to:
            registrations = registrations.filter(joining_date__lte=date_to)
        
        # Search functionality (name, email, phone, registration number)
        search = request.GET.get('search')
        if search:
            registrations = registrations.filter(
                Q(student_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_no__icontains=search) |
                Q(registration_number__icontains=search)
            )
        
        # Get total count before pagination
        total_count = registrations.count()
        
        # Apply pagination
        paginator = BranchPagination()
        paginated_registrations = paginator.paginate_queryset(registrations, request)
        
        # Serialize
        from staff_app.serializers import StudentRegistrationSerializer
        serializer = StudentRegistrationSerializer(paginated_registrations, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response({
            'branch': branch_profile.get_branch_display(),
            'total_registrations': total_count,
            'registrations': serializer.data,
            'filters_applied': {
                'student_type': student_type,
                'class_mode': class_mode,
                'course_type': course_type,
                'course': course,
                'certificate_issued': certificate_issued,
                'payment_status': payment_status,
                'course_status': course_status,
                'search': search,
                'date_from': date_from,
                'date_to': date_to,
                'created_by': created_by
            }
        })
        
    except BranchProfile.DoesNotExist:
        return Response({
            'error': 'Branch profile not found or inactive'
        }, status=status.HTTP_403_FORBIDDEN)
        

# ============================================
# OPTIONAL: Get Filter Options for Branch
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def branch_filter_options(request):
    """
    Returns all available filter options for the branch
    Useful for building dynamic filter dropdowns in frontend
    """
    user = request.user
    
    try:
        branch_profile = BranchProfile.objects.get(user=user, is_active=True)
        
        # Get courses available for this branch
        from staff_app.models import CourseType, Course
        course_types = CourseType.objects.all()
        courses = Course.objects.all()
        
        # Get staff members for this branch (for assigned_to filter)
        from staff_app.models import StaffProfile
        branch_staff = StaffProfile.objects.filter(
            branch=branch_profile.branch,
            is_active=True
        ).select_related('user')
        
        return Response({
            'enquiry_filters': {
                'enquiry_statuses': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in Student_api.ENQUIRY_STATUS
                ],
                'trades': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in Student_api.TRADE_CHOICES
                ],
                'enquiry_sources': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in Student_api.ENQUIRY_SOURCE_CHOICES
                ],
                'student_types': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in Student_api.STUDENT_TYPE_CHOICES
                ],
                'class_modes': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in Student_api.CLASS_MODE_CHOICES
                ],
                'staff': [
                    {
                        'value': staff.id,
                        'label': staff.user.get_full_name() or staff.user.username
                    }
                    for staff in branch_staff
                ]
            },
            'registration_filters': {
                'student_types': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in StudentRegistration.STUDENT_TYPE_CHOICES
                ],
                'class_modes': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in StudentRegistration.CLASS_MODE_CHOICES
                ],
                'course_types': [
                    {'value': ct.id, 'label': ct.name}
                    for ct in course_types
                ],
                'courses': [
                    {'value': c.id, 'label': c.name}
                    for c in courses
                ],
                'payment_statuses': [
                    {'value': 'paid', 'label': 'Fully Paid'},
                    {'value': 'pending', 'label': 'Payment Pending'},
                    {'value': 'partial', 'label': 'Partially Paid'}
                ],
                'course_statuses': [
                    {'value': 'not_started', 'label': 'Not Started'},
                    {'value': 'ongoing', 'label': 'Ongoing'},
                    {'value': 'completed', 'label': 'Completed'}
                ],
                'staff': [
                    {
                        'value': staff.id,
                        'label': staff.user.get_full_name() or staff.user.username
                    }
                    for staff in branch_staff
                ]
            }
        }, status=status.HTTP_200_OK)
        
    except BranchProfile.DoesNotExist:
        return Response({
            'error': 'Branch profile not found or inactive'
        }, status=status.HTTP_403_FORBIDDEN)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])  # You can change this to IsAdminUser if only admins should access
def list_all_branches(request):
    """
    Get list of all branches with their credentials (username only, no passwords)
    
    Query Parameters:
    - is_active: Filter by branch active status (true/false)
    - branch: Filter by specific branch name (e.g., jalandhar1)
    - search: Search by username, email, branch name
    - ordering: Order results (e.g., -created_at, username, branch)
    
    Examples:
    GET /branch/list/
    GET /branch/list/?is_active=true
    GET /branch/list/?branch=jalandhar1
    GET /branch/list/?search=jalandhar
    GET /branch/list/?ordering=-created_at
    """
    
    # Start with all branch profiles
    branches = BranchProfile.objects.select_related('user').all()
    
    # ========================================
    # APPLY FILTERS
    # ========================================
    
    # Filter by active status
    is_active = request.GET.get('is_active')
    if is_active is not None:
        active_status = is_active.lower() == 'true'
        branches = branches.filter(is_active=active_status)
    
    # Filter by specific branch
    branch = request.GET.get('branch')
    if branch:
        branches = branches.filter(branch=branch)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        branches = branches.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(branch__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Ordering
    ordering = request.GET.get('ordering', '-created_at')
    valid_orderings = ['created_at', '-created_at', 'username', '-username', 
                      'branch', '-branch', 'user__username', '-user__username']
    if ordering in valid_orderings:
        if ordering in ['username', '-username']:
            ordering = ordering.replace('username', 'user__username')
        branches = branches.order_by(ordering)
    
    # Get total count
    total_count = branches.count()
    
    # Serialize
    serializer = BranchListSerializer(branches, many=True)
    
    return Response({
        'total_branches': total_count,
        'branches': serializer.data,
        'filters_applied': {
            'is_active': is_active,
            'branch': branch,
            'search': search,
            'ordering': ordering
        }
    }, status=status.HTTP_200_OK)


# OPTIONAL: Get branch credentials summary (for admin dashboard)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def branch_credentials_summary(request):
    """
    Get summary of all branches and their credential status
    Useful for admin dashboard
    """
    
    all_branches = BranchProfile.CENTRE_CHOICES
    created_branches = BranchProfile.objects.select_related('user').all()
    
    branch_summary = []
    
    for branch_code, branch_name in all_branches:
        try:
            branch_profile = created_branches.get(branch=branch_code)
            branch_summary.append({
                'branch_code': branch_code,
                'branch_name': branch_name,
                'has_credentials': True,
                'username': branch_profile.user.username,
                'email': branch_profile.user.email,
                'is_active': branch_profile.is_active,
                'is_user_active': branch_profile.user.is_active,
                'created_at': branch_profile.created_at,
                'last_login': branch_profile.user.last_login
            })
        except BranchProfile.DoesNotExist:
            branch_summary.append({
                'branch_code': branch_code,
                'branch_name': branch_name,
                'has_credentials': False,
                'username': None,
                'email': None,
                'is_active': False,
                'is_user_active': False,
                'created_at': None,
                'last_login': None
            })
    
    total_branches = len(all_branches)
    branches_with_credentials = sum(1 for b in branch_summary if b['has_credentials'])
    branches_without_credentials = total_branches - branches_with_credentials
    active_branches = sum(1 for b in branch_summary if b['has_credentials'] and b['is_active'])
    
    return Response({
        'summary': {
            'total_branches': total_branches,
            'branches_with_credentials': branches_with_credentials,
            'branches_without_credentials': branches_without_credentials,
            'active_branches': active_branches,
            'inactive_branches': branches_with_credentials - active_branches
        },
        'branches': branch_summary
    }, status=status.HTTP_200_OK)