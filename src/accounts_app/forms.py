from uuid import uuid4

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify
from clients_app.models import Client
from entreprises_app.models import Entreprise, Zone
from livreurs_app.models import Livreur

User = get_user_model()


# ==========================================
# 1. FORMULAIRE CLIENT
# ==========================================
class InscriptionClientForm(forms.ModelForm):
    """Inscription du compte utilisateur et de son profil client."""
    username = forms.CharField(
        max_length=30,
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={
            'placeholder': "Nom d'utilisateur",
            'class': 'input input-bordered w-full rounded-xl',
        }),
    )
    first_name = forms.CharField(
        max_length=30,
        label="Prénom",
        widget=forms.TextInput(attrs={
            'placeholder': 'Prénom',
            'class': 'input input-bordered w-full rounded-xl',
        }),
    )
    last_name = forms.CharField(
        max_length=30,
        label="Nom",
        widget=forms.TextInput(attrs={
            'placeholder': 'Nom',
            'class': 'input input-bordered w-full rounded-xl',
        }),
    )
    telephone = forms.CharField(
        max_length=20,
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={
            'placeholder': 'Numéro de téléphone (ex: 70000000)',
            'class': 'input input-bordered w-full rounded-xl',
        }),
    )
    email = forms.EmailField(
        required=False,
        label="Email",
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email (Optionnel)',
            'class': 'input input-bordered w-full rounded-xl',
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mot de passe',
            ":type":"showPassword ? 'text' : 'password'",
            "class": 'input input-bordered w-full pr-10 rounded-xl focus:border-[#059669] focus:outline-none transition-colors',
            "required": True,
            }),
        label="Mot de passe"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirmez le mot de passe',
            ":type":"showConfirmPassword ? 'text' : 'password'",
            "class": 'input input-bordered w-full pr-10 rounded-xl focus:border-[#059669] focus:outline-none transition-colors',
            "required": True,
        }),
        label="Confirmation du mot de passe"
    )

    class Meta:  # Configure le modèle enregistré et les champs affichés par ModelForm.
        model = Client
        fields = ["photo_profil", "ville", "quartier"]
        widgets = {
            'photo_profil': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'ville': forms.TextInput(attrs={
                'placeholder': 'Ville (Optionnel)',
                'class': 'input input-bordered w-full rounded-xl',
            }),
            'quartier': forms.TextInput(attrs={
                'placeholder': 'Quartier (Optionnel)',
                'class': 'input input-bordered w-full rounded-xl',
            }),
        }

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return confirm_password

    def clean_telephone(self):
        telephone = self.cleaned_data['telephone']
        if User.objects.filter(telephone=telephone).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return telephone

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username

    @transaction.atomic
    def save(self, commit=True):
        client = super().save(commit=False)
        user = User(
            username=self.cleaned_data['username'],
            telephone=self.cleaned_data['telephone'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data.get('email', ''),
            role='client',
        )
        user.set_password(self.cleaned_data['password'])
        client.user = user

        if commit:
            user.save()
            client.save()
        return client


# ==========================================
# 2. FORMULAIRE LIVREUR INDÉPENDANT
# ==========================================
class InscriptionLivreurForm(forms.ModelForm):
    """
    Formulaire combiné : Crée l'User + le profil Livreur
    (Véhicule, Photos de CNI/Selfie pour vérification)
    """
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmation")

    # Champs spécifiques à l'utilisateur
    username = forms.CharField(max_length=30, label="Nom d'utilisateur")
    first_name = forms.CharField(max_length=30, label="Prénom")
    last_name = forms.CharField(max_length=30, label="Nom")
    telephone = forms.CharField(max_length=20, label="Numéro de téléphone")
    email = forms.EmailField(required=False, label="Email")

    class Meta:
        model = Livreur
        fields = [
            'type_vehicule', 
            'photo_profil', 
            'photo_cni_recto', 
            'photo_cni_verso', 
            'photo_selfie'
        ]

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if User.objects.filter(telephone=telephone).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return telephone

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return confirm_password

    @transaction.atomic
    def save(self, commit=True):
        # 1. Création du compte utilisateur de base
        user = User.objects.create_user(
            username=self.cleaned_data['username'],  # Utilisation du téléphone comme nom d'utilisateur
            telephone=self.cleaned_data['telephone'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data.get('email', ''),
            password=self.cleaned_data['password'],
            role='livreur'
        )

        # 2. Création du profil livreur rattaché à l'utilisateur
        livreur = super().save(commit=False)
        livreur.user = user
        livreur.statut_verification = 'en_attente'  # Doit être validé par l'admin/support
        
        if commit:
            livreur.save()
        return livreur


# ==========================================
# 3. FORMULAIRE ENTREPRISE DE LIVRAISON
# ==========================================
class InscriptionEntrepriseForm(forms.ModelForm):
    """
    Formulaire combiné : Crée l'User principal + la structure Entreprise
    """
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe admin principal")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmation")

    # Champs de l'administrateur principal de l'entreprise
    first_name = forms.CharField(max_length=30, label="Prénom du responsable")
    last_name = forms.CharField(max_length=30, label="Nom du responsable")
    telephone = forms.CharField(max_length=20, label="Téléphone professionnel")
    email = forms.EmailField(required=False, label="Email professionnel")

    class Meta:
        model = Entreprise
        fields = ['nom_entreprise', 'logo', 'zones_couvertes']
        widgets = {
            'zones_couvertes': forms.CheckboxSelectMultiple(),  # Choix des zones sur la carte/liste
        }

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if User.objects.filter(telephone=telephone).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return telephone

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return confirm_password

    @transaction.atomic
    def save(self, commit=True):
        # 1. Création du compte utilisateur Admin de l'entreprise
        user = User.objects.create_user(
            telephone=self.cleaned_data['telephone'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data.get('email', ''),
            password=self.cleaned_data['password'],
            role='entreprise'
        )

        # 2. Création du profil Entreprise
        entreprise = super().save(commit=False)
        entreprise.user_principal = user
        
        if commit:
            entreprise.save()
            # On enregistre les zones (ManyToManyField nécessite que l'entreprise soit déjà sauvée en BDD)
            self.save_m2m()

        return entreprise


# ==========================================
# 4. FORMULAIRE LIVREUR POUR ENTREPRISE
# ==========================================

class InscriptionLivreurEntrepriseForm(forms.ModelForm):
    """Formulaire qui crée le compte utilisateur et le profil d'un livreur d'entreprise."""

    first_name = forms.CharField(max_length=30, label="Prénom")  # Demande le prénom pour créer le compte utilisateur.
    last_name = forms.CharField(max_length=30, label="Nom")  # Demande le nom de famille du livreur.
    telephone = forms.CharField(
        max_length=20,  # Respecte la longueur maximale du champ téléphone du modèle User.
        label="Numéro de téléphone WhatsApp",  # Utilise ce numéro comme destinataire du message WhatsApp.
        help_text="Saisissez le numéro au format international, par exemple +22670000000.",  # Indique le format E.164 attendu.
    )
    email = forms.EmailField(required=True, label="Adresse e-mail")  # Rend l'e-mail obligatoire pour transmettre les identifiants.

    class Meta:
        model = Livreur  # Enregistre les informations du profil dans le modèle Livreur.
        fields = [
            'type_vehicule',  # Enregistre le moyen de transport déclaré.
            'photo_profil',  # Permet de joindre la photo de profil du livreur.
            'photo_cni_recto',  # Permet de joindre le recto de sa pièce d'identité.
            'photo_cni_verso',  # Permet de joindre le verso de sa pièce d'identité.
            'photo_selfie',  # Permet de joindre le selfie utilisé pour la vérification.
        ]

    def __init__(self, *args, user, **kwargs):  # Reçoit notamment l'utilisateur entreprise fourni par la vue.
        super().__init__(*args, **kwargs)  # Initialise les champs Django, y compris les données POST éventuelles.
        self.user = user  # Mémorise l'administrateur connecté transmis par get_form_kwargs().
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input input-bordered w-full rounded-xl'  # Applique le style partagé aux contrôles du formulaire.

    def clean_telephone(self):  # Ajoute les vérifications métier au nettoyage du numéro.
        telephone = self.cleaned_data.get('telephone')  # Récupère le numéro validé par les contrôles de base de Django.
        if User.objects.filter(telephone=telephone).exists():  # Vérifie que le numéro n'est pas déjà associé à un compte.
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")  # Refuse un numéro déjà pris.
        if not telephone or not telephone.startswith('+') or not telephone[1:].isdigit():
            # Exige un indicatif international et uniquement des chiffres après le signe +.
            raise forms.ValidationError(
                "Saisissez le numéro au format international, par exemple +22670000000."
            )
        if not 8 <= len(telephone[1:]) <= 15 or telephone[1] == '0':
            # Vérifie la plage de longueur E.164 et interdit un indicatif commençant par zéro.
            raise forms.ValidationError("Le numéro international saisi n'est pas valide.")
        return telephone  # Conserve la valeur validée dans cleaned_data.

    @transaction.atomic  # Annule l'ensemble de l'enregistrement si une écriture en base échoue.
    def save(self, commit=True):  # Crée le User puis le profil Livreur associé.
        """Crée le compte et le profil dans une transaction atomique."""
        livreur = super().save(commit=False)  # Construit le profil sans l'enregistrer avant son association à un User.
        
        username_base = slugify(
            f"{self.cleaned_data['first_name']}.{self.cleaned_data['last_name']}"
        )[:21] or 'livreur'  # Normalise les noms pour en faire une base de username courte et lisible.
        
        username = f"{username_base}-{uuid4().hex[:8]}"  # Ajoute un suffixe aléatoire pour rendre le username unique.
        while User.objects.filter(username=username).exists():
            username = f"{username_base}-{uuid4().hex[:8]}"  # Génère un autre suffixe si une collision très improbable survient.

        password = uuid4().hex + uuid4().hex[:8]  # Génère un secret aléatoire de 40 caractères sans le demander au formulaire.
        user = User(
            username=username,  # Définit l'identifiant de connexion généré.
            telephone=self.cleaned_data['telephone'],  # Enregistre le numéro validé du livreur.
            first_name=self.cleaned_data['first_name'],  # Enregistre son prénom.
            last_name=self.cleaned_data['last_name'],  # Enregistre son nom.
            email=self.cleaned_data['email'],  # Enregistre son adresse e-mail obligatoire.
            role='livreur',  # Attribue au compte le rôle requis pour accéder aux fonctions livreur.
        )
        print(f""" mot de passe  {password}
              username {username}
              """)
        user.set_password(password)  # Hache le mot de passe avant son stockage en base de données.
        livreur.user = user  # Relie le profil livreur au compte qui vient d'être préparé.
        livreur.entreprise = self.user.entreprise_profil  # Rattache le livreur à l'entreprise de l'administrateur connecté.
        livreur.statut_verification = 'en_attente'  # Exige la vérification avant de considérer le livreur comme validé.
        self.generated_username = username  # Rend l'identifiant disponible à la vue pour les notifications.
        self.generated_password = password  # Rend temporairement le mot de passe disponible pour les notifications.

        if commit:
            user.save()  # Enregistre le compte avant son profil, qui dépend de celui-ci.
            livreur.save()  # Enregistre le profil et son association à l'utilisateur et à l'entreprise.

        return livreur  # Renvoie le profil créé à la vue appelante.