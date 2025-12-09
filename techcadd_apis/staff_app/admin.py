from django.contrib import admin

# Register your models here.
from .models import StaffProfile, Student_api, StudentRegistration
admin.site.register(StaffProfile)
admin.site.register(Student_api)
admin.site.register(StudentRegistration)