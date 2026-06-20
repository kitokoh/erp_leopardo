from django.contrib import admin
from .models import ProductCategory, Product

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_account', 'description', 'created_at')
    list_filter = ('company_account', 'created_at')
    search_fields = ('name', 'description', 'company_account__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('company_account', 'name', 'description')
        }),
        ('Horodatage et ID', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',) # Masquer par défaut
        }),
    )
    raw_id_fields = ('company_account',)

    def get_queryset(self, request):
        # Filtrage pour multi-tenant dans l'admin (simplifié)
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Pour les autres staff users, ne montrer que les catégories de leurs sociétés
        # return qs.filter(company_account__owner=request.user)
        # Ou si un utilisateur peut être lié à plusieurs sociétés (ex: via Membership)
        # user_companies = request.user.managed_companies.all() # managed_companies serait une related_name
        # return qs.filter(company_account__in=user_companies)
        return qs # Pour l'instant, pas de filtrage admin supplémentaire pour non-superuser


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'reference',
        'category',
        'company_account',
        'unit_price_ht',
        'product_type',
        'is_active',
        'created_at'
    )
    list_filter = ('is_active', 'product_type', 'company_account', 'category', 'created_at')
    search_fields = ('name', 'reference', 'description', 'category__name', 'company_account__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('company_account', 'name', 'reference', 'category', 'is_active')
        }),
        ('Détails du Produit/Service', {
            'fields': ('description', 'unit_price_ht', 'product_type', 'unit_of_measure')
        }),
        ('Horodatage et ID', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    raw_id_fields = ('company_account', 'category')
    list_select_related = ('category', 'company_account') # Optimisation pour l'affichage en liste

    def get_queryset(self, request):
        # Filtrage pour multi-tenant dans l'admin (simplifié)
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.select_related('category', 'company_account')
        # return qs.filter(company_account__owner=request.user).select_related('category', 'company_account')
        return qs.select_related('category', 'company_account') # Pour l'instant, pas de filtrage admin supplémentaire
