from django.urls import path
from . import views

urlpatterns = [
    # Authentication & User Management
    path('signup/', views.Signup, name="SignUp"),
    path('login/', views.Login, name="Login"),
    path('user_login/', views.user_login, name='user_login'),
    path('logout/', views.logout, name="logout"),
    path('current_user/', views.current_user, name='current_user'),
    path('users/', views.Get_Users, name='Get_Users'),
    path('users/list/', views.Get_User_List, name='Get_User_List'),
    path('users/<int:id>/delete/', views.delete_user, name="delete_user"),

    # Task Management
    path('tasks/', views.View_Tasks, name='View_Tasks'),
    path('tasks/add/', views.Add_Tasks, name='Add_tasks'),
    path('tasks/<int:id>/update/', views.Update_Tasks, name='Update_Task'),
    path('tasks/<int:id>/delete/', views.Delete_Task, name='Delete_Tasks'),
    path('tasks/<int:task_id>/view/', views.View_Single_Task, name='View_Single_Task'),
    path('tasks/user/', views.View_User_Tasks, name='View_User_Tasks'),
    path('tasks/summary/', views.total_tasks_summary, name='total_tasks_summary'),
    path('tasks/admin-summary/', views.admin_tasks_summary, name='admin_tasks_summary'),
    path('tasks/total/', views.total_tasks, name="Total_Tasks"),
    path('tasks/update-status/', views.update_task_status, name='update_task_status'),

    # Project Management
    path('projects/', views.View_Projects, name='View_Projects'),
    path('projects/add/', views.Add_Projects, name='Add_projects'),
    path('projects/<int:id>/update/', views.update_projects, name='Updated_projects'),
    path('projects/<int:id>/delete/', views.Delete_Projects, name='Delete_projects'),
    path('projects/total/', views.total_projects, name="Total_Projects"),
    path('projects/total-by-user/', views.total_projects_by_user, name="total_projects_by_user"),
    path('projects/<int:project_id>/view/', views.View_Single_Project, name="view_single_project"),

    # Dashboards & Reporting
    path('dashboard/summary/', views.admin_dashboard_summary, name="admin_dashboard_summary"),
    path('dashboard/employee-status/', views.employee_status_summary, name="employee_status_summary"),
    path('reports/weekly-work/', views.weekly_work_report, name="weekly_work_report"),
    path('employees/productivity/', views.View_Employees_Productivity, name="employees_productivity"),
    path('employees/<int:user_id>/productivity/', views.View_Single_Employee_Productivity, name="single_employee_productivity"),

    # Kanban
    path('kanban/tasks/', views.kanban_tasks, name="kanban_tasks"),
    path('kanban/tasks/<int:task_id>/status/', views.update_task_status, name="update_kanban_status"),

    # Time Tracking
    path('tasks/<int:task_id>/start/', views.start_task, name='Start_Task'),
    path('tasks/<int:task_id>/stop/', views.stop_task, name='stop_task'),
    path('tasks/<int:task_id>/running/', views.get_running_task_session, name='get_running_session'),
    path('tasks/running/', views.get_active_task, name="get_active_task"),

    # Notifications
    path('notifications/', views.user_notifications, name='user_notifications'),

    # Screenshots (Standardized name)
    path('upload-screenshot/', views.upload_screenshot, name='upload_screenshot'),
]
