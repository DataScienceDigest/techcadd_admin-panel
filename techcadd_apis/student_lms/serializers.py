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