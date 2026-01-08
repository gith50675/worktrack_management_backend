

from django.urls import path
from .import views


urlpatterns = [
    path('signup/',views.Signup,name="SignUp"),
    path('login/',views.Login,name="Login"),
    path('logout', views.logout, name="logout"),
    path('current_user/', views.current_user, name='current_user'),
    path('users/list/',views.Get_User_List, name='Get_User_List'),
    path('add_tasks',views.Add_Tasks,name='Add_tasks'),
    path('update_tasks/<int:id>',views.Update_Tasks,name='Update_Task'),
    path('delete_tasks/<int:id>/',views.Delete_Task,name='Delete_Tasks'),
    path('view_tasks',views.View_Tasks,name='View_Tasks'),

    path("users", views.Get_Users),




    #projects

    path('add_projects',views.Add_Projects,name='Add_projects'),
    path('view_projects/',views.View_Projects,name='View_Projects'),
    path('update_projects/<int:id>/',views.update_projects,name='Updated_projects'),
    path('delete_projects/<int:id>/',views.Delete_Projects,name='Delete_projects'),
    path("total_projects",views.total_projects,name="Total_Projects"),
    path("total_projects_by_users", views.total_projects_by_user, name="Total_Projects_by_users"),
    path("view-project/<int:project_id>/", views.View_Single_Project, name="view_single_project"),

    path('update-task-status/', views.update_task_status, name='update_task_status'),
    path('start_task',views.Start_Task,name='Start_Task'),
    path('stop_task', views.Stop_Task, name='stop_task'),
    path('task_summary',views.Task_Summary,name="Task_summary"),
    path('total_task',views.total_tasks,name="Total_Tasks"),
    path('total_tasks_by_users', views.total_tasks_by_users, name="Total_Tasks_By_Users"),
    path("single_view_task/<int:task_id>", views.View_Single_Task),
path("employee_productivity/<int:user_id>/", views.View_Single_Employee_Productivity),


    #productivity
    path("employees_productivity/", views.View_Employees_Productivity, name="employees_productivity"),



]