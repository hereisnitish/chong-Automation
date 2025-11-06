from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import User, Dashboard, EmailFolder
from django.db import IntegrityError
import json


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number
            )
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        except IntegrityError:
            messages.error(request, 'Email, username, or phone number already exists.')
            return render(request, 'signup.html')
    
    return render(request, 'signup.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username/email or password.')
    
    return render(request, 'login.html')


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required(login_url='login')
def dashboard_view(request):
    dashboard_records = Dashboard.objects.filter(user=request.user)
    
    context = {
        'dashboard_records': dashboard_records,
        'total_records': dashboard_records.count(),
        'whatsapp_count': dashboard_records.filter(type='whatsapp').count(),
        'gmail_count': dashboard_records.filter(type='gmail').count(),
        'sms_count': dashboard_records.filter(type='sms').count(),
    }
    
    return render(request, 'dashboard.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_dashboard_record(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        email = data.get('email')
        phone_number = data.get('phone_number')
        record_type = data.get('type')
        google_drive_link = data.get('google_drive_link', '')
        
        if not all([email, phone_number, record_type]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields: email, phone_number, type'
            }, status=400)
        
        if record_type not in ['whatsapp', 'gmail', 'sms']:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid type. Must be: whatsapp, gmail, or sms'
            }, status=400)
        
        user = User.objects.first()

        # if user_email:
        #     try:
        #         user = User.objects.get(email=user_email)
        #     except User.DoesNotExist:
        #         return JsonResponse({
        #             'status': 'error',
        #             'message': f'User with email {user_email} not found'
        #         }, status=404)
        # else:
        #     user = User.objects.first()
        
        if not user:
            return JsonResponse({
                'status': 'error',
                'message': 'No user available. Please provide user_email or create a user first.'
            }, status=400)
        
        dashboard_record = Dashboard.objects.create(
            user=user,
            email=email,
            phone_number=phone_number,
            type=record_type,
            google_drive_link=google_drive_link
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Dashboard record created successfully',
            'data': {
                'id': dashboard_record.id,
                'email': dashboard_record.email,
                'phone_number': dashboard_record.phone_number,
                'type': dashboard_record.type,
                'google_drive_link': dashboard_record.google_drive_link,
                'created_date': dashboard_record.created_date.isoformat(),
                'user': dashboard_record.user.email
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def search_email_records(request):
    try:
        if request.method == 'POST':
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            email = data.get('email')
        else:
            email = request.GET.get('email')
        
        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Email parameter is required'
            }, status=400)
        
        from datetime import datetime
        from django.utils import timezone
        
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        current_date = now.date()
        
        all_records = EmailFolder.objects.filter(email=email)
        
        email_exists = all_records.exists()
        
        if not email_exists:
            return JsonResponse({
                'status': 'success',
                'email': email,
                'exists': False,
                'has_current_year': False,
                'has_current_month': False,
                'has_today': False,
                'message': 'No folder records found for this email'
            }, status=200)
        
        year_records = all_records.filter(folder_year=current_year)
        month_records = year_records.filter(folder_month=current_month)
        today_records = month_records.filter(folder_date=current_date)
        
        has_current_year = year_records.exists()
        has_current_month = month_records.exists()
        has_today = today_records.exists()
        
        response_data = {
            'status': 'success',
            'email': email,
            'exists': True,
            'has_current_year': has_current_year,
            'has_current_month': has_current_month,
            'has_today': has_today,
            'message': 'Folder records found for this email'
        }
        
        latest_record = all_records.first()
        if latest_record:
            response_data['email_folder_id'] = latest_record.email_folder_id
        
        if has_current_year:
            year_record = year_records.first()
            response_data['year_folder_id'] = year_record.year_folder_id
        
        if has_current_month:
            month_record = month_records.first()
            response_data['month_folder_id'] = month_record.month_folder_id
        
        if has_today:
            today_record = today_records.first()
            response_data['date_folder_id'] = today_record.date_folder_id
        
        return JsonResponse(response_data, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_email_folder(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        email = data.get('email')
        email_folder_id = data.get('email_folder_id')
        year_folder_id = data.get('year_folder_id')
        month_folder_id = data.get('month_folder_id')
        date_folder_id = data.get('date_folder_id')
        folder_year = data.get('folder_year')
        folder_month = data.get('folder_month')
        folder_date = data.get('folder_date')
        
        if not all([email, email_folder_id, year_folder_id, month_folder_id, date_folder_id, folder_year, folder_month, folder_date]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields: email, email_folder_id, year_folder_id, month_folder_id, date_folder_id, folder_year, folder_month, folder_date'
            }, status=400)
        
        from datetime import datetime
        try:
            folder_year = int(folder_year)
            folder_month = int(folder_month)
            if isinstance(folder_date, str):
                folder_date = datetime.strptime(folder_date, '%Y-%m-%d').date()
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid date format. folder_year and folder_month must be integers, folder_date must be YYYY-MM-DD format'
            }, status=400)
        
        email_folder = EmailFolder.objects.create(
            email=email,
            email_folder_id=email_folder_id,
            year_folder_id=year_folder_id,
            month_folder_id=month_folder_id,
            date_folder_id=date_folder_id,
            folder_year=folder_year,
            folder_month=folder_month,
            folder_date=folder_date
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Email folder record created successfully',
            'data': {
                'id': email_folder.id,
                'email': email_folder.email,
                'email_folder_id': email_folder.email_folder_id,
                'year_folder_id': email_folder.year_folder_id,
                'month_folder_id': email_folder.month_folder_id,
                'date_folder_id': email_folder.date_folder_id,
                'folder_year': email_folder.folder_year,
                'folder_month': email_folder.folder_month,
                'folder_date': email_folder.folder_date.isoformat(),
                'created_at': email_folder.created_at.isoformat(),
                'updated_at': email_folder.updated_at.isoformat()
            }
        }, status=201)
        
    except IntegrityError:
        return JsonResponse({
            'status': 'error',
            'message': 'This folder structure already exists for this email and date'
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)



