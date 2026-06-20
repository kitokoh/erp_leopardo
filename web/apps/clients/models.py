from django.db import models
from apps.common.models import TimeStampedModel
from apps.users.models import Company # Référence au modèle Company de l'app users

class Client(TimeStampedModel):
    company_account = models.ForeignKey(
        Company,
        related_name='clients',
        on_delete=models.CASCADE, # Si la société est supprimée, ses clients le sont aussi.
        verbose_name="Société propriétaire"
    )
    client_name = models.CharField(max_length=255, verbose_name="Nom du client")
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    phone = models.CharField(max_length=50, null=True, blank=True, verbose_name="Téléphone")
    address = models.TextField(null=True, blank=True, verbose_name="Adresse")

    contact_person_name = models.CharField(
        max_length=200,
        null=True, blank=True,
        verbose_name="Nom du contact principal"
    )
    contact_person_email = models.EmailField(
        null=True, blank=True,
        verbose_name="Email du contact"
    )
    contact_person_phone = models.CharField(
        max_length=50,
        null=True, blank=True,
        verbose_name="Téléphone du contact"
    )

    notes = models.TextField(null=True, blank=True, verbose_name="Notes internes")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['client_name']
        # Un client doit être unique pour une société donnée (basé sur le nom par exemple)
        # unique_together = ('company_account', 'client_name') # A discuter si cette contrainte est souhaitée

    def __str__(self):
        return f"{self.client_name} (Société: {self.company_account.name})"
