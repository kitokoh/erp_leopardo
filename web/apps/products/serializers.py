from rest_framework import serializers
from .models import ProductCategory, Product
from apps.users.models import Company # Pour la validation de company_account

class ProductCategorySerializer(serializers.ModelSerializer):
    # company_account_name = serializers.CharField(source='company_account.name', read_only=True)

    class Meta:
        model = ProductCategory
        fields = [
            'id',
            'company_account', # Requis pour l'assignation multi-tenant
            # 'company_account_name',
            'name',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at') # company_account_name si présent
        extra_kwargs = {
            'company_account': {'write_only': True, 'required': False},
            # write_only car on ne le renvoie pas directement (ou on pourrait avoir un champ id + nom séparé)
            # required=False car setté dans perform_create du ViewSet.
            'description': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

    def validate_name(self, value):
        # Valider l'unicité du nom de catégorie par société
        request = self.context.get('request')
        # La company_account sera soit dans les données initiales (si fournie par le client API),
        # soit sera celle assignée par le ViewSet (perform_create) avant la validation complète du serializer.
        # Pour être sûr, on récupère la company_account qui SERA utilisée.

        company_account = None
        if self.instance: # Mise à jour
            company_account = self.instance.company_account
        elif 'company_account' in self.initial_data: # Création avec company_account fournie (même si on la force dans la vue)
            try:
                company_pk = self.initial_data.get('company_account')
                if isinstance(company_pk, Company): # Si l'objet est déjà passé (rare pour input direct)
                    company_account = company_pk
                else: # C'est un PK
                    company_account = Company.objects.get(pk=company_pk)
            except Company.DoesNotExist: # Géré par la validation du champ company_account lui-même
                pass

        # Si toujours pas de company_account, et qu'on est en création, on ne peut pas valider l'unicité ici
        # car elle dépend de la company qui sera assignée dans perform_create.
        # Le modèle avec unique_together s'en chargera à la sauvegarde BD.
        # Si on veut une validation plus tôt, il faut que company_account soit requis et validé avant ce point.
        # Pour l'instant, on se fie à la contrainte de base de données unique_together.
        # Si la company_account est connue (ex: self.instance existe):
        if company_account and value:
            query = ProductCategory.objects.filter(company_account=company_account, name__iexact=value)
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError(f"Une catégorie nommée '{value}' existe déjà pour cette société.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    # company_account_name = serializers.CharField(source='company_account.name', read_only=True)

    # Permettre de passer l'ID de la catégorie lors de la création/mise à jour
    # Le queryset sera filtré dans le ViewSet pour ne montrer que les catégories de la bonne société
    category = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'company_account', # Requis pour multi-tenant
            # 'company_account_name',
            'name',
            'reference',
            'category', # En tant que PK pour écriture
            'category_name', # En tant que nom pour lecture
            'description',
            'unit_price_ht',
            'product_type',
            'unit_of_measure',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'category_name') # company_account_name si présent
        extra_kwargs = {
            'company_account': {'write_only': True, 'required': False},
            'reference': {'required': False, 'allow_null': True, 'allow_blank': True},
            'description': {'required': False, 'allow_null': True, 'allow_blank': True},
            'unit_of_measure': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

    def validate_category(self, value):
        # S'assurer que la catégorie sélectionnée appartient à la même company_account que le produit
        # La company_account du produit sera définie dans perform_create/perform_update du ViewSet.
        # Cette validation est donc un peu délicate ici sans connaître la future company_account du produit.
        # Il est plus robuste de la faire dans la méthode validate() globale ou dans le ViewSet.
        # Pour l'instant, on assume que le queryset du champ 'category' est déjà filtré correctement par le ViewSet.
        if value is None: # La catégorie est optionnelle
            return value

        # Récupérer la company_account (logique similaire à validate_name de ProductCategorySerializer)
        # Cette logique est complexe ici. Le plus simple est de s'assurer que le ViewSet
        # fournit un queryset filtré pour le champ 'category' dans le serializer.
        # Par exemple, dans le ViewSet:
        # def get_serializer_context(self):
        #     context = super().get_serializer_context()
        #     # Déterminer company_account
        #     # context['product_category_queryset'] = ProductCategory.objects.filter(company_account=determined_company)
        #     return context
        # Et dans le serializer:
        # category = serializers.PrimaryKeyRelatedField(queryset=None, allow_null=True, required=False)
        # def __init__(self, *args, **kwargs):
        #     super().__init__(*args, **kwargs)
        #     if 'product_category_queryset' in self.context:
        #         self.fields['category'].queryset = self.context['product_category_queryset']
        #
        # Si on a l'instance du produit (mise à jour) ou la future company_account (création)
        # on peut valider que value.company_account est la même.
        # company_of_product = self.instance.company_account if self.instance else self.context.get('company_account_for_product')
        # if company_of_product and value.company_account != company_of_product:
        #     raise serializers.ValidationError("La catégorie sélectionnée n'appartient pas à la même société que le produit.")
        return value

    def validate_reference(self, value):
        # Nettoyer la référence: si vide ou que des espaces, la mettre à None
        if value is not None and not value.strip():
            return None
        # La validation d'unicité (company_account, reference) se fera au niveau du modèle/DB.
        # On pourrait la dupliquer ici si on connaît company_account (voir validate_name de ProductCategory).
        return value

    # def validate(self, data):
    #     # Validation croisée, par exemple pour reference unique par company_account
    #     # (similaire à ce qui est commenté dans ClientSerializer)
    #     # company_account = data.get('company_account') or getattr(self.instance, 'company_account', None)
    #     # ... logique de vérification d'unicité ...
    #     return data
