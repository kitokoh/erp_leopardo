from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Company

class UserAdmin(BaseUserAdmin):
    # Les champs à afficher dans la liste des utilisateurs
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'id')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    # Pour le formulaire d'édition d'un utilisateur
    # On hérite de BaseUserAdmin.fieldsets et on ajoute nos champs si besoin
    # ou on redéfinit complètement. Pour un User personnalisé, il faut souvent le faire.
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'updated_at')}), # updated_at vient de TimeStampedModel
        ('UUID', {'fields': ('id',)}), # id vient de TimeStampedModel
    )
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at', 'id') # created_at vient de TimeStampedModel

    # Si on utilise un formulaire personnalisé pour la création/modification
    # add_form = YourUserCreationForm
    # form = YourUserChangeForm

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at', 'id')
    search_fields = ('name', 'owner__username', 'owner__email')
    list_filter = ('created_at', 'owner')
    raw_id_fields = ('owner',) # Utile si beaucoup d'utilisateurs, pour éviter un long select

admin.site.register(User, UserAdmin)
