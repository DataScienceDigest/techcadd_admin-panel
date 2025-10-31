# student_lms/serializers.py
from rest_framework import serializers
from staff_app.models import StudentRegistration

class StudentLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            try:
                # Simple check - we'll improve security later
                student = StudentRegistration.objects.get(
                    username=username, 
                    password=password  # Use as-is for now
                )
                data['student'] = student
            except StudentRegistration.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'")

        return data
    

# student_lms/serializers.py - Add this
from rest_framework import serializers
from staff_app.models import StudentRegistration

class StudentDashboardSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_type_name = serializers.CharField(source='course_type.name', read_only=True)
    branch_display = serializers.CharField(source='get_branch_display', read_only=True)
    days_remaining_to_complete = serializers.SerializerMethodField()
    course_status = serializers.SerializerMethodField()
    payment_percentage = serializers.SerializerMethodField()

    class Meta:
        model = StudentRegistration
        fields = (
            'registration_number',
            'student_name', 
            'joining_date',
            'course_name',
            'course_type_name',
            'branch_display',
            'course_completion_date',
            'days_remaining_to_complete',
            'course_status',
            'total_course_fee',
            'paid_fee', 
            'fee_balance',
            'payment_percentage'
        )

    def get_days_remaining_to_complete(self, obj):
        """Calculate days remaining to complete course"""
        from datetime import date
        today = date.today()
        
        if not obj.course_completion_date:
            return None
            
        if today < obj.joining_date:
            return (obj.course_completion_date - obj.joining_date).days
        elif today <= obj.course_completion_date:
            return (obj.course_completion_date - today).days
        else:
            return 0

    def get_course_status(self, obj):
        """Get course status"""
        from datetime import date
        today = date.today()
        
        if today < obj.joining_date:
            return "not_started"
        elif today <= obj.course_completion_date:
            return "ongoing"
        else:
            return "completed"

    def get_payment_percentage(self, obj):
        """Calculate payment percentage"""
        if obj.total_course_fee > 0:
            return round((obj.paid_fee / obj.total_course_fee) * 100, 2)
        return 0
    
# student_lms/course_serializers.py
from rest_framework import serializers
from .models import CourseModule, Lesson, StudentProgress, StudentNote
from staff_app.models import Course

class LessonListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing lessons with basic info
    """
    is_completed = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = (
            'id',
            'title',
            'lesson_type',
            'order',
            'duration_minutes',
            'is_free_preview',
            'is_completed',
            'progress_percentage',
        )
    
    def get_is_completed(self, obj):
        """Check if student has completed this lesson"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                progress = StudentProgress.objects.get(
                    student=request.user,
                    lesson=obj
                )
                return progress.status == 'completed'
            except StudentProgress.DoesNotExist:
                return False
        return False
    
    def get_progress_percentage(self, obj):
        """Get student's progress percentage for this lesson"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                progress = StudentProgress.objects.get(
                    student=request.user,
                    lesson=obj
                )
                return float(progress.completion_percentage)
            except StudentProgress.DoesNotExist:
                return 0.0
        return 0.0


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual lesson view
    """
    module_title = serializers.CharField(source='module.title', read_only=True)
    progress = serializers.SerializerMethodField()
    my_notes = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = (
            'id',
            'title',
            'description',
            'lesson_type',
            'module_title',
            'video_url',
            'document_file',
            'text_content',
            'duration_minutes',
            'order',
            'progress',
            'my_notes',
        )
    
    def get_progress(self, obj):
        """Get student's progress for this lesson"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                progress = StudentProgress.objects.get(
                    student=request.user,
                    lesson=obj
                )
                return {
                    'status': progress.status,
                    'completion_percentage': float(progress.completion_percentage),
                    'time_spent_minutes': progress.time_spent_minutes,
                    'last_accessed': progress.last_accessed,
                }
            except StudentProgress.DoesNotExist:
                return {
                    'status': 'not_started',
                    'completion_percentage': 0.0,
                    'time_spent_minutes': 0,
                    'last_accessed': None,
                }
        return None
    
    def get_my_notes(self, obj):
        """Get student's notes for this lesson"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            notes = StudentNote.objects.filter(
                student=request.user,
                lesson=obj
            ).order_by('timestamp_seconds')
            return StudentNoteSerializer(notes, many=True).data
        return []


class CourseModuleSerializer(serializers.ModelSerializer):
    """
    Serializer for course modules with lessons
    """
    lessons = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()
    completed_lessons = serializers.SerializerMethodField()
    total_duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseModule
        fields = (
            'id',
            'title',
            'description',
            'order',
            'total_lessons',
            'completed_lessons',
            'total_duration_minutes',
            'lessons',
        )
    
    def get_lessons(self, obj):
        """Get all lessons in this module"""
        lessons = obj.lessons.filter(is_active=True)
        return LessonListSerializer(
            lessons, 
            many=True, 
            context=self.context
        ).data
    
    def get_total_lessons(self, obj):
        """Count total lessons in module"""
        return obj.lessons.filter(is_active=True).count()
    
    def get_completed_lessons(self, obj):
        """Count completed lessons by student"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return StudentProgress.objects.filter(
                student=request.user,
                lesson__module=obj,
                status='completed'
            ).count()
        return 0
    
    def get_total_duration_minutes(self, obj):
        """Calculate total duration of all lessons"""
        return sum(
            lesson.duration_minutes 
            for lesson in obj.lessons.filter(is_active=True)
        )


class CourseDetailSerializer(serializers.ModelSerializer):
    modules = serializers.SerializerMethodField()
    course_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = (
            'id',
            'name',
            'course_progress',
            'modules',
        )
    
    def get_modules(self, obj):
        """Get all modules in this course"""
        modules = CourseModule.objects.filter(
            course=obj,
            is_active=True
        ).order_by('order')
        return CourseModuleSerializer(
            modules,
            many=True,
            context=self.context
        ).data
    
    def get_course_progress(self, obj):
        """Calculate overall course progress"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Get all lessons in this course
            total_lessons = Lesson.objects.filter(
                module__course=obj,
                module__is_active=True,
                is_active=True
            ).count()
            
            if total_lessons == 0:
                return {
                    'total_lessons': 0,
                    'completed_lessons': 0,
                    'progress_percentage': 0.0
                }
            
            # Count completed lessons
            completed_lessons = StudentProgress.objects.filter(
                student=request.user,
                lesson__module__course=obj,
                status='completed'
            ).count()
            
            progress_percentage = (completed_lessons / total_lessons) * 100
            
            return {
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'progress_percentage': round(progress_percentage, 2)
            }
        return None


class StudentProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for updating student progress
    """
    class Meta:
        model = StudentProgress
        fields = (
            'lesson',
            'status',
            'completion_percentage',
            'time_spent_minutes',
        )
        read_only_fields = ('lesson',)


class StudentNoteSerializer(serializers.ModelSerializer):
    """
    Serializer for student notes
    """
    class Meta:
        model = StudentNote
        fields = (
            'id',
            'lesson',
            'note_text',
            'timestamp_seconds',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')