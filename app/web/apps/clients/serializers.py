from rest_framework import serializers
from .models import Client
from apps.users.models import Company # Pour valider/lier company_account

class ClientSerializer(serializers.ModelSerializer):
    company_account_name = serializers.CharField(source='company_account.name', read_only=True)
    # Si on veut permettre de passer l'ID de company_account lors de la création/mise à jour
    # company_account = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=True)
    # Ou laisser DRF gérer la relation via le champ du modèle, mais s'assurer qu'il est bien géré dans perform_create/perform_update du ViewSet.

    class Meta:
        model = Client
        fields = [
            'id',
            'company_account', # Important pour l'assignation et le filtrage multi-tenant
            'company_account_name',
            'client_name',
            'email',
            'phone',
            'address',
            'contact_person_name',
            'contact_person_email',
            'contact_person_phone',
            'notes',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'company_account_name')
        extra_kwargs = {
            'company_account': {'write_only': True, 'required': False}
            # write_only=True car on ne veut pas le renvoyer en détail (on a company_account_name)
            # required=False car il sera setté dans perform_create du ViewSet
        }

    def validate_company_account(self, value):
        # Cette validation est optionnelle ici si on gère l'assignation
        # et la permission d'accès à la Company dans le ViewSet.
        # Mais peut être utile si l'ID est passé explicitement.
        user = self.context['request'].user
        # Vérifier que l'utilisateur est propriétaire de la société fournie
        # (ou a les droits sur cette société selon la logique métier)
        if not user.owned_companies.filter(pk=value.pk).exists():
            # Alternative: if not Company.objects.filter(pk=value.pk, owner=user).exists():
            raise serializers.ValidationError("Vous n'êtes pas autorisé à assigner des clients à cette société.")
        return value

    # Si on veut une validation unique pour client_name par company_account:
    # def validate(self, data):
    #     company_account = data.get('company_account') or getattr(self.instance, 'company_account', None)
    #     client_name = data.get('client_name')

    #     if not company_account: # Devrait être setté par le ViewSet si non fourni
    #         user = self.context['request'].user
    #         # Prendre la première société de l'utilisateur par défaut ou la société active de la session
    #         # Cette logique est mieux dans le ViewSet (perform_create/update)
    #         company_account = user.owned_companies.first()
    #         if not company_account:
    #              raise serializers.ValidationError("Aucune société n'est associée à cet utilisateur pour ce client.")
    #         data['company_account'] = company_account


    #     query = Client.objects.filter(company_account=company_account, client_name=client_name)
    #     if self.instance: # En cas de mise à jour, exclure l'instance actuelle
    #         query = query.exclude(pk=self.instance.pk)
    #     if query.exists():
    #         raise serializers.ValidationError({
    #             'client_name': f"Un client avec le nom '{client_name}' existe déjà pour cette société."
    #         })
    #     return data
