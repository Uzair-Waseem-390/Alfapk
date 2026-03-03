from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from .models import User
from .forms import OwnerSetupForm, EmployeeCreationForm, LoginForm, UserUpdateForm
from django.core.paginator import Paginator

def is_owner(user):
    return user.is_authenticated and user.role == User.Role.OWNER

def is_admin_or_owner(user):
    return user.is_authenticated and user.role in [User.Role.OWNER, User.Role.ADMIN]

def setup_owner(request):
    """First-time setup for owner"""
    if User.owner_exists():
        messages.warning(request, 'Owner already exists. Please login.')
        return redirect('login')
    
    if request.method == 'POST':
        form = OwnerSetupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Role.OWNER
            user.is_staff = True
            user.is_superuser = True
            user.save()
            login(request, user)
            messages.success(request, 'Owner account created successfully!')
            return redirect('dashboard')
    else:
        form = OwnerSetupForm()
    
    return render(request, 'accounts/setup_owner.html', {'form': form})

def login_view(request):
    """Login view that handles both owner and employee login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # If no owner exists, redirect to setup
    if not User.owner_exists():
        return redirect('setup_owner')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('root')

@login_required
def dashboard(request):
    """Dashboard view - blank for now"""
    return render(request, 'accounts/dashboard.html', {'user': request.user})

@login_required
@user_passes_test(is_owner)
def employee_list(request):
    """List all employees (only for owner)"""
    employees = User.objects.exclude(role=User.Role.OWNER).order_by('-date_joined')
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        employees = employees.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(role__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(employees, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'accounts/employee_list.html', {'page_obj': page_obj, 'query': query})

@login_required
@user_passes_test(is_owner)
def employee_create(request):
    """Create new employee (only for owner)"""
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, f'Employee {user.get_full_name()} created successfully!')
            return redirect('employee_list')
    else:
        form = EmployeeCreationForm()
    
    return render(request, 'accounts/employee_form.html', {'form': form, 'title': 'Add New Employee'})

@login_required
@user_passes_test(is_owner)
def employee_update(request, pk):
    """Update employee details (only for owner)"""
    employee = get_object_or_404(User, pk=pk)
    if employee.role == User.Role.OWNER:
        messages.error(request, 'Cannot edit owner through this interface.')
        return redirect('employee_list')
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=employee, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Employee {employee.get_full_name()} updated successfully!')
            return redirect('employee_list')
    else:
        form = UserUpdateForm(instance=employee, user=request.user)
    
    return render(request, 'accounts/employee_form.html', {
        'form': form, 
        'title': f'Edit Employee: {employee.get_full_name()}'
    })

@login_required
@user_passes_test(is_owner)
def employee_delete(request, pk):
    """Delete employee (only for owner)"""
    employee = get_object_or_404(User, pk=pk)
    if employee.role == User.Role.OWNER:
        messages.error(request, 'Cannot delete owner.')
        return redirect('employee_list')
    
    if request.method == 'POST':
        name = employee.get_full_name()
        employee.delete()
        messages.success(request, f'Employee {name} deleted successfully!')
        return redirect('employee_list')
    
    return render(request, 'accounts/employee_confirm_delete.html', {'employee': employee})

@login_required
def profile_view(request):
    """View user profile"""
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def profile_update(request):
    """Update user profile"""
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user, user=request.user)
    
    return render(request, 'accounts/profile_form.html', {'form': form})