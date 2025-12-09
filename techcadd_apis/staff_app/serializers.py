# staff_app/serializers.py
from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import *

class StaffLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            
            if user:
                # Check if user has staff profile and is active
                try:
                    staff_profile = StaffProfile.objects.get(user=user, is_active=True)
                    data['user'] = user
                    data['staff_profile'] = staff_profile
                except StaffProfile.DoesNotExist:
                    raise serializers.ValidationError(
                        "Staff account not found or inactive."
                    )
            else:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials."
                )
        else:
            raise serializers.ValidationError(
                "Must include 'username' and 'password'."
            )

        return data

class StaffProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = StaffProfile
        fields = ('id', 'user_id', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'department', 'phone', 'address', 'is_active', 
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class CreateStaffSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    email = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = StaffProfile
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 
                 'role', 'department', 'phone', 'address')

    def create(self, validated_data):
        # Extract user data
        user_data = {
            'username': validated_data.pop('username'),
            'password': validated_data.pop('password'),
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name', ''),
            'last_name': validated_data.pop('last_name', ''),
        }
        
        # Create user
        user = User.objects.create_user(
            username=user_data['username'],
            password=user_data['password'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        
        # Create staff profile
        staff_profile = StaffProfile.objects.create(user=user, **validated_data)
        return staff_profile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

# staff_app/serializers.py - Add these to your existing serializers
from .models import Student_api

# class StudentSerializer(serializers.ModelSerializer):
#     enquiry_taken_by_name = serializers.CharField(source='enquiry_taken_by.user.get_full_name', read_only=True)
#     assign_enquiry_name = serializers.CharField(source='assign_enquiry.user.get_full_name', read_only=True)
#     enquiry_status_display = serializers.CharField(source='get_enquiry_status_display', read_only=True)
#     trade_display = serializers.CharField(source='get_trade_display', read_only=True)
#     centre_display = serializers.CharField(source='get_centre_display', read_only=True)
#     enquiry_source_display = serializers.CharField(source='get_enquiry_source_display', read_only=True)
    
#     class Meta:
#         model = Student_api
#         fields = (
#             'id', 'student_name', 'date_of_birth', 'qualification', 'work_college',
#             'mobile', 'email', 'address', 'enquiry_date', 'centre', 'centre_display',
#             'enquiry_taken_by', 'enquiry_taken_by_name', 'batch_time', 
#             'course_fee_offer', 'course_interested', 'trade', 'trade_display', 
#             'enquiry_source', 'enquiry_source_display', 'assign_enquiry', 
#             'assign_enquiry_name', 'enquiry_status', 'enquiry_status_display', 
#             'remark', 'next_follow_up_date', 'username', 'password', 'created_at'
#         )
#         read_only_fields = ('username', 'password', 'created_at', 'updated_at', 'enquiry_taken_by')

class CreateStudentSerializer(serializers.ModelSerializer):
    """Serializer for creating student enquiries"""
    
    class Meta:
        model = Student_api
        fields = (
            'student_name', 'date_of_birth', 'qualification', 
            'student_type', 'semester', 'college_name', 
            'class_name', 'school_name', 'job_role', 'company_name',
            'mobile', 'email', 'address', 
            'centre', 'batch_time', 'class_mode',
            'course_fee_offer', 'course_interested', 'trade', 
            'enquiry_source', 'assign_enquiry', 
            'enquiry_status', 'remark', 'next_follow_up_date'
        )
    
    def validate_mobile(self, value):
        """Validate mobile number format"""
        if len(value) < 10:
            raise serializers.ValidationError("Mobile number must be at least 10 digits")
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if Student_api.objects.filter(email=value).exists():
            raise serializers.ValidationError("A student with this email already exists.")
        return value
    
    def validate(self, data):
        """
        Cross-field validation based on student_type
        """
        student_type = data.get('student_type')
        
        # Validate College Student
        if student_type == 'college':
            if not data.get('semester'):
                raise serializers.ValidationError({
                    'semester': 'Semester is required for college students.'
                })
            if not data.get('college_name'):
                raise serializers.ValidationError({
                    'college_name': 'College name is required for college students.'
                })
            # Clear other type fields
            data['class_name'] = None
            data['school_name'] = None
            data['job_role'] = None
            data['company_name'] = None
        
        # Validate School Student
        elif student_type == 'school':
            if not data.get('class_name'):
                raise serializers.ValidationError({
                    'class_name': 'Class is required for school students.'
                })
            if not data.get('school_name'):
                raise serializers.ValidationError({
                    'school_name': 'School name is required for school students.'
                })
            # Clear other type fields
            data['semester'] = None
            data['college_name'] = None
            data['job_role'] = None
            data['company_name'] = None
        
        # Validate Working Professional
        elif student_type == 'working':
            if not data.get('job_role'):
                raise serializers.ValidationError({
                    'job_role': 'Job role is required for working professionals.'
                })
            if not data.get('company_name'):
                raise serializers.ValidationError({
                    'company_name': 'Company name is required for working professionals.'
                })
            # Clear other type fields
            data['semester'] = None
            data['college_name'] = None
            data['class_name'] = None
            data['school_name'] = None
        
        return data
    
    def create(self, validated_data):
        """Create student with auto-assigned staff"""
        # Get the staff member who is creating the student (from request)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            staff_profile = StaffProfile.objects.get(user=request.user)
            validated_data['enquiry_taken_by'] = staff_profile
            
            # If assign_enquiry is not provided, assign to current staff
            if not validated_data.get('assign_enquiry'):
                validated_data['assign_enquiry'] = staff_profile
        
        # Create student - username and password will be auto-generated in save()
        student = Student_api.objects.create(**validated_data)
        return student

class StudentSerializer(serializers.ModelSerializer):
    """Serializer for displaying complete student information"""
    
    enquiry_taken_by = StaffProfileSerializer(read_only=True)
    assign_enquiry = StaffProfileSerializer(read_only=True)
    
    # Display human-readable values
    centre_display = serializers.CharField(source='get_centre_display', read_only=True)
    trade_display = serializers.CharField(source='get_trade_display', read_only=True)
    enquiry_source_display = serializers.CharField(source='get_enquiry_source_display', read_only=True)
    enquiry_status_display = serializers.CharField(source='get_enquiry_status_display', read_only=True)
    student_type_display = serializers.CharField(source='get_student_type_display', read_only=True)
    class_mode_display = serializers.CharField(source='get_class_mode_display', read_only=True)
    
    # Add method field for student-specific info
    student_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Student_api
        fields = (
            'id', 'student_name', 'date_of_birth', 'qualification',
            'student_type', 'student_type_display',
            'semester', 'college_name',
            'class_name', 'school_name',
            'job_role', 'company_name',
            'student_info',
            'mobile', 'email', 'address',
            'enquiry_date', 'centre', 'centre_display',
            'enquiry_taken_by', 'assign_enquiry',
            'batch_time', 'class_mode', 'class_mode_display',
            'course_fee_offer', 'course_interested',
            'trade', 'trade_display',
            'enquiry_source', 'enquiry_source_display',
            'enquiry_status', 'enquiry_status_display',
            'remark', 'next_follow_up_date',
            'username',  # Include username but NOT password for security
            'created_at', 'updated_at'
        )
    
    def get_student_info(self, obj):
        """Get formatted student-specific information"""
        return obj.get_student_info()

class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing students"""
    
    enquiry_taken_by_name = serializers.CharField(
        source='enquiry_taken_by.user.get_full_name', 
        read_only=True
    )
    student_type_display = serializers.CharField(source='get_student_type_display', read_only=True)
    enquiry_status_display = serializers.CharField(source='get_enquiry_status_display', read_only=True)
    class_mode_display = serializers.CharField(source='get_class_mode_display', read_only=True)
    
    class Meta:
        model = Student_api
        fields = (
            'id', 'student_name', 'mobile', 'email',
            'student_type', 'student_type_display',
            'class_mode', 'class_mode_display',
            'course_interested', 'trade',
            'enquiry_status', 'enquiry_status_display',
            'enquiry_taken_by_name', 'next_follow_up_date',
            'created_at'
        )

class UpdateStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student_api
        fields = (
            'student_name', 'date_of_birth', 'qualification', 'work_college',
            'mobile', 'email', 'address', 'centre', 'batch_time', 
            'course_fee_offer', 'course_interested', 'trade', 'enquiry_source',
            'assign_enquiry', 'enquiry_status', 'remark', 'next_follow_up_date'
        )
    
    def validate_mobile(self, value):
        """Validate mobile number format"""
        if len(value) < 10:
            raise serializers.ValidationError("Mobile number must be at least 10 digits")
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness excluding current instance"""
        instance = self.instance
        if instance and Student_api.objects.filter(email=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError("A student with this email already exists.")
        return value

        # ----------------registration section start ================
# staff_app/serializers.py - Add these serializers

class CourseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseType
        fields = ('id', 'name')

class CourseSerializer(serializers.ModelSerializer):
    course_type_name = serializers.CharField(source='course_type.name', read_only=True)
    duration_months_display = serializers.CharField(source='get_duration_months_display', read_only=True)
    
    class Meta:
        model = Course
        fields = ('id', 'name', 'course_type', 'course_type_name', 'software_covered', 
                 'duration_months', 'duration_months_display', 'duration_hours', 'course_fee')

# class StudentRegistrationSerializer(serializers.ModelSerializer):
#     course_type_name = serializers.CharField(source='course_type.name', read_only=True)
#     course_name = serializers.CharField(source='course.name', read_only=True)
#     branch_display = serializers.CharField(source='get_branch_display', read_only=True)
#     duration_months_display = serializers.CharField(source='get_duration_months_display', read_only=True)
#     created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True)
    
#     class Meta:
#         model = StudentRegistration
#         fields = (
#             'id','registration_number', 'branch', 'branch_display', 'joining_date', 'student_name', 
#             'father_name', 'date_of_birth', 'email', 'qualification', 'work_college',
#             'contact_address', 'phone_no', 'whatsapp_no', 'parents_no', 'course_type',
#             'course_type_name', 'course', 'course_name', 'software_covered',
#             'duration_months', 'duration_months_display', 'duration_hours', 'course_fee',
#             'username', 'password', 'created_at', 'created_by', 'created_by_name'
#         )
#         read_only_fields = ('registration_number','username', 'password', 'created_at', 'created_by')
class StudentRegistrationSerializer(serializers.ModelSerializer):
    course_type_name = serializers.CharField(source='course_type.name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    branch_display = serializers.CharField(source='get_branch_display', read_only=True)
    duration_months_display = serializers.CharField(source='get_duration_months_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True)
    is_eligible_for_certificate = serializers.BooleanField(read_only=True)
    days_remaining_to_complete = serializers.SerializerMethodField(read_only=True)
    total_course_days = serializers.SerializerMethodField(read_only=True)  # ✅ CORRECT - Use SerializerMethodField
    course_status = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = StudentRegistration
        fields = (
            'id', 'registration_number', 'branch', 'branch_display', 'joining_date', 
            'student_name', 'father_name', 'date_of_birth', 'email', 'qualification', 
            'work_college', 'contact_address', 'phone_no', 'whatsapp_no', 'parents_no', 
            'course_type', 'course_type_name', 'course', 'course_name', 'software_covered',
            'duration_months', 'duration_months_display', 'duration_hours', 
            'total_course_fee', 'paid_fee', 'fee_balance',  # Fee fields
            'course_completion_date',  # Completion date
            'days_remaining_to_complete',  # NEW: Days remaining
            'course_status',
            'total_course_days', 
            'certificate_issued', 'certificate_number', 'certificate_issue_date',  # Certificate fields
            'is_eligible_for_certificate',  # Eligibility check
            'username', 'created_at', 'created_by', 'created_by_name'
        )
        read_only_fields = ('registration_number', 'username', 'created_at', 'created_by', 
                          'fee_balance', 'course_completion_date', 'is_eligible_for_certificate',
                          'days_remaining_to_complete')
    def get_days_remaining_to_complete(self, obj):
            return obj.get_days_remaining()
    
    def get_total_course_days(self, obj):
            return obj.get_total_course_days()
    def get_course_status(self, obj):
        return obj.get_course_status()

class CreateStudentRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for creating student registrations with all fields"""
    
    class Meta:
        model = StudentRegistration
        fields = (
            # Branch and Registration Details
            'branch', 'joining_date',
            
            # Student Personal Details
            'student_name', 'father_name', 'date_of_birth', 'qualification',
            
            # Student Type Fields
            'student_type', 'semester', 'college_name',
            'class_name', 'school_name', 'job_role', 'company_name',
            
            # Work/Study Information
            'work_college',
            
            # Contact Details
            'email', 'contact_address', 'phone_no', 'whatsapp_no', 'parents_no',
            
            # Course Details
            'course_type', 'course', 'class_mode', 'software_covered',
            'duration_months', 'duration_hours',
            
            # Financial Details
            'total_course_fee', 'paid_fee'
        )
    
    def validate(self, data):
        """
        Comprehensive validation including student_type specific fields
        """
        # Ensure paid_fee doesn't exceed total_course_fee
        if data.get('paid_fee', 0) > data.get('total_course_fee', 0):
            raise serializers.ValidationError({
                'paid_fee': 'Paid fee cannot exceed total course fee'
            })
        
        # Student type specific validation
        student_type = data.get('student_type')
        
        # Validate College Student
        if student_type == 'college':
            if not data.get('semester'):
                raise serializers.ValidationError({
                    'semester': 'Semester is required for college students.'
                })
            if not data.get('college_name'):
                raise serializers.ValidationError({
                    'college_name': 'College name is required for college students.'
                })
            # Clear other type fields
            data['class_name'] = None
            data['school_name'] = None
            data['job_role'] = None
            data['company_name'] = None
        
        # Validate School Student
        elif student_type == 'school':
            if not data.get('class_name'):
                raise serializers.ValidationError({
                    'class_name': 'Class is required for school students.'
                })
            if not data.get('school_name'):
                raise serializers.ValidationError({
                    'school_name': 'School name is required for school students.'
                })
            # Clear other type fields
            data['semester'] = None
            data['college_name'] = None
            data['job_role'] = None
            data['company_name'] = None
        
        # Validate Working Professional
        elif student_type == 'working':
            if not data.get('job_role'):
                raise serializers.ValidationError({
                    'job_role': 'Job role is required for working professionals.'
                })
            if not data.get('company_name'):
                raise serializers.ValidationError({
                    'company_name': 'Company name is required for working professionals.'
                })
            # Clear other type fields
            data['semester'] = None
            data['college_name'] = None
            data['class_name'] = None
            data['school_name'] = None
        
        # Validate work_college based on student type
        if student_type == 'college' and not data.get('work_college'):
            data['work_college'] = data.get('college_name', '')
        elif student_type == 'school' and not data.get('work_college'):
            data['work_college'] = data.get('school_name', '')
        elif student_type == 'working' and not data.get('work_college'):
            data['work_college'] = data.get('company_name', '')
        
        return data
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if StudentRegistration.objects.filter(email=value).exists():
            raise serializers.ValidationError("A student with this email already exists.")
        return value
    
    def validate_phone_no(self, value):
        """Validate phone number format"""
        if len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value
    
    def validate_class_mode(self, value):
        """Validate class mode"""
        valid_modes = ['online', 'offline', 'both']
        if value not in valid_modes:
            raise serializers.ValidationError(
                f"Class mode must be one of: {', '.join(valid_modes)}"
            )
        return value
    
    def validate_student_type(self, value):
        """Validate student type"""
        valid_types = ['college', 'school', 'working']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Student type must be one of: {', '.join(valid_types)}"
            )
        return value
    
    def create(self, validated_data):
        """Create student registration with all required fields"""
        # Get the staff member who is creating the registration (from request)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                staff_profile = StaffProfile.objects.get(user=request.user)
                validated_data['created_by'] = staff_profile
            except StaffProfile.DoesNotExist:
                raise serializers.ValidationError("Staff profile not found for the current user.")
        
        # Create registration - username, password, and registration number 
        # will be auto-generated in save() method of the model
        registration = StudentRegistration.objects.create(**validated_data)
        
        # Create initial payment if paid_fee > 0
        paid_fee = validated_data.get('paid_fee', 0)
        if paid_fee > 0 and 'created_by' in validated_data:
            PaymentTransaction.objects.create(
                student_registration=registration,
                installment_number=1,
                amount=paid_fee,
                payment_mode='cash',  # Default to cash, can be changed in API
                received_by=validated_data['created_by'],
                remark='Initial registration payment'
            )
        
        return registration
    
class CourseOptionsSerializer(serializers.Serializer):
    course_types = CourseTypeSerializer(many=True)
    duration_choices = serializers.ListField(
        child=serializers.DictField()
    )

class CreateStudentRegistrationResponseSerializer(serializers.ModelSerializer):
    """Serializer used ONLY for create response to show password once"""
    
    # Display fields
    course_type_name = serializers.CharField(source='course_type.name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    branch_display = serializers.CharField(source='get_branch_display', read_only=True)
    student_type_display = serializers.CharField(source='get_student_type_display', read_only=True)
    class_mode_display = serializers.CharField(source='get_class_mode_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True)
    
    # Student type specific info
    student_type_info = serializers.SerializerMethodField(read_only=True)
    
    # Course status fields
    is_eligible_for_certificate = serializers.BooleanField(read_only=True)
    days_remaining_to_complete = serializers.SerializerMethodField(read_only=True)
    total_course_days = serializers.SerializerMethodField(read_only=True)
    course_status = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = StudentRegistration
        fields = (
            # Registration details
            'id', 'registration_number', 
            'branch', 'branch_display', 
            'joining_date', 'created_at',
            
            # Student personal details
            'student_name', 'father_name', 
            'date_of_birth', 'qualification',
            
            # Student type fields
            'student_type', 'student_type_display',
            'semester', 'college_name',
            'class_name', 'school_name',
            'job_role', 'company_name',
            'work_college',
            'student_type_info',
            
            # Contact details
            'email', 'contact_address',
            'phone_no', 'whatsapp_no', 'parents_no',
            
            # Course details
            'course_type', 'course_type_name',
            'course', 'course_name',
            'class_mode', 'class_mode_display',
            'software_covered',
            'duration_months', 'duration_hours',
            
            # Financial details
            'total_course_fee', 'paid_fee', 'fee_balance',
            
            # Course status
            'course_completion_date',
            'days_remaining_to_complete',
            'total_course_days',
            'course_status',
            'is_eligible_for_certificate',
            
            # Certificate details
            'certificate_issued',
            'certificate_issue_date',
            'certificate_number',
            
            # Staff details
            'created_by', 'created_by_name',
            
            # Login credentials (shown only once)
            'username', 'password'
        )
    
    def get_student_type_info(self, obj):
        """Get student type specific information"""
        return obj.get_student_info()
    
    def get_days_remaining_to_complete(self, obj):
        """Get days remaining for course completion"""
        return obj.get_days_remaining()
    
    def get_total_course_days(self, obj):
        """Get total course duration in days"""
        return obj.get_total_course_days()
    
    def get_course_status(self, obj):
        """Get course status (not_started/ongoing/completed)"""
        return obj.get_course_status()
    
class UpdateFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentRegistration
        fields = ('paid_fee',)
    
    def validate_paid_fee(self, value):
        if value > self.instance.total_course_fee:
            raise serializers.ValidationError(
                f"Paid fee cannot exceed total course fee: {self.instance.total_course_fee}"
            )
        return value

# staff_app/serializers.py - Add these serializers

class PaymentTransactionSerializer(serializers.ModelSerializer):
    received_by_name = serializers.CharField(source='received_by.user.get_full_name', read_only=True)
    payment_mode_display = serializers.CharField(source='get_payment_mode_display', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = (
            'id', 'installment_number', 'amount', 'payment_date', 
            'payment_mode', 'payment_mode_display', 'transaction_id',
            'received_by', 'received_by_name', 'remark', 'created_at'
        )

class AddPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ('amount', 'payment_mode', 'transaction_id', 'remark')
    
    def create(self, validated_data):
        request = self.context.get('request')
        registration = self.context.get('registration')
        staff_profile = self.context.get('staff_profile')
        
        # Get next installment number
        last_payment = PaymentTransaction.objects.filter(
            student_registration=registration
        ).order_by('-installment_number').first()
        
        next_installment = (last_payment.installment_number + 1) if last_payment else 1
        
        # Create payment transaction
        payment = PaymentTransaction.objects.create(
            student_registration=registration,
            installment_number=next_installment,
            received_by=staff_profile,
            **validated_data
        )
        
        # Update student registration paid_fee
        registration.paid_fee += payment.amount
        registration.save()
        
        return payment