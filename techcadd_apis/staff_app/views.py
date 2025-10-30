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

# Helper functions
def is_staff_user(user):
    """Check if user is an active staff member"""
    try:
        return StaffProfile.objects.filter(user=user, is_active=True).exists()
    except:
        return False

def get_staff_profile(user):
    """Get staff profile if user is staff"""
    try:
        return StaffProfile.objects.get(user=user, is_active=True)
    except StaffProfile.DoesNotExist:
        return None

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
    
    if not staff_profile:
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
    
    if not staff_profile:
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
    
    if not staff_profile:
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
    """Staff creates new student enquiry"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile:
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = CreateStudentSerializer(data=request.data, context={'request': request})
    
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
                    'password': student.password  # This will be the plain password for first time
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_students(request):
    """Staff views all students (with filtering options)"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile:
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get query parameters for filtering
    enquiry_status = request.GET.get('enquiry_status')
    trade = request.GET.get('trade')
    centre = request.GET.get('centre')
    
    students = Student_api.objects.all()
    
    # Apply filters
    if enquiry_status:
        students = students.filter(enquiry_status=enquiry_status)
    if trade:
        students = students.filter(trade=trade)
    if centre:
        students = students.filter(centre=centre)
    
    # If staff is not manager, only show their assigned enquiries
    if staff_profile.role not in ['manager']:
        students = students.filter(assign_enquiry=staff_profile)
    
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
    
    if not staff_profile:
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

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_student(request, student_id):
    """Staff updates student information"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile:
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        student = Student_api.objects.get(id=student_id)
        
        # Check if staff has permission to update this student
        if staff_profile.role not in ['manager'] and student.assign_enquiry != staff_profile:
            return Response({
                'error': 'Access denied. You can only update your assigned students.'
            }, status=status.HTTP_403_FORBIDDEN)
        
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_stats(request):
    """Get student statistics for dashboard"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile:
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
    
    if not staff_profile:
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
    
    if not staff_profile:
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
    
    if not staff_profile:
        return Response({
            'error': 'Access denied. Staff privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        courses = Course.objects.filter(course_type_id=course_type_id, is_active=True)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)
    except Course.DoesNotExist:
        return Response([])

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def create_student_registration(request):
#     """Create new student registration"""
#     staff_profile = get_staff_profile(request.user)
    
#     if not staff_profile:
#         return Response({
#             'error': 'Access denied. Staff privileges required.'
#         }, status=status.HTTP_403_FORBIDDEN)
    
#     serializer = CreateStudentRegistrationSerializer(
#         data=request.data, 
#         context={'request': request}
#     )
    
#     if serializer.is_valid():
#         try:
#             registration = serializer.save()
            
#             # Return registration with generated credentials
#             response_serializer = StudentRegistrationSerializer(registration)
            
#             return Response({
#                 'message': 'Student registration created successfully',
#                 'registration': response_serializer.data,
#                 'login_credentials': {
#                     'username': registration.username,
#                     'password': registration.password
#                 }
#             }, status=status.HTTP_201_CREATED)
            
#         except Exception as e:
#             return Response({
#                 'error': f'Failed to create registration: {str(e)}'
#             }, status=status.HTTP_400_BAD_REQUEST)
    
#     return Response({
#         'error': 'Validation failed',
#         'details': serializer.errors
#     }, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_student_registration(request):
    """Create new student registration"""
    staff_profile = get_staff_profile(request.user)
    
    if not staff_profile:
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
            
            # Use special serializer that shows password ONLY for create response
            response_serializer = CreateStudentRegistrationResponseSerializer(registration)
            
            return Response({
                'message': 'Student registration created successfully',
                'registration': response_serializer.data,
                'login_credentials': {
                    'username': registration.username,
                    'password': registration.password  # Show only once
                }
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
    
    if not staff_profile:
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
    
    if not staff_profile:
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
    
    if not staff_profile:
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
    
    if not staff_profile:
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
    
    if not staff_profile:
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
    
    if not staff_profile:
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
    if not staff_profile:
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