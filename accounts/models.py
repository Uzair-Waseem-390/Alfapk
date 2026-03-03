from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, EmailValidator
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', self.model.Role.OWNER)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        # Check if owner already exists
        if self.model.objects.filter(role=self.model.Role.OWNER).exists():
            raise ValueError('An owner already exists. Cannot create another owner.')
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        ADMIN = 'ADMIN', 'Admin'
        MANAGER = 'MANAGER', 'Manager'
        SALESMAN = 'SALESMAN', 'Sales Man'

    username = None  # Remove username field
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.SALESMAN)
    
    # Employee specific fields
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                 validators=[MinValueValidator(0)])
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    # Personal information
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    
    # Profile picture (optional)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return f"{self.get_full_name()} - {self.get_role_display()}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @classmethod
    def owner_exists(cls):
        return cls.objects.filter(role=cls.Role.OWNER).exists()

    def save(self, *args, **kwargs):
        # Generate employee ID if not set
        if not self.employee_id:
            last_employee = User.objects.filter(employee_id__isnull=False).order_by('-id').first()
            if last_employee and last_employee.employee_id:
                try:
                    last_num = int(last_employee.employee_id.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.employee_id = f"EMP-{str(new_num).zfill(4)}"
        
        super().save(*args, **kwargs)

# Signal to assign permissions after user is saved
@receiver(post_save, sender=User)
def assign_role_permissions(sender, instance, created, **kwargs):
    """Assign user to appropriate group based on role"""
    if created or instance.role:
        # Clear existing groups
        instance.groups.clear()
        
        # Get or create group for role
        group_name = f"{instance.role}_GROUP"
        group, created = Group.objects.get_or_create(name=group_name)
        
        # Assign permissions based on role
        if instance.role == User.Role.OWNER:
            # Owner gets all permissions
            permissions = Permission.objects.all()
            group.permissions.set(permissions)
        
        elif instance.role == User.Role.ADMIN:
            # Admin permissions - can manage users but not owners
            content_type = ContentType.objects.get_for_model(User)
            permissions = Permission.objects.filter(
                content_type=content_type,
                codename__in=['view_user', 'change_user', 'add_user', 'delete_user']
            )
            group.permissions.set(permissions)
        
        elif instance.role == User.Role.MANAGER:
            # Manager permissions - can only view users
            content_type = ContentType.objects.get_for_model(User)
            permissions = Permission.objects.filter(
                content_type=content_type,
                codename__in=['view_user']
            )
            group.permissions.set(permissions)
        
        elif instance.role == User.Role.SALESMAN:
            # Salesman permissions - minimal access
            group.permissions.clear()
        
        # Add user to group
        instance.groups.add(group)

