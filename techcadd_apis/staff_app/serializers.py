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

class StudentSerializer(serializers.ModelSerializer):
    enquiry_taken_by_name = serializers.CharField(source='enquiry_taken_by.user.get_full_name', read_only=True)
    assign_enquiry_name = serializers.CharField(source='assign_enquiry.user.get_full_name', read_only=True)
    enquiry_status_display = serializers.CharField(source='get_enquiry_status_display', read_only=True)
    trade_display = serializers.CharField(source='get_trade_display', read_only=True)
    centre_display = serializers.CharField(source='get_centre_display', read_only=True)
    enquiry_source_display = serializers.CharField(source='get_enquiry_source_display', read_only=True)
    
    class Meta:
        model = Student_api
        fields = (
            'id', 'student_name', 'date_of_birth', 'qualification', 'work_college',
            'mobile', 'email', 'address', 'enquiry_date', 'centre', 'centre_display',
            'enquiry_taken_by', 'enquiry_taken_by_name', 'batch_time', 
            'course_fee_offer', 'course_interested', 'trade', 'trade_display', 
            'enquiry_source', 'enquiry_source_display', 'assign_enquiry', 
            'assign_enquiry_name', 'enquiry_status', 'enquiry_status_display', 
            'remark', 'next_follow_up_date', 'username', 'password', 'created_at'
        )
        read_only_fields = ('username', 'password', 'created_at', 'updated_at', 'enquiry_taken_by')

class CreateStudentSerializer(serializers.ModelSerializer):
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
        # Add your mobile validation logic here
        if len(value) < 10:
            raise serializers.ValidationError("Mobile number must be at least 10 digits")
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if Student_api.objects.filter(email=value).exists():
            raise serializers.ValidationError("A student with this email already exists.")
        return value
    
    def create(self, validated_data):
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

class StudentListSerializer(serializers.ModelSerializer):
    enquiry_taken_by_name = serializers.CharField(source='enquiry_taken_by.user.get_full_name', read_only=True)
    enquiry_status_display = serializers.CharField(source='get_enquiry_status_display', read_only=True)
    trade_display = serializers.CharField(source='get_trade_display', read_only=True)
    centre_display = serializers.CharField(source='get_centre_display', read_only=True)
    
    class Meta:
        model = Student_api
        fields = (
            'id', 'student_name', 'mobile', 'email', 'enquiry_date',
            'enquiry_status', 'enquiry_status_display', 'enquiry_taken_by_name',
            'next_follow_up_date', 'centre', 'centre_display', 'trade', 'trade_display'
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
    class Meta:
        model = StudentRegistration
        fields = (
            'branch', 'joining_date', 'student_name', 'father_name', 'date_of_birth',
            'email', 'qualification', 'work_college', 'contact_address', 'phone_no',
            'whatsapp_no', 'parents_no', 'course_type', 'course', 'software_covered',
            'duration_months', 'duration_hours', 'total_course_fee', 'paid_fee'  # Added fee fields
        )
    
    def validate(self, data):
        # Ensure paid_fee doesn't exceed total_course_fee
        if data.get('paid_fee', 0) > data.get('total_course_fee', 0):
            raise serializers.ValidationError({
                'paid_fee': 'Paid fee cannot exceed total course fee'
            })
        return data
    
    def validate_email(self, value):
        if StudentRegistration.objects.filter(email=value).exists():
            raise serializers.ValidationError("A student with this email already exists.")
        return value
    
    def validate_phone_no(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value
    
    def create(self, validated_data):
        # Set the created_by staff
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            staff_profile = StaffProfile.objects.get(user=request.user)
            validated_data['created_by'] = staff_profile
        
        # Create registration
        registration = StudentRegistration.objects.create(**validated_data)
        return registration

class CourseOptionsSerializer(serializers.Serializer):
    course_types = CourseTypeSerializer(many=True)
    duration_choices = serializers.ListField(
        child=serializers.DictField()
    )

class CreateStudentRegistrationResponseSerializer(serializers.ModelSerializer):
    """Serializer used ONLY for create response to show password once"""
    course_type_name = serializers.CharField(source='course_type.name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    branch_display = serializers.CharField(source='get_branch_display', read_only=True)
    is_eligible_for_certificate = serializers.BooleanField(read_only=True)
    days_remaining_to_complete = serializers.SerializerMethodField(read_only=True)
    total_course_days = serializers.SerializerMethodField(read_only=True)  # ADD THIS
    course_status = serializers.SerializerMethodField(read_only=True)  # ADD THIS
    
    
    class Meta:
        model = StudentRegistration
        fields = (
            'id', 'registration_number', 'branch', 'branch_display', 'joining_date', 
            'student_name', 'email', 'phone_no', 'course_type_name', 'course_name',
            'total_course_fee', 'paid_fee', 'fee_balance',  # Fee info
            'course_completion_date',  # Completion date
            'days_remaining_to_complete',  # NEW: Days remaining
            'is_eligible_for_certificate',  # Eligibility
            'total_course_days',  # ADD THIS
            'course_status',  # ADD THIS
            'username', 'password', 'created_at'
        )
    def get_days_remaining_to_complete(self, obj):
            return obj.get_days_remaining()
    def get_total_course_days(self, obj):
        return obj.get_total_course_days()
    def get_course_status(self, obj):
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