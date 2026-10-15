import json  # Sérialise le message WhatsApp au format JSON exigé par Meta.
from smtplib import SMTPException  # Reconnaît les erreurs d'envoi du backend SMTP.
from urllib.error import HTTPError, URLError  # Distingue les erreurs HTTP et réseau de l'API Meta.
from urllib.request import Request, urlopen  # Construit et exécute la requête HTTPS vers WhatsApp.

from django.conf import settings  # Lit les paramètres e-mail et WhatsApp du projet.
from django.core.mail import send_mail  # Envoie le courriel via le backend configuré dans Django.


class CredentialDeliveryError(Exception):
    """Signale une configuration manquante ou un échec d'envoi des identifiants."""


def validate_credential_delivery_configuration():
    """Vérifie les paramètres requis avant de créer un compte et tenter les envois."""
    missing = []  # Accumule les noms des paramètres absents pour les signaler ensemble.
    email_backend = settings.EMAIL_BACKEND  # Récupère le backend e-mail sélectionné dans les réglages Django.
    if 'console.EmailBackend' in email_backend:
        missing.append('EMAIL_BACKEND (configure an e-mail backend)')  # Le backend console n'envoie pas réellement de courriels.
    elif email_backend.endswith('smtp.EmailBackend') and not settings.EMAIL_HOST:
        missing.append('EMAIL_HOST')  # Le backend SMTP ne peut pas se connecter sans serveur hôte.
    if not settings.DEFAULT_FROM_EMAIL:
        missing.append('DEFAULT_FROM_EMAIL')  # Exige une adresse expéditeur pour l'e-mail des identifiants.

    # Parcourt les réglages indispensables à l'envoi d'un modèle WhatsApp via Meta.
    for name in (
        'WHATSAPP_ACCESS_TOKEN',
        'WHATSAPP_PHONE_NUMBER_ID',
        'WHATSAPP_CREDENTIALS_TEMPLATE',
    ):
        if not getattr(settings, name, ''):
            missing.append(name)  # Ajoute à la liste tout réglage Meta absent ou vide.

    if missing:
        # Arrête le traitement avant la création du compte si un canal n'est pas configuré.
        raise CredentialDeliveryError(
            'Configuration manquante pour envoyer les identifiants : '
            + ', '.join(missing)
        )


def _send_email(user, username, password):
    """Envoie les identifiants générés à l'adresse e-mail du livreur."""
    sent = send_mail(
        subject='Vos identifiants de livreur',  # Définit l'objet visible dans la boîte de réception.
        message=(
            f"Bonjour {user.first_name},\n\n"  # Personnalise le message avec le prénom du destinataire.
            f"Votre compte livreur a été créé.\n"
            f"Nom d'utilisateur : {username}\n"  # Communique le nom d'utilisateur généré.
            f"Mot de passe : {password}\n\n"  # Communique le mot de passe généré une seule fois.
            "Gardez ces identifiants confidentiels."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,  # Utilise l'adresse expéditeur configurée dans Django.
        recipient_list=[user.email],  # Adresse e-mail du livreur, rendue obligatoire par le formulaire.
        fail_silently=False,  # Laisse remonter les erreurs pour détecter un échec réel d'envoi.
    )
    if sent != 1:
        # Django renvoie le nombre d'e-mails acceptés; toute valeur autre que 1 indique un échec.
        raise CredentialDeliveryError("L'e-mail n'a pas été accepté par le serveur.")


def _send_whatsapp(user, username, password):
    """Envoie les identifiants par un modèle WhatsApp approuvé de Meta."""
    recipient = user.telephone[1:]  # Retire le + initial; l'API WhatsApp attend l'indicatif en chiffres.
    # Prépare le message et les variables remplaçant les deux paramètres du modèle approuvé.
    payload = {
        'messaging_product': 'whatsapp',  # Indique à Meta que le message utilise WhatsApp.
        'to': recipient,  # Spécifie le numéro international du livreur comme destinataire.
        'type': 'template',  # Envoie un modèle approuvé, utilisable hors de la fenêtre de service.
        'template': {
            'name': settings.WHATSAPP_CREDENTIALS_TEMPLATE,  # Sélectionne le modèle configuré dans Meta.
            'language': {'code': settings.WHATSAPP_TEMPLATE_LANGUAGE},  # Choisit la langue dans laquelle le modèle a été approuvé.
            'components': [{
                'type': 'body',  # Renseigne les variables du texte principal du modèle.
                'parameters': [
                    {'type': 'text', 'text': username},  # Remplace le premier paramètre du modèle par le username.
                    {'type': 'text', 'text': password},  # Remplace le deuxième paramètre du modèle par le mot de passe.
                ],
            }],
        },
    }
    # Construit l'URL du point de terminaison Messages pour le numéro WhatsApp configuré.
    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    request = Request(
        url,  # Adresse de l'API Meta à appeler.
        data=json.dumps(payload).encode('utf-8'),  # Encode le payload JSON en octets UTF-8 pour la requête HTTP.
        headers={
            # Le jeton d'accès Meta authentifie l'appel; il reste dans les réglages, jamais dans le code.
            'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}',
            'Content-Type': 'application/json',  # Déclare le format du corps de la requête.
        },
        method='POST',  # Utilise POST pour demander à Meta l'envoi d'un nouveau message.
    )
    try:
        with urlopen(request, timeout=15) as response:  # Envoie la requête et impose un délai maximal de 15 secondes.
            if not 200 <= response.status < 300:
                # Toute réponse hors de la plage HTTP 2xx signale que Meta n'a pas accepté la demande.
                raise CredentialDeliveryError(
                    f"L'API WhatsApp a répondu avec le statut {response.status}."
                )
    except HTTPError as error:
        # Convertit les réponses HTTP d'erreur en une erreur métier sans exposer la réponse brute de Meta.
        raise CredentialDeliveryError(
            f"L'API WhatsApp a répondu avec le statut {error.code}."
        ) from error
    except (URLError, OSError) as error:
        # Signale les échecs réseau, comme un délai dépassé ou un serveur inaccessible.
        raise CredentialDeliveryError(
            "Connexion à l'API WhatsApp impossible."
        ) from error


def send_courier_credentials(user, username, password):
    """Tente les deux canaux et signale explicitement chaque envoi qui échoue."""
    validate_credential_delivery_configuration()  # Refuse de poursuivre si l'e-mail ou WhatsApp n'est pas configuré.
    failures = []  # Garde les erreurs d'un canal tout en tentant l'autre canal aussi.

    try:
        _send_email(user, username, password)  # Tente d'envoyer le message par e-mail.
    except (CredentialDeliveryError, SMTPException, OSError) as error:
        failures.append(f'e-mail : {error}')  # Conserve l'erreur e-mail pour la signaler après l'essai WhatsApp.

    try:
        _send_whatsapp(user, username, password)  # Tente l'envoi WhatsApp même si l'e-mail a échoué.
    except CredentialDeliveryError as error:
        failures.append(f'WhatsApp : {error}')  # Conserve aussi l'échec WhatsApp pour le rapport final.

    if failures:
        # Rapporte tous les canaux en échec au lieu de masquer l'un d'eux.
        raise CredentialDeliveryError(
            "Échec d'envoi des identifiants — " + '; '.join(failures)
        )
