from django.contrib import admin
from django.urls import path
from tasks.views import Inicio, InicioAdminListView, SignInView, SignOutView, UserTasksListView, TaskUpdateView, TaskCompleteView, TaskDeleteView, TaskCreateView, UserCompletedTasksListView, UsersDetailView, UserUpdateView, UserDeleteView, signup

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', Inicio.as_view(), name='index'),
    path('tasks/', UserTasksListView.as_view(), name='tasks'),
    path('tasks_completed/', UserCompletedTasksListView.as_view(), name='tasks_completed'),
    path('tasks/create/', TaskCreateView.as_view(), name='create_task'),
    path('tasks/<int:pk>', TaskUpdateView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/complete/', TaskCompleteView.as_view(), name='complete_task'),
    path('tasks/<int:pk>/delete/', TaskDeleteView.as_view(), name='delete_task'),

    path('signin/', SignInView.as_view(), name='signin'),
    path('logout/', SignOutView.as_view(), name='logout'),

    path('inicioAdmin/', InicioAdminListView.as_view(), name='inicioAdmin'),
    path('signup/', signup, name='signup'), 
    path('usersDetail/', UsersDetailView.as_view(), name='usersDetail'),
    path('usersDetail/<int:pk>/', UserUpdateView.as_view(), name='updateUser'),
    path('usersDetail/<int:pk>/delete/', UserDeleteView.as_view(), name='deleteUser'),
    
    ]
