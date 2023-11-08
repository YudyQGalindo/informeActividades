from django.shortcuts import redirect

# Validar inicio de sesión y verificación de Superusuario
class superUserMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return super().dispatch(request, *args, **kwargs)
            else:
                return redirect('tasks')
        return redirect('signin')

# Validar inicio de sesión y verificación de usuario común
class normalUserMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser == False:
                return super().dispatch(request, *args, **kwargs)
            else:
                return redirect('inicioAdmin')
        return redirect('signin')
    