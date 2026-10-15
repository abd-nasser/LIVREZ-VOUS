import json
from unittest.mock import patch

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.core import mail
from clients_app.models import Client
from entreprises_app.models import Entreprise
from livreurs_app.models import Livreur
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


class EntrepriseLivreurCreationTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			telephone='70200000',
			first_name='Entreprise',
			last_name='Admin',
			password='secret123',
			role='entreprise',
		)
		self.entreprise = Entreprise.objects.create(
			user_principal=self.admin,
			nom_entreprise='Livraison Test',
			palier='standard',
		)
		self.url = reverse('accounts_app:ajouter-livreur-entreprise')

	@override_settings(
		EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
		DEFAULT_FROM_EMAIL='noreply@example.com',
		WHATSAPP_ACCESS_TOKEN='test-token',
		WHATSAPP_PHONE_NUMBER_ID='test-phone-id',
		WHATSAPP_CREDENTIALS_TEMPLATE='livreur_credentials',
	)
	@patch('accounts_app.notifications.urlopen')
	def test_company_admin_creates_livreur_and_sends_generated_credentials(
		self,
		urlopen,
	):
		self.client.force_login(self.admin)
		urlopen.return_value.__enter__.return_value.status = 200

		response = self.client.post(
			self.url,
			{
				'first_name': 'Nouveau',
				'last_name': 'Livreur',
				'telephone': '+22670200001',
				'email': 'livreur@example.com',
				'type_vehicule': 'moto',
			},
		)

		self.assertRedirects(
			response,
			reverse('entreprises_app:entreprise-profil', args=[self.entreprise.pk]),
		)
		livreur = Livreur.objects.select_related('user', 'entreprise').get(
			user__telephone='+22670200001',
		)
		self.assertEqual(livreur.entreprise, self.entreprise)
		self.assertEqual(livreur.user.role, 'livreur')
		self.assertEqual(livreur.user.email, 'livreur@example.com')
		self.assertTrue(livreur.user.check_password(
			mail.outbox[0].body.split('Mot de passe : ', 1)[1].splitlines()[0]
		))
		self.assertIsNotNone(livreur.user.username)
		self.assertIn(livreur.user.username, mail.outbox[0].body)
		self.assertEqual(mail.outbox[0].to, ['livreur@example.com'])

		request = urlopen.call_args.args[0]
		self.assertIn(
			'https://graph.facebook.com/v23.0/test-phone-id/messages',
			request.full_url,
		)
		self.assertEqual(request.get_header('Authorization'), 'Bearer test-token')
		payload = json.loads(request.data)
		self.assertEqual(payload['to'], '22670200001')
		self.assertEqual(
			payload['template']['components'][0]['parameters'][0]['text'],
			livreur.user.username,
		)
		self.assertEqual(
			payload['template']['components'][0]['parameters'][1]['text'],
			mail.outbox[0].body.split('Mot de passe : ', 1)[1].splitlines()[0],
		)

	@override_settings(
		EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
		DEFAULT_FROM_EMAIL='',
		WHATSAPP_ACCESS_TOKEN='',
		WHATSAPP_PHONE_NUMBER_ID='',
		WHATSAPP_CREDENTIALS_TEMPLATE='',
	)
	def test_missing_delivery_configuration_does_not_create_account(self):
		self.client.force_login(self.admin)

		response = self.client.post(self.url, {
			'first_name': 'Nouveau',
			'last_name': 'Livreur',
			'telephone': '+22670200001',
			'email': 'livreur@example.com',
			'type_vehicule': 'moto',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Configuration manquante')
		self.assertFalse(User.objects.filter(telephone='+22670200001').exists())
		self.assertEqual(Livreur.objects.count(), 0)

	def test_non_entreprise_user_cannot_create_company_livreur(self):
		user = User.objects.create_user(
			telephone='+22670200002',
			first_name='Client',
			last_name='Test',
			password='secret123',
			role='client',
		)
		self.client.force_login(user)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 403)
		self.assertEqual(Livreur.objects.count(), 0)
