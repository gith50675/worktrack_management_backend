

from django.urls import path
from .import views


urlpatterns = [
    path('signup/',views.Signup,name="SignUp"),
    path('login/',views.Login,name="Login"),
    path('user_login', views.user_login, name='user_login'),
    path('logout', views.logout, name="logout"),
    path('current_user/', views.current_user, name='current_user'),
    path('users/list/',views.Get_User_List, name='Get_User_List'),
    path('add_tasks/',views.Add_Tasks,name='Add_tasks'),
    path('update_tasks/<int:id>',views.Update_Tasks,name='Update_Task'),
    path('delete_tasks/<int:id>/',views.Delete_Task,name='Delete_Tasks'),
    path('view_tasks',views.View_Tasks,name='View_Tasks'),
    path('user_task/', views.View_User_Tasks, name='View_User_Tasks'),
    path('total_projects_by_users', views.total_projects_by_user, name="total_projects_by_user"),
    path('task_summary', views.total_tasks_summary, name="task_summary"),
    path("dashboard/summary/", views.admin_dashboard_summary),
    path("users", views.Get_Users),

    #projects

    path('add_projects/',views.Add_Projects,name='Add_projects'),
    path('view_projects/',views.View_Projects,name='View_Projects'),
    path('update_projects/<int:id>/',views.update_projects,name='Updated_projects'),
    path('delete_projects/<int:id>/',views.Delete_Projects,name='Delete_projects'),
    path("total_projects",views.total_projects,name="Total_Projects"),
    # path("total_projects_by_users", views.total_projects_by_user, name="Total_Projects_by_users"),
    path("view-project/<int:project_id>/", views.View_Single_Project, name="view_single_project"),

    path('update-task-status/', views.update_task_status, name='update_task_status'),
    path('task_summary',views.Task_Summary,name="Task_summary"),
    path('total_task',views.total_tasks,name="Total_Tasks"),
    # path('total_tasks_by_users', views.total_tasks_by_users, name="Total_Tasks_By_Users"),
    path("single_view_task/<int:task_id>", views.View_Single_Task),
    path("employee_productivity/<int:user_id>/", views.View_Single_Employee_Productivity),
    path('notifications/', views.user_notifications, name= 'user_notifications'),
    path("dashboard/employee-status/",views.employee_status_summary),


    #productivity
    path("employees_productivity/", views.View_Employees_Productivity, name="employees_productivity"),

    #kanban
    path("kanban/tasks/<int:task_id>/status/", views.Update_Task_Status),
    path("kanban/tasks/", views.kanban_tasks),

#     time tracking
    path('tasks/<int:task_id>/start/',views.start_task,name='Start_Task'),
    path('tasks/<int:task_id>/stop/', views.stop_task, name='stop_task'),
    path("tasks/<int:task_id>/running/",views.get_running_task_session),
path("tasks/running/", views.get_active_task, name="get_active_task"),


]