from django.contrib.auth import get_user_model
from django.db import transaction # Pour s'assurer de la création atomique User + Company
from rest_framework import serializers
from .models import Company

User = get_user_model()

class CompanyBasicSerializer(serializers.ModelSerializer):
    """
    Serializer basique pour Company, utilisé pour l'affichage imbriqué.
    """
    class Meta:
        model = Company
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle User (lecture et mise à jour du profil).
    """
    # Pour afficher les sociétés possédées par l'utilisateur de manière imbriquée et en lecture seule.
    owned_companies = CompanyBasicSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active', # Utile de le voir, même si non modifiable directement ici pour l'utilisateur lui-même
            'is_staff',  # Idem
            'date_joined',
            'updated_at',
            'owned_companies'
        ]
        read_only_fields = ('id', 'username', 'email', 'date_joined', 'updated_at', 'owned_companies', 'is_staff', 'is_active')
        # L'utilisateur ne peut pas changer son username ou email directement via ce serializer de profil
        # pour éviter des problèmes. Ces actions pourraient nécessiter des flux de vérification spécifiques.


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription de nouveaux utilisateurs.
    Gère la création de l'utilisateur et de sa société par défaut.
    """
    password2 = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True,
        label="Confirmation du mot de passe",
        help_text="Retapez votre mot de passe."
    )
    company_name = serializers.CharField(
        max_length=255,
        write_only=True,
        required=False, # Optionnel, un nom par défaut sera généré sinon
        label="Nom de votre société (optionnel)",
        help_text="Le nom de la société qui sera créée pour votre compte."
    )
    first_name = serializers.CharField(required=True, label="Prénom")
    last_name = serializers.CharField(required=True, label="Nom de famille")


    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password2',
            'first_name',
            'last_name',
            'company_name'
        ]
        extra_kwargs = {
            'password': {
                'write_only': True,
                'style': {'input_type': 'password'},
                'help_text': "Votre mot de passe (8 caractères minimum).", # Ajouter une aide si des validateurs sont en place
            },
            'email': {'required': True},
            'username': {'required': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists(): # insensible à la casse
            raise serializers.ValidationError("Un utilisateur avec cette adresse email existe déjà.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists(): # insensible à la casse
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        # Ajouter d'autres validations pour username si nécessaire (ex: caractères autorisés)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Les deux mots de passe ne correspondent pas."})

        # S'assurer que first_name et last_name sont bien présents (même si `required=True` sur le champ,
        # une validation globale peut être utile si on a des logiques conditionnelles)
        if not attrs.get('first_name'):
            raise serializers.ValidationError({"first_name": "Le prénom est requis."})
        if not attrs.get('last_name'):
            raise serializers.ValidationError({"last_name": "Le nom de famille est requis."})

        # On pourrait ajouter ici des validateurs de complexité de mot de passe si Django ne les gère pas
        # via AUTH_PASSWORD_VALIDATORS dans settings.py. Mais il vaut mieux utiliser les validateurs Django.
        return attrs

    @transaction.atomic # Assure que la création de l'User et de la Company est atomique
    def create(self, validated_data):
        validated_data.pop('password2')
        company_name_provided = validated_data.pop('company_name', None)

        user = User.objects.create_user( # Utilise le UserManager.create_user
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'], # create_user s'occupe du hachage
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name')
        )

        default_company_name = company_name_provided if company_name_provided else f"Société de {user.username}"
        # S'assurer de l'unicité du nom de la société pour cet owner si cette logique est requise,
        # bien que ce soit la première société, donc peu de risque de conflit ici.
        Company.objects.create(name=default_company_name, owner=user)

        return user


class CompanySerializer(serializers.ModelSerializer):
    """
    Serializer complet pour le modèle Company.
    """
    owner = UserSerializer(read_only=True) # Afficher les détails du propriétaire en lecture
    # Si on veut juste l'ID du propriétaire en écriture/lecture :
    # owner_id = serializers.UUIDField(source='owner.id', read_only=True) # Ou PrimaryKeyRelatedField pour écriture

    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'address',
            'logo',
            'owner', # Imbriqué en lecture
            # 'owner_id', # Si on préfère l'ID
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at')
        extra_kwargs = {
            'logo': {'required': False, 'allow_null': True},
            'address': {'required': False, 'allow_null': True},
        }

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Le nom de la société ne peut pas être vide.")

        # Assurer l'unicité du nom de la société PAR PROPRIÉTAIRE lors de la création/MAJ
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            owner = request.user
            query = Company.objects.filter(owner=owner, name__iexact=value) # insensible à la casse

            if self.instance: # Si c'est une mise à jour (instance existe)
                query = query.exclude(pk=self.instance.pk) # Exclure l'objet actuel de la vérification

            if query.exists():
                raise serializers.ValidationError(f"Vous possédez déjà une société nommée '{value}'. Veuillez choisir un autre nom.")
        return value

    def create(self, validated_data):
        # L'owner est automatiquement setté dans la vue (perform_create) basé sur request.user
        # Si on voulait le passer dans le serializer, il faudrait l'ajouter ici.
        # validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
