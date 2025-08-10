from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'company_account', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'company_account', 'created_at')
    search_fields = ('client_name', 'email', 'contact_person_name', 'company_account__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('company_account', 'client_name', 'is_active')
        }),
        ('Contact Principal', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Personne de Contact Secondaire', {
            'classes': ('collapse',), # Section initialement masquée
            'fields': ('contact_person_name', 'contact_person_email', 'contact_person_phone')
        }),
        ('Informations Internes', {
            'fields': ('notes',)
        }),
        ('Horodatage et ID', {
            'fields': ('id', 'created_at', 'updated_at'),
        }),
    )
    raw_id_fields = ('company_account',) # Pour une meilleure performance si beaucoup de sociétés

    def get_queryset(self, request):
        # Pour les superusers, montrer tous les clients.
        # Pour les autres (staff users), ne montrer que les clients des sociétés qu'ils possèdent.
        # Ceci est une simplification pour l'admin, la logique multi-tenant principale sera dans les vues API/Web.
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Si on veut filtrer pour les staff users non superusers:
        # return qs.filter(company_account__owner=request.user)
        # Ou si un utilisateur peut être lié à plusieurs sociétés via un autre modèle (ex: Membership)
        # user_companies = request.user.managed_companies.all() # managed_companies serait une related_name
        # return qs.filter(company_account__in=user_companies)
        return qs # Par défaut, pour l'instant, ne pas filtrer plus pour les non-superusers dans l'admin
                 # La vraie sécurité multi-tenant sera dans l'API et les vues frontend.

