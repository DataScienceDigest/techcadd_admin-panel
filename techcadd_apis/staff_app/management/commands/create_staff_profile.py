# staff_app/management/commands/create_staff_profile.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from staff_app.models import StaffProfile

class Command(BaseCommand):
    help = 'Create a StaffProfile for admin user'

    def handle(self, *args, **options):
        try:
            admin_user = User.objects.get(username='admin')
            StaffProfile.objects.create(
                user=admin_user,
                role='manager',
                department='Administration',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('StaffProfile created successfully!'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin user does not exist'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))