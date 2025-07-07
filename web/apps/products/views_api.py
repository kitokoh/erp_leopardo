from rest_framework import viewsets, permissions, serializers # Ajout de serializers pour ValidationError
from .models import ProductCategory, Product
from .serializers import ProductCategorySerializer, ProductSerializer
from apps.users.models import Company # Pour récupérer la société de l'utilisateur
from apps.users.permissions import CanManageObjectBasedOnCompany # Permission multi-tenant

class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les catégories de produits.
    Filtré par la société de l'utilisateur.
    """
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated, CanManageObjectBasedOnCompany]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser: # Optionnel: les superusers voient tout
            return ProductCategory.objects.all().select_related('company_account')

        # Récupérer les sociétés possédées par l'utilisateur
        user_companies = Company.objects.filter(owner=user)
        if not user_companies.exists():
            return ProductCategory.objects.none()

        # Filtrer par les sociétés de l'utilisateur
        return ProductCategory.objects.filter(company_account__in=user_companies).select_related('company_account')

    def perform_create(self, serializer):
        user = self.request.user
        # Essayer de déterminer la company_account
        # Soit elle est fournie dans la requête (et validée par la permission ou ici)
        # Soit on prend la première société de l'utilisateur
        company_id_from_request = self.request.data.get('company_account')
        target_company = None

        if company_id_from_request:
            if isinstance(company_id_from_request, dict):
                 company_id_from_request = company_id_from_request.get('id')
            try:
                target_company = Company.objects.get(pk=company_id_from_request, owner=user)
            except Company.DoesNotExist:
                raise serializers.ValidationError({
                    "company_account": "La société spécifiée n'existe pas ou vous n'en êtes pas le propriétaire."
                })
        else:
            target_company = user.owned_companies.order_by('created_at').first()

        if not target_company:
            raise serializers.ValidationError({
                "company_account": "Aucune société n'est associée à votre compte pour créer cette catégorie."
            })

        # La validation d'unicité (company_account, name) est gérée par le serializer/modèle.
        serializer.save(company_account=target_company)

    def perform_update(self, serializer):
        # La permission CanManageObjectBasedOnCompany vérifie déjà l'objet.
        # Si company_account est dans les données de la requête et différent,
        # la permission devrait empêcher la modification si la nouvelle société n'appartient pas à l'user.
        # Ici, on s'assure juste de sauvegarder.
        serializer.save()


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les produits et services.
    Filtré par la société de l'utilisateur.
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageObjectBasedOnCompany]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Product.objects.all().select_related('company_account', 'category')

        user_companies = Company.objects.filter(owner=user)
        if not user_companies.exists():
            return Product.objects.none()

        return Product.objects.filter(company_account__in=user_companies).select_related('company_account', 'category')

    def get_serializer_context(self):
        # Fournir un queryset filtré pour le champ 'category' dans ProductSerializer
        context = super().get_serializer_context()
        user = self.request.user

        # Déterminer la company_account pour le produit en cours de création/modification
        # Pour la création (POST), company_account n'est pas encore sur l'instance.
        # Pour la modification (PUT/PATCH), company_account est sur self.get_object().
        # On doit fournir les catégories de la *bonne* société.

        target_company_for_product = None
        if self.action == 'create':
            company_id_from_request = self.request.data.get('company_account')
            if company_id_from_request: # Si fourni dans la requête
                if isinstance(company_id_from_request, dict):
                    company_id_from_request = company_id_from_request.get('id')
                try:
                    # Vérifier que l'utilisateur a le droit sur cette company
                    target_company_for_product = Company.objects.get(pk=company_id_from_request, owner=user)
                except Company.DoesNotExist:
                    pass # Sera géré dans perform_create ou validation serializer
            if not target_company_for_product: # Si non fourni ou invalide, prendre la première de l'user
                target_company_for_product = user.owned_companies.order_by('created_at').first()

        elif self.action in ['update', 'partial_update', 'retrieve'] and hasattr(self, 'object') and self.object:
            target_company_for_product = self.object.company_account
        elif self.action in ['update', 'partial_update', 'retrieve'] and 'pk' in self.kwargs : # Pour retrieve avant get_object
             try:
                product_instance = Product.objects.get(pk=self.kwargs['pk'])
                # Vérifier les droits avant de continuer
                if product_instance.company_account.owner == user or user.is_superuser:
                    target_company_for_product = product_instance.company_account
             except Product.DoesNotExist:
                pass


        if target_company_for_product:
            context['product_category_queryset'] = ProductCategory.objects.filter(company_account=target_company_for_product)
        else:
            # Si aucune société ne peut être déterminée (ex: user sans société essayant de créer),
            # fournir un queryset vide pour les catégories.
            context['product_category_queryset'] = ProductCategory.objects.none()

        context['request'] = self.request # S'assurer que request est dans le contexte pour les validateurs de serializer
        return context

    def perform_create(self, serializer):
        user = self.request.user
        company_id_from_request = self.request.data.get('company_account')
        target_company = None

        if company_id_from_request:
            if isinstance(company_id_from_request, dict):
                 company_id_from_request = company_id_from_request.get('id')
            try:
                target_company = Company.objects.get(pk=company_id_from_request, owner=user)
            except Company.DoesNotExist:
                raise serializers.ValidationError({
                    "company_account": "La société spécifiée n'existe pas ou vous n'en êtes pas le propriétaire."
                })
        else:
            target_company = user.owned_companies.order_by('created_at').first()

        if not target_company:
            raise serializers.ValidationError({
                "company_account": "Aucune société n'est associée à votre compte pour créer ce produit."
            })

        # Valider la catégorie sélectionnée (si fournie)
        category_instance = serializer.validated_data.get('category')
        if category_instance and category_instance.company_account != target_company:
            raise serializers.ValidationError({
                "category": f"La catégorie '{category_instance.name}' n'appartient pas à la société '{target_company.name}'."
            })

        # La validation d'unicité de référence (company_account, reference) est gérée par le modèle.
        serializer.save(company_account=target_company)

    def perform_update(self, serializer):
        # La permission a déjà vérifié l'objet.
        # Valider la catégorie si elle est modifiée
        category_instance = serializer.validated_data.get('category')
        # La company_account de l'instance ne change pas ici (ou si elle change, une logique similaire à perform_create serait nécessaire)
        target_company = serializer.instance.company_account

        if category_instance and category_instance.company_account != target_company:
            raise serializers.ValidationError({
                "category": f"La catégorie '{category_instance.name}' n'appartient pas à la société '{target_company.name}'."
            })
        serializer.save()
