import json
from unittest.mock import patch

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.core import mail
from django.contrib.auth import HASH_SESSION_KEY
from clients_app.models import Client
from entreprises_app.models import Entreprise
from livreurs_app.models import Livreur
from .forms import ChangeCredentialsLivreurEntrepriseForm
from .models import User


class ChangeCredentialsLivreurEntrepriseFormTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			telephone='+22670000001',
			username='courier.old',
			first_name='Courier',
			last_name='Test',
			password='old-secret-456',
			role='livreur',
		)

	def form_data(self, **overrides):
		data = {
			'new_username': 'courier.new',
			'new_password': 'Violet-Planet-47!Strong',
			'current_password': 'old-secret-456',
			'confirm_new_password': 'Violet-Planet-47!Strong',
		}
		data.update(overrides)
		return data

	def test_valid_form_changes_username_and_password(self):
		form = ChangeCredentialsLivreurEntrepriseForm(
			data=self.form_data(),
			user=self.user,
		)

		self.assertTrue(form.is_valid(), form.errors)
		updated_user = form.save()
		updated_user.refresh_from_db()

		self.assertEqual(updated_user.username, 'courier.new')
		self.assertTrue(updated_user.check_password('Violet-Planet-47!Strong'))

	def test_incorrect_current_password_is_rejected(self):
		form = ChangeCredentialsLivreurEntrepriseForm(
			data=self.form_data(current_password='wrong-password'),
			user=self.user,
		)

		self.assertFalse(form.is_valid())
		self.assertIn('current_password', form.errors)

	def test_username_used_by_another_user_is_rejected(self):
		User.objects.create_user(
			telephone='+22670000002',
			username='courier.taken',
			first_name='Other',
			last_name='Courier',
			password='old-secret-456',
		)
		form = ChangeCredentialsLivreurEntrepriseForm(
			data=self.form_data(new_username='courier.taken'),
			user=self.user,
		)

		self.assertFalse(form.is_valid())
		self.assertIn('new_username', form.errors)

	def test_password_confirmation_must_match(self):
		form = ChangeCredentialsLivreurEntrepriseForm(
			data=self.form_data(confirm_new_password='Different-Password-3!'),
			user=self.user,
		)

		self.assertFalse(form.is_valid())
		self.assertIn('confirm_new_password', form.errors)

	def test_new_password_must_pass_django_password_validators(self):
		form = ChangeCredentialsLivreurEntrepriseForm(
			data=self.form_data(
				new_password='password',
				confirm_new_password='password',
			),
			user=self.user,
		)

		self.assertFalse(form.is_valid())
		self.assertIn('new_password', form.errors)


class ChangeCredentialsLivreurEntrepriseViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			telephone='+22670000003',
			username='courier.view',
			first_name='Courier',
			last_name='View',
			password='old-secret-456',
			role='livreur',
		)
		self.livreur = Livreur.objects.create(
			user=self.user,
			type_vehicule='moto',
		)
		self.url = reverse('accounts_app:change-livreur-credentials')

	def test_successful_password_change_keeps_user_session_active(self):
		self.client.force_login(self.user)

		response = self.client.post(self.url, {
			'new_username': 'courier.updated',
			'new_password': 'Violet-Planet-47!Strong',
			'current_password': 'old-secret-456',
			'confirm_new_password': 'Violet-Planet-47!Strong',
		})

		self.user.refresh_from_db()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response['HX-Trigger'], 'livreur-credentials-change-success')
		self.assertContains(response, 'Identifiants mis à jour')
		self.assertContains(response, reverse(
			'livreurs_app:livreur-profil',
			args=[self.livreur.pk],
		))
		self.assertEqual(
			self.client.session[HASH_SESSION_KEY],
			self.user.get_session_auth_hash(),
		)
		self.assertTrue(self.user.check_password('Violet-Planet-47!Strong'))
		self.assertEqual(self.user.username, 'courier.updated')

	def test_invalid_submission_returns_form_errors_through_htmx(self):
		self.client.force_login(self.user)

		response = self.client.post(self.url, {
			'new_username': 'courier.updated',
			'new_password': 'Violet-Planet-47!Strong',
			'current_password': 'wrong-password',
			'confirm_new_password': 'Violet-Planet-47!Strong',
		}, HTTP_HX_REQUEST='true')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			response['HX-Retarget'],
			'#credentials-form-container',
		)
		self.assertContains(response, 'Le mot de passe actuel est incorrect.')
		self.user.refresh_from_db()
		self.assertEqual(self.user.username, 'courier.view')

	def test_non_livreur_cannot_access_credentials_change(self):
		client_user = User.objects.create_user(
			telephone='+22670000004',
			username='client.view',
			first_name='Client',
			last_name='View',
			password='old-secret-456',
			role='client',
		)
		self.client.force_login(client_user)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 403)


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
