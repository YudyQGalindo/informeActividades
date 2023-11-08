from io import BytesIO
from xhtml2pdf import pisa
from weasyprint import HTML
from django.template.loader import get_template
from django.shortcuts import redirect, render
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.views.generic import TemplateView, ListView, UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.template.loader import render_to_string
from datetime import datetime
from .forms import createTaskForm, CustomUserCreationForm, UserUpdateForm
from .models import Task
from user.models import User
from user.mixins import superUserMixin, normalUserMixin

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
class TaskCreateView(normalUserMixin, CreateView):
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
class UserTasksListView(normalUserMixin, ListView):
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
class UserCompletedTasksListView(normalUserMixin, ListView):
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
class TaskUpdateView(normalUserMixin, UpdateView):
    model = Task
    form_class = createTaskForm
    template_name = 'task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, pk=self.kwargs['pk'])

    def get_success_url(self):
        return reverse_lazy('tasks')

# Marcar una actividad como completada
class TaskCompleteView(normalUserMixin, UpdateView):
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
class TaskDeleteView(normalUserMixin, DeleteView):
    model = Task
    template_name = 'task_confirm_delete.html'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('tasks')

# Mostrar el reporte de actvidades
class reportTasks(ListView):
    model = Task
    template_name = 'reportTasks.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.filter(user=user)

        date1 = self.request.GET.get('dateReport1')
        date2 = self.request.GET.get('dateReport2')

        if date1 and date2:
            date1 = timezone.make_aware(datetime.strptime(date1, '%Y-%m-%d'))
            date2 = timezone.make_aware(datetime.strptime(date2, '%Y-%m-%d'))
            queryset = queryset.filter(created__range=[date1, date2])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['total_activities'] = self.get_queryset().count()
        context['activities_in_progress'] = self.get_queryset().filter(datecompleted__isnull=True).count()
        context['activities_completed'] = self.get_queryset().filter(datecompleted__isnull=False).count()
        context['for_pdf'] = self.request.GET.get('for_pdf')
        return context

# Comvertir html a pdf
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)

    if not pdf.err:
        return result.getvalue()

    return None

# Generar reporte en PDF
class GeneratePDFView(TemplateView):
    template_name = 'reportTasks.html'

    def get(self, request, *args, **kwargs):
        user = self.request.user
        queryset = Task.objects.filter(user=user)

        date1 = self.request.GET.get('dateReport1')
        date2 = self.request.GET.get('dateReport2')

        if date1 and date2:
            date1 = timezone.make_aware(datetime.strptime(date1, '%Y-%m-%d'))
            date2 = timezone.make_aware(datetime.strptime(date2, '%Y-%m-%d'))
            queryset = queryset.filter(created__range=[date1, date2])

        context = {
            'tasks': queryset,
            'user': user,
            'total_activities': queryset.count(),
            'activities_in_progress': queryset.filter(datecompleted__isnull=True).count(),
            'activities_completed': queryset.filter(datecompleted__isnull=False).count(),
        }

        html = render_to_string(self.template_name, context)
        pdf = HTML(string=html).write_pdf()

        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = 'ReporteActividades.pdf'
            content = f'attachment; filename="{filename}"'
            response['Content-Disposition'] = content
            return response

        return HttpResponse('Error al generar el PDF', content_type='text/html')

# Mostrar la página principal Admin "Tareas Registradas"
class InicioAdminListView(superUserMixin, ListView):
    model = Task
    template_name = 'inicioAdmin.html'
    context_object_name = 'tasks'


# Registrar un nuevo usuario
class SignupView(superUserMixin, CreateView):
    model = User
    template_name = 'signup.html'
    form_class = CustomUserCreationForm

    def form_valid(self, form):
        new_user = form.save(commit=False)
        is_staff = form.cleaned_data.get('is_staff')
        if is_staff:
            new_user.is_superuser = True
        else:
            new_user.is_superuser = False

        new_user.save()
        
        return redirect('usersDetail')

    def form_invalid(self, form):

        return self.render_to_response(self.get_context_data(form=form, error="Ingrese datos válidos: Recuerde que el usuario debe contener solo letras, numeros y caracteres como @/./+/-/_ y la contraseña debe tener mínimo 8 caracteres."))

# Mostrar usuarios registrados en el panel Admin
class UsersDetailView(superUserMixin, ListView):
    template_name = 'usersDetail.html'
    model = User
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.all()

# Actualizar los datos del usuario panel Admin
class UserUpdateView(superUserMixin, UpdateView):
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
class UserDeleteView(superUserMixin, DeleteView):
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
