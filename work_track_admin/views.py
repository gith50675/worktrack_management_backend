import json
import os
import base64
import platform
import threading
import subprocess
import psutil
from datetime import datetime, date, timedelta

from django.contrib.auth import authenticate, get_user_model
from django.db.models import Sum, Q, F, ExpressionWrapper, DurationField
from django.db.models.functions import ExtractWeekDay
from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Task, Project, Notification, TaskTime
from .serializers import (
    UserSerializer,
    TaskSerializer,
    ProjectSerializer,
    TaskTimeSerializer,
    NotificationSerializer
)

User = get_user_model()

@api_view(["POST"])
@permission_classes([AllowAny])
def Signup(request):
    data = request.data.copy()
    # Handle the mapping of 'name' to 'first_name' and use email as username
    if 'name' in data:
        data['first_name'] = data.pop('name')
    if 'email' in data:
        data['username'] = data['email']
    
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        user.set_password(request.data.get('password'))
        user.save()
        return Response({
            "message": "User registered successfully",
            "user": serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def Login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)
    if user:
        if user.role != "admin":
            return Response({"error": "Admin access only"}, status=status.HTTP_403_FORBIDDEN)
        
        if not user.is_active:
            return Response({"error": "Account disabled"}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Admin login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": user.role,
        }, status=status.HTTP_200_OK)

    return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)
    if user:
        if not user.is_active:
            return Response({"error": "Account disabled"}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "User login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": user.role,
        }, status=status.HTTP_200_OK)

    return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logged out successfully"})
    except Exception:
        return Response({"error": "Invalid token"}, status=400)

@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def delete_user(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def Get_Users(request):
    users = User.objects.filter(role="user")
    response_data = []

    for user in users:
        tasks = Task.objects.filter(assigned_to=user)
        if tasks.exists():
            for task in tasks:
                response_data.append({
                    "id": task.id,
                    "user_id": user.id,
                    "user_name": user.first_name or user.username.split("@")[0],
                    "email": user.email,
                    "avatar": None,
                    "task_name": task.task_name,
                    "due_date": task.due_date.strftime("%Y-%m-%d") if task.due_date else "",
                    "status": task.status,
                    "working_hours": f"{task.working_hours}h",
                    "priority": task.priority,
                })
        else:
            response_data.append({
                "id": None,
                "user_id": user.id,
                "user_name": user.first_name or user.username.split("@")[0],
                "email": user.email,
                "avatar": None,
                "task_name": "No task assigned",
                "due_date": "-",
                "status": "Pending",
                "working_hours": "0h",
                "priority": "Low",
            })

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def Get_User_List(request):
    users = User.objects.filter(role="user")
    serializer = UserSerializer(users, many=True)
    # Filter to only return id, first_name, email as per original logic
    data = [
        {"id": u['id'], "first_name": u['first_name'], "email": u['email']}
        for u in serializer.data
    ]
    return Response(data, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([IsAdminUser])
def Add_Tasks(request):
    data = request.data.copy()
    mapping = {
        'task_name': 'task_name',
        'priority': 'priority',
        'due_date': 'due_date',
        'status': 'status',
        'working_hours': 'working_hours',
        'description': 'description',
        'assigned_to': 'assigned_to'
    }
    
    formatted_data = {mapping.get(k, k): v for k, v in data.items()}
    
    serializer = TaskSerializer(data=formatted_data)
    if serializer.is_valid():
        task = serializer.save()
        
        # Create notifications
        for user in task.assigned_to.all():
            Notification.objects.create(
                user=user,
                message=f"You have been assigned a new task: {task.task_name}"
            )
            
        return Response({
            "message": "Task successfully added",
            "task": serializer.data
        }, status=status.HTTP_201_CREATED)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def View_Tasks(request):
    query = request.GET.get("search", "")
    tasks = Task.objects.all().order_by("-id")

    if query:
        tasks = tasks.filter(
            Q(task_name__icontains=query) |
            Q(priority__icontains=query) |
            Q(status__icontains=query) |
            Q(description__icontains=query)
        )

    serializer = TaskSerializer(tasks, many=True)
    return Response({
        "count": len(serializer.data),
        "tasks": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def View_User_Tasks(request):
    query = request.GET.get("search", "")
    tasks = Task.objects.filter(assigned_to=request.user).order_by("-id")

    if query:
        tasks = tasks.filter(
            Q(task_name__icontains=query) |
            Q(priority__icontains=query) |
            Q(status__icontains=query) |
            Q(description__icontains=query)
        )

    serializer = TaskSerializer(tasks, many=True)
    return Response({
        "count": len(serializer.data),
        "tasks": serializer.data
    }, status=status.HTTP_200_OK)



from django.http import JsonResponse
from django.db.models import Q
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def View_Single_Task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    serializer = TaskSerializer(task)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET", "POST", "PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def Update_Tasks(request, id):
    task = get_object_or_404(Task, id=id)

    if request.method == 'GET':
        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # For update, require admin role as per original logic for POST
    if request.user.role != "admin":
        return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)

    data = request.data.copy()
    # Handle legacy frontend field mappings if necessary
    mapping = {
        'task-name': 'task_name',
        'priority': 'priority',
        'due-date': 'due_date',
        'status': 'status',
        'description': 'description',
        'working-hours': 'working_hours',
        'discussion': 'discussion',
        'links': 'links',
        'attachments': 'attachments',
        'assigned-by[]': 'assigned_to'
    }
    formatted_data = {mapping.get(k, k): v for k, v in data.items()}

    serializer = TaskSerializer(task, data=formatted_data, partial=(request.method in ['PATCH', 'POST']))
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "successfully updated",
            "task": serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def Delete_Task(request, id):
    task = get_object_or_404(Task, id=id)
    task.delete()
    return Response({'message': 'successfully deleted'}, status=status.HTTP_200_OK)

#total task
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def total_tasks(request):
    total = Task.objects.count()
    return Response({"total_tasks": total}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def total_projects_by_user(request):
    # Filters projects where the logged-in user is assigned
    count = Project.objects.filter(assigned_to=request.user).count()
    return Response({"total_projects": count}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def total_tasks_summary(request):
    # Get tasks assigned to the logged-in user
    user_tasks = Task.objects.filter(assigned_to=request.user)

    total = user_tasks.count()
    todo = user_tasks.filter(status__iexact="To Do").count()
    inprogress = user_tasks.filter(status__iexact="In Progress").count()
    pending = user_tasks.filter(status__iexact="Pending").count()
    taskdone = user_tasks.filter(status__iexact="Task Done").count()
    completed = user_tasks.filter(status__iexact="Completed").count()
    
    unfinished = total - completed

    return Response({
        "total_tasks": total,
        "todo_tasks": todo,
        "inprogress_tasks": inprogress,
        "pending_tasks": pending,
        "taskdone_tasks": taskdone,
        "completed_tasks": completed,
        "unfinished_tasks": unfinished
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_tasks_summary(request):
    # Get all tasks for admin view
    all_tasks = Task.objects.all()

    total = all_tasks.count()
    todo = all_tasks.filter(status__iexact="To Do").count()
    inprogress = all_tasks.filter(status__iexact="In Progress").count()
    pending = all_tasks.filter(status__iexact="Pending").count()
    taskdone = all_tasks.filter(status__iexact="Task Done").count()
    completed = all_tasks.filter(status__iexact="Completed").count()
    
    return Response({
        "total_tasks": total,
        "todo_tasks": todo,
        "inprogress_tasks": inprogress,
        "pending_tasks": pending,
        "taskdone_tasks": taskdone,
        "completed_tasks": completed
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_dashboard_summary(request):
    # Optional: enforce admin role
    if request.user.role != "admin":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    total_projects = Project.objects.count()
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status__iexact="Completed").count()
    active_tasks = total_tasks - completed_tasks
    active_members = User.objects.filter(is_active=True).count()

    return Response({
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "completed_tasks": completed_tasks,
        "active_members": active_members,
    }, status=status.HTTP_200_OK)


# def total_tasks_by_users(request, username):
#     total_task = Tasks.objects.filter(
#         Assigned_By__iexact=username
#     ).count()
#
#     return JsonResponse({
#         "employee": username,
#         "total_tasks": total_task
#     })


@api_view(["POST"])
@permission_classes([IsAdminUser])
def Add_Projects(request):
    data = request.data.copy()
    mapping = {
        'project_name': 'project_name',
        'company_name': 'company_name',
        'description': 'description',
        'assigned_by': 'assigned_to',
        'due_date': 'due_date',
        'est_hr': 'est_hour',
        'priority': 'priority',
        'links': 'links',
        'status': 'status'
    }
    
    formatted_data = {mapping.get(k, k): v for k, v in data.items()}
    
    # Ensure assigned_to is a list of IDs for the serializer if it's currently a single ID
    if 'assigned_to' in formatted_data:
        val = formatted_data['assigned_to']
        if not isinstance(val, list):
            # If it's a comma-separated string from FormData, split it
            if isinstance(val, str) and ',' in val:
                formatted_data['assigned_to'] = [x.strip() for x in val.split(',')]
            else:
                formatted_data['assigned_to'] = [val]

    # Handle attachments separately if not already in formatted_data
    if 'attachments' in request.FILES:
        # If model only supports one file, take the first one
        attachments = request.FILES.getlist('attachments')
        if attachments:
            formatted_data['attachments'] = attachments[0]
    
    serializer = ProjectSerializer(data=formatted_data)
    if serializer.is_valid():
        project = serializer.save(active='View')
        return Response({
            'message': 'Project added successfully',
            'project': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def View_Projects(request):
    projects = Project.objects.all().order_by('-id')

    status_filter = request.query_params.get("status")
    if status_filter and status_filter != "All":
        projects = projects.filter(status=status_filter)

    serializer = ProjectSerializer(projects, many=True)
    return Response({
        'message': 'success', 
        'count': len(serializer.data),
        'projects': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def View_Single_Project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    serializer = ProjectSerializer(project)
    return Response({
        'message': 'success', 
        'project': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(["GET", "POST", "PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_projects(request, id):
    project = get_object_or_404(Project, id=id)

    if request.method == 'GET':
        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.user.role != "admin":
        return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)

    data = request.data.copy()
    mapping = {
        'project_name': 'project_name',
        'company_name': 'company_name',
        'description': 'description',
        'due_date': 'due_date',
        'est_hr': 'est_hour',
        'priority': 'priority',
        'links': 'links',
        'status': 'status',
        'assigned_by': 'assigned_to'
    }
    formatted_data = {mapping.get(k, k): v for k, v in data.items()}
    if 'assigned_to' in formatted_data and not isinstance(formatted_data['assigned_to'], list):
        formatted_data['assigned_to'] = [formatted_data['assigned_to']]

    serializer = ProjectSerializer(project, data=formatted_data, partial=(request.method in ['PATCH', 'POST']))
    if serializer.is_valid():
        serializer.save()
        if 'attachments' in request.FILES:
            project.attachments = request.FILES['attachments']
            project.save()
            
        return Response({
            'message': 'Successfully updated',
            'project': serializer.data
        }, status=status.HTTP_200_OK)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def Delete_Projects(request, id):
    project = get_object_or_404(Project, id=id)
    project.delete()
    return Response({'message': 'Successfully deleted'}, status=status.HTTP_200_OK)


#total project
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def total_projects(request):
    total = Project.objects.filter(active="View").count()
    return Response({"total_projects": total}, status=status.HTTP_200_OK)

# def total_projects_by_user(request, username):
#     total = Projects.objects.filter(
#         Assigned_to__name__iexact=username
#     ).count()
#
#     return JsonResponse({
#         "user": username,
#         "total_projects": total
#     })


@api_view(["POST", "PATCH"])
@permission_classes([IsAuthenticated])
def update_task_status(request, task_id=None):
    # Support both task_id in URL or in POST data
    tid = task_id or request.data.get("task_id")
    new_status = request.data.get("status") or request.data.get("new_status")
    
    if not tid or not new_status:
        return Response({"error": "task_id and status required"}, status=status.HTTP_400_BAD_REQUEST)
        
    task = get_object_or_404(Task, id=tid)
    
    # Optional: if role is user, ensure they are assigned to this task
    if request.user.role != "admin" and not task.assigned_to.filter(id=request.user.id).exists():
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    valid_statuses = ["Pending", "In Progress", "Completed", "Task Done", "To Do"]
    if new_status not in valid_statuses:
        return Response({"error": f"Invalid status. Must be one of {valid_statuses}"}, status=status.HTTP_400_BAD_REQUEST)

    task.status = new_status
    task.save()
    
    return Response({
        "message": "Task status updated successfully",
        "task_id": tid,
        "status": task.status
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def weekly_work_report(request):
    try:
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)

        sessions = (
            TaskTime.objects
            .filter(
                user=request.user,
                start_time__date__gte=start_of_week,
                start_time__date__lte=end_of_week,
                end_time__isnull=False
            )
            .annotate(
                duration_expr=ExpressionWrapper(
                    F("end_time") - F("start_time"),
                    output_field=DurationField()
                ),
                weekday=ExtractWeekDay("start_time")  # 1=Sun, 2=Mon...
            )
        )

        days_map = {
            2: {"day": "Mon", "hours": 0},
            3: {"day": "Tue", "hours": 0},
            4: {"day": "Wed", "hours": 0},
            5: {"day": "Thu", "hours": 0},
            6: {"day": "Fri", "hours": 0},
            7: {"day": "Sat", "hours": 0},
            1: {"day": "Sun", "hours": 0},
        }
        for s in sessions:
            hours = s.duration.total_seconds() / 3600
            days_map[s.weekday]["hours"] += round(hours, 2)
        return Response(list(days_map.values()), status=status.HTTP_200_OK)
    except Exception:
        return Response({"error": "An internal error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def kanban_tasks(request):
    if request.user.role == "admin":
        tasks = Task.objects.all().prefetch_related("assigned_to")
    else:
        tasks = Task.objects.filter(assigned_to=request.user).prefetch_related("assigned_to")
    
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_task(request, task_id):

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response(
            {"error": "Task not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if TaskTime.objects.filter(
        task=task,
        user=request.user,
        end_time__isnull=True
    ).exists():
        return Response(
            {"error": "Task already running"},
            status=status.HTTP_400_BAD_REQUEST
        )

    TaskTime.objects.create(
        task=task,
        user=request.user
    )

    return Response(
        {"message": "Task started"},
        status=status.HTTP_201_CREATED
    )



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stop_task(request, task_id):

    session = TaskTime.objects.filter(
        task_id=task_id,
        user=request.user,
        end_time__isnull=True
    ).first()

    if not session:
        return Response(
            {"error": "No running task"},
            status=status.HTTP_400_BAD_REQUEST
        )

    session.stop()

    return Response(
        {
            "message": "Task stopped",
            "duration_seconds": int(session.duration.total_seconds())
        },
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_running_task_session(request, task_id):
    session = TaskTime.objects.filter(
        task_id=task_id,
        user=request.user,
        end_time__isnull=True
    ).first()

    if not session:
        return Response({"running": False}, status=status.HTTP_200_OK)

    elapsed_seconds = int((timezone.now() - session.start_time).total_seconds())
    return Response({
        "running": True,
        "start_time": session.start_time.isoformat(),
        "elapsed_seconds": elapsed_seconds
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_active_task(request):
    session = TaskTime.objects.filter(
        user=request.user,
        end_time__isnull=True
    ).first()

    if not session:
        return Response({"running": False})

    elapsed_seconds = int(
        (timezone.now() - session.start_time).total_seconds()
    )

    return Response({
        "running": True,
        "task_id": session.task_id,
        "elapsed_seconds": elapsed_seconds
    })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def Task_Summary(request):
    tasks = Task.objects.all()
    data = []
    for t in tasks:
        data.append({
            "id": t.id,
            "task_name": t.task_name,
            "total_time": str(t.total_time),
            "sessions": t.sessions.count()
        })
    return Response({"tasks": data}, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAdminUser])
def View_Employees_Productivity(request):
    users = User.objects.filter(role="user")
    data = []

    for user in users:
        tasks = Task.objects.filter(assigned_to=user)
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status="Completed").count()
        total_hours = tasks.aggregate(total=Sum("working_hours"))["total"] or 0
        today_tasks = tasks.filter(due_date=date.today()).count()

        productivity = 0
        if total_tasks > 0:
            productivity = round((completed_tasks / total_tasks) * 100)

        data.append({
            "id": user.id,
            "name": user.first_name or "Unnamed",
            "email": user.email,
            "time": f"{today_tasks} Tasks",
            "efficiency": f"{total_hours} Hr",
            "percent": productivity
        })

    return Response({"users": data}, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAdminUser])
def View_Single_Employee_Productivity(request, user_id):
    user = get_object_or_404(User, id=user_id)
    tasks = Task.objects.filter(assigned_to=user).order_by('-id')

    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status="Completed").count()
    inprogress_tasks = tasks.filter(status="In Progress").count()
    pending_tasks = tasks.filter(status="Pending").count()
    today_tasks = tasks.filter(due_date=date.today()).count()
    total_hours = tasks.aggregate(total=Sum("working_hours"))["total"] or 0

    recent_tasks = [
        {
            "task_name": t.task_name,
            "status": t.status,
            "due_date": t.due_date.strftime("%Y-%m-%d") if t.due_date else "",
        }
        for t in tasks[:5]
    ]
    
    # Task list for the bottom table
    task_list = TaskSerializer(tasks, many=True).data

    data = {
        "user": {
            "id": user.id,
            "name": user.first_name or user.username,
            "email": user.email,
            "active_projects": total_tasks,
            "in_progress": inprogress_tasks,
            "completed": completed_tasks,
            "idle_today": pending_tasks,
            "today_tasks": today_tasks,
            "worked_hours": f"{total_hours} Hr",
            "recent_tasks": recent_tasks,
        },
        "productivity": {
            "productive": 70,  # Placeholder/calculated based on completed
            "neutral": 20,
            "unproductive": 10
        },
        "tasks": task_list
    }

    return Response(data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def employee_status_summary(request):
    user = request.user
    today = timezone.now().date()

    active_projects = Project.objects.filter(
        assigned_to=user,
        status="In Progress"
    ).count()

    task_in_progress = Task.objects.filter(
        assigned_to=user,
        status="In Progress"
    ).count()

    completed_tasks = Task.objects.filter(
        assigned_to=user,
        status="Task Done"
    ).count()

    today_sessions = TaskTime.objects.filter(
        user=user,
        start_time__date=today
    )

    worked_seconds = sum(
        [(s.duration or timedelta()).total_seconds() for s in today_sessions]
    )

    idle_seconds = max(0, 8 * 3600 - worked_seconds)  # assuming 8h workday

    return Response({
        "active_projects": active_projects,
        "task_in_progress": task_in_progress,
        "completed_tasks": completed_tasks,
        "idle_time_minutes": int(idle_seconds // 60),
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def upload_screenshot(request):
    try:
        data = request.data
        image_base64 = data.get("image")
        reason = data.get("reason", "unknown")
        username = data.get("username", "anonymous")

        if not image_base64:
            return Response({"error": "Image required"}, status=status.HTTP_400_BAD_REQUEST)

        image_data = base64.b64decode(image_base64)
        folder = f"media/screenshots/{username}"
        os.makedirs(folder, exist_ok=True)

        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{reason}.png"
        filepath = os.path.join(folder, filename)

        with open(filepath, "wb") as f:
            f.write(image_data)

        return Response({"status": "success"}, status=status.HTTP_201_CREATED)

    except Exception:
        return Response({"error": "An internal error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
