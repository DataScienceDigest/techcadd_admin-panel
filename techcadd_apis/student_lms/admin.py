from django.contrib import admin

# Register your models here.
# student_lms/admin.py
from django.contrib import admin
from .models import CourseModule, Lesson, StudentProgress, StudentNote

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'lesson_type', 'order', 'duration_minutes', 'is_active')

@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_active', 'created_at')
    list_filter = ('course', 'is_active', 'created_at')
    search_fields = ('title', 'course__name')
    inlines = [LessonInline]
    ordering = ('course', 'order')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'lesson_type', 'order', 'duration_minutes', 'is_active')
    list_filter = ('lesson_type', 'is_active', 'is_free_preview', 'module__course')
    search_fields = ('title', 'module__title')
    ordering = ('module', 'order')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('module', 'title', 'description', 'lesson_type', 'order')
        }),
        ('Content', {
            'fields': ('video_url', 'document_file', 'text_content')
        }),
        ('Settings', {
            'fields': ('duration_minutes', 'is_free_preview', 'is_active')
        }),
    )

@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'status', 'completion_percentage', 'last_accessed')
    list_filter = ('status', 'completed_at')
    search_fields = ('student__student_name', 'lesson__title')
    readonly_fields = ('created_at', 'updated_at', 'last_accessed')
    
    fieldsets = (
        ('Student & Lesson', {
            'fields': ('student', 'lesson')
        }),
        ('Progress', {
            'fields': ('status', 'completion_percentage', 'time_spent_minutes')
        }),
        ('Timestamps', {
            'fields': ('last_accessed', 'completed_at', 'created_at', 'updated_at')
        }),
    )

@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'timestamp_seconds', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('student__student_name', 'lesson__title', 'note_text')
    readonly_fields = ('created_at', 'updated_at')