from celery import shared_task
from django.core.mail import send_mail
from django_snippets.settings import EMAIL_HOST_USER as sender

#Enviar un mail al correo de la persona para avisar que se creó un snippet.
#Se envía nombre y descripción del snippet al mail registrado del usuario.
@shared_task
def sendEmailInSnippetCreation(snippet_name, snippet_description, user_mail):
    subject='Snippet "'+snippet_name+'" creado con éxito'
    body='Se ha creado con éxito el snippet "'+snippet_name+'" con la siguiente descripción: \n'+snippet_description
    #Si y solo si el usuario registró un correo, enviamos el mail
    if user_mail:
        send_mail(subject, body, sender, [user_mail])