from django.contrib import admin

from .models import Language


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)


from .models import Snippet
@admin.register(Snippet)
class SnippetAdmin(admin.ModelAdmin):
    list_display = ('user', 'created', 'updated', 'name', 'description', 'snippet', 'language', 'public')
