from django.test import TestCase
from django.urls import reverse
from clients_app.models import Client
from .models import User


class LoginViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			telephone='70000000',
			username='livreur.test',
			first_name='Test',
			last_name='Livreur',
			password='secret123',
		)
		self.url = reverse('accounts_app:login')
		self.logout_url = reverse('accounts_app:logout')

	def test_login_with_telephone(self):
		response = self.client.post(self.url, {
			'login_method': 'telephone',
			'telephone': self.user.telephone,
			'password': 'secret123',
		})

		self.assertEqual(response.status_code, 200)
		self.assertIn('_auth_user_id', self.client.session)
		self.assertContains(response, 'Bienvenue Test')
		self.assertEqual(response['HX-Trigger'], 'login-success')

	def test_login_with_username(self):
		response = self.client.post(self.url, {
			'login_method': 'username',
			'username': self.user.username,
			'password': 'secret123',
		})

		self.assertEqual(response.status_code, 200)
		self.assertIn('_auth_user_id', self.client.session)
		self.assertContains(response, 'Bienvenue Test')

	def test_invalid_credentials_show_error(self):
		response = self.client.post(self.url, {
			'login_method': 'telephone',
			'telephone': self.user.telephone,
			'password': 'wrong-password',
		})

		self.assertEqual(response.status_code, 200)
		self.assertNotIn('_auth_user_id', self.client.session)
		self.assertContains(response, 'Identifiant ou mot de passe incorrect.')
		self.assertEqual(response['HX-Retarget'], '#login-message')
		self.assertEqual(response['HX-Reswap'], 'innerHTML')

	def test_logout_clears_session(self):
		self.client.force_login(self.user)

		response = self.client.post(self.logout_url)

		self.assertRedirects(response, reverse('home_app:home-page'))
		self.assertNotIn('_auth_user_id', self.client.session)


class ClientRegistrationTests(TestCase):
	def test_registration_creates_user_and_client_profile(self):
		response = self.client.post(reverse('accounts_app:inscription-clients'), {
			'username': 'client.test',
			'first_name': 'Client',
			'last_name': 'Test',
			'telephone': '70123456',
			'email': 'client@example.com',
			'password': 'secret123',
			'confirm_password': 'secret123',
			'ville': 'Ouagadougou',
			'quartier': 'Koulouba',
		})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response['HX-Trigger'], 'client-register-success')
		client = Client.objects.select_related('user').get(user__telephone='70123456')
		self.assertEqual(client.user.username, 'client.test')
		self.assertEqual(client.user.role, 'client')
		self.assertTrue(client.user.check_password('secret123'))
		self.assertEqual(client.ville, 'Ouagadougou')
		self.assertEqual(client.quartier, 'Koulouba')
		self.assertFalse(client.photo_profil)

	def test_duplicate_telephone_returns_form_errors(self):
		User.objects.create_user(
			telephone='70123456',
			username='existing.client',
			first_name='Existing',
			last_name='Client',
			password='secret123',
		)

		response = self.client.post(reverse('accounts_app:inscription-clients'), {
			'username': 'new.client',
			'first_name': 'New',
			'last_name': 'Client',
			'telephone': '70123456',
			'password': 'secret123',
			'confirm_password': 'secret123',
		})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response['HX-Retarget'], '#form-container')
		self.assertContains(response, 'Ce numéro de téléphone est déjà utilisé.')
		self.assertEqual(Client.objects.count(), 0)
