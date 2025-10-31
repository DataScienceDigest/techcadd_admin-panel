# Create this file: student_lms/management/commands/create_sample_course.py

from django.core.management.base import BaseCommand
from staff_app.models import Course
from student_lms.models import CourseModule, Lesson


class Command(BaseCommand):
    help = 'Create sample course content for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course-id',
            type=int,
            default=8,
            help='Course ID to create content for'
        )

    def handle(self, *args, **options):
        course_id = options['course_id']
        
        try:
            course = Course.objects.get(id=course_id)
            self.stdout.write(f"Creating content for: {course.name}")
            
            # Clear existing data (optional)
            CourseModule.objects.filter(course=course).delete()
            
            # Create Module 1
            module1 = CourseModule.objects.create(
                course=course,
                title="HTML Fundamentals",
                description="Learn the basics of HTML and structure web pages",
                order=1,
                is_active=True
            )
            
            Lesson.objects.create(
                module=module1,
                title="Introduction to HTML",
                description="What is HTML and why we use it",
                lesson_type="video",
                order=1,
                video_url="https://www.youtube.com/watch?v=example1",
                duration_minutes=30,
                is_active=True
            )
            
            Lesson.objects.create(
                module=module1,
                title="HTML Tags and Elements",
                description="Understanding HTML tags, elements and attributes",
                lesson_type="video",
                order=2,
                video_url="https://www.youtube.com/watch?v=example2",
                duration_minutes=45,
                is_active=True
            )
            
            Lesson.objects.create(
                module=module1,
                title="HTML Document Structure",
                description="Learn about HTML document structure",
                lesson_type="text",
                order=3,
                text_content="HTML documents have a specific structure with head and body sections...",
                duration_minutes=20,
                is_active=True
            )
            
            # Create Module 2
            module2 = CourseModule.objects.create(
                course=course,
                title="CSS Fundamentals",
                description="Style your web pages with CSS",
                order=2,
                is_active=True
            )
            
            Lesson.objects.create(
                module=module2,
                title="Introduction to CSS",
                description="What is CSS and how to use it",
                lesson_type="video",
                order=1,
                video_url="https://www.youtube.com/watch?v=example3",
                duration_minutes=35,
                is_active=True
            )
            
            Lesson.objects.create(
                module=module2,
                title="CSS Selectors",
                description="Learn different types of CSS selectors",
                lesson_type="video",
                order=2,
                video_url="https://www.youtube.com/watch?v=example4",
                duration_minutes=40,
                is_active=True
            )
            
            # Create Module 3
            module3 = CourseModule.objects.create(
                course=course,
                title="JavaScript Basics",
                description="Add interactivity to your web pages",
                order=3,
                is_active=True
            )
            
            Lesson.objects.create(
                module=module3,
                title="Introduction to JavaScript",
                description="Getting started with JavaScript",
                lesson_type="video",
                order=1,
                video_url="https://www.youtube.com/watch?v=example5",
                duration_minutes=50,
                is_active=True
            )
            
            modules_count = CourseModule.objects.filter(course=course).count()
            lessons_count = Lesson.objects.filter(module__course=course).count()
            
            self.stdout.write(self.style.SUCCESS(
                f'✅ Successfully created {modules_count} modules and {lessons_count} lessons for {course.name}'
            ))
            
        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'❌ Course with ID {course_id} not found'
            ))