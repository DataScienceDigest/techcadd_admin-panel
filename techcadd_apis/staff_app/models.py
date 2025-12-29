from django.db import models
# staff_app/models.py - Add this import at the top
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
class StaffProfile(models.Model):
    STAFF_ROLES = [
        ('trainer', 'Trainer'),
        ('counselor', 'counselor'),
        ('manager', 'Manager')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    role = models.CharField(max_length=20, choices=STAFF_ROLES, default='support')
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'staff_profiles'
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

# # Signal to create staff profile (optional)
# @receiver(post_save, sender=User)
# def create_or_update_staff_profile(sender, instance, created, **kwargs):
#     if created:
#         StaffProfile.objects.get_or_create(user=instance)

# staff_app/models.py
from django.db import models
import secrets
import string

class Student_api(models.Model):
    CENTRE_CHOICES = [
        ('jalandhar1', 'Jalandhar 1'),
        ('jalandhar2', 'Jalandhar 2'),
        ('maqsudan', 'Maqsudan'),
        ('ludhiana', 'Ludhiana'),
        ('hoshiarpur', 'Hoshiarpur'),
        ('mohali', 'Mohali'),
        ('phagwara', 'Phagwara'),
    ]
    
    TRADE_CHOICES = [
        ('computer', 'Computer'),
        ('it', 'IT'),
        ('graphic_designing', 'Graphic Designing'),
        ('civil', 'Civil'),
        ('mechanical', 'Mechanical'),
        ('ielts', 'IELTS'),
        ('ece', 'ECE'),
        ('programming', 'Programming'),
        ('digital_marketing', 'Digital Marketing'),
        ('hardware', 'Hardware'),
        ('networking', 'Networking'),
    ]
    
    ENQUIRY_SOURCE_CHOICES = [
        ('social_media', 'Social Media'),
        ('just_dial', 'Just Dial'),
        ('random_call', 'Random Call'),
        ('direct_visit', 'Direct Visit'),
        ('banner', 'Banner'),
        ('website', 'Website'),
        ('reference', 'Reference'),
        ('newspaper', 'Newspaper'),
        ('friend_reference', 'Friend Reference'),
        ('google_search', 'Google Search'),
    ]
    
    ENQUIRY_STATUS = [
        ('registration_done', 'Registration Done'),
        ('visited', 'Visited'),
        ('in_process', 'In Process'),
        ('negative', 'Negative'),
        ('positive', 'Positive'),
        ('follow_up_required', 'Follow Up Required'),
        ('admission_done', 'Admission Done'),
        ('course_completed', 'Course Completed'),
        ('dropped', 'Dropped'),
    ]
    
    # Student Type Choices
    STUDENT_TYPE_CHOICES = [
        ('college', 'College Student'),
        ('school', 'School Student'),
        ('working', 'Working Professional'),
    ]
    
    # NEW: Class Mode Choices
    CLASS_MODE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('both', 'Both (Online & Offline)'),
    ]
    
    # Student Personal Details
    student_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    qualification = models.CharField(max_length=100)
    
    # Student Type (Required)
    student_type = models.CharField(
        max_length=20, 
        choices=STUDENT_TYPE_CHOICES,
        help_text="Type of student: college, school, or working"
    )
    
    # College Student Fields (conditional)
    semester = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'college'"
    )
    college_name = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'college'"
    )
    
    # School Student Fields (conditional)
    class_name = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'school'"
    )
    school_name = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'school'"
    )
    
    # Working Professional Fields (conditional)
    job_role = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'working'"
    )
    company_name = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'working'"
    )
    
    # Contact Details
    mobile = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    address = models.TextField()
    
    # Enquiry Details
    enquiry_date = models.DateField(auto_now_add=True)
    centre = models.CharField(max_length=20, choices=CENTRE_CHOICES)
    enquiry_taken_by = models.ForeignKey(
        'StaffProfile', 
        on_delete=models.CASCADE, 
        related_name='enquiries_taken'
    )
    batch_time = models.CharField(max_length=50, blank=True)
    
    # NEW: Class Mode Preference (Required)
    class_mode = models.CharField(
        max_length=10,
        choices=CLASS_MODE_CHOICES,
        help_text="Preferred mode of class: online, offline, or both"
    )
    
    course_fee_offer = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    course_interested = models.CharField(max_length=100, blank=True)
    trade = models.CharField(max_length=20, choices=TRADE_CHOICES)
    enquiry_source = models.CharField(max_length=20, choices=ENQUIRY_SOURCE_CHOICES)
    assign_enquiry = models.ForeignKey(
        'StaffProfile', 
        on_delete=models.CASCADE, 
        related_name='assigned_enquiries', 
        null=True, 
        blank=True
    )
    
    # Tracking Details
    enquiry_status = models.CharField(
        max_length=20, 
        choices=ENQUIRY_STATUS, 
        default='in_process'
    )
    converted_to_registration = models.BooleanField(default=False)
    registration_id = models.IntegerField(null=True, blank=True, help_text="ID of created registration")

    remark = models.TextField(blank=True) 
    next_follow_up_date = models.DateField(null=True, blank=True)
    
    # Login Credentials (auto-generated)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # Store hashed password
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
        ordering = ['-created_at']
        verbose_name = 'Student Enquiry'
        verbose_name_plural = 'Student Enquiries'
    
    def __str__(self):
        return f"{self.student_name} ({self.username}) - {self.get_student_type_display()} - {self.get_class_mode_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-generate username if not provided
        if not self.username:
            base_username = self.student_name.lower().replace(' ', '')
            username = base_username
            counter = 1
            while Student_api.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            self.username = username
        
        # Auto-generate password if not provided
        if not self.password:
            alphabet = string.ascii_letters + string.digits
            self.password = ''.join(secrets.choice(alphabet) for i in range(8))
        
        super().save(*args, **kwargs)
    
    def get_student_info(self):
        """Returns student-type specific information"""
        if self.student_type == 'college':
            return f"{self.semester} at {self.college_name}"
        elif self.student_type == 'school':
            return f"Class {self.class_name} at {self.school_name}"
        elif self.student_type == 'working':
            return f"{self.job_role} at {self.company_name}"
        return "N/A"
    
    def get_full_info(self):
        """Returns complete student information"""
        return {
            'name': self.student_name,
            'type': self.get_student_type_display(),
            'details': self.get_student_info(),
            'class_mode': self.get_class_mode_display(),
            'course': self.course_interested,
            'centre': self.get_centre_display()
        }


# staff_app/models.py - Add these models
# registrations sections start here 
class CourseType(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'course_types'
    
    def __str__(self):
        return self.name

class Course(models.Model):
    DURATION_CHOICES = [
        ('6_weeks', '6 Weeks'),
        ('1_month', '1 Month'),
        ('2_months', '2 Months'),
        ('3_months', '3 Months'),
        ('4_months', '4 Months'),
        ('5_months', '5 Months'),
        ('6_months', '6 Months'),
        ('7_months', '7 Months'),
        ('8_months', '8 Months'),
        ('9_months', '9 Months'),
        ('10_months', '10 Months'),
        ('1_year', '1 Year'),
    ]
    
    course_type = models.ForeignKey(CourseType, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=200)
    software_covered = models.TextField(blank=True)
    duration_months = models.CharField(max_length=20, choices=DURATION_CHOICES)
    duration_hours = models.IntegerField(help_text="Total course hours")
    course_fee = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'courses'
        ordering = ['course_type', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.course_type}"

# class StudentRegistration(models.Model):
#     CENTRE_CHOICES = [
#         ('jalandhar1', 'Jalandhar 1'),
#         ('jalandhar2', 'Jalandhar 2'),
#         ('maqsudan', 'Maqsudan'),
#         ('ludhiana', 'Ludhiana'),
#         ('hoshiarpur', 'Hoshiarpur'),
#         ('mohali', 'Mohali'),
#         ('phagwara', 'Phagwara'),
#     ]
#     BRANCH_CODES = {
#         'jalandhar1': '4001',
#         'jalandhar2': '4002', 
#         'maqsudan': '4003',
#         'ludhiana': '4004',
#         'hoshiarpur': '4005',
#         'mohali': '4006',
#         'phagwara': '4007',
#     }
    
#     # Add registration number field
#     registration_number = models.CharField(max_length=20, unique=True, blank=True)
#     # Branch and Basic Info
#     branch = models.CharField(max_length=20, choices=CENTRE_CHOICES)
#     joining_date = models.DateField()
#     student_name = models.CharField(max_length=100)
#     father_name = models.CharField(max_length=100)
#     date_of_birth = models.DateField()
#     email = models.EmailField(unique=True)
#     qualification = models.CharField(max_length=100)
#     work_college = models.CharField(max_length=100)
#     contact_address = models.TextField()
#     phone_no = models.CharField(max_length=15)
#     whatsapp_no = models.CharField(max_length=15, blank=True)
#     parents_no = models.CharField(max_length=15, blank=True)
#     course_type = models.ForeignKey(CourseType, on_delete=models.CASCADE, related_name='registrations')
#     course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='registrations')
#     software_covered = models.TextField(blank=True)  # Can override course software
#     duration_months = models.CharField(max_length=20, choices=Course.DURATION_CHOICES)
#     duration_hours = models.IntegerField()
#     username = models.CharField(max_length=50, unique=True)
#     password = models.CharField(max_length=128)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     created_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='student_registrations')
#     total_course_fee = models.DecimalField(max_digits=10, decimal_places=2)
#     paid_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     fee_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     course_completion_date = models.DateField(null=True, blank=True)
#     certificate_issued = models.BooleanField(default=False)
#     certificate_issue_date = models.DateField(null=True, blank=True)
#     certificate_number = models.CharField(max_length=50, blank=True)
#     class Meta:
#         db_table = 'student_registrations'
#         ordering = ['-created_at']
    
#     def __str__(self):
#         return f"{self.student_name} - {self.course.name}"
    
#     def save(self, *args, **kwargs):
#         if not self.registration_number:
#             self.registration_number = self.generate_registration_number()
#         self.fee_balance = self.total_course_fee - self.paid_fee
        
#         # Calculate course completion date based on duration
#         if self.joining_date and self.duration_months:
#             self.course_completion_date = self.calculate_completion_date()
        
#         # Auto-generate username if not provided
#         if not self.username:
#             base_username = self.student_name.lower().replace(' ', '')
#             username = base_username
#             counter = 1
#             while StudentRegistration.objects.filter(username=username).exists():
#                 username = f"{base_username}{counter}"
#                 counter += 1
#             self.username = username
        
#         # Auto-generate password if not provided
#         if not self.password:
#             import secrets
#             import string
#             alphabet = string.ascii_letters + string.digits
#             self.password = ''.join(secrets.choice(alphabet) for i in range(8))
        
#         super().save(*args, **kwargs)
#     def generate_registration_number(self):
#         branch_code = self.BRANCH_CODES.get(self.branch, '4000')
#         last_reg = StudentRegistration.objects.filter(
#             registration_number__startswith=f"TCD/{branch_code}/"
#         ).order_by('-id').first()
        
#         if last_reg and last_reg.registration_number:
#             try:
#                 last_number = int(last_reg.registration_number.split('/')[-1])
#                 sequential_number = last_number + 1
#             except (ValueError, IndexError):
#                 sequential_number = 1
#         else:
#             sequential_number = 1
        
#         sequential_str = str(sequential_number).zfill(4)
#         return f"TCD/{branch_code}/{sequential_str}"
    
#     def __str__(self):
#         return f"{self.registration_number} - {self.student_name}"

#     def calculate_completion_date(self):
#         from dateutil.relativedelta import relativedelta
        
#         duration_map = {
#             '6_weeks': relativedelta(weeks=6),
#             '1_month': relativedelta(months=1),
#             '2_months': relativedelta(months=2),
#             '3_months': relativedelta(months=3),
#             '4_months': relativedelta(months=4),
#             '5_months': relativedelta(months=5),
#             '6_months': relativedelta(months=6),
#             '7_months': relativedelta(months=7),
#             '8_months': relativedelta(months=8),
#             '9_months': relativedelta(months=9),
#             '10_months': relativedelta(months=10),
#             '1_year': relativedelta(years=1),
#         }
        
#         duration_delta = duration_map.get(self.duration_months, relativedelta(months=3))
#         return self.joining_date + duration_delta
    
#     def is_eligible_for_certificate(self):
#         """Check if student is eligible for certificate"""
#         from django.utils import timezone
#         today = timezone.now().date()
        
#         # Check if fees are fully paid
#         fees_cleared = self.paid_fee >= self.total_course_fee
        
#         # Check if course duration is completed
#         course_completed = self.course_completion_date and today >= self.course_completion_date
        
#         return fees_cleared and course_completed
    
#     def generate_certificate_number(self):
#         """Generate unique certificate number"""
#         if not self.certificate_number:
#             base_number = f"CERT-{self.registration_number.replace('/', '')}"
#             self.certificate_number = base_number
#         return self.certificate_number
#     def get_days_remaining(self):
#         if not self.course_completion_date:
#             return None
#         today = datetime.datetime.now().date()
#         if today < self.joining_date:
#             total_duration = (self.course_completion_date - self.joining_date).days
#             return total_duration
        
#         # If course is in progress
#         if today <= self.course_completion_date:
#             days_remaining = (self.course_completion_date - today).days
#             return days_remaining
#         return 0

#     def get_course_status(self):
#         """Get course status"""
#         from django.utils import timezone
#         today = datetime.datetime.now().date()
#         if today < self.joining_date:
#             return "not_started"
#         elif today <= self.course_completion_date:
#             return "ongoing"
#         else:
#             return "completed"
#     # In your StudentRegistration model
#     def get_total_course_days(self):
#         """Get total duration of course in days"""
#         if self.joining_date and self.course_completion_date:
#             total_days = (self.course_completion_date - self.joining_date).days
#             return total_days
#         return None

class StudentRegistration(models.Model):
    CENTRE_CHOICES = [
        ('jalandhar1', 'Jalandhar 1'),
        ('jalandhar2', 'Jalandhar 2'),
        ('maqsudan', 'Maqsudan'),
        ('ludhiana', 'Ludhiana'),
        ('hoshiarpur', 'Hoshiarpur'),
        ('mohali', 'Mohali'),
        ('phagwara', 'Phagwara'),
    ]
    
    BRANCH_CODES = {
        'jalandhar1': '4001',
        'jalandhar2': '4002', 
        'maqsudan': '4003',
        'ludhiana': '4004',
        'hoshiarpur': '4005',
        'mohali': '4006',
        'phagwara': '4007',
    }
    
    # Student Type Choices
    STUDENT_TYPE_CHOICES = [
        ('college', 'College Student'),
        ('school', 'School Student'),
        ('working', 'Working Professional'),
    ]
    
    # Class Mode Choices
    CLASS_MODE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('both', 'Both (Online & Offline)'),
    ]
    
    # Registration Details
    registration_number = models.CharField(max_length=20, unique=True, blank=True)
    branch = models.CharField(max_length=20, choices=CENTRE_CHOICES)
    joining_date = models.DateField()
    
    # Student Personal Details
    student_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    qualification = models.CharField(max_length=100)
    
    # Student Type (Required)
    student_type = models.CharField(
        max_length=20, 
        choices=STUDENT_TYPE_CHOICES,
        help_text="Type of student: college, school, or working"
    )
    
    # College Student Fields (conditional)
    semester = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'college'"
    )
    college_name = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'college'"
    )
    
    # School Student Fields (conditional)
    class_name = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'school'"
    )
    school_name = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'school'"
    )
    
    # Working Professional Fields (conditional)
    job_role = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'working'"
    )
    company_name = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Required if student_type is 'working'"
    )
    
    # Work/Study Information
    work_college = models.CharField(
        max_length=200, 
        help_text="Current workplace or college name"
    )
    
    # Contact Details
    email = models.EmailField(unique=True)
    contact_address = models.TextField()
    phone_no = models.CharField(max_length=15)
    whatsapp_no = models.CharField(max_length=15, blank=True)
    parents_no = models.CharField(max_length=15, blank=True)
    
    # Course Details
    course_type = models.ForeignKey(CourseType, on_delete=models.CASCADE, related_name='registrations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='registrations')
    
    # NEW: Class Mode Preference (Required)
    class_mode = models.CharField(
        max_length=10,
        choices=CLASS_MODE_CHOICES,
        help_text="Preferred mode of class: online, offline, or both"
    )
    
    software_covered = models.TextField(blank=True)  # Can override course software
    duration_months = models.CharField(max_length=20, choices=Course.DURATION_CHOICES)
    duration_hours = models.IntegerField()
    
    # Financial Details
    total_course_fee = models.DecimalField(max_digits=10, decimal_places=2)
    paid_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Course Completion Details
    course_completion_date = models.DateField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)
    certificate_issue_date = models.DateField(null=True, blank=True)
    certificate_number = models.CharField(max_length=50, blank=True)
    
    # Login Credentials
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    
    # Staff Information
    created_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='student_registrations')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_registrations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.registration_number} - {self.student_name} - {self.get_student_type_display()}"
    
    def save(self, *args, **kwargs):
        # Generate registration number if not provided
        if not self.registration_number:
            self.registration_number = self.generate_registration_number()
        
        # Calculate fee balance
        self.fee_balance = self.total_course_fee - self.paid_fee
        
        # Calculate course completion date based on duration
        if self.joining_date and self.duration_months:
            self.course_completion_date = self.calculate_completion_date()
        
        # Auto-generate username if not provided
        if not self.username:
            base_username = self.student_name.lower().replace(' ', '')
            username = base_username
            counter = 1
            while StudentRegistration.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            self.username = username
        
        # Auto-generate password if not provided
        if not self.password:
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits
            self.password = ''.join(secrets.choice(alphabet) for i in range(8))
        
        super().save(*args, **kwargs)
    
    def generate_registration_number(self):
        branch_code = self.BRANCH_CODES.get(self.branch, '4000')
        last_reg = StudentRegistration.objects.filter(
            registration_number__startswith=f"TCD/{branch_code}/"
        ).order_by('-id').first()
        
        if last_reg and last_reg.registration_number:
            try:
                last_number = int(last_reg.registration_number.split('/')[-1])
                sequential_number = last_number + 1
            except (ValueError, IndexError):
                sequential_number = 1
        else:
            sequential_number = 1
        
        sequential_str = str(sequential_number).zfill(4)
        return f"TCD/{branch_code}/{sequential_str}"
    
    def calculate_completion_date(self):
        from dateutil.relativedelta import relativedelta
        
        duration_map = {
            '6_weeks': relativedelta(weeks=6),
            '1_month': relativedelta(months=1),
            '2_months': relativedelta(months=2),
            '3_months': relativedelta(months=3),
            '4_months': relativedelta(months=4),
            '5_months': relativedelta(months=5),
            '6_months': relativedelta(months=6),
            '7_months': relativedelta(months=7),
            '8_months': relativedelta(months=8),
            '9_months': relativedelta(months=9),
            '10_months': relativedelta(months=10),
            '1_year': relativedelta(years=1),
        }
        
        duration_delta = duration_map.get(self.duration_months, relativedelta(months=3))
        return self.joining_date + duration_delta
    
    def is_eligible_for_certificate(self):
        """Check if student is eligible for certificate"""
        from django.utils import timezone
        today = timezone.now().date()
        
        # Check if fees are fully paid
        fees_cleared = self.paid_fee >= self.total_course_fee
        
        # Check if course duration is completed
        course_completed = self.course_completion_date and today >= self.course_completion_date
        
        return fees_cleared and course_completed
    
    def generate_certificate_number(self):
        """Generate unique certificate number"""
        if not self.certificate_number:
            base_number = f"CERT-{self.registration_number.replace('/', '')}"
            self.certificate_number = base_number
        return self.certificate_number
    
    def get_days_remaining(self):
        import datetime
        if not self.course_completion_date:
            return None
        today = datetime.datetime.now().date()
        if today < self.joining_date:
            total_duration = (self.course_completion_date - self.joining_date).days
            return total_duration
        
        # If course is in progress
        if today <= self.course_completion_date:
            days_remaining = (self.course_completion_date - today).days
            return days_remaining
        return 0

    def get_course_status(self):
        """Get course status"""
        import datetime
        today = datetime.datetime.now().date()
        if today < self.joining_date:
            return "not_started"
        elif today <= self.course_completion_date:
            return "ongoing"
        else:
            return "completed"
    
    def get_total_course_days(self):
        """Get total duration of course in days"""
        if self.joining_date and self.course_completion_date:
            total_days = (self.course_completion_date - self.joining_date).days
            return total_days
        return None
    
    def get_student_info(self):
        """Returns student-type specific information"""
        if self.student_type == 'college':
            return f"{self.semester} at {self.college_name}"
        elif self.student_type == 'school':
            return f"Class {self.class_name} at {self.school_name}"
        elif self.student_type == 'working':
            return f"{self.job_role} at {self.company_name}"
        return "N/A"
    
    def get_full_info(self):
        """Returns complete student information"""
        return {
            'registration_number': self.registration_number,
            'name': self.student_name,
            'father_name': self.father_name,
            'type': self.get_student_type_display(),
            'details': self.get_student_info(),
            'class_mode': self.get_class_mode_display(),
            'course': self.course.name if self.course else None,
            'branch': self.get_branch_display(),
            'joining_date': self.joining_date,
            'completion_date': self.course_completion_date,
            'fees_paid': float(self.paid_fee),
            'fees_balance': float(self.fee_balance),
            'total_fees': float(self.total_course_fee)
        }
# staff_app/models.py - Add this model

class PaymentTransaction(models.Model):
    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('online', 'Online'),
        ('cheque', 'Cheque'),
        ('card', 'Card'),
        ('upi', 'UPI'),
    ]
    
    student_registration = models.ForeignKey(StudentRegistration, on_delete=models.CASCADE, related_name='payment_transactions')
    installment_number = models.IntegerField(help_text="Installment number (1st, 2nd, 3rd, etc.)")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES, default='cash')
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Transaction ID for online payments")
    received_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='received_payments')
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_transactions'
        ordering = ['installment_number']
    
    def __str__(self):
        return f"Installment #{self.installment_number} - {self.amount} for {self.student_registration.registration_number}"
    

# ============================== BRANCH SECTION START HERE =============================

class BranchProfile(models.Model):
    CENTRE_CHOICES = [
        ('jalandhar1', 'Jalandhar 1'),
        ('jalandhar2', 'Jalandhar 2'),
        ('maqsudan', 'Maqsudan'),
        ('ludhiana', 'Ludhiana'),
        ('hoshiarpur', 'Hoshiarpur'),
        ('mohali', 'Mohali'),
        ('phagwara', 'Phagwara'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='branch_profile')
    branch = models.CharField(max_length=20, choices=CENTRE_CHOICES, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'branch_profiles'
        verbose_name = 'Branch Profile'
        verbose_name_plural = 'Branch Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_branch_display()} - {self.user.username}"