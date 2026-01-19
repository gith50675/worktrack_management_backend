import json
import os
import time

from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime
import pyautogui
import self
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from datetime import datetime
from .models import Tasks, Notification
from .models import Projects, Task_Time
from .models import Tasks
from .models import User

import os
import time
import platform
import threading
from datetime import datetime, timedelta
import subprocess

import pyautogui
import psutil
from pynput import mouse, keyboard


import base64


from django.contrib.auth import get_user_model
User = get_user_model()

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Projects


@csrf_exempt
@require_http_methods(["POST"])
def Signup(request):
    try:
        data = json.loads(request.body.decode("utf-8"))

        name = data.get("name")
        email = data.get("email")
        mobile = data.get("mobile")
        password = data.get("password")

        if not all([name, email, mobile, password]):
            return JsonResponse({"error": "All fields are required"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email already registered"}, status=400)

        User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
            mobile=mobile,
            role="user"
        )

        return JsonResponse({"message": "User registered successfully"}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(["POST"])
@permission_classes([AllowAny])
def Login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)

    if not user:
        return Response({"error": "Invalid email or password"}, status=401)

    if not user.is_active:
        return Response({"error": "Account disabled"}, status=403)

    if user.role != "admin":
        return Response({"error": "Admin access only"}, status=403)

    refresh = RefreshToken.for_user(user)

    return Response({
        "message": "Admin login successful",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "role": user.role,
    })

@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)

    if not user:
        return Response({"error": "Invalid email or password"}, status=401)

    if not user.is_active:
        return Response({"error": "Account disabled"}, status=403)

    if user.role == "admin":
        return Response(
            {"error": "Admins must use admin login"},
            status=403
        )

    refresh = RefreshToken.for_user(user)

    return Response({
        "message": "User login successful",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "role": user.role,
    })

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

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user
    return Response({
        "id": user.id,
        "name": user.first_name,
        "email": user.email,
        "mobile": user.mobile,
        "role": user.role
    })



from django.http import JsonResponse
from .models import User
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Tasks

User = get_user_model()

@require_GET
def Get_Users(request):
    users = User.objects.filter(role="user")
    response_data = []

    for user in users:
        tasks = Tasks.objects.filter(Assigned_to=user)

        if tasks.exists():
            for task in tasks:
                response_data.append({
                    "id": task.id,
                    "user_id": user.id,
                    "user_name": user.first_name or user.email.split("@")[0],
                    "email": user.email,
                    "avatar": None,
                    "task_name": task.Task_Name,
                    "due_date": task.Due_Date.strftime("%Y-%m-%d") if task.Due_Date else "",
                    "status": task.Status,
                    "working_hours": f"{task.Working_Hours}h",
                    "priority": task.Priority,
                })
        else:
            response_data.append({
                "id": None,
                "user_id": user.id,
                "user_name": user.first_name or user.email.split("@")[0],
                "email": user.email,
                "avatar": None,
                "task_name": "No task assigned",
                "due_date": "-",
                "status": "Pending",
                "working_hours": "0h",
                "priority": "Low",
            })

    return JsonResponse(response_data, safe=False, status=200)


@require_GET
def Get_User_List(request):
    users = User.objects.filter(role="user").values(
        "id", "first_name", "email"
    )
    return JsonResponse(list(users), safe=False, status=200)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User

from django.contrib.auth import get_user_model
User = get_user_model()

@csrf_exempt
def Add_Tasks(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        task_name = data.get("task_name")
        priority = data.get("priority")
        due_date = data.get("due_date")
        status = data.get("status")
        assigned_ids = data.get("assigned_to", [])
        working_hours = data.get("working_hours", 0)
        description = data.get("description", "")

        if not (task_name and priority and due_date and assigned_ids):
            return JsonResponse({"error": "Required fields missing"}, status=400)

        try:
            assigned_ids = [int(uid) for uid in assigned_ids]
        except ValueError:
            return JsonResponse({"error": "Invalid user IDs"}, status=400)

        due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()

        task = Tasks.objects.create(
            Task_Name=task_name,
            Priority=priority,
            Due_Date=due_date_obj,
            Status=status,
            Working_Hours=working_hours,
            Description=description,
        )

        task.Assigned_to.set(assigned_ids)

        for user_id in assigned_ids:
            Notification.objects.create(
                user_id=user_id,
                message=f"You have been assigned a new task: {task.Task_Name}",
            )

        return JsonResponse(
            {"message": "Task successfully added", "task_id": task.id},
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



from django.http import JsonResponse
from django.db.models import Q
from .models import Tasks

from django.http import JsonResponse
from django.db.models import Q

def View_Tasks(request):
    if request.method == "GET":
        try:
            query = request.GET.get("search", "")

            tasks = Tasks.objects.all().order_by("-id")

            if query:
                tasks = tasks.filter(
                    Q(Task_Name__icontains=query) |
                    Q(Priority__icontains=query) |
                    Q(Status__icontains=query) |
                    Q(Description__icontains=query)
                )

            task_list = []
            for t in tasks:
                task_list.append({
                    "id": t.id,
                    "task_name": t.Task_Name,
                    "priority": t.Priority,
                    "due_date": t.Due_Date.strftime("%Y-%m-%d") if t.Due_Date else "",
                    "start_date": "",
                    "status": t.Status,

                    # FIX HERE 👇 convert ManyToMany to list
                    "assigned_to": list(
                        t.Assigned_to.values("id", "first_name", "last_name", "email")
                    ),

                    "working_hours": t.Working_Hours,
                    "description": t.Description,
                })

            return JsonResponse({
                "message": "Successfully viewed",
                "count": len(task_list),
                "tasks": task_list
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def View_User_Tasks(request):
    try:
        query = request.GET.get("search", "")

        # 🔐 ONLY TASKS ASSIGNED TO THE LOGGED-IN USER
        tasks = Tasks.objects.filter(
            Assigned_to=request.user
        ).order_by("-id")

        if query:
            tasks = tasks.filter(
                Q(Task_Name__icontains=query) |
                Q(Priority__icontains=query) |
                Q(Status__icontains=query) |
                Q(Description__icontains=query)
            )

        task_list = []
        for t in tasks:
            task_list.append({
                "id": t.id,
                "task_name": t.Task_Name,
                "priority": t.Priority,
                "due_date": t.Due_Date.strftime("%Y-%m-%d") if t.Due_Date else "",
                "start_date": "",
                "status": t.Status,
                "assigned_to": list(
                    t.Assigned_to.values("id", "first_name", "last_name", "email")
                ),
                "working_hours": t.Working_Hours,
                "description": t.Description,
            })

        return JsonResponse(
            {
                "count": len(task_list),
                "tasks": task_list,
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



from django.http import JsonResponse
from django.db.models import Q
def View_Single_Task(request, task_id):
    if request.method == "GET":
        try:
            task = Tasks.objects.get(id=task_id)

            data = {
                "id": task.id,
                "task_name": task.Task_Name,
                "description": task.Description,
                "priority": task.Priority,
                "due_date": task.Due_Date.strftime("%Y-%m-%d") if task.Due_Date else "",
                "status": task.Status,

                # FIX HERE 👇 ManyToMany → list aakki serialize cheyyanam
                "assigned_to": list(
                    task.Assigned_to.values("id", "first_name", "last_name", "email")
                ),
            }

            return JsonResponse({"task": data}, status=200)

        except Tasks.DoesNotExist:
            return JsonResponse({"error": "Task not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


from django.http import JsonResponse
from django.db.models import Q


@csrf_exempt
def Update_Tasks(request,id):
    tasks = get_object_or_404(Tasks,id=id)

    # ---------- GET ----------
    if request.method == 'GET':
        return JsonResponse({
            'task_name': tasks.Task_Name,
            'priority': tasks.Priority,
            'due_date': tasks.Due_Date,
            'status': tasks.Status,

            'assigned_to': [
                {
                    "id": u.id,
                    "name": f"{u.first_name} {u.last_name}".strip(),
                    "email": u.email
                }
                for u in tasks.Assigned_to.all()
            ],

            'description': tasks.Description,
            'working_hours': tasks.Working_Hours,
            'discussion': tasks.Discussion,
            'links': tasks.Links,
            'attachments': tasks.Attachments
        })

    # ---------- UPDATE ----------
    elif request.method == 'POST':
        try:
            tasks.Task_Name = request.POST.get('task-name', tasks.Task_Name)
            tasks.Priority = request.POST.get('priority', tasks.Priority)
            tasks.Due_Date = request.POST.get('due-date', tasks.Due_Date)
            tasks.Status = request.POST.get('status', tasks.Status)

            assigned_ids = request.POST.getlist('assigned-by[]')
            if assigned_ids:
                tasks.Assigned_to.set(assigned_ids)

            tasks.Description = request.POST.get('description', tasks.Description)
            tasks.Working_Hours = request.POST.get('working-hours', tasks.Working_Hours)
            tasks.Discussion = request.POST.get('discussion', tasks.Discussion)
            tasks.Links = request.POST.get('links', tasks.Links)
            tasks.Attachments = request.POST.get('attachments', tasks.Attachments)

            tasks.save()

            return JsonResponse({'message':'successfully updated','id':tasks.id})

        except Exception as e:
            return JsonResponse({'error': f'updated field {str(e)}'})

    return JsonResponse({'error':'invalid request method'})


@csrf_exempt
def Delete_Task(request,id):
    if request.method=='DELETE':
        try:
            del_task=get_object_or_404(Tasks,id=id)
            del_task.delete()
            return JsonResponse({'message':'successfully deleted'})
        except Exception as e:
            return JsonResponse({'error':f'Deleted data{str(e)}'})
    return JsonResponse({'error':'invalid request method'})

#total task
def total_tasks(request):
    total_tasks = Tasks.objects.count()
    return JsonResponse({
        "total_tasks": total_tasks
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def total_projects_by_user(request):
    # Filters projects where the logged-in user is assigned
    count = Projects.objects.filter(Assigned_to=request.user).count()
    return JsonResponse({"total_projects": count})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def total_tasks_summary(request):
    # Get tasks assigned to the logged-in user
    user_tasks = Tasks.objects.filter(Assigned_to=request.user)

    total = user_tasks.count()
    completed = user_tasks.filter(Status__iexact="Completed").count()
    unfinished = total - completed

    return JsonResponse({
        "total_tasks": total,
        "completed_tasks": completed,
        "unfinished_tasks": unfinished
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_dashboard_summary(request):
    # Optional: enforce admin role
    if request.user.role != "admin":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    total_projects = Projects.objects.count()
    total_tasks = Tasks.objects.count()
    completed_tasks = Tasks.objects.filter(Status__iexact="Completed").count()
    active_tasks = total_tasks - completed_tasks
    active_members = User.objects.filter(is_active=True).count()

    return JsonResponse({
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "completed_tasks": completed_tasks,
        "active_members": active_members,
    }, status=200)


# def total_tasks_by_users(request, username):
#     total_task = Tasks.objects.filter(
#         Assigned_By__iexact=username
#     ).count()
#
#     return JsonResponse({
#         "employee": username,
#         "total_tasks": total_task
#     })


@csrf_exempt
def Add_Projects(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        project_name = request.POST.get('project_name')
        company_name = request.POST.get('company_name')
        description = request.POST.get('description', '')
        assigned_id = request.POST.get('assigned_by')   # <-- USER ID
        due_date = request.POST.get('due_date') or None
        est_hour = request.POST.get('est_hr')
        priority = request.POST.get('priority')
        links = request.POST.get('links', '')
        status = request.POST.get('status', 'Pending')

        if not project_name or not company_name or not assigned_id:
            return JsonResponse({'error': 'Required fields missing'}, status=400)

        project = Projects.objects.create(
            Project_Name=project_name,
            Company_Name=company_name,
            Description=description,
            Due_Date=due_date,
            Est_Hour=int(est_hour),
            Priority=priority,
            Links=links,
            Status=status,
            Active='View'
        )

        # ----------- IMPORTANT FIX ----------
        user = User.objects.filter(id=assigned_id).first()
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)

        project.Assigned_to.add(user)
        # ------------------------------------
        print("ASSIGNED_ID:", assigned_id, type(assigned_id))
        print("USERS IN DB:", list(User.objects.values_list("id", flat=True)))

        return JsonResponse({
            'message': 'Project added successfully',
            'project_id': project.id
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def View_Projects(request):
    if request.method != "GET":
        return JsonResponse({'error': 'invalid request method'}, status=405)

    projects = Projects.objects.all().order_by('-id')

    status = request.GET.get("status")
    if status and status != "All":
        projects = projects.filter(Status=status)

    proj_list = []

    for p in projects:
        proj_list.append({
            "id": p.id,
            "Project_Name": p.Project_Name,
            "Company_Name": p.Company_Name,
            "Description": p.Description,

            # -------- SAFE USER SHOW ----------
            "Assigned_to": [
                (u.first_name or u.username or u.email)
                for u in p.Assigned_to.all()
            ],
            # -----------------------------------

            "Due_Date": p.Due_Date.strftime("%Y-%m-%d") if p.Due_Date else "",
            "Est_Hour": p.Est_Hour,
            "Priority": p.Priority,
            "Links": p.Links,
            "Status": p.Status
        })

    return JsonResponse({'message': 'success', 'projects': proj_list}, status=200)


@csrf_exempt
def View_Single_Project(request, project_id):
    if request.method != "GET":
        return JsonResponse({'error': 'invalid request method'}, status=405)

    try:
        p = Projects.objects.get(id=project_id)

        data = {
            "id": p.id,
            "Project_Name": p.Project_Name,
            "Company_Name": p.Company_Name,
            "Description": p.Description,

            # ---------- FIX HERE ----------
            "Assigned_to": [
                (u.first_name or u.username or u.email)
                for u in p.Assigned_to.all()
            ],
            # --------------------------------

            # ---------- DATE FIX ----------
            "Due_Date": p.Due_Date.strftime("%Y-%m-%d") if p.Due_Date else "",
            # --------------------------------

            "Est_Hour": p.Est_Hour,
            "Priority": p.Priority,
            "Links": p.Links,
            "Status": p.Status
        }

        return JsonResponse({'message': 'success', 'project': data}, status=200)

    except Projects.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def update_projects(request, id):
    proj = get_object_or_404(Projects, id=id)

    # ----------- GET = return editable data -----------
    if request.method == 'GET':
        return JsonResponse({
            "id": proj.id,
            "Project_Name": proj.Project_Name,
            "Company_Name": proj.Company_Name,
            "Description": proj.Description,
            "Assigned_to": [u.name for u in proj.Assigned_to.all()],
            "Due_Date": proj.Due_Date.strftime("%Y-%m-%d") if proj.Due_Date else "",
            "Est_Hour": proj.Est_Hour,
            "Priority": proj.Priority,
            "Links": proj.Links,
            "Attachments": proj.Attachments.url if proj.Attachments else "",
            "Status": proj.Status
        }, status=200)

    # ----------- UPDATE -----------
    elif request.method == "POST":
        try:
            proj.Project_Name = request.POST.get('project_name', proj.Project_Name)
            proj.Company_Name = request.POST.get('company_name', proj.Company_Name)
            proj.Description = request.POST.get('description', proj.Description)
            proj.Due_Date = request.POST.get('due_date', proj.Due_Date)
            proj.Est_Hour = request.POST.get('est_hr', proj.Est_Hour)
            proj.Priority = request.POST.get('priority', proj.Priority)
            proj.Links = request.POST.get('links', proj.Links)
            proj.Status = request.POST.get('status', proj.Status)

            # -------- UPDATE ASSIGNED USER --------
            assigned_id = request.POST.get("assigned_by")
            if assigned_id:
                user = User.objects.filter(id=assigned_id).first()
                if not user:
                    return JsonResponse({'error': "User not found"}, status=404)

                proj.Assigned_to.clear()
                proj.Assigned_to.add(user)

            # -------- FILE UPDATE (if needed) -------
            if 'attachments' in request.FILES:
                proj.Attachments = request.FILES['attachments']

            proj.save()

            return JsonResponse({'message': 'Successfully updated', 'id': proj.id}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'invalid request method'}, status=405)



User = get_user_model()

@csrf_exempt
def Delete_Projects(request,id):
    if request.method=='DELETE':
        try:
            projs=get_object_or_404(Projects,id=id)
            projs.delete()
            return JsonResponse({'message':'Successfully deleted datas'})
        except Exception as e:
            return JsonResponse({'error':f'deleted field    {str(e)}'})
    return JsonResponse({'error':'invalid request method'})


#total project
def total_projects(request):
    total = Projects.objects.filter(Active="View").count()
    return JsonResponse({
        "total_projects": total
    })

# def total_projects_by_user(request, username):
#     total = Projects.objects.filter(
#         Assigned_to__name__iexact=username
#     ).count()
#
#     return JsonResponse({
#         "user": username,
#         "total_projects": total
#     })


@csrf_exempt
def update_task_status(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))

        task_id = data.get("task_id")
        new_status = data.get("new_status")

        try:
            task = Tasks.objects.get(id=task_id)
            task.Status = new_status
            task.save()
            print(new_status)
            return JsonResponse({
                "status": "success",
                "message": "Task status updated successfully",
                "task_id": task_id,
                "new_status": new_status
            })

        except Tasks.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "Task not found"
            }, status=404)

    return JsonResponse({"status": "error", "message": "POST method required"}, status=400)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def Update_Task_Status(request, task_id):
    if request.user.role != "admin":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    status = request.data.get("status")

    if status not in ["Pending", "In Progress", "Completed"]:
        return JsonResponse({"error": "Invalid status"}, status=400)

    task = Tasks.objects.filter(id=task_id).first()
    if not task:
        return JsonResponse({"error": "Task not found"}, status=404)

    task.Status = status
    task.save()

    return JsonResponse({"message": "Status updated",
                         "status":task.Status}, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def kanban_tasks(request):
    if request.user.role != "admin":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    tasks = Tasks.objects.prefetch_related("Assigned_to")
    data = []
    for task in tasks:
        data.append({
            "id": task.id,
            "task_name": task.Task_Name,
            "status": task.Status,
            "priority": task.Priority,
            "assigned_to": [
                u.first_name or u.email for u in task.Assigned_to.all()
            ],
        })
    return JsonResponse(data, safe=False, status=200)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_task(request, task_id):

    try:
        task = Tasks.objects.get(id=task_id)
    except Tasks.DoesNotExist:
        return Response(
            {"error": "Task not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if Task_Time.objects.filter(
        Task=task,
        user=request.user,
        End_Time__isnull=True
    ).exists():
        return Response(
            {"error": "Task already running"},
            status=status.HTTP_400_BAD_REQUEST
        )

    Task_Time.objects.create(
        Task=task,
        user=request.user
    )

    return Response(
        {"message": "Task started"},
        status=status.HTTP_201_CREATED
    )



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stop_task(request, task_id):

    session = Task_Time.objects.filter(
        Task_id=task_id,
        user=request.user,
        End_Time__isnull=True
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
            "duration_seconds": int(session.Duration.total_seconds())
        },
        status=status.HTTP_200_OK
    )


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_running_task_session(request, task_id):
    session = Task_Time.objects.filter(
        Task_id=task_id,
        user=request.user,
        End_Time__isnull=True
    ).first()

    if not session:
        return Response({"running": False})

    elapsed_seconds = int(
        (timezone.now() - session.Start_Time).total_seconds()
    )

    return Response({
        "running": True,
        "start_time": session.Start_Time,
        "elapsed_seconds": elapsed_seconds
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_active_task(request):
    session = Task_Time.objects.filter(
        user=request.user,
        End_Time__isnull=True
    ).first()

    if not session:
        return Response({"running": False})

    elapsed_seconds = int(
        (timezone.now() - session.Start_Time).total_seconds()
    )

    return Response({
        "running": True,
        "task_id": session.Task_id,
        "elapsed_seconds": elapsed_seconds
    })


@require_http_methods(["GET"])
def Task_Summary(request):
    tasks=Tasks.objects.all()
    data=[]
    for t in tasks:
        data.append({
            "id":t.id,
            "Task_Name":t.Task_Name,
            "Total_Time":str(t.Total_Time),
            "Sessions":t.sessions.count()
        })
    return JsonResponse({"tasks":data})


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def View_Employees_Productivity(request):
    try:
        User = get_user_model()
        users = User.objects.all()
        data = []

        for user in users:
            tasks = Tasks.objects.filter(Assigned_to=user)

            total_tasks = tasks.count()
            completed_tasks = tasks.filter(Status="Completed").count()
            inprogress_tasks = tasks.filter(Status="In Progress").count()
            pending_tasks = tasks.filter(Status="Pending").count()

            today_tasks = tasks.filter(Due_Date=date.today()).count()

            total_hours = tasks.aggregate(
                total=Sum("Working_Hours")
            )["total"] or 0

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

        return Response({
            "status": True,
            "users": data
        }, status=200)

    except Exception as e:
        return Response({
            "status": False,
            "error": str(e)
        }, status=500)

from datetime import date
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Tasks

User = get_user_model()

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def View_Single_Employee_Productivity(request, user_id):
    try:
        user = User.objects.get(id=user_id)

        tasks = Tasks.objects.filter(Assigned_to=user).order_by('-id')

        total_tasks = tasks.count()
        completed_tasks = tasks.filter(Status="Completed").count()
        inprogress_tasks = tasks.filter(Status="In Progress").count()
        pending_tasks = tasks.filter(Status="Pending").count()

        today_tasks = tasks.filter(Due_Date=date.today()).count()

        total_hours = tasks.aggregate(total=Sum("Working_Hours"))["total"] or 0

        recent_tasks = [
            {
                "task_name": t.Task_Name,
                "status": t.Status,
                "due_date": t.Due_Date.strftime("%Y-%m-%d") if t.Due_Date else "",
            }
            for t in tasks[:5]      # last 5 tasks
        ]

        data = {
            "id": user.id,
            "name": user.first_name,
            "email": user.email,

            "active_projects": total_tasks,
            "in_progress": inprogress_tasks,
            "completed": completed_tasks,
            "idle_today": pending_tasks,

            "today_tasks": today_tasks,
            "worked_hours": f"{total_hours} Hr",

            "recent_tasks": recent_tasks
        }

        return Response({"status": True, "user": data}, status=200)

    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def employee_status_summary(request):
    user = request.user
    today = timezone.now().date()

    active_projects = Projects.objects.filter(
        Assigned_to=user,
        Status="In Progress"
    ).count()

    task_in_progress = Tasks.objects.filter(
        Assigned_to=user,
        Status="In Progress"
    ).count()

    completed_tasks = Tasks.objects.filter(
        Assigned_to=user,
        Status="Task Done"
    ).count()

    today_sessions = Task_Time.objects.filter(
        user=user,
        Start_Time__date=today
    )

    worked_seconds = sum(
        [(s.Duration or timedelta()).total_seconds() for s in today_sessions]
    )

    idle_seconds = max(0, 8 * 3600 - worked_seconds)  # assuming 8h workday

    return Response({
        "active_projects": active_projects,
        "task_in_progress": task_in_progress,
        "completed_tasks": completed_tasks,
        "idle_time_minutes": int(idle_seconds // 60),
    })


# #Screenshot and application detective
#
#
# # ==========================
# # CONFIGURATION
# # ==========================
#
# SCREENSHOT_INTERVAL_MIN = 30
# INACTIVITY_THRESHOLD_MIN = 5
# ACTIVE_APP_CHECK_SEC = 5
#
# BLACKLISTED_KEYWORDS = [
#     "youtube",
#     "spotify",
#     "netflix",
#     "prime video",
#     "hotstar"
# ]
#
# BASE_SCREENSHOT_DIR  = "screenshots"
# USER = os.getlogin()
# OS_NAME = platform.system()
#
# # ==========================
# # UTILITIES
# # ==========================
#
# def ensure_directory(path):
#     os.makedirs(path, exist_ok=True)
#
# def current_timestamp():
#     return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#
# def today_directory():
#     return os.path.join(BASE_SCREENSHOT_DIR , USER, datetime.now().strftime("%Y-%m-%d"))
#
# # ==========================
# # SCREENSHOT MANAGER
# # ==========================
#
# class ScreenshotManager:
#     @staticmethod
#     def capture(reason):
#         try:
#             directory = today_directory()
#             ensure_directory(directory)
#             filename = f"{current_timestamp()}_{reason}.png"
#             pyautogui.screenshot(os.path.join(directory, filename))
#         except Exception:
#             pass  # silent failure
#
# # ==========================
# # ACTIVITY TRACKER
# # ==========================
#
# class ActivityTracker:
#     def init(self):
#         self.last_activity = datetime.now()
#         self.lock = threading.Lock()
#
#     def update(self):
#         with self.lock:
#             self.last_activity = datetime.now()
#
#     def inactive_for(self):
#         with self.lock:
#             return datetime.now() - self.last_activity
#
#     def start(self):
#         mouse.Listener(
#             on_move=lambda *a: self.update(),
#             on_click=lambda *a: self.update(),
#             on_scroll=lambda *a: self.update()
#         ).start()
#
#         keyboard.Listener(
#             on_press=lambda *a: self.update(),
#             on_release=lambda *a: self.update()
#         ).start()
#
# # ==========================
# # ACTIVE WINDOW DETECTION
# # ==========================
#
# class ActiveWindowDetector:
#
#     @staticmethod
#     def get_active_window_text():
#         try:
#             if OS_NAME == "Windows":
#                 import win32gui, win32process
#                 hwnd = win32gui.GetForegroundWindow()
#                 _, pid = win32process.GetWindowThreadProcessId(hwnd)
#                 proc = psutil.Process(pid)
#                 return f"{proc.name()} {win32gui.GetWindowText(hwnd)}".lower()
#
#             elif OS_NAME == "Darwin":  # macOS
#                 from AppKit import NSWorkspace
#                 app = NSWorkspace.sharedWorkspace().frontmostApplication()
#                 return f"{app.localizedName()}".lower()
#
#             elif OS_NAME == "Linux":
#                 result = subprocess.check_output(["wmctrl", "-lp"])
#                 active = subprocess.check_output(["xdotool", "getwindowfocus", "getwindowpid"]).decode().strip()
#                 for line in result.decode().splitlines():
#                     if active in line:
#                         return line.lower()
#                 return ""
#
#         except Exception:
#             return ""
#
#     @staticmethod
#     def is_blacklisted(text):
#         return any(word in text for word in BLACKLISTED_KEYWORDS)
#
# # ==========================
# # CONTROLLER
# # ==========================
#
# class MonitorController:
#     def init(self):
#         self.activity = ActivityTracker()
#         self.last_interval = datetime.now()
#         self.inactivity_shot_taken = False
#
#     def start(self):
#         self.activity.start()
#         threading.Thread(target=self.interval_loop, daemon=True).start()
#         threading.Thread(target=self.inactivity_loop, daemon=True).start()
#         threading.Thread(target=self.app_monitor_loop, daemon=True).start()
#
#         while True:
#             time.sleep(60)
#
#     def _interval_screenshot_loop(self):
#         while True:
#             if datetime.now() - self.last_interval >= timedelta(minutes=SCREENSHOT_INTERVAL_MIN):
#                 ScreenshotManager.capture("interval")
#                 self.last_interval = datetime.now()
#             time.sleep(30)
#
#     def _inactivity_monitor_loop(self):
#         while True:
#             if self.activity.inactive_for() >= timedelta(minutes=INACTIVITY_THRESHOLD_MIN):
#                 if not self.inactivity_shot_taken:
#                     ScreenshotManager.capture("inactivity")
#                     self.inactivity_shot_taken = True
#             else:
#                 self.inactivity_shot_taken = False
#             time.sleep(10)
#
#     def _application_monitor_loop(self):
#         last_state = False
#         while True:
#             text = ActiveWindowDetector.get_active_window_text()
#             blacklisted = ActiveWindowDetector.is_blacklisted(text)
#             if blacklisted and not last_state:
#                 ScreenshotManager.capture("blacklisted")
#             last_state = blacklisted
#             time.sleep(ACTIVE_APP_CHECK_SEC)
#
#
# # ==========================
# # ENTRY POINT
# # ==========================
#
# if __name__ == "__main__":
#     MonitorController().start()
#
#
# @csrf_exempt
# def upload_screenshot(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "POST only"}, status=405)
#
#     try:
#         image_base64 = request.POST.get("image")
#         reason = request.POST.get("reason", "unknown")
#         username = request.POST.get("username", "anonymous")
#
#         if not image_base64:
#             return JsonResponse({"error": "Image required"}, status=400)
#
#         image_data = base64.b64decode(image_base64)
#
#         folder = f"media/screenshots/{username}"
#         os.makedirs(folder, exist_ok=True)
#
#         filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{reason}.png"
#         filepath = os.path.join(folder, filename)
#
#         with open(filepath, "wb") as f:
#             f.write(image_data)
#
#         return JsonResponse({"status": "success"})
#
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
#
#
# import base64
# import requests
# from io import BytesIO
#
# DJANGO_API_URL = "http://127.0.0.1:8000/api/upload-screenshot/"
#
#
# def send_screenshot_to_server(reason):
#     try:
#         screenshot = pyautogui.screenshot()
#         buffer = BytesIO()
#         screenshot.save(buffer, format="PNG")
#
#         encoded_image = base64.b64encode(buffer.getvalue()).decode()
#
#         payload = {
#             "image": encoded_image,
#             "reason": reason,
#             "username": USER
#         }
#
#         requests.post(DJANGO_API_URL, data=payload, timeout=5)
#
#     except Exception:
#         pass
# SCREENSHOT_INTERVAL_SEC = 60  # 1 minute
#
# def is_task_running(task_id):
#     try:
#         res = requests.get(
#             f"http://127.0.0.1:8000/tasks/{task_id}/running/",
#             headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
#             timeout=3
#         )
#         return res.json().get("running", False)
#     except Exception:
#         return False
#
#
# def screenshot_loop(task_id):
#     while True:
#         if is_task_running(task_id):
#             send_screenshot_to_server("interval")
#             time.sleep(SCREENSHOT_INTERVAL_SEC)
#         else:
#             time.sleep(5)  # check again



from rest_framework_simplejwt.authentication import JWTAuthentication
@csrf_exempt
@require_GET
def user_notifications(request):
    jwt_auth = JWTAuthentication()
    validated = jwt_auth.authenticate(request)

    if validated is None:
        return JsonResponse({"detail": "Authentication required"}, status=401)

    user, _ = validated

    notifications = (
        Notification.objects
        .filter(user=user)
        .order_by("-created_at")
    )

    data = [
        {
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ]

    return JsonResponse(data, safe=False, status=200)
