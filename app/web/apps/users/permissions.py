from rest_framework import permissions

class IsOwnerOfCompany(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser uniquement le propriétaire d'une société
    à la voir ou la modifier.
    """
    def has_object_permission(self, request, view, obj):
        # Les requêtes de lecture (GET, HEAD, OPTIONS) sont autorisées si l'objet a un owner
        # et que cet owner est l'utilisateur connecté.
        # Pour les autres méthodes (PUT, PATCH, DELETE), il faut être le propriétaire.
        if obj.owner == request.user:
            return True
        return False


class IsObjectRelatedToUserCompany(permissions.BasePermission):
    """
    Permission personnalisée pour vérifier si l'objet demandé (ex: Client, Produit, Document)
    est lié à une société (`company_account`) dont l'utilisateur connecté est le propriétaire.
    """
    def has_permission(self, request, view):
        # Cette permission est souvent utilisée pour les vues de liste (GET list, POST)
        # où l'on n'a pas encore d'instance d'objet spécifique.
        # La logique de filtrage du queryset dans la vue est le principal garant ici.
        # On peut s'assurer que l'utilisateur a au moins une société.
        return request.user and request.user.is_authenticated and request.user.owned_companies.exists()

    def has_object_permission(self, request, view, obj):
        # Vérifie si l'objet a un attribut 'company_account'
        if not hasattr(obj, 'company_account'):
            # Si l'objet n'a pas de company_account (ex: un UserProfile),
            # cette permission n'est peut-être pas la bonne ou doit être adaptée.
            # Pour l'instant, on refuse l'accès si ce champ n'existe pas.
            return False

        # Vérifie si l'utilisateur est le propriétaire de la company_account de l'objet.
        # obj.company_account est une instance de Company.
        # obj.company_account.owner est une instance de User.
        if obj.company_account and obj.company_account.owner == request.user:
            return True

        # Gérer le cas où company_account pourrait être None si le modèle le permet
        # (bien que pour notre cas multi-tenant strict, il ne devrait pas l'être pour les objets métier).
        if obj.company_account is None:
            return False # Ou une autre logique si des objets orphelins sont permis

        return False


class CanManageObjectBasedOnCompany(permissions.BasePermission):
    """
    Permission plus générique pour les objets liés à une Company.
    - Pour les actions de liste (GET) et de création (POST), l'utilisateur doit être authentifié
      et avoir au moins une société. La logique de filtrage/assignation se fait dans la vue.
    - Pour les actions sur un objet spécifique (GET détail, PUT, PATCH, DELETE),
      l'utilisateur doit être le propriétaire de la `company_account` de l'objet.
    """

    def has_permission(self, request, view):
        """
        Autorisation pour les actions de niveau liste (GET /) ou création (POST /).
        """
        if not (request.user and request.user.is_authenticated):
            return False

        # Pour POST (création), l'utilisateur doit avoir une société à laquelle lier l'objet.
        # Le ViewSet se chargera d'assigner la bonne company_account.
        if request.method == 'POST':
            # L'utilisateur doit avoir au moins une société qu'il possède pour créer un objet lié à une société.
            # La logique pour choisir *quelle* société utiliser (si plusieurs) sera dans le perform_create du ViewSet.
            return request.user.owned_companies.exists()

        # Pour GET (liste), l'utilisateur doit être authentifié.
        # Le filtrage du queryset dans le ViewSet se chargera de ne montrer que les objets pertinents.
        return True


    def has_object_permission(self, request, view, obj):
        """
        Autorisation pour les actions de niveau détail (GET /id, PUT /id, PATCH /id, DELETE /id).
        """
        if not (request.user and request.user.is_authenticated):
            return False

        if not hasattr(obj, 'company_account') or obj.company_account is None:
            return False # L'objet doit être lié à une société

        # L'utilisateur doit être le propriétaire de la société à laquelle l'objet est lié.
        return obj.company_account.owner == request.user
