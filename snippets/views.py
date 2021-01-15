from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as log_in, logout as log_out
from django.contrib.auth.forms import AuthenticationForm

from snippets.models import Language, Snippet
from django.contrib.auth.models import User
from pygments import highlight
from pygments import lexers
from pygments.formatters.html import HtmlFormatter
from pygments.styles import get_style_by_name


def login(request):
    # Si ya estaba autenticado, no tiene sentido volver a hacerlo
    if request.user.is_authenticated:
        return redirect('/')
    # Formulario que ve el usuario
    form = AuthenticationForm()
    if request.method == "POST":
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
    # Si no es método POST (se ve el form por primera vez), renderizo
    return render(request, 'login.html', {'form': form})


def logout(request):
    # Si el usuario no estaba autenticado, no tiene sentido desloguearse
    if request.user.is_authenticated == False:
        return redirect('/')
    # Si estaba autenticado, hago el logout y redirecciono a la vista index
    log_out(request)
    return redirect('/')


def index(request):
    # Obtener los snippets publicos
    snippets = Snippet.objects.filter(public=True)
    return render(request, 'index.html', {'snippets': snippets})


def language(request, language):
    # Si el lenguaje no existe, salgo de esta página
    if Language.objects.filter(slug=language).exists() == False:
        return redirect('/')
    # Obtener los snippets publicos
    snippets = Snippet.objects.filter(public=True, language__slug=language)
    return render(request, 'index.html', {'snippets': snippets})


def user_snippets(request, username):
    # Si el usuario no existe, salgo de esta página:
    if User.objects.filter(username=username).exists() == False:
        return redirect('/')
    # Obtengo el usuario
    user = User.objects.filter(username=username)[0]
    # Obtengo todos los snippets públicos del usuario
    snippets = Snippet.objects.filter(user=user, public=True)
    # Si es el perfil del usuario logueado, entonces también muestro los privados
    if username == request.user.username:
        snippets |= Snippet.objects.filter(user=user, public=False)
    return render(request, 'snippets/user_snippets.html', {'snippetUsername': username, 'snippets': snippets})


def snippet(request, id):
    # Si el snippet no existe, salgo de esta página
    if Snippet.objects.filter(id=id).exists() == False:
        return redirect('/')
    # Obtengo información del snippet
    snippet = Snippet.objects.filter(id=id)[0]
    # Si el snippet es privado y no soy el usuario que lo creo, no entro
    if snippet.public == False and snippet.user.username != request.user.username:
        return redirect('/')
    # Uso pygments para formatear el codigo
    snippet.snippet = highlight(snippet.snippet, lexers.get_lexer_by_name(snippet.language.slug),
                                HtmlFormatter(style=get_style_by_name('colorful')))
    # Renderizo con los datos obtenidos
    return render(request, 'snippets/snippet.html', {'snippet': snippet})


def snippet_add(request):
    # Si el usuario no estaba autenticado, no puede crear snippets. Lo redireccionamos al login
    if request.user.is_authenticated == False:
        return redirect('/login')
    # Si está queriendo crear el snippet
    if request.method == 'POST':
        # Datos del formulario de creación del snippet
        snippet_user = User.objects.filter(username=request.user.username)[0]
        snippet_name = request.POST['name']
        snippet_description = request.POST['description']
        snippet_language = Language.objects.filter(name=request.POST['language'])[0]
        snippet_code = request.POST['code']
        snippet_public = False
        # Si el snippet va a ser público, cambio el valor del booleano
        if request.POST['public'] == 'Público':
            snippet_public = True
        # Insertar en la DB
        Snippet.objects.create(user=snippet_user, name=snippet_name, description=snippet_description,
                               snippet=snippet_code, language=snippet_language, public=snippet_public)
        # Redirecciono al index
        return redirect('/')
    # Recupero la lista de lenguajes disponibles para mostrar en lista desplegable
    lang = Language.objects.all()
    return render(request, 'snippets/snippet_add.html', {'languages': lang})


def snippet_edit(request, id):
    # Si el snippet no existe, salgo de esta página
    if Snippet.objects.filter(id=id).exists() == False:
        return redirect('/')
    # Obtengo información del snippet
    snippet = Snippet.objects.filter(id=id)[0]
    # Recupero la lista de lenguajes disponibles para mostrar en lista desplegable
    lang = Language.objects.all()
    # No puedo editar si no soy el usuario logueado
    if request.user.username != snippet.user.username:
        return redirect('/')
    # Si se están mandando los datos para editar el snippet
    if request.method == 'POST':
        # Datos del formulario de edición del snippet
        snippet_user = User.objects.filter(username=request.user.username)[0]
        snippet_name = request.POST['name']
        snippet_description = request.POST['description']
        snippet_language = Language.objects.filter(name=request.POST['language'])[0]
        snippet_code = request.POST['code']
        snippet_public = False
        # Si el snippet va a ser público, cambio el valor del booleano
        if request.POST['public'] == 'Público':
            snippet_public = True
        # Actualizar la DB
        SnippetObject = Snippet.objects.get(id=id)
        SnippetObject.name = snippet_name
        SnippetObject.description = snippet_description
        SnippetObject.snippet = snippet_code
        SnippetObject.language = snippet_language
        SnippetObject.public = snippet_public
        SnippetObject.save()
        # Redirecciono al index
        return redirect('/')
    # Si cumple las condiciones para editar, cargo los datos en el form
    return render(request, 'snippets/snippet_add.html', {'snippet': snippet, 'languages': lang})


def snippet_delete(request, id):
    # Si el snippet no existe, salgo de esta página
    if Snippet.objects.filter(id=id).exists() == False:
        return redirect('/')
    # Obtengo información del snippet
    snippet = Snippet.objects.filter(id=id)[0]
    # No puedo eliminar si no soy el usuario logueado
    if request.user.username != snippet.user.username:
        return redirect('/')
    # Eliminar snippet
    Snippet.objects.filter(id=id).delete()
    return redirect('/')
