from django.shortcuts import render

# Create your views here.
# admin_app/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .serializers import AdminLoginSerializer, UserSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    serializer = AdminLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_logout(request):
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_admin_profile(request):
    """Get current admin user profile"""
    user = request.user
    if not user.is_staff and not user.is_superuser:
        return Response({
            'error': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_admin_token(request):
    """Verify if the current token belongs to an admin user"""
    user = request.user
    if not user.is_staff and not user.is_superuser:
        return Response({
            'valid': False,
            'error': 'User is not an admin'
        }, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        'valid': True,
        'user': UserSerializer(user).data
    })

# ----------------------------------------staff section start here -----------------------------------

from staff_app.models import StaffProfile
from staff_app.serializers import StaffProfileSerializer, CreateStaffSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_staff_account(request):
    """Admin creates new staff account"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'error': 'Only admin can create staff accounts'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = CreateStaffSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            staff_profile = serializer.save()
            return Response({
                'message': 'Staff account created successfully',
                'staff_account': StaffProfileSerializer(staff_profile).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create staff account: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_staff(request):
    """Admin views all staff accounts"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'error': 'Only admin can view staff list'
        }, status=status.HTTP_403_FORBIDDEN)
    
    staff_profiles = StaffProfile.objects.select_related('user').all()
    serializer = StaffProfileSerializer(staff_profiles, many=True)
    
    return Response({
        'staff_count': staff_profiles.count(),
        'staff_list': serializer.data
    })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_staff_status(request, staff_id):
    """Admin activates/deactivates staff account"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'error': 'Only admin can update staff status'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        staff_profile = StaffProfile.objects.get(id=staff_id)
        staff_profile.is_active = request.data.get('is_active', staff_profile.is_active)
        
        # Update other fields if provided
        if 'role' in request.data:
            staff_profile.role = request.data['role']
        if 'department' in request.data:
            staff_profile.department = request.data['department']
        if 'phone' in request.data:
            staff_profile.phone = request.data['phone']
        if 'address' in request.data:
            staff_profile.address = request.data['address']
            
        staff_profile.save()
        
        return Response({
            'message': 'Staff account updated successfully',
            'staff_account': StaffProfileSerializer(staff_profile).data
        })
        
    except StaffProfile.DoesNotExist:
        return Response({
            'error': 'Staff account not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_staff_account(request, staff_id):
    """Admin permanently deletes staff account (user + profile)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'error': 'Only admin can delete staff accounts'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        staff_profile = StaffProfile.objects.get(id=staff_id)
        user = staff_profile.user
        
        # Get staff info before deletion for response
        staff_data = StaffProfileSerializer(staff_profile).data
        
        # Delete staff profile and user
        staff_profile.delete()
        user.delete()
        
        return Response({
            'message': 'Staff account deleted permanently',
            'deleted_staff': staff_data
        }, status=status.HTTP_200_OK)
        
    except StaffProfile.DoesNotExist:
        return Response({
            'error': 'Staff account not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_staff_detail(request, staff_id):
    """Admin gets specific staff account details"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'error': 'Only admin can view staff details'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        staff_profile = StaffProfile.objects.get(id=staff_id)
        serializer = StaffProfileSerializer(staff_profile)
        return Response(serializer.data)
        
    except StaffProfile.DoesNotExist:
        return Response({
            'error': 'Staff account not found'
        }, status=status.HTTP_404_NOT_FOUND)