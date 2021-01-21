from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as log_in, logout as log_out
from django.contrib.auth.forms import AuthenticationForm
from snippets.models import Snippet
from django.contrib.auth.models import User
from pygments import highlight
from pygments import lexers
from pygments.formatters.html import HtmlFormatter
from pygments.styles import get_style_by_name
from .tasks import sendEmailInSnippetCreation
from .forms import SnippetForm
from django.views import View

class SnippetAdd(View):
    # Si se quiere renderizar el formulario
    def get(self, request, *args, **kwargs):
        # Si el usuario no estaba autenticado, no puede crear snippets. Lo redireccionamos al login
        if request.user.is_authenticated == False:
            return redirect('/login')
        # Formulario de creación de snippet
        form = SnippetForm()
        return render(request, 'snippets/snippet_add.html', {'form': form, 'action': 'Crear'})

    # Si está queriendo crear el snippet
    def post(self, request, *args, **kwargs):
        # Si el usuario no estaba autenticado, no puede crear snippets. Lo redireccionamos al login
        if request.user.is_authenticated == False:
            return redirect('/login')
        # Usuario que va a crear el snippet
        snippet_user = User.objects.get(username=request.user.username)
        # Datos del formulario de creación del snippet
        form = SnippetForm(request.POST, instance=Snippet(user=snippet_user))
        # Si el formulario es válido
        if form.is_valid():
            # Nombre y descripción del snippet para enviar el mail
            snippet_name = form.cleaned_data['name']
            snippet_description = form.cleaned_data['description']
            # Creamos el snippet
            form.save()
            # Enviar mail al usuario avisando que se creó un snippet
            # Se usa celery para hacer el proceso de envío de mail de forma asincrónica
            sendEmailInSnippetCreation.delay(snippet_name, snippet_description, snippet_user.email)
        # Redirecciono al index
        return redirect('/')


class SnippetEdit(View):
    # Si se quiere renderizar el formulario para editar el snippet
    def get(self, request, *args, **kwargs):
        # ID del snippet que se quiere editar
        snippet_id = self.kwargs['id']
        try:
            # Snippet a editar
            snippet = Snippet.objects.get(id=snippet_id)
        except:
            # Si el snippet no existe, salgo de esta página
            return redirect('/')
        # No puedo editar si no soy el usuario logueado
        if request.user.username != snippet.user.username:
            return redirect('/')
        # Creo el form con los datos que estaban guardados
        form = SnippetForm(instance=snippet)
        # Si cumple las condiciones para editar, cargo los datos en el form
        return render(request, 'snippets/snippet_add.html', {'form': form, 'action': 'Editar'})

    # Si se están mandando los datos para editar el snippet
    def post(self, request, *args, **kwargs):
        # ID del snippet que se quiere editar
        snippet_id = self.kwargs['id']
        try:
            # Snippet a editar
            snippet = Snippet.objects.get(id=snippet_id)
        except:
            # Si el snippet no existe, salgo de esta página
            return redirect('/')
        # Datos del formulario de edición del snippet
        form = SnippetForm(request.POST, instance=snippet)
        # Si el formulario es válido, actualizo la DB
        if form.is_valid():
            form.save()
        # Redirecciono al index
        return redirect('/')


class SnippetDelete(View):
    # Si se quiere borrar el snippet
    def get(self, request, *args, **kwargs):
        # ID del snippet que se quiere eliminar
        snippet_id = self.kwargs['id']
        try:
            # Snippet a eliminar
            snippet = Snippet.objects.get(id=snippet_id)
        except:
            # Si el snippet no existe, salgo de esta página
            return redirect('/')
        # No puedo eliminar si no soy el usuario logueado
        if request.user.username != snippet.user.username:
            return redirect('/')
        # Eliminar snippet
        snippet.delete()
        return redirect('/')


class SnippetDetails(View):
    # Si se quiere ver el snippet
    def get(self, request, *args, **kwargs):
        # ID del snippet que se quiere visualizar
        snippet_id = self.kwargs['id']
        try:
            # Snippet a visualizar
            snippet = Snippet.objects.get(id=snippet_id)
        except:
            # Si el snippet no existe, salgo de esta página
            return redirect('/')
        # Si el snippet es privado y no soy el usuario que lo creo, no entro
        if snippet.public == False and snippet.user.username != request.user.username:
            return redirect('/')
        # Uso pygments para formatear el codigo
        snippet.snippet = highlight(snippet.snippet, lexers.get_lexer_by_name(snippet.language.slug),
                                    HtmlFormatter(style=get_style_by_name('colorful')))
        # Renderizo con los datos obtenidos
        return render(request, 'snippets/snippet.html', {'snippet': snippet})


class UserSnippets(View):
    # Ver snippets de un determinado usuario
    def get(self, request, *args, **kwargs):
        # Username del perfil que se quiere visualizar
        username = self.kwargs['username']
        try:
            # Usuario a visualizar
            user = User.objects.get(username=username)
        except:
            # Si el usuario no existe, salgo de esta página
            return redirect('/')
        # Si es el perfil del usuario logueado, muestro todos los snippets
        if username == request.user.username:
            snippets = Snippet.objects.filter(user=user)
        # Si no es el usuario, solo muestro los públicos
        else:
            snippets = Snippet.objects.filter(user=user, public=True)
        return render(request, 'snippets/user_snippets.html', {'snippetUsername': username, 'snippets': snippets})


class SnippetsByLanguage(View):
    # Ver snippets de un determinado lenguaje
    def get(self, request, *args, **kwargs):
        # Lenguaje de snippets a visualizar
        language = self.kwargs['language']
        # Obtener los snippets públicos que se correspondan con el lenguaje
        snippets = Snippet.objects.filter(public=True, language__slug=language)
        return render(request, 'index.html', {'snippets': snippets})


class Login(View):
    # Renderizar formulario de login
    def get(self, request, *args, **kwargs):
        # Si ya estaba autenticado, no tiene sentido volver a hacerlo
        if request.user.is_authenticated:
            return redirect('/')
        # Formulario que ve el usuario
        form = AuthenticationForm()
        # Renderizo
        return render(request, 'login.html', {'form': form})

    # Si el usuario está intentando loguearse
    def post(self, request, *args, **kwargs):
        # Si ya estaba autenticado, no tiene sentido volver a hacerlo
        if request.user.is_authenticated:
            return redirect('/')
        # Datos ingresados en el formulario
        form = AuthenticationForm(data=request.POST)
        # Chequeo que los datos ingresados sean validos
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Si los datos están bien, hago el login y redirecciono a la vista del index
                log_in(request, user)
                return redirect('/')
        # Renderizo
        return render(request, 'login.html', {'form': form})

class Logout(View):
    #Hacer el logout
    def get(self, request, *args, **kwargs):
        # Si el usuario no estaba autenticado, no tiene sentido desloguearse
        if request.user.is_authenticated == False:
            return redirect('/')
        # Si estaba autenticado, hago el logout y redirecciono a la vista index
        log_out(request)
        return redirect('/')

class Index(View):
    # Vista index
    def get(self, request, *args, **kwargs):
        # Obtener los snippets publicos
        snippets = Snippet.objects.filter(public=True)
        return render(request, 'index.html', {'snippets': snippets})
