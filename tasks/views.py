from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseForbidden
from .forms import createTaskForm, CustomUserCreationForm, UserUpdateForm
from .models import Task
from user.models import User
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import View

# Mostrar la página principal
class Inicio(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'index.html')

# Mostrar la página principal Admin
@login_required
def inicioAdmin(request):
    queryset = request.GET.get("buscar")
    tasks = Task.objects.filter().order_by('-created')

    if queryset:
        tasks = tasks.filter(
            Q(user__username__icontains=queryset) |
            Q(user__dependencia__icontains=queryset) |
            Q(title__icontains=queryset) |
            Q(description__icontains=queryset)
        ).distinct()

    paginator = Paginator(tasks, 3)
    pagina = request.GET.get('page')
    
    try:
        tasks = paginator.get_page(pagina)
    except PageNotAnInteger:
        tasks = paginator.get_page(1)
    except EmptyPage:
        tasks = paginator.get_page(paginator.num_pages)
    
    pagina_actual = int(pagina) if pagina else 1
    paginas = range(1, tasks.paginator.num_pages + 1)

    return render(request, 'inicioAdmin.html', {'tasks': tasks, 'paginas': paginas, 'pagina_actual': pagina_actual})

# Mostrar las actividades pendientes de un usuario
@login_required
def tasks(request):
    tasks = Task.objects.filter(user=request.user, datecompleted__isnull=True)
    paginator = Paginator(tasks, 3)
    pagina = request.GET.get('page') or 1
    tasks = paginator.get_page(pagina)
    pagina_actual = int(pagina)
    paginas = range(1, tasks.paginator.num_pages + 1)
    return render(request, 'tasks.html', {'tasks': tasks, 'paginas': paginas, 'pagina_actual': pagina_actual})

# Mostrar las actividades completadas de un usuario
@login_required
def tasks_completed(request):
    tasks = Task.objects.filter(
        user=request.user, datecompleted__isnull=False).order_by('-datecompleted')
    paginator = Paginator(tasks, 3)
    pagina = request.GET.get('page') or 1
    tasks = paginator.get_page(pagina)
    pagina_actual = int(pagina)
    paginas = range(1, tasks.paginator.num_pages + 1)
    return render(request, 'tasks.html', {'tasks': tasks, 'paginas': paginas, 'pagina_actual': pagina_actual})

# Crear una nueva actividad
@login_required
def create_task(request):
    if request.method == 'GET':
        return render(request, 'create_task.html', {
            'form': createTaskForm
        })
    else:
        try:
            form = createTaskForm(request.POST)
            new_task = form.save(commit=False)
            new_task.user = request.user
            new_task.save()
            return redirect('tasks')
        except ValueError:
            return render(request, 'create_task.html', {
                'form': createTaskForm,
                'error': '¡Error: por favor ingrese datos válidos!'
            })

# Actualizar las actividades pendientes de un usuario
@login_required
def task_detail(request, task_id):
    if request.method == 'GET':
        task = get_object_or_404(Task, pk=task_id, user=request.user)
        form = createTaskForm(instance=task)
        return render(request, 'task_detail.html', {
            'task': task, 'form': form
        })
    else:
        try:
            task = get_object_or_404(Task, pk=task_id, user=request.user)
            form = createTaskForm(request.POST, instance=task)
            form.save()
            return redirect('tasks')
        except ValueError:
            return render(request, 'task_detail.html', {
                'task': task, 'form': form,
                'error': "Error: al actualizar los datos, intente de nuevo."
            })

# Marcar una actividad como completada
@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST':
        task.datecompleted = timezone.now()
        task.save()
        return redirect('tasks')

# Eliminar una actividad
@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        return redirect('tasks')

# Inicio de sesión
def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': AuthenticationForm
        })
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            if user.username == 'Admin':
                # El usuario es un administrador, redirigir a la vista de registro de usuarios
                login(request, user)
                return redirect('inicioAdmin')
            else:
                # El usuario no es un administrador, redirigir a la vista de tareas pendientes
                login(request, user)
                return redirect('tasks')
        else:
            # Los datos ingresados están erróneos
            return render(request, 'signin.html', {
                'form': AuthenticationForm(),
                'error': '¡Error: Usuario o contraseña incorrectos!'
            })

# Cerrar sesión
@login_required
def signout(request):
    logout(request)
    return redirect('index')

# Registrar un nuevo usuario
@login_required
def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {
            'form': CustomUserCreationForm
        })
    else:
        # Verifica si el usuario actual es Admin
        if request.user.username == 'Admin':
            if request.POST['password1'] == request.POST['password2']:
                # Registro de usuario
                try:
                    user = User.objects.create_user(
                        username=request.POST['username'], first_name=request.POST['first_name'], last_name=request.POST['last_name'],  password=request.POST['password1'], dependencia=request.POST['dependencia'])
                    user.save()
                    return redirect('usersDetail')
                except:
                    return render(request, 'signup.html', {
                        'form': CustomUserCreationForm,
                        "error": 'Ingrese datos válidos.'
                    })
            return render(request, 'signup.html', {
                'form': CustomUserCreationForm,
                "error": 'La contraseña no coincide'
            })
        else:
            # Si el usuario no es Admin, mostrar una página de acceso denegado
            return HttpResponseForbidden("Acceso denegado")

# Mostrar usuarios registrados panel Admin
@login_required
def usersDetail(request):
    users = User.objects.all()
    paginator = Paginator(users, 3)
    pagina = request.GET.get('page') or 1
    users = paginator.get_page(pagina)
    pagina_actual = int(pagina)
    paginas = range(1, users.paginator.num_pages + 1)
    return render(request, 'usersDetail.html', {'users': users, 'paginas': paginas, 'pagina_actual': pagina_actual})

# Actualizar los datos del usuario panel Admin
@login_required
def updateUser(request, user_id):
    if request.method == 'GET':
        user = get_object_or_404(User, pk=user_id)
        form = UserUpdateForm(instance=user)
        return render(request, 'updateUser.html', {
            'user': user, 'form': form
        })
    else:
        try:
            user = get_object_or_404(User, pk=user_id)
            form = UserUpdateForm(request.POST, instance=user)
            form.save()
            return redirect('usersDetail')
        except ValueError:
            return render(request, 'updateUser.html', {
                'user': user, 'form': form,
                'error': "Error: al actualizar los datos, intente de nuevo."
            })

# Eliminar los datos de usuario
@login_required
def deleteUser(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('usersDetail')
