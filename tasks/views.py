from django.shortcuts import redirect, render
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.views.generic import TemplateView, ListView, UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from .forms import createTaskForm, CustomUserCreationForm, UserUpdateForm
from .models import Task
from user.models import User

# Mostrar la página principal
class Inicio(TemplateView):
    template_name = 'index.html'

# Inicio de sesión
class SignInView(TemplateView):
    def get(self, request):
        return render(request, 'signin.html', {'form': AuthenticationForm()})

    def post(self, request):
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_superuser:
                    login(request, user)
                    return redirect('inicioAdmin')
                else:
                    login(request, user)
                    return redirect('tasks')
        return render(request, 'signin.html', {'form': form, 'error': '¡Error: Usuario o contraseña incorrectos!'})

# Cerrar sesión
class SignOutView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('index')

# Crear una nueva actividad
class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    template_name = 'create_task.html'
    form_class = createTaskForm

    def form_valid(self, form):
        new_task = form.save(commit=False)
        new_task.user = self.request.user
        new_task.save()
        return redirect('tasks')

    def form_invalid(self, form):
        return render(self.request, self.template_name, {'form': form})
    
# Mostrar las actividades pendientes de un usuario
class UserTasksListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        queryset = Task.objects.filter(
            user=self.request.user,
            datecompleted__isnull=True
        )
        return queryset

# Mostrar las actividades completadas de un usuario
class UserCompletedTasksListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(
            user=self.request.user,
            datecompleted__isnull=False
        ).order_by('-datecompleted')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
# Actualizar las actividades pendientes de un usuario
class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = createTaskForm
    template_name = 'task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, pk=self.kwargs['pk'])

    def get_success_url(self):
        return reverse_lazy('tasks')

# Marcar una actividad como completada
class TaskCompleteView(LoginRequiredMixin, UpdateView):
    model = Task
    template_name = 'tasks.html'
    fields = []  # No permitimos actualizar ningún campo en esta vista

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, datecompleted__isnull=True)

    def form_valid(self, form):
        task = form.save(commit=False)
        task.datecompleted = timezone.now()
        task.save()
        return redirect('tasks')

    def get_success_url(self):
        return reverse_lazy('tasks')
    
# Eliminar una actividad
class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'task_confirm_delete.html'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('tasks')
    
# Mostrar la página principal Admin "Tareas Registradas"
class InicioAdminListView(ListView):
    model = Task
    template_name = 'inicioAdmin.html'
    context_object_name = 'tasks'

# Registrar un nuevo usuario
def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {
            'form': CustomUserCreationForm
        })
    else:
        # Verifica si el usuario actual es Admin
        if request.user.is_superuser:
            if request.POST['password1'] == request.POST['password2']:
                # Registro de usuario
                try:
                    
                    user = User.objects.create_user(
                        username=request.POST['username'], first_name=request.POST['first_name'], last_name=request.POST['last_name'],  password=request.POST['password1'], dependencia=request.POST['dependencia'], is_superuser=request.POST.get('is_superuser') == 'on')
                    
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
      
# Mostrar usuarios registrados en el panel Admin
class UsersDetailView(ListView):
    template_name = 'usersDetail.html'
    model = User
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.all()

# Actualizar los datos del usuario panel Admin
class UserUpdateView(UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'updateUser.html'
    success_url = reverse_lazy('usersDetail')
    context_object_name = 'user'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form))
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

# Eliminar los datos de usuario
class UserDeleteView(DeleteView):
    model = User
    template_name = 'updateUser.html'
    success_url = reverse_lazy('usersDetail')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)