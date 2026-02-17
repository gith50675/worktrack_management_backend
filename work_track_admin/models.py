from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
from django.utils import timezone
from django.db import models
from django.db.models import DateField
from django.views.decorators.csrf import csrf_exempt



# Create your models here.
class User(AbstractUser):
    username = models.EmailField(unique=True)
    email = models.EmailField(unique=True)

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("project_lead", "Project Lead"),
        ("user", "User"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="user"
    )

    mobile = models.CharField(max_length=15, blank=True, null=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.email


class Task(models.Model):
    PRIORITY_CHOICES = [('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')]
    STATUS_CHOICES = [
        ('In Progress', 'In Progress'),
        ('Pending', 'Pending'),
        ('To Do', 'To Do'),
        ('Task Done', 'Task Done'),
        ('Completed', 'Completed')
    ]
    
    task_name = models.CharField(max_length=255)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    due_date = models.DateField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    assigned_to = models.ManyToManyField(User, blank=True, related_name='tasks')
    working_hours = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    discussion = models.TextField(blank=True)
    links = models.URLField(blank=True)
    attachments = models.URLField(blank=True)
    total_time = models.DurationField(default=timedelta())

    def __str__(self):
        return self.task_name


class Project(models.Model):
    PRIORITY_CHOICES = [('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')]
    STATUS_CHOICES = [
        ('In Progress', 'In Progress'),
        ('Pending', 'Pending'),
        ('To Do', 'To Do'),
        ('Task Done', 'Task Done'),
        ('Completed', 'Completed')
    ]
    ACTIVE_CHOICES = [('View', 'View'), ('Edit', 'Edit'), ('Delete', 'Delete')]
    
    project_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ManyToManyField(User, blank=True, related_name='projects')
    due_date = models.DateField(null=True, blank=True)
    est_hour = models.IntegerField(default=0)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    links = models.URLField(blank=True)
    attachments = models.FileField(upload_to="project_files/", blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    active = models.CharField(max_length=15, choices=ACTIVE_CHOICES, default='View')

    def __str__(self):
        return self.project_name


class TaskTime(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="sessions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_sessions")
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task", "user"],
                condition=models.Q(end_time__isnull=True),
                name="one_running_session_per_user_per_task"
            )
        ]
        
    def stop(self):
        if not self.end_time:
            self.end_time = timezone.now()
            self.duration = self.end_time - self.start_time
            self.save(update_fields=["end_time", "duration"])
            self.task.total_time += self.duration
            self.task.save(update_fields=["total_time"])

    def __str__(self):
        return f"{self.task.task_name} - {self.user.email}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.message}"

