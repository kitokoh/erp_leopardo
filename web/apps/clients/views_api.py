from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Client
from .serializers import ClientSerializer
from apps.users.models import Company # Pour récupérer la société de l'utilisateur
from apps.users.permissions import CanManageObjectBasedOnCompany # Notre permission multi-tenant

class ClientViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows clients to be viewed or edited.
    Ensures multi-tenancy by filtering clients based on the user's company.
    """
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageObjectBasedOnCompany]

    def get_queryset(self):
        """
        This view should return a list of all the clients
        for the currently authenticated user's companies.
        """
        user = self.request.user
        if user.is_superuser: # Les superusers peuvent voir tous les clients (optionnel, selon la politique)
            return Client.objects.all().select_related('company_account')

        # Récupérer toutes les sociétés possédées par l'utilisateur
        user_companies = Company.objects.filter(owner=user)
        if not user_companies.exists():
            return Client.objects.none() # Pas de sociétés, donc pas de clients à voir

        # Pour une approche où l'utilisateur travaille dans UNE société active à la fois (stockée en session par exemple)
        # active_company_id = self.request.session.get('active_company_id')
        # if active_company_id:
        #     return Client.objects.filter(company_account_id=active_company_id, company_account__owner=user).select_related('company_account')
        # else:
        #     # Fallback: si pas de société active, on pourrait ne rien retourner ou retourner ceux de la première société
        #     first_company = user_companies.first()
        #     if first_company:
        #         return Client.objects.filter(company_account=first_company).select_related('company_account')
        #     return Client.objects.none()

        # Pour l'instant, retournons les clients de toutes les sociétés possédées par l'utilisateur.
        # La logique de "société active" sera gérée plus tard par le frontend et potentiellement une session.
        return Client.objects.filter(company_account__in=user_companies).select_related('company_account')

    def perform_create(self, serializer):
        """
        Assign the company_account based on the authenticated user.
        """
        user = self.request.user

        # Logique pour déterminer la company_account :
        # 1. Essayer de prendre company_account_id depuis les données de la requête si fourni
        #    et vérifier que l'utilisateur en est bien le propriétaire.
        # 2. Sinon, prendre la première société possédée par l'utilisateur.
        # 3. Si l'utilisateur n'a pas de société, lever une erreur.

        company_id_from_request = self.request.data.get('company_account') # Peut être l'ID ou un dict
        target_company = None

        if company_id_from_request:
            if isinstance(company_id_from_request, dict): # Si c'est un objet imbriqué
                 company_id_from_request = company_id_from_request.get('id')
            try:
                # Essayer de récupérer la société si l'ID est fourni
                target_company = Company.objects.get(pk=company_id_from_request, owner=user)
            except Company.DoesNotExist:
                raise serializers.ValidationError({
                    "company_account": "La société spécifiée n'existe pas ou vous n'en êtes pas le propriétaire."
                })
        else:
            # Si non fourni, prendre la première société de l'utilisateur
            target_company = user.owned_companies.first()

        if not target_company:
            # Ceci ne devrait pas arriver si l'inscription crée une société par défaut,
            # ou si l'UI force la sélection/création d'une société avant de créer un client.
            raise serializers.ValidationError({
                "company_account": "Aucune société n'est associée à votre compte pour créer ce client. Veuillez d'abord créer ou sélectionner une société."
            })

        # Valider si un client avec ce nom existe déjà pour cette société
        client_name = serializer.validated_data.get('client_name')
        if Client.objects.filter(company_account=target_company, client_name=client_name).exists():
            raise serializers.ValidationError({
                'client_name': f"Un client avec le nom '{client_name}' existe déjà pour la société '{target_company.name}'."
            })

        serializer.save(company_account=target_company)

    def perform_update(self, serializer):
        # La permission CanManageObjectBasedOnCompany a déjà vérifié que l'utilisateur
        # est propriétaire de la company_account de l'objet `instance` qui va être mis à jour.
        # On s'assure que company_account ne peut pas être changé vers une société non possédée.

        requested_company_id = None
        if 'company_account' in self.request.data:
            company_data = self.request.data.get('company_account')
            if isinstance(company_data, dict): # Si c'est un objet imbriqué
                 requested_company_id = company_data.get('id')
            elif company_data is not None : # Si c'est un ID direct
                 requested_company_id = str(company_data) # Assurer que c'est une string pour la comparaison avec UUID.hex

        current_company_id = str(serializer.instance.company_account.id)

        if requested_company_id and requested_company_id != current_company_id:
            # Si on tente de changer la company_account, il faut vérifier les droits sur la nouvelle.
            try:
                target_company = Company.objects.get(pk=requested_company_id, owner=self.request.user)
                serializer.save(company_account=target_company) # Permettre le changement
            except Company.DoesNotExist:
                raise serializers.ValidationError({
                    "company_account": "Vous ne pouvez pas assigner ce client à la société spécifiée."
                })
        else:
            # Si company_account n'est pas dans la requête ou est la même, on sauvegarde normalement.
            # company_account sera conservé ou mis à jour avec les autres champs validés.
            serializer.save()


    # Si on a besoin de plus de contrôle, on peut redéfinir les méthodes create(), update(), list(), etc.
    # def create(self, request, *args, **kwargs):
    #     # Logique personnalisée avant/après la création
    #     return super().create(request, *args, **kwargs)

    # def list(self, request, *args, **kwargs):
    #     # Logique personnalisée pour la liste
    #     return super().list(request, *args, **kwargs)
