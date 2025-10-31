from django.db import models

# Create your models here.
# student_lms/models.py
from django.db import models
from staff_app.models import Course, StudentRegistration

class CourseModule(models.Model):
    """
    Modules/Chapters in a course
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)  # To maintain sequence
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Course Module'
        verbose_name_plural = 'Course Modules'
    
    def __str__(self):
        return f"{self.course.name} - {self.title}"


class Lesson(models.Model):
    """
    Individual lessons within a module
    """
    LESSON_TYPES = (
        ('video', 'Video'),
        ('document', 'Document'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('live_class', 'Live Class'),
        ('text', 'Text Content'),
    )
    
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='video')
    order = models.PositiveIntegerField(default=0)
    
    # Content fields
    video_url = models.URLField(blank=True, null=True, help_text="YouTube, Vimeo, or direct video URL")
    document_file = models.FileField(upload_to='lessons/documents/', blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)
    
    # Duration and settings
    duration_minutes = models.PositiveIntegerField(default=0, help_text="Lesson duration in minutes")
    is_free_preview = models.BooleanField(default=False, help_text="Allow preview without enrollment")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"


class StudentProgress(models.Model):
    """
    Track student's progress through lessons
    """
    STATUS_CHOICES = (
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    
    student = models.ForeignKey(StudentRegistration, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    # Progress tracking
    time_spent_minutes = models.PositiveIntegerField(default=0)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    last_accessed = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'lesson')
        verbose_name = 'Student Progress'
        verbose_name_plural = 'Student Progress'
    
    def __str__(self):
        return f"{self.student.student_name} - {self.lesson.title} ({self.status})"


class StudentNote(models.Model):
    """
    Notes that students can take during lessons
    """
    student = models.ForeignKey(StudentRegistration, on_delete=models.CASCADE, related_name='notes')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_notes')
    note_text = models.TextField()
    timestamp_seconds = models.PositiveIntegerField(default=0, help_text="Time in lesson when note was taken")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Note'
        verbose_name_plural = 'Student Notes'
    
    def __str__(self):
        return f"{self.student.student_name} - {self.lesson.title}"