from django.db import models

# Create your models here.
# staff_app/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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

# staff_app/models.py - Add this to your existing models
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
    # Student Personal Details
    student_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    qualification = models.CharField(max_length=100)
    work_college = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    address = models.TextField()
    
    # Enquiry Details
    enquiry_date = models.DateField(auto_now_add=True)
    # centre = models.CharField(max_length=100)
    centre = models.CharField(max_length=20, choices=CENTRE_CHOICES)
    enquiry_taken_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='enquiries_taken')
    batch_time = models.CharField(max_length=50, blank=True)
    course_fee_offer = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    course_interested = models.CharField(max_length=100, blank=True)
    # trade = models.CharField(max_length=20, choices=TRADES)
    trade = models.CharField(max_length=20, choices=TRADE_CHOICES)
    # enquiry_source = models.CharField(max_length=20, choices=ENQUIRY_SOURCES)
    enquiry_source = models.CharField(max_length=20, choices=ENQUIRY_SOURCE_CHOICES)
    assign_enquiry = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='assigned_enquiries', null=True, blank=True)
    
    # Tracking Details
    enquiry_status = models.CharField(max_length=20, choices=ENQUIRY_STATUS, default='new')
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
    
    def __str__(self):
        return f"{self.student_name} ({self.username})"
    
    def save(self, *args, **kwargs):
        # Auto-generate username if not provided
        if not self.username:
            base_username = self.student_name.lower().replace(' ', '')
            username = base_username
            counter = 1
            # FIX: Use Student_api instead of Student
            while Student_api.objects.filter(username=username).exists():
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
    
    # Add registration number field
    registration_number = models.CharField(max_length=20, unique=True, blank=True)
    # Branch and Basic Info
    branch = models.CharField(max_length=20, choices=CENTRE_CHOICES)
    joining_date = models.DateField()
    
    # Student Personal Details
    student_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    email = models.EmailField(unique=True)
    qualification = models.CharField(max_length=100)
    work_college = models.CharField(max_length=100)
    contact_address = models.TextField()
    phone_no = models.CharField(max_length=15)
    whatsapp_no = models.CharField(max_length=15, blank=True)
    parents_no = models.CharField(max_length=15, blank=True)
    
    # Course Details
    course_type = models.ForeignKey(CourseType, on_delete=models.CASCADE, related_name='registrations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='registrations')
    software_covered = models.TextField(blank=True)  # Can override course software
    duration_months = models.CharField(max_length=20, choices=Course.DURATION_CHOICES)
    duration_hours = models.IntegerField()
    course_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Login Credentials (auto-generated)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='student_registrations')
    
    class Meta:
        db_table = 'student_registrations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student_name} - {self.course.name}"
    
    def save(self, *args, **kwargs):
         # Auto-generate registration number if not provided
        if not self.registration_number:
            self.registration_number = self.generate_registration_number()
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
        """Generate unique registration number in format: TCD/BRANCH_CODE/SEQUENTIAL_NUMBER"""
        branch_code = self.BRANCH_CODES.get(self.branch, '4000')
        
        # Get the last registration number for this branch
        last_reg = StudentRegistration.objects.filter(
            registration_number__startswith=f"TCD/{branch_code}/"
        ).order_by('-id').first()
        
        if last_reg and last_reg.registration_number:
            # Extract sequential number and increment
            try:
                last_number = int(last_reg.registration_number.split('/')[-1])
                sequential_number = last_number + 1
            except (ValueError, IndexError):
                sequential_number = 1
        else:
            sequential_number = 1
        
        # Format with leading zeros (4 digits)
        sequential_str = str(sequential_number).zfill(4)
        return f"TCD/{branch_code}/{sequential_str}"
    
    def __str__(self):
        return f"{self.registration_number} - {self.student_name}"