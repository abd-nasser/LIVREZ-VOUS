from django.test import TestCase
from django.urls import reverse
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
