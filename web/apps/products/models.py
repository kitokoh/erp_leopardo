from django.db import models
from apps.common.models import TimeStampedModel
from apps.users.models import Company # Pour la ForeignKey company_account

class ProductCategory(TimeStampedModel):
    company_account = models.ForeignKey(
        Company,
        related_name='product_categories',
        on_delete=models.CASCADE,
        verbose_name="Société propriétaire"
    )
    name = models.CharField(max_length=200, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    class Meta:
        verbose_name = "Catégorie de produit"
        verbose_name_plural = "Catégories de produits"
        ordering = ['name']
        unique_together = ('company_account', 'name') # Nom de catégorie unique par société

    def __str__(self):
        return f"{self.name} (Société: {self.company_account.name})"


class Product(TimeStampedModel):
    PRODUCT_TYPE_CHOICES = [
        ('GOODS', 'Bien Matériel'),
        ('SERVICE', 'Service'),
    ]

    company_account = models.ForeignKey(
        Company,
        related_name='products',
        on_delete=models.CASCADE,
        verbose_name="Société propriétaire"
    )
    category = models.ForeignKey(
        ProductCategory,
        related_name='products',
        on_delete=models.SET_NULL, # Si la catégorie est supprimée, le produit reste mais sans catégorie
        null=True,
        blank=True,
        verbose_name="Catégorie"
    )
    name = models.CharField(max_length=255, verbose_name="Nom du produit/service")
    reference = models.CharField(
        max_length=100,
        null=True, blank=True,
        verbose_name="Référence"
        # unique=True # Si la référence doit être unique globalement.
                      # Pour unique par société, il faudrait unique_together avec company_account.
    )
    description = models.TextField(null=True, blank=True, verbose_name="Description détaillée")
    unit_price_ht = models.DecimalField(
        max_digits=12, # Augmenté pour plus de flexibilité
        decimal_places=2,
        verbose_name="Prix Unitaire HT"
    )
    product_type = models.CharField(
        max_length=50,
        choices=PRODUCT_TYPE_CHOICES,
        default='GOODS',
        verbose_name="Type de produit"
    )
    unit_of_measure = models.CharField(
        max_length=50,
        null=True, blank=True,
        verbose_name="Unité de mesure",
        help_text="Ex: pièce, kg, heure, forfait"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    # Potentiels futurs champs:
    # stock_quantity = models.IntegerField(default=0, null=True, blank=True, verbose_name="Quantité en stock")
    # supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.SET_NULL, null=True, blank=True) # Si module fournisseurs

    class Meta:
        verbose_name = "Produit/Service"
        verbose_name_plural = "Produits & Services"
        ordering = ['name']
        # Référence unique par société si nécessaire
        unique_together = (('company_account', 'reference'),) # Assure que la référence est unique pour une société donnée si elle n'est pas vide/null

    def __str__(self):
        return f"{self.name} (Réf: {self.reference or 'N/A'})"

    def clean(self):
        # Assurer que si la référence est fournie, elle n'est pas une chaîne vide
        if self.reference is not None and not self.reference.strip():
            self.reference = None # Mettre à None si seulement des espaces
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean() # Appeler clean() pour valider avant de sauvegarder
        super().save(*args, **kwargs)
