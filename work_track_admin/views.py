import json
import time


import pyautogui
import self
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Projects, Task_Time
from .models import Tasks
from .models import User



from django.contrib.auth import get_user_model
User = get_user_model()

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

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
            mobile=mobile
        )

        return JsonResponse({"message": "User registered successfully"}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def Login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)
    if not user:
        return JsonResponse({"error": "Invalid email or password"}, status=401)

    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role

    return JsonResponse({
        "message": "Login successful",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "name": user.first_name,
            "email": user.email,
            "mobile": user.mobile,
            "role": user.role,
        }
    }, status=200)


@csrf_exempt
def Add_Tasks(request):
    if request.method=='POST':
        try:
            task_name=request.POST.get('task-name')
            priority=request.POST.get('priority')
            due_date=request.POST.get('due-date')
            status=request.POST.get('status')
            assigned_by=request.POST.get('assigned-by')
            working_hours=request.POST.get('working-hours')
            description=request.POST.get('description')
            discussion=request.POST.get('discussion')
            links=request.POST.get('links')
            attachments=request.POST.get('attachments')
            if task_name and priority and due_date and assigned_by:
                user=Tasks.objects.create(
                    Task_Name=task_name,
                    Priority=priority,
                    Due_Date=due_date,
                    Status=status,
                    Assigned_By=assigned_by,
                    Working_Hours=working_hours,
                    Description=description,
                    Discussion=discussion,
                    Links=links,
                    Attachments=attachments
                )
                return JsonResponse({'message':'successfully added','user':user.id})
        except Exception as e:
            return JsonResponse({'error':f'added field{str(e)}'})
    return JsonResponse({'error':'invalid request method'})



def View_Tasks(request):
    if request.method == "GET":
        try:
            tasks = Tasks.objects.all()
            task_list = []

            for i in tasks:
                task_list.append({
                    "id": i.id,
                    "task_name": i.Task_Name,
                    "priority": i.Priority,
                    "due_date": i.Due_Date,
                    "status": i.Status,
                    "assigned_by": i.Assigned_By,
                    "working_hours": i.Working_Hours,
                    "description": i.Description,
                })

            return JsonResponse({
                "message": "Successfully viewed",
                "tasks": task_list
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)



@csrf_exempt
def Update_Tasks(request,id):
    tasks=get_object_or_404(Tasks,id=id)
    if request.method=='GET':
        return JsonResponse({
            'Task_Name':tasks.Task_Name,
            'Priority':tasks.Priority,
            'Due_Date':tasks.Due_Date,
            'Status':tasks.Status,
            'Assigned to':tasks.Assigned_By,
            'Description':tasks.Description,
            'Effort Hours':tasks.Working_Hours,
            'Discussion':tasks.Discussion,
            'Links':tasks.Links,
            'Attachments':tasks.Attachments
        })
    elif request.method=='POST':
        try:
            update_taskname=request.POST.get('task-name',tasks.Task_Name)
            update_priority=request.POST.get('priority',tasks.Priority)
            update_duedate=request.POST.get('due-date',tasks.Due_Date)
            update_status=request.POST.get('status',tasks.Status)
            update_assignedto=request.POST.get('assigned-by',tasks.Assigned_By)
            update_description=request.POST.get('description',tasks.Description)
            update_efforthrs=request.POST.get('working-hours',tasks.Working_Hours)
            update_discussion=request.POST.get('discussion',tasks.Discussion)
            update_links=request.POST.get('links',tasks.Links)
            update_attachments=request.POST.get('attachments',tasks.Attachments)

            tasks.Task_Name=update_taskname
            tasks.Priority=update_priority
            tasks.Due_Date=update_duedate
            tasks.Status=update_status
            tasks.Assigned_By=update_assignedto
            tasks.Description=update_description
            tasks.Working_Hours=update_efforthrs
            tasks.Discussion=update_discussion
            tasks.Links=update_links
            tasks.Attachments=update_attachments

            tasks.save()
            return JsonResponse({'message':'successfully updated','id':tasks.id})
        except Exception as e:
            return JsonResponse({'error':f'updated filled{str(e)}'})
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

# Projects(CRUD)

@csrf_exempt
def Add_Projects(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        project_name = request.POST.get('project_name')
        company_name = request.POST.get('company_name')
        description = request.POST.get('description', '')
        assigned_name = request.POST.get('assigned_by')   # USER NAME
        due_date = request.POST.get('due_date') or None
        est_hour = request.POST.get('est_hr')
        priority = request.POST.get('priority')
        links = request.POST.get('links', '')
        status = request.POST.get('status', 'Pending')

        if not project_name or not company_name or not assigned_name:
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


        user = User.objects.filter(
            name__iexact=assigned_name  # case-insensitive
        ).first()

        if not user:
            return JsonResponse(
                {'error': f'User "{assigned_name}" not found'},
                status=404
            )


        project.Assigned_to.add(user)

        return JsonResponse({
            'message': 'Project added successfully',
            'project_id': project.id
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def View_Projects(request):
    if request.method != "GET":
        return JsonResponse({'error': 'invalid request method'}, status=405)

    proj_list = []

    for p in Projects.objects.all():
        proj_list.append({
            "id": p.id,
            "Project_Name": p.Project_Name,
            "Company_Name": p.Company_Name,
            "Description": p.Description,
            "Assigned_to": [u.name for u in p.Assigned_to.all()],
            "Due_Date": p.Due_Date,
            "Est_Hour": p.Est_Hour,
            "Priority": p.Priority,
            "Links": p.Links,
            "Status": p.Status
        })

    return JsonResponse({'message': 'success', 'id': proj_list}, safe=False)
@csrf_exempt
def update_projects(request,id):
    proj = get_object_or_404(Projects,id=id)
    if request.method=='GET':
        return JsonResponse({
            "Project_Name":proj.Project_Name,
            "Company_Name": proj.Company_Name,
            'Description': proj.Description,
            'Assigned_to': proj.Assigned_to,
            'Due_Date': proj.Due_Date,
            'Est_Hour': proj.Est_Hour,
            'Priority': proj.Priority,
            'Links': proj.Links,
            'Attachments': proj.Attachments,
            'Status': proj.Status
        })
    elif request.method=="POST":
        try:
            update_projectname = request.POST.get('task-name', proj.Project_Name)
            update_companyname=request.POST.get('company_name',proj.Company_Name)
            update_description = request.POST.get('description', proj.Description)
            update_assignedto = request.POST.get('assigned-by', proj.Assigned_to)
            update_duedate = request.POST.get('due-date', proj.Due_Date)
            update_esthrs = request.POST.get('working-hours', proj.Est_Hour)
            update_priority=request.POST.get('priority',proj.Priority)
            update_links = request.POST.get('links', proj.Links)
            update_attachments = request.POST.get('attachments', proj.Attachments)
            update_status = request.POST.get('status', proj.Status)

            proj.Project_Name=update_projectname
            proj.Company_Name = update_companyname
            proj.Description = update_description
            proj.Assigned_By = update_assignedto
            proj.Due_Date = update_duedate
            proj.Est_Hour = update_esthrs
            proj.Priority = update_priority
            proj.Links = update_links
            proj.Attachments = update_attachments
            proj.Status = update_status

            proj.save()

            return JsonResponse({'message':'successfully updated','id':proj.id})
        except Exception as e:
            return JsonResponse({'error':f'updated field{str(e)}'})
    return JsonResponse({'error':'invalid request method'})


User = get_user_model()


@csrf_exempt
def update_projects(request, id):
    proj = get_object_or_404(Projects, id=id)

    if request.method == 'GET':
        return JsonResponse({
            "Project_Name": proj.Project_Name,
            "Company_Name": proj.Company_Name,
            "Description": proj.Description,
            "Assigned_to": [u.name for u in proj.Assigned_to.all()],
            "Due_Date": proj.Due_Date,
            "Est_Hour": proj.Est_Hour,
            "Priority": proj.Priority,
            "Links": proj.Links,
            "Attachments": proj.Attachments,
            "Status": proj.Status
        })

    elif request.method == "POST":
        try:
            proj.Project_Name = request.POST.get('project_name', proj.Project_Name)
            proj.Company_Name = request.POST.get('company_name', proj.Company_Name)
            proj.Description = request.POST.get('description', proj.Description)
            proj.Due_Date = request.POST.get('due_date', proj.Due_Date)
            proj.Est_Hour = request.POST.get('est_hr', proj.Est_Hour)
            proj.Priority = request.POST.get('priority', proj.Priority)
            proj.Links = request.POST.get('links', proj.Links)
            proj.Attachments = request.POST.get('attachments', proj.Attachments)
            proj.Status = request.POST.get('status', proj.Status)

            assigned_names = request.POST.getlist('assigned_to')
            users = User.objects.filter(name__in=assigned_names)
            proj.Assigned_to.set(users)

            proj.save()
            return JsonResponse({'message': 'successfully updated', 'id': proj.id})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'invalid request method'}, status=405)



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




@csrf_exempt
@require_http_methods(["POST"])
def Start_Task(request):
    try:
        data = json.loads(request.body)
        task_name = data.get('name')
        if not task_name:
            return JsonResponse({"error": "Task name is required"}, status=400)

        # Get or create the task
        task, created = Tasks.objects.get_or_create(Task_Name=task_name)

        # Check if there’s already a running session
        if Task_Time.objects.filter(Task=task, End_Time__isnull=True).exists():
            return JsonResponse({"error": "Task already running"}, status=400)

        # Create new session with Start_Time set automatically
        Task_Time.objects.create(Task=task, Start_Time=timezone.now())

        return JsonResponse({
            "message": f"Started task '{task.Task_Name}'",
            "task_id": task.id
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def Stop_Task(request):
    try:
        data = json.loads(request.body)
        task_name = data.get('name')
        if not task_name:
            return JsonResponse({"error": "Task name is required"}, status=400)

        # Get the task
        try:
            task = Tasks.objects.get(Task_Name=task_name)
        except Tasks.DoesNotExist:
            return JsonResponse({"error": "Task not found"}, status=404)

        # Find active session
        try:
            session = Task_Time.objects.filter(Task=task, End_Time__isnull=True).latest("Start_Time")
        except Task_Time.DoesNotExist:
            return JsonResponse({"error": "No active session found"}, status=400)

        # Stop session
        session.End_Time = timezone.now()
        session.Duration = session.End_Time - session.Start_Time
        session.save()

        # Add duration to total task time
        task.Total_Time += session.Duration
        task.save()

        return JsonResponse({
            "message": f"Stopped task '{task.Task_Name}'",
            "session_duration": str(session.Duration),
            "total_duration": str(task.Total_Time)
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def View_Employees_Productivity(request):
    try:
        users = User.objects.all().values(
            "id",
            "first_name",
            "email",
            "role"
        )

        data = []
        for u in users:
            data.append({
                "id": u["id"],
                "name": u["first_name"],
                "email": u["email"],
                "role": u["role"],

                # TEMP / derived values (until real tracking exists)
                "time": "0hr 00m",
                "efficiency": "8hr",
                "percent": 0,
            })

        return JsonResponse({
            "message": "success",
            "users": data
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)






