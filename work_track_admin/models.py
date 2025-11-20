from datetime import timedelta

from django.contrib.auth.hashers import make_password,check_password
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from django.db.models import DateField
from django.views.decorators.csrf import csrf_exempt




# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    password = models.CharField(max_length=255)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def _str_(self):
        return self.email

class Tasks(models.Model):
    Priority_choices=[('High','High'),('Medium','Medium'),('Low','Low')]
    Status_choices=[('In Progress','In Progress'),('Pending','Pending'),('To Do','To Do'),('Task Done','Task Done')]

    Task_Name=models.CharField(max_length=100)
    Priority=models.CharField(max_length=20,choices= Priority_choices)
    Due_Date=models.DateField()
    Status=models.CharField(max_length=50,choices=Status_choices)
    Assigned_By=models.CharField(max_length=50)
    Working_Hours=models.IntegerField()
    Description=models.CharField(max_length=1000)
    Discussion=models.CharField(max_length=1000)
    Links=models.URLField()
    Attachments=models.URLField()
    Total_Time = models.DurationField(default=timedelta())

class Projects(models.Model):

    Priority_choices = [('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')]
    Status_choices = [('In Progress', 'In Progress'), ('Pending', 'Pending'), ('To Do', 'To Do'),
                      ('Task Done', 'Task Done')]
    Active_choices=[('View','View'),('Edit','Edit'),('Delete','Delete')]

    Project_Name=models.CharField(max_length=100)
    Company_Name=models.CharField(max_length=100)
    Description=models.CharField(max_length=1000)
    Assigned_to=models.ManyToManyField(User,blank=True,null=True)
    Due_Date = models.DateField(null=True, blank=True)
    Est_Hour=models.IntegerField()
    Priority=models.CharField(max_length=20,choices=Priority_choices)
    Links = models.URLField()
    Attachments = models.URLField()
    Status = models.CharField(max_length=50,choices=Status_choices)
    Active=models.CharField(max_length=15,choices=Active_choices)

class Task_Time(models.Model):
    Task = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="sessions")
    Start_Time = models.DateTimeField(default=timezone.now, null=True, blank=True)
    End_Time = models.DateTimeField(null=True, blank=True)
    Duration = models.DurationField(null=True, blank=True)

    def stop(self):
        if not self.End_Time:
            self.End_Time = timezone.now()
            self.Duration = self.End_Time - self.Start_Time
            self.save()
            self.Task.Total_Time += self.Duration
            self.Task.save()


