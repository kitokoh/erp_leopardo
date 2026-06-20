from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from apps.users.models import User, Company
from .models import ProductCategory, Product

class ProductCategoryAPITests(APITestCase):
    def setUp(self):
        self.client_api = APIClient() # Renommé pour éviter conflit si on importe le client Django standard

        # User 1, Company 1
        self.user1 = User.objects.create_user(email='p_user1@example.com', username='p_user1', password='password123', first_name='PUser1', last_name='Test')
        self.company1 = Company.objects.create(name="PCompany A", owner=self.user1)
        self.client_api.force_authenticate(user=self.user1) # Authentifier user1 par défaut pour la plupart des tests

        # User 2, Company 2
        self.user2 = User.objects.create_user(email='p_user2@example.com', username='p_user2', password='password123', first_name='PUser2', last_name='Test')
        self.company2 = Company.objects.create(name="PCompany B", owner=self.user2)

        # URLs
        self.categories_list_create_url = reverse('products_api:productcategory-list')

        # Catégorie initiale pour company1
        self.category1_c1 = ProductCategory.objects.create(company_account=self.company1, name="Cat1 for C1")

    def test_create_product_category_success(self):
        data = {'name': 'New Category C1', 'description': 'Desc for new cat'}
        # company_account est automatiquement gérée par le ViewSet (perform_create)
        response = self.client_api.post(self.categories_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductCategory.objects.count(), 2) # Initial + New
        new_cat = ProductCategory.objects.get(name='New Category C1')
        self.assertEqual(new_cat.company_account, self.company1)

    def test_create_product_category_duplicate_name_for_same_company(self):
        data = {'name': self.category1_c1.name} # Nom existant pour company1
        response = self.client_api.post(self.categories_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data) # Le serializer devrait retourner une erreur

    def test_list_product_categories_for_own_company(self):
        # Ajouter une autre catégorie pour company1
        ProductCategory.objects.create(company_account=self.company1, name="Cat2 for C1")
        # Créer une catégorie pour company2 (par user2)
        self.client_api.force_authenticate(user=self.user2)
        self.client_api.post(self.categories_list_create_url, {'name': 'Cat1 for C2'}, format='json')

        # Revenir à user1
        self.client_api.force_authenticate(user=self.user1)
        response = self.client_api.get(self.categories_list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2) # Seulement les 2 de company1
        category_names = [cat['name'] for cat in response.data['results']]
        self.assertIn(self.category1_c1.name, category_names)
        self.assertIn("Cat2 for C1", category_names)
        self.assertNotIn("Cat1 for C2", category_names)

    def test_retrieve_own_product_category(self):
        detail_url = reverse('products_api:productcategory-detail', kwargs={'pk': self.category1_c1.pk})
        response = self.client_api.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.category1_c1.name)

    def test_cannot_retrieve_other_company_product_category(self):
        category_c2 = ProductCategory.objects.create(company_account=self.company2, name="Cat Other C2")
        detail_url_other = reverse('products_api:productcategory-detail', kwargs={'pk': category_c2.pk})
        # user1 est toujours authentifié
        response = self.client_api.get(detail_url_other)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Ou 403 selon la permission exacte

    def test_update_own_product_category(self):
        detail_url = reverse('products_api:productcategory-detail', kwargs={'pk': self.category1_c1.pk})
        update_data = {'name': 'Cat1 for C1 Updated', 'description': 'Updated desc'}
        response = self.client_api.put(detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category1_c1.refresh_from_db()
        self.assertEqual(self.category1_c1.name, 'Cat1 for C1 Updated')

    def test_delete_own_product_category(self):
        detail_url = reverse('products_api:productcategory-detail', kwargs={'pk': self.category1_c1.pk})
        response = self.client_api.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProductCategory.objects.filter(pk=self.category1_c1.pk).exists())


class ProductAPITests(APITestCase):
    def setUp(self):
        self.client_api = APIClient()

        self.user1 = User.objects.create_user(email='prod_user1@example.com', username='prod_user1', password='password123')
        self.company1 = Company.objects.create(name="ProdCompany A", owner=self.user1)
        self.category_c1 = ProductCategory.objects.create(company_account=self.company1, name="Electronics C1")

        self.user2 = User.objects.create_user(email='prod_user2@example.com', username='prod_user2', password='password123')
        self.company2 = Company.objects.create(name="ProdCompany B", owner=self.user2)
        self.category_c2 = ProductCategory.objects.create(company_account=self.company2, name="Books C2")

        self.client_api.force_authenticate(user=self.user1)
        self.products_list_create_url = reverse('products_api:product-list')

        self.product1_c1 = Product.objects.create(
            company_account=self.company1, category=self.category_c1,
            name="Laptop C1", reference="LP001", unit_price_ht="999.99"
        )

    def test_create_product_success(self):
        data = {
            'name': 'New Product C1', 'reference': 'NP001', 'unit_price_ht': '19.99',
            'category': self.category_c1.pk, # Passer le PK de la catégorie
            'product_type': 'GOODS', 'description': 'A brand new product'
        }
        response = self.client_api.post(self.products_list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Product.objects.count(), 2)
        new_prod = Product.objects.get(name='New Product C1')
        self.assertEqual(new_prod.company_account, self.company1)
        self.assertEqual(new_prod.category, self.category_c1)

    def test_create_product_with_category_from_another_company_fails(self):
        data = {
            'name': 'Product Bad Category', 'reference': 'BC001', 'unit_price_ht': '25.00',
            'category': self.category_c2.pk # Catégorie de company2, mais user1 est authentifié
        }
        response = self.client_api.post(self.products_list_create_url, data, format='json')
        # Le ViewSet (perform_create ou get_serializer_context) devrait attraper ça
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)

    def test_list_products_for_own_company(self):
        Product.objects.create(company_account=self.company1, name="Mouse C1", unit_price_ht="29.99")
        # Produit pour company2 (ne doit pas apparaître pour user1)
        Product.objects.create(company_account=self.company2, category=self.category_c2, name="Book C2", unit_price_ht="15.00")

        response = self.client_api.get(self.products_list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2) # Laptop C1 et Mouse C1
        product_names = [p['name'] for p in response.data['results']]
        self.assertIn("Laptop C1", product_names)
        self.assertIn("Mouse C1", product_names)
        self.assertNotIn("Book C2", product_names)

    def test_retrieve_own_product(self):
        detail_url = reverse('products_api:product-detail', kwargs={'pk': self.product1_c1.pk})
        response = self.client_api.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.product1_c1.name)

    def test_cannot_retrieve_other_company_product(self):
        product_c2 = Product.objects.create(company_account=self.company2, name="OtherProd C2", unit_price_ht="1.00")
        detail_url_other = reverse('products_api:product-detail', kwargs={'pk': product_c2.pk})
        response = self.client_api.get(detail_url_other)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_product(self):
        detail_url = reverse('products_api:product-detail', kwargs={'pk': self.product1_c1.pk})
        update_data = {
            'name': 'Laptop C1 Updated',
            'unit_price_ht': '1099.00',
            'category': self.category_c1.pk, # Important de renvoyer les champs obligatoires pour PUT
            'reference': self.product1_c1.reference, # ou le mettre à jour
            'product_type': self.product1_c1.product_type,
        }
        response = self.client_api.put(detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.product1_c1.refresh_from_db()
        self.assertEqual(self.product1_c1.name, 'Laptop C1 Updated')
        self.assertEqual(float(self.product1_c1.unit_price_ht), 1099.00)

    def test_update_product_cannot_change_category_to_other_company_category(self):
        detail_url = reverse('products_api:product-detail', kwargs={'pk': self.product1_c1.pk})
        update_data = {
            'name': self.product1_c1.name,
            'unit_price_ht': self.product1_c1.unit_price_ht,
            'category': self.category_c2.pk, # Tente de changer pour une catégorie de company2
            'reference': self.product1_c1.reference,
            'product_type': self.product1_c1.product_type,
        }
        response = self.client_api.put(detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)

    def test_delete_own_product(self):
        detail_url = reverse('products_api:product-detail', kwargs={'pk': self.product1_c1.pk})
        response = self.client_api.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=self.product1_c1.pk).exists())

    def test_product_reference_uniqueness_per_company(self):
        # product1_c1 a reference "LP001" pour company1
        data_same_ref = {
            'name': 'Another Laptop', 'reference': 'LP001', 'unit_price_ht': '800.00',
            'category': self.category_c1.pk
        }
        response = self.client_api.post(self.products_list_create_url, data_same_ref, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # Devrait échouer à cause de unique_together
        self.assertIn('reference', response.data) # ou non_field_errors si c'est unique_together

        # Mais user2 (company2) peut utiliser la même référence
        self.client_api.force_authenticate(user=self.user2)
        data_same_ref_c2 = {
            'name': 'Laptop C2', 'reference': 'LP001', 'unit_price_ht': '850.00',
            'category': self.category_c2.pk
        }
        response_c2 = self.client_api.post(reverse('products_api:product-list'), data_same_ref_c2, format='json')
        self.assertEqual(response_c2.status_code, status.HTTP_201_CREATED, response_c2.data)
        self.assertTrue(Product.objects.filter(company_account=self.company2, reference='LP001').exists())
