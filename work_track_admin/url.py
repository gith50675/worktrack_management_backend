from django.urls import path
from .import views
urlpatterns = [
    path('signup',views.Signup,name="SignUp"),
    path('login',views.Login,name="Login"),
    path('add_tasks',views.Add_Tasks,name='Add_tasks'),
    path('update_tasks/<int:id>',views.Update_Tasks,name='Update_Task'),
    path('delete_tasks/<int:id>',views.Delete_Task,name='Delete_Tasks'),
    path('view_tasks',views.View_Tasks,name='View_Tasks'),
    #projects
    path('add_projects',views.Add_Projects,name='Add_projects'),
    path('view_projects',views.View_Projects,name='View_Projects'),
    path('update_projects/<int:id>',views.update_projects,name='Updated_projects'),
    path('delete_projects/<int:id>',views.Delete_Projects,name='Delete_projects'),

    path('update-task-status/', views.update_task_status, name='update_task_status'),
    path('start_task',views.Start_Task,name='Start_Task'),
    path('stop_task', views.Stop_Task, name='stop_task'),
    path('task_summary',views.Task_Summary,name="Task_summary"),
]
