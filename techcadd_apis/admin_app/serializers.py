# admin_app/serializers.py

from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth import authenticate

class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            
            if user:
                if not user.is_staff and not user.is_superuser:
                    raise serializers.ValidationError(
                        "Only admin users are allowed to login."
                    )
                data['user'] = user
            else:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials."
                )
        else:
            raise serializers.ValidationError(
                "Must include 'username' and 'password'."
            )

        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
