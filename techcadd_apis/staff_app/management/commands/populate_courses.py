# staff_app/management/commands/populate_courses.py
#  python manage.py populate_courses
from django.core.management.base import BaseCommand
from staff_app.models import CourseType, Course

class Command(BaseCommand):
    help = 'Populate course types and courses data'

    def handle(self, *args, **kwargs):
        # Course Types
        course_types_data = [
            {'id': 1, 'name': 'Civil'},
            {'id': 7, 'name': 'Mechanical'},
            {'id': 10, 'name': 'Computer Application'},
            {'id': 18, 'name': 'IT'},
            {'id': 14, 'name': 'Graphic Designing'},
            {'id': 11, 'name': 'Digital Marketing'},
        ]
        
        # Courses data by type
        courses_data = {
            'Civil': [
                {'name': 'Certificate Course in Civil CAD', 'duration': '3_months', 'hours': 120, 'fee': 15000},
                {'name': 'Diploma in Civil CAD', 'duration': '6_months', 'hours': 240, 'fee': 25000},
                {'name': 'Professional Diploma in Civil CAD', 'duration': '9_months', 'hours': 360, 'fee': 35000},
                {'name': 'Master Diploma in Civil CAD', 'duration': '1_year', 'hours': 480, 'fee': 45000},
            ],
            'IT': [
                {'name': 'Certificate in Programming Language', 'duration': '2_months', 'hours': 80, 'fee': 12000},
                {'name': 'Certificate in Web Designing', 'duration': '3_months', 'hours': 120, 'fee': 15000},
                {'name': 'Certificate in Web Development', 'duration': '3_months', 'hours': 120, 'fee': 16000},
                {'name': 'Diploma in Web Designing', 'duration': '6_months', 'hours': 240, 'fee': 25000},
                {'name': 'Diploma in Web Development', 'duration': '6_months', 'hours': 240, 'fee': 28000},
                {'name': 'Full Stack Web Development', 'duration': '6_months', 'hours': 300, 'fee': 35000},
                {'name': 'MERN Stack Development', 'duration': '6_months', 'hours': 300, 'fee': 38000},
                {'name': 'Certificate Course in Cyber Security', 'duration': '4_months', 'hours': 160, 'fee': 22000},
            ],
            'Computer Application': [
                {'name': 'Certificate in Computer Applications', 'duration': '3_months', 'hours': 120, 'fee': 10000},
                {'name': 'Advanced Computer Applications', 'duration': '6_months', 'hours': 240, 'fee': 18000},
            ],
            'Graphic Designing': [
                {'name': 'Certificate Course in Graphic Designing', 'duration': '3_months', 'hours': 120, 'fee': 15000},
                {'name': 'Diploma in Graphic Designing', 'duration': '6_months', 'hours': 240, 'fee': 25000},
                {'name': 'Professional Graphic Design Course', 'duration': '9_months', 'hours': 360, 'fee': 35000},
            ],
            'Digital Marketing': [
                {'name': 'Certificate in Digital Marketing', 'duration': '3_months', 'hours': 120, 'fee': 18000},
                {'name': 'Advanced Digital Marketing', 'duration': '6_months', 'hours': 240, 'fee': 30000},
            ],
            'Mechanical': [
                {'name': 'Certificate Course in Mechanical CAD', 'duration': '3_months', 'hours': 120, 'fee': 16000},
                {'name': 'Diploma in Mechanical CAD', 'duration': '6_months', 'hours': 240, 'fee': 28000},
                {'name': 'Professional Mechanical Design', 'duration': '9_months', 'hours': 360, 'fee': 40000},
            ]
        }
        
        # Create course types
        for type_data in course_types_data:
            course_type, created = CourseType.objects.get_or_create(
                id=type_data['id'],
                defaults={'name': type_data['name']}
            )
            if created:
                self.stdout.write(f"Created course type: {course_type.name}")
        
        # Create courses
        for type_name, courses in courses_data.items():
            course_type = CourseType.objects.get(name=type_name)
            for course_data in courses:
                course, created = Course.objects.get_or_create(
                    course_type=course_type,
                    name=course_data['name'],
                    defaults={
                        'duration_months': course_data['duration'],
                        'duration_hours': course_data['hours'],
                        'course_fee': course_data['fee'],
                        'software_covered': f"Software for {course_data['name']}"
                    }
                )
                if created:
                    self.stdout.write(f"Created course: {course.name}")
        
        self.stdout.write(self.style.SUCCESS('Successfully populated course data'))