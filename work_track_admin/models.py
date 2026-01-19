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


class Tasks(models.Model):
    Priority_choices = [('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')]
    Status_choices = [('In Progress', 'In Progress'), ('Pending', 'Pending'), ('To Do', 'To Do'),
                      ('Task Done', 'Task Done')]
    Task_Name = models.CharField(max_length=100)
    Priority = models.CharField(max_length=20, choices=Priority_choices)
    Due_Date = models.DateField()
    Status = models.CharField(max_length=50, choices=Status_choices)
    Assigned_to = models.ManyToManyField(User, blank=True)
    Working_Hours = models.IntegerField()
    Description = models.CharField(max_length=1000)
    Discussion = models.CharField(max_length=1000)
    Links = models.URLField()
    Attachments = models.URLField()
    Total_Time = models.DurationField(default=timedelta())


class Projects(models.Model):
    Priority_choices = [('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')]
    Status_choices = [('In Progress', 'In Progress'), ('Pending', 'Pending'), ('To Do', 'To Do'),
                      ('Task Done', 'Task Done')]
    Active_choices = [('View', 'View'), ('Edit', 'Edit'), ('Delete', 'Delete')]
    Project_Name = models.CharField(max_length=100)
    Company_Name = models.CharField(max_length=100)
    Description = models.CharField(max_length=1000)
    Assigned_to = models.ManyToManyField(User, blank=True)
    Due_Date = models.DateField(null=True, blank=True)
    Est_Hour = models.IntegerField()
    Priority = models.CharField(max_length=20, choices=Priority_choices)
    Links = models.URLField()
    Attachments = models.FileField(upload_to="project_files/", blank=True, null=True)
    Status = models.CharField(max_length=50, choices=Status_choices)
    Active = models.CharField(max_length=15, choices=Active_choices)


class Task_Time(models.Model):
    Task = models.ForeignKey(
        Tasks,
        on_delete=models.CASCADE,
        related_name="sessions"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    Start_Time = models.DateTimeField(default=timezone.now)
    End_Time = models.DateTimeField(null=True, blank=True)
    Duration = models.DurationField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["Task", "user"],
                condition=models.Q(End_Time__isnull=True),
                name="one_running_session_per_user_per_task"
            )
        ]
    def stop(self):
        if not self.End_Time:
            self.End_Time = timezone.now()
            self.Duration = self.End_Time - self.Start_Time
            self.save(update_fields=["End_Time", "Duration"])
            self.Task.Total_Time += self.Duration
            self.Task.save(update_fields=["Total_Time"])

    def __str__(self):
        return f"{self.Task.Task_Name} - {self.user}"



User = settings.AUTH_USER_MODEL

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.message}"

