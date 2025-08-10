from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    """
    Formulaire d'inscription pour les nouveaux utilisateurs pour le frontend web.
    Il est similaire au UserRegistrationSerializer mais est un formulaire Django.
    """
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput,
        help_text="Votre mot de passe (8 caractères minimum)." # Doit correspondre aux validateurs si utilisés
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput,
        help_text="Retapez votre mot de passe."
    )
    company_name = forms.CharField(
        label="Nom de votre société (optionnel)",
        max_length=255,
        required=False,
        help_text="Le nom de la société qui sera créée pour votre compte."
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'company_name', 'password', 'password2')
        # Labels personnalisés si différents de ceux générés par Django à partir du verbose_name du modèle
        labels = {
            'username': "Nom d'utilisateur",
            'email': "Adresse Email",
            'first_name': "Prénom",
            'last_name': "Nom de famille",
        }
        help_texts = {
            'username': "Ce nom sera public et utilisé pour vous identifier.",
            'email': "Nous ne partagerons jamais votre email.",
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un utilisateur avec cette adresse email existe déjà.")
        return email.lower() # Normaliser l'email en minuscules

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        # Ajouter d'autres validations si nécessaire (ex: caractères interdits)
        return username

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        # On pourrait ajouter ici des validateurs de complexité de mot de passe
        # si on ne s'appuie pas uniquement sur AUTH_PASSWORD_VALIDATORS de Django.
        return password2

    # Note: La création effective de l'User et de la Company associée se fera dans la vue
    # en appelant l'API DRF (UserRegistrationSerializer) pour centraliser la logique métier.
    # Ce formulaire Django sert principalement à la validation et au rendu dans le template.


class UserLoginForm(AuthenticationForm):
    """
    Formulaire de connexion personnalisé si on veut changer le style ou ajouter des champs.
    Hérite de AuthenticationForm de Django pour la logique de base.
    """
    username = forms.CharField(
        label="Email ou Nom d'utilisateur", # On permet de se connecter avec l'un ou l'autre
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'})
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}),
    )

    # Si on voulait ajouter "Se souvenir de moi"
    # remember_me = forms.BooleanField(label="Se souvenir de moi", required=False)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        # On peut customiser les placeholders ou autres attributs ici si besoin
        # self.fields['username'].widget.attrs.update({'placeholder': 'Email ou Nom d'utilisateur'})
        # self.fields['password'].widget.attrs.update({'placeholder': 'Mot de passe'})


class UserProfileUpdateForm(forms.ModelForm):
    """
    Formulaire pour mettre à jour le profil utilisateur (prénom, nom).
    L'email et le nom d'utilisateur ne sont pas modifiables via ce formulaire simple.
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name')
        labels = {
            'first_name': "Prénom",
            'last_name': "Nom de famille",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs requis si ce n'est pas déjà le cas au niveau du modèle
        # pour ce formulaire spécifique.
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class CustomPasswordChangeForm(DjangoPasswordChangeForm):
    """
    Formulaire de changement de mot de passe personnalisé, si besoin.
    """
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        # Appliquer des classes Bootstrap ou autres customisations aux champs
        for fieldname in ['old_password', 'new_password1', 'new_password2']:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'
            self.fields[fieldname].help_text = None # Enlever les help_text par défaut si on les gère autrement

# Formulaires pour la réinitialisation de mot de passe (PasswordResetForm, SetPasswordForm)
# On peut utiliser ceux de django.contrib.auth.forms directement dans les vues
# ou les sous-classer ici pour les customiser si nécessaire.
# from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
