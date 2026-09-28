from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from entreprises_app.models import Entreprise, Zone
from livreurs_app.models import Livreur

User = get_user_model()


# ==========================================
# 1. FORMULAIRE CLIENT
# ==========================================
class InscriptionClientForm(forms.ModelForm):
    """Inscription simple pour les clients finaux (Téléphone + Mot de passe + Nom)"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Mot de passe'}),
        label="Mot de passe"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmez le mot de passe'}),
        label="Confirmation du mot de passe"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'telephone', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Nom'}),
            'telephone': forms.TextInput(attrs={'placeholder': 'Numéro de téléphone (ex: 70000000)'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email (Optionnel)'}),
        }

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return confirm_password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'client'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


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
        fields = ['nom_entreprise', 'logo', 'zones_couvertes', 'palier']
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