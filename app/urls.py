from django.contrib import admin
from django.urls import path
from tasks import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('inicioAdmin/', views.inicioAdmin, name='inicioAdmin'),
    path('usersDetail/', views.usersDetail, name='usersDetail'),
    path('usersDetail/<user_id>/', views.updateUser, name='updateUser'),
    path('usersDetail/<int:user_id>/delete/', views.deleteUser, name='deleteUser'),
    path('signup/', views.signup, name='signup'),
    path('tasks/', views.tasks, name='tasks'),
    path('tasks_completed/', views.tasks_completed, name='tasks_completed'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('logout/', views.signout, name='logout'),
    path('signin/', views.signin, name='signin')
    ]

