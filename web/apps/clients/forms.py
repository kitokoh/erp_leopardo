from django import forms
# from .models import Client # Pas un ModelForm pour le filtre pour l'instant

class ClientFilterForm(forms.Form):
    search_query = forms.CharField(
        label="Rechercher un client", # Label plus explicite
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm me-2', # me-2 pour marge à droite
            'placeholder': 'Nom, email, contact...',
            'aria-label': "Rechercher client" # Pour l'accessibilité
        })
    )
    is_active = forms.ChoiceField(
        label="Statut du client", # Label plus explicite
        required=False,
        choices=[
            ('', 'Tous les statuts'), # Option par défaut plus claire
            ('true', 'Actif'),
            ('false', 'Inactif'),
        ],
        widget=forms.Select(attrs={'class': 'form-select form-select-sm', 'aria-label': "Filtrer par statut"})
    )
    # On pourrait ajouter un champ pour trier (ordering)
    # ordering = forms.ChoiceField(
    #     label="Trier par",
    #     required=False,
    #     choices=[
    #         ('client_name', 'Nom (A-Z)'),
    #         ('-client_name', 'Nom (Z-A)'),
    #         ('created_at', 'Date de création (Plus anciens)'),
    #         ('-created_at', 'Date de création (Plus récents)'),
    #     ],
    #     widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    # )


class ClientForm(forms.Form):
    """
    Formulaire pour la création et la modification d'un client.
    Utilise forms.Form car la logique de sauvegarde passe par l'API DRF.
    Les champs correspondent aux champs attendus par ClientSerializer.
    """
    client_name = forms.CharField(
        label="Nom du client*",
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email",
        required=False, # Rendre optionnel comme dans le modèle/serializer
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemple@domaine.com'})
    )
    phone = forms.CharField(
        label="Téléphone",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+33 1 23 45 67 89'})
    )
    address = forms.CharField(
        label="Adresse",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '123 Rue Principale\n75001 Paris'})
    )
    contact_person_name = forms.CharField(
        label="Nom du contact principal",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    contact_person_email = forms.EmailField(
        label="Email du contact",
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    contact_person_phone = forms.CharField(
        label="Téléphone du contact",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        label="Notes internes",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    is_active = forms.BooleanField(
        label="Client actif",
        required=False, # Une checkbox non cochée retourne False, donc required=False est ok
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    # company_account n'est pas dans ce formulaire car il est géré par la vue (session)

    def __init__(self, *args, **kwargs):
        # On peut passer une instance initiale pour pré-remplir le formulaire en mode édition
        # (même si ce n'est pas un ModelForm, on peut le faire manuellement)
        initial_data = kwargs.pop('initial', None)
        super().__init__(*args, **kwargs)
        if initial_data:
            for field_name, value in initial_data.items():
                if field_name in self.fields:
                    self.fields[field_name].initial = value

    def clean_client_name(self):
        client_name = self.cleaned_data.get('client_name')
        if not client_name or not client_name.strip():
            raise forms.ValidationError("Le nom du client ne peut pas être vide.")
        return client_name.strip()

    # La validation d'unicité du client_name par company_account est gérée par l'API/Serializer DRF.
    # Si on voulait la dupliquer ici, il faudrait avoir accès à la company_account
    # (par exemple, la passer au constructeur du formulaire depuis la vue).
    # def clean(self):
    #     cleaned_data = super().clean()
    #     # ... logique de validation croisée ...
    #     return cleaned_data
